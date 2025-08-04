import streamlit as st
import pandas as pd
from common.login import LoginManager
from models.jugador_model import JugadorModel
from models.partido_model import PartidoModel
import os
import json
import uuid
from datetime import datetime, timedelta
import random


# Configuración de la página
st.set_page_config(
    page_title="Dashboard de Scouting - Scouting Pro",
    page_icon="📊",
    layout="wide"
)

# CSS personalizado para dashboard ejecutivo
st.markdown("""
<style>
/* Dashboard cards */
.dashboard-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-left: 4px solid #007bff;
}

.metric-card {
    background: linear-gradient(135deg, #007bff, #0056b3);
    color: white;
    border-radius: 10px;
    padding: 15px;
    text-align: center;
    margin: 5px;
    box-shadow: 0 4px 15px rgba(0,123,255,0.3);
}

/* Recomendación cards */
.recom-contratar {
    background: linear-gradient(145deg, #d4edda, #c3e6cb);
    border-left: 4px solid #28a745;
    border-radius: 10px;
    padding: 15px;
    margin: 8px 0;
    box-shadow: 0 2px 10px rgba(40,167,69,0.2);
}

.recom-seguir {
    background: linear-gradient(145deg, #fff3cd, #ffeaa7);
    border-left: 4px solid #ffc107;
    border-radius: 10px;
    padding: 15px;
    margin: 8px 0;
    box-shadow: 0 2px 10px rgba(255,193,7,0.2);
}

.recom-cartera {
    background: linear-gradient(145deg, #d1ecf1, #bee5eb);
    border-left: 4px solid #17a2b8;
    border-radius: 10px;
    padding: 15px;
    margin: 8px 0;
    box-shadow: 0 2px 10px rgba(23,162,184,0.2);
}

.recom-descartar {
    background: linear-gradient(145deg, #f8d7da, #f1b0b7);
    border-left: 4px solid #dc3545;
    border-radius: 10px;
    padding: 15px;
    margin: 8px 0;
    box-shadow: 0 2px 10px rgba(220,53,69,0.2);
}

/* Discovery cards */
.discovery-card {
    background: linear-gradient(145deg, #e8f5e8, #d4edda);
    border-radius: 12px;
    padding: 15px;
    margin: 8px 0;
    border-left: 4px solid #2ecc71;
    box-shadow: 0 3px 12px rgba(46,204,113,0.2);
}

/* Section headers */
.section-title {
    background: linear-gradient(135deg, #24282a, #34495e);
    color: white;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin: 20px 0 10px 0;
    font-weight: bold;
}

/* Quick stats */
.quick-stat {
    display: inline-block;
    background: rgba(0,123,255,0.1);
    padding: 5px 10px;
    border-radius: 15px;
    margin: 2px;
    font-size: 12px;
    color: #007bff;
    font-weight: bold;
}

/* Scout activity */
.scout-activity {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 10px;
    margin: 5px 0;
    border-left: 3px solid #6c757d;
}

/* Responsive design */
@media (max-width: 768px) {
    .dashboard-card {
        padding: 15px;
        margin: 5px 0;
    }
    
    .metric-card {
        padding: 10px;
        margin: 3px;
    }
}
</style>
""", unsafe_allow_html=True)

# Verificar autenticación
login_manager = LoginManager()
if not login_manager.is_authenticated():
    st.error("🔒 Debes iniciar sesión para acceder a esta página")
    st.stop()

# Inicializar modelos
jugador_model = JugadorModel()
partido_model = PartidoModel()

# Inicializar session state
if 'jugador_para_informe' not in st.session_state:
    st.session_state.jugador_para_informe = None

# ================================
# FUNCIONES DE CACHE Y UTILIDAD
# ================================

@st.cache_data(ttl=300)
def cargar_todos_informes():
    """Cache para todos los informes"""
    return partido_model.obtener_todos_informes()

@st.cache_data(ttl=300)
def cargar_estadisticas_dashboard():
    """Cache para estadísticas del dashboard"""
    return partido_model.obtener_estadisticas_dashboard()

@st.cache_data(ttl=600)  # Cache por 10 minutos
def cargar_datos_wyscout():
    """Carga datos de Wyscout para discovery"""
    try:
        wyscout_path = "data/wyscout_LaLiga_limpio.xlsx"
        if os.path.exists(wyscout_path):
            df_wyscout = pd.read_excel(wyscout_path, engine='openpyxl')
            return df_wyscout
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()
    
def convertir_valor_mercado(valor_str):
    """Convierte valores como '180M', '5.5M', '800K' a números"""
    try:
        if pd.isna(valor_str) or valor_str == '-' or valor_str == '':
            return 0
        
        valor_str = str(valor_str).strip().upper()
        
        if valor_str.endswith('M'):
            # Millones: '180M' -> 180000000
            numero = float(valor_str[:-1])
            return numero * 1000000
        elif valor_str.endswith('K'):
            # Miles: '800K' -> 800000
            numero = float(valor_str[:-1])
            return numero * 1000
        else:
            # Número directo
            return float(valor_str)
            
    except (ValueError, AttributeError):
        return 0
    
def cargar_lista_visualizacion():
    """Carga la lista de jugadores en seguimiento desde JSON"""
    try:
        with open('data/lista_visualizacion.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Si no existe el archivo o está corrupto, crear estructura vacía
        return {"jugadores_seguimiento": []}

def guardar_lista_visualizacion(data):
    """Guarda la lista de jugadores en seguimiento en JSON"""
    try:
        # Crear directorio si no existe
        import os
        os.makedirs('data', exist_ok=True)
        
        with open('data/lista_visualizacion.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error guardando lista: {e}")
        return False

def generar_proximo_partido(equipo):
    """Genera datos ficticios del próximo partido"""
    # Equipos comunes de La Liga para rivales
    equipos_laliga = [
        "Barcelona", "Atlético Madrid", "Real Sociedad", "Athletic Bilbao",
        "Betis", "Villarreal", "Valencia", "Sevilla", "Osasuna", "Getafe",
        "Las Palmas", "Girona", "Mallorca", "Celta", "Rayo Vallecano",
        "Alavés", "Leganes", "Espanyol", "Valladolid"
    ]
    
    # Estadios reales
    estadios = {
        "Real Madrid": "Santiago Bernabéu",
        "Barcelona": "Camp Nou", 
        "Atlético Madrid": "Metropolitano",
        "Valencia": "Mestalla",
        "Sevilla": "Ramón Sánchez-Pizjuán",
        "Betis": "Benito Villamarín",
        "Athletic Bilbao": "San Mamés"
    }
    
    # Rival aleatorio (que no sea el mismo equipo)
    rivales_posibles = [e for e in equipos_laliga if e != equipo]
    rival = random.choice(rivales_posibles)
    
    # Fecha en los próximos 7-21 días
    dias_adelante = random.randint(7, 21)
    fecha = datetime.now() + timedelta(days=dias_adelante)
    
    # Estadio (50% probabilidad casa/visitante)
    es_local = random.choice([True, False])
    if es_local:
        estadio = estadios.get(equipo, f"Estadio de {equipo}")
    else:
        estadio = estadios.get(rival, f"Estadio de {rival}")
    
    return {
        "fecha": fecha.strftime("%Y-%m-%d"),
        "rival": rival,
        "estadio": estadio,
        "competicion": "La Liga",
        "es_local": es_local
    }

def jugador_ya_en_lista(nombre_jugador, equipo):
    """Verifica si un jugador ya está en la lista de visualización"""
    lista = cargar_lista_visualizacion()
    
    for jugador in lista["jugadores_seguimiento"]:
        if (jugador["jugador"] == nombre_jugador and 
            jugador["equipo"] == equipo):
            return True
    return False

def añadir_jugador_a_lista(datos_jugador):
    """Añade un jugador a la lista de visualización"""
    lista = cargar_lista_visualizacion()
    
    # Verificar si ya existe
    if jugador_ya_en_lista(datos_jugador["jugador"], datos_jugador["equipo"]):
        return False, "El jugador ya está en la lista de visualización"
    
    # Crear nuevo entrada
    nuevo_jugador = {
        "id": str(uuid.uuid4()),
        "jugador": datos_jugador["jugador"],
        "equipo": datos_jugador["equipo"],
        "edad": datos_jugador.get("edad", "N/A"),
        "posicion": datos_jugador.get("pos_principal", datos_jugador.get("pos_secundaria", "N/A")),
        "valor_mercado": datos_jugador.get("valor_mercado", "Sin valor"),
        "scout_asignado": None,
        "prioridad": "media",  # Por defecto
        "proximo_partido": generar_proximo_partido(datos_jugador["equipo"]),
        "estado": "pendiente",
        "fecha_añadido": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "datos_wyscout": {
            "minutos": datos_jugador.get("min", 0),
            "goles": datos_jugador.get("goles", 0),
            "asistencias": datos_jugador.get("asistencias", 0),
            "partidos": datos_jugador.get("partidos_jugados", 0)
        }
    }
    
    # Añadir a la lista
    lista["jugadores_seguimiento"].append(nuevo_jugador)
    
    # Guardar
    if guardar_lista_visualizacion(lista):
        return True, "Jugador añadido correctamente a la lista de visualización"
    else:
        return False, "Error al guardar en la lista"

def obtener_estadisticas_lista():
    """Obtiene estadísticas rápidas de la lista de visualización"""
    lista = cargar_lista_visualizacion()
    jugadores = lista["jugadores_seguimiento"]
    
    total = len(jugadores)
    pendientes = len([j for j in jugadores if j["estado"] == "pendiente"])
    con_scout = len([j for j in jugadores if j["scout_asignado"] is not None])
    sin_scout = total - con_scout
    
    return {
        "total": total,
        "pendientes": pendientes,
        "con_scout": con_scout,
        "sin_scout": sin_scout
    }

def crear_card_jugador_compacta(jugador_data, tipo_recomendacion):
    """Crea una card compacta para el dashboard"""
    nombre = jugador_data.get('jugador_nombre', 'Jugador')
    equipo = jugador_data.get('equipo', 'N/A')
    nota = float(jugador_data.get('nota_promedio', jugador_data.get('nota_general', 0)) or 0)
    observaciones = int(jugador_data.get('veces_observado', jugador_data.get('id', 0)) or 0)
    
    # Determinar clase CSS según tipo
    css_class = {
        'contratar': 'fichar',
        'seguir_observando': 'recom-seguir',
        'interes_moderado': 'recom-cartera',
        'seguir': 'recom-seguir',
        'descartar': 'recom-descartar'
    }.get(tipo_recomendacion, 'recom-seguir')
    
    # Icono según recomendación
    icono = {
        'fichar': '🟢',
        'seguir_observando': '🟡',
        'interes_moderado': '🔵',
        'seguir': '🟡',
        'descartar': '🔴'
    }.get(tipo_recomendacion, '⚪')
    
    with st.container():
        st.markdown(f"""
        <div class="{css_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{icono} {nombre}</strong><br>
                    <small>{equipo}</small>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 18px; font-weight: bold; color: #2c3e50;">{nota:.1f}</div>
                    <small>{observaciones} obs.</small>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Botón para ver informe
        btn_key = f"ver_informe_{nombre}_{equipo}_{tipo_recomendacion}"
        if st.button("📄 Ver Informe", key=btn_key, use_container_width=True):
            st.session_state['jugador_para_informe'] = {
                'nombre': nombre,
                'equipo': equipo,
                'datos_completos': jugador_data
            }
            st.switch_page("pages/5_📋_Mis_Informes.py")

def crear_card_jugador_discovery(talento_data):
    """Crea una card elegante para el discovery hub con botón de lista de visualización"""
    nombre = talento_data.get('jugador', 'Jugador Desconocido')
    equipo = talento_data.get('equipo', 'N/A')
    edad = talento_data.get('edad', 'N/A')
    posicion = talento_data.get('pos_principal', talento_data.get('pos_secundaria', 'N/A'))
    
    # Función para convertir valores de forma segura
    def convertir_a_numero(valor, tipo='int'):
        try:
            if pd.isna(valor) or valor == '-' or valor == '' or valor is None:
                return 0
            if tipo == 'int':
                return int(float(valor))
            else:
                return float(valor)
        except (ValueError, TypeError):
            return 0
    
    # Estadísticas principales con conversión segura
    valor_mercado = convertir_a_numero(talento_data.get('valor_numerico', 0), 'float')
    minutos = convertir_a_numero(talento_data.get('min', 0))
    goles = convertir_a_numero(talento_data.get('goles', 0))
    asistencias = convertir_a_numero(talento_data.get('asistencias', 0))
    partidos = convertir_a_numero(talento_data.get('partidos_jugados', 0))
    
    # Formatear valor de mercado
    if valor_mercado > 0:
        if valor_mercado >= 1000000:
            valor_str = f"€{valor_mercado/1000000:.1f}M"
        elif valor_mercado >= 1000:
            valor_str = f"€{valor_mercado/1000:.0f}K"
        else:
            valor_str = f"€{valor_mercado:.0f}"
    else:
        valor_str = "Sin valor"
    
    # Calcular minutos por partido
    min_por_partido = int(minutos / partidos) if partidos > 0 else 0
    
    # Verificar si ya está en la lista
    ya_en_lista = jugador_ya_en_lista(nombre, equipo)
    
    # Crear card usando solo componentes Streamlit nativos
    with st.container(border=True):
        # Header con información del jugador
        col_header1, col_header2 = st.columns([3, 1])
        
        with col_header1:
            st.markdown(f"### 🌟 {nombre}")
            st.caption(f"**{posicion}** • {equipo} • {edad} años")
        
        with col_header2:
            if valor_mercado > 0:
                st.metric("💰 Valor", valor_str)
            else:
                st.metric("💰 Valor", "N/A")
        
        # Separador visual
        st.divider()
        
        # Estadísticas en métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="⏱️ Minutos",
                value=f"{minutos}'",
                help="Total de minutos jugados en la temporada"
            )
        
        with col2:
            st.metric(
                label="⚽ Goles",
                value=goles,
                help="Goles marcados en la temporada"
            )
        
        with col3:
            st.metric(
                label="🎯 Asistencias",
                value=asistencias,
                help="Asistencias realizadas en la temporada"
            )
        
        with col4:
            st.metric(
                label="📊 Partidos",
                value=partidos,
                help="Partidos disputados en la temporada"
            )
        
        with col5:
            st.metric(
                label="⏰ Min/PJ",
                value=f"{min_por_partido}'",
                help="Minutos promedio por partido"
            )
        
        # Separador y botón
        st.divider()
        
        # Botón de acción
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        with col_btn2:
            btn_key = f"añadir_lista_{nombre}_{equipo}_discovery"
            
            if ya_en_lista:
                # Si ya está en la lista, mostrar botón deshabilitado
                st.button(
                    "✅ Ya en Lista de Visualización",
                    key=btn_key,
                    use_container_width=True,
                    disabled=True,
                    help="Este jugador ya está en tu lista de visualización"
                )
            else:
                # Si no está, mostrar botón activo
                if st.button(
                    "👀 Añadir a Lista de Visualización",
                    key=btn_key,
                    use_container_width=True,
                    type="primary",
                    help="Añadir este jugador a tu lista para observar en próximos partidos"
                ):
                    # Preparar datos del jugador
                    datos_jugador = {
                        "jugador": nombre,
                        "equipo": equipo,
                        "edad": edad,
                        "pos_principal": posicion,
                        "valor_mercado": valor_str,
                        "min": minutos,
                        "goles": goles,
                        "asistencias": asistencias,
                        "partidos_jugados": partidos
                    }
                    
                    # Añadir a la lista
                    exito, mensaje = añadir_jugador_a_lista(datos_jugador)
                    
                    if exito:
                        st.success(f"✅ {mensaje}")
                        st.info("💡 Ve a la sección 'Lista de Visualización' para ver todos tus jugadores pendientes")
                        # Rerun para actualizar el estado del botón
                        st.rerun()
                    else:
                        st.error(f"❌ {mensaje}")
        
        # Información adicional en expander
        with st.expander("📈 Más detalles"):
            info_col1, info_col2 = st.columns(2)
            
            with info_col1:
                if goles > 0 and partidos > 0:
                    goles_por_partido = round(goles / partidos, 2)
                    st.write(f"⚽ **Goles por partido:** {goles_por_partido}")
                
                if asistencias > 0 and partidos > 0:
                    asist_por_partido = round(asistencias / partidos, 2)
                    st.write(f"🎯 **Asistencias por partido:** {asist_por_partido}")
            
            with info_col2:
                if minutos > 0:
                    st.write(f"⏱️ **Total minutos:** {minutos}'")
                
                participacion = round((minutos / (partidos * 90)) * 100, 1) if partidos > 0 else 0
                st.write(f"📊 **% Participación:** {participacion}%")

# ================================
# HEADER PRINCIPAL
# ================================
st.markdown("""
<div class="section-title">
    <h1>📊 DASHBOARD DE SCOUTING</h1>
    <p style="margin: 5px 0 0 0;">Vista ejecutiva del estado completo de scouting</p>
</div>
""", unsafe_allow_html=True)

# ================================
# PANEL DE CONTROL GENERAL
# ================================
st.markdown("## 📈 RESUMEN EJECUTIVO")

try:
    # Cargar datos
    todos_informes = cargar_todos_informes()
    stats = cargar_estadisticas_dashboard()
    
    if todos_informes and len(todos_informes) > 0:
        df_informes = pd.DataFrame(todos_informes)
        
        # Calcular métricas clave
        jugadores_unicos = len(df_informes['jugador_nombre'].unique())
        scouts_activos = len(df_informes['scout_usuario'].unique())
        nota_promedio = df_informes['nota_general'].mean()
        
        # Contar por recomendación
        recom_counts = df_informes['recomendacion'].value_counts()
        
        # Panel de métricas
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div style="font-size: 24px; font-weight: bold;">{jugadores_unicos}</div>
                <div>Jugadores Seguidos</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            contratar = recom_counts.get('fichar', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #28a745, #1e7e34);">
                <div style="font-size: 24px; font-weight: bold;">{contratar}</div>
                <div>Para Fichar</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            seguir = recom_counts.get('seguir_observando', 0) + recom_counts.get('seguir', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #ffc107, #e0a800);">
                <div style="font-size: 24px; font-weight: bold;">{seguir}</div>
                <div>En Seguimiento</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            cartera = recom_counts.get('interes_moderado', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #17a2b8, #117a8b);">
                <div style="font-size: 24px; font-weight: bold;">{cartera}</div>
                <div>En Cartera</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            descartados = recom_counts.get('descartar', 0)
            st.markdown(f"""
            <div class="metric-card" style="background: linear-gradient(135deg, #dc3545, #c82333);">
                <div style="font-size: 24px; font-weight: bold;">{descartados}</div>
                <div>Descartados</div>
            </div>
            """, unsafe_allow_html=True)
        
        # Actividad por scout
        st.markdown("### 👥 ACTIVIDAD POR SCOUT")
        
        scout_activity = df_informes.groupby('scout_usuario').agg({
            'id': 'count',
            'nota_general': 'mean',
            'jugador_nombre': 'nunique'
        }).reset_index()
        scout_activity.columns = ['scout', 'informes_totales', 'nota_promedio', 'jugadores_unicos']
        
        cols_scouts = st.columns(min(len(scout_activity), 4))
        
        for i, (_, scout) in enumerate(scout_activity.iterrows()):
            if i < 4:  # Máximo 4 scouts en pantalla
                with cols_scouts[i]:
                    st.markdown(f"""
                    <div class="scout-activity">
                        <strong>👤 {scout['scout']}</strong><br>
                        <span class="quick-stat">{scout['informes_totales']} informes</span>
                        <span class="quick-stat">{scout['jugadores_unicos']} jugadores</span><br>
                        <small>Nota promedio: {scout['nota_promedio']:.1f}/10</small>
                    </div>
                    """, unsafe_allow_html=True)
    
    else:
        st.info("📝 No hay informes de scouting disponibles")
        
except Exception as e:
    st.error(f"Error cargando resumen ejecutivo: {str(e)}")

# ================================
# ESTADO POR RECOMENDACIÓN
# ================================
st.markdown("---")
st.markdown("## 🎯 ESTADO POR RECOMENDACIÓN")

try:
    if todos_informes and len(todos_informes) > 0:
        df_informes = pd.DataFrame(todos_informes)
        
        # Agrupar por jugador y obtener última recomendación
        jugadores_agrupados = df_informes.groupby(['jugador_nombre', 'equipo']).agg({
            'nota_general': 'mean',
            'id': 'count',
            'recomendacion': 'last',  # Última recomendación
            'potencial': 'last',
            'fecha_creacion': 'max'
        }).reset_index()
        
        jugadores_agrupados.columns = ['jugador_nombre', 'equipo', 'nota_promedio', 'veces_observado', 'recomendacion', 'potencial', 'fecha_ultima']
        
        # Crear columnas para cada tipo de recomendación
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="section-title" style="background: linear-gradient(135deg, #28a745, #1e7e34); margin: 0 0 15px 0;">
                🟢 PARA CONTRATAR
            </div>
            """, unsafe_allow_html=True)
            
            contratar_jugadores = jugadores_agrupados[jugadores_agrupados['recomendacion'] == 'fichar']
            
            if not contratar_jugadores.empty:
                for _, jugador in contratar_jugadores.head(5).iterrows():
                    crear_card_jugador_compacta(jugador.to_dict(), 'contratar')
            else:
                st.info("Sin jugadores para contratar")
        
        with col2:
            st.markdown("""
            <div class="section-title" style="background: linear-gradient(135deg, #ffc107, #e0a800); margin: 0 0 15px 0;">
                🟡 SEGUIR OBSERVANDO
            </div>
            """, unsafe_allow_html=True)
            
            seguir_jugadores = jugadores_agrupados[
                (jugadores_agrupados['recomendacion'] == 'seguir_observando') |
                (jugadores_agrupados['recomendacion'] == 'seguir')
            ]
            
            if not seguir_jugadores.empty:
                for _, jugador in seguir_jugadores.head(5).iterrows():
                    crear_card_jugador_compacta(jugador.to_dict(), 'seguir_observando')
            else:
                st.info("Sin jugadores en seguimiento")
        
        with col3:
            st.markdown("""
            <div class="section-title" style="background: linear-gradient(135deg, #17a2b8, #117a8b); margin: 0 0 15px 0;">
                🔵 CARTERA FUTURIBLES
            </div>
            """, unsafe_allow_html=True)
            
            cartera_jugadores = jugadores_agrupados[jugadores_agrupados['recomendacion'] == 'interes_moderado']
            
            if not cartera_jugadores.empty:
                for _, jugador in cartera_jugadores.head(5).iterrows():
                    crear_card_jugador_compacta(jugador.to_dict(), 'interes_moderado')
            else:
                st.info("Sin jugadores en cartera")
        
        with col4:
            st.markdown("""
            <div class="section-title" style="background: linear-gradient(135deg, #dc3545, #c82333); margin: 0 0 15px 0;">
                🔴 DESCARTADOS
            </div>
            """, unsafe_allow_html=True)
            
            descartados_jugadores = jugadores_agrupados[jugadores_agrupados['recomendacion'] == 'descartar']
            
            if not descartados_jugadores.empty:
                for _, jugador in descartados_jugadores.head(5).iterrows():
                    crear_card_jugador_compacta(jugador.to_dict(), 'descartar')
            else:
                st.info("Sin jugadores descartados")
    
    else:
        st.info("📊 No hay datos de recomendaciones disponibles")
        
except Exception as e:
    st.error(f"Error cargando recomendaciones: {str(e)}")

# ================================
# DISCOVERY HUB - WYSCOUT SUB-23
# ================================
st.markdown("---")
st.markdown("## 💎 DISCOVERY HUB - TALENTOS EMERGENTES")
st.caption("Sub-23 de Wyscout sin observar - Futuros talentos a seguir")

try:
    # Cargar datos de Wyscout
    df_wyscout = cargar_datos_wyscout()
    
    if not df_wyscout.empty:
        # Filtrar Sub-23 (ya sabemos que edad está bien)
        if 'edad' in df_wyscout.columns:
            # Filtrar Sub-23, manejando valores nulos correctamente
            sub23_wyscout = df_wyscout[
                (df_wyscout['edad'] <= 22) & 
                (df_wyscout['edad'].notna())
            ].copy()
            
            # Obtener jugadores ya observados
            if todos_informes:
                df_informes = pd.DataFrame(todos_informes)
                jugadores_observados = set(df_informes['jugador_nombre'].unique())
                
                # Crear nombres completos para comparar
                sub23_wyscout['nombre_completo'] = sub23_wyscout['jugador'].fillna('') + ' ' + sub23_wyscout.get('apellidos', sub23_wyscout.get('jugador', ''))
                
                # Filtrar solo los NO observados
                sin_observar = sub23_wyscout[~sub23_wyscout['nombre_completo'].isin(jugadores_observados)]
            else:
                sin_observar = sub23_wyscout
            
            if not sin_observar.empty:
                st.info(f"🌟 {len(sin_observar)} talentos Sub-23 disponibles en Wyscout sin observar")
                
                # ================================
                # FILTROS AVANZADOS MEJORADOS
                # ================================
                st.markdown("### 🔍 **FILTROS DE BÚSQUEDA**")

                col_filter1, col_filter2, col_filter3 = st.columns(3)

                with col_filter1:
                    if 'liga' in sin_observar.columns:
                        ligas_disponibles = sin_observar['liga'].dropna().unique()
                        liga_filtro = st.selectbox(
                            "🏆 Liga:", 
                            ["Todas"] + sorted(list(ligas_disponibles)), 
                            key="discovery_liga"
                        )

                with col_filter2:
                    if 'pos_principal' in sin_observar.columns:
                        posiciones_disponibles = sin_observar['pos_principal'].dropna().unique()
                        pos_filtro = st.selectbox(
                            "⚽ Posición:", 
                            ["Todas"] + sorted(list(posiciones_disponibles)), 
                            key="discovery_pos"
                        )

                with col_filter3:
                    # Filtro de minutos
                    if 'min' in sin_observar.columns:
                        # Convertir minutos a números para el filtro
                        sin_observar['min_numericos'] = pd.to_numeric(sin_observar['min'], errors='coerce').fillna(0)
                        
                        min_minutos = int(sin_observar['min_numericos'].min())
                        max_minutos = int(sin_observar['min_numericos'].max())
                        
                        # Slider para rango de minutos
                        rango_minutos = st.slider(
                            "⏱️ Minutos jugados:",
                            min_value=min_minutos,
                            max_value=max_minutos,
                            value=(min_minutos, max_minutos),
                            step=100,
                            key="discovery_minutos",
                            help="Filtra jugadores por minutos jugados en la temporada"
                        )

                # Mostrar estadísticas de filtros
                col_stats1, col_stats2, col_stats3 = st.columns(3)

                with col_stats1:
                    st.metric(
                        "📊 Total disponibles", 
                        len(sin_observar),
                        help="Jugadores Sub-23 sin observar en total"
                    )

                # Aplicar todos los filtros
                sin_observar_filtrado = sin_observar.copy()

                # Filtro de liga
                if 'liga_filtro' in locals() and liga_filtro != "Todas":
                    sin_observar_filtrado = sin_observar_filtrado[sin_observar_filtrado['liga'] == liga_filtro]

                # Filtro de posición
                if 'pos_filtro' in locals() and pos_filtro != "Todas":
                    sin_observar_filtrado = sin_observar_filtrado[sin_observar_filtrado['pos_principal'] == pos_filtro]

                # Filtro de minutos
                if 'rango_minutos' in locals():
                    sin_observar_filtrado = sin_observar_filtrado[
                        (sin_observar_filtrado['min_numericos'] >= rango_minutos[0]) &
                        (sin_observar_filtrado['min_numericos'] <= rango_minutos[1])
                    ]

                # Mostrar estadísticas después del filtro
                with col_stats2:
                    st.metric(
                        "🎯 Después de filtros", 
                        len(sin_observar_filtrado),
                        delta=len(sin_observar_filtrado) - len(sin_observar),
                        help="Jugadores que cumplen los criterios de filtro"
                    )

                # AQUÍ ESTÁ LA CORRECCIÓN - Convertir y ordenar por valor de mercado
                if 'valor_de_mercado_(transfermarkt)' in sin_observar_filtrado.columns:
                    # Convertir valores de mercado de string a número
                    sin_observar_filtrado['valor_numerico'] = sin_observar_filtrado['valor_de_mercado_(transfermarkt)'].apply(convertir_valor_mercado)
                    sin_observar_filtrado = sin_observar_filtrado.sort_values(
                        'valor_numerico', 
                        ascending=False, 
                        na_position='last'
                    )

                with col_stats3:
                    if len(sin_observar_filtrado) > 0:
                        valor_promedio = sin_observar_filtrado['valor_numerico'].mean()
                        if valor_promedio > 0:
                            valor_promedio_str = f"€{valor_promedio/1000000:.1f}M"
                        else:
                            valor_promedio_str = "N/A"
                        
                        st.metric(
                            "💰 Valor promedio", 
                            valor_promedio_str,
                            help="Valor de mercado promedio de los jugadores filtrados"
                        )

                # Separador antes de mostrar jugadores
                st.markdown("---")
                
                # Mostrar top talentos
                if len(sin_observar_filtrado) > 0:
                    st.markdown(f"### 🌟 **TOP {min(8, len(sin_observar_filtrado))} TALENTOS FILTRADOS**")
                    for _, talento in sin_observar_filtrado.head(8).iterrows():
                        crear_card_jugador_discovery(talento.to_dict())
                else:
                    st.warning("🔍 No se encontraron jugadores que cumplan con los filtros seleccionados")
                    st.info("💡 **Sugerencia:** Ajusta los filtros para ver más resultados")
            
            else:
                st.success("🎉 ¡Todos los talentos Sub-23 ya están siendo observados!")
        
        else:
            st.warning("📊 Columna de edad no disponible en datos Wyscout")
    
    else:
        st.warning("📁 Datos de Wyscout no disponibles. Verifica el archivo Excel.")
        
except Exception as e:
    st.error(f"Error cargando discovery hub: {str(e)}")

# ================================
# ACCESOS RÁPIDOS (Sidebar)
# ================================
with st.sidebar:
    st.markdown("### 🚀 Acciones Rápidas")
    
    if st.button("📋 Ver Todos los Informes", use_container_width=True):
        st.switch_page("pages/5_📋_Mis_Informes.py")
    
    if st.button("📊 Análisis Avanzado", use_container_width=True):
        st.switch_page("pages/3_📊_Visualizaciones.py")
    
    st.markdown("---")
    
    # Estadísticas rápidas en sidebar
    try:
        if todos_informes:
            df_informes = pd.DataFrame(todos_informes)
            st.markdown("### 📈 Stats Rápidas")
            st.metric("📊 Total Informes", len(df_informes))
            st.metric("👥 Scouts Activos", len(df_informes['scout_usuario'].unique()))
            st.metric("⭐ Nota Promedio", f"{df_informes['nota_general'].mean():.1f}/10")
            
            # Último informe
            ultimo_informe = df_informes.sort_values('fecha_creacion').iloc[-1]
            st.markdown(f"""
            **🕒 Último informe:**  
            {ultimo_informe['jugador_nombre']}  
            por {ultimo_informe['scout_usuario']}
            """)
    except Exception:
        pass

    # Estadísticas de Lista de Visualización
    try:
        stats_lista = obtener_estadisticas_lista()
        st.markdown("### 👀 Lista de Visualización")
        st.metric("🎯 Total en Lista", stats_lista["total"])
        
        if stats_lista["total"] > 0:
            st.metric("⏳ Pendientes", stats_lista["pendientes"])
            st.metric("👤 Sin Scout Asignado", stats_lista["sin_scout"])
            
            if st.button("📋 Ver Lista Completa", use_container_width=True):
                st.switch_page("pages/6_👀_Lista_Visualizacion.py")
                
    except Exception:
        pass