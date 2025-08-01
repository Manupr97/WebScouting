import streamlit as st

st.set_page_config(
    page_title="WebScouting",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ WebScouting - Versión 1")

# Solo imports básicos
st.header("1. Test de imports básicos")
try:
    import pandas as pd
    st.success("✅ pandas importado")
    
    # Leer el Excel
    df = pd.read_excel("data/wyscout_LaLiga_limpio.xlsx")
    st.success(f"✅ Excel cargado: {len(df)} jugadores")
    
    # Mostrar métricas básicas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Jugadores", len(df))
    with col2:
        if 'edad' in df.columns:
            st.metric("Edad Promedio", f"{df['edad'].mean():.1f}")
    with col3:
        st.metric("Columnas", len(df.columns))
    
    # Mostrar primeros jugadores
    st.dataframe(df.head())
    
except Exception as e:
    st.error(f"Error: {e}")

st.info("Si ves esto, la versión 1 funciona correctamente.")