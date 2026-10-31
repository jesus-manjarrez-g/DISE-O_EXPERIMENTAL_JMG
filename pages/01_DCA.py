import streamlit as st
import pandas as pd
import plotly.express as px
import scipy.stats as stats
from utils.anova_utils import (
    cargar_datos, validar_dca, ajustar_dca, tabla_anova,
    resumen_tratamientos, coeficiente_variacion, tukey, interpretar_dca
)
from utils.diagnostico_utils import (
    residuos_y_ajustados, prueba_shapiro, prueba_levene, 
    grafico_residuos_vs_ajustados, grafico_qq
)

st.title("Diseño Completamente al Azar (DCA)")
st.write("El DCA se utiliza cuando las unidades experimentales son homogéneas. Ejemplo: Evaluar cuál de 4 secadores solares deja las rodajas de yuca con menor humedad.")

# Carga de datos con caché
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

    # Creación de las Pestañas (ahora son 5)
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Datos", "ANOVA", "Comparaciones", "Gráficos", "Supuestos"])

    with tab1:
        st.subheader("Datos ingresados")
        st.dataframe(df)
        st.subheader("Resumen por tratamiento")
        resumen = resumen_tratamientos(df, col_trat, col_resp)
        st.dataframe(resumen)

    modelo = ajustar_dca(df, col_trat, col_resp)
    anova = tabla_anova(modelo)
    
    with tab2:
        st.subheader("Tabla ANOVA")
        st.dataframe(anova.style.format(precision=4, na_rep="-"))
        
        gl_trat = anova.loc['Tratamientos', 'gl']
        gl_err = anova.loc['Error', 'gl']
        f_crit = stats.f.ppf(1 - alfa, gl_trat, gl_err)
        st.write(f"**F crítica ({alfa}):** {f_crit:.4f}")
        
        cv = coeficiente_variacion(modelo, df, col_resp)
        st.write(f"**Coeficiente de Variación (CV):** {cv:.2f}%")
        
        interpretacion = interpretar_dca(anova, alfa)
        if anova.loc['Tratamientos', 'p-valor'] < alfa:
            st.success(interpretacion)
        else:
            st.info(interpretacion)

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
            st.info("No se realiza la prueba de Tukey porque no se rechazó la hipótesis nula.")

    with tab4:
        st.subheader("Gráfico de Cajas (Boxplot)")
        fig_box = px.box(df, x=col_trat, y=col_resp, points="all", title="Distribución por Tratamiento",
                         labels={col_trat: "Tratamiento", col_resp: "Respuesta"})
        st.plotly_chart(fig_box, use_container_width=True)
        
        st.subheader("Gráfico de Medias")
        fig_medias = px.line(resumen, x='Tratamiento', y='Media', markers=True, error_y='Desviación',
                             title="Medias y Desviación Estándar por Tratamiento")
        st.plotly_chart(fig_medias, use_container_width=True)
        
    # Nueva Pestaña 5: Supuestos
    with tab5:
        st.subheader("Diagnóstico de Supuestos del Modelo")
        st.write("**1. Normalidad:** Los residuos deben distribuirse normalmente (Prueba de Shapiro-Wilk).")
        st.write("**2. Homogeneidad de Varianzas (Homocedasticidad):** La variabilidad debe ser similar en todos los tratamientos (Prueba de Levene).")
        st.write("**3. Independencia:** Garantizada por la aleatorización de los lotes en los secadores durante el experimento.")
        
        residuos, ajustados = residuos_y_ajustados(modelo)
        
        # Pruebas estadísticas formales
        stat_shapiro, p_shapiro, concl_shapiro = prueba_shapiro(residuos, alfa)
        stat_levene, p_levene, concl_levene = prueba_levene(df, col_trat, col_resp, alfa)
        
        df_supuestos = pd.DataFrame({
            "Supuesto": ["Normalidad (Shapiro-Wilk)", "Homogeneidad (Levene)"],
            "Estadístico": [stat_shapiro, stat_levene],
            "p-valor": [p_shapiro, p_levene],
            "Conclusión": [concl_shapiro, concl_levene]
        })
        st.dataframe(df_supuestos.style.format({'Estadístico': '{:.4f}', 'p-valor': '{:.4f}'}))
        
        # Gráficos de validación
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_qq = grafico_qq(residuos)
            st.plotly_chart(fig_qq, use_container_width=True)
        with col_g2:
            fig_res = grafico_residuos_vs_ajustados(ajustados, residuos)
            st.plotly_chart(fig_res, use_container_width=True)