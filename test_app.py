import streamlit as st

st.title("🧪 Test Mínimo")
st.write("Si ves esto, Streamlit funciona!")

# Test 1: Imports básicos
try:
    import pandas as pd
    st.success("✅ pandas importado")
except Exception as e:
    st.error(f"❌ pandas: {e}")

# Test 2: Leer Excel
try:
    df = pd.read_excel("data/wyscout_LaLiga_limpio.xlsx")
    st.success(f"✅ Excel leído: {len(df)} filas")
except Exception as e:
    st.error(f"❌ Error leyendo Excel: {e}")

# Test 3: Import de login
try:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from common.login import LoginManager
    st.success("✅ LoginManager importado")
except Exception as e:
    st.error(f"❌ LoginManager: {e}")

st.info("Fin del test")