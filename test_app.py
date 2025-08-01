import streamlit as st
import sys
import os

st.set_page_config(page_title="Test App", page_icon="🧪")

st.title("🧪 Diagnóstico de WebScouting")

# Información del sistema
st.header("1. Información del Sistema")
col1, col2 = st.columns(2)
with col1:
    st.info(f"Python: {sys.version}")
    st.info(f"Streamlit: {st.__version__}")
with col2:
    st.info(f"Directorio actual: {os.getcwd()}")
    st.info(f"Archivos en raíz: {len(os.listdir('.'))}")

# Verificar estructura de carpetas
st.header("2. Estructura de Carpetas")
folders_to_check = ['data', 'models', 'common', 'pages', '.streamlit']
for folder in folders_to_check:
    if os.path.exists(folder):
        files = os.listdir(folder)
        st.success(f"✅ {folder}/ existe ({len(files)} archivos)")
    else:
        st.error(f"❌ {folder}/ NO existe")

# Verificar archivos críticos
st.header("3. Archivos Críticos")
files_to_check = [
    'data/wyscout_LaLiga_limpio.xlsx',
    'models/wyscout_model.py',
    'models/partido_model.py',
    'common/login.py'
]
for file in files_to_check:
    if os.path.exists(file):
        size = os.path.getsize(file) / 1024  # KB
        st.success(f"✅ {file} ({size:.1f} KB)")
    else:
        st.error(f"❌ {file} NO encontrado")

# Test de imports
st.header("4. Test de Imports")

try:
    import pandas as pd
    st.success(f"✅ pandas {pd.__version__}")
except Exception as e:
    st.error(f"❌ pandas: {e}")

try:
    import plotly
    st.success(f"✅ plotly {plotly.__version__}")
except Exception as e:
    st.error(f"❌ plotly: {e}")

try:
    import openpyxl
    st.success(f"✅ openpyxl {openpyxl.__version__}")
except Exception as e:
    st.error(f"❌ openpyxl: {e}")

# Test de carga de Excel
st.header("5. Test de Carga de Excel")
try:
    import pandas as pd
    df = pd.read_excel("data/wyscout_LaLiga_limpio.xlsx")
    st.success(f"✅ Excel cargado correctamente: {len(df)} filas, {len(df.columns)} columnas")
    st.dataframe(df.head(3))
except Exception as e:
    st.error(f"❌ Error al cargar Excel: {str(e)}")
    st.error(f"Tipo de error: {type(e).__name__}")

# Test de imports locales
st.header("6. Test de Imports Locales")

# Agregar path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from common.login import LoginManager
    st.success("✅ LoginManager importado correctamente")
except Exception as e:
    st.error(f"❌ Error importando LoginManager: {e}")

try:
    from models.wyscout_model import WyscoutModel
    st.success("✅ WyscoutModel importado correctamente")
except Exception as e:
    st.error(f"❌ Error importando WyscoutModel: {e}")

try:
    from models.partido_model import PartidoModel
    st.success("✅ PartidoModel importado correctamente")
except Exception as e:
    st.error(f"❌ Error importando PartidoModel: {e}")

st.header("7. Resumen")
st.info("""
Si todos los tests pasan ✅, el problema podría ser:
1. Timeout al inicializar los modelos
2. Problema con la base de datos SQLite
3. Error en alguna inicialización

Si algún test falla ❌, ese es el problema a resolver.
""")