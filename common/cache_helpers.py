# common/cache_helpers.py
"""
Funciones de cache compartidas para optimizar rendimiento
Diseñado para 5-8 usuarios simultáneos
"""

import streamlit as st
import pandas as pd
import time
import logging
from models.wyscout_model import WyscoutModel
from models.partido_model import PartidoModel
from models.jugador_model import JugadorModel

# ========================================
# CACHE NIVEL 1: Datos compartidos entre TODOS los usuarios
# ========================================

@st.cache_resource(show_spinner=False)
def get_wyscout_singleton():
    """
    Obtiene la instancia única de WyscoutModel
    Cache a nivel de aplicación - compartido entre TODOS los usuarios
    """
    return WyscoutModel()

@st.cache_data(ttl=3600, show_spinner=False)  # 1 hora
def cargar_datos_wyscout():
    """
    Carga datos de Wyscout con cache compartido
    TODOS los usuarios comparten estos datos
    """
    wyscout_model = get_wyscout_singleton()
    return wyscout_model.get_all_players()

@st.cache_data(ttl=300, show_spinner=False)  # 5 minutos
def cargar_lista_visualizacion():
    """
    Carga lista de visualización con cache
    Se actualiza cada 5 minutos
    """
    try:
        with open('data/lista_visualizacion.json', 'r', encoding='utf-8') as f:
            import json
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"jugadores_seguimiento": []}

# ========================================
# CACHE NIVEL 2: Datos por usuario
# ========================================

@st.cache_data(ttl=180, show_spinner=False)  # 3 minutos
def cargar_informes_usuario(usuario_id):
    """
    Cache individual por usuario para sus informes
    Se actualiza más frecuentemente
    """
    partido_model = PartidoModel()
    return partido_model.obtener_informes_por_usuario(usuario_id)

@st.cache_data(ttl=300, show_spinner=False)  # 5 minutos
def cargar_todos_informes():
    """
    Cache para todos los informes del sistema
    Para vistas administrativas
    """
    partido_model = PartidoModel()
    return partido_model.obtener_todos_informes()

@st.cache_data(ttl=300, show_spinner=False)  # 5 minutos
def cargar_estadisticas_dashboard():
    """
    Cache para estadísticas del dashboard
    """
    partido_model = PartidoModel()
    return partido_model.obtener_estadisticas_dashboard()

# ========================================
# CACHE NIVEL 3: Procesamiento de datos
# ========================================

@st.cache_data(ttl=1800, show_spinner=False)  # 30 minutos
def procesar_jugadores_sub23(df_wyscout):
    """
    Procesa y filtra jugadores Sub-23
    Cache de procesamiento para evitar recálculos
    """
    if df_wyscout.empty or 'edad' not in df_wyscout.columns:
        return pd.DataFrame()
    
    # Filtrar Sub-23
    sub23 = df_wyscout[
        (df_wyscout['edad'] <= 22) & 
        (df_wyscout['edad'].notna())
    ].copy()
    
    return sub23

@st.cache_data(ttl=1800, show_spinner=False)  # 30 minutos
def obtener_top_performers(df_wyscout, categoria, limite=5):
    """
    Cache para cálculos de top performers
    """
    if df_wyscout.empty:
        return pd.DataFrame()
    
    # Lógica según categoría
    if categoria == 'goleadores':
        return df_wyscout.nlargest(limite, 'goles')
    elif categoria == 'asistentes':
        return df_wyscout.nlargest(limite, 'asistencias')
    # ... más categorías
    
    return pd.DataFrame()

# ========================================
# FUNCIONES DE UTILIDAD
# ========================================

def mostrar_estado_cache():
    """
    Muestra el estado del cache en el sidebar (para debug)
    """
    wyscout_model = get_wyscout_singleton()
    cache_info = wyscout_model.get_cache_info()
    
    if cache_info['cached']:
        remaining_min = cache_info['remaining_seconds'] / 60
        st.sidebar.success(f"✅ Cache activo: {remaining_min:.1f} min restantes")
        st.sidebar.caption(f"Total jugadores: {cache_info['total_players']}")
    else:
        st.sidebar.warning("⏳ Cache no inicializado")

def limpiar_cache_manual():
    """
    Limpia todo el cache manualmente (botón admin)
    """
    # Limpiar cache de Streamlit
    st.cache_data.clear()
    st.cache_resource.clear()
    
    # Forzar recarga de Wyscout
    wyscout_model = get_wyscout_singleton()
    wyscout_model.force_refresh()
    
    st.success("✅ Cache limpiado completamente")
    st.balloons()

# ========================================
# DECORADOR PERSONALIZADO PARA MÉTRICAS
# ========================================

def track_performance(func):
    """
    Decorador para medir tiempos de carga
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start_time
        
        if elapsed > 1.0:  # Si tarda más de 1 segundo
            logging.warning(f"⚠️ {func.__name__} tardó {elapsed:.2f}s")
        
        return result
    return wrapper