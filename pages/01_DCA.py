import streamlit as st

st.title("Diseño Completamente al Azar (DCA)")
st.info("Módulo en desarrollo")
import streamlit as st
import pandas as pd
import plotly.express as px
import scipy.stats as stats
from utils.anova_utils import (
    cargar_datos, validar_dca, ajustar_dca, tabla_anova,
    resumen_tratamientos, coeficiente_variacion, tukey, interpretar_dca
)

st.title("Diseño Completamente al Azar (DCA)")
st.write("El DCA se utiliza cuando las unidades experimentales son homogéneas. Ejemplo: Evaluar cuál de 4 secadores solares deja las rodajas de yuca con menor humedad.")

# Carga de datos con caché para no recargar en cada clic
@st.cache_data
def load_data(file):
    return cargar_datos(file)

@st.cache_data
def load_default_data():
    return pd.read_csv("data/dca_secadores.csv")

archivo = st.file_uploader("Cargar datos (CSV o Excel)", type=["csv", "xlsx", "xls"])

if archivo is not None:
    try:
        df = load_data(archivo)
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        st.stop()
else:
    df = load_default_data()
    st.caption("Usando datos de ejemplo (dca_secadores.csv). Sube un archivo para usar tus propios datos.")

if not df.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        col_trat = st.selectbox("Columna de Tratamientos", df.columns, index=0)
    with col2:
        col_resp = st.selectbox("Columna de Respuesta", df.columns, index=len(df.columns)-1)
    with col3:
        alfa = st.slider("Nivel de significancia (Alfa)", min_value=0.01, max_value=0.10, value=0.05, step=0.01)

    # Validaciones antes de calcular
    errores = validar_dca(df, col_trat, col_resp)
    if errores:
        for error in errores:
            st.error(error)
        st.stop()

    # Creación de las Pestañas
    tab1, tab2, tab3, tab4 = st.tabs(["Datos", "ANOVA", "Comparaciones", "Gráficos"])

    # Pestaña 1: Datos
    with tab1:
        st.subheader("Datos ingresados")
        st.dataframe(df)
        st.subheader("Resumen por tratamiento")
        resumen = resumen_tratamientos(df, col_trat, col_resp)
        st.dataframe(resumen)

    # Preparar el ANOVA en memoria
    modelo = ajustar_dca(df, col_trat, col_resp)
    anova = tabla_anova(modelo)
    
    # Pestaña 2: ANOVA
    with tab2:
        st.subheader("Tabla ANOVA")
        st.dataframe(anova.style.format(precision=4, na_rep="-"))
        
        # F crítica
        gl_trat = anova.loc['Tratamientos', 'gl']
        gl_err = anova.loc['Error', 'gl']
        f_crit = stats.f.ppf(1 - alfa, gl_trat, gl_err)
        st.write(f"**F crítica ({alfa}):** {f_crit:.4f}")
        
        # Coeficiente de Variación
        cv = coeficiente_variacion(modelo, df, col_resp)
        st.write(f"**Coeficiente de Variación (CV):** {cv:.2f}%")
        
        # Interpretación automática
        interpretacion = interpretar_dca(anova, alfa)
        if anova.loc['Tratamientos', 'p-valor'] < alfa:
            st.success(interpretacion)
        else:
            st.info(interpretacion)

    # Pestaña 3: Comparaciones
    with tab3:
        p_valor = anova.loc['Tratamientos', 'p-valor']
        if p_valor < alfa:
            st.subheader("Prueba de Tukey")
            df_tukey, dms, balanceado = tukey(df, col_trat, col_resp, alfa)
            if not balanceado:
                st.warning("El diseño no está balanceado. La DMS calculada es aproximada.")
            
            st.write(f"**Diferencia Mínima Significativa (DMS):** {dms:.4f}")
            st.dataframe(df_tukey)
        else:
            st.info("No se realiza la prueba de Tukey porque no se rechazó la hipótesis nula (las medias se consideran estadísticamente iguales).")

    # Pestaña 4: Gráficos
    with tab4:
        st.subheader("Gráfico de Cajas (Boxplot)")
        fig_box = px.box(df, x=col_trat, y=col_resp, points="all", title="Distribución por Tratamiento",
                         labels={col_trat: "Tratamiento", col_resp: "Respuesta"})
        st.plotly_chart(fig_box, use_container_width=True)
        
        st.subheader("Gráfico de Medias")
        fig_medias = px.line(resumen, x='Tratamiento', y='Media', markers=True, error_y='Desviación',
                             title="Medias y Desviación Estándar por Tratamiento")
        st.plotly_chart(fig_medias, use_container_width=True)