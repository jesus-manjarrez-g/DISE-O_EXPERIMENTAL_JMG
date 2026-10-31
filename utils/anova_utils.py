import pandas as pd
import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd

def cargar_datos(archivo) -> pd.DataFrame:
    """Carga datos desde un archivo CSV o Excel."""
    nombre = archivo.name.lower()
    if nombre.endswith('.csv'):
        # Intenta leer con coma, si falla usa punto y coma
        try:
            return pd.read_csv(archivo, sep=',')
        except:
            return pd.read_csv(archivo, sep=';')
    elif nombre.endswith(('.xls', '.xlsx')):
        return pd.read_excel(archivo)
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel.")

def validar_dca(df: pd.DataFrame, col_trat: str, col_resp: str) -> list[str]:
    """Valida que los datos cumplan los requisitos mínimos para un DCA."""
    errores = []
    if col_trat not in df.columns or col_resp not in df.columns:
        errores.append("Faltan las columnas seleccionadas en los datos.")
        return errores
    
    if not pd.api.types.is_numeric_dtype(df[col_resp]):
        errores.append(f"La columna de respuesta '{col_resp}' debe ser numérica.")
    
    if df[col_resp].isnull().any() or df[col_trat].isnull().any():
        errores.append("Hay datos faltantes (nulos) en las columnas seleccionadas.")
        
    tratamientos = df[col_trat].unique()
    if len(tratamientos) < 2:
        errores.append("Debe haber al menos 2 tratamientos para comparar.")
        
    conteos = df.groupby(col_trat).size()
    if (conteos < 2).any():
        errores.append("Cada tratamiento debe tener al menos 2 réplicas para calcular el error.")
        
    return errores

def ajustar_dca(df: pd.DataFrame, col_trat: str, col_resp: str):
    """Ajusta el modelo lineal OLS para el DCA."""
    # Protegemos los nombres de las columnas con Q() por si tienen espacios
    formula = f'Q("{col_resp}") ~ C(Q("{col_trat}"))'
    modelo = ols(formula, data=df).fit()
    return modelo

def tabla_anova(modelo) -> pd.DataFrame:
    """Genera la tabla ANOVA clásica (Tipo II)."""
    # Calculamos la tabla ANOVA usando typ=2
    anova = anova_lm(modelo, typ=2)
    
    # Renombramos columnas al español
    anova.columns = ['SC', 'gl', 'F', 'p-valor']
    anova.index = ['Tratamientos', 'Error']
    
    # Reorganizamos y calculamos Cuadrados Medios (CM = SC / gl)
    anova['CM'] = anova['SC'] / anova['gl']
    anova = anova[['gl', 'SC', 'CM', 'F', 'p-valor']]
    
    # Agregamos la fila Total (suma de SC y gl de Tratamientos y Error)
    fila_total = pd.DataFrame({
        'gl': [anova['gl'].sum()],
        'SC': [anova['SC'].sum()],
        'CM': [np.nan],
        'F': [np.nan],
        'p-valor': [np.nan]
    }, index=['Total'])
    
    return pd.concat([anova, fila_total])

def resumen_tratamientos(df: pd.DataFrame, col_trat: str, col_resp: str) -> pd.DataFrame:
    """Calcula n, suma, media y desviación estándar por tratamiento."""
    resumen = df.groupby(col_trat)[col_resp].agg(
        n='count',
        Total='sum',
        Media='mean',
        Desviación='std'
    ).reset_index()
    resumen.rename(columns={col_trat: 'Tratamiento'}, inplace=True)
    return resumen

def coeficiente_variacion(modelo, df: pd.DataFrame, col_resp: str) -> float:
    """Calcula el Coeficiente de Variación (CV)."""
    cme = modelo.mse_resid # Cuadrado Medio del Error
    media_general = df[col_resp].mean()
    cv = (np.sqrt(cme) / media_general) * 100
    return cv

def tukey(df: pd.DataFrame, col_trat: str, col_resp: str, alfa=0.05) -> tuple[pd.DataFrame, float, bool]:
    """Realiza la prueba de medias de Tukey."""
    tukey_res = pairwise_tukeyhsd(endog=df[col_resp], groups=df[col_trat], alpha=alfa)
    
    # Convertimos los resultados a un DataFrame en español
    df_tukey = pd.DataFrame(data=tukey_res._results_table.data[1:], columns=tukey_res._results_table.data[0])
    
    # Se ajusta a 7 columnas para coincidir con la versión actual de statsmodels
    df_tukey.columns = ['Grupo 1', 'Grupo 2', 'Diferencia', 'p-valor', 'LI', 'LS', 'Rechazar H0']
    
    # Cálculo manual de la DMS (Diferencia Mínima Significativa)
    gl_error = len(df) - len(df[col_trat].unique())
    cme = anova_lm(ols(f'Q("{col_resp}") ~ C(Q("{col_trat}"))', data=df).fit(), typ=2).loc[f'C(Q("{col_trat}"))', 'sum_sq'] / (len(df[col_trat].unique()) - 1) 
    
    # Usamos ols para extraer el mse correcto (CME)
    modelo_temp = ols(f'Q("{col_resp}") ~ C(Q("{col_trat}"))', data=df).fit()
    cme = modelo_temp.mse_resid
    t = len(df[col_trat].unique())
    
    # Verificamos si es balanceado
    conteos = df.groupby(col_trat).size()
    balanceado = conteos.nunique() == 1
    r = conteos.iloc[0] if balanceado else len(df) / t # Promedio armónico simplificado para la advertencia
    
    # Valor crítico q de la distribución de rango estudentizado
    q_crit = stats.studentized_range.ppf(1 - alfa, t, gl_error)
    dms = q_crit * np.sqrt(cme / r)
    
    return df_tukey, dms, balanceado

def interpretar_dca(tabla_anova: pd.DataFrame, alfa=0.05) -> str:
    """Interpreta el p-valor de la tabla ANOVA."""
    p_valor = tabla_anova.loc['Tratamientos', 'p-valor']
    if p_valor < alfa:
        return f"Se rechaza H0 (p = {p_valor:.4f} < {alfa}). Hay evidencia estadística de que al menos un tratamiento (secador) tiene un efecto diferente sobre la variable de respuesta. Procede a revisar la prueba de Tukey."
    else:
        return f"No se rechaza H0 (p = {p_valor:.4f} >= {alfa}). No hay evidencia suficiente para afirmar que los tratamientos tienen efectos diferentes."