import streamlit as st
import pandas as pd
import numpy as np
import sys
import os

try:
    st.set_page_config(page_title="Web Scouting", layout="wide")

    st.write("✅ Arranque de Streamlit exitoso")

    if "usuario" not in st.session_state:
        st.warning("Esperando autenticación")
        st.stop()

except Exception as e:
    st.error(f"❌ Error crítico al arrancar la app: {e}")
    st.stop()

# Configuración de la página
st.set_page_config(
    page_title="WebScouting - Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Agregar path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Intentar imports con manejo de errores
try:
    from common.login import LoginManager
    from models.wyscout_model import WyscoutModel
    from models.partido_model import PartidoModel
    login_ok = True
except ImportError as e:
    st.error(f"Error al importar módulos: {e}")
    login_ok = False

# CSS básico
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        padding: 2rem;
        background: linear-gradient(90deg, #f0f0f0 0%, #ffffff 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Función principal
def main():
    if not login_ok:
        st.error("No se pudieron cargar los módulos necesarios")
        return
    
    # Inicializar login
    login_manager = LoginManager()
    
    # Verificar autenticación
    if not login_manager.is_authenticated():
        st.markdown('<h1 class="main-header">⚽ WebScouting</h1>', unsafe_allow_html=True)
        login_manager.mostrar_login()
    else:
        # Usuario autenticado
        user = login_manager.get_current_user()
        
        # Sidebar
        with st.sidebar:
            st.markdown(f"### 👤 {user['nombre']}")
            st.markdown(f"*{user['rol'].title()}*")
            
            st.markdown("---")
            
            if st.button("🔍 Buscar Jugadores", use_container_width=True):
                st.switch_page("pages/1_🔍_Jugadores.py")
            
            if st.button("📊 Visualizaciones", use_container_width=True):
                st.switch_page("pages/3_📊_Visualizaciones.py")
            
            if st.button("📋 Base de Datos", use_container_width=True):
                st.switch_page("pages/2_📊_Bases_Datos_Unificadas.py")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                login_manager.logout()
        
        # Contenido principal
        st.markdown('<h1 class="main-header">⚽ WebScouting Dashboard</h1>', unsafe_allow_html=True)
        
        # Cargar datos
        try:
            wyscout_model = WyscoutModel()
            df = wyscout_model.get_all_players()
            
            # Métricas básicas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("👥 Total Jugadores", len(df))
            
            with col2:
                if 'equipo_durante_el_período_seleccionado' in df.columns:
                    st.metric("🏟️ Equipos", df['equipo_durante_el_período_seleccionado'].nunique())
                else:
                    st.metric("🏟️ Equipos", "N/A")
            
            with col3:
                if 'edad' in df.columns:
                    st.metric("🎂 Edad Media", f"{df['edad'].mean():.1f}")
                else:
                    st.metric("🎂 Edad Media", "N/A")
            
            with col4:
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                st.metric("📊 Métricas", len(numeric_cols))
            
            st.markdown("---")
            
            # Información básica
            st.info("""
            ### 🎯 Bienvenido a WebScouting
            
            Sistema profesional de análisis y scouting de fútbol con datos de LaLiga.
            
            **Funcionalidades disponibles:**
            - 🔍 Búsqueda y filtrado de jugadores
            - 📊 Visualizaciones interactivas
            - 📋 Base de datos completa
            - ⚽ Centro de scouting
            - 📝 Gestión de informes
            """)
            
        except Exception as e:
            st.error(f"Error al cargar datos: {str(e)}")
            st.info("Por favor, verifica que el archivo de datos esté disponible.")

if __name__ == "__main__":
    main()