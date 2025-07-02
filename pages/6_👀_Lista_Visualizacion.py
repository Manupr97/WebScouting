import streamlit as st
import pandas as pd
import json
from datetime import datetime
from common.login import LoginManager
from models.partido_model import PartidoModel

# Configuración de la página
st.set_page_config(
    page_title="Lista de Visualización - Scouting Pro",
    page_icon="👀",
    layout="wide"
)

# CSS personalizado
st.markdown("""
<style>
/* Cards para jugadores en lista */
.lista-card {
    background: linear-gradient(145deg, #ffffff, #f8f9fa);
    border-radius: 15px;
    padding: 20px;
    margin: 15px 0;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    border-left: 4px solid #007bff;
}

.lista-card-pendiente {
    border-left: 4px solid #ffc107;
}

.lista-card-asignado {
    border-left: 4px solid #28a745;
}

.lista-card-observacion {
    border-left: 4px solid #17a2b8;
}

.partido-info {
    background: linear-gradient(145deg, #e3f2fd, #bbdefb);
    border-radius: 10px;
    padding: 12px;
    margin: 10px 0;
    border-left: 3px solid #2196f3;
}

.prioridad-alta {
    background: linear-gradient(145deg, #ffebee, #ffcdd2);
    border-left: 3px solid #f44336;
    padding: 5px 10px;
    border-radius: 5px;
    margin: 5px 0;
}

.prioridad-media {
    background: linear-gradient(145deg, #fff3e0, #ffe0b2);
    border-left: 3px solid #ff9800;
    padding: 5px 10px;
    border-radius: 5px;
    margin: 5px 0;
}

.prioridad-baja {
    background: linear-gradient(145deg, #e8f5e8, #c8e6c9);
    border-left: 3px solid #4caf50;
    padding: 5px 10px;
    border-radius: 5px;
    margin: 5px 0;
}

.section-title {
    background: linear-gradient(135deg, #24282a, #34495e);
    color: white;
    padding: 15px;
    border-radius: 10px;
    text-align: center;
    margin: 20px 0 10px 0;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# Verificar autenticación
login_manager = LoginManager()
if not login_manager.is_authenticated():
    st.error("🔒 Debes iniciar sesión para acceder a esta página")
    st.stop()

# ================================
# FUNCIONES DE GESTIÓN DE LISTA
# ================================

def cargar_lista_visualizacion():
    """Carga la lista de jugadores en seguimiento desde JSON"""
    try:
        with open('data/lista_visualizacion.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"jugadores_seguimiento": []}

def guardar_lista_visualizacion(data):
    """Guarda la lista de jugadores en seguimiento en JSON"""
    try:
        import os
        os.makedirs('data', exist_ok=True)
        
        with open('data/lista_visualizacion.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Error guardando lista: {e}")
        return False

def asignar_scout_jugador(jugador_id, scout_nombre):
    """Asigna un scout a un jugador específico"""
    lista = cargar_lista_visualizacion()
    
    for jugador in lista["jugadores_seguimiento"]:
        if jugador["id"] == jugador_id:
            jugador["scout_asignado"] = scout_nombre
            jugador["estado"] = "asignado" if scout_nombre else "pendiente"
            break
    
    return guardar_lista_visualizacion(lista)

def cambiar_prioridad_jugador(jugador_id, nueva_prioridad):
    """Cambia la prioridad de un jugador"""
    lista = cargar_lista_visualizacion()
    
    for jugador in lista["jugadores_seguimiento"]:
        if jugador["id"] == jugador_id:
            jugador["prioridad"] = nueva_prioridad
            break
    
    return guardar_lista_visualizacion(lista)

def eliminar_jugador_lista(jugador_id):
    """Elimina un jugador de la lista de visualización"""
    lista = cargar_lista_visualizacion()
    
    lista["jugadores_seguimiento"] = [
        j for j in lista["jugadores_seguimiento"] 
        if j["id"] != jugador_id
    ]
    
    return guardar_lista_visualizacion(lista)

# ================================
# FUNCIONES DE CONEXIÓN CON INFORMES
# ================================

def verificar_informes_jugador(nombre_jugador, equipo_jugador):
    """Verifica si un jugador objetivo tiene informes creados"""
    try:
        from models.partido_model import PartidoModel
        partido_model = PartidoModel()
        
        # Obtener todos los informes del sistema
        todos_informes = partido_model.obtener_todos_informes()
        
        # Buscar informes de este jugador específico
        informes_jugador = []
        for informe in todos_informes:
            # Comparar nombres de manera flexible
            if (nombre_jugador.lower() in informe.get('jugador_nombre', '').lower() and 
                equipo_jugador.lower() in informe.get('equipo', '').lower()):
                informes_jugador.append({
                    'id': informe.get('id'),
                    'fecha': informe.get('fecha_creacion'),
                    'scout': informe.get('scout_usuario'),
                    'nota': informe.get('nota_general'),
                    'recomendacion': informe.get('recomendacion')
                })
        
        return {
            'tiene_informes': len(informes_jugador) > 0,
            'cantidad_informes': len(informes_jugador),
            'informes': informes_jugador,
            'ultimo_informe': informes_jugador[-1] if informes_jugador else None
        }
        
    except Exception as e:
        print(f"Error verificando informes: {e}")
        return {
            'tiene_informes': False,
            'cantidad_informes': 0,
            'informes': [],
            'ultimo_informe': None
        }

def actualizar_estado_por_informes(jugador_id, tiene_informes):
    """Actualiza el estado del jugador basado en si tiene informes"""
    lista = cargar_lista_visualizacion()
    
    for jugador in lista["jugadores_seguimiento"]:
        if jugador["id"] == jugador_id:
            if tiene_informes:
                if jugador["estado"] == "pendiente":
                    jugador["estado"] = "evaluado"
            break
    
    return guardar_lista_visualizacion(lista)

def obtener_estadisticas_evaluacion():
    """Obtiene estadísticas de evaluación de jugadores objetivo"""
    try:
        lista = cargar_lista_visualizacion()
        stats = {
            'total': 0,
            'evaluados': 0,
            'pendientes': 0,
            'sin_scout': 0,
            'con_informes': 0
        }
        
        jugadores = lista.get("jugadores_seguimiento", [])
        stats['total'] = len(jugadores)
        
        for jugador in jugadores:
            # Verificar informes
            try:
                info_informes = verificar_informes_jugador(jugador["jugador"], jugador["equipo"])
                
                if info_informes['tiene_informes']:
                    stats['con_informes'] += 1
                    stats['evaluados'] += 1
                else:
                    stats['pendientes'] += 1
            except:
                stats['pendientes'] += 1
            
            # Verificar scout asignado
            if not jugador.get("scout_asignado"):
                stats['sin_scout'] += 1
        
        return stats
        
    except Exception as e:
        # En caso de error, devolver valores por defecto
        return {
            'total': 0,
            'evaluados': 0,
            'pendientes': 0,
            'sin_scout': 0,
            'con_informes': 0
        }

# ================================
# FUNCIÓN PARA CREAR CARDS
# ================================

def crear_card_jugador_lista(jugador_data, scouts_disponibles):
    """Crea una card para gestionar jugadores en la lista con estado de informes"""
    
    # Verificar informes del jugador
    info_informes = verificar_informes_jugador(jugador_data["jugador"], jugador_data["equipo"])
    
    # Determinar clase CSS y estado según informes
    estado = jugador_data.get("estado", "pendiente")
    if info_informes['tiene_informes'] and estado == "pendiente":
        estado = "evaluado"
        # Actualizar en JSON
        actualizar_estado_por_informes(jugador_data["id"], True)
    
    css_class = {
        "pendiente": "lista-card lista-card-pendiente",
        "asignado": "lista-card lista-card-asignado", 
        "observacion": "lista-card lista-card-observacion",
        "evaluado": "lista-card lista-card-asignado"  # Verde para evaluados
    }.get(estado, "lista-card")
    
    # Información del partido
    st.info(f"⚽ **Próximo partido:** Pendiente de programación")
    
    with st.container(border=True):
        # Header con estado de informe
        col_header1, col_header2 = st.columns([2, 1])
        
        with col_header1:
            st.markdown(f"### 🌟 {jugador_data['jugador']}")
            st.caption(f"**{jugador_data['posicion']}** • {jugador_data['equipo']} • {jugador_data['edad']} años")
        
        with col_header2:
            st.metric("💰 Valor", jugador_data.get('valor_mercado', 'Sin valor'))
        
        # NUEVO: Estado de evaluación prominente
        if info_informes['tiene_informes']:
            st.success(f"✅ **EVALUADO** - {info_informes['cantidad_informes']} informe(s)")
            
            ultimo_informe = info_informes['ultimo_informe']
            if ultimo_informe:
                col_informe1, col_informe2 = st.columns(2)
                with col_informe1:
                    st.write(f"**Última nota:** {ultimo_informe['nota']}/10")
                with col_informe2:
                    st.write(f"**Scout:** {ultimo_informe['scout']}")
        else:
            st.warning("⏳ **PENDIENTE DE EVALUACIÓN**")
        
        # Información del próximo partido
        partido = jugador_data.get("proximo_partido", {})
        if partido and partido.get('fecha'):
            fecha_partido = partido.get('fecha', 'N/A')
            rival = partido.get('rival', 'N/A')
            estadio = partido.get('estadio', 'N/A')
            es_local = partido.get('es_local', True)
            local_visitante = "🏠 Local" if es_local else "✈️ Visitante"
            
            with st.expander("⚽ Información del próximo partido"):
                st.write(f"📅 **Fecha:** {fecha_partido}")
                st.write(f"🆚 **Rival:** {rival}")
                st.write(f"🏟️ **Estadio:** {estadio} • {local_visitante}")
        else:
            with st.expander("⚽ Próximo partido"):
                st.info("📅 Pendiente de programación")
        
        # Controles de gestión
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Asignación de scout
            scout_actual = jugador_data.get("scout_asignado", None)
            scout_index = 0
            
            if scout_actual:
                try:
                    scout_index = scouts_disponibles.index(scout_actual) + 1
                except ValueError:
                    scout_index = 0
            
            nuevo_scout = st.selectbox(
                "👤 Scout:",
                ["Sin asignar"] + scouts_disponibles,
                index=scout_index,
                key=f"scout_{jugador_data['id']}"
            )
            
            if st.button("✅ Asignar", key=f"asignar_{jugador_data['id']}"):
                scout_final = nuevo_scout if nuevo_scout != "Sin asignar" else None
                if asignar_scout_jugador(jugador_data["id"], scout_final):
                    st.success("Scout asignado")
                    st.rerun()
        
        with col2:
            # Cambio de prioridad
            prioridad_actual = jugador_data.get("prioridad", "media")
            prioridades = ["alta", "media", "baja"]
            prioridad_index = prioridades.index(prioridad_actual) if prioridad_actual in prioridades else 1
            
            nueva_prioridad = st.selectbox(
                "🎯 Prioridad:",
                prioridades,
                index=prioridad_index,
                key=f"prioridad_{jugador_data['id']}"
            )
            
            if st.button("🔄 Cambiar", key=f"cambiar_prio_{jugador_data['id']}"):
                if cambiar_prioridad_jugador(jugador_data["id"], nueva_prioridad):
                    st.success("Prioridad actualizada")
                    st.rerun()
        
        with col3:
            # Estado y acciones
            iconos_estado = {
                "pendiente": "⏳",
                "asignado": "👤", 
                "observacion": "👀",
                "evaluado": "✅"
            }
            
            icono = iconos_estado.get(estado, "❓")
            st.metric("Estado", f"{icono} {estado.title()}")
            
            # Botón para ver informes
            if info_informes['tiene_informes']:
                if st.button("📋 Ver Informes", key=f"ver_informes_{jugador_data['id']}", use_container_width=True):
                    # Mostrar informes en expander
                    with st.expander("📋 Informes de este jugador", expanded=True):
                        for i, informe in enumerate(info_informes['informes']):
                            st.write(f"**Informe #{i+1}**")
                            st.write(f"• **Fecha:** {informe['fecha']}")
                            st.write(f"• **Scout:** {informe['scout']}")
                            st.write(f"• **Nota:** {informe['nota']}/10")
                            st.write(f"• **Recomendación:** {informe['recomendacion']}")
                            st.write("---")
        
        with col4:
            # Botón eliminar
            if st.button("🗑️ Eliminar", key=f"eliminar_{jugador_data['id']}", type="secondary"):
                if eliminar_jugador_lista(jugador_data["id"]):
                    st.success("Jugador eliminado")
                    st.rerun()
        
        # Mostrar prioridad visual
        prioridad = jugador_data.get("prioridad", "media")
        emojis_prioridad = {"alta": "🔴", "media": "🟡", "baja": "🟢"}
        emoji = emojis_prioridad.get(prioridad, "⚪")
        
        col_prio1, col_prio2 = st.columns(2)
        with col_prio1:
            st.caption(f"{emoji} **Prioridad {prioridad.title()}**")
        with col_prio2:
            if info_informes['tiene_informes']:
                st.caption(f"📊 **{info_informes['cantidad_informes']} evaluación(es)**")
            else:
                st.caption("📝 **Sin evaluar**")
        
        # Estadísticas del jugador (en expander)
        with st.expander("📊 Estadísticas Wyscout"):
            datos_wyscout = jugador_data.get("datos_wyscout", {})
            
            col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
            
            with col_stat1:
                st.metric("⏱️ Minutos", f"{datos_wyscout.get('minutos', 0)}'")
            with col_stat2:
                st.metric("⚽ Goles", datos_wyscout.get('goles', 0))
            with col_stat3:
                st.metric("🎯 Asistencias", datos_wyscout.get('asistencias', 0))
            with col_stat4:
                st.metric("📊 Partidos", datos_wyscout.get('partidos', 0))

# ================================
# INTERFAZ PRINCIPAL
# ================================

# Header
st.markdown("""
<div class="section-title">
    <h1>👀 LISTA DE VISUALIZACIÓN</h1>
    <p style="margin: 5px 0 0 0;">Gestión de jugadores Sub-23 pendientes de observar</p>
</div>
""", unsafe_allow_html=True)

# Cargar datos
lista_data = cargar_lista_visualizacion()
jugadores = lista_data.get("jugadores_seguimiento", [])

# Estadísticas generales
if jugadores:
    # Calcular estadísticas básicas de forma segura
    total = len(jugadores)
    
    # Contar evaluados manualmente (más seguro)
    evaluados = 0
    pendientes = 0
    sin_scout = 0
    
    for jugador in jugadores:
        try:
            info_informes = verificar_informes_jugador(jugador["jugador"], jugador["equipo"])
            if info_informes and info_informes.get('tiene_informes', False):
                evaluados += 1
            else:
                pendientes += 1
        except:
            pendientes += 1
        
        if not jugador.get("scout_asignado"):
            sin_scout += 1
    
    con_scout = total - sin_scout
    
    # Panel de métricas
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("📊 Total en Lista", total)
    with col2:
        st.metric("✅ Evaluados", evaluados)
    with col3:
        st.metric("⏳ Pendientes", pendientes)
    with col4:
        st.metric("👤 Con Scout", con_scout)
    with col5:
        st.metric("📋 Con Informes", evaluados)  # Mismo que evaluados por ahora
    
    st.markdown("---")
    
    # Lista de scouts disponibles (puedes personalizar esto)
    scouts_disponibles = [
        "Juan Pérez", "María García", "Carlos López", "Ana Martín", 
        "Luis Rodríguez", "Elena Sánchez", "Pablo Torres"
    ]
    
    # Filtros básicos
    st.markdown("### 🔍 Filtros")
    col_filtro1, col_filtro2 = st.columns(2)
    
    with col_filtro1:
        filtro_estado = st.selectbox(
            "Estado:",
            ["Todos", "pendiente", "asignado", "observacion"]
        )
    
    with col_filtro2:
        filtro_prioridad = st.selectbox(
            "Prioridad:",
            ["Todas", "alta", "media", "baja"]
        )
    
    # Aplicar filtros
    jugadores_filtrados = jugadores.copy()
    
    if filtro_estado != "Todos":
        jugadores_filtrados = [j for j in jugadores_filtrados if j.get("estado", "pendiente") == filtro_estado]
    
    if filtro_prioridad != "Todas":
        jugadores_filtrados = [j for j in jugadores_filtrados if j.get("prioridad", "media") == filtro_prioridad]
    
    st.markdown(f"### 🎯 Mostrando {len(jugadores_filtrados)} de {total} jugadores")
    
    # Mostrar jugadores
    if jugadores_filtrados:
        for jugador in jugadores_filtrados:
            crear_card_jugador_lista(jugador, scouts_disponibles)
    else:
        st.info("🔍 No hay jugadores que coincidan con los filtros seleccionados")

else:
    # Si no hay jugadores en la lista
    st.info("📋 La lista de visualización está vacía")
    st.markdown("""
    ### 💡 ¿Cómo añadir jugadores?
    
    1. Ve al **Dashboard** → **Discovery Hub**
    2. Explora los talentos Sub-23 disponibles
    3. Haz clic en **"👀 Añadir a Lista de Visualización"**
    4. Los jugadores aparecerán aquí para gestionar
    
    """)
    
    if st.button("🚀 Ir a Discovery Hub", type="primary"):
        st.switch_page("pages/1_🔍_Jugadores.py")

# ================================
# SIDEBAR CON ACCIONES RÁPIDAS
# ================================

with st.sidebar:
    st.markdown("### 🚀 Acciones Rápidas")
    
    if st.button("🔙 Volver al Dashboard", use_container_width=True):
        st.switch_page("pages/1_🔍_Jugadores.py")
    
    if st.button("💎 Discovery Hub", use_container_width=True):
        st.switch_page("pages/1_🔍_Jugadores.py")  # Redirige al dashboard que tiene el discovery hub
    
    st.markdown("---")
    
    if jugadores:
        st.markdown("### 📈 Resumen Rápido")
        
        # Próximos partidos esta semana
        from datetime import datetime, timedelta
        hoy = datetime.now()
        una_semana = hoy + timedelta(days=7)
        
        partidos_semana = []
        for jugador in jugadores:
            partido = jugador.get("proximo_partido", {})
            if partido.get("fecha"):
                try:
                    fecha_partido = datetime.strptime(partido["fecha"], "%Y-%m-%d")
                    if hoy <= fecha_partido <= una_semana:
                        partidos_semana.append({
                            "jugador": jugador["jugador"],
                            "fecha": partido["fecha"],
                            "rival": partido.get("rival", "N/A")
                        })
                except:
                    pass
        
        if partidos_semana:
            st.markdown("**⚽ Partidos esta semana:**")
            for partido in partidos_semana:
                st.write(f"• {partido['jugador']} vs {partido['rival']}")
                st.caption(f"  📅 {partido['fecha']}")
        else:
            st.info("Sin partidos programados esta semana")