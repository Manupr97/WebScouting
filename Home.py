import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import numpy as np
import sys
import os
import json

# Configuración de la página - DEBE IR PRIMERO
st.set_page_config(
    page_title="Scouting Pro - Dashboard",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Añadir el directorio actual al path para imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Intentar imports con manejo de errores
try:
    from common.login import LoginManager
    from models.wyscout_model import WyscoutModel
    from models.partido_model import PartidoModel
except ImportError as e:
    st.error(f"Error al importar módulos: {e}")
    st.info("Verifica que todos los archivos estén en su lugar.")
    st.stop()

# CSS personalizado con paleta corporativa
st.markdown("""
<style>
    /* Variables de color corporativo */
    :root {
        --primary-dark: #24282a;
        --primary-blue: #007bff;
        --background-light: #f8f9fa;
        --text-light: #6c757d;
        --success-green: #28a745;
        --warning-orange: #ffc107;
        --danger-red: #dc3545;
    }
    
    /* Header personalizado */
    .dashboard-header {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-blue) 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
        box-shadow: 0 4px 20px rgba(0, 123, 255, 0.3);
    }
    
    .dashboard-header h1 {
        margin: 0;
        font-size: 2.8em;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .dashboard-header p {
        margin: 10px 0 0 0;
        font-size: 1.3em;
        opacity: 0.9;
    }
    
    /* Cards mejoradas */
    .metric-card {
        background: white;
        padding: 1.8rem;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(36, 40, 42, 0.1);
        border-left: 5px solid var(--primary-blue);
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: linear-gradient(45deg, transparent 30%, rgba(0, 123, 255, 0.1) 100%);
        border-radius: 50%;
        transform: translate(30px, -30px);
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 25px rgba(36, 40, 42, 0.15);
        border-left-color: var(--primary-dark);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: var(--primary-dark);
        margin: 0;
        position: relative;
        z-index: 1;
    }
    
    .metric-label {
        font-size: 1rem;
        color: var(--text-light);
        margin: 0;
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
        position: relative;
        z-index: 1;
    }
    
    .metric-delta {
        font-size: 0.9rem;
        color: var(--success-green);
        font-weight: 600;
        margin-top: 0.5rem;
        position: relative;
        z-index: 1;
    }
    
    /* Activity feed mejorado */
    .activity-item {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 4px solid var(--primary-blue);
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
    }
    
    .activity-item:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    
    .activity-time {
        color: var(--text-light);
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .activity-user {
        color: var(--primary-blue);
        font-weight: 600;
    }
    
    /* Top performer cards */
    .performer-card {
        background: white;
        padding: 1.2rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        transition: all 0.2s ease;
        border-left: 4px solid;
    }
    
    .performer-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .performer-card.goleador {
        border-left-color: var(--success-green);
    }
    
    .performer-card.asistente {
        border-left-color: var(--primary-blue);
    }
    
    .performer-card.valioso {
        border-left-color: var(--warning-orange);
    }
    
    /* Guía de usuario */
    .guide-section {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        margin: 2rem 0;
        border: 1px solid #dee2e6;
    }
    
    .guide-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        border-left: 4px solid var(--primary-blue);
        transition: all 0.2s ease;
    }
    
    .guide-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.12);
    }
    
    .guide-title {
        font-size: 1.1rem;
        font-weight: 700;
        color: var(--primary-dark);
        margin-bottom: 0.5rem;
    }
    
    .guide-description {
        color: var(--text-light);
        font-size: 0.95rem;
        line-height: 1.4;
    }
    
    /* Footer personalizado */
    .custom-footer {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-blue) 100%);
        color: white;
        padding: 2.5rem;
        border-radius: 15px;
        text-align: center;
        margin-top: 3rem;
        box-shadow: 0 4px 20px rgba(0, 123, 255, 0.3);
    }
    
    .brand-name {
        color: #ffffff;
        font-weight: 700;
        font-size: 1.3rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
    }
    
    /* Sidebar personalizada */
    .sidebar-user-card {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-blue) 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 123, 255, 0.3);
    }
    
    /* Ocultar elementos de Streamlit */
    .stDeployButton { display: none; }
    footer { display: none; }
    .stApp > header { background-color: transparent; }
    .block-container { padding-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# Función para formatear valores de manera inteligente
def format_value(value):
    """Formatear valores para mostrar de manera limpia"""
    if pd.isna(value):
        return "N/A"
    
    try:
        num_value = float(value)
        if abs(num_value) >= 1000000:
            return f"{num_value/1000000:.1f}M"
        elif abs(num_value) >= 1000:
            return f"{num_value/1000:.1f}K"
        elif num_value.is_integer() and abs(num_value) < 10000:
            return str(int(num_value))
        else:
            return f"{num_value:.1f}"
    except:
        return str(value)

# Función para obtener estadísticas del dataset
@st.cache_data
def get_wyscout_stats():
    """Obtener estadísticas principales del dataset de Wyscout"""
    try:
        wyscout_model = WyscoutModel()
        df = wyscout_model.get_all_players()
        
        if df.empty:
            return None, None
        
        # Detectar columnas principales
        detected_columns = {
            'player': 'jugador',
            'team': 'equipo_durante_el_período_seleccionado',
            'position': 'pos_principal',
            'age': 'edad'
        }
        
        # Calcular estadísticas
        stats = {
            'total_players': len(df),
            'total_teams': df[detected_columns['team']].nunique() if detected_columns['team'] in df.columns else 0,
            'total_positions': df[detected_columns['position']].nunique() if detected_columns['position'] in df.columns else 0,
            'avg_age': df[detected_columns['age']].mean() if detected_columns['age'] in df.columns else 0,
            'age_range': (df[detected_columns['age']].min(), df[detected_columns['age']].max()) if detected_columns['age'] in df.columns else (0, 0)
        }
        
        return df, stats
    except Exception as e:
        st.error(f"Error al cargar datos: {str(e)}")
        return None, None

# Función para generar actividad simulada realista
def generate_realistic_activity():
    """Generar actividad del sistema más realista"""
    scout_names = ["Ana García", "Carlos López", "María Ruiz", "José Martín", "Laura Sánchez", "Diego Torres"]
    
    actividades = [
        {
            "usuario": np.random.choice(scout_names),
            "accion": "analizó el rendimiento de K. Mbappé en detalle",
            "tiempo": "hace 1 hora",
            "tipo": "analisis",
            "icon": "🔍"
        },
        {
            "usuario": np.random.choice(scout_names),
            "accion": "comparó 3 porteros de LaLiga usando radar",
            "tiempo": "hace 2 horas",
            "tipo": "comparacion",
            "icon": "📊"
        },
        {
            "usuario": "Sistema",
            "accion": "actualizó datos de 574 jugadores de Wyscout",
            "tiempo": "hace 3 horas",
            "tipo": "sistema",
            "icon": "🔄"
        },
        {
            "usuario": np.random.choice(scout_names),
            "accion": "generó informe ejecutivo de J. Bellingham",
            "tiempo": "hace 4 horas",
            "tipo": "informe",
            "icon": "📋"
        },
        {
            "usuario": np.random.choice(scout_names),
            "accion": "identificó 5 talentos jóvenes en análisis dispersión",
            "tiempo": "hace 5 horas",
            "tipo": "descubrimiento",
            "icon": "⭐"
        },
        {
            "usuario": np.random.choice(scout_names),
            "accion": "exploró correlaciones en categoría Creatividad y Pases",
            "tiempo": "hace 6 horas",
            "tipo": "exploracion",
            "icon": "🔥"
        }
    ]
    
    return actividades

# Funciones auxiliares
def obtener_partidos_hoy():
    """Obtiene partidos de hoy"""
    try:
        partido_model = PartidoModel()
        fecha_hoy = date.today().strftime('%Y-%m-%d')
        partidos = partido_model.obtener_partidos_por_fecha(fecha_hoy)
        return partidos
    except:
        return []

def verificar_informes_jugador(nombre_jugador, equipo):
    """Verifica si un jugador tiene informes"""
    try:
        partido_model = PartidoModel()
        informes = partido_model.obtener_todos_informes()
        
        # Buscar informes del jugador
        informes_jugador = [
            inf for inf in informes 
            if inf.get('jugador_nombre', '').lower() == nombre_jugador.lower() 
            and inf.get('equipo', '').lower() == equipo.lower()
        ]
        
        return {
            'tiene_informes': len(informes_jugador) > 0,
            'cantidad': len(informes_jugador)
        }
    except:
        return {'tiene_informes': False, 'cantidad': 0}

def cargar_lista_visualizacion():
    """Carga lista de visualización desde archivo JSON"""
    try:
        filepath = os.path.join('data', 'lista_visualizacion.json')
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"jugadores_seguimiento": []}
    except:
        return {"jugadores_seguimiento": []}

# === MAIN APP ===
def main():
    # Inicializar modelos
    try:
        login_manager = LoginManager()
        partido_model = PartidoModel()
    except Exception as e:
        st.error(f"Error al inicializar: {str(e)}")
        st.stop()

    # Verificar autenticación
    if not login_manager.is_authenticated():
        login_manager.mostrar_login()
    else:
        # Usuario autenticado
        current_user = login_manager.get_current_user()
        
        # Cargar datos de Wyscout
        df_wyscout, wyscout_stats = get_wyscout_stats()
        
        if df_wyscout is None or df_wyscout.empty:
            st.error("❌ Error al cargar datos de Wyscout")
            st.info("Verifica que el archivo `wyscout_LaLiga_limpio.xlsx` esté en la carpeta `data/`")
            st.stop()
        
        # === SIDEBAR ===
        with st.sidebar:
            st.markdown(f"""
            <div class='sidebar-user-card'>
                <h3 style='margin: 0;'>👤 {current_user['nombre']}</h3>
                <p style='margin: 5px 0 0 0; opacity: 0.9; font-size: 0.9rem;'>
                    {current_user['rol'].title()}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("### 🧭 Navegación")
            
            if st.button("🔍 **Buscar Jugadores**", use_container_width=True):
                st.switch_page("1_🔍_Jugadores")
            
            if st.button("📊 **Visualizaciones**", use_container_width=True):
                st.switch_page("3_📊_Visualizaciones")
            
            if st.button("📋 **Base de Datos**", use_container_width=True):
                st.switch_page("2_📊_Bases_Datos_Unificadas")
            
            st.markdown("---")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True, type="secondary"):
                login_manager.logout()

            # Monitor de rendimiento solo para admin
            if current_user.get('rol') == 'admin':
                try:
                    from utils.monitor_performance import mostrar_metricas_rendimiento
                    mostrar_metricas_rendimiento()
                except:
                    pass
        
        # === HEADER PRINCIPAL ===
        st.markdown(f"""
        <div class='dashboard-header'>
            <h1>⚽ Dashboard Ejecutivo de Scouting</h1>
            <p>Bienvenido/a, <strong>{current_user['nombre']}</strong> - Centro de Control Profesional Wyscout</p>
        </div>
        """, unsafe_allow_html=True)
        
        # === MÉTRICAS PRINCIPALES ===
        st.markdown("### 📊 Métricas Principales del Sistema")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-label'>👥 Base de Datos</p>
                <p class='metric-value'>{wyscout_stats['total_players']:,}</p>
                <p class='metric-delta'>Jugadores LaLiga</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-label'>🏟️ Cobertura</p>
                <p class='metric-value'>{wyscout_stats['total_teams']}</p>
                <p class='metric-delta'>Equipos monitoreados</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            # Obtener columnas numéricas disponibles
            numeric_cols = df_wyscout.select_dtypes(include=[np.number]).columns
            metrics_count = len([col for col in numeric_cols if not col.lower().endswith('_id')])
            
            st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-label'>📈 Métricas</p>
                <p class='metric-value'>{metrics_count}</p>
                <p class='metric-delta'>Estadísticas especializadas</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class='metric-card'>
                <p class='metric-label'>🎂 Edad Promedio</p>
                <p class='metric-value'>{wyscout_stats['avg_age']:.1f}</p>
                <p class='metric-delta'>años ({wyscout_stats['age_range'][0]:.0f}-{wyscout_stats['age_range'][1]:.0f})</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # === SECCIÓN PRINCIPAL: ACTIVIDAD Y ANÁLISIS ===
        col_left, col_right = st.columns([1.2, 0.8])
        
        with col_left:
            st.markdown("### 🔥 Actividad Reciente del Sistema")
            
            # Generar actividad realista
            actividades = generate_realistic_activity()
            
            for actividad in actividades:
                st.markdown(f"""
                <div class='activity-item'>
                    <div>{actividad['icon']} <span class='activity-user'>{actividad['usuario']}</span> {actividad['accion']}</div>
                    <div class='activity-time'>{actividad['tiempo']}</div>
                </div>
                """, unsafe_allow_html=True)
            
            # Insights del sistema
            st.markdown("### 💡 Insights del Sistema")
            
            insights_col1, insights_col2 = st.columns(2)
            
            with insights_col1:
                st.info(f"""
                **📊 Estado del Dataset:**
                - **{wyscout_stats['total_players']} jugadores** en total
                - **{wyscout_stats['total_teams']} equipos** de LaLiga
                - **{wyscout_stats['total_positions']} posiciones** diferentes
                - Cobertura **100% profesional**
                """)
            
            with insights_col2:
                # Calcular distribución de edades
                if 'edad' in df_wyscout.columns:
                    jovenes = len(df_wyscout[df_wyscout['edad'] <= 23])
                    senior = len(df_wyscout[df_wyscout['edad'] >= 30])
                    porcentaje_jovenes = (jovenes / len(df_wyscout)) * 100
                    
                    st.success(f"""
                    **🎯 Análisis Demográfico:**
                    - **{porcentaje_jovenes:.1f}% jugadores jóvenes** (≤23 años)
                    - **{senior} jugadores senior** (≥30 años)
                    - **Edad media: {wyscout_stats['avg_age']:.1f} años**
                    - Rango perfecto para scouting
                    """)
        
        with col_right:
            st.markdown("### 📊 Distribución por Equipos")
            
            # Gráfico de equipos con más jugadores
            if 'equipo_durante_el_período_seleccionado' in df_wyscout.columns:
                team_counts = df_wyscout['equipo_durante_el_período_seleccionado'].value_counts().head(8)
                
                fig_teams = px.bar(
                    x=team_counts.values,
                    y=team_counts.index,
                    orientation='h',
                    title="Top 8 Equipos por Número de Jugadores",
                    color=team_counts.values,
                    color_continuous_scale=['#007bff', '#24282a']
                )
                fig_teams.update_layout(
                    height=350,
                    showlegend=False,
                    font=dict(size=11),
                    title_font_size=14
                )
                st.plotly_chart(fig_teams, use_container_width=True)
            
            # Distribución de posiciones
            if 'pos_principal' in df_wyscout.columns:
                st.markdown("#### ⚽ Por Posiciones")
                pos_counts = df_wyscout['pos_principal'].value_counts().head(6)
                
                for pos, count in pos_counts.items():
                    percentage = (count / len(df_wyscout)) * 100
                    st.write(f"**{pos}:** {count} jugadores ({percentage:.1f}%)")
        
        st.markdown("---")
        
        # === TOP PERFORMERS ===
        st.markdown("### 🏆 Top Performers - Jugadores Relevantes")
        st.caption("*Filtrado por jugadores con +1700 minutos (mínimo para ser considerado titular)*")
        
        col_perf1, col_perf2, col_perf3 = st.columns(3)
        
        # APLICAR FILTRO DE MINUTOS MÍNIMOS
        min_minutes = 1700
        
        # Buscar columna de minutos
        minutes_cols = [col for col in df_wyscout.columns if 'min' in col.lower() and not 'admin' in col.lower()]
        df_filtered_minutes = df_wyscout.copy()
        
        if minutes_cols:
            minutes_col = minutes_cols[0]
            try:
                minutes_data = pd.to_numeric(df_wyscout[minutes_col], errors='coerce')
                df_filtered_minutes = df_wyscout[minutes_data >= min_minutes]
            except:
                df_filtered_minutes = df_wyscout.copy()
        
        # Obtener top performers
        numeric_cols = df_filtered_minutes.select_dtypes(include=[np.number]).columns
        
        with col_perf1:
            st.markdown("#### ⚽ Rendimiento Ofensivo")
            
            # Top goleador
            if 'goles' in df_filtered_minutes.columns:
                try:
                    goles_data = pd.to_numeric(df_filtered_minutes['goles'], errors='coerce')
                    if goles_data.max() > 0:
                        top_goleador_idx = goles_data.idxmax()
                        top_goleador = df_filtered_minutes.loc[top_goleador_idx]
                        
                        st.markdown(f"""
                        <div class='performer-card goleador'>
                            <strong>🥇 Máximo Goleador</strong><br>
                            <strong>{top_goleador.get('jugador', 'N/A')}</strong><br>
                            {format_value(goles_data[top_goleador_idx])} goles<br>
                            <small style='color: #6c757d;'>{top_goleador.get('equipo_durante_el_período_seleccionado', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                except:
                    st.info("Datos de goles no disponibles")
            
            # Top asistente
            if 'asistencias' in df_filtered_minutes.columns:
                try:
                    asist_data = pd.to_numeric(df_filtered_minutes['asistencias'], errors='coerce')
                    if asist_data.max() > 0:
                        top_asistente_idx = asist_data.idxmax()
                        top_asistente = df_filtered_minutes.loc[top_asistente_idx]
                        
                        st.markdown(f"""
                        <div class='performer-card asistente'>
                            <strong>🎯 Máximo Asistente</strong><br>
                            <strong>{top_asistente.get('jugador', 'N/A')}</strong><br>
                            {format_value(asist_data[top_asistente_idx])} asistencias<br>
                            <small style='color: #6c757d;'>{top_asistente.get('equipo_durante_el_período_seleccionado', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                except:
                    st.info("Datos de asistencias no disponibles")
        
        with col_perf2:
            st.markdown("#### 🛡️ Rendimiento Defensivo")
            
            # Top en interceptaciones
            intercept_cols = [col for col in numeric_cols if 'intercep' in col.lower()]
            if intercept_cols:
                try:
                    intercept_col = intercept_cols[0]
                    intercept_data = pd.to_numeric(df_filtered_minutes[intercept_col], errors='coerce')
                    if intercept_data.max() > 0:
                        top_intercept_idx = intercept_data.idxmax()
                        top_intercept = df_filtered_minutes.loc[top_intercept_idx]
                        
                        st.markdown(f"""
                        <div class='performer-card goleador'>
                            <strong>🔍 Líder en Interceptaciones</strong><br>
                            <strong>{top_intercept.get('jugador', 'N/A')}</strong><br>
                            {format_value(intercept_data[top_intercept_idx])}<br>
                            <small style='color: #6c757d;'>{top_intercept.get('equipo_durante_el_período_seleccionado', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                except:
                    st.info("Datos defensivos no disponibles")
            
            # Entrada/duelos defensivos
            entry_cols = [col for col in numeric_cols if 'entrada' in col.lower() or ('duel' in col.lower() and 'def' in col.lower())]
            if entry_cols:
                try:
                    entry_col = entry_cols[0]
                    entry_data = pd.to_numeric(df_filtered_minutes[entry_col], errors='coerce')
                    if entry_data.max() > 0:
                        top_entry_idx = entry_data.idxmax()
                        top_entry = df_filtered_minutes.loc[top_entry_idx]
                        
                        st.markdown(f"""
                        <div class='performer-card asistente'>
                            <strong>⚔️ Líder Defensivo</strong><br>
                            <strong>{top_entry.get('jugador', 'N/A')}</strong><br>
                            {format_value(entry_data[top_entry_idx])}<br>
                            <small style='color: #6c757d;'>{top_entry.get('equipo_durante_el_período_seleccionado', 'N/A')}</small>
                        </div>
                        """, unsafe_allow_html=True)
                except:
                    pass
        
        with col_perf3:
            st.markdown("#### 🥅 Rendimiento Porteros")
            
            # Filtrar porteros
            if 'pos_principal' in df_filtered_minutes.columns:
                try:
                    porteros_df = df_filtered_minutes[df_filtered_minutes['pos_principal'].str.contains('Portero', case=False, na=False)]
                    
                    if not porteros_df.empty:
                        # Top portero por paradas
                        paradas_cols = [col for col in numeric_cols if 'parada' in col.lower() or 'save' in col.lower()]
                        if paradas_cols:
                            paradas_col = paradas_cols[0]
                            if paradas_col in porteros_df.columns:
                                paradas_data = pd.to_numeric(porteros_df[paradas_col], errors='coerce')
                                if paradas_data.max() > 0:
                                    top_portero_idx = paradas_data.idxmax()
                                    top_portero = porteros_df.loc[top_portero_idx]
                                    
                                    st.markdown(f"""
                                    <div class='performer-card goleador'>
                                        <strong>🥅 Líder en Paradas</strong><br>
                                        <strong>{top_portero.get('jugador', 'N/A')}</strong><br>
                                        {format_value(paradas_data[top_portero_idx])}%<br>
                                        <small style='color: #6c757d;'>{top_portero.get('equipo_durante_el_período_seleccionado', 'N/A')}</small>
                                    </div>
                                    """, unsafe_allow_html=True)
                        
                        # Número total de porteros
                        st.markdown(f"""
                        <div class='performer-card valioso'>
                            <strong>🏟️ Porteros Titulares</strong><br>
                            <strong>{len(porteros_df)} porteros</strong><br>
                            Con +{min_minutes} min<br>
                            <small style='color: #6c757d;'>Rendimiento relevante</small>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info("No se encontraron porteros con minutos suficientes")
                except:
                    st.info("Datos de porteros no disponibles")
        
        st.markdown("---")
        
        # === GRÁFICOS EJECUTIVOS ===
        st.markdown("### 📈 Análisis Ejecutivo")
        
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            # Distribución de edades
            if 'edad' in df_wyscout.columns:
                st.markdown("#### 🎂 Distribución de Edades")
                
                fig_age = px.histogram(
                    df_wyscout,
                    x='edad',
                    nbins=15,
                    title="Distribución de Edades en LaLiga",
                    color_discrete_sequence=['#007bff']
                )
                fig_age.update_layout(
                    height=300,
                    showlegend=False,
                    font=dict(size=11)
                )
                st.plotly_chart(fig_age, use_container_width=True)
        
        with chart_col2:
            # Top equipos por valor promedio
            if 'equipo_durante_el_período_seleccionado' in df_wyscout.columns:
                # Buscar columna de valor
                valor_cols = [col for col in numeric_cols if 'valor' in col.lower() or 'value' in col.lower()]
                if valor_cols:
                    valor_col = valor_cols[0]
                    
                    st.markdown("#### 💰 Top Equipos por Valor Promedio")
                    
                    team_values = df_wyscout.groupby('equipo_durante_el_período_seleccionado')[valor_col].mean().sort_values(ascending=False).head(8)
                    
                    fig_values = px.bar(
                        x=team_values.values,
                        y=team_values.index,
                        orientation='h',
                        title="Valor Promedio por Equipo",
                        color=team_values.values,
                        color_continuous_scale=['#24282a', '#007bff']
                    )
                    fig_values.update_layout(
                        height=300,
                        showlegend=False,
                        font=dict(size=10)
                    )
                    st.plotly_chart(fig_values, use_container_width=True)
        
        # === GUÍA DE USUARIO DINÁMICA ===
        st.markdown("""
        <div class='guide-section'>
            <h3 style='text-align: center; color: #24282a; margin-bottom: 1.5rem;'>
                🎯 ¿Qué puedes hacer ahora?
            </h3>
        </div>
        """, unsafe_allow_html=True)

        # Determinar el estado del usuario
        def obtener_estado_usuario_dinamico():
            """Analiza el estado actual del usuario para sugerir acciones"""
            try:
                informes_usuario = partido_model.obtener_informes_por_usuario(current_user['usuario'])
                lista_visualizacion = cargar_lista_visualizacion()
                
                estado = {
                    'es_nuevo': len(informes_usuario) == 0,
                    'tiene_informes': len(informes_usuario) > 0,
                    'cantidad_informes': len(informes_usuario),
                    'tiene_lista_visualizacion': len(lista_visualizacion.get('jugadores_seguimiento', [])) > 0,
                    'jugadores_pendientes': len([j for j in lista_visualizacion.get('jugadores_seguimiento', []) 
                                            if not verificar_informes_jugador(j['jugador'], j['equipo'])['tiene_informes']]),
                    'partidos_hoy': len(obtener_partidos_hoy()),
                }
                return estado
            except:
                return {'es_nuevo': True, 'tiene_informes': False, 'cantidad_informes': 0}

        # Obtener estado dinámico
        estado_usuario = obtener_estado_usuario_dinamico()

        # Crear recomendaciones personalizadas
        if estado_usuario['es_nuevo']:
            # Usuario nuevo - Guía de primeros pasos
            st.markdown("""
            <div class='guide-card' style='border-left: 4px solid #28a745;'>
                <div class='guide-title'>🌟 ¡Bienvenido al Scouting Profesional!</div>
                <div class='guide-description'>
                    Parece que es tu primera vez. Te recomendamos comenzar con estos pasos:
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_nuevo1, col_nuevo2 = st.columns(2)
            
            with col_nuevo1:
                if st.button("🎯 1. Base de Datos", use_container_width=True, type="primary"):
                    st.switch_page("📊 Bases Datos Unificadas")
                st.caption("Descubre los 574 jugadores de LaLiga disponibles")
            
            with col_nuevo2:
                if st.button("💎 2. Discovery Hub", use_container_width=True, type="primary"):
                    st.switch_page("1_🔍_Jugadores")
                st.caption("Encuentra talentos Sub-23 sin observar")

        elif estado_usuario['jugadores_pendientes'] > 0:
            # Usuario con jugadores pendientes
            st.markdown(f"""
            <div class='guide-card' style='border-left: 4px solid #ffc107;'>
                <div class='guide-title'>⏳ Tienes {estado_usuario['jugadores_pendientes']} jugadores pendientes</div>
                <div class='guide-description'>
                    Hay jugadores en tu lista de visualización esperando evaluación. ¡Es hora de observarlos!
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_pend1, col_pend2 = st.columns(2)
            
            with col_pend1:
                if st.button("👀 Ver Lista de Visualización", use_container_width=True, type="primary"):
                    st.switch_page("6_👀_Lista_Visualizacion")
                st.caption("Gestiona tus jugadores objetivo")
            
            with col_pend2:
                if st.button("⚽ Partidos en Vivo", use_container_width=True, type="primary"):
                    st.switch_page("4_⚽_Centro_de_Scouting")
                st.caption("Observa jugadores en acción")

        elif estado_usuario['partidos_hoy'] > 0:
            # Hay partidos hoy
            st.markdown(f"""
            <div class='guide-card' style='border-left: 4px solid #dc3545;'>
                <div class='guide-title'>🔴 {estado_usuario['partidos_hoy']} partidos en vivo HOY</div>
                <div class='guide-description'>
                    ¡Perfecto momento para hacer scouting en tiempo real!
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🎯 Ir a Scouting en Vivo", use_container_width=True, type="primary"):
                st.switch_page("4_⚽_Centro de Scouting")

        else:
            # Usuario experimentado
            st.markdown("""
            <div class='guide-card' style='border-left: 4px solid #17a2b8;'>
                <div class='guide-title'>🏆 Continúa tu trabajo de scouting</div>
                <div class='guide-description'>
                    Ya tienes experiencia. Aquí tienes las herramientas más útiles:
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_exp1, col_exp2, col_exp3 = st.columns(3)
            
            with col_exp1:
                if st.button("📊 Análisis Avanzado", use_container_width=True):
                    st.switch_page("3_📊_Visualizaciones")
                st.caption("Radar, dispersión, correlaciones")
            
            with col_exp2:
                if st.button("📋 Mis Informes", use_container_width=True):
                    st.switch_page("5_📋_Mis_Informes")
                st.caption(f"Gestiona tus {estado_usuario['cantidad_informes']} informes")
            
            with col_exp3:
                if st.button("🔍 Búsqueda Avanzada", use_container_width=True):
                    st.switch_page("2_📊_Bases_Datos_Unificadas")
                st.caption("Filtros y análisis detallado")

        # Accesos rápidos
        st.markdown("---")
        st.markdown("#### ⚡ Accesos Rápidos")

        quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

        with quick_col1:
            if st.button("🔍 Explorar", use_container_width=True):
                st.switch_page("1_🔍_Jugadores")

        with quick_col2:
            if st.button("📊 Visualizar", use_container_width=True):
                st.switch_page("3_📊_Visualizaciones")

        with quick_col3:
            if st.button("⚽ Observar", use_container_width=True):
                st.switch_page("4_⚽_Centro_de_Scouting")

        with quick_col4:
            if st.button("📋 Informes", use_container_width=True):
                st.switch_page("5_📋_Mis_Informes")
        
        # === FOOTER ===
        st.markdown(f"""
        <div class='custom-footer'>
            <h3>⚽ Sistema de Scouting Profesional</h3>
            <p style='font-size: 1.1rem; margin: 1rem 0;'>
                Potenciado por datos reales de <strong>Wyscout LaLiga</strong><br>
                {wyscout_stats['total_players']} jugadores | {wyscout_stats['total_teams']} equipos | {metrics_count} métricas especializadas
            </p>
            <div style='margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid rgba(255,255,255,0.3);'>
                <div class='brand-name'>Sistema desarrollado por Manuel Pérez Ruda</div>
                <p style='font-size: 0.9rem; opacity: 0.9; margin-top: 0.5rem;'>
                    Scouting Pro v2.0 - Dashboard Ejecutivo | {datetime.now().year}
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Ejecutar la aplicación
if __name__ == "__main__":
    main()