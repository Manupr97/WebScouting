# utils/monitor_performance.py
"""
Monitor de rendimiento para el sistema de scouting
Útil para verificar que las optimizaciones funcionan
"""

import streamlit as st
import time
import psutil
import os
from common.cache_helpers import get_wyscout_singleton

def mostrar_metricas_rendimiento():
    """
    Muestra métricas de rendimiento en el sidebar
    Solo para modo desarrollo/admin
    """
    # Información del proceso
    process = psutil.Process(os.getpid())
    memoria_mb = process.memory_info().rss / 1024 / 1024
    
    # Información del cache
    wyscout_model = get_wyscout_singleton()
    cache_info = wyscout_model.get_cache_info()
    
    # Mostrar en sidebar
    with st.sidebar.expander("🔧 Monitor de Rendimiento", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("💾 RAM", f"{memoria_mb:.1f} MB")
            st.metric("⏱️ Cache", "Activo" if cache_info['cached'] else "Inactivo")
        
        with col2:
            if cache_info['cached']:
                tiempo_restante = cache_info['remaining_seconds'] / 60
                st.metric("⏰ Expira en", f"{tiempo_restante:.1f} min")
                st.metric("📊 Jugadores", cache_info['total_players'])
        
        # Botón para limpiar cache (solo admin)
        if st.button("🔄 Forzar Recarga", use_container_width=True):
            wyscout_model.force_refresh()
            st.rerun()

def log_tiempo_carga(funcion_nombre, tiempo_inicio):
    """
    Registra tiempos de carga en desarrollo
    """
    tiempo_total = time.time() - tiempo_inicio
    
    if tiempo_total > 1.0:  # Si tarda más de 1 segundo
        st.warning(f"⚠️ {funcion_nombre} tardó {tiempo_total:.2f} segundos")
    
    # Log para desarrollo
    import logging
    logging.info(f"⏱️ {funcion_nombre}: {tiempo_total:.3f}s")

# Uso en páginas:
# from utils.monitor_performance import mostrar_metricas_rendimiento
# if current_user['rol'] == 'admin':
#     mostrar_metricas_rendimiento()