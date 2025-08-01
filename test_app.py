import streamlit as st
import sys
import os
import traceback

st.set_page_config(page_title="Trace Error", page_icon="🔍")

st.title("🔍 Rastreando el Error")

# Log cada paso
steps = []

try:
    steps.append("1. Iniciando imports...")
    
    # Import pandas
    steps.append("2. Importando pandas...")
    import pandas as pd
    steps.append("✅ pandas OK")
    
    # Agregar path
    steps.append("3. Configurando path...")
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    steps.append(f"✅ Path: {os.getcwd()}")
    
    # Import LoginManager
    steps.append("4. Importando LoginManager...")
    from common.login import LoginManager
    steps.append("✅ LoginManager importado")
    
    # Crear instancia de LoginManager
    steps.append("5. Creando LoginManager...")
    login_manager = LoginManager()
    steps.append("✅ LoginManager creado")
    
    # Import WyscoutModel
    steps.append("6. Importando WyscoutModel...")
    from models.wyscout_model import WyscoutModel
    steps.append("✅ WyscoutModel importado")
    
    # Crear instancia de WyscoutModel
    steps.append("7. Creando WyscoutModel...")
    wyscout_model = WyscoutModel()
    steps.append("✅ WyscoutModel creado")
    
    # Import PartidoModel
    steps.append("8. Importando PartidoModel...")
    from models.partido_model import PartidoModel
    steps.append("✅ PartidoModel importado")
    
    # Crear instancia de PartidoModel
    steps.append("9. Creando PartidoModel...")
    partido_model = PartidoModel()
    steps.append("✅ PartidoModel creado")
    
    # Verificar autenticación
    steps.append("10. Verificando autenticación...")
    is_auth = login_manager.is_authenticated()
    steps.append(f"✅ Autenticado: {is_auth}")
    
    # Si llegamos aquí, todo está bien
    steps.append("✅ TODO OK - No hay errores de inicialización")
    
    # Mostrar formulario de login si no está autenticado
    if not is_auth:
        steps.append("11. Mostrando login...")
        login_manager.mostrar_login()
        steps.append("✅ Login mostrado")
    else:
        steps.append("11. Usuario ya autenticado")
        user = login_manager.get_current_user()
        st.success(f"Bienvenido {user['nombre']}")
    
except Exception as e:
    steps.append(f"❌ ERROR: {str(e)}")
    steps.append(f"Tipo: {type(e).__name__}")
    steps.append("Traceback completo:")
    steps.append(traceback.format_exc())

# Mostrar todos los pasos
st.header("Registro de Ejecución:")
for step in steps:
    if "✅" in step:
        st.success(step)
    elif "❌" in step:
        st.error(step)
    else:
        st.info(step)

# Info adicional
st.header("Información del Sistema:")
col1, col2 = st.columns(2)
with col1:
    st.info(f"Python: {sys.version}")
    st.info(f"CWD: {os.getcwd()}")
with col2:
    st.info(f"Streamlit: {st.__version__}")
    st.info(f"Archivos en data: {len(os.listdir('data')) if os.path.exists('data') else 'No existe'}")