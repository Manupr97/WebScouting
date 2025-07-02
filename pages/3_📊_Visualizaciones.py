import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import sys
import os


# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Importar modelos necesarios
from common.login import LoginManager
from models.wyscout_model import WyscoutModel

# Configuración de la página
st.set_page_config(
    page_title="Visualizaciones - Scouting Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Personalizado con Paleta Corporativa
st.markdown("""
<style>
    /* Variables CSS */
    :root {
        --primary-color: #24282a;
        --secondary-color: #007bff;
        --background-light: #f8f9fa;
        --text-dark: #262730;
        --border-light: #e9ecef;
    }
    
    /* Header Personalizado */
    .custom-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, var(--secondary-color) 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.2);
    }
    
    .custom-header h1 {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        font-weight: 700;
    }
    
    .custom-header p {
        font-size: 1.1rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* Sidebar Styling */
    .sidebar-section {
        background: var(--background-light);
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
        border-left: 3px solid var(--secondary-color);
    }
    
    .sidebar-section h4 {
        color: var(--primary-color);
        margin-bottom: 0.8rem;
        font-size: 0.95rem;
        font-weight: 600;
    }
    
    /* Estados */
    .empty-state {
        text-align: center;
        padding: 3rem;
        background: var(--background-light);
        border-radius: 10px;
        border: 2px dashed var(--secondary-color);
    }
    
    .empty-state h3 {
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    /* Ocultar elementos de Streamlit */
    .stDeployButton { display: none; }
    footer { display: none; }
    .stApp > header { background-color: transparent; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# Verificar autenticación
login_manager = LoginManager()
if not login_manager.is_authenticated():
    st.error("🔒 Debes iniciar sesión para acceder a esta página")
    st.stop()

# Obtener usuario actual
current_user = login_manager.get_current_user()

# Header personalizado
st.markdown(f"""
<div class="custom-header">
    <h1>📊 Visualizaciones Interactivas</h1>
    <p>Análisis avanzado de rendimiento - Datos Wyscout LaLiga</p>
    <p style="font-size: 0.9rem; margin-top: 0.5rem;">Bienvenido/a, {current_user['nombre']} ({current_user['rol']})</p>
</div>
""", unsafe_allow_html=True)

# Función para limpiar y procesar datos
@st.cache_data
def load_and_clean_data():
    """Cargar y limpiar datos de Wyscout con manejo robusto de errores"""
    wyscout_model = WyscoutModel()
    df_raw = wyscout_model.get_all_players()
    
    if df_raw.empty:
        return pd.DataFrame(), {}, {}, wyscout_model
    
    # Copiar datos para trabajar
    df = df_raw.copy()
    
    # Limpiar datos problemáticos
    # Convertir '-' y valores no numéricos a NaN en columnas numéricas
    for col in df.columns:
        if df[col].dtype == 'object':
            # Intentar convertir a numérico si es posible
            try:
                # Reemplazar '-' y valores no válidos
                df[col] = df[col].replace(['-', '', 'N/A', 'nan', 'null'], np.nan)
                # Intentar conversión numérica
                df_numeric = pd.to_numeric(df[col], errors='ignore')
                if df_numeric.notna().sum() > 0 and df_numeric.dtype in ['int64', 'float64']:
                    df[col] = df_numeric
            except:
                pass
    
    # Definir columnas principales con nombres exactos del dataset
    detected_columns = {
        'player': 'jugador',
        'team': 'equipo_durante_el_período_seleccionado',
        'position': 'pos_principal', 
        'age': 'edad'
    }
    
    # Verificar que las columnas existen
    for key, col_name in detected_columns.items():
        if col_name not in df.columns:
            st.warning(f"⚠️ Columna '{col_name}' no encontrada en el dataset")
    
    # Obtener resumen
    summary = {
        'total_players': len(df),
        'total_teams': df[detected_columns['team']].nunique() if detected_columns['team'] in df.columns else 0,
        'total_positions': df[detected_columns['position']].nunique() if detected_columns['position'] in df.columns else 0,
        'age_stats': df[detected_columns['age']].describe().to_dict() if detected_columns['age'] in df.columns else {}
    }
    
    return df, detected_columns, summary, wyscout_model

# Función para obtener columnas numéricas válidas
def get_numeric_columns(df):
    """Obtener solo columnas verdaderamente numéricas"""
    numeric_cols = []
    for col in df.columns:
        if df[col].dtype in ['int64', 'float64']:
            # Verificar que tiene valores válidos
            if df[col].notna().sum() > 0:
                numeric_cols.append(col)
    return numeric_cols

# Función para formatear valores
def format_value(value):
    """Formatear valores para mostrar de manera limpia"""
    if pd.isna(value):
        return "N/A"
    
    try:
        num_value = float(value)
        # Si es un entero, mostrarlo como entero
        if num_value.is_integer() and abs(num_value) < 10000:
            return str(int(num_value))
        # Si es decimal, máximo 2 decimales
        elif abs(num_value) < 1:
            return f"{num_value:.3f}"
        else:
            return f"{num_value:.1f}"
    except:
        return str(value)

# Definir métricas relevantes para scouting USANDO NOMBRES EXACTOS DEL DATASET
SCOUTING_METRICS = {
    'Rendimiento Ofensivo': {
        'metrics': ['goles', 'goles/90', 'xg', 'xg/90', 'asistencias', 'asistencias/90', 'xa', 'xa/90', 
                   'remates', 'remates/90', '%tiros_a_la_portería,_', 'goles_ex_pen'],
        'icon': '⚽',
        'description': 'Capacidad goleadora y contribución ofensiva'
    },
    'Creatividad y Pases': {
        'metrics': ['pases/90', '%precisión_pases,_', 'pases_largos/90', '%precisión_pases_largos,_',
                   'pases_en_profundidad/90', '%precisión_pases_en_profundidad,_', 'jugadas_claves/90',
                   'pases_al_área_de_penalti/90', 'pases_progre/90'],
        'icon': '🎯',
        'description': 'Creación de juego y distribución de balón'
    },
    'Duelos y Defensa': {
        'metrics': ['duelos/90', '%duelos_ganados,_', 'duelos_def/90', '%duelos_defensivos_ganados,_',
                   'duelos_aéreos_en_los_90', '%duelos_aéreos_ganados,_', 'entradas/90', 'intercep/90'],
        'icon': '🛡️',
        'description': 'Capacidad defensiva y recuperación de balón'
    },
    'Movilidad y Técnica': {
        'metrics': ['regates/90', '%regates_realizados,_', 'carreras_en_progresión/90', 'aceleraciones/90',
                   'faltas_recibidas/90', 'desmarques/90'],
        'icon': '⚡',
        'description': 'Habilidad técnica y capacidad de progresión'
    },
    'Porteros': {
        'metrics': ['goles_recibidos', 'goles_recibidos/90', '%paradas,_', 'xg_en_contra', 'xg_en_contra/90',
                   'goles_evitados', 'goles_evitados/90', 'salidas/90', 'pases_rec_por/90'],
        'icon': '🥅',
        'description': 'Estadísticas específicas de porteros'
    },
    'Físico y Disciplina': {
        'metrics': ['altura', 'peso', 'faltas/90', 'tarjetas_amarillas', 'tarjetas_rojas'],
        'icon': '💪',
        'description': 'Aspectos físicos y disciplinarios'
    }
}

# Cargar datos
with st.spinner("🔄 Cargando y procesando datos de Wyscout..."):
    df, detected_columns, summary, wyscout_model = load_and_clean_data()

# Verificar si hay datos
if df.empty:
    st.error("❌ **No se pudieron cargar los datos de Wyscout**")
    
    with st.expander("🔧 Información de Diagnóstico", expanded=True):
        st.write("**Verifica que el archivo `wyscout_LaLiga_limpio.xlsx` esté en la carpeta `data/`**")
        
        data_path = os.path.join(parent_dir, "data", "wyscout_LaLiga_limpio.xlsx")
        st.write(f"**Buscando archivo en:** `{data_path}`")
        st.write(f"**¿Existe?** {'✅ Sí' if os.path.exists(data_path) else '❌ No'}")
    
    st.stop()

# Dashboard de métricas principales
st.markdown("### 📊 Dashboard Principal")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        label="👥 Total Jugadores",
        value=f"{summary.get('total_players', 0):,}",
        help="Jugadores en el dataset de Wyscout LaLiga"
    )

with col2:
    st.metric(
        label="🏟️ Equipos",
        value=summary.get('total_teams', 0),
        help="Equipos de LaLiga en el dataset"
    )

with col3:
    st.metric(
        label="⚽ Posiciones",
        value=summary.get('total_positions', 0),
        help="Posiciones diferentes detectadas"
    )

with col4:
    age_stats = summary.get('age_stats', {})
    avg_age = age_stats.get('mean', 0)
    st.metric(
        label="📈 Edad Promedio",
        value=f"{avg_age:.1f} años" if avg_age else "N/A",
        help="Edad promedio de todos los jugadores"
    )

st.markdown("---")

# Sidebar con filtros mejorados
with st.sidebar:
    st.markdown("## 🎯 Panel de Control")
    
    # Tipo de análisis
    st.markdown("### 📈 Tipo de Análisis")
    tipo_analisis = st.selectbox(
        "Selecciona el análisis:",
        [
            "🎯 Radar Individual - Personalizado",
            "📊 Comparación Múltiple Avanzada",
            "📈 Análisis de Dispersión - Scout",
            "🏟️ Rendimiento por Equipo",
            "🔥 Mapa de Correlaciones",
            "🔍 Explorador de Jugadores"
        ],
        help="Selecciona el tipo de análisis que deseas realizar"
    )
    
    st.markdown("---")
    
    # Filtros principales
    st.markdown("### 🔍 Filtros de Datos")
    
    # Obtener nombres de columnas principales
    player_col = detected_columns.get('player')
    team_col = detected_columns.get('team') 
    position_col = detected_columns.get('position')
    age_col = detected_columns.get('age')
    
    # Búsqueda de jugador
    player_search = ""
    if player_col and player_col in df.columns:
        st.markdown("#### 👤 Buscar Jugador")
        player_search = st.text_input(
            "Buscar jugador:",
            placeholder="Ej: Mbappé, Bellingham...",
            help=f"Buscar en: {player_col}"
        )
    
    # Filtro por equipos
    selected_teams = []
    if team_col and team_col in df.columns:
        st.markdown("#### 🏟️ Equipos")
        teams = sorted(df[team_col].dropna().unique().tolist())
        selected_teams = st.multiselect(
            "Seleccionar equipos:",
            options=teams,
            default=[],
            help=f"Filtrar por: {team_col}"
        )
    
    # Filtro por posiciones
    selected_positions = []
    if position_col and position_col in df.columns:
        st.markdown("#### ⚽ Posiciones")
        positions = sorted(df[position_col].dropna().unique().tolist())
        selected_positions = st.multiselect(
            "Seleccionar posiciones:",
            options=positions,
            default=[],
            help=f"Filtrar por: {position_col}"
        )
    
    # Filtro por edad
    age_range = None
    if age_col and age_col in df.columns:
        age_data = df[age_col].dropna()
        if not age_data.empty:
            st.markdown("#### 📊 Edad")
            min_age = int(age_data.min())
            max_age = int(age_data.max())
            age_range = st.slider(
                "Rango de edad:",
                min_value=min_age,
                max_value=max_age,
                value=(min_age, max_age),
                help=f"Filtrar por: {age_col}"
            )
    
    # Filtros avanzados
    st.markdown("---")
    st.markdown("### ⚙️ Filtros Avanzados")
    
    # Filtro por minutos jugados
    min_col = 'min' if 'min' in df.columns else None
    min_minutes = 0
    if min_col:
        min_minutes = st.number_input(
            "⏱️ Minutos mínimos jugados:",
            min_value=0,
            value=0,
            step=100,
            help="Filtrar jugadores con mínimo de minutos jugados"
        )
    
    # Filtro por partidos jugados
    partidos_col = 'partidos_jugados' if 'partidos_jugados' in df.columns else None
    min_matches = 0
    if partidos_col:
        min_matches = st.number_input(
            "🏟️ Partidos mínimos jugados:",
            min_value=0,
            value=0,
            step=1,
            help="Filtrar jugadores con mínimo de partidos jugados"
        )
    
    # Selector de categoría de métricas para análisis
    if "Radar" in tipo_analisis or "Comparación" in tipo_analisis:
        st.markdown("#### 📊 Categoría de Análisis")
        selected_category = st.selectbox(
            "Enfoque del análisis:",
            list(SCOUTING_METRICS.keys()),
            help="Selecciona el aspecto del juego a analizar"
        )
    
    # Información de filtros aplicados
    st.markdown("---")
    st.markdown("### 📋 Resumen de Filtros")
    
    filter_count = 0
    if player_search: filter_count += 1
    if selected_teams: filter_count += 1
    if selected_positions: filter_count += 1
    if min_minutes > 0: filter_count += 1
    if min_matches > 0: filter_count += 1
    
    st.write(f"**Filtros activos:** {filter_count}")
    
    if st.button("🗑️ Limpiar Todos los Filtros", use_container_width=True):
        st.rerun()

# Aplicar filtros
def apply_filters_advanced(df, filters_dict):
    """Aplicar filtros avanzados al dataframe"""
    filtered_df = df.copy()
    
    # Filtro por búsqueda de jugador
    if filters_dict.get('player_search') and player_col:
        search_term = filters_dict['player_search'].lower()
        mask = filtered_df[player_col].astype(str).str.lower().str.contains(search_term, na=False)
        filtered_df = filtered_df[mask]
    
    # Filtro por equipos
    if filters_dict.get('teams') and team_col:
        filtered_df = filtered_df[filtered_df[team_col].isin(filters_dict['teams'])]
    
    # Filtro por posiciones
    if filters_dict.get('positions') and position_col:
        filtered_df = filtered_df[filtered_df[position_col].isin(filters_dict['positions'])]
    
    # Filtro por edad
    if filters_dict.get('age_range') and age_col:
        min_age, max_age = filters_dict['age_range']
        filtered_df = filtered_df[
            (filtered_df[age_col] >= min_age) & 
            (filtered_df[age_col] <= max_age)
        ]
    
    # Filtro por minutos jugados
    if filters_dict.get('min_minutes', 0) > 0 and min_col:
        filtered_df = filtered_df[filtered_df[min_col] >= filters_dict['min_minutes']]
    
    # Filtro por partidos jugados
    if filters_dict.get('min_matches', 0) > 0 and partidos_col:
        filtered_df = filtered_df[filtered_df[partidos_col] >= filters_dict['min_matches']]
    
    return filtered_df

# Preparar filtros
filters = {
    'player_search': player_search,
    'teams': selected_teams,
    'positions': selected_positions, 
    'age_range': age_range,
    'min_minutes': min_minutes,
    'min_matches': min_matches
}

# Aplicar filtros
with st.spinner("🔄 Aplicando filtros..."):
    df_filtered = apply_filters_advanced(df, filters)

# Mostrar información de filtrado
st.markdown("### 📊 Datos Filtrados")

info_col1, info_col2, info_col3 = st.columns(3)
with info_col1:
    st.metric("📋 Jugadores Filtrados", f"{len(df_filtered):,}")
with info_col2:
    percentage = (len(df_filtered) / len(df)) * 100 if len(df) > 0 else 0
    st.metric("📊 Porcentaje del Total", f"{percentage:.1f}%")
with info_col3:
    if team_col and team_col in df_filtered.columns:
        unique_teams = df_filtered[team_col].nunique()
        st.metric("🏟️ Equipos Representados", unique_teams)

# Verificar si hay datos filtrados
if df_filtered.empty:
    st.markdown("""
    <div class="empty-state">
        <h3>⚠️ Sin Resultados</h3>
        <p>No se encontraron jugadores con los filtros aplicados.</p>
        <p style="font-size: 0.9rem; color: #6c757d; margin-top: 0.5rem;">
            Intenta modificar o eliminar algunos filtros para obtener resultados.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

st.markdown("---")

# Función auxiliar para obtener métricas disponibles con validación
def get_available_metrics(df, category_metrics):
    """Obtener métricas disponibles en el dataframe para una categoría"""
    available = []
    numeric_cols = get_numeric_columns(df)
    
    for metric in category_metrics:
        if metric in df.columns and metric in numeric_cols:
            # Verificar que tiene datos válidos
            if df[metric].notna().sum() > 5:  # Al menos 5 valores válidos
                available.append(metric)
    
    return available[:8]  # Máximo 8 para visualizaciones

# CONTENIDO PRINCIPAL SEGÚN TIPO DE ANÁLISIS
if "Radar" in tipo_analisis:
    st.markdown("### 🎯 Análisis de Radar Individual - Personalizado")
    st.markdown(f"**Enfoque:** {SCOUTING_METRICS[selected_category]['icon']} {selected_category}")
    st.markdown(f"*{SCOUTING_METRICS[selected_category]['description']}*")
    
    # Selector de jugador
    if player_col and player_col in df_filtered.columns:
        player_options = sorted(df_filtered[player_col].dropna().unique().tolist())
        
        if player_options:
            selected_player = st.selectbox(
                "👤 Seleccionar Jugador:",
                player_options,
                help="Jugador para análisis de radar personalizado"
            )
            
            # Obtener métricas relevantes para la categoría seleccionada
            category_metrics = SCOUTING_METRICS[selected_category]['metrics']
            available_metrics = get_available_metrics(df_filtered, category_metrics)
            
            if len(available_metrics) >= 3:
                # Permitir selección personalizada de métricas
                st.markdown("#### 📊 Personalizar Métricas del Radar")
                selected_metrics = st.multiselect(
                    "Selecciona las métricas para el radar:",
                    available_metrics,
                    default=available_metrics[:6],
                    max_selections=8,
                    help="Máximo 8 métricas para el gráfico de radar"
                )
                
                if selected_metrics:
                    # Obtener datos del jugador
                    player_data = df_filtered[df_filtered[player_col] == selected_player].iloc[0]
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        # Crear gráfico de radar mejorado
                        categories = []
                        values = []
                        
                        for metric in selected_metrics:
                            if metric in player_data.index and pd.notna(player_data[metric]):
                                # Normalizar valores (0-100) basado en percentiles
                                metric_data = df_filtered[metric].dropna()
                                if len(metric_data) > 1:
                                    percentile = (metric_data <= player_data[metric]).mean() * 100
                                else:
                                    percentile = 50
                                
                                # Limpiar nombre de métrica para mostrar
                                clean_name = metric.replace('_', ' ').replace('/', ' / ').replace(',_', '').title()
                                categories.append(clean_name)
                                values.append(min(max(percentile, 0), 100))
                        
                        if categories and values:
                            # Crear gráfico de radar más visual
                            fig = go.Figure()
                            
                            fig.add_trace(go.Scatterpolar(
                                r=values,
                                theta=categories,
                                fill='toself',
                                name=selected_player,
                                line=dict(color='#007bff', width=4),
                                fillcolor='rgba(0, 123, 255, 0.25)',
                                marker=dict(color='#007bff', size=8)
                            ))
                            
                            fig.update_layout(
                                polar=dict(
                                    radialaxis=dict(
                                        visible=True,
                                        range=[0, 100],
                                        tickfont=dict(size=12, color='#666'),
                                        tickvals=[25, 50, 75, 100],
                                        ticktext=['25%', '50%', '75%', '100%'],
                                        gridcolor='rgba(0,0,0,0.1)'
                                    ),
                                    angularaxis=dict(
                                        tickfont=dict(size=12, color='#333'),
                                        linecolor='rgba(0,0,0,0.2)'
                                    ),
                                    bgcolor='rgba(255,255,255,0.8)'
                                ),
                                showlegend=True,
                                title=dict(
                                    text=f"Perfil de Rendimiento: {selected_player}",
                                    font=dict(size=18, color='#24282a'),
                                    x=0.5
                                ),
                                height=650,
                                font=dict(size=12),
                                paper_bgcolor='white',
                                plot_bgcolor='white'
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Explicación del percentil
                            st.caption("📊 **Valores en percentiles:** 100% = mejor del dataset, 0% = peor del dataset")
                    
                    with col2:
                        st.markdown("#### 📋 Información del Jugador")
                        
                        # Información básica
                        basic_info = {}
                        if team_col and team_col in player_data.index:
                            basic_info[f"🏟️ Equipo"] = player_data[team_col]
                        if position_col and position_col in player_data.index:
                            basic_info[f"⚽ Posición"] = player_data[position_col]
                        if age_col and age_col in player_data.index:
                            basic_info[f"📊 Edad"] = f"{player_data[age_col]} años"
                        
                        for label, value in basic_info.items():
                            st.write(f"**{label}:** {value}")
                        
                        st.markdown("#### 📈 Valores Reales")
                        
                        # Mostrar valores reales de las métricas seleccionadas
                        for metric in selected_metrics[:6]:
                            if metric in player_data.index and pd.notna(player_data[metric]):
                                raw_value = player_data[metric]
                                # Calcular percentil para mostrar
                                metric_data = df_filtered[metric].dropna()
                                percentile = (metric_data <= raw_value).mean() * 100 if len(metric_data) > 1 else 50
                                
                                formatted_value = format_value(raw_value)
                                clean_metric_name = metric.replace('_', ' ').replace('/', ' / ').replace(',_', '').title()
                                st.write(f"**{clean_metric_name}:** {formatted_value} ({percentile:.0f}%)")
                else:
                    st.warning("⚠️ Selecciona al menos 3 métricas para crear el radar")
            else:
                st.warning(f"⚠️ No hay suficientes métricas numéricas disponibles para {selected_category}")
                if available_metrics:
                    st.info(f"Métricas disponibles: {', '.join(available_metrics)}")
        else:
            st.warning("⚠️ No hay jugadores disponibles con los filtros aplicados")
    else:
        st.error("❌ No se detectó columna de jugadores")

elif "Comparación" in tipo_analisis:
    st.markdown("### 📊 Comparación Múltiple Avanzada")
    st.markdown(f"**Enfoque:** {SCOUTING_METRICS[selected_category]['icon']} {selected_category}")
    
    if player_col and player_col in df_filtered.columns:
        player_options = sorted(df_filtered[player_col].dropna().unique().tolist())
        
        # Seleccionar múltiples jugadores
        selected_players = st.multiselect(
            "👥 Seleccionar Jugadores a Comparar:",
            player_options,
            default=[],
            max_selections=5,
            help="Selecciona entre 2 y 5 jugadores"
        )
        
        if len(selected_players) >= 2:
            # Obtener métricas para la categoría
            category_metrics = SCOUTING_METRICS[selected_category]['metrics']
            available_metrics = get_available_metrics(df_filtered, category_metrics)
            
            if available_metrics:
                selected_stats = st.multiselect(
                    "📊 Métricas a Comparar:",
                    available_metrics,
                    default=available_metrics[:5],
                    help="Selecciona las métricas para comparar"
                )
                
                if selected_stats:
                    # Tipo de comparación
                    comparison_type = st.radio(
                        "📈 Tipo de Comparación:",
                        ["Valores Absolutos", "Percentiles", "Radar Múltiple"],
                        horizontal=True,
                        help="Selecciona cómo quieres comparar las métricas"
                    )
                    
                    if comparison_type == "Radar Múltiple":
                        # Radar con múltiples jugadores
                        fig = go.Figure()
                        
                        colors = ['#007bff', '#28a745', '#ffc107', '#dc3545', '#6f42c1']
                        
                        for i, player in enumerate(selected_players):
                            player_data = df_filtered[df_filtered[player_col] == player].iloc[0]
                            
                            categories = []
                            values = []
                            
                            for metric in selected_stats:
                                if metric in player_data.index and pd.notna(player_data[metric]):
                                    metric_data = df_filtered[metric].dropna()
                                    percentile = (metric_data <= player_data[metric]).mean() * 100
                                    
                                    clean_name = metric.replace('_', ' ').replace('/', ' / ').replace(',_', '').title()
                                    categories.append(clean_name)
                                    values.append(min(max(percentile, 0), 100))
                            
                            if categories and values:
                                fig.add_trace(go.Scatterpolar(
                                    r=values,
                                    theta=categories,
                                    fill='toself',
                                    name=player,
                                    line=dict(color=colors[i % len(colors)], width=3),
                                    fillcolor=f'rgba({int(colors[i % len(colors)][1:3], 16)}, {int(colors[i % len(colors)][3:5], 16)}, {int(colors[i % len(colors)][5:7], 16)}, 0.15)'
                                ))
                        
                        fig.update_layout(
                            polar=dict(
                                radialaxis=dict(
                                    visible=True,
                                    range=[0, 100],
                                    tickvals=[25, 50, 75, 100],
                                    ticktext=['25%', '50%', '75%', '100%']
                                )
                            ),
                            title=f"Comparación Radar: {selected_category}",
                            height=600
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                    else:
                        # Gráfico de barras
                        comparison_data = []
                        
                        for player in selected_players:
                            player_data = df_filtered[df_filtered[player_col] == player].iloc[0]
                            for stat in selected_stats:
                                if stat in player_data.index and pd.notna(player_data[stat]):
                                    value = player_data[stat]
                                    
                                    if comparison_type == "Percentiles":
                                        # Convertir a percentil
                                        metric_data = df_filtered[stat].dropna()
                                        value = (metric_data <= value).mean() * 100
                                    
                                    clean_stat_name = stat.replace('_', ' ').replace('/', ' / ').replace(',_', '').title()
                                    comparison_data.append({
                                        'Jugador': player,
                                        'Métrica': clean_stat_name,
                                        'Valor': value
                                    })
                        
                        if comparison_data:
                            comparison_df = pd.DataFrame(comparison_data)
                            
                            fig = px.bar(
                                comparison_df,
                                x='Métrica',
                                y='Valor',
                                color='Jugador',
                                barmode='group',
                                title=f"Comparación {comparison_type}: {selected_category}",
                                color_discrete_sequence=px.colors.qualitative.Set1
                            )
                            
                            fig.update_layout(
                                height=500,
                                xaxis_tickangle=-45
                            )
                            
                            if comparison_type == "Percentiles":
                                fig.update_yaxes(title="Percentil (%)", range=[0, 100])
                            
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # Tabla de comparación
                            st.markdown("#### 📋 Tabla de Comparación Detallada")
                            pivot_df = comparison_df.pivot(index='Métrica', columns='Jugador', values='Valor')
                            # Formatear valores
                            for col in pivot_df.columns:
                                pivot_df[col] = pivot_df[col].apply(lambda x: format_value(x) if pd.notna(x) else "N/A")
                            st.dataframe(pivot_df, use_container_width=True)
                else:
                    st.warning("⚠️ Selecciona métricas para comparar")
            else:
                st.warning(f"⚠️ No hay métricas numéricas disponibles para {selected_category}")
        elif len(selected_players) == 1:
            st.info("ℹ️ Selecciona al menos 2 jugadores para comparar")
        else:
            st.info("ℹ️ Selecciona jugadores para comenzar la comparación")

elif "Dispersión" in tipo_analisis:
    st.markdown("### 📈 Análisis de Dispersión - Scout")
    st.markdown("Herramienta personalizable para scouts: selecciona las métricas que quieres analizar")
    
    # Obtener todas las métricas numéricas disponibles
    all_numeric_cols = get_numeric_columns(df_filtered)
    relevant_metrics = [col for col in all_numeric_cols if not col.lower().endswith('_id')]
    
    if len(relevant_metrics) >= 2:
        # Interfaz de selección para scouts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📈 Métrica Principal (Eje X)")
            x_metric = st.selectbox(
                "Selecciona métrica X:",
                relevant_metrics,
                help="Métrica que se mostrará en el eje horizontal"
            )
            
            # Filtros específicos para X
            if x_metric:
                x_data = df_filtered[x_metric].dropna()
                if len(x_data) > 0:
                    x_min, x_max = float(x_data.min()), float(x_data.max())
                    x_range = st.slider(
                        f"Rango de {x_metric.replace('_', ' ').title()}:",
                        min_value=x_min,
                        max_value=x_max,
                        value=(x_min, x_max),
                        help="Filtrar jugadores por este rango"
                    )
        
        with col2:
            st.markdown("#### 📊 Métrica Secundaria (Eje Y)")
            y_options = [col for col in relevant_metrics if col != x_metric]
            y_metric = st.selectbox(
                "Selecciona métrica Y:",
                y_options,
                help="Métrica que se mostrará en el eje vertical"
            )
            
            # Filtros específicos para Y
            if y_metric:
                y_data = df_filtered[y_metric].dropna()
                if len(y_data) > 0:
                    y_min, y_max = float(y_data.min()), float(y_data.max())
                    y_range = st.slider(
                        f"Rango de {y_metric.replace('_', ' ').title()}:",
                        min_value=y_min,
                        max_value=y_max,
                        value=(y_min, y_max),
                        help="Filtrar jugadores por este rango"
                    )
        
        if x_metric and y_metric:
            # Opciones de visualización
            st.markdown("#### ⚙️ Opciones de Visualización")
            viz_col1, viz_col2, viz_col3 = st.columns(3)
            
            with viz_col1:
                size_by = st.selectbox(
                    "📏 Tamaño de puntos por:",
                    ["Uniforme"] + [col for col in relevant_metrics if col not in [x_metric, y_metric]][:6],
                    help="Variar tamaño de puntos según esta métrica para análisis adicional"
                )
                if size_by == "Uniforme":
                    size_by = None
            
            with viz_col2:
                show_trendline = st.checkbox(
                    "📈 Línea de tendencia",
                    value=True,
                    help="Mostrar línea de tendencia estadística"
                )
            
            with viz_col3:
                show_averages = st.checkbox(
                    "📊 Líneas promedio",
                    value=True,
                    help="Mostrar líneas promedio de cada métrica para dividir en cuadrantes"
                )
            
            # Aplicar filtros de rango
            filtered_scatter_df = df_filtered.copy()
            if 'x_range' in locals():
                filtered_scatter_df = filtered_scatter_df[
                    (filtered_scatter_df[x_metric] >= x_range[0]) & 
                    (filtered_scatter_df[x_metric] <= x_range[1])
                ]
            if 'y_range' in locals():
                filtered_scatter_df = filtered_scatter_df[
                    (filtered_scatter_df[y_metric] >= y_range[0]) & 
                    (filtered_scatter_df[y_metric] <= y_range[1])
                ]
            
            if not filtered_scatter_df.empty:
                # Crear gráfico de dispersión personalizado
                fig_scatter = px.scatter(
                    filtered_scatter_df,
                    x=x_metric,
                    y=y_metric,
                    size=size_by,
                    title=f"Análisis Scout: {x_metric.replace('_', ' ').title()} vs {y_metric.replace('_', ' ').title()}",
                    trendline="ols" if show_trendline else None,
                    hover_data=[player_col, team_col, position_col] if all([player_col, team_col, position_col]) else None,
                    labels={
                        x_metric: x_metric.replace('_', ' ').title(),
                        y_metric: y_metric.replace('_', ' ').title()
                    },
                    color_discrete_sequence=['#007bff']  # Color corporativo uniforme
                )
                
                # Añadir líneas promedio si está activado
                if show_averages:
                    x_mean = filtered_scatter_df[x_metric].mean()
                    y_mean = filtered_scatter_df[y_metric].mean()
                    
                    # Obtener rangos del gráfico para los sombreados
                    x_min, x_max = filtered_scatter_df[x_metric].min(), filtered_scatter_df[x_metric].max()
                    y_min, y_max = filtered_scatter_df[y_metric].min(), filtered_scatter_df[y_metric].max()
                    
                    # Añadir sombreados de cuadrantes (fondo sutil)
                    # Cuadrante Elite (Alto-Alto) - Verde muy suave
                    fig_scatter.add_shape(
                        type="rect",
                        x0=x_mean, y0=y_mean,
                        x1=x_max, y1=y_max,
                        fillcolor="rgba(34, 197, 94, 0.08)",  # Verde muy transparente
                        line=dict(width=0),
                        layer="below"
                    )
                    
                    # Cuadrante Especialistas Y (Bajo-Alto) - Amarillo muy suave
                    fig_scatter.add_shape(
                        type="rect",
                        x0=x_min, y0=y_mean,
                        x1=x_mean, y1=y_max,
                        fillcolor="rgba(250, 204, 21, 0.08)",  # Amarillo muy transparente
                        line=dict(width=0),
                        layer="below"
                    )
                    
                    # Cuadrante Especialistas X (Alto-Bajo) - Naranja muy suave
                    fig_scatter.add_shape(
                        type="rect",
                        x0=x_mean, y0=y_min,
                        x1=x_max, y1=y_mean,
                        fillcolor="rgba(249, 115, 22, 0.08)",  # Naranja muy transparente
                        line=dict(width=0),
                        layer="below"
                    )
                    
                    # Cuadrante Mejora (Bajo-Bajo) - Rojo muy suave
                    fig_scatter.add_shape(
                        type="rect",
                        x0=x_min, y0=y_min,
                        x1=x_mean, y1=y_mean,
                        fillcolor="rgba(239, 68, 68, 0.08)",  # Rojo muy transparente
                        line=dict(width=0),
                        layer="below"
                    )
                    
                    # Línea vertical (promedio X)
                    fig_scatter.add_vline(
                        x=x_mean,
                        line_dash="dash",
                        line_color="rgba(239, 68, 68, 0.7)",  # Rojo semitransparente
                        line_width=2,
                        annotation_text=f"Promedio {x_metric.replace('_', ' ').title()}: {format_value(x_mean)}",
                        annotation_position="top",
                        annotation=dict(
                            bgcolor="rgba(255, 255, 255, 0.8)",
                            bordercolor="rgba(239, 68, 68, 0.7)",
                            font=dict(size=10)
                        )
                    )
                    
                    # Línea horizontal (promedio Y)
                    fig_scatter.add_hline(
                        y=y_mean,
                        line_dash="dash",
                        line_color="rgba(34, 197, 94, 0.7)",  # Verde semitransparente
                        line_width=2,
                        annotation_text=f"Promedio {y_metric.replace('_', ' ').title()}: {format_value(y_mean)}",
                        annotation_position="right",
                        annotation=dict(
                            bgcolor="rgba(255, 255, 255, 0.8)",
                            bordercolor="rgba(34, 197, 94, 0.7)",
                            font=dict(size=10)
                        )
                    )
                
                # Personalizar gráfico
                fig_scatter.update_layout(
                    height=600,
                    font=dict(size=12),
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    showlegend=False
                )
                
                fig_scatter.update_traces(
                    marker=dict(
                        line=dict(width=1, color='rgba(0,0,0,0.3)'),
                        opacity=0.8,
                        color='#007bff'  # Color corporativo
                    )
                )
                
                st.plotly_chart(fig_scatter, use_container_width=True)
                
                # Estadísticas de correlación
                if x_metric != y_metric:
                    correlation_coef = filtered_scatter_df[x_metric].corr(filtered_scatter_df[y_metric])
                    
                    # Interpretación de la correlación
                    if abs(correlation_coef) > 0.7:
                        interpretation = "Muy fuerte"
                        color = "🔴" if correlation_coef > 0 else "🔵"
                    elif abs(correlation_coef) > 0.5:
                        interpretation = "Fuerte"
                        color = "🟠" if correlation_coef > 0 else "🟡"
                    elif abs(correlation_coef) > 0.3:
                        interpretation = "Moderada"
                        color = "🟡" if correlation_coef > 0 else "🟢"
                    else:
                        interpretation = "Débil"
                        color = "⚪"
                    
                    direction = "positiva" if correlation_coef > 0 else "negativa"
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Correlación", f"{correlation_coef:.3f}")
                    with col2:
                        st.metric("📈 Interpretación", f"{color} {interpretation}")
                    with col3:
                        st.metric("🔄 Dirección", direction.capitalize())
                
                # Información adicional
                st.markdown("#### 📋 Resumen del Análisis")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("👥 Jugadores analizados", len(filtered_scatter_df))
                
                with col2:
                    if size_by:
                        size_range = filtered_scatter_df[size_by].agg(['min', 'max'])
                        st.metric(f"📏 Rango {size_by.replace('_', ' ').title()}", f"{format_value(size_range['min'])} - {format_value(size_range['max'])}")
                    else:
                        st.metric("📊 Correlación", f"{correlation_coef:.3f}")
                
                with col3:
                    # Jugador destacado (mejor en ambas métricas)
                    if len(filtered_scatter_df) > 0:
                        # Normalizar y sumar ambas métricas
                        x_norm = (filtered_scatter_df[x_metric] - filtered_scatter_df[x_metric].min()) / (filtered_scatter_df[x_metric].max() - filtered_scatter_df[x_metric].min())
                        y_norm = (filtered_scatter_df[y_metric] - filtered_scatter_df[y_metric].min()) / (filtered_scatter_df[y_metric].max() - filtered_scatter_df[y_metric].min())
                        combined_score = x_norm + y_norm
                        
                        best_idx = combined_score.idxmax()
                        best_player = filtered_scatter_df.loc[best_idx, player_col] if player_col else "N/A"
                        
                        st.metric("⭐ Jugador destacado", best_player)
                
                # Insights automáticos para scouts usando líneas promedio
                if show_averages:
                    st.markdown("#### 💡 Análisis por Cuadrantes (Líneas Promedio)")
                    
                    # Calcular promedios
                    x_mean = filtered_scatter_df[x_metric].mean()
                    y_mean = filtered_scatter_df[y_metric].mean()
                    
                    # Dividir en cuadrantes usando promedios
                    cuadrante_1 = filtered_scatter_df[
                        (filtered_scatter_df[x_metric] > x_mean) & 
                        (filtered_scatter_df[y_metric] > y_mean)
                    ]  # Alto-Alto (Superior Derecho)
                    
                    cuadrante_2 = filtered_scatter_df[
                        (filtered_scatter_df[x_metric] < x_mean) & 
                        (filtered_scatter_df[y_metric] > y_mean)
                    ]  # Bajo-Alto (Superior Izquierdo)
                    
                    cuadrante_3 = filtered_scatter_df[
                        (filtered_scatter_df[x_metric] < x_mean) & 
                        (filtered_scatter_df[y_metric] < y_mean)
                    ]  # Bajo-Bajo (Inferior Izquierdo)
                    
                    cuadrante_4 = filtered_scatter_df[
                        (filtered_scatter_df[x_metric] > x_mean) & 
                        (filtered_scatter_df[y_metric] < y_mean)
                    ]  # Alto-Bajo (Inferior Derecho)
                    
                    # Mostrar análisis por cuadrantes
                    quad_col1, quad_col2 = st.columns(2)
                    
                    with quad_col1:
                        st.markdown("**🟢 Cuadrante Elite (Alto-Alto):**")
                        if len(cuadrante_1) > 0:
                            st.success(f"✅ {len(cuadrante_1)} jugadores sobresalen en ambas métricas")
                            elite_players = cuadrante_1.nlargest(3, x_metric)[player_col].tolist() if player_col else []
                            for i, player in enumerate(elite_players[:3]):
                                st.write(f"🥇 {player}")
                        else:
                            st.write("No hay jugadores en este cuadrante")
                        
                        st.markdown("**🟡 Especialistas en Y (Bajo-Alto):**")
                        if len(cuadrante_2) > 0:
                            st.info(f"ℹ️ {len(cuadrante_2)} jugadores destacan más en {y_metric.replace('_', ' ').title()}")
                            spec_y_players = cuadrante_2.nlargest(2, y_metric)[player_col].tolist() if player_col else []
                            for player in spec_y_players[:2]:
                                st.write(f"📊 {player}")
                        else:
                            st.write("No hay jugadores en este cuadrante")
                    
                    with quad_col2:
                        st.markdown("**🟠 Especialistas en X (Alto-Bajo):**")
                        if len(cuadrante_4) > 0:
                            st.info(f"ℹ️ {len(cuadrante_4)} jugadores destacan más en {x_metric.replace('_', ' ').title()}")
                            spec_x_players = cuadrante_4.nlargest(2, x_metric)[player_col].tolist() if player_col else []
                            for player in spec_x_players[:2]:
                                st.write(f"📈 {player}")
                        else:
                            st.write("No hay jugadores en este cuadrante")
                        
                        st.markdown("**🔴 Área de Mejora (Bajo-Bajo):**")
                        if len(cuadrante_3) > 0:
                            st.warning(f"⚠️ {len(cuadrante_3)} jugadores por debajo del promedio en ambas")
                            improve_players = cuadrante_3.nsmallest(2, x_metric)[player_col].tolist() if player_col else []
                            for player in improve_players[:2]:
                                st.write(f"📉 {player}")
                        else:
                            st.write("No hay jugadores en este cuadrante")
                else:
                    st.markdown("#### 💡 Insights para Scouts")
                    
                    # Identificar jugadores en cuadrantes específicos usando mediana
                    x_median = filtered_scatter_df[x_metric].median()
                    y_median = filtered_scatter_df[y_metric].median()
                    
                    # Cuadrante superior derecho (altos en ambas métricas)
                    top_right = filtered_scatter_df[
                        (filtered_scatter_df[x_metric] > x_median) & 
                        (filtered_scatter_df[y_metric] > y_median)
                    ]
                    
                    # Cuadrante inferior izquierdo (bajos en ambas métricas)
                    bottom_left = filtered_scatter_df[
                        (filtered_scatter_df[x_metric] < x_median) & 
                        (filtered_scatter_df[y_metric] < y_median)
                    ]
                    
                    insights_col1, insights_col2 = st.columns(2)
                    
                    with insights_col1:
                        st.markdown("**🎯 Jugadores Elite (Alto-Alto):**")
                        if len(top_right) > 0:
                            elite_players = top_right.nlargest(3, x_metric)[player_col].tolist() if player_col else []
                            for i, player in enumerate(elite_players[:3]):
                                st.write(f"{i+1}. {player}")
                        else:
                            st.write("No hay jugadores en este cuadrante")
                    
                    with insights_col2:
                        st.markdown("**⚠️ Jugadores a Mejorar (Bajo-Bajo):**")
                        if len(bottom_left) > 0:
                            improve_players = bottom_left.nsmallest(3, x_metric)[player_col].tolist() if player_col else []
                            for i, player in enumerate(improve_players[:3]):
                                st.write(f"{i+1}. {player}")
                        else:
                            st.write("No hay jugadores en este cuadrante")
            
            else:
                st.warning("⚠️ No hay jugadores que cumplan los criterios de filtrado seleccionados")
    else:
        st.warning("⚠️ No hay suficientes métricas numéricas para crear análisis de dispersión")

elif "Equipo" in tipo_analisis:
    st.markdown("### 🏟️ Análisis de Rendimiento por Equipo")
    
    if team_col and team_col in df_filtered.columns:
        # Obtener métricas numéricas válidas
        numeric_cols = get_numeric_columns(df_filtered)
        relevant_metrics = [col for col in numeric_cols if any(keyword in col.lower() 
                          for keyword in ['gol', 'asist', 'pase', 'duel', 'xg', 'min'])]
        
        if relevant_metrics:
            selected_metric = st.selectbox(
                "📊 Métrica Principal:",
                relevant_metrics,
                help="Selecciona la métrica para análisis por equipos"
            )
            
            metric_type = st.radio(
                "📈 Tipo de Agregación:",
                ["Promedio", "Total", "Mediana"],
                horizontal=True
            )
            
            # Calcular estadísticas por equipo
            try:
                if metric_type == "Promedio":
                    team_stats = df_filtered.groupby(team_col)[selected_metric].mean()
                elif metric_type == "Total":
                    team_stats = df_filtered.groupby(team_col)[selected_metric].sum()
                else:
                    team_stats = df_filtered.groupby(team_col)[selected_metric].median()
                
                team_stats = team_stats.sort_values(ascending=False)
                
                # Gráfico principal
                fig = px.bar(
                    x=team_stats.values,
                    y=team_stats.index,
                    orientation='h',
                    title=f"{metric_type} de {selected_metric.replace('_', ' ').title()} por Equipo",
                    color=team_stats.values,
                    color_continuous_scale='viridis'
                )
                fig.update_layout(height=max(400, len(team_stats) * 25), showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Top 5 equipos
                st.markdown("#### 🏆 Top 5 Equipos")
                top5 = team_stats.head(5)
                
                for i, (team, value) in enumerate(top5.items()):
                    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]
                    formatted_value = format_value(value)
                    st.write(f"{medal} **{team}:** {formatted_value}")
                    
            except Exception as e:
                st.error(f"Error al calcular estadísticas por equipo: {str(e)}")
        else:
            st.warning("No hay métricas numéricas relevantes disponibles")

elif "Correlaciones" in tipo_analisis or "Mapa" in tipo_analisis:
    st.markdown("### 🔥 Mapa de Correlaciones por Categorías")
    st.markdown("Visualiza las relaciones entre métricas especializadas")
    
    # Selector de categoría
    correlation_category = st.selectbox(
        "📊 Categoría para Análisis:",
        list(SCOUTING_METRICS.keys()),
        help="Selecciona la categoría de métricas para análizar correlaciones"
    )
    
    category_metrics = SCOUTING_METRICS[correlation_category]['metrics']
    available_metrics = get_available_metrics(df_filtered, category_metrics)
    
    if len(available_metrics) >= 3:
        try:
            # Calcular matriz de correlación
            correlation_matrix = df_filtered[available_metrics].corr()
            
            # Crear nombres limpios para el mapa
            clean_names = []
            for metric in available_metrics:
                clean_name = metric.replace('_', ' ').replace('/', ' / ').replace(',_', '').title()
                # Limitar longitud del nombre
                if len(clean_name) > 20:
                    clean_name = clean_name[:17] + "..."
                clean_names.append(clean_name)
            
            # Crear matriz con nombres limpios
            correlation_display = correlation_matrix.copy()
            correlation_display.index = clean_names
            correlation_display.columns = clean_names
            
            # Mapa de calor mejorado
            fig_corr = px.imshow(
                correlation_display,
                title=f"🔥 Mapa de Correlaciones: {SCOUTING_METRICS[correlation_category]['icon']} {correlation_category}",
                color_continuous_scale='RdBu_r',
                zmin=-1, zmax=1,
                aspect="auto"
            )
            
            # Personalizar el mapa de calor
            fig_corr.update_layout(
                height=600,
                font=dict(size=11),
                title=dict(font=dict(size=16)),
                xaxis=dict(tickangle=45),
                yaxis=dict(tickangle=0)
            )
            
            # Añadir valores de correlación en las celdas
            fig_corr.update_traces(
                text=correlation_display.round(2),
                texttemplate="%{text}",
                textfont={"size": 10},
                hovertemplate="<b>%{x}</b><br><b>%{y}</b><br>Correlación: %{z:.3f}<extra></extra>"
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)
            
            # Insights de correlaciones más fuertes
            st.markdown("#### 🔍 Correlaciones Más Destacadas")
            
            # Obtener todas las correlaciones (excluyendo diagonal)
            correlations_flat = []
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_value = correlation_matrix.iloc[i, j]
                    if not pd.isna(corr_value):
                        correlations_flat.append({
                            'Métrica 1': clean_names[i],
                            'Métrica 2': clean_names[j],
                            'Correlación': corr_value
                        })
            
            if correlations_flat:
                correlations_df = pd.DataFrame(correlations_flat)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔴 Correlaciones Positivas Más Fuertes:**")
                    positive_corr = correlations_df[correlations_df['Correlación'] > 0].nlargest(5, 'Correlación')
                    for _, row in positive_corr.iterrows():
                        st.write(f"📈 **{row['Métrica 1']}** ↔ **{row['Métrica 2']}**: {row['Correlación']:.3f}")
                
                with col2:
                    st.markdown("**🔵 Correlaciones Negativas Más Fuertes:**")
                    negative_corr = correlations_df[correlations_df['Correlación'] < 0].nsmallest(5, 'Correlación')
                    for _, row in negative_corr.iterrows():
                        st.write(f"📉 **{row['Métrica 1']}** ↔ **{row['Métrica 2']}**: {row['Correlación']:.3f}")
            
            # Explicación para scouts
            st.markdown("#### 💡 Interpretación para Scouts")
            st.info("""
            **🔴 Correlación Positiva (0.5 a 1.0):** Las métricas aumentan juntas. Útil para identificar jugadores completos.
            
            **🔵 Correlación Negativa (-0.5 a -1.0):** Una métrica alta implica la otra baja. Puede indicar especializaciones.
            
            **⚪ Sin Correlación (-0.3 a 0.3):** Las métricas son independientes. Permite perfiles diversos.
            """)
            
        except Exception as e:
            st.error(f"Error al calcular correlaciones: {str(e)}")
    else:
        st.warning(f"⚠️ No hay suficientes métricas numéricas para análisis de correlaciones en {correlation_category}")
        if available_metrics:
            st.info(f"Métricas disponibles: {len(available_metrics)} - Se necesitan al menos 3")
            st.write("Métricas encontradas:", ", ".join(available_metrics))

else:  # Explorador de Jugadores
    st.markdown("### 🔍 Explorador Avanzado de Jugadores")
    
    # Pestañas para organizar
    tab1, tab2, tab3 = st.tabs(["📊 Vista General", "🔍 Búsqueda Detallada", "📈 Rankings"])
    
    with tab1:
        st.markdown("#### 📋 Vista General del Dataset Filtrado")
        
        # Información del dataset
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("👥 Jugadores", len(df_filtered))
            if team_col:
                st.metric("🏟️ Equipos", df_filtered[team_col].nunique())
        
        with col2:
            if position_col:
                st.metric("⚽ Posiciones", df_filtered[position_col].nunique())
            if age_col:
                st.metric("📊 Edad Promedio", f"{df_filtered[age_col].mean():.1f}")
        
        with col3:
            numeric_cols = get_numeric_columns(df_filtered)
            st.metric("🔢 Métricas Numéricas", len(numeric_cols))
            st.metric("📝 Métricas Texto", len(df_filtered.columns) - len(numeric_cols))
        
        # Muestra de datos
        st.markdown("#### 📋 Muestra de Datos")
        
        # Seleccionar columnas importantes para mostrar
        important_cols = [player_col, team_col, position_col, age_col]
        important_cols = [col for col in important_cols if col and col in df_filtered.columns]
        
        # Añadir algunas métricas numéricas relevantes
        numeric_cols = get_numeric_columns(df_filtered)
        relevant_numeric = [col for col in numeric_cols if any(keyword in col.lower() 
                          for keyword in ['gol', 'asist', 'min', 'partido'])][:4]
        
        display_cols = important_cols + relevant_numeric
        
        if display_cols:
            st.dataframe(df_filtered[display_cols].head(20), use_container_width=True)
    
    with tab2:
        st.markdown("#### 🔍 Búsqueda Detallada de Jugadores")
        
        # Búsqueda avanzada
        search_col1, search_col2 = st.columns(2)
        
        with search_col1:
            text_columns = [col for col in df_filtered.columns if df_filtered[col].dtype == 'object']
            search_columns = st.multiselect(
                "📋 Columnas donde buscar:",
                text_columns,
                default=[player_col] if player_col in text_columns else [],
                help="Selecciona columnas para la búsqueda"
            )
        
        with search_col2:
            search_term = st.text_input(
                "🔍 Término de búsqueda:",
                placeholder="Buscar...",
                help="Búsqueda insensible a mayúsculas"
            )
        
        if search_term and search_columns:
            # Realizar búsqueda
            search_results = pd.DataFrame()
            
            for col in search_columns:
                mask = df_filtered[col].astype(str).str.contains(search_term, case=False, na=False)
                matching_rows = df_filtered[mask]
                search_results = pd.concat([search_results, matching_rows]).drop_duplicates()
            
            if not search_results.empty:
                st.success(f"✅ {len(search_results)} resultados encontrados")
                st.dataframe(search_results, use_container_width=True, height=400)
            else:
                st.warning(f"⚠️ No se encontraron resultados para '{search_term}'")
    
    with tab3:
        st.markdown("#### 📈 Rankings por Métricas")
        
        # Selector de métrica para ranking
        numeric_cols = get_numeric_columns(df_filtered)
        
        if numeric_cols:
            ranking_metric = st.selectbox(
                "📊 Métrica para Ranking:",
                numeric_cols,
                help="Selecciona métrica para crear ranking"
            )
            
            ranking_order = st.radio(
                "📈 Orden:",
                ["Descendente (Mayor a Menor)", "Ascendente (Menor a Mayor)"],
                horizontal=True
            )
            
            ascending = ranking_order.startswith("Ascendente")
            
            # Crear ranking
            try:
                ranking_df = df_filtered.nlargest(20, ranking_metric) if not ascending else df_filtered.nsmallest(20, ranking_metric)
                
                if not ranking_df.empty:
                    # Mostrar top 10 como métricas
                    st.markdown(f"#### 🏆 Top 10 - {ranking_metric.replace('_', ' ').title()}")
                    
                    top_10 = ranking_df.head(10)
                    
                    for i, (_, player_row) in enumerate(top_10.iterrows()):
                        position_emoji = ["🥇", "🥈", "🥉"] + ["🏅"] * 7
                        player_name = player_row[player_col] if player_col else f"Jugador {i+1}"
                        metric_value = player_row[ranking_metric]
                        
                        formatted_value = format_value(metric_value)
                        st.write(f"{position_emoji[i]} **{player_name}:** {formatted_value}")
                    
                    # Tabla completa
                    st.markdown("#### 📋 Ranking Completo")
                    
                    display_cols = [player_col, team_col, position_col, ranking_metric]
                    display_cols = [col for col in display_cols if col and col in ranking_df.columns]
                    
                    if display_cols:
                        ranking_display = ranking_df[display_cols].reset_index(drop=True)
                        ranking_display.index += 1
                        
                        # Formatear la columna de métrica
                        ranking_display[ranking_metric] = ranking_display[ranking_metric].apply(format_value)
                        
                        st.dataframe(ranking_display, use_container_width=True)
            except Exception as e:
                st.error(f"Error al crear ranking: {str(e)}")
        else:
            st.warning("No hay métricas numéricas disponibles para crear rankings")

# Footer informativo
st.markdown("---")
st.markdown(f"""
<div style='background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 10px; text-align: center;'>
    <h4>📊 Visualizaciones Interactivas - Wyscout LaLiga</h4>
    <p><strong>Dataset: {len(df):,} jugadores | Filtrados: {len(df_filtered):,} | Análisis: {tipo_analisis}</strong></p>
    <p style='font-size: 0.9em; color: #666;'>Sistema de scouting profesional con {len(get_numeric_columns(df))} métricas numéricas especializadas</p>
</div>
""", unsafe_allow_html=True)