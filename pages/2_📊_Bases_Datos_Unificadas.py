import streamlit as st
import pandas as pd
import sys
import os
import json
from datetime import datetime


# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

# Imports del sistema
from common.login import LoginManager
from models.wyscout_model import WyscoutModel
from models.jugador_model import JugadorModel

# Configuración de la página
st.set_page_config(
    page_title="Bases de Datos - Scouting Pro",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS simplificado y limpio
st.markdown("""
<style>
    /* Ocultar elementos que causan ruido */
    .stDeployButton { display: none !important; }
    footer { display: none !important; }
    .stApp > header { background-color: transparent; }
    .block-container { padding-top: 1rem; }
    
    /* Header limpio */
    .clean-header {
        background: linear-gradient(135deg, #1f2937 0%, #3b82f6 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .clean-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .clean-header p {
        margin: 8px 0 0 0;
        opacity: 0.9;
    }
    
    /* Métricas simples */
    .simple-metric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .simple-metric h3 {
        margin: 0;
        color: #1f2937;
        font-size: 1.5rem;
    }
    
    .simple-metric p {
        margin: 4px 0 0 0;
        color: #6b7280;
        font-size: 0.875rem;
    }
    
    /* Configuración limpia */
    .config-section {
        background: #f9fafb;
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    }
    
    /* Paginación abajo */
    .bottom-pagination {
        margin-top: 1rem;
        padding: 1rem;
        background: #f9fafb;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# Verificar autenticación
login_manager = LoginManager()
if not login_manager.is_authenticated():
    st.error("🔒 Acceso denegado")
    st.stop()

current_user = login_manager.get_current_user()

# ================================
# FUNCIONES OPTIMIZADAS (SIN CACHE AGRESIVO)
# ================================

def detectar_columnas_por_acciones(df):
    """Detecta y clasifica columnas por zonas del campo y tipos de acciones"""
    if df.empty:
        return {'todas': [], 'basicas': [], 'defensivas': [], 'ofensivas': [], 'creacion': [], 'porteros': [], 'fisicas': [], 'otras': []}
    
    todas = list(df.columns)
    basicas = [col for col in ['jugador', 'equipo_durante_el_período_seleccionado', 'pos_principal', 'edad'] if col in todas]
    
    # Clasificación por acciones/zonas
    defensivas = []
    ofensivas = []
    creacion = []
    porteros = []
    fisicas = []
    otras = []
    
    for col in todas:
        if col not in basicas:
            col_lower = col.lower()
            
            # MÉTRICAS DEFENSIVAS
            if any(palabra in col_lower for palabra in [
                'entradas', 'intercep', 'despeje', 'bloqueo', 'falta', 'tarjeta',
                'duelos_defensivos', 'duelos_ganados', 'duelos_aéreos', 'recuper',
                'defensive', 'tackle', 'interception', 'clearance'
            ]):
                defensivas.append(col)
            
            # MÉTRICAS OFENSIVAS
            elif any(palabra in col_lower for palabra in [
                'goles', 'remates', 'tiros', 'disparos', 'ocasiones', 'finishing',
                'shots', 'goals', 'xg', 'expected_goals', 'penaltis'
            ]):
                ofensivas.append(col)
            
            # MÉTRICAS DE CREACIÓN/PASES
            elif any(palabra in col_lower for palabra in [
                'asistencias', 'pases', 'centros', 'córners', 'jugadas_claves', 'xa',
                'passes', 'assists', 'key_passes', 'through_balls', 'cross',
                'precisión_pases', 'pases_largos', 'pases_progre', 'pases_hacia'
            ]):
                creacion.append(col)
            
            # MÉTRICAS DE PORTEROS
            elif any(palabra in col_lower for palabra in [
                'paradas', 'goles_recibidos', 'goles_evitados', 'salidas',
                'saves', 'goals_conceded', 'clean_sheets', 'goalkeeper',
                'portería', 'arco', 'valla'
            ]):
                porteros.append(col)
            
            # MÉTRICAS FÍSICAS
            elif any(palabra in col_lower for palabra in [
                'velocidad', 'distancia', 'carreras', 'aceleración', 'regates',
                'km', 'sprint', 'dribbles', 'speed', 'distance', 'runs',
                'physical', 'stamina', 'min', 'minutos', 'partidos_jugados'
            ]):
                fisicas.append(col)
            
            # OTRAS MÉTRICAS
            else:
                otras.append(col)
    
    return {
        'todas': todas,
        'basicas': basicas,
        'defensivas': sorted(defensivas),
        'ofensivas': sorted(ofensivas),
        'creacion': sorted(creacion),
        'porteros': sorted(porteros),
        'fisicas': sorted(fisicas),
        'otras': sorted(otras)
    }

def limpiar_columnas_duplicadas(columnas):
    """Elimina duplicados manteniendo orden"""
    vistas = set()
    resultado = []
    for col in columnas:
        if col not in vistas:
            vistas.add(col)
            resultado.append(col)
    return resultado

@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_datos_wyscout_simple():
    """Carga datos directamente del Excel"""
    try:
        # En lugar de: wyscout_model.get_all_players()
        df = pd.read_excel('data\wyscout_LaLiga_limpio.xlsx')
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {str(e)}")
        return pd.DataFrame()

def cargar_datos_personales_reales():
    """
    Carga los jugadores directamente de jugadores_observados con TODAS las nuevas columnas
    """
    try:
        import sqlite3
        conn = sqlite3.connect('data/jugadores.db')
        
        # Query que NO filtra por total_informes para asegurar que veamos TODOS los jugadores
        query = """
        SELECT 
            id,
            COALESCE(jugador, nombre_completo) as nombre_completo,
            equipo,
            posicion,
            numero_camiseta,
            CASE 
                WHEN edad IS NULL OR edad = 0 THEN NULL
                ELSE edad 
            END as edad,
            nacionalidad,
            liga,
            imagen_url,
            escudo_equipo,
            veces_observado,
            COALESCE(estado, 'Evaluado') as estado_observacion,
            COALESCE(nota_general, 0) as nota_general,
            COALESCE(nota_promedio, nota_general, 0) as nota_promedio,
            COALESCE(mejor_nota, nota_general, 0) as mejor_nota,
            COALESCE(peor_nota, nota_general, 0) as peor_nota,
            COALESCE(total_informes, 1) as total_informes,
            ultima_fecha_visto,
            scout_agregado,
            -- Agregar campo de recomendación basado en nota_promedio o nota_general
            CASE 
                WHEN COALESCE(nota_promedio, nota_general, 0) >= 7 THEN 'Fichar'
                WHEN COALESCE(nota_promedio, nota_general, 0) >= 5 THEN 'Seguir observando'
                WHEN COALESCE(nota_promedio, nota_general, 0) > 0 THEN 'Descartar'
                ELSE 'Sin evaluar'
            END as recomendacion_calculada
        FROM jugadores_observados
        WHERE 1=1  -- Sin filtros, mostrar TODOS
        ORDER BY 
            COALESCE(nota_promedio, nota_general, 0) DESC,
            COALESCE(total_informes, 0) DESC,
            id DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        # IMPORTANTE: Para jugadores sin nota_promedio, usar nota_general
        if not df.empty:
            # Asegurar que las notas no sean None/NaN
            df['nota_promedio'] = df.apply(
                lambda row: row['nota_general'] if pd.isna(row['nota_promedio']) or row['nota_promedio'] == 0 
                else row['nota_promedio'], 
                axis=1
            )
            
            df['mejor_nota'] = df.apply(
                lambda row: row['nota_general'] if pd.isna(row['mejor_nota']) or row['mejor_nota'] == 0 
                else row['mejor_nota'], 
                axis=1
            )
            
            df['peor_nota'] = df.apply(
                lambda row: row['nota_general'] if pd.isna(row['peor_nota']) or row['peor_nota'] == 0 
                else row['peor_nota'], 
                axis=1
            )
        
        conn.close()
        
        # Log para debug
        print(f"✅ Cargados {len(df)} jugadores de la base personal")
        if len(df) > 0:
            print(f"   Columnas disponibles: {', '.join(df.columns)}")
            print(f"\n   Primeros jugadores:")
            for idx, row in df.head(5).iterrows():
                print(f"   - {row['nombre_completo']} ({row['equipo']}) - Nota: {row['nota_promedio']:.1f}, Informes: {row['total_informes']}")
        
        return df
        
    except Exception as e:
        st.warning(f"Error cargando datos personales: {str(e)}")
        import traceback
        traceback.print_exc()
        return pd.DataFrame()

def cargar_lista_objetivos():
    """Carga lista de objetivos"""
    try:
        with open('data/lista_visualizacion.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("jugadores_seguimiento", [])
    except:
        return []

# ================================
# HEADER LIMPIO
# ================================

st.markdown(f"""
<div class="clean-header">
    <h1>📊 Bases de Datos</h1>
    <p>Sistema de Scouting Profesional • {current_user['nombre']} ({current_user['rol']})</p>
</div>
""", unsafe_allow_html=True)

# ================================
# CARGA DE DATOS (OPTIMIZADA)
# ================================

# Mostrar spinner solo durante carga inicial
with st.spinner("Cargando datos..."):
    df_wyscout = cargar_datos_wyscout_simple()
    df_personal = cargar_datos_personales_reales()
    lista_objetivos = cargar_lista_objetivos()

# ================================
# MÉTRICAS SIMPLES
# ================================

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_wyscout = len(df_wyscout) if not df_wyscout.empty else 0
    st.markdown(f"""
    <div class="simple-metric">
        <h3>{total_wyscout:,}</h3>
        <p>Wyscout LaLiga</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    total_personal = len(df_personal) if not df_personal.empty else 0
    st.markdown(f"""
    <div class="simple-metric">
        <h3>{total_personal}</h3>
        <p>Base Personal</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    total_objetivos = len(lista_objetivos)
    st.markdown(f"""
    <div class="simple-metric">
        <h3>{total_objetivos}</h3>
        <p>Lista Objetivos</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    total_combinado = total_wyscout + total_personal + total_objetivos
    st.markdown(f"""
    <div class="simple-metric">
        <h3>{total_combinado:,}</h3>
        <p>Total Registros</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ================================
# PESTAÑAS PRINCIPALES
# ================================

tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 Wyscout LaLiga", 
    "👤 Base Personal", 
    "👀 Lista Objetivos",
    "🔍 Búsqueda Global"
])

# ==================== PESTAÑA 1: WYSCOUT ====================
with tab1:
    st.markdown("### 🌐 Base Wyscout LaLiga")
    
    if not df_wyscout.empty:
        # Detectar columnas disponibles por acciones
        info_columnas = detectar_columnas_por_acciones(df_wyscout)
        
        total_metricas = (len(info_columnas['defensivas']) + len(info_columnas['ofensivas']) + 
                         len(info_columnas['creacion']) + len(info_columnas['porteros']) + 
                         len(info_columnas['fisicas']))
        
        st.info(f"⚽ Dataset: {len(info_columnas['todas'])} columnas | {total_metricas} métricas de fútbol | {len(info_columnas['otras'])} otras")
        
        # FILTROS SIMPLES
        st.markdown("#### Filtros")
        
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            busqueda = st.text_input("🔍 Buscar jugador:", key="search")
        
        with col_f2:
            if 'equipo_durante_el_período_seleccionado' in df_wyscout.columns:
                equipos = ['Todos'] + sorted(df_wyscout['equipo_durante_el_período_seleccionado'].dropna().unique().tolist())
            else:
                equipos = ['Todos']
            equipo = st.selectbox("🏠 Equipo:", equipos, key="team")
        
        with col_f3:
            if 'pos_principal' in df_wyscout.columns:
                posiciones = ['Todas'] + sorted(df_wyscout['pos_principal'].dropna().unique().tolist())
            else:
                posiciones = ['Todas']
            posicion = st.selectbox("⚽ Posición:", posiciones, key="pos")
        
        with col_f4:
            if 'edad' in df_wyscout.columns:
                edad_min = int(df_wyscout['edad'].min())
                edad_max = int(df_wyscout['edad'].max())
                edad_rango = st.slider("🎂 Edad:", edad_min, edad_max, (edad_min, edad_max), key="age")
            else:
                edad_rango = (18, 35)
        
        # CONFIGURACIÓN DE COLUMNAS SIMPLIFICADA
        st.markdown("#### Configuración de Columnas")
        
        col_c1, col_c2 = st.columns([1, 2])
        
        with col_c1:
            modo = st.radio(
                "Modo de vista:",
                ["📊 Todas las columnas", "🎯 Selección manual", "⚡ Solo básicas"],
                key="mode"
            )
        
        with col_c2:
            if modo == "🎯 Selección manual":
                st.write("**Selecciona métricas por zona/acción:**")
                
                defensivas_sel = []
                ofensivas_sel = []
                creacion_sel = []
                porteros_sel = []
                fisicas_sel = []
                otras_sel = []
                
                # MÉTRICAS DEFENSIVAS
                if info_columnas['defensivas']:
                    with st.expander(f"🛡️ Defensivas ({len(info_columnas['defensivas'])})", expanded=True):
                        defensivas_sel = st.multiselect(
                            "Entradas, intercepciones, duelos, etc:",
                            info_columnas['defensivas'],
                            default=info_columnas['defensivas'][:4] if len(info_columnas['defensivas']) >= 4 else info_columnas['defensivas'],
                            key="defensivas"
                        )
                
                # MÉTRICAS OFENSIVAS
                if info_columnas['ofensivas']:
                    with st.expander(f"⚽ Ofensivas ({len(info_columnas['ofensivas'])})", expanded=True):
                        ofensivas_sel = st.multiselect(
                            "Goles, remates, ocasiones, etc:",
                            info_columnas['ofensivas'],
                            default=info_columnas['ofensivas'][:4] if len(info_columnas['ofensivas']) >= 4 else info_columnas['ofensivas'],
                            key="ofensivas"
                        )
                
                # MÉTRICAS DE CREACIÓN
                if info_columnas['creacion']:
                    with st.expander(f"🎯 Creación ({len(info_columnas['creacion'])})", expanded=True):
                        creacion_sel = st.multiselect(
                            "Asistencias, pases, jugadas clave, etc:",
                            info_columnas['creacion'],
                            default=info_columnas['creacion'][:4] if len(info_columnas['creacion']) >= 4 else info_columnas['creacion'],
                            key="creacion"
                        )
                
                # MÉTRICAS DE PORTEROS
                if info_columnas['porteros']:
                    with st.expander(f"🥅 Porteros ({len(info_columnas['porteros'])})", expanded=False):
                        porteros_sel = st.multiselect(
                            "Paradas, goles evitados, salidas, etc:",
                            info_columnas['porteros'],
                            default=[],
                            key="porteros"
                        )
                
                # MÉTRICAS FÍSICAS
                if info_columnas['fisicas']:
                    with st.expander(f"🏃 Físicas ({len(info_columnas['fisicas'])})", expanded=False):
                        fisicas_sel = st.multiselect(
                            "Velocidad, distancia, regates, minutos, etc:",
                            info_columnas['fisicas'],
                            default=info_columnas['fisicas'][:3] if len(info_columnas['fisicas']) >= 3 else info_columnas['fisicas'],
                            key="fisicas"
                        )
                
                # OTRAS MÉTRICAS
                if info_columnas['otras']:
                    with st.expander(f"📊 Otras ({len(info_columnas['otras'])})", expanded=False):
                        otras_sel = st.multiselect(
                            "Otras métricas no categorizadas:",
                            info_columnas['otras'],
                            default=[],
                            key="otras"
                        )
                
                # Combinar todas las selecciones
                columnas_seleccionadas = (info_columnas['basicas'] + defensivas_sel + ofensivas_sel + 
                                        creacion_sel + porteros_sel + fisicas_sel + otras_sel)
                
            elif modo == "📊 Todas las columnas":
                columnas_seleccionadas = info_columnas['todas']
                st.success(f"Mostrando todas las {len(columnas_seleccionadas)} columnas")
                
            else:  # Solo básicas
                columnas_seleccionadas = info_columnas['basicas']
                st.info(f"Mostrando {len(columnas_seleccionadas)} columnas básicas")
        
        # Limpiar duplicados
        columnas_mostrar = limpiar_columnas_duplicadas(columnas_seleccionadas)
        columnas_mostrar = [col for col in columnas_mostrar if col in df_wyscout.columns]
        
        st.success(f"✅ {len(columnas_mostrar)} columnas configuradas")
        
        # APLICAR FILTROS
        df_filtrado = df_wyscout.copy()
        
        if busqueda and 'jugador' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['jugador'].str.contains(busqueda, case=False, na=False)]
        
        if equipo != 'Todos' and 'equipo_durante_el_período_seleccionado' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['equipo_durante_el_período_seleccionado'] == equipo]
        
        if posicion != 'Todas' and 'pos_principal' in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado['pos_principal'] == posicion]
        
        if 'edad' in df_filtrado.columns:
            df_filtrado = df_filtrado[
                (df_filtrado['edad'] >= edad_rango[0]) & 
                (df_filtrado['edad'] <= edad_rango[1])
            ]
        
        # ================================
        # TABLA PRINCIPAL
        # ================================
        
        st.markdown(f"#### 📋 Resultados: {len(df_filtrado):,} jugadores")
        
        if len(df_filtrado) > 0:
            # Configuración inicial de paginación
            if 'page_size' not in st.session_state:
                st.session_state.page_size = 50
            if 'current_page' not in st.session_state:
                st.session_state.current_page = 1
                
            # Calcular paginación
            total_registros = len(df_filtrado)
            registros_por_pagina = st.session_state.page_size
            total_paginas = (total_registros - 1) // registros_por_pagina + 1
            
            # Ajustar página actual si es necesaria
            if st.session_state.current_page > total_paginas:
                st.session_state.current_page = 1
            
            # Calcular rango de datos
            inicio = (st.session_state.current_page - 1) * registros_por_pagina
            fin = min(inicio + registros_por_pagina, total_registros)
            
            # Mostrar datos
            df_mostrar = df_filtrado.iloc[inicio:fin][columnas_mostrar]
            
            # Configurar formato de columnas
            column_config = {}
            for col in columnas_mostrar:
                if col in df_mostrar.columns:
                    clean_name = col.replace('_', ' ').replace(',_', '').title()
                    
                    if df_mostrar[col].dtype in ['float64', 'int64']:
                        if col in ['edad', 'goles', 'asistencias']:
                            column_config[col] = st.column_config.NumberColumn(clean_name, format="%d")
                        elif '%' in col:
                            column_config[col] = st.column_config.NumberColumn(clean_name, format="%.1f%%")
                        else:
                            column_config[col] = st.column_config.NumberColumn(clean_name, format="%.2f")
                    else:
                        column_config[col] = st.column_config.TextColumn(clean_name)
            
            # MOSTRAR TABLA
            st.dataframe(
                df_mostrar,
                use_container_width=True,
                height=500,
                column_config=column_config,
                hide_index=True
            )
            
            # ================================
            # PAGINACIÓN ABAJO (COMO SOLICITASTE)
            # ================================
            
            st.markdown('<div class="bottom-pagination">', unsafe_allow_html=True)
            
            col_pag1, col_pag2, col_pag3 = st.columns([1, 1, 2])
            
            with col_pag1:
                nuevo_tamano = st.selectbox(
                    "Registros por página:",
                    [25, 50, 100, 200],
                    index=[25, 50, 100, 200].index(st.session_state.page_size),
                    key="page_size_select"
                )
                if nuevo_tamano != st.session_state.page_size:
                    st.session_state.page_size = nuevo_tamano
                    st.session_state.current_page = 1
                    st.rerun()
            
            with col_pag2:
                if total_paginas > 1:
                    nueva_pagina = st.selectbox(
                        f"Página (1-{total_paginas}):",
                        range(1, total_paginas + 1),
                        index=st.session_state.current_page - 1,
                        key="page_select"
                    )
                    if nueva_pagina != st.session_state.current_page:
                        st.session_state.current_page = nueva_pagina
                        st.rerun()
                else:
                    st.write("Página 1 de 1")
            
            with col_pag3:
                st.caption(f"Mostrando registros {inicio + 1}-{fin} de {total_registros:,}")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        else:
            st.warning("Sin resultados con estos filtros")
    
    else:
        st.error("❌ Error cargando datos Wyscout")

# ==================== PESTAÑA 2: BASE PERSONAL ====================
with tab2:
    st.markdown("### 👤 Mi Base Personal")
    st.caption("Solo jugadores con informes de scouting reales")
    
    if not df_personal.empty:
        # Filtros simples
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        
        with col_f1:
            busqueda_personal = st.text_input("🔍 Buscar:", key="search_personal")
        
        with col_f2:
            if 'equipo' in df_personal.columns:
                equipos_personal = ['Todos'] + sorted(df_personal['equipo'].dropna().unique().tolist())
            else:
                equipos_personal = ['Todos']
            equipo_personal = st.selectbox("🏠 Equipo:", equipos_personal, key="team_personal")
        
        with col_f3:
            if 'recomendacion_calculada' in df_personal.columns:
                recomendaciones = ['Todas'] + sorted(df_personal['recomendacion_calculada'].dropna().unique().tolist())
            else:
                recomendaciones = ['Todas']
            recomendacion_filtro = st.selectbox("💼 Recomendación:", recomendaciones, key="rec_personal")
        
        with col_f4:
            # Filtro por rango de nota promedio
            if 'nota_promedio' in df_personal.columns and not df_personal['nota_promedio'].isna().all():
                nota_min = float(df_personal['nota_promedio'].min())
                nota_max = float(df_personal['nota_promedio'].max())
                # Asegurar que todos los valores son float y agregar step
                nota_rango = st.slider(
                    "⭐ Nota Media:", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=(max(0.0, nota_min), min(10.0, nota_max)), 
                    step=0.1,
                    key="nota_range"
                )
            else:
                nota_rango = st.slider(
                    "⭐ Nota Media:", 
                    min_value=0.0, 
                    max_value=10.0, 
                    value=(0.0, 10.0), 
                    step=0.1,
                    key="nota_range"
                )
        
        # Aplicar filtros
        df_personal_filtrado = df_personal.copy()
        
        if busqueda_personal and 'nombre_completo' in df_personal_filtrado.columns:
            df_personal_filtrado = df_personal_filtrado[
                df_personal_filtrado['nombre_completo'].str.contains(busqueda_personal, case=False, na=False)
            ]
        
        if equipo_personal != 'Todos' and 'equipo' in df_personal_filtrado.columns:
            df_personal_filtrado = df_personal_filtrado[df_personal_filtrado['equipo'] == equipo_personal]
        
        if recomendacion_filtro != 'Todas' and 'recomendacion_calculada' in df_personal_filtrado.columns:
            df_personal_filtrado = df_personal_filtrado[df_personal_filtrado['recomendacion_calculada'] == recomendacion_filtro]
        
        # Filtro por nota - CORREGIDO para manejar valores None/NaN
        if 'nota_promedio' in df_personal_filtrado.columns:
            # Convertir a float y manejar NaN
            df_personal_filtrado['nota_promedio'] = pd.to_numeric(df_personal_filtrado['nota_promedio'], errors='coerce')
            
            # Aplicar filtro solo a valores no-NaN
            mask = (
                df_personal_filtrado['nota_promedio'].isna() |  # Incluir NaN
                (
                    (df_personal_filtrado['nota_promedio'] >= nota_rango[0]) & 
                    (df_personal_filtrado['nota_promedio'] <= nota_rango[1])
                )
            )
            df_personal_filtrado = df_personal_filtrado[mask]
        
        st.markdown(f"#### 📋 Resultados: {len(df_personal_filtrado)} jugadores")
        
        if len(df_personal_filtrado) > 0:
            # Preparar DataFrame para mostrar
            df_vista = df_personal_filtrado.copy()
            
            # Agregar emoji de recomendación para mejor visualización
            if 'recomendacion_calculada' in df_vista.columns:
                df_vista['recomendacion_visual'] = df_vista['recomendacion_calculada'].apply(
                    lambda x: '🟢 Fichar' if x == 'Fichar' else 
                             '🟡 Seguir' if 'Seguir' in str(x) else 
                             '🔴 Descartar' if x == 'Descartar' else 
                             '⚪ Sin evaluar'
                )
            
            # Definir TODAS las columnas a mostrar (incluyendo imagen)
            columnas_completas = [
                'imagen_url',
                'nombre_completo', 
                'equipo',
                'escudo_equipo',
                'posicion',
                'numero_camiseta',
                'edad',
                'nacionalidad',
                'liga',
                'nota_promedio',
                'mejor_nota',
                'peor_nota',
                'total_informes',
                'veces_observado',
                'ultima_fecha_visto',
                'recomendacion_visual',
                'scout_agregado'
            ]
            
            # Filtrar solo columnas disponibles
            columnas_disponibles = [col for col in columnas_completas if col in df_vista.columns]
            
            # Configuración completa de columnas
            column_config = {
                'imagen_url': st.column_config.ImageColumn(
                    "Foto",
                    width="small",
                    help="Foto del jugador"
                ),
                'nombre_completo': st.column_config.TextColumn(
                    "Jugador", 
                    width="medium",
                    help="Nombre completo del jugador"
                ),
                'equipo': st.column_config.TextColumn(
                    "Equipo", 
                    width="medium"
                ),
                'escudo_equipo': st.column_config.ImageColumn(
                    "Escudo",
                    width="small",
                    help="Escudo del equipo"
                ),
                'posicion': st.column_config.TextColumn(
                    "Posición", 
                    width="small"
                ),
                'numero_camiseta': st.column_config.TextColumn(
                    "Dorsal", 
                    width="small"
                ),
                'edad': st.column_config.NumberColumn(
                    "Edad", 
                    format="%d",
                    width="small"
                ),
                'nacionalidad': st.column_config.TextColumn(
                    "País", 
                    width="small"
                ),
                'liga': st.column_config.TextColumn(
                    "Liga", 
                    width="medium"
                ),
                'nota_promedio': st.column_config.ProgressColumn(
                    "Nota Media",
                    width="small",
                    format="%.1f",
                    min_value=0,
                    max_value=10
                ),
                'mejor_nota': st.column_config.NumberColumn(
                    "Mejor", 
                    format="%.0f",
                    width="small"
                ),
                'peor_nota': st.column_config.NumberColumn(
                    "Peor", 
                    format="%.0f",
                    width="small"
                ),
                'total_informes': st.column_config.NumberColumn(
                    "Informes", 
                    format="%d",
                    width="small"
                ),
                'veces_observado': st.column_config.NumberColumn(
                    "Veces Visto", 
                    format="%d",
                    width="small"
                ),
                'ultima_fecha_visto': st.column_config.DateColumn(
                    "Última Vez", 
                    width="small",
                    format="DD/MM/YYYY"
                ),
                'recomendacion_visual': st.column_config.TextColumn(
                    "Recomendación",
                    width="medium",
                    help="Recomendación basada en nota promedio"
                ),
                'scout_agregado': st.column_config.TextColumn(
                    "Scout",
                    width="small",
                    help="Scout que agregó al jugador"
                )
            }
            
            # Mostrar tabla completa con todas las funcionalidades
            st.dataframe(
                df_vista[columnas_disponibles],
                use_container_width=True,
                height=600,  # Altura mayor para mejor visualización
                column_config=column_config,
                hide_index=True
            )
            
            # Estadísticas mejoradas con más información
            st.markdown("#### 📊 Estadísticas")
            
            col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)

            with col_s1:
                if 'nota_promedio' in df_personal_filtrado.columns:
                    nota_media_global = df_personal_filtrado['nota_promedio'].mean()
                    st.metric("📊 Nota Media Global", f"{nota_media_global:.1f}/10")
                else:
                    st.metric("📊 Nota Media Global", "N/A")

            with col_s2:
                if 'total_informes' in df_personal_filtrado.columns:
                    total_informes_sum = df_personal_filtrado['total_informes'].sum()
                    st.metric("📝 Total Informes", total_informes_sum)
                else:
                    st.metric("📝 Total Informes", 0)

            with col_s3:
                if 'recomendacion_calculada' in df_personal_filtrado.columns:
                    fichajes_recom = len(df_personal_filtrado[df_personal_filtrado['recomendacion_calculada'] == 'Fichar'])
                    st.metric("🟢 Para Fichar", fichajes_recom)
                else:
                    st.metric("🟢 Para Fichar", 0)

            with col_s4:
                if 'nacionalidad' in df_personal_filtrado.columns:
                    paises_unicos = df_personal_filtrado['nacionalidad'].nunique()
                    st.metric("🌍 Países", paises_unicos)
                else:
                    st.metric("🌍 Países", "N/A")

            with col_s5:
                if 'liga' in df_personal_filtrado.columns:
                    ligas_unicas = df_personal_filtrado['liga'].nunique()
                    st.metric("🏆 Ligas", ligas_unicas)
                else:
                    st.metric("🏆 Ligas", "N/A")
            
            # Top jugadores - CORREGIDO
            if 'nota_promedio' in df_vista.columns and len(df_vista) > 0:
                # Filtrar jugadores con nota válida
                df_con_nota = df_vista[df_vista['nota_promedio'].notna() & (df_vista['nota_promedio'] > 0)]
                
                if len(df_con_nota) > 0:
                    st.markdown("#### 🏆 Top 5 Mejores Jugadores")
                    
                    # Obtener top 5
                    top_jugadores = df_con_nota.nlargest(5, 'nota_promedio')
                    
                    # Mostrar top jugadores con formato especial
                    for idx, (_, jugador) in enumerate(top_jugadores.iterrows()):
                        col1, col2, col3 = st.columns([1, 3, 1])
                        
                        with col1:
                            if pd.notna(jugador.get('imagen_url')) and jugador['imagen_url'] != '':
                                st.image(jugador['imagen_url'], width=60)
                            else:
                                st.markdown("👤")
                        
                        with col2:
                            st.markdown(f"**{idx + 1}. {jugador['nombre_completo']}**")
                            st.caption(f"{jugador['equipo']} • {jugador.get('posicion', 'N/A')}")
                        
                        with col3:
                            st.metric("Nota", f"{jugador['nota_promedio']:.1f}", 
                                     delta=f"{jugador.get('total_informes', 1)} informes",
                                     delta_color="off")
                            if 'recomendacion_visual' in jugador:
                                st.caption(jugador['recomendacion_visual'])
                            else:
                                # Calcular recomendación si no existe
                                nota = jugador['nota_promedio']
                                if nota >= 7:
                                    st.caption("🟢 Fichar")
                                elif nota >= 5:
                                    st.caption("🟡 Seguir")
                                else:
                                    st.caption("🔴 Descartar")
        
        else:
            st.warning("🔍 No se encontraron jugadores con los filtros aplicados")
            
            if st.button("🔄 Limpiar Filtros", use_container_width=True):
                st.rerun()
    
    else:
        st.info("🎯 Tu base personal está vacía")
        st.write("Los jugadores aparecerán aquí automáticamente cuando crees informes de scouting.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("⚽ Crear Mi Primer Informe", use_container_width=True, type="primary"):
                st.switch_page("pages/4_⚽_Centro de Scouting.py")
        
        with col2:
            if st.button("📚 Ver Tutorial", use_container_width=True):
                st.info("""
                **Cómo llenar tu base personal:**
                1. Ve al Centro de Scouting
                2. Selecciona un partido
                3. Evalúa jugadores y guarda informes
                4. Los jugadores aparecerán automáticamente aquí
                """)

# ==================== PESTAÑA 3: LISTA OBJETIVOS ====================
with tab3:
    st.markdown("### 👀 Lista de Objetivos")
    
    if lista_objetivos:
        df_objetivos = pd.DataFrame(lista_objetivos)
        
        # Filtros simples
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            busqueda_obj = st.text_input("🔍 Buscar:", key="search_obj")
        
        with col_f2:
            prioridades = ['Todas'] + ['alta', 'media', 'baja']
            prioridad = st.selectbox("🎯 Prioridad:", prioridades, key="priority_obj")
        
        # Aplicar filtros
        df_obj_filtrado = df_objetivos.copy()
        
        if busqueda_obj and 'jugador' in df_obj_filtrado.columns:
            df_obj_filtrado = df_obj_filtrado[
                df_obj_filtrado['jugador'].str.contains(busqueda_obj, case=False, na=False)
            ]
        
        if prioridad != 'Todas' and 'prioridad' in df_obj_filtrado.columns:
            df_obj_filtrado = df_obj_filtrado[df_obj_filtrado['prioridad'] == prioridad]
        
        st.markdown(f"#### 📋 Resultados: {len(df_obj_filtrado)} objetivos")
        
        if len(df_obj_filtrado) > 0:
            # Añadir próximo partido simplificado
            df_obj_filtrado['proximo_partido'] = "Fuera de temporada"
            
            # Configurar columnas
            columnas_obj = ['jugador', 'edad', 'equipo', 'posicion', 'prioridad', 'proximo_partido']
            columnas_obj_disponibles = [col for col in columnas_obj if col in df_obj_filtrado.columns]
            
            column_config = {
                'jugador': st.column_config.TextColumn("Jugador"),
                'edad': st.column_config.NumberColumn("Edad", format="%d años"),
                'equipo': st.column_config.TextColumn("Equipo"),
                'posicion': st.column_config.TextColumn("Posición"),
                'prioridad': st.column_config.TextColumn("Prioridad"),
                'proximo_partido': st.column_config.TextColumn("Próximo Partido")
            }
            
            st.dataframe(
                df_obj_filtrado[columnas_obj_disponibles],
                use_container_width=True,
                height=500,
                column_config=column_config,
                hide_index=True
            )
        
        else:
            st.warning("Sin objetivos con estos filtros")
    
    else:
        st.info("📋 Lista de objetivos vacía")
        if st.button("💎 Ir a Discovery", use_container_width=True):
            st.switch_page("pages/1_🔍_Jugadores.py")

# ==================== PESTAÑA 4: BÚSQUEDA GLOBAL ====================
with tab4:
    st.markdown("### 🔍 Búsqueda Global")
    
    col_s1, col_s2 = st.columns(2)
    
    with col_s1:
        busqueda_global = st.text_input("🔍 Buscar en todas las bases:", key="global_search")
    
    with col_s2:
        scope = st.selectbox("📊 Alcance:", ["Todas las bases", "Solo Wyscout", "Solo personal", "Solo objetivos"], key="scope")
    
    if busqueda_global:
        st.markdown(f"#### Resultados para: '{busqueda_global}'")
        
        resultados_total = 0
        
        # Wyscout
        if scope in ["Todas las bases", "Solo Wyscout"] and not df_wyscout.empty:
            if 'jugador' in df_wyscout.columns:
                wyscout_results = df_wyscout[
                    df_wyscout['jugador'].str.contains(busqueda_global, case=False, na=False)
                ].head(5)
                
                if not wyscout_results.empty:
                    st.markdown("##### 🌐 Wyscout:")
                    cols_show = ['jugador', 'equipo_durante_el_período_seleccionado', 'pos_principal', 'edad']
                    cols_show = [col for col in cols_show if col in wyscout_results.columns]
                    
                    st.dataframe(wyscout_results[cols_show], use_container_width=True, height=200, hide_index=True)
                    resultados_total += len(wyscout_results)
        
        # Personal
        if scope in ["Todas las bases", "Solo personal"] and not df_personal.empty:
            if 'nombre_completo' in df_personal.columns:
                personal_results = df_personal[
                    df_personal['nombre_completo'].str.contains(busqueda_global, case=False, na=False)
                ].head(5)
                
                if not personal_results.empty:
                    st.markdown("##### 👤 Base Personal:")
                    cols_show = ['nombre_completo', 'equipo', 'posicion', 'veces_observado']
                    cols_show = [col for col in cols_show if col in personal_results.columns]
                    
                    st.dataframe(personal_results[cols_show], use_container_width=True, height=200, hide_index=True)
                    resultados_total += len(personal_results)
        
        # Objetivos
        if scope in ["Todas las bases", "Solo objetivos"] and lista_objetivos:
            obj_results = [j for j in lista_objetivos if busqueda_global.lower() in j.get('jugador', '').lower()]
            
            if obj_results:
                st.markdown("##### 👀 Objetivos:")
                df_obj_results = pd.DataFrame(obj_results)
                st.dataframe(df_obj_results[['jugador', 'equipo', 'posicion', 'prioridad']], use_container_width=True, height=200, hide_index=True)
                resultados_total += len(obj_results)
        
        if resultados_total == 0:
            st.warning(f"Sin resultados para '{busqueda_global}'")
        else:
            st.success(f"✅ {resultados_total} resultados encontrados")

# ================================
# SIDEBAR SIMPLIFICADO
# ================================

with st.sidebar:
    st.markdown("### 🚀 Navegación")
    
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/1_🔍_Jugadores.py")
    
    if st.button("📊 Visualizaciones", use_container_width=True):
        st.switch_page("pages/3_📊_Visualizaciones.py")
    
    if st.button("⚽ Scouting en Vivo", use_container_width=True):
        st.switch_page("pages/4_⚽_Centro de Scouting.py")
    
    if st.button("📋 Mis Informes", use_container_width=True):
        st.switch_page("pages/5_📋_Mis_Informes.py")
    
    st.markdown("---")
    
    # Resumen simple
    st.markdown("### 📊 Resumen")
    st.write(f"🌐 **Wyscout:** {total_wyscout:,}")
    st.write(f"👤 **Personal:** {total_personal}")
    st.write(f"👀 **Objetivos:** {total_objetivos}")
    st.write(f"📊 **Total:** {total_combinado:,}")
    
    st.markdown("---")
    st.caption(f"👤 {current_user['nombre']}")
    st.caption(f"📅 {datetime.now().strftime('%d/%m/%Y')}")
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        login_manager.logout()

# Footer simple
st.markdown("---")
st.caption("📊 Sistema de Scouting Profesional")