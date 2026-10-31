import pandas as pd
import scipy.stats as stats
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def residuos_y_ajustados(modelo):
    """Obtiene los residuos y los valores ajustados del modelo OLS."""
    return modelo.resid, modelo.fittedvalues

def prueba_shapiro(residuos, alfa=0.05):
    """Realiza la prueba de Shapiro-Wilk para normalidad de los residuos."""
    stat, p_valor = stats.shapiro(residuos)
    conclusion = "Se cumple (Normal)" if p_valor >= alfa else "No se cumple (No normal)"
    return stat, p_valor, conclusion

def prueba_levene(df, col_trat, col_resp, alfa=0.05):
    """Realiza la prueba de Levene para homogeneidad de varianzas (basada en la mediana)."""
    # Agrupamos los datos por tratamiento para ingresarlos a la función
    grupos = [grupo[col_resp].values for _, grupo in df.groupby(col_trat)]
    stat, p_valor = stats.levene(*grupos, center="median")
    conclusion = "Se cumple (Homogéneas)" if p_valor >= alfa else "No se cumple (Heterogéneas)"
    return stat, p_valor, conclusion

def grafico_residuos_vs_ajustados(ajustados, residuos):
    """Genera un gráfico de residuos vs valores ajustados usando Plotly."""
    fig = px.scatter(
        x=ajustados, y=residuos, 
        labels={'x': 'Valores Ajustados (Medias)', 'y': 'Residuos'},
        title='Homocedasticidad: Residuos vs Ajustados'
    )
    # Agregamos línea horizontal en el cero
    fig.add_hline(y=0, line_dash="dash", line_color="red")
    return fig

def grafico_qq(residuos):
    """Genera un gráfico Q-Q plot de los residuos usando Plotly para evaluar normalidad."""
    qq = stats.probplot(residuos, dist="norm")
    teoricos = qq[0][0]
    reales = qq[0][1]
    
    fig = px.scatter(
        x=teoricos, y=reales, 
        labels={'x': 'Cuantiles Teóricos', 'y': 'Cuantiles de los Residuos'},
        title='Normalidad: Gráfico Q-Q'
    )
    
    # Dibujamos la recta de referencia ideal
    m = qq[1][0]
    b = qq[1][1]
    x_line = np.array([min(teoricos), max(teoricos)])
    y_line = m * x_line + b
    
    fig.add_trace(go.Scatter(x=x_line, y=y_line, mode='lines', name='Referencia Normal', line=dict(color='red', dash='dash')))
    return fig
