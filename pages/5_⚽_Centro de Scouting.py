import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os
import json


# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Imports del sistema
from common.login import LoginManager
from models.partido_model import PartidoModel

# Import del scraper de BeSoccer CORREGIDO
try:
    from utils.besoccer_scraper import obtener_partidos_besoccer, obtener_alineaciones_besoccer, BeSoccerAlineacionesScraper
    BESOCCER_DISPONIBLE = True
    print("✅ BeSoccer scraper CORREGIDO disponible")
except ImportError as e:
    print(f"⚠️ BeSoccer scraper no disponible: {e}")
    BESOCCER_DISPONIBLE = False

# Configuración de la página
st.set_page_config(
    page_title="Centro de Scouting - Scouting Pro",
    page_icon="🎯",
    layout="wide"
)

# CSS mejorado y LIMPIO (mantener igual)
st.markdown("""
<style>
    .stDeployButton { display: none !important; }
    footer { display: none !important; }
    .block-container { padding-top: 1rem; }
    
    /* Header principal */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5em;
    }
    
    .main-header p {
        margin: 0;
        font-size: 1.2em;
    }
    
    /* Cards de partidos LIMPIOS */
    .partido-card {
        border: 1px solid #e1e5e9;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .partido-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    
    .estado-en-vivo {
        background: #dc3545;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    .estado-programado {
        background: #ffc107;
        color: #212529;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    .estado-finalizado {
        background: #6c757d;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: bold;
    }
    
    /* Resultado destacado */
    .resultado-partido {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 12px 20px;
        border-radius: 8px;
        font-weight: bold;
        text-align: center;
        font-size: 1.2em;
    }
    
    /* Formulario de evaluación */
    .eval-form {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 12px;
        border: 2px solid #007bff;
        margin: 2rem 0;
    }
    
    .jugador-seleccionado {
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        text-align: center;
    }
    
    /* Alineaciones MEJORADAS */
    .alineacion-container {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .jugador-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 16px;
        margin: 8px 0;
        background: #f8f9fa;
        border-radius: 8px;
        border: 1px solid #e9ecef;
        transition: all 0.2s ease;
    }
    
    .jugador-item:hover {
        background: #e9ecef;
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .jugador-info {
        flex-grow: 1;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .jugador-foto {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        object-fit: cover;
        border: 2px solid #dee2e6;
    }
    
    .jugador-numero {
        background: #007bff;
        color: white;
        padding: 4px 8px;
        border-radius: 50%;
        font-weight: bold;
        min-width: 24px;
        text-align: center;
        font-size: 0.9em;
    }
    
    .posicion-badge {
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8em;
        font-weight: bold;
        margin: 0 4px;
    }
    
    .pos-portero { background: #ffc107; color: #212529; }
    .pos-defensa { background: #28a745; color: white; }
    .pos-medio { background: #007bff; color: white; }
    .pos-delantero { background: #dc3545; color: white; }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-header h1 { font-size: 1.8em; }
        .main-header p { font-size: 1em; }
        .partido-card { padding: 1rem; }
    }
</style>
""", unsafe_allow_html=True)

# Inicializar LoginManager
login_manager = LoginManager()

# Verificación de login
if not login_manager.is_authenticated():
    login_manager.mostrar_login()
    st.stop()

current_user = login_manager.get_current_user()
partido_model = PartidoModel()

# Header principal
st.markdown(f"""
<div class="main-header">
    <h1>🎯 Centro de Scouting</h1>
    <p>Observación y Evaluación en Tiempo Real</p>
    <div style='background: rgba(255,255,255,0.2); padding: 8px 16px; border-radius: 20px; display: inline-block; margin-top: 10px;'>
        <span style='font-weight: bold;'>👤 {current_user['nombre']} | 🎯 {current_user['rol'].title()}</span>
    </div>
</div>
""", unsafe_allow_html=True)

# ================================
# FUNCIONES AUXILIARES CORREGIDAS
# ================================

def obtener_clase_posicion(posicion):
    """Devuelve la clase CSS según la posición"""
    if not posicion:
        return "pos-medio"
    
    pos_lower = posicion.lower()
    if 'portero' in pos_lower or 'goalkeeper' in pos_lower or 'por' in pos_lower:
        return "pos-portero"
    elif 'defensa' in pos_lower or 'defense' in pos_lower or 'def' in pos_lower:
        return "pos-defensa"
    elif 'medio' in pos_lower or 'mid' in pos_lower or 'med' in pos_lower:
        return "pos-medio"
    elif 'delantero' in pos_lower or 'forward' in pos_lower or 'striker' in pos_lower or 'del' in pos_lower:
        return "pos-delantero"
    else:
        return "pos-medio"

def cargar_lista_visualizacion():
    """Carga la lista de jugadores en seguimiento desde JSON"""
    try:
        with open('data/lista_visualizacion.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"jugadores_seguimiento": []}

def es_jugador_objetivo(nombre_jugador, equipo_jugador):
    """Verifica si un jugador está en nuestra lista de objetivos"""
    lista = cargar_lista_visualizacion()
    
    for jugador in lista.get("jugadores_seguimiento", []):
        if (jugador["jugador"].lower() in nombre_jugador.lower() and 
            jugador["equipo"].lower() in equipo_jugador.lower()):
            return True, jugador
    return False, None

def buscar_alineaciones_automatico(partido):
    """FUNCIÓN CORREGIDA: Busca alineaciones AUTOMÁTICAMENTE al entrar al partido"""
    if not BESOCCER_DISPONIBLE:
        print("❌ BeSoccer no disponible para búsqueda automática")
        return None
    
    # CORREGIR: Usar besoccer_id en lugar de besocrer_id
    besoccer_id = partido.get('besoccer_id')
    if not besoccer_id:
        print(f"❌ No hay besoccer_id en el partido: {partido.keys()}")
        return None
    
    try:
        print(f"🔍 Búsqueda automática de alineaciones para {besoccer_id}")
        resultado = obtener_alineaciones_besoccer(
            besoccer_id,
            partido.get('equipo_local', ''),
            partido.get('equipo_visitante', '')
        )
        
        if resultado and resultado.get('encontrado'):
            # Actualizar datos del partido en session_state
            if 'partido_activo' in st.session_state:
                st.session_state.partido_activo['alineacion_local'] = resultado['alineacion_local']
                st.session_state.partido_activo['alineacion_visitante'] = resultado['alineacion_visitante']
            
            print(f"✅ Alineaciones encontradas automáticamente: {len(resultado['alineacion_local'])} vs {len(resultado['alineacion_visitante'])}")
            return resultado
        else:
            print(f"❌ No se encontraron alineaciones: {resultado.get('mensaje', 'Sin mensaje') if resultado else 'Sin resultado'}")
            return None
    except Exception as e:
        print(f"❌ Error en búsqueda automática: {str(e)}")
        return None

def buscar_alineaciones_manual(partido):
    """FUNCIÓN NUEVA: Búsqueda manual mejorada para el botón"""
    if not BESOCCER_DISPONIBLE:
        st.error("❌ Sistema de scraping no disponible")
        return None
    
    # CORREGIR: Usar besoccer_id en lugar de besocrer_id
    besoccer_id = partido.get('besoccer_id')
    if not besoccer_id:
        st.error("❌ Este partido no tiene ID de BeSoccer válido")
        return None
    
    try:
        print(f"🔍 Búsqueda MANUAL de alineaciones para {besoccer_id}")
        
        # Mostrar progreso
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("🔍 Conectando con BeSoccer...")
        progress_bar.progress(25)
        
        resultado = obtener_alineaciones_besoccer(
            besoccer_id,
            partido.get('equipo_local', ''),
            partido.get('equipo_visitante', '')
        )
        
        progress_bar.progress(75)
        status_text.text("🔍 Procesando alineaciones...")
        
        if resultado and resultado.get('encontrado'):
            # Actualizar datos del partido en session_state
            if 'partido_activo' in st.session_state:
                st.session_state.partido_activo['alineacion_local'] = resultado['alineacion_local']
                st.session_state.partido_activo['alineacion_visitante'] = resultado['alineacion_visitante']
            
            progress_bar.progress(100)
            status_text.text("✅ ¡Alineaciones encontradas!")
            
            print(f"✅ Búsqueda manual exitosa: {len(resultado['alineacion_local'])} vs {len(resultado['alineacion_visitante'])}")
            
            # Limpiar progreso después de un momento
            import time
            time.sleep(1)
            progress_bar.empty()
            status_text.empty()
            
            return resultado
        else:
            progress_bar.progress(100)
            error_msg = resultado.get('mensaje', 'Alineaciones no disponibles') if resultado else 'Error desconocido'
            status_text.text(f"❌ {error_msg}")
            
            print(f"❌ Búsqueda manual fallida: {error_msg}")
            
            # Limpiar progreso
            import time
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
            
            return None
            
    except Exception as e:
        st.error(f"❌ Error en búsqueda manual: {str(e)}")
        print(f"❌ Error en búsqueda manual: {str(e)}")
        return None

def cargar_partidos_limpio(fecha_str):
    """FUNCIÓN CORREGIDA: Carga partidos con interface LIMPIA"""
    if not BESOCCER_DISPONIBLE:
        return partido_model.obtener_partidos_por_fecha(fecha_str)
    
    try:
        print(f"🔍 Carga limpia para {fecha_str}")
        
        scraper_livescore = BeSoccerAlineacionesScraper()
        partidos_livescore = scraper_livescore.buscar_partidos_en_fecha(fecha_str)
        
        if not partidos_livescore:
            st.info("📅 No hay partidos disponibles para esta fecha")
            return []
        
        # Convertir con información LIMPIA y CORREGIDA
        partidos_convertidos = []
        
        for p in partidos_livescore:
            partido_convertido = {
                'id': f"livescore_{p['match_id']}",
                'fecha': fecha_str,
                'hora': p.get('hora', 'TBD'),
                'equipo_local': p['equipo_local'],
                'equipo_visitante': p['equipo_visitante'],
                'estado': p.get('estado', 'programado'),
                'escudo_local': p.get('escudo_local', ''),
                'escudo_visitante': p.get('escudo_visitante', ''),
                'besoccer_id': p['match_id'],  # CORREGIDO: besoccer_id
                'resultado_local': p.get('resultado_local'),
                'resultado_visitante': p.get('resultado_visitante'),
                'alineacion_local': [],
                'alineacion_visitante': []
            }
            partidos_convertidos.append(partido_convertido)
        
        print(f"✅ {len(partidos_convertidos)} partidos cargados con interface limpia")
        return partidos_convertidos
        
    except Exception as e:
        st.error(f"❌ Error cargando partidos: {str(e)}")
        return partido_model.obtener_partidos_por_fecha(fecha_str)

# ================================
# ESTADO DE LA APLICACIÓN
# ================================

# Inicializar estados
if 'modo_vista' not in st.session_state:
    st.session_state.modo_vista = 'lista_partidos'
if 'partido_activo' not in st.session_state:
    st.session_state.partido_activo = None
if 'jugador_evaluando' not in st.session_state:
    st.session_state.jugador_evaluando = None
if 'modo_evaluacion' not in st.session_state:
    st.session_state.modo_evaluacion = 'campo'
    
# Nuevo estado para control de alineaciones automáticas
if 'alineaciones_buscadas' not in st.session_state:
    st.session_state.alineaciones_buscadas = False

# ================================
# VISTA: LISTA DE PARTIDOS LIMPIA (mantener igual)
# ================================

if st.session_state.modo_vista == 'lista_partidos':
    
    # Controles superiores
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("🗓️ Partidos")
    
    with col2:
        fecha_seleccionada = st.date_input(
            "Fecha:",
            value=date.today(),
            min_value=date.today() - timedelta(days=7),
            max_value=date.today() + timedelta(days=14)
        )
    
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True):
            st.rerun()
    
    # Cargar partidos LIMPIO
    with st.spinner("🔄 Cargando partidos..."):
        fecha_str = fecha_seleccionada.strftime('%Y-%m-%d')
        partidos = cargar_partidos_limpio(fecha_str)
    
    # Estadísticas rápidas
    if partidos:
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        partidos_en_vivo = len([p for p in partidos if p['estado'] == 'en_vivo'])
        partidos_programados = len([p for p in partidos if p['estado'] == 'programado'])
        partidos_finalizados = len([p for p in partidos if p['estado'] == 'finalizado'])
        
        with col_s1:
            st.metric("📊 Total", len(partidos))
        with col_s2:
            st.metric("🔴 En Vivo", partidos_en_vivo)
        with col_s3:
            st.metric("🟡 Programados", partidos_programados)
        with col_s4:
            st.metric("⚪ Finalizados", partidos_finalizados)
        
        st.markdown("---")
        
        # Lista de partidos LIMPIA
        st.subheader(f"🏟️ {fecha_seleccionada.strftime('%d/%m/%Y')}")
        
        for partido in partidos:
            # Determinar estado LIMPIO
            if partido['estado'] == 'en_vivo':
                estado_clase = "estado-en-vivo"
                estado_texto = "🔴 EN VIVO"
            elif partido['estado'] == 'programado':
                estado_clase = "estado-programado"
                estado_texto = "🟡 PROGRAMADO"
            else:
                estado_clase = "estado-finalizado"
                estado_texto = "⚪ FINALIZADO"
            
            # Card LIMPIO del partido
            st.markdown(f"""
            <div class="partido-card">
                <div class="partido-header">
                    <span class="{estado_clase}">{estado_texto}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Información del enfrentamiento LIMPIA
            col_vs1, col_vs2, col_vs3 = st.columns([3, 2, 3])
            
            with col_vs1:
                if partido.get('escudo_local'):
                    st.markdown(f"""
                    <div style='display: flex; align-items: center; justify-content: center;'>
                        <img src="{partido['escudo_local']}" width="50" style='margin-right: 15px;'>
                        <div>
                            <h3 style='margin: 0;'>{partido['equipo_local']}</h3>
                            <p style='margin: 0; color: gray; font-size: 0.9em;'>🏠 Local</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"### {partido['equipo_local']}")
                    st.caption("🏠 Local")
            
            with col_vs2:
                # Mostrar resultado DESTACADO si está finalizado
                if partido['estado'] == 'finalizado' and partido.get('resultado_local') is not None:
                    st.markdown(f"""
                    <div class="resultado-partido">
                        {partido['resultado_local']} - {partido['resultado_visitante']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("#### VS")
                    if partido.get('hora') and partido['hora'] != 'TBD':
                        st.caption(f"⏰ {partido['hora']}")
            
            with col_vs3:
                if partido.get('escudo_visitante'):
                    st.markdown(f"""
                    <div style='display: flex; align-items: center; justify-content: center;'>
                        <div style='text-align: right; margin-right: 15px;'>
                            <h3 style='margin: 0;'>{partido['equipo_visitante']}</h3>
                            <p style='margin: 0; color: gray; font-size: 0.9em;'>✈️ Visitante</p>
                        </div>
                        <img src="{partido['escudo_visitante']}" width="50">
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"### {partido['equipo_visitante']}")
                    st.caption("✈️ Visitante")
            
            # Solo el botón ESENCIAL
            if st.button(f"🎯 Iniciar Scouting", key=f"scout_{partido['id']}", use_container_width=True, type="primary"):
                st.session_state.partido_activo = partido
                st.session_state.modo_vista = 'observacion'
                st.session_state.alineaciones_buscadas = False  # Reset para nueva búsqueda
                st.rerun()
            
            st.markdown("---")
    
    else:
        st.info(f"📅 No hay partidos para el {fecha_seleccionada.strftime('%d/%m/%Y')}")

# ================================
# VISTA: OBSERVACIÓN ACTIVA - CORREGIDA
# ================================

elif st.session_state.modo_vista == 'observacion':
    
    if not st.session_state.partido_activo:
        st.error("❌ No hay partido activo")
        if st.button("🔙 Volver a partidos", use_container_width=True):
            st.session_state.modo_vista = 'lista_partidos'
            st.rerun()
        st.stop()
    
    partido = st.session_state.partido_activo
    
    # Header LIMPIO del partido activo
    col_h1, col_h2, col_h3 = st.columns([1, 3, 1])
    
    with col_h1:
        if st.button("🔙 Volver", use_container_width=True):
            st.session_state.modo_vista = 'lista_partidos'
            st.session_state.partido_activo = None
            st.session_state.jugador_evaluando = None
            st.session_state.alineaciones_buscadas = False
            st.rerun()
    
    with col_h2:
        st.markdown(f"### 🎯 {partido['equipo_local']} vs {partido['equipo_visitante']}")
        
        # Mostrar información del partido
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            st.write(f"📅 **Fecha:** {partido.get('fecha', 'N/A')}")
            st.write(f"⏰ **Hora:** {partido.get('hora', 'TBD')}")
        with col_info2:
            st.write(f"🏟️ **Estado:** {partido.get('estado', 'programado').upper()}")
            if partido.get('besoccer_id'):
                st.write(f"🆔 **ID BeSoccer:** {partido['besoccer_id']}")
        
        # Resultado si está finalizado
        if partido['estado'] == 'finalizado' and partido.get('resultado_local') is not None:
            st.markdown(f"""
            <div class="resultado-partido" style="margin-top: 10px;">
                ⚽ RESULTADO FINAL: {partido['resultado_local']} - {partido['resultado_visitante']}
            </div>
            """, unsafe_allow_html=True)
        elif partido['estado'] == 'en_vivo':
            st.markdown("🔴 **PARTIDO EN VIVO**")
        else:
            st.markdown("🟡 **PARTIDO PROGRAMADO**")
    
    with col_h3:
        # BOTÓN CORREGIDO de alineaciones
        if st.button("🔍 Buscar Alineaciones", use_container_width=True):
            print("🔍 Botón 'Buscar Alineaciones' presionado")
            with st.spinner("🔍 Buscando alineaciones..."):
                resultado = buscar_alineaciones_manual(partido)
                if resultado and resultado.get('encontrado'):
                    st.success("✅ Alineaciones actualizadas")
                    st.rerun()
                else:
                    st.warning("⚠️ No se pudieron obtener las alineaciones")
    
    st.markdown("---")
    
    # BÚSQUEDA AUTOMÁTICA CORREGIDA de alineaciones al entrar
    if not st.session_state.alineaciones_buscadas and partido.get('besoccer_id'):
        with st.spinner("🔍 Buscando alineaciones automáticamente..."):
            resultado = buscar_alineaciones_automatico(partido)
            st.session_state.alineaciones_buscadas = True
            if resultado and resultado.get('encontrado'):
                st.success("✅ Alineaciones encontradas automáticamente")
                # Mostrar info adicional sobre el resultado
                if 'mensaje' in resultado:
                    st.info(f"ℹ️ {resultado['mensaje']}")
                st.rerun()
            else:
                st.info("💡 Las alineaciones se publican 30-45 minutos antes del partido. Usa el botón 'Buscar Alineaciones' para intentarlo.")
    
    # ================================
    # OBTENER ALINEACIONES - CORREGIDO
    # ================================
    
    alineacion_local = partido.get('alineacion_local', [])
    alineacion_visitante = partido.get('alineacion_visitante', [])
    
    # DEBUG CORREGIDO - Variables definidas correctamente
    if st.sidebar.button("🔧 Debug Info"):
        st.sidebar.write(f"**Local total:** {len(alineacion_local)}")
        st.sidebar.write(f"**Visitante total:** {len(alineacion_visitante)}")
        
        if alineacion_local or alineacion_visitante:
            local_titulares = len([j for j in alineacion_local if j.get('es_titular', True)])
            local_suplentes = len(alineacion_local) - local_titulares
            visitante_titulares = len([j for j in alineacion_visitante if j.get('es_titular', True)])
            visitante_suplentes = len(alineacion_visitante) - visitante_titulares
            
            st.sidebar.write(f"**Local:** {local_titulares}T + {local_suplentes}S")
            st.sidebar.write(f"**Visitante:** {visitante_titulares}T + {visitante_suplentes}S")
    
    # ================================
    # MOSTRAR ALINEACIONES - COMPLETAMENTE CORREGIDO
    # ================================
    
    if alineacion_local or alineacion_visitante:
        
        col_eq1, col_eq2 = st.columns(2)
        
        # ========================================
        # EQUIPO LOCAL - ESTRUCTURA COMPLETAMENTE LIMPIA
        # ========================================
        with col_eq1:
            st.markdown(f"### 🏠 {partido['equipo_local']}")
            
            if alineacion_local:
                # Separar titulares y suplentes
                titulares_local = [j for j in alineacion_local if j.get('es_titular', True)]
                suplentes_local = [j for j in alineacion_local if not j.get('es_titular', True)]
                
                # Si no hay info de titular/suplente, asumir primeros 11
                if not any('es_titular' in j for j in alineacion_local):
                    titulares_local = alineacion_local[:11] if len(alineacion_local) >= 11 else alineacion_local
                    suplentes_local = alineacion_local[11:] if len(alineacion_local) > 11 else []
                
                # ========================================
                # TITULARES LOCAL - HTML COMPLETAMENTE LIMPIO
                # ========================================
                st.markdown("#### ⭐ Titulares")
                
                for i, jugador in enumerate(titulares_local):
                    nombre = jugador.get('nombre', 'Sin nombre')
                    numero = jugador.get('numero', '?')
                    posicion = jugador.get('posicion', 'N/A')
                    imagen_url = jugador.get('imagen_url', '')
                    
                    # Verificar si es objetivo
                    es_objetivo, datos_objetivo = es_jugador_objetivo(nombre, partido['equipo_local'])
                    
                    # Crear imagen del jugador
                    if imagen_url:
                        imagen_html = f'<img src="{imagen_url}" class="jugador-foto" alt="{nombre}">'
                    else:
                        imagen_html = '<div style="width: 40px; height: 40px; border-radius: 50%; background: #e9ecef; display: flex; align-items: center; justify-content: center; font-size: 1.2em;">👤</div>'
                    
                    # Crear el HTML completo en una sola línea
                    objetivo_html = '🎯' if es_objetivo else ''
                    st.markdown(f'<div class="jugador-item"><div class="jugador-info">{imagen_html}<div class="jugador-numero">{numero}</div><strong>{nombre}</strong><span class="posicion-badge {obtener_clase_posicion(posicion)}">{posicion}</span>{objetivo_html}</div></div>', unsafe_allow_html=True)
                    
                    # Botón de evaluación
                    if st.button(f"📝 Evaluar", key=f"eval_local_{i}_{nombre}", use_container_width=True):
                        st.session_state.jugador_evaluando = {
                            'nombre': nombre,
                            'equipo': partido['equipo_local'],
                            'posicion': posicion,
                            'numero': numero,
                            'partido_id': partido['id'],
                            'es_objetivo': es_objetivo,
                            'datos_objetivo': datos_objetivo or {}
                        }
                        st.rerun()
                
                # ========================================
                # SUPLENTES LOCAL - LAYOUT COMPLETAMENTE CORREGIDO
                # ========================================
                if suplentes_local:
                    with st.expander(f"🔄 Suplentes ({len(suplentes_local)})", expanded=False):
                        for i, jugador in enumerate(suplentes_local):
                            nombre = jugador.get('nombre', 'Sin nombre')
                            numero = jugador.get('numero', '?')
                            posicion = jugador.get('posicion', 'N/A')
                            imagen_url = jugador.get('imagen_url', '')
                            
                            # Verificar si es objetivo
                            es_objetivo, datos_objetivo = es_jugador_objetivo(nombre, partido['equipo_local'])
                            
                            # DISEÑO INTEGRADO - Una sola fila sin duplicación
                            cols_suplente = st.columns([4, 1])
                            
                            with cols_suplente[0]:
                                # Crear imagen pequeña
                                if imagen_url:
                                    imagen_mini = f'<img src="{imagen_url}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px;" alt="{nombre}">'
                                else:
                                    imagen_mini = '<div style="width: 30px; height: 30px; border-radius: 50%; background: #e9ecef; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 0.8em;">👤</div>'
                                
                                # Layout integrado - SOLO un número mostrado
                                st.markdown(f"""
                                <div style="display: flex; align-items: center; padding: 8px; background: #f8f9fa; border-radius: 6px; margin: 4px 0;">
                                    {imagen_mini}
                                    <span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 50%; font-size: 0.8em; margin-right: 8px; min-width: 20px; text-align: center;">{numero}</span>
                                    <strong style="margin-right: 8px;">{nombre}</strong>
                                    <span style="padding: 2px 6px; border-radius: 8px; font-size: 0.7em; background: #e9ecef; color: #495057;">{posicion}</span>
                                    {' <span style="margin-left: 8px;">🎯</span>' if es_objetivo else ""}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            with cols_suplente[1]:
                                # Botón simplificado sin número duplicado
                                if st.button("📝", key=f"eval_sup_local_{i}_{nombre}", help=f"Evaluar {nombre}"):
                                    st.session_state.jugador_evaluando = {
                                        'nombre': nombre,
                                        'equipo': partido['equipo_local'],
                                        'posicion': posicion,
                                        'numero': numero,
                                        'partido_id': partido['id'],
                                        'es_objetivo': es_objetivo,
                                        'datos_objetivo': datos_objetivo or {}
                                    }
                                    st.rerun()
            
            else:
                st.warning("⏰ Alineación no disponible")
        
        # ========================================
        # EQUIPO VISITANTE - ESTRUCTURA IDÉNTICA Y LIMPIA
        # ========================================
        with col_eq2:
            st.markdown(f"### ✈️ {partido['equipo_visitante']}")
            
            if alineacion_visitante:
                # Separar titulares y suplentes
                titulares_visitante = [j for j in alineacion_visitante if j.get('es_titular', True)]
                suplentes_visitante = [j for j in alineacion_visitante if not j.get('es_titular', True)]
                
                # Si no hay info de titular/suplente, asumir primeros 11
                if not any('es_titular' in j for j in alineacion_visitante):
                    titulares_visitante = alineacion_visitante[:11] if len(alineacion_visitante) >= 11 else alineacion_visitante
                    suplentes_visitante = alineacion_visitante[11:] if len(alineacion_visitante) > 11 else []
                
                # ========================================
                # TITULARES VISITANTE - HTML COMPLETAMENTE LIMPIO
                # ========================================
                st.markdown("#### ⭐ Titulares")
                
                for i, jugador in enumerate(titulares_visitante):
                    nombre = jugador.get('nombre', 'Sin nombre')
                    numero = jugador.get('numero', '?')
                    posicion = jugador.get('posicion', 'N/A')
                    imagen_url = jugador.get('imagen_url', '')
                    
                    # Verificar si es objetivo
                    es_objetivo, datos_objetivo = es_jugador_objetivo(nombre, partido['equipo_visitante'])
                    
                    # Crear imagen del jugador
                    if imagen_url:
                        imagen_html = f'<img src="{imagen_url}" class="jugador-foto" alt="{nombre}">'
                    else:
                        imagen_html = '<div style="width: 40px; height: 40px; border-radius: 50%; background: #e9ecef; display: flex; align-items: center; justify-content: center; font-size: 1.2em;">👤</div>'
                    
                    # Crear el HTML completo en una sola línea
                    objetivo_html = '🎯' if es_objetivo else ''
                    st.markdown(f'<div class="jugador-item"><div class="jugador-info">{imagen_html}<div class="jugador-numero">{numero}</div><strong>{nombre}</strong><span class="posicion-badge {obtener_clase_posicion(posicion)}">{posicion}</span>{objetivo_html}</div></div>', unsafe_allow_html=True)
                    
                    # Botón de evaluación
                    if st.button(f"📝 Evaluar", key=f"eval_visitante_{i}_{nombre}", use_container_width=True):
                        st.session_state.jugador_evaluando = {
                            'nombre': nombre,
                            'equipo': partido['equipo_visitante'],
                            'posicion': posicion,
                            'numero': numero,
                            'partido_id': partido['id'],
                            'es_objetivo': es_objetivo,
                            'datos_objetivo': datos_objetivo or {}
                        }
                        st.rerun()
                
                # ========================================
                # SUPLENTES VISITANTE - LAYOUT COMPLETAMENTE CORREGIDO
                # ========================================
                if suplentes_visitante:
                    with st.expander(f"🔄 Suplentes ({len(suplentes_visitante)})", expanded=False):
                        for i, jugador in enumerate(suplentes_visitante):
                            nombre = jugador.get('nombre', 'Sin nombre')
                            numero = jugador.get('numero', '?')
                            posicion = jugador.get('posicion', 'N/A')
                            imagen_url = jugador.get('imagen_url', '')
                            
                            # Verificar si es objetivo
                            es_objetivo, datos_objetivo = es_jugador_objetivo(nombre, partido['equipo_visitante'])
                            
                            # DISEÑO INTEGRADO - Una sola fila sin duplicación
                            cols_suplente = st.columns([4, 1])
                            
                            with cols_suplente[0]:
                                # Crear imagen pequeña
                                if imagen_url:
                                    imagen_mini = f'<img src="{imagen_url}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px;" alt="{nombre}">'
                                else:
                                    imagen_mini = '<div style="width: 30px; height: 30px; border-radius: 50%; background: #e9ecef; display: inline-flex; align-items: center; justify-content: center; margin-right: 10px; font-size: 0.8em;">👤</div>'
                                
                                # Layout integrado - SOLO un número mostrado
                                st.markdown(f"""
                                <div style="display: flex; align-items: center; padding: 8px; background: #f8f9fa; border-radius: 6px; margin: 4px 0;">
                                    {imagen_mini}
                                    <span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 50%; font-size: 0.8em; margin-right: 8px; min-width: 20px; text-align: center;">{numero}</span>
                                    <strong style="margin-right: 8px;">{nombre}</strong>
                                    <span style="padding: 2px 6px; border-radius: 8px; font-size: 0.7em; background: #e9ecef; color: #495057;">{posicion}</span>
                                    {' <span style="margin-left: 8px;">🎯</span>' if es_objetivo else ""}
                                </div
                                """,unsafe_allow_html=True)
                            
                            with cols_suplente[1]:
                                # Botón simplificado sin número duplicado
                                if st.button("📝", key=f"eval_sup_visitante_{i}_{nombre}", help=f"Evaluar {nombre}"):
                                    st.session_state.jugador_evaluando = {
                                        'nombre': nombre,
                                        'equipo': partido['equipo_visitante'],
                                        'posicion': posicion,
                                        'numero': numero,
                                        'partido_id': partido['id'],
                                        'es_objetivo': es_objetivo,
                                        'datos_objetivo': datos_objetivo or {}
                                    }
                                    st.rerun()
            
            else:
                st.warning("⏰ Alineación no disponible")
    
    else:
        st.info("⏰ **Alineaciones no disponibles**")
        if partido.get('besoccer_id'):
            st.write("💡 Las alineaciones se publican 30-45 minutos antes del partido.")
            st.write("🔍 Usa el botón 'Buscar Alineaciones' para intentar obtenerlas.")
        else:
            st.warning("⚠️ Partido sin ID de BeSoccer - Las alineaciones pueden no estar disponibles")
    
    # ================================
    # FORMULARIO DE EVALUACIÓN (mantener igual)
    # ================================
    
    if st.session_state.jugador_evaluando:
        player = st.session_state.jugador_evaluando
        
        st.markdown('<div class="eval-form">', unsafe_allow_html=True)
        
        # Header del jugador seleccionado
        st.markdown(f"""
        <div class="jugador-seleccionado">
            <h3>📝 Evaluando: {player['nombre']}</h3>
            <p>{player['equipo']} • {player['posicion']} • #{player['numero']}</p>
            {f"<p>🎯 Jugador Objetivo</p>" if player['es_objetivo'] else ""}
        </div>
        """, unsafe_allow_html=True)
        
        # Selector de modo de evaluación
        col_mode1, col_mode2, col_mode3 = st.columns([1, 1, 1])
        
        with col_mode1:
            if st.button("🏟️ Modo Campo", use_container_width=True, 
                        type="primary" if st.session_state.modo_evaluacion == 'campo' else "secondary"):
                st.session_state.modo_evaluacion = 'campo'
                st.rerun()
        
        with col_mode2:
            if st.button("🎥 Modo Completo", use_container_width=True,
                        type="primary" if st.session_state.modo_evaluacion == 'completo' else "secondary"):
                st.session_state.modo_evaluacion = 'completo'
                st.rerun()
        
        with col_mode3:
            if st.button("❌ Cancelar", use_container_width=True):
                st.session_state.jugador_evaluando = None
                st.rerun()
        
        # FORMULARIO SEGÚN MODO (mantener igual)
        with st.form("evaluacion_jugador", clear_on_submit=False):
            
            if st.session_state.modo_evaluacion == 'campo':
                st.markdown("#### 🏟️ Evaluación Rápida en Campo")
                st.info("💡 Ideal para observación en vivo - Solo aspectos esenciales")
                
                col_eval1, col_eval2 = st.columns(2)
                
                with col_eval1:
                    nota_general = st.slider("🌟 Nota General", 1, 10, 5, help="Evaluación global del rendimiento")
                    
                    # Aspectos principales según posición
                    if 'portero' in player['posicion'].lower():
                        aspecto1 = st.slider("🥅 Paradas/Reflejos", 1, 10, 5)
                        aspecto2 = st.slider("🦶 Juego con pies", 1, 10, 5)
                        aspecto3 = st.slider("📢 Comunicación", 1, 10, 5)
                    elif 'defensa' in player['posicion'].lower():
                        aspecto1 = st.slider("🛡️ Marcaje/Duelos", 1, 10, 5)
                        aspecto2 = st.slider("⚽ Pase/Salida balón", 1, 10, 5)
                        aspecto3 = st.slider("🧠 Posicionamiento", 1, 10, 5)
                    elif 'medio' in player['posicion'].lower():
                        aspecto1 = st.slider("⚽ Pase/Distribución", 1, 10, 5)
                        aspecto2 = st.slider("🧠 Visión de juego", 1, 10, 5)
                        aspecto3 = st.slider("💪 Físico/Duelos", 1, 10, 5)
                    else:  # Delantero
                        aspecto1 = st.slider("🎯 Finalización", 1, 10, 5)
                        aspecto2 = st.slider("🏃 Desmarque/Movilidad", 1, 10, 5)
                        aspecto3 = st.slider("⚽ Técnica/Primer toque", 1, 10, 5)
                
                with col_eval2:
                    potencial = st.selectbox("📈 Potencial", ["Bajo", "Medio", "Alto", "Muy Alto"], index=1)
                    recomendacion = st.selectbox("💼 Recomendación", 
                                               ["Descartar", "Seguir observando", "Interés moderado", "Contratar"], 
                                               index=1)
                    minutos_jugados = st.number_input("⚽ Minutos jugados", min_value=1, max_value=120, value=45)
                
                # Campo de observaciones amplio
                observaciones = st.text_area("💭 Observaciones", 
                                           placeholder="Acciones destacadas, fortalezas observadas, debilidades detectadas...",
                                           height=120)
            
            else:  # Modo completo (mantener igual)
                st.markdown("#### 🎥 Evaluación Completa")
                st.info("💡 Para análisis posterior detallado")
                
                nota_general = st.slider("🌟 Nota General", 1, 10, 5)
                potencial = st.selectbox("📈 Potencial", ["Bajo", "Medio", "Alto", "Muy Alto"], index=1)
                recomendacion = st.selectbox("💼 Recomendación", 
                                           ["Descartar", "Seguir observando", "Interés moderado", "Contratar"], 
                                           index=1)
                minutos_jugados = st.number_input("⚽ Minutos jugados", min_value=1, max_value=120, value=45)
                observaciones = st.text_area("💭 Observaciones detalladas", 
                                           placeholder="Análisis completo del rendimiento...",
                                           height=100)
                
                # Para modo completo, usar valores por defecto
                aspecto1 = aspecto2 = aspecto3 = 5
            
            # Botones de envío
            col_submit1, col_submit2 = st.columns(2)
            
            with col_submit1:
                submitted = st.form_submit_button("💾 Guardar Informe", use_container_width=True, type="primary")
            
            with col_submit2:
                continuar = st.form_submit_button("➡️ Guardar y Continuar", use_container_width=True)
        
        # Procesar envío del formulario (mantener igual)
        if submitted or continuar:
            try:
                informe_data = {
                    'partido_id': player['partido_id'],
                    'jugador_nombre': player['nombre'],
                    'equipo': player['equipo'],
                    'posicion': player['posicion'],
                    'scout_usuario': current_user['usuario'],
                    'nota_general': nota_general,
                    'potencial': potencial.lower(),
                    'recomendacion': recomendacion.lower().replace(' ', '_'),
                    'observaciones': observaciones,
                    'minutos_observados': minutos_jugados,
                    'fortalezas': f"Evaluación {st.session_state.modo_evaluacion}. Aspectos: {aspecto1}/10, {aspecto2}/10, {aspecto3}/10",
                    'debilidades': f"Modo: {st.session_state.modo_evaluacion}. {observaciones[:100] if observaciones else 'Sin observaciones adicionales'}"
                }
                
                informe_id = partido_model.crear_informe_scouting(informe_data)
                
                st.success(f"✅ **Informe guardado exitosamente!** (ID: {informe_id})")
                st.success(f"🎯 **Jugador:** {player['nombre']} | **Nota:** {nota_general}/10 | **Recomendación:** {recomendacion}")
                
                if continuar:
                    st.session_state.jugador_evaluando = None
                    st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error al guardar el informe: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)

# ================================
# SIDEBAR (simplificado)
# ================================

with st.sidebar:
    st.markdown("### 🎯 Centro de Scouting")
    st.write(f"**Scout:** {current_user['nombre']}")
    st.write(f"**Rol:** {current_user['rol'].title()}")
    
    st.markdown("---")
    
    # Información del estado actual
    if st.session_state.modo_vista == 'lista_partidos':
        st.info("📋 **Seleccionando partido**")
    else:
        st.success("🎯 **Scouting activo**")
        if st.session_state.partido_activo:
            partido = st.session_state.partido_activo
            st.write(f"**Partido:** {partido['equipo_local']} vs {partido['equipo_visitante']}")
            
            if st.session_state.jugador_evaluando:
                player = st.session_state.jugador_evaluando
                st.write(f"**Evaluando:** {player['nombre']}")
    
    st.markdown("---")
    
    # Estadísticas del scout
    st.markdown("#### 📊 Mis Estadísticas")
    try:
        informes_totales = len(partido_model.obtener_informes_por_usuario(current_user['usuario']))
        st.metric("Informes Creados", informes_totales)
    except:
        st.metric("Informes Creados", 0)
    
    st.markdown("---")
    
    # Navegación
    if st.button("📊 Dashboard", use_container_width=True):
        st.switch_page("pages/1_🔍_Jugadores.py")
    
    if st.button("📋 Mis Informes", use_container_width=True):
        st.switch_page("pages/9_📋_Mis_Informes.py")
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        login_manager.logout()

# Footer LIMPIO
st.markdown("---")
st.markdown("""
<div style='text-align: center; padding: 15px; background: #f8f9fa; border-radius: 10px; margin-top: 20px;'>
    <h4 style='color: #495057; margin-bottom: 8px;'>🎯 Centro de Scouting Profesional</h4>
    <p style='color: #6c757d; margin: 0; font-size: 0.9em;'>
        Interface limpia • Búsqueda automática • Evaluación profesional
    </p>
</div>
""", unsafe_allow_html=True)