import streamlit as st

AUTOR = "Jesús Eduardo Manjarrez González"

st.set_page_config(page_title="App de Diseño Experimental", page_icon="🌱", layout="wide")

st.title("App de Diseño Experimental")
st.subheader("Ingeniería Agrícola – Universidad de Sucre")

st.write("El diseño experimental en el campo agrícola permite evaluar objetivamente el efecto de diferentes tratamientos (como métodos de riego, tipos de fertilizantes o secadores) sobre una variable de interés, minimizando el error aleatorio para tomar decisiones basadas en evidencia estadística.")

st.markdown("""
| Módulo | Cuándo se usa | Ejemplo agrícola | Estado |
|---|---|---|---|
| **DCA** | Unidades experimentales homogéneas | Comparar rendimiento de 4 secadores de yuca | Disponible |
| **DBCA** | Hay un gradiente de variabilidad (bloques) | Evaluar fertilizantes en un terreno con pendiente | En construcción |
| **DCL** | Control de variabilidad en dos direcciones | Probar tractores en diferentes días y con diferentes operadores | En construcción |
| **DPD** | Parcelas divididas (factor principal y secundario) | Riego en parcela principal, variedad de semilla en subparcela | En construcción |
| **Factoriales** | Dos o más factores interactuando | Efecto combinado de nitrógeno y fósforo en maíz | En construcción |
| **RSM** | Superficies de respuesta para optimización | Encontrar temperatura y tiempo óptimos para secado de granos | En construcción |
""")

st.markdown("### Instrucciones de uso")
st.markdown("""
1. **Elegir módulo:** Selecciona el diseño correspondiente en el menú lateral.
2. **Cargar datos:** Sube tu archivo CSV o Excel con las observaciones.
3. **Revisar resultados:** Analiza la tabla ANOVA, gráficos y diagnóstico de supuestos.
4. **Verificar a mano:** Compara los resultados con tu cálculo en la Fase 1.
""")

st.warning("Esta app apoya el aprendizaje. El estudiante interpreta los resultados, verifica supuestos y compara con su cálculo manual.")

st.sidebar.markdown(f"**Autor:** {AUTOR}")
st.sidebar.markdown("**Curso:** Diseño Experimental")
st.sidebar.markdown("**Semestre:** 2026-2")