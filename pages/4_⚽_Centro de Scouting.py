import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import sys
import os
import json
import time

# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Imports del sistema
from common.login import LoginManager
from models.partido_model import PartidoModel

partido_model = PartidoModel()

# Import del scraper de BeSoccer CORREGIDO
try:
    from utils.besoccer_scraper import obtener_partidos_besoccer, obtener_alineaciones_besoccer, BeSoccerAlineacionesScraper
    BESOCCER_DISPONIBLE = True
    print("✅ BeSoccer scraper CORREGIDO disponible")
except ImportError as e:
    print(f"⚠️ BeSoccer scraper no disponible: {e}")
    BESOCCER_DISPONIBLE = False

# Después de los otros imports, añadir:
try:
    from utils.db_helpers import actualizar_jugador_desde_scraper, procesar_alineaciones_completas
    DB_HELPERS_DISPONIBLE = True
    print("✅ DB Helpers disponible")
except ImportError as e:
    print(f"⚠️ DB Helpers no disponible: {e}")
    DB_HELPERS_DISPONIBLE = False

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
    
    /* Formulario más compacto */
    .eval-form {
        background: #f8f9fa;
        padding: 1.5rem;  /* Reducido de 2rem */
        border-radius: 10px;
        border: 1px solid #dee2e6;  /* Borde más sutil */
        margin: 1rem 0;  /* Menos margen */
    }
            
    /* Métricas más compactas */
    [data-testid="metric-container"] {
        padding: 0.5rem;
    }
            
    /* Expanders más compactos */
    .streamlit-expanderHeader {
        font-size: 0.95em;
        padding: 0.5rem;
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
print(f"DEBUG Centro Scouting - current_user: {current_user}")

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
    
    besoccer_id = partido.get('besoccer_id')
    if not besoccer_id:
        print(f"❌ No hay besoccer_id en el partido: {partido.keys()}")
        return None
    
    try:
        print(f"🔍 Búsqueda automática de alineaciones para {besoccer_id}")
        resultado = obtener_alineaciones_besoccer(
            besoccer_id,
            partido.get('equipo_local', ''),
            partido.get('equipo_visitante', ''),
            fecha_partido=partido.get('fecha')
        )
        
        if resultado and resultado.get('encontrado'):
            # Actualizar datos del partido en session_state
            if 'partido_activo' in st.session_state:
                st.session_state.partido_activo['alineacion_local'] = resultado['alineacion_local']
                st.session_state.partido_activo['alineacion_visitante'] = resultado['alineacion_visitante']
            
            print(f"✅ Alineaciones encontradas automáticamente: {len(resultado['alineacion_local'])} vs {len(resultado['alineacion_visitante'])}")
            
            # ELIMINADO: Ya NO procesamos jugadores automáticamente
            # Solo mostramos las alineaciones
            
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
            partido.get('equipo_visitante', ''),
            fecha_partido=partido.get('fecha')
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
            
            # ELIMINADO: Ya NO procesamos jugadores automáticamente
            
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
    """FUNCIÓN CORREGIDA: Carga partidos con interface LIMPIA - SIN CACHE DE SESSION STATE"""
    if not BESOCCER_DISPONIBLE:
        return partido_model.obtener_partidos_por_fecha(fecha_str)
    
    try:
        print(f"🔍 Carga limpia para {fecha_str}")
        
        # IMPORTANTE: No usar cache de session state, siempre buscar nuevos
        scraper_livescore = BeSoccerAlineacionesScraper()
        partidos_livescore = scraper_livescore.buscar_partidos_en_fecha(fecha_str)
        
        if not partidos_livescore:
            st.info("📅 No hay partidos disponibles para esta fecha")
            return []
        
        # Convertir con información LIMPIA y CORREGIDA
        partidos_convertidos = []
        
        for p in partidos_livescore:
            partido_convertido = {
                'id': f"livescore_{p['match_id']}_{fecha_str}",  # Añadir fecha al ID para evitar cache
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
# FUNCIONES DEL FORMULARIO DE CAMPO
# ================================

def mostrar_formulario_evaluacion_campo(player, partido):
    """
    Muestra el formulario de evaluación rápida para uso durante el partido
    """
    
    # Inicializar estados si no existen
    if 'acciones_partido' not in st.session_state:
        st.session_state.acciones_partido = {
            'positivas': 0,
            'neutras': 0,
            'negativas': 0,
            'eventos': []
        }
    
    if 'evaluacion_temporal' not in st.session_state:
        st.session_state.evaluacion_temporal = {}
    
    st.markdown('<div class="eval-form">', unsafe_allow_html=True)
    
    # Header compacto del jugador con selector de posición
    col_info1, col_info2 = st.columns([2, 1])
    
    with col_info1:
        st.markdown(f"""
        <div class="jugador-seleccionado">
            <h3 style="margin: 0;">📝 {player['nombre']} (#{player['numero']})</h3>
            <p style="margin: 0;">{player['equipo']} {' • 🎯 Objetivo' if player['es_objetivo'] else ''}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        # Selector de posición REAL en el partido
        posiciones = [
            'Portero', 'Central', 'Lateral Derecho', 'Lateral Izquierdo',
            'Mediocentro Defensivo', 'Mediocentro', 'Media Punta',
            'Extremo Derecho', 'Extremo Izquierdo', 'Delantero'
        ]
        
        # Intentar preseleccionar basado en posición de BeSoccer
        posicion_besoccer = player.get('posicion', 'Mediocentro')
        try:
            index_default = next(i for i, p in enumerate(posiciones) 
                               if posicion_besoccer.lower() in p.lower())
        except:
            index_default = 5  # Mediocentro por defecto
        
        posicion_real = st.selectbox(
            "📍 Posición real:",
            posiciones,
            index=index_default,
            key=f"posicion_real_{player['nombre']}"
        )
        
        # Guardar la posición seleccionada
        st.session_state.evaluacion_temporal['posicion_real'] = posicion_real
    
    st.markdown("---")
    
    # SECCIÓN 1: CAPTURA RÁPIDA MEJORADA
    st.subheader("⚡ Registro de Acciones")
    
    # Primero el minuto y la nota
    col_minuto, col_nota = st.columns([1, 3])
    
    with col_minuto:
        minuto_actual = st.number_input(
            "⏱️ Min:",
            min_value=1,
            max_value=120,
            value=st.session_state.get('minuto_actual', 1),
            key="input_minuto",
            step=1
        )
        st.session_state.minuto_actual = minuto_actual
    
    with col_nota:
        nota_rapida = st.text_input(
            "💭 Descripción (opcional):",
            placeholder="Ej: Gran pase entre líneas, Fallo en el marcaje...",
            key="nota_rapida"
        )
    
    # Luego los botones de acción
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("✅ POSITIVA", key="btn_positivo", use_container_width=True, type="primary"):
            st.session_state.acciones_partido['positivas'] += 1
            evento = {
                'minuto': minuto_actual,
                'tipo': 'positivo',
                'nota': nota_rapida if nota_rapida else 'Acción positiva'
            }
            st.session_state.acciones_partido['eventos'].append(evento)
            st.success(f"✅ Min {minuto_actual}: {evento['nota']}")
            
    
    with col_btn2:
        if st.button("➖ NEUTRA", key="btn_neutro", use_container_width=True):
            st.session_state.acciones_partido['neutras'] += 1
            evento = {
                'minuto': minuto_actual,
                'tipo': 'neutro',
                'nota': nota_rapida if nota_rapida else 'Acción neutra'
            }
            st.session_state.acciones_partido['eventos'].append(evento)
            st.info(f"➖ Min {minuto_actual}: {evento['nota']}")
            
    
    with col_btn3:
        if st.button("❌ NEGATIVA", key="btn_negativo", use_container_width=True):
            st.session_state.acciones_partido['negativas'] += 1
            evento = {
                'minuto': minuto_actual,
                'tipo': 'negativo',
                'nota': nota_rapida if nota_rapida else 'Acción negativa'
            }
            st.session_state.acciones_partido['eventos'].append(evento)
            st.error(f"❌ Min {minuto_actual}: {evento['nota']}")
            
    
    # SECCIÓN 2: RESUMEN COMPACTO
    st.markdown("### 📊 Resumen")
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    
    with col_stats1:
        total = (st.session_state.acciones_partido['positivas'] + 
                st.session_state.acciones_partido['neutras'] + 
                st.session_state.acciones_partido['negativas'])
        st.metric("Total", total)
    
    with col_stats2:
        st.metric("✅ Positivas", st.session_state.acciones_partido['positivas'], 
                 delta=f"{st.session_state.acciones_partido['positivas']}/{total}" if total > 0 else "0")
    
    with col_stats3:
        st.metric("➖ Neutras", st.session_state.acciones_partido['neutras'])
    
    with col_stats4:
        st.metric("❌ Negativas", st.session_state.acciones_partido['negativas'],
                 delta=f"-{st.session_state.acciones_partido['negativas']}/{total}" if total > 0 else "0")
    
    # SECCIÓN 3: EVALUACIÓN RÁPIDA (Más compacta)
    with st.expander("📋 Evaluación Detallada (pausas/descanso)", expanded=False):
        
        # Nota general en la misma línea
        col_nota1, col_nota2 = st.columns([1, 3])
        with col_nota1:
            nota_general = st.number_input(
                "🌟 Nota General",
                min_value=1,
                max_value=10,
                value=st.session_state.evaluacion_temporal.get('nota_general', 5),
                key="nota_general_campo"
            )
            st.session_state.evaluacion_temporal['nota_general'] = nota_general
        
        with col_nota2:
            st.info("💡 Completa los aspectos específicos durante las pausas del partido")
        
        # Aspectos según posición en grid de 2 columnas
        st.markdown("**Aspectos específicos:**")
        
        aspectos_por_posicion = {
            'Portero': {
                'Paradas y reflejos': 5,
                'Juego con pies': 5,
                'Salidas': 5,
                'Comunicación': 5
            },
            'Central': {
                'Marcaje': 5,
                'Juego aéreo': 5,
                'Salida de balón': 5,
                'Posicionamiento': 5
            },
            'Lateral Derecho': {
                'Defensa 1v1': 5,
                'Apoyo ofensivo': 5,
                'Centros': 5,
                'Físico': 5
            },
            'Lateral Izquierdo': {
                'Defensa 1v1': 5,
                'Apoyo ofensivo': 5,
                'Centros': 5,
                'Físico': 5
            },
            'Mediocentro Defensivo': {
                'Recuperación': 5,
                'Distribución': 5,
                'Posicionamiento': 5,
                'Duelos': 5
            },
            'Mediocentro': {
                'Pase': 5,
                'Visión de juego': 5,
                'Recuperación': 5,
                'Llegada': 5
            },
            'Media Punta': {
                'Creatividad': 5,
                'Último pase': 5,
                'Finalización': 5,
                'Movilidad': 5
            },
            'Extremo Derecho': {
                'Regate': 5,
                'Velocidad': 5,
                'Centros': 5,
                'Finalización': 5
            },
            'Extremo Izquierdo': {
                'Regate': 5,
                'Velocidad': 5,
                'Centros': 5,
                'Finalización': 5
            },
            'Delantero': {
                'Finalización': 5,
                'Desmarques': 5,
                'Juego aéreo': 5,
                'Pressing': 5
            }
        }
        
        aspectos = aspectos_por_posicion.get(posicion_real, aspectos_por_posicion['Mediocentro'])
        
        # Crear grid de 2 columnas para aspectos
        cols = st.columns(2)
        for i, (aspecto, valor_default) in enumerate(aspectos.items()):
            with cols[i % 2]:
                valor = st.slider(
                    f"{aspecto}",
                    min_value=1,
                    max_value=10,
                    value=st.session_state.evaluacion_temporal.get(f'aspecto_{aspecto}', valor_default),
                    key=f"slider_{aspecto}"
                )
                st.session_state.evaluacion_temporal[f'aspecto_{aspecto}'] = valor
        
        # Observaciones
        st.markdown("**Observaciones:**")
        obs_general = st.text_area(
            "Notas generales:",
            value=st.session_state.evaluacion_temporal.get('obs_general', ''),
            placeholder="Aspectos destacados, evolución durante el partido, etc...",
            height=80,
            key="obs_general_campo"
        )
        st.session_state.evaluacion_temporal['obs_general'] = obs_general
    
    # SECCIÓN 4: ÚLTIMOS EVENTOS (Más compacto)
    if st.session_state.acciones_partido['eventos']:
        with st.expander(f"📜 Últimos eventos ({len(st.session_state.acciones_partido['eventos'])})", expanded=False):
            # Mostrar solo los últimos 5 eventos
            for evento in reversed(st.session_state.acciones_partido['eventos'][-5:]):
                if evento['tipo'] == 'positivo':
                    st.success(f"**Min {evento['minuto']}**: {evento['nota']}")
                elif evento['tipo'] == 'neutro':
                    st.info(f"**Min {evento['minuto']}**: {evento['nota']}")
                else:
                    st.error(f"**Min {evento['minuto']}**: {evento['nota']}")
    
    # SECCIÓN 5: BOTONES DE ACCIÓN
    st.markdown("---")
    col_btn_final1, col_btn_final2, col_btn_final3 = st.columns([1, 1, 1])
    
    with col_btn_final1:
        if st.button("💾 Guardar Borrador", key="btn_guardar_borrador", use_container_width=True):
            guardar_evaluacion_temporal(player, partido, posicion_real)
            st.success("✅ Borrador guardado")
    
    with col_btn_final2:
        if st.button("🔄 Limpiar", key="btn_limpiar", use_container_width=True):
            if st.session_state.acciones_partido['eventos']:
                limpiar_estados_evaluacion()
                st.info("🔄 Formulario limpio")
    
    with col_btn_final3:
        if st.button("✅ FINALIZAR", key="btn_guardar_informe", 
                     use_container_width=True, type="primary"):
            if guardar_informe_final_campo(player, partido, posicion_real):
                st.success("✅ Informe guardado exitosamente")
                time.sleep(1)
                limpiar_estados_evaluacion()
                st.session_state.jugador_evaluando = None
                st.rerun()  # Solo aquí hacemos rerun
            else:
                st.error("❌ Error al guardar el informe")
    
    st.markdown('</div>', unsafe_allow_html=True)


def guardar_evaluacion_temporal(player, partido, posicion_real):
    """Guarda la evaluación temporal en session_state"""
    
    evaluacion_completa = {
        'jugador': player,
        'partido': partido,
        'posicion_real': posicion_real,
        'fecha_evaluacion': datetime.now(),
        'acciones': st.session_state.acciones_partido.copy(),
        'evaluacion': st.session_state.evaluacion_temporal.copy(),
        'tipo_evaluacion': 'campo'
    }
    
    # Guardar con ID único
    eval_id = f"{player['nombre']}_{partido['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    if 'evaluaciones_guardadas' not in st.session_state:
        st.session_state.evaluaciones_guardadas = {}
    
    st.session_state.evaluaciones_guardadas[eval_id] = evaluacion_completa


def guardar_informe_final_campo(player, partido, posicion_real):
    """Prepara y guarda el informe final en la base de datos"""    
    try:
        # Calcular estadísticas
        total_acciones = (st.session_state.acciones_partido['positivas'] + 
                         st.session_state.acciones_partido['neutras'] + 
                         st.session_state.acciones_partido['negativas'])
        
        if total_acciones > 0:
            porcentaje_positivas = (st.session_state.acciones_partido['positivas'] / total_acciones) * 100
        else:
            porcentaje_positivas = 0
        
        # Preparar observaciones mejoradas
        observaciones = f"""
EVALUACIÓN EN CAMPO - {posicion_real}

Acciones registradas:
- Positivas: {st.session_state.acciones_partido['positivas']} ({porcentaje_positivas:.1f}%)
- Neutras: {st.session_state.acciones_partido['neutras']}
- Negativas: {st.session_state.acciones_partido['negativas']}

EVENTOS DESTACADOS:
"""
        
        # Añadir eventos más relevantes
        eventos_relevantes = st.session_state.acciones_partido['eventos'][-10:]  # Últimos 10 eventos
        for evento in eventos_relevantes:
            observaciones += f"\n- Min {evento['minuto']}: {evento['nota']} [{evento['tipo'].upper()}]"
        
        observaciones += f"\n\nObservaciones generales: {st.session_state.evaluacion_temporal.get('obs_general', 'Sin observaciones adicionales')}"
        
        # Recopilar fortalezas y debilidades basadas en evaluación
        fortalezas = []
        debilidades = []
        aspectos_evaluados = []
        
        for key, value in st.session_state.evaluacion_temporal.items():
            if key.startswith('aspecto_'):
                aspecto_nombre = key.replace('aspecto_', '')
                if value >= 7:
                    fortalezas.append(f"{aspecto_nombre}: {value}/10")
                elif value <= 4:
                    debilidades.append(f"{aspecto_nombre}: {value}/10")
                aspectos_evaluados.append(f"{aspecto_nombre}: {value}")
        
        # Determinar recomendación basada en nota general y rendimiento
        nota_general = st.session_state.evaluacion_temporal.get('nota_general', 5)
        
        # Ajustar nota ligeramente según el rendimiento en campo
        if porcentaje_positivas > 70:
            nota_ajustada = min(10, nota_general + 0.5)
        elif porcentaje_positivas < 30:
            nota_ajustada = max(1, nota_general - 0.5)
        else:
            nota_ajustada = nota_general
        
        if nota_ajustada >= 7:
            recomendacion = 'fichar'
        elif nota_ajustada >= 5:
            recomendacion = 'seguir_observando'
        else:
            recomendacion = 'descartar'

        # Si hay alguna clave con 'img' o 'image', mostrarla
        for key in player.keys():
            if 'img' in key.lower() or 'image' in key.lower() or 'foto' in key.lower():
                print(f"   {key}: '{player[key]}'")
        
        # Preparar datos para partido_model
        informe_data = {
            'partido_id': partido['id'],
            'jugador_nombre': player['nombre'],
            'equipo': player['equipo'],
            'posicion': posicion_real,  # Usamos la posición real, no la de BeSoccer
            'scout_usuario': current_user['usuario'],
            'nota_general': nota_ajustada,
            'potencial': 'medio',  # Por defecto en evaluación de campo
            'recomendacion': recomendacion,
            'observaciones': observaciones.strip(),
            'minutos_observados': st.session_state.get('minuto_actual', 90),
            'fortalezas': ', '.join(fortalezas) if fortalezas else 'Por determinar en análisis completo',
            'debilidades': ', '.join(debilidades) if debilidades else 'Por determinar en análisis completo',
            'tipo_evaluacion': 'campo',
            'imagen_url': player.get('imagen_url', '')
        }
        
        print(f"DEBUG - informe_data: {informe_data}")
        print(f"DEBUG - Llamando a crear_informe_scouting...")
        
        # NUEVO: Guardar el partido antes del informe
        partido_model.guardar_partido_si_no_existe(partido)
        
        # Llamar a partido_model para guardar el informe
        informe_id = partido_model.crear_informe_scouting(informe_data)
        print(f"DEBUG - Informe creado con ID: {informe_id}")
        
        # AHORA SÍ: Después de guardar el informe exitosamente, actualizamos/creamos el jugador en Base Personal
        if DB_HELPERS_DISPONIBLE and informe_id:
            try:
                print("💾 Actualizando jugador en Base Personal DESPUÉS de guardar informe...")
                
                # Preparar datos completos del jugador
                jugador_data = {
                    'nombre': player['nombre'],
                    'numero': player.get('numero', '?'),
                    'posicion': posicion_real,  # Usar la posición real evaluada
                    'imagen_url': player.get('imagen_url', ''),
                    'es_titular': True  # Si lo evaluamos, asumimos que jugó
                }
                
                # Preparar datos del partido con información correcta
                partido_data = {
                    **partido,
                    'equipo': player['equipo'],
                    'escudo_equipo': partido.get('escudo_local', '') if player['equipo'] == partido['equipo_local'] else partido.get('escudo_visitante', ''),
                    'nota_evaluacion': nota_ajustada,  # Añadir la nota de la evaluación
                    'recomendacion': recomendacion
                }
                
                # Actualizar/crear jugador con la información del informe
                from utils.db_helpers import actualizar_jugador_desde_informe
                actualizar_jugador_desde_informe(jugador_data, partido_data, current_user['usuario'], informe_id)
                
                print("✅ Jugador actualizado en Base Personal con datos del informe")
                
            except Exception as e:
                print(f"⚠️ Error actualizando Base Personal: {e}")
                # No fallar si hay error al actualizar base personal
        
        return True
        
    except Exception as e:
        print(f"Error al guardar informe: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    

def limpiar_estados_evaluacion():
    """Limpia los estados temporales después de guardar"""
    
    if 'acciones_partido' in st.session_state:
        del st.session_state.acciones_partido
    
    if 'evaluacion_temporal' in st.session_state:
        del st.session_state.evaluacion_temporal
    
    if 'minuto_actual' in st.session_state:
        del st.session_state.minuto_actual

def mostrar_formulario_evaluacion_completo(player, partido):
    """
    Muestra el formulario de evaluación completa con análisis de video
    """
    
    # Inicializar estados si no existen
    if 'eval_completa' not in st.session_state:
        st.session_state.eval_completa = {
            'tiempo_analisis': 45,
            'contexto_partido': '',
            'datos_tecnicos': {},
            'datos_tacticos': {},
            'datos_fisicos': {},
            'datos_psicologicos': {},
            'observaciones': {},
            'posicion_real': player.get('posicion', 'Mediocentro')
        }
    
    st.markdown('<div class="eval-form">', unsafe_allow_html=True)
    
    # Header del jugador con selector de posición
    col_info1, col_info2 = st.columns([2, 1])
    
    with col_info1:
        st.markdown(f"""
        <div class="jugador-seleccionado">
            <h3 style="margin: 0;">🎥 Análisis Completo: {player['nombre']} (#{player['numero']})</h3>
            <p style="margin: 0;">{player['equipo']} {' • 🎯 Objetivo' if player['es_objetivo'] else ''}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_info2:
        # Selector de posición REAL en el partido
        posiciones = [
            'Portero', 'Central', 'Lateral Derecho', 'Lateral Izquierdo',
            'Mediocentro Defensivo', 'Mediocentro', 'Media Punta',
            'Extremo Derecho', 'Extremo Izquierdo', 'Delantero'
        ]
        
        # Intentar preseleccionar basado en posición de BeSoccer
        posicion_besoccer = player.get('posicion', 'Mediocentro')
        try:
            index_default = next(i for i, p in enumerate(posiciones) 
                               if posicion_besoccer.lower() in p.lower())
        except:
            index_default = 5  # Mediocentro por defecto
        
        posicion_real = st.selectbox(
            "📍 Posición real:",
            posiciones,
            index=index_default,
            key=f"posicion_real_completo_{player['nombre']}"
        )
        
        # Guardar la posición seleccionada
        st.session_state.eval_completa['posicion_real'] = posicion_real
    
    st.markdown("---")
    
    # Información del contexto
    col_ctx1, col_ctx2, col_ctx3 = st.columns(3)
    
    with col_ctx1:
        tiempo_analisis = st.number_input(
            "⏱️ Minutos analizados:",
            min_value=10,
            max_value=180,
            value=st.session_state.eval_completa.get('tiempo_analisis', 45),
            step=5,
            help="¿Cuántos minutos de video has visto?"
        )
        st.session_state.eval_completa['tiempo_analisis'] = tiempo_analisis
    
    with col_ctx2:
        calidad_video = st.selectbox(
            "📹 Calidad del análisis:",
            ["Video completo HD", "Highlights YouTube", "Transmisión TV", "Grabación móvil"],
            help="Tipo de material usado"
        )
        st.session_state.eval_completa['calidad_video'] = calidad_video
    
    with col_ctx3:
        contexto_partido = st.selectbox(
            "🏆 Contexto del partido:",
            ["Liga regular", "Copa/Eliminatoria", "Derbi/Clásico", "Partido amistoso", "Final/Semifinal"],
            help="Importancia del encuentro"
        )
        st.session_state.eval_completa['contexto_partido'] = contexto_partido
    
    # Nota general y decisión rápida
    st.markdown("### 📊 Evaluación General")
    col_gen1, col_gen2, col_gen3 = st.columns(3)
    
    with col_gen1:
        nota_general = st.slider(
            "🌟 **Nota General**",
            min_value=1,
            max_value=10,
            value=6,
            help="Valoración global del jugador"
        )
        st.session_state.eval_completa['nota_general'] = nota_general
    
    with col_gen2:
        encaja_equipo = st.selectbox(
            "🤝 **¿Encaja en nuestro equipo?**",
            ["Sí, perfectamente", "Sí, con ajustes", "Tal vez", "No"],
            help="¿Se adaptaría a nuestro estilo?"
        )
        st.session_state.eval_completa['encaja_equipo'] = encaja_equipo
    
    with col_gen3:
        decision_final = st.selectbox(
            "✅ **Decisión**",
            ["📗 Fichar YA", "📘 Seguir observando", "📙 Lista de espera", "📕 Descartar"],
            help="¿Qué hacemos con este jugador?"
        )
        st.session_state.eval_completa['decision_final'] = decision_final
    
    st.markdown("---")
    
    # EVALUACIÓN POR CATEGORÍAS - ADAPTADA A LA POSICIÓN
    
    # Obtener aspectos específicos según la posición seleccionada
    aspectos = obtener_aspectos_evaluacion_completa(posicion_real)
    
    # 1. TÉCNICO
    with st.expander("🛠️ **Evaluación Técnica**", expanded=True):
        col_tec1, col_tec2 = st.columns(2)
        
        datos_tecnicos = {}
        aspectos_tecnicos = aspectos['tecnicos']
        
        for i, (aspecto, valor_default) in enumerate(aspectos_tecnicos.items()):
            with col_tec1 if i % 2 == 0 else col_tec2:
                valor = st.slider(
                    aspecto,
                    min_value=1,
                    max_value=10,
                    value=st.session_state.eval_completa.get('datos_tecnicos', {}).get(aspecto, valor_default),
                    key=f"tec_completo_{aspecto.replace(' ', '_').replace('/', '_')}"
                )
                datos_tecnicos[aspecto] = valor
        
        st.session_state.eval_completa['datos_tecnicos'] = datos_tecnicos
        
        # Observaciones técnicas
        obs_tecnicas = st.text_area(
            "💭 Observaciones técnicas:",
            placeholder="Ej: Excelente primer toque, le falta mejorar el perfil débil...",
            height=80,
            key="obs_tecnicas_completo"
        )
        st.session_state.eval_completa['observaciones']['tecnicas'] = obs_tecnicas
    
    # 2. TÁCTICO
    with st.expander("🧠 **Evaluación Táctica**", expanded=True):
        col_tac1, col_tac2 = st.columns(2)
        
        datos_tacticos = {}
        aspectos_tacticos = aspectos['tacticos']
        
        for i, (aspecto, valor_default) in enumerate(aspectos_tacticos.items()):
            with col_tac1 if i % 2 == 0 else col_tac2:
                valor = st.slider(
                    aspecto,
                    min_value=1,
                    max_value=10,
                    value=st.session_state.eval_completa.get('datos_tacticos', {}).get(aspecto, valor_default),
                    key=f"tac_completo_{aspecto.replace(' ', '_')}"
                )
                datos_tacticos[aspecto] = valor
        
        st.session_state.eval_completa['datos_tacticos'] = datos_tacticos
        
        # Observaciones tácticas
        obs_tacticas = st.text_area(
            "💭 Observaciones tácticas:",
            placeholder="Ej: Excelente timing en los desmarques, debe mejorar la cobertura defensiva...",
            height=80,
            key="obs_tacticas_completo"
        )
        st.session_state.eval_completa['observaciones']['tacticas'] = obs_tacticas
    
    # 3. FÍSICO
    with st.expander("💪 **Evaluación Física**", expanded=True):
        col_fis1, col_fis2 = st.columns(2)
        
        datos_fisicos = {}
        aspectos_fisicos = aspectos['fisicos']
        
        # Primero los sliders numéricos
        aspectos_numericos = {k: v for k, v in aspectos_fisicos.items() if isinstance(v, int)}
        for i, (aspecto, valor_default) in enumerate(aspectos_numericos.items()):
            with col_fis1 if i % 2 == 0 else col_fis2:
                valor = st.slider(
                    aspecto,
                    min_value=1,
                    max_value=10,
                    value=st.session_state.eval_completa.get('datos_fisicos', {}).get(aspecto, valor_default),
                    key=f"fis_completo_{aspecto.replace(' ', '_')}"
                )
                datos_fisicos[aspecto] = valor
        
        # Luego los selectores categóricos
        st.markdown("**Evaluación cualitativa:**")
        col_fis_cual1, col_fis_cual2 = st.columns(2)
        
        with col_fis_cual1:
            ritmo_juego = st.select_slider(
                "⚡ Ritmo de juego",
                options=["Muy bajo", "Bajo", "Normal", "Alto", "Muy alto"],
                value="Normal",
                help="¿A qué ritmo puede jugar?"
            )
            datos_fisicos['ritmo_juego'] = ritmo_juego
        
        with col_fis_cual2:
            aguanta_90min = st.select_slider(
                "⏱️ ¿Aguanta 90 minutos?",
                options=["No", "Con dificultad", "Sí", "Sí, sobrado"],
                value="Sí",
                help="¿Mantiene el nivel todo el partido?"
            )
            datos_fisicos['aguanta_90min'] = aguanta_90min
        
        st.session_state.eval_completa['datos_fisicos'] = datos_fisicos
        
        # Observaciones físicas
        obs_fisicas = st.text_area(
            "💭 Observaciones físicas:",
            placeholder="Ej: Pierde fuelle en el min 70, muy explosivo en carreras cortas...",
            height=80,
            key="obs_fisicas_completo"
        )
        st.session_state.eval_completa['observaciones']['fisicas'] = obs_fisicas
    
    # 4. PSICOLÓGICO/MENTAL
    with st.expander("🧠 **Evaluación Mental**", expanded=True):
        st.info("💡 En categorías modestas, el carácter marca la diferencia")
        
        col_psi1, col_psi2 = st.columns(2)
        
        datos_psicologicos = {}
        aspectos_mentales = aspectos['mentales']
        
        for i, (aspecto, valor_default) in enumerate(aspectos_mentales.items()):
            with col_psi1 if i % 2 == 0 else col_psi2:
                valor = st.slider(
                    aspecto,
                    min_value=1,
                    max_value=10,
                    value=st.session_state.eval_completa.get('datos_psicologicos', {}).get(aspecto, valor_default),
                    key=f"mental_completo_{aspecto.replace(' ', '_')}"
                )
                datos_psicologicos[aspecto] = valor
        
        # Añadir evaluaciones cualitativas
        st.markdown("**Características de personalidad:**")
        col_psi_cual1, col_psi_cual2 = st.columns(2)
        
        with col_psi_cual1:
            liderazgo = st.select_slider(
                "👑 Liderazgo",
                options=["Nulo", "Poco", "Normal", "Líder", "Líder nato"],
                value="Normal"
            )
            datos_psicologicos['liderazgo'] = liderazgo
        
        with col_psi_cual2:
            reaccion_adversidad = st.select_slider(
                "💪 Ante la adversidad",
                options=["Se hunde", "Le afecta", "Normal", "Se crece", "Bestia competitiva"],
                value="Normal"
            )
            datos_psicologicos['reaccion_adversidad'] = reaccion_adversidad
        
        st.session_state.eval_completa['datos_psicologicos'] = datos_psicologicos
        
        # Observaciones psicológicas
        obs_psicologicas = st.text_area(
            "💭 Observaciones mentales:",
            placeholder="Ej: Líder nato, organiza la defensa, mantiene la calma en momentos de presión...",
            height=80,
            key="obs_psicologicas_completo"
        )
        st.session_state.eval_completa['observaciones']['psicologicas'] = obs_psicologicas
    
    # MOMENTOS CLAVE
    with st.expander("📹 **Momentos Destacados del Video**", expanded=False):
        st.info("💡 Anota los minutos clave para crear un video resumen")
        
        momentos_clave = st.text_area(
            "Momentos importantes (minuto: acción):",
            placeholder="""Min 12: Gran pase entre líneas que genera ocasión
Min 34: Error en salida que casi cuesta gol
Min 67: Golazo desde fuera del área
Min 89: Carrera de 60m para evitar un gol""",
            height=120,
            key="momentos_clave_completo"
        )
        st.session_state.eval_completa['momentos_clave'] = momentos_clave
    
    # RESUMEN FINAL
    st.markdown("---")
    st.markdown("### 📋 Resumen y Recomendación Final")
    
    col_res1, col_res2 = st.columns([2, 1])
    
    with col_res1:
        resumen_scout = st.text_area(
            "✍️ **Resumen ejecutivo** (lo que le dirías al director deportivo):",
            placeholder="""Jugador técnico con buena visión de juego. Destaca en espacios reducidos.
Le falta intensidad defensiva pero tiene carácter ganador.
Encajaría bien en nuestro 4-3-3 como interior.
Por 50.000€ sería una gran incorporación.""",
            height=120,
            key="resumen_scout_completo"
        )
        st.session_state.eval_completa['resumen_scout'] = resumen_scout
    
    with col_res2:
        precio_maximo = st.selectbox(
            "💰 **Precio máximo a pagar**",
            ["Gratis/Libre", "< 10.000€", "10-25.000€", "25-50.000€", 
             "50-100.000€", "100-250.000€", "> 250.000€"],
            help="¿Cuánto pagarías como máximo?"
        )
        st.session_state.eval_completa['precio_maximo'] = precio_maximo
        
        prioridad_fichaje = st.select_slider(
            "🎯 **Prioridad**",
            options=["Baja", "Media", "Alta", "Urgente"],
            value="Media",
            help="¿Cuán urgente es ficharlo?"
        )
        st.session_state.eval_completa['prioridad_fichaje'] = prioridad_fichaje
    
    # VALIDACIÓN Y GUARDADO
    st.markdown("---")
    
    # Mostrar completitud
    col_val1, col_val2, col_val3 = st.columns(3)
    
    with col_val1:
        completitud = min(100, int((tiempo_analisis / 30) * 100))
        st.metric("📊 Análisis completado", f"{completitud}%")
    
    with col_val2:
        total_aspectos = (len(datos_tecnicos) + len(datos_tacticos) + 
                         len(datos_fisicos) + len(datos_psicologicos))
        st.metric("✅ Aspectos evaluados", total_aspectos)
    
    with col_val3:
        tiene_resumen = len(resumen_scout) > 50
        st.metric("📝 Resumen", "✅ Sí" if tiene_resumen else "❌ No")
    
    # Botones de acción
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
    
    with col_btn1:
        if st.button("💾 Guardar Borrador", key="save_draft_completo_v2", use_container_width=True):
            st.info("💾 Guardando borrador...")
            # Aquí se podría implementar guardado temporal
            st.success("✅ Borrador guardado")
    
    with col_btn2:
        if st.button("📄 Vista Previa", key="preview_completo_v2", use_container_width=True):
            with st.expander("Vista previa del informe", expanded=True):
                st.write(f"**Jugador:** {player['nombre']} ({player['equipo']})")
                st.write(f"**Posición evaluada:** {posicion_real}")
                st.write(f"**Nota:** {nota_general}/10")
                st.write(f"**Decisión:** {decision_final}")
                st.write(f"**Resumen:** {resumen_scout}")
    
    with col_btn3:
        puede_guardar = (tiempo_analisis >= 15 and len(resumen_scout) > 50)
        
        if st.button(
            "✅ GUARDAR INFORME", 
            key="save_final_completo_v2", 
            use_container_width=True, 
            type="primary",
            disabled=not puede_guardar
        ):
            if guardar_informe_final_completo(player, partido, posicion_real):
                st.success("✅ Informe guardado exitosamente")
                time.sleep(1)
                limpiar_estados_evaluacion_completo()
                st.session_state.jugador_evaluando = None
                st.rerun()
            else:
                st.error("❌ Error al guardar el informe")
    
    if not puede_guardar:
        if tiempo_analisis < 15:
            st.warning("⚠️ Necesitas al menos 15 minutos de análisis")
        if len(resumen_scout) <= 50:
            st.warning("⚠️ El resumen debe tener al menos 50 caracteres")
    
    st.markdown('</div>', unsafe_allow_html=True)


def obtener_aspectos_evaluacion_completa(posicion):
    """
    Devuelve los aspectos de evaluación específicos para cada posición
    en el modo de evaluación completa (más detallado que el modo campo)
    """
    
    aspectos_por_posicion = {
        'Portero': {
            'tecnicos': {
                'Paradas reflejos': 5,
                'Blocaje seguro': 5,
                'Juego con pies': 5,
                'Saques precisión': 5,
                'Salidas aéreas': 5,
                'Mano a mano': 5
            },
            'tacticos': {
                'Posicionamiento': 5,
                'Lectura del juego': 5,
                'Comunicación defensa': 5,
                'Dominio del área': 5,
                'Anticipación': 5,
                'Organización defensiva': 5
            },
            'fisicos': {
                'Agilidad': 5,
                'Explosividad': 5,
                'Flexibilidad': 5,
                'Alcance': 5
            },
            'mentales': {
                'Concentración': 5,
                'Confianza': 5,
                'Presión': 5,
                'Recuperación errores': 5,
                'Liderazgo': 5,
                'Personalidad': 5
            }
        },
        
        'Central': {
            'tecnicos': {
                'Juego aéreo': 5,
                'Pase largo': 5,
                'Control orientado': 5,
                'Salida balón': 5,
                'Entrada limpia': 5,
                'Despeje orientado': 5
            },
            'tacticos': {
                'Marcaje hombre': 5,
                'Marcaje zonal': 5,
                'Cobertura': 5,
                'Línea de pase': 5,
                'Anticipación': 5,
                'Timing subida': 5
            },
            'fisicos': {
                'Fuerza': 5,
                'Salto': 5,
                'Velocidad': 5,
                'Resistencia': 5
            },
            'mentales': {
                'Concentración': 5,
                'Agresividad': 5,
                'Liderazgo': 5,
                'Comunicación': 5,
                'Temple': 5,
                'Inteligencia': 5
            }
        },
        
        'Lateral Derecho': {
            'tecnicos': {
                'Centro precisión': 5,
                'Control velocidad': 5,
                'Pase interior': 5,
                'Conducción': 5,
                'Tackle': 5,
                'Técnica defensiva': 5
            },
            'tacticos': {
                'Subida ataque': 5,
                'Repliegue': 5,
                'Apoyo interior': 5,
                'Vigilancia extremo': 5,
                'Basculación': 5,
                'Profundidad': 5
            },
            'fisicos': {
                'Velocidad': 5,
                'Resistencia': 5,
                'Agilidad': 5,
                'Potencia': 5
            },
            'mentales': {
                'Disciplina táctica': 5,
                'Concentración': 5,
                'Valentía': 5,
                'Inteligencia': 5,
                'Sacrificio': 5,
                'Ambición': 5
            }
        },
        
        'Lateral Izquierdo': {
            'tecnicos': {
                'Centro precisión': 5,
                'Control velocidad': 5,
                'Pase interior': 5,
                'Conducción': 5,
                'Tackle': 5,
                'Técnica defensiva': 5
            },
            'tacticos': {
                'Subida ataque': 5,
                'Repliegue': 5,
                'Apoyo interior': 5,
                'Vigilancia extremo': 5,
                'Basculación': 5,
                'Profundidad': 5
            },
            'fisicos': {
                'Velocidad': 5,
                'Resistencia': 5,
                'Agilidad': 5,
                'Potencia': 5
            },
            'mentales': {
                'Disciplina táctica': 5,
                'Concentración': 5,
                'Valentía': 5,
                'Inteligencia': 5,
                'Sacrificio': 5,
                'Ambición': 5
            }
        },
        
        'Mediocentro Defensivo': {
            'tecnicos': {
                'Interceptación': 5,
                'Pase corto seguro': 5,
                'Pase largo': 5,
                'Control presión': 5,
                'Barrido': 5,
                'Juego aéreo': 5
            },
            'tacticos': {
                'Cobertura defensiva': 5,
                'Distribución': 5,
                'Posicionamiento': 5,
                'Pressing': 5,
                'Transición def-atq': 5,
                'Lectura juego': 5
            },
            'fisicos': {
                'Resistencia': 5,
                'Fuerza': 5,
                'Agilidad': 5,
                'Potencia': 5
            },
            'mentales': {
                'Concentración': 5,
                'Disciplina': 5,
                'Liderazgo': 5,
                'Sacrificio': 5,
                'Inteligencia táctica': 5,
                'Madurez': 5
            }
        },
        
        'Mediocentro': {
            'tecnicos': {
                'Pase corto': 5,
                'Pase medio': 5,
                'Control orientado': 5,
                'Conducción': 5,
                'Tiro medio': 5,
                'Presión': 5
            },
            'tacticos': {
                'Visión juego': 5,
                'Movilidad': 5,
                'Creación espacios': 5,
                'Pressing inteligente': 5,
                'Llegada área': 5,
                'Equilibrio': 5
            },
            'fisicos': {
                'Resistencia': 5,
                'Velocidad': 5,
                'Agilidad': 5,
                'Cambio ritmo': 5
            },
            'mentales': {
                'Creatividad': 5,
                'Personalidad': 5,
                'Presión': 5,
                'Inteligencia': 5,
                'Ambición': 5,
                'Trabajo equipo': 5
            }
        },
        
        'Media Punta': {
            'tecnicos': {
                'Último pase': 5,
                'Control espacios reducidos': 5,
                'Regate corto': 5,
                'Tiro': 5,
                'Pase entre líneas': 5,
                'Técnica depurada': 5
            },
            'tacticos': {
                'Encontrar espacios': 5,
                'Asociación': 5,
                'Desmarque apoyo': 5,
                'Lectura defensiva rival': 5,
                'Timing pase': 5,
                'Cambio orientación': 5
            },
            'fisicos': {
                'Agilidad': 5,
                'Cambio ritmo': 5,
                'Equilibrio': 5,
                'Coordinación': 5
            },
            'mentales': {
                'Creatividad': 5,
                'Visión': 5,
                'Confianza': 5,
                'Personalidad': 5,
                'Presión': 5,
                'Liderazgo técnico': 5
            }
        },
        
        'Extremo Derecho': {
            'tecnicos': {
                'Regate': 5,
                'Centro': 5,
                'Finalización': 5,
                'Control velocidad': 5,
                'Cambio ritmo': 5,
                'Recorte interior': 5
            },
            'tacticos': {
                'Desmarque': 5,
                'Profundidad': 5,
                'Ayuda defensiva': 5,
                'Movimientos sin balón': 5,
                'Asociación': 5,
                'Amplitud': 5
            },
            'fisicos': {
                'Velocidad punta': 5,
                'Explosividad': 5,
                'Agilidad': 5,
                'Resistencia': 5
            },
            'mentales': {
                'Valentía 1v1': 5,
                'Confianza': 5,
                'Sacrificio': 5,
                'Perseverancia': 5,
                'Decisión': 5,
                'Ambición': 5
            }
        },
        
        'Extremo Izquierdo': {
            'tecnicos': {
                'Regate': 5,
                'Centro': 5,
                'Finalización': 5,
                'Control velocidad': 5,
                'Cambio ritmo': 5,
                'Recorte interior': 5
            },
            'tacticos': {
                'Desmarque': 5,
                'Profundidad': 5,
                'Ayuda defensiva': 5,
                'Movimientos sin balón': 5,
                'Asociación': 5,
                'Amplitud': 5
            },
            'fisicos': {
                'Velocidad punta': 5,
                'Explosividad': 5,
                'Agilidad': 5,
                'Resistencia': 5
            },
            'mentales': {
                'Valentía 1v1': 5,
                'Confianza': 5,
                'Sacrificio': 5,
                'Perseverancia': 5,
                'Decisión': 5,
                'Ambición': 5
            }
        },
        
        'Delantero': {
            'tecnicos': {
                'Finalización pie derecho': 5,
                'Finalización pie izquierdo': 5,
                'Finalización cabeza': 5,
                'Control área': 5,
                'Juego espaldas': 5,
                'Primer toque': 5
            },
            'tacticos': {
                'Desmarque ruptura': 5,
                'Timing llegada': 5,
                'Arrastre marcas': 5,
                'Pressing': 5,
                'Asociación': 5,
                'Lectura juego': 5
            },
            'fisicos': {
                'Potencia': 5,
                'Velocidad': 5,
                'Salto': 5,
                'Fuerza': 5
            },
            'mentales': {
                'Sangre fría': 5,
                'Confianza': 5,
                'Ambición': 5,
                'Persistencia': 5,
                'Competitividad': 5,
                'Presión gol': 5
            }
        }
    }
    
    # Si la posición no está definida, usar aspectos genéricos de Mediocentro
    return aspectos_por_posicion.get(posicion, aspectos_por_posicion['Mediocentro'])


def guardar_informe_final_completo(player, partido, posicion_real):
    """Prepara y guarda el informe final de evaluación completa en la base de datos"""
    try:
        # Obtener todos los datos de la evaluación
        eval_data = st.session_state.eval_completa
        
        # Calcular promedios por categoría
        datos_tecnicos = eval_data.get('datos_tecnicos', {})
        datos_tacticos = eval_data.get('datos_tacticos', {})
        datos_fisicos = eval_data.get('datos_fisicos', {})
        datos_psicologicos = eval_data.get('datos_psicologicos', {})
        
        promedio_tecnico = sum(datos_tecnicos.values()) / len(datos_tecnicos) if datos_tecnicos else 5
        promedio_tactico = sum(datos_tacticos.values()) / len(datos_tacticos) if datos_tacticos else 5
        
        # Para físicos y psicológicos, filtrar solo valores numéricos
        valores_fisicos_num = [v for v in datos_fisicos.values() if isinstance(v, int)]
        valores_psico_num = [v for v in datos_psicologicos.values() if isinstance(v, int)]
        
        promedio_fisico = sum(valores_fisicos_num) / len(valores_fisicos_num) if valores_fisicos_num else 5
        promedio_psicologico = sum(valores_psico_num) / len(valores_psico_num) if valores_psico_num else 5
        
        # Obtener datos generales
        nota_general = eval_data.get('nota_general', 5)
        decision_final = eval_data.get('decision_final', '📘 Seguir observando')
        resumen_scout = eval_data.get('resumen_scout', '')
        
        # Mapear decisión a recomendación
        mapeo_decision = {
            "📗 Fichar YA": "fichar",
            "📘 Seguir observando": "seguir_observando",
            "📙 Lista de espera": "seguir_observando",
            "📕 Descartar": "descartar"
        }
        
        # Determinar potencial basado en edad y nota
        if nota_general >= 8:
            potencial = "alto"
        elif nota_general >= 6:
            potencial = "medio"
        else:
            potencial = "bajo"
        
        # Preparar observaciones completas
        observaciones_completas = f"""
ANÁLISIS COMPLETO CON VIDEO
Posición evaluada: {posicion_real}
Tiempo de análisis: {eval_data.get('tiempo_analisis', 0)} minutos
Calidad: {eval_data.get('calidad_video', 'N/A')}
Contexto: {eval_data.get('contexto_partido', 'N/A')}

RESUMEN EJECUTIVO:
{resumen_scout}

EVALUACIÓN POR ÁREAS:
- Técnica: {promedio_tecnico:.1f}/10
- Táctica: {promedio_tactico:.1f}/10
- Física: {promedio_fisico:.1f}/10 ({datos_fisicos.get('ritmo_juego', 'N/A')} / {datos_fisicos.get('aguanta_90min', 'N/A')})
- Mental: {promedio_psicologico:.1f}/10

OBSERVACIONES TÉCNICAS:
{eval_data.get('observaciones', {}).get('tecnicas', 'Sin observaciones')}

OBSERVACIONES TÁCTICAS:
{eval_data.get('observaciones', {}).get('tacticas', 'Sin observaciones')}

OBSERVACIONES FÍSICAS:
{eval_data.get('observaciones', {}).get('fisicas', 'Sin observaciones')}

OBSERVACIONES MENTALES:
{eval_data.get('observaciones', {}).get('psicologicas', 'Sin observaciones')}

MOMENTOS CLAVE:
{eval_data.get('momentos_clave', 'Sin momentos destacados')}

DECISIÓN: {decision_final}
PRECIO MÁXIMO: {eval_data.get('precio_maximo', 'No especificado')}
PRIORIDAD: {eval_data.get('prioridad_fichaje', 'Media')}
"""
        
        # Identificar fortalezas y debilidades
        fortalezas = []
        debilidades = []
        
        # Analizar todos los aspectos evaluados
        todos_aspectos = {
            **datos_tecnicos,
            **datos_tacticos,
            **{k: v for k, v in datos_fisicos.items() if isinstance(v, int)},
            **{k: v for k, v in datos_psicologicos.items() if isinstance(v, int)}
        }
        
        for aspecto, valor in todos_aspectos.items():
            if valor >= 7:
                fortalezas.append(f"{aspecto} ({valor}/10)")
            elif valor <= 4:
                debilidades.append(f"{aspecto} ({valor}/10)")
        
        # Preparar datos para guardar - mapear a campos de BD existentes
        informe_data = {
            'partido_id': partido['id'],
            'jugador_nombre': player['nombre'],
            'equipo': player['equipo'],
            'posicion': posicion_real,  # Usar la posición real evaluada
            'scout_usuario': current_user['usuario'],
            'nota_general': nota_general,
            'potencial': potencial,
            'recomendacion': mapeo_decision.get(decision_final, 'seguir_observando'),
            'observaciones': observaciones_completas,
            'minutos_observados': eval_data.get('tiempo_analisis', 45),
            'fortalezas': ', '.join(fortalezas[:5]) if fortalezas else 'Ver evaluación detallada',
            'debilidades': ', '.join(debilidades[:5]) if debilidades else 'Ver evaluación detallada',
            'tipo_evaluacion': 'video_completo',
            'imagen_url': player.get('imagen_url', ''),
            
            # Mapear evaluaciones a campos existentes de BD
            'control_balon': datos_tecnicos.get('Control orientado', datos_tecnicos.get('Control y primer toque', 5)),
            'primer_toque': datos_tecnicos.get('Primer toque', datos_tecnicos.get('Control y primer toque', 5)),
            'pase_corto': datos_tecnicos.get('Pase corto', datos_tecnicos.get('Pase corto/medio', 5)),
            'pase_largo': datos_tecnicos.get('Pase largo', 5),
            'regate': datos_tecnicos.get('Regate', datos_tecnicos.get('Regate/Conducción', 5)),
            'finalizacion': datos_tecnicos.get('Finalización', datos_tecnicos.get('Finalización pie derecho', 5)),
            
            'vision_juego': datos_tacticos.get('Visión juego', datos_tacticos.get('Lectura del juego', 5)),
            'posicionamiento': datos_tacticos.get('Posicionamiento', 5),
            'marcaje': datos_tacticos.get('Marcaje hombre', datos_tacticos.get('Marcaje', 5)),
            'pressing': datos_tacticos.get('Pressing', datos_tacticos.get('Pressing inteligente', 5)),
            'transiciones': datos_tacticos.get('Transición def-atq', datos_tacticos.get('Movimientos sin balón', 5)),
            
            'velocidad': datos_fisicos.get('Velocidad', datos_fisicos.get('Velocidad punta', 5)),
            'resistencia': datos_fisicos.get('Resistencia', 5),
            'fuerza': datos_fisicos.get('Fuerza', 5),
            'salto': datos_fisicos.get('Salto', 5),
            'agilidad': datos_fisicos.get('Agilidad', 5),
            
            'concentracion': datos_psicologicos.get('Concentración', 5),
            'liderazgo': datos_psicologicos.get('Liderazgo', 5),
            'comunicacion': datos_psicologicos.get('Comunicación', 5),
            'presion': datos_psicologicos.get('Presión', 5),
            'decision': datos_tacticos.get('Toma de decisiones', datos_psicologicos.get('Decisión', 5))
        }
        
        # Guardar el partido si no existe
        partido_model.guardar_partido_si_no_existe(partido)
        
        # Guardar el informe
        informe_id = partido_model.crear_informe_scouting(informe_data)
        
        if informe_id:
            # Actualizar base personal si está disponible
            if DB_HELPERS_DISPONIBLE:
                try:
                    jugador_data = {
                        'nombre': player['nombre'],
                        'numero': player.get('numero', '?'),
                        'posicion': posicion_real,
                        'imagen_url': player.get('imagen_url', ''),
                        'es_titular': True
                    }
                    
                    partido_data = {
                        **partido,
                        'equipo': player['equipo'],
                        'nota_evaluacion': nota_general,
                        'recomendacion': mapeo_decision.get(decision_final, 'seguir_observando')
                    }
                    
                    from utils.db_helpers import actualizar_jugador_desde_informe
                    actualizar_jugador_desde_informe(jugador_data, partido_data, current_user['usuario'], informe_id)
                    
                except Exception as e:
                    print(f"⚠️ Error actualizando Base Personal: {e}")
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error al guardar informe completo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def limpiar_estados_evaluacion_completo():
    """Limpia los estados temporales de la evaluación completa"""
    if 'eval_completa' in st.session_state:
        del st.session_state.eval_completa

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

# IMPORTANTE: Estado para la fecha seleccionada
if 'fecha_seleccionada' not in st.session_state:
    st.session_state.fecha_seleccionada = date.today()

# ================================
# VISTA: LISTA DE PARTIDOS LIMPIA - CORREGIDA PARA CAMBIO DE FECHA
# ================================

if st.session_state.modo_vista == 'lista_partidos':
    
    # Controles superiores
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.subheader("🗓️ Partidos")
    
    with col2:
        # IMPORTANTE: Usar key único para el date_input
        nueva_fecha = st.date_input(
            "Fecha:",
            value=st.session_state.fecha_seleccionada,
            min_value=date.today() - timedelta(days=7),
            max_value=date.today() + timedelta(days=14),
            key="selector_fecha_partidos"
        )
        
        # Si la fecha cambió, actualizar el estado
        if nueva_fecha != st.session_state.fecha_seleccionada:
            st.session_state.fecha_seleccionada = nueva_fecha
            st.rerun()
    
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True):
            # Forzar recarga
            st.cache_data.clear()
            st.rerun()
    
    # Cargar partidos LIMPIO - SIEMPRE usar la fecha del session state
    with st.spinner("🔄 Cargando partidos..."):
        fecha_str = st.session_state.fecha_seleccionada.strftime('%Y-%m-%d')
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
        st.subheader(f"🏟️ {st.session_state.fecha_seleccionada.strftime('%d/%m/%Y')}")
        
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
        st.info(f"📅 No hay partidos para el {st.session_state.fecha_seleccionada.strftime('%d/%m/%Y')}")

# [Resto del código permanece igual desde la vista de observación...]
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
                    numero = jugador.get('numero') or jugador.get('dorsal') or '?'
                    posicion = jugador.get('posicion') or jugador.get('position') or 'N/A'
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
                            'datos_objetivo': datos_objetivo or {},
                            'imagen_url': imagen_url  # AÑADIDO: pasar imagen_url
                        }
                        st.rerun()
                
                # ========================================
                # SUPLENTES LOCAL - LAYOUT COMPLETAMENTE CORREGIDO
                # ========================================
                if suplentes_local:
                    with st.expander(f"🔄 Suplentes ({len(suplentes_local)})", expanded=False):
                        for i, jugador in enumerate(suplentes_local):
                            nombre = jugador.get('nombre', 'Sin nombre')
                            numero = jugador.get('numero') or jugador.get('dorsal') or '?'
                            posicion = jugador.get('posicion') or jugador.get('position') or 'N/A'
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
                                        'datos_objetivo': datos_objetivo or {},
                                        'imagen_url': imagen_url  # AÑADIDO: pasar imagen_url
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
                    numero = jugador.get('numero') or jugador.get('dorsal') or '?'
                    posicion = jugador.get('posicion') or jugador.get('position') or 'N/A'
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
                            'datos_objetivo': datos_objetivo or {},
                            'imagen_url': imagen_url  # AÑADIDO: pasar imagen_url
                        }
                        st.rerun()
                
                # ========================================
                # SUPLENTES VISITANTE - LAYOUT COMPLETAMENTE CORREGIDO
                # ========================================
                if suplentes_visitante:
                    with st.expander(f"🔄 Suplentes ({len(suplentes_visitante)})", expanded=False):
                        for i, jugador in enumerate(suplentes_visitante):
                            nombre = jugador.get('nombre', 'Sin nombre')
                            numero = jugador.get('numero') or jugador.get('dorsal') or '?'
                            posicion = jugador.get('posicion') or jugador.get('position') or 'N/A'
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
                                </div>
                                """, unsafe_allow_html=True)
                            
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
                                        'datos_objetivo': datos_objetivo or {},
                                        'imagen_url': imagen_url  # AÑADIDO: pasar imagen_url
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
    # FORMULARIO DE EVALUACIÓN
    # ================================
    
    if st.session_state.jugador_evaluando:
        player = st.session_state.jugador_evaluando
        
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
        
        # LLAMAR A LA FUNCIÓN CORRESPONDIENTE SEGÚN EL MODO
        if st.session_state.modo_evaluacion == 'campo':
            mostrar_formulario_evaluacion_campo(player, st.session_state.partido_activo)
        else:  # 'completo'
            mostrar_formulario_evaluacion_completo(player, st.session_state.partido_activo)

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
        st.switch_page("pages/5_📋_Mis_Informes.py")
    
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