# pages/📋_Mis_Informes.py - COMPLETO CON RADAR CHART

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import re
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from mplsoccer import Radar
import tempfile
from fpdf import FPDF
from PIL import Image
import requests
from io import BytesIO
from datetime import datetime, timedelta
import json
import logging
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from common.login import LoginManager
from models.partido_model import PartidoModel
from models.jugador_model import JugadorModel


# Configurar nivel de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # Formato simple para Streamlit
)

# Silenciar logs innecesarios
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)

from utils.resumen_scouting_ia import (
    ResumenScoutingIA, 
    agregar_resumenes_ia_al_pdf, 
    mostrar_resumenes_ia_streamlit
)
from utils.normalizacion import normalizar_nombre_metrica
from utils.normalizacion import generar_o_cargar_mapping_wyscout

# Definir rutas
excel_path = os.path.join(parent_dir, "data", "wyscout_LaLiga_limpio.xlsx")
json_path = os.path.join(parent_dir, "utils", "mapping_wyscout.json")

# Generar o cargar mapping automáticamente
mapping_wyscout = generar_o_cargar_mapping_wyscout(excel_path, json_path)
print("Mapping cargado desde:", json_path)
mapping_wyscout = {normalizar_nombre_metrica(k): normalizar_nombre_metrica(v) for k, v in mapping_wyscout.items()}

# Configuración de la página
st.set_page_config(
    page_title="Mis Informes - Scouting Pro",
    page_icon="📋",
    layout="wide"
)

# Inicializar LoginManager
login_manager = LoginManager()

# Verificación de login
if not login_manager.is_authenticated():
    login_manager.mostrar_login()
    st.stop()

# Obtener datos del usuario actual
current_user = login_manager.get_current_user()

# Inicializar modelos
partido_model = PartidoModel()
jugador_model = JugadorModel()

# Header de la página
st.markdown(f"""
<div style='
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2rem;
    border-radius: 15px;
    margin-bottom: 2rem;
    text-align: center;
    color: white;
'>
    <h1 style='margin: 0; font-size: 2.5em;'>📋 Mis Informes de Scouting</h1>
    <p style='margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.9;'>
        Historial completo de evaluaciones realizadas por <strong>{current_user['nombre']}</strong>
    </p>
</div>
""", unsafe_allow_html=True)

# Navegación
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

with nav_col1:
    if st.button("🔙 Volver a Partidos", use_container_width=True):
        st.switch_page("pages/4_⚽_Centro de Scouting.py")

st.markdown("---")

def determinar_grupo_posicion_wyscout(pos_principal):
    """
    Determina el grupo de posición basándose en la columna pos_principal de Wyscout
    """
    if not pos_principal:
        return 'general'
    
    pos = str(pos_principal).upper().strip()
    
    # Mapeo de posiciones
    if pos in ['GK', 'POR', 'G', 'PORTERO', 'GOALKEEPER']:
        return 'portero'
    elif pos in ['CB', 'DC', 'DFC', 'DCB', 'DEFENSA CENTRAL', 'CENTRE-BACK']:
        return 'defensa_central'
    elif pos in ['LB', 'RB', 'LWB', 'RWB', 'LAT', 'LI', 'LD', 'LATERAL', 'LEFT-BACK', 'RIGHT-BACK', 'WING-BACK']:
        return 'lateral'
    elif pos in ['DMC', 'DM', 'CDM', 'MCD', 'MEDIOCENTRO DEFENSIVO', 'DEFENSIVE MIDFIELDER', 'MC', 'CM', 'CMF', 'MEDIOCENTRO', 'CENTRAL MIDFIELDER']:
        return 'mediocentro'
    elif pos in ['AMC', 'CAM', 'AM', 'MCO', 'MEDIAPUNTA', 'ATTACKING MIDFIELDER','MEDIOCENTRO OFENSIVO']:
        return 'mediapunta'
    elif pos in ['LW', 'RW', 'LM', 'RM', 'WF', 'EXTREMO', 'WINGER', 'AML', 'AMR', 'EXT', 'ED', 'EI', 'EXTREMO IZQUIERDO', 'EXTREMO DERECHO']:
        return 'extremo'
    elif pos in ['CF', 'ST', 'FW', 'DC', 'DEL', 'DELANTERO', 'STRIKER', 'FORWARD', 'SS']:
        return 'delantero'
    else:
        return 'general'

def obtener_parametros_radar_wyscout(grupo_posicion, dict_jugador, mapping_wyscout):
    """
    Obtiene los parámetros del radar según la posición y verifica disponibilidad
    ACTUALIZADO: Usando columnas que realmente existen en el Excel
    """
    # IMPORTANTE: Los parametros deben usar las claves EXACTAS del Excel de Wyscout
    parametros_por_posicion = {
        'portero': [
            ('paradas/90', 'Paradas p90'),
            ('goles_concedidos/90', 'Goles concedidos p90'),
            ('salidas/90', 'Salidas p90'),
            ('%precisión_pases,_', 'Precisión pases'),
            ('%precisión_pases_largos,_', 'Pases largos'),
            ('%duelos_aéreos_ganados,_', 'Duelos aéreos'),
            ('salvadas_%', 'Porcentaje paradas')
        ],
        'defensa_central': [
            ('%duelos_aéreos_ganados,_', 'Duelos aéreos'),
            ('%duelos_ganados,_', 'Duelos ganados'),
            ('intercep/90', 'Intercepciones'),
            ('despejes/90', 'Despejes'),
            ('%precisión_pases,_', 'Precisión pases'),
            ('%precisión_pases_largos,_', 'Pases largos'),
            ('tiros_interceptados/90', 'Bloqueos')
        ],
        'lateral': [
            ('%duelos_ganados,_', 'Duelos ganados'),
            ('%precisión_centros,_', 'Centros precisos'),
            ('pases_adelante/90', 'Pases adelante'),
            ('intercep/90', 'Intercepciones'),
            ('regates/90', 'Regates'),
            ('asistencias/90', 'Asistencias'),
            ('aceleraciones/90', 'Aceleraciones')
        ],
        'mediocentro': [
            ('%precisión_pases,_', 'Precisión pases'),
            ('pases_adelante/90', 'Pases adelante'),
            ('jugadas_claves/90', 'Pases clave'),
            ('%duelos_ganados,_', 'Duelos ganados'),
            ('intercep/90', 'Intercepciones'),
            ('pases/90', 'Pases p90'),
            ('xa/90', 'xA p90')
        ],
        'mediapunta': [
            ('goles/90', 'Goles p90'),
            ('xg/90', 'xG p90'),
            ('asistencias/90', 'Asistencias p90'),
            ('xa/90', 'xA p90'),
            ('jugadas_claves/90', 'Pases clave'),
            ('regates/90', 'Regates'),
            ('remates/90', 'Tiros p90')
        ],
        'extremo': [
            ('goles/90', 'Goles p90'),
            ('xg/90', 'xG p90'),
            ('asistencias/90', 'Asistencias p90'),
            ('xa/90', 'xA p90'),
            ('regates/90', 'Regates'),
            ('%precisión_centros,_', 'Centros precisos'),
            ('aceleraciones/90', 'Aceleraciones')
        ],
        'delantero': [
            ('goles/90', 'Goles p90'),
            ('xg/90', 'xG p90'),
            ('remates/90', 'Tiros p90'),
            ('%tiros_a_la_portería,_', 'Precisión tiros'),
            ('%duelos_aéreos_ganados,_', 'Duelos aéreos'),
            ('toques_en_el_área_de_penalti/90', 'Toques área'),
            ('asistencias/90', 'Asistencias p90')
        ],
        'general': [
            ('goles/90', 'Goles p90'),
            ('asistencias/90', 'Asistencias p90'),
            ('%duelos_ganados,_', 'Duelos ganados'),
            ('%precisión_pases,_', 'Precisión pases'),
            ('regates/90', 'Regates'),
            ('intercep/90', 'Intercepciones'),
            ('pases/90', 'Pases p90')
        ]
    }

    parametros = parametros_por_posicion.get(grupo_posicion, parametros_por_posicion['general'])
    disponibles, etiquetas = [], []
    
    # Limpiar claves del diccionario del jugador (quitar comillas extra)
    dict_jugador_limpio = {}
    for k, v in dict_jugador.items():
        # Limpiar posibles comillas extra
        k_limpio = k.strip().replace("''", "'").replace("''", "'")
        dict_jugador_limpio[k_limpio] = v
    
    print(f"\n🔍 Verificando métricas para {grupo_posicion}:")
    print(f"📊 Total claves en jugador: {len(dict_jugador_limpio)}")
    
    # Para cada métrica requerida
    for columna_excel, etiqueta in parametros:
        # Buscar directamente en el diccionario del jugador
        if columna_excel in dict_jugador_limpio and pd.notnull(dict_jugador_limpio[columna_excel]):
            valor = dict_jugador_limpio[columna_excel]
            print(f"✅ {columna_excel} = {valor}")
            disponibles.append(columna_excel)
            etiquetas.append(etiqueta)
        else:
            # Intentar variaciones de la clave
            variaciones = [
                columna_excel,
                columna_excel.replace('/', '_'),
                columna_excel.replace('%', '').strip(),
                columna_excel.replace(',_', ''),
                columna_excel.replace('_', ' ')
            ]
            
            encontrado = False
            for var in variaciones:
                if var in dict_jugador_limpio and pd.notnull(dict_jugador_limpio[var]):
                    valor = dict_jugador_limpio[var]
                    print(f"✅ {var} (variación de {columna_excel}) = {valor}")
                    disponibles.append(var)
                    etiquetas.append(etiqueta)
                    encontrado = True
                    break
            
            if not encontrado:
                print(f"❌ {columna_excel} - NO ENCONTRADO")
                # Intentar encontrar columnas similares para debug
                for k in dict_jugador_limpio.keys():
                    if any(parte in k.lower() for parte in columna_excel.lower().split('_')):
                        print(f"   💡 Columna similar encontrada: {k}")
    
    print(f"\n📊 Métricas disponibles: {len(disponibles)}/{len(parametros)}")
    
    # Si tenemos menos de 5 métricas, intentar añadir algunas generales
    if len(disponibles) < 5:
        metricas_fallback = [
            ('min', 'Minutos'),
            ('partidos_jugados', 'Partidos'),
            ('edad', 'Edad')
        ]
        
        for columna, etiqueta in metricas_fallback:
            if columna in dict_jugador_limpio and columna not in disponibles:
                disponibles.append(columna)
                etiquetas.append(etiqueta)
                if len(disponibles) >= 5:
                    break
    
    return disponibles, etiquetas

def calcular_percentiles_liga(df_jugador, parametros, df_wyscout_completo=None, grupo_posicion='general'):
    """
    Calcula los percentiles REALES del jugador respecto a su liga y posición
    
    Args:
        df_jugador: dict con los datos del jugador
        parametros: lista de métricas a evaluar
        df_wyscout_completo: DataFrame con todos los jugadores de Wyscout (opcional)
        grupo_posicion: grupo de posición del jugador para comparación más precisa
    
    Returns:
        lista de percentiles (0-100) para cada parámetro
    """
    
    percentiles = []
    
    # Si no se proporciona el DataFrame, intentar cargarlo
    if df_wyscout_completo is None:
        try:
            rutas_posibles = [
                'data/wyscout_LaLiga_limpio.xlsx',
                '../data/wyscout_LaLiga_limpio.xlsx',
                os.path.join(os.path.dirname(__file__), '../data/wyscout_LaLiga_limpio.xlsx')
            ]
            
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    print(f"📊 Cargando datos Wyscout para percentiles desde: {ruta}")
                    df_wyscout_completo = pd.read_excel(ruta)
                    break
                    
        except Exception as e:
            print(f"⚠️ No se pudieron cargar datos Wyscout para percentiles: {e}")
            df_wyscout_completo = None
    
    # Si no hay datos de comparación, usar el método simplificado anterior
    if df_wyscout_completo is None or df_wyscout_completo.empty:
        print("⚠️ Usando percentiles simulados (sin datos de comparación)")
        for param in parametros:
            valor = df_jugador.get(param, 0)
            if pd.isna(valor):
                valor = 0
                
            if '%' in param:  # Porcentajes
                percentil = min(valor, 100)
            elif 'goles' in param.lower() or 'xg' in param.lower():
                percentil = min(valor * 100, 100)
            elif 'asistencias' in param.lower() or 'xa' in param.lower():
                percentil = min(valor * 150, 100)
            else:
                percentil = min(valor * 10, 100)
            
            percentiles.append(percentil)
        return percentiles
    
    # CÁLCULO DE PERCENTILES REALES
    print(f"\n📊 Calculando percentiles reales para {len(parametros)} métricas")
    
    # Filtrar jugadores con minutos mínimos (ej: 500 minutos)
    min_minutos = 500
    df_filtrado = df_wyscout_completo[df_wyscout_completo['min'] >= min_minutos].copy()
    print(f"👥 Jugadores con >{min_minutos} min: {len(df_filtrado)}/{len(df_wyscout_completo)}")
    
    # Si es posible, filtrar por grupo de posición similar
    if grupo_posicion != 'general' and 'pos_principal' in df_filtrado.columns:
        # Mapeo de grupos de posición
        grupos_similares = {
            'portero': ['GK', 'POR', 'G', 'PORTERO'],
            'defensa_central': ['CB', 'DC', 'DFC', 'DCB'],
            'lateral': ['LB', 'RB', 'LWB', 'RWB', 'LAT', 'LI', 'LD'],
            'mediocentro': ['DMC', 'DM', 'CDM', 'MC', 'CM', 'CMF'],
            'mediapunta': ['AMC', 'CAM', 'AM', 'MCO', 'MEDIOCENTRO OFENSIVO'],
            'extremo': ['LW', 'RW', 'LM', 'RM', 'WF', 'AML', 'AMR'],
            'delantero': ['CF', 'ST', 'FW', 'DC', 'DEL']
        }
        
        if grupo_posicion in grupos_similares:
            posiciones_validas = grupos_similares[grupo_posicion]
            mascara_posicion = df_filtrado['pos_principal'].str.upper().isin(posiciones_validas)
            df_comparacion = df_filtrado[mascara_posicion].copy()
            
            if len(df_comparacion) < 10:  # Si hay muy pocos jugadores, usar todos
                print(f"⚠️ Solo {len(df_comparacion)} jugadores en {grupo_posicion}, usando todos")
                df_comparacion = df_filtrado
            else:
                print(f"🎯 Comparando con {len(df_comparacion)} jugadores de {grupo_posicion}")
        else:
            df_comparacion = df_filtrado
    else:
        df_comparacion = df_filtrado
    
    # Calcular percentil para cada parámetro
    for i, param in enumerate(parametros):
        valor_jugador = df_jugador.get(param, 0)
        if pd.isna(valor_jugador):
            valor_jugador = 0
        
        # Convertir a float de forma segura
        try:
            valor_jugador = float(valor_jugador)
        except (ValueError, TypeError):
            print(f"⚠️ {param}: Valor del jugador no es numérico: {valor_jugador}")
            percentiles.append(50)  # Valor neutral
            continue
        
        # Obtener todos los valores de esta métrica
        if param in df_comparacion.columns:
            # Obtener la columna y limpiar valores no numéricos
            valores_liga_raw = df_comparacion[param]
            
            # Convertir a numérico, forzando errores a NaN
            valores_liga = pd.to_numeric(valores_liga_raw, errors='coerce')
            
            # Eliminar NaN
            valores_liga = valores_liga.dropna()
            
            # Verificar que tengamos valores válidos
            if len(valores_liga) > 0:
                # Verificar que todos los valores sean numéricos
                if valores_liga.dtype in ['float64', 'int64', 'float32', 'int32']:
                    # Calcular percentil real
                    percentil = stats.percentileofscore(valores_liga, valor_jugador, kind='rank')
                    
                    # Información adicional para debug
                    media_liga = valores_liga.mean()
                    mediana_liga = valores_liga.median()
                    
                    print(f"📈 {param}:")
                    print(f"   - Valor jugador: {valor_jugador:.2f}")
                    print(f"   - Media liga: {media_liga:.2f}")
                    print(f"   - Mediana liga: {mediana_liga:.2f}")
                    print(f"   - Percentil: {percentil:.1f}")
                else:
                    print(f"⚠️ {param}: Valores no numéricos después de conversión")
                    # Usar método simple como fallback
                    if '%' in param:
                        percentil = min(valor_jugador, 100)
                    else:
                        percentil = min(valor_jugador * 20, 100)
            else:
                print(f"⚠️ {param}: Sin datos válidos de comparación")
                # Fallback al método simple
                if '%' in param:
                    percentil = min(valor_jugador, 100)
                else:
                    percentil = min(valor_jugador * 20, 100)
        else:
            print(f"❌ {param}: No encontrado en datos Wyscout")
            percentil = 50  # Valor neutral si no hay datos
        
        percentiles.append(round(percentil, 1))
    
    print(f"\n✅ Percentiles calculados: {percentiles}")
    return percentiles


# Función auxiliar para cargar y cachear datos Wyscout (optimización)
@st.cache_data
def cargar_datos_wyscout_para_percentiles():
    """
    Carga los datos de Wyscout una sola vez y los cachea para eficiencia
    Incluye limpieza de datos
    """
    try:
        rutas_posibles = [
            'data/wyscout_LaLiga_limpio.xlsx',
            '../data/wyscout_LaLiga_limpio.xlsx',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '../data/wyscout_LaLiga_limpio.xlsx')
        ]
        
        for ruta in rutas_posibles:
            if os.path.exists(ruta):
                print(f"💾 Cargando y cacheando datos Wyscout desde: {ruta}")
                df = pd.read_excel(ruta)
                
                # Limpiar columnas numéricas
                columnas_numericas = [
                    'goles/90', 'xg/90', 'asistencias/90', 'xa/90', 
                    'regates/90', 'remates/90', 'jugadas_claves/90',
                    '%duelos_ganados,_', '%precisión_pases,_', 
                    'intercep/90', 'entradas/90', 'pases/90'
                ]
                
                for col in columnas_numericas:
                    if col in df.columns:
                        # Convertir a numérico, reemplazando errores con NaN
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                print(f"✅ Datos cargados y limpiados: {len(df)} jugadores")
                return df
                
    except Exception as e:
        print(f"❌ Error cargando datos Wyscout: {e}")
    
    return None


# Actualización en crear_radar_chart_jugador para usar percentiles reales
def calcular_percentiles_con_datos_reales(jugador_wyscout, parametros_disponibles, grupo_posicion):
    """
    Wrapper para calcular percentiles con datos reales de Wyscout
    """
    # Cargar datos cacheados
    df_wyscout = cargar_datos_wyscout_para_percentiles()
    
    if df_wyscout is not None:
        # Calcular percentiles reales
        percentiles = calcular_percentiles_liga(
            jugador_wyscout, 
            parametros_disponibles,
            df_wyscout,
            grupo_posicion
        )
    else:
        # Fallback al método simple
        percentiles = calcular_percentiles_liga(jugador_wyscout, parametros_disponibles)
    
    return percentiles

def inferir_posicion_por_metricas(informes_ordenados):
    """
    Intenta inferir la posición basándose en las métricas evaluadas
    """
    metricas_frecuentes = {}
    
    for informe in informes_ordenados:
        metricas_json = informe.get('metricas', {})
        if isinstance(metricas_json, str):
            try:
                metricas_json = json.loads(metricas_json)
            except:
                continue
        
        # Analizar métricas evaluadas
        if 'evaluaciones' in metricas_json:
            for metrica in metricas_json['evaluaciones'].keys():
                metrica_lower = metrica.lower()
                metricas_frecuentes[metrica_lower] = metricas_frecuentes.get(metrica_lower, 0) + 1
        
        if 'categorias' in metricas_json:
            for categoria, metricas_cat in metricas_json['categorias'].items():
                for metrica in metricas_cat.keys():
                    metrica_lower = metrica.lower()
                    metricas_frecuentes[metrica_lower] = metricas_frecuentes.get(metrica_lower, 0) + 1
    
    # Patrones de métricas por posición
    patrones_posicion = {
        'Delantero': ['finalizacion', 'desmarque', 'remate', 'gol', 'area'],
        'Extremo': ['regate', 'centro', 'banda', 'velocidad', 'desborde'],
        'Media Punta': ['creatividad', 'ultimo_pase', 'vision', 'entre_lineas'],
        'Mediocentro': ['pase', 'distribucion', 'llegada', 'recuperacion'],
        'Mediocentro Defensivo': ['recuperacion', 'corte', 'posicionamiento', 'barrido'],
        'Central': ['marcaje', 'aereo', 'despeje', 'salida_balon'],
        'Lateral': ['subida', 'repliegue', 'centro', 'apoyo'],
        'Portero': ['parada', 'salida', 'blocaje', 'mano']
    }
    
    # Contar coincidencias
    mejores_coincidencias = []
    for posicion, patrones in patrones_posicion.items():
        coincidencias = 0
        for patron in patrones:
            for metrica in metricas_frecuentes:
                if patron in metrica:
                    coincidencias += metricas_frecuentes[metrica]
        
        if coincidencias > 0:
            mejores_coincidencias.append((posicion, coincidencias))
    
    # Ordenar y devolver la mejor
    if mejores_coincidencias:
        mejores_coincidencias.sort(key=lambda x: x[1], reverse=True)
        return mejores_coincidencias[0][0]
    
    return None

def crear_radar_metricas_especificas(informes_ordenados, posicion):
    """
    Crea radar con métricas específicas para evaluaciones video_completo
    MEJORADO: Funciona incluso con 1 solo informe
    """
    # Definir métricas clave por posición (8-10 máximo)
    metricas_por_posicion = {
        'Portero': [
            ('paradas_reflejos', 'Paradas'),
            ('blocaje_seguro', 'Blocaje'),
            ('juego_con_pies', 'Juego pies'),
            ('salidas_aereas', 'Salidas'),
            ('mano_a_mano', '1vs1'),
            ('comunicacion_defensa', 'Comunicación'),
            ('concentracion', 'Concentración'),
            ('confianza', 'Confianza')
        ],
        'Central': [
            ('juego_aereo', 'Juego aéreo'),
            ('marcaje_hombre', 'Marcaje'),
            ('salida_balon', 'Salida balón'),
            ('anticipacion', 'Anticipación'),
            ('fuerza', 'Fuerza'),
            ('concentracion', 'Concentración'),
            ('liderazgo', 'Liderazgo'),
            ('timing_subida', 'Timing')
        ],
        'Lateral Derecho': [
            ('centro_precision', 'Centros'),
            ('subida_ataque', 'Subidas'),
            ('velocidad', 'Velocidad'),
            ('resistencia', 'Resistencia'),
            ('tackle', 'Entradas'),
            ('repliegue', 'Repliegue'),
            ('apoyo_interior', 'Apoyo'),
            ('valentia', 'Valentía')
        ],
        'Lateral Izquierdo': [
            ('centro_precision', 'Centros'),
            ('subida_ataque', 'Subidas'),
            ('velocidad', 'Velocidad'),
            ('resistencia', 'Resistencia'),
            ('tackle', 'Entradas'),
            ('repliegue', 'Repliegue'),
            ('apoyo_interior', 'Apoyo'),
            ('valentia', 'Valentía')
        ],
        'Mediocentro Defensivo': [
            ('interceptacion', 'Intercepción'),
            ('distribucion', 'Distribución'),
            ('posicionamiento', 'Posición'),
            ('resistencia', 'Resistencia'),
            ('pase_largo', 'Pase largo'),
            ('recuperacion', 'Recuperación'),
            ('concentracion', 'Concentración'),
            ('liderazgo', 'Liderazgo')
        ],
        'Mediocentro': [
            ('pase_corto', 'Pase corto'),
            ('vision_juego', 'Visión'),
            ('llegada_area', 'Llegada'),
            ('resistencia', 'Resistencia'),
            ('pressing', 'Pressing'),
            ('creatividad', 'Creatividad'),
            ('movilidad', 'Movilidad'),
            ('transicion_def-atq', 'Transición')
        ],
        'Media Punta': [
            ('ultimo_pase', 'Último pase'),
            ('control_espacios_reducidos', 'Control'),
            ('regate_corto', 'Regate'),
            ('creatividad', 'Creatividad'),
            ('encontrar_espacios', 'Espacios'),
            ('vision', 'Visión'),
            ('cambio_orientacion', 'Cambio juego'),
            ('asociacion', 'Asociación')
        ],
        'Extremo Derecho': [
            ('regate', 'Regate'),
            ('centro', 'Centros'),
            ('finalizacion', 'Finalización'),
            ('velocidad_punta', 'Velocidad'),
            ('cambio_ritmo', 'Cambio ritmo'),
            ('desmarque', 'Desmarque'),
            ('profundidad', 'Profundidad'),
            ('recorte_interior', 'Recorte')
        ],
        'Extremo Izquierdo': [
            ('regate', 'Regate'),
            ('centro', 'Centros'),
            ('finalizacion', 'Finalización'),
            ('velocidad_punta', 'Velocidad'),
            ('cambio_ritmo', 'Cambio ritmo'),
            ('desmarque', 'Desmarque'),
            ('profundidad', 'Profundidad'),
            ('recorte_interior', 'Recorte')
        ],
        'Delantero': [
            ('finalizacion_pie_derecho', 'Final. PD'),
            ('finalizacion_cabeza', 'Cabeza'),
            ('desmarque_ruptura', 'Desmarques'),
            ('primer_toque', '1er toque'),
            ('potencia', 'Potencia'),
            ('sangre_fria', 'Sangre fría'),
            ('juego_espaldas', 'Juego espaldas'),
            ('pressing', 'Pressing')
        ]
    }
    
    metricas_config = metricas_por_posicion.get(posicion, metricas_por_posicion['Mediocentro'])
    
    # Extraer valores con ponderación
    valores_ponderados = {}
    pesos_totales = {}
    metricas_encontradas = set()  # Para trackear qué métricas encontramos
    
    for idx, informe in enumerate(informes_ordenados):
        peso = 1.0 - (0.1 * idx)  # Mayor peso a informes recientes
        
        metricas_json = informe.get('metricas', {})
        if isinstance(metricas_json, str):
            try:
                metricas_json = json.loads(metricas_json)
            except:
                continue
        
        print(f"📊 Analizando informe {idx + 1}, tipo: {informe.get('tipo_evaluacion')}")
        
        # MEJORADO: Buscar en múltiples lugares
        # 1. Buscar en categorías
        if 'categorias' in metricas_json:
            print(f"   - Encontradas categorías: {list(metricas_json['categorias'].keys())}")
            for categoria, metricas_cat in metricas_json['categorias'].items():
                for nombre_metrica, valor in metricas_cat.items():
                    nombre_norm = nombre_metrica.lower().replace(' ', '_').replace('ó', 'o').replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ú', 'u')
                    
                    # Buscar coincidencia con nuestras métricas clave
                    for metrica_key, _ in metricas_config:
                        if metrica_key in nombre_norm or nombre_norm in metrica_key:
                            if metrica_key not in valores_ponderados:
                                valores_ponderados[metrica_key] = 0
                                pesos_totales[metrica_key] = 0
                            
                            try:
                                valor_num = float(valor)
                                valores_ponderados[metrica_key] += valor_num * peso
                                pesos_totales[metrica_key] += peso
                                metricas_encontradas.add(metrica_key)
                                print(f"   ✓ {metrica_key}: {valor}")
                            except:
                                pass
                            break
        
        # 2. Buscar en evaluaciones (si existe)
        if 'evaluaciones' in metricas_json:
            print(f"   - Encontradas evaluaciones")
            for nombre_metrica, valor in metricas_json['evaluaciones'].items():
                nombre_norm = nombre_metrica.lower().replace(' ', '_')
                
                for metrica_key, _ in metricas_config:
                    if metrica_key in nombre_norm or nombre_norm in metrica_key:
                        if metrica_key not in valores_ponderados:
                            valores_ponderados[metrica_key] = 0
                            pesos_totales[metrica_key] = 0
                        
                        try:
                            valor_num = float(valor)
                            valores_ponderados[metrica_key] += valor_num * peso
                            pesos_totales[metrica_key] += peso
                            metricas_encontradas.add(metrica_key)
                            print(f"   ✓ {metrica_key}: {valor}")
                        except:
                            pass
                        break
    
    print(f"📊 Métricas encontradas: {len(metricas_encontradas)}")
    
    # Si encontramos menos de 4 métricas específicas, complementar con categorías generales
    if len(metricas_encontradas) < 4:
        print("⚠️ Pocas métricas específicas, añadiendo promedios de categorías")
        
        # Extraer promedios de categorías del primer informe
        if informes_ordenados:
            primer_informe = informes_ordenados[0]
            metricas_json = primer_informe.get('metricas', {})
            if isinstance(metricas_json, str):
                try:
                    metricas_json = json.loads(metricas_json)
                except:
                    metricas_json = {}
            
            # Buscar promedios
            if 'promedios' in metricas_json:
                # Añadir las 4 categorías como métricas base
                categorias_base = [
                    ('tecnica_general', 'Técnica', metricas_json['promedios'].get('tecnicos', 5)),
                    ('tactica_general', 'Táctica', metricas_json['promedios'].get('tacticos', 5)),
                    ('fisico_general', 'Físico', metricas_json['promedios'].get('fisicos', 5)),
                    ('mental_general', 'Mental', metricas_json['promedios'].get('mentales', 5))
                ]
                
                for metrica_key, etiqueta, valor in categorias_base:
                    if metrica_key not in valores_ponderados:
                        valores_ponderados[metrica_key] = valor
                        pesos_totales[metrica_key] = 1
                        metricas_config.append((metrica_key, etiqueta))
    
    # Calcular promedios y preparar resultado
    etiquetas = []
    valores = []
    
    # Primero las categorías generales si las añadimos
    for metrica_key, etiqueta in metricas_config:
        if metrica_key in valores_ponderados and pesos_totales[metrica_key] > 0:
            valor_promedio = round(valores_ponderados[metrica_key] / pesos_totales[metrica_key], 1)
            etiquetas.append(etiqueta)
            valores.append(valor_promedio)
    
    # Si aún tenemos pocas métricas, devolver None para usar otro método
    if len(valores) < 5:
        print(f"⚠️ Solo {len(valores)} métricas, insuficiente para radar específico")
        return None
    
    print(f"✅ Radar específico generado con {len(valores)} métricas")
    
    return {
        'etiquetas': etiquetas,
        'valores': valores,
        'modo': 'especifico'
    }

def obtener_metricas_para_pdf(informe_data):
    """
    Extrae y normaliza las métricas del informe para usarlas en barras y radar.
    Maneja tanto estructura nueva como antigua.
    VERSIÓN CORREGIDA: Maneja conversión de tipos correctamente
    """
    import json
    
    metricas_raw = informe_data.get("metricas", {})
    if isinstance(metricas_raw, str):
        try:
            metricas = json.loads(metricas_raw)
        except json.JSONDecodeError:
            metricas = {}
    else:
        metricas = metricas_raw if isinstance(metricas_raw, dict) else {}

    resultado = {
        "modo": "campo",
        "categorias": {},
        "metricas": [],
        "promedios": {
            "tecnicos": 0,
            "tacticos": 0,
            "fisicos": 0,
            "mentales": 0
        }
    }

    # CASO 1: Estructura nueva con promedios
    if 'promedios' in metricas:
        resultado["modo"] = "completo"
        resultado["promedios"] = {
            'tecnicos': float(metricas['promedios'].get('tecnicos', 0)),
            'tacticos': float(metricas['promedios'].get('tacticos', 0)),
            'fisicos': float(metricas['promedios'].get('fisicos', 0)),
            'mentales': float(metricas['promedios'].get('mentales', 0))
        }
        
        # Si hay categorías, extraerlas
        if 'categorias' in metricas:
            resultado["categorias"] = metricas['categorias']
    
    # CASO 2: Estructura antigua con categorías directas (como la de ID 25, 26)
    elif all(key in metricas for key in ['tecnicos', 'tacticos', 'fisicos', 'mentales']):
        resultado["modo"] = "completo"
        resultado["categorias"] = metricas
        
        # Calcular promedios desde las categorías - CORREGIDO
        for categoria in ['tecnicos', 'tacticos', 'fisicos', 'mentales']:
            valores_raw = list(metricas.get(categoria, {}).values())
            # Convertir todos los valores a float, ignorando strings
            valores = []
            for v in valores_raw:
                try:
                    valores.append(float(v))
                except (ValueError, TypeError):
                    # Si no se puede convertir, ignorar este valor
                    continue
            
            if valores:
                resultado["promedios"][categoria] = round(sum(valores) / len(valores), 1)
            else:
                resultado["promedios"][categoria] = 0
    
    # CASO 3: Evaluaciones de campo
    elif 'evaluaciones' in metricas:
        for nombre, valor in metricas['evaluaciones'].items():
            try:
                valor_float = float(valor)
                resultado["metricas"].append({"nombre": nombre, "valor": round(valor_float, 2)})
            except (ValueError, TypeError):
                # Si no se puede convertir a float, ignorar
                continue
        
        # Intentar calcular promedios si no existen
        if not any(resultado["promedios"].values()):
            valores = [m['valor'] for m in resultado["metricas"]]
            if valores:
                promedio_general = sum(valores) / len(valores)
                # Distribuir el promedio con variación
                resultado["promedios"] = {
                    'tecnicos': round(promedio_general + 0.2, 1),
                    'tacticos': round(promedio_general, 1),
                    'fisicos': round(promedio_general - 0.2, 1),
                    'mentales': round(promedio_general, 1)
                }
    
    # CASO 4: Si es un diccionario plano de métricas (estructura muy antigua)
    elif isinstance(metricas, dict) and len(metricas) > 0:
        # Verificar si son evaluaciones planas
        es_plano = True
        valores_planos = []
        
        for k, v in metricas.items():
            # Saltar claves de metadatos
            if k in ['tipo', 'posicion_evaluada', 'version', 'timestamp', 'num_metricas_evaluadas']:
                es_plano = False
                break
            
            try:
                valores_planos.append(float(v))
            except (ValueError, TypeError):
                # Si hay algún valor que no es numérico, no es estructura plana
                es_plano = False
                break
        
        if es_plano and valores_planos:
            # Es una estructura plana antigua de evaluaciones
            promedio_general = sum(valores_planos) / len(valores_planos)
            resultado["promedios"] = {
                'tecnicos': round(promedio_general + 0.2, 1),
                'tacticos': round(promedio_general, 1),
                'fisicos': round(promedio_general - 0.2, 1),
                'mentales': round(promedio_general, 1)
            }
            
            # Añadir las métricas individuales
            for k, v in metricas.items():
                try:
                    resultado["metricas"].append({
                        "nombre": k,
                        "valor": round(float(v), 2)
                    })
                except:
                    continue
    
    # CASO 5: Si todo falla, usar nota general
    if not any(resultado["promedios"].values()):
        try:
            nota_general = float(informe_data.get('nota_general', 7))
        except (ValueError, TypeError):
            nota_general = 7.0
            
        resultado["promedios"] = {
            'tecnicos': round(nota_general + 0.3, 1),
            'tacticos': round(nota_general + 0.5, 1),
            'fisicos': round(max(0, nota_general - 0.5), 1),  # Asegurar que no sea negativo
            'mentales': round(nota_general, 1)
        }

    # Asegurar que todos los promedios estén en el rango 0-10
    for categoria in resultado["promedios"]:
        resultado["promedios"][categoria] = max(0, min(10, resultado["promedios"][categoria]))

    return resultado

def crear_radar_categorias_basicas(informes_ordenados, posicion):
    """
    Crea radar con categorías + métricas básicas para evaluaciones campo
    """
    # Acumuladores para promedios de categorías
    suma_categorias = {
        'tecnico': 0, 'tactico': 0, 'fisico': 0, 'mental': 0
    }
    pesos_categorias = {
        'tecnico': 0, 'tactico': 0, 'fisico': 0, 'mental': 0
    }
    
    # Métricas específicas de campo según posición
    metricas_campo_posicion = {
        'Delantero': ['finalizacion', 'desmarques', 'juego_aereo', 'pressing'],
        'Media Punta': ['creatividad', 'ultimo_pase', 'control_balon', 'movilidad'],
        'Extremo Derecho': ['regate', 'velocidad', 'centros', 'finalizacion'],
        'Extremo Izquierdo': ['regate', 'velocidad', 'centros', 'finalizacion'],
        'Mediocentro': ['pase', 'vision_de_juego', 'recuperacion', 'llegada'],
        'Mediocentro Defensivo': ['recuperacion', 'distribucion', 'posicionamiento', 'duelos'],
        'Central': ['marcaje', 'juego_aereo', 'salida_de_balon', 'posicionamiento'],
        'Lateral Derecho': ['defensa_1v1', 'apoyo_ofensivo', 'centros', 'fisico'],
        'Lateral Izquierdo': ['defensa_1v1', 'apoyo_ofensivo', 'centros', 'fisico'],
        'Portero': ['paradas_y_reflejos', 'juego_con_pies', 'salidas', 'comunicacion']
    }
    
    metricas_especificas = metricas_campo_posicion.get(posicion, ['finalizacion', 'creatividad', 'trabajo_defensivo', 'liderazgo'])
    valores_metricas = {m: [] for m in metricas_especificas}
    
    # Mapeo correcto de categorías para evitar el problema con 'mentales' -> 'mentale'
    mapeo_categorias = {
        'tecnicos': 'tecnico',
        'tacticos': 'tactico',
        'fisicos': 'fisico',
        'mentales': 'mental'  # Mapeo explícito
    }
    
    # Procesar informes
    for idx, informe in enumerate(informes_ordenados):
        peso = 1.0 - (0.1 * idx)
        
        metricas_json = informe.get('metricas', {})
        if isinstance(metricas_json, str):
            try:
                metricas_json = json.loads(metricas_json)
            except:
                continue
        
        # Para evaluaciones campo
        if informe.get('tipo_evaluacion') == 'campo' and 'evaluaciones' in metricas_json:
            # Buscar métricas específicas
            for metrica, valor in metricas_json['evaluaciones'].items():
                metrica_norm = metrica.lower().replace(' ', '_')
                for metrica_buscar in metricas_especificas:
                    if metrica_buscar in metrica_norm or metrica_norm in metrica_buscar:
                        try:
                            valor_num = float(valor)
                            valores_metricas[metrica_buscar].append(valor_num)
                        except (ValueError, TypeError):
                            continue
                        break
        # NUEVO: También buscar en categorías para enriquecer el radar
        if isinstance(metricas_json, dict) and 'categorias' in metricas_json:
            for categoria, metricas_cat in metricas_json['categorias'].items():
                for nombre_metrica, valor in metricas_cat.items():
                    metrica_norm = nombre_metrica.lower().replace(' ', '_')
                    for metrica_buscar in metricas_especificas:
                        if metrica_buscar in metrica_norm or metrica_norm in metrica_buscar:
                            try:
                                valor_num = float(valor)
                                if metrica_buscar not in valores_metricas:
                                    valores_metricas[metrica_buscar] = []
                                valores_metricas[metrica_buscar].append(valor_num)
                            except (ValueError, TypeError):
                                continue
                            break
                        
        # Calcular promedios de categorías - VERSIÓN CORREGIDA
        if isinstance(metricas_json, dict):
            # Opción 1: Tiene estructura con 'promedios'
            if 'promedios' in metricas_json:
                for cat_plural, cat_simple in mapeo_categorias.items():
                    if cat_plural in metricas_json['promedios']:
                        try:
                            valor_prom = float(metricas_json['promedios'][cat_plural])
                            suma_categorias[cat_simple] += valor_prom * peso
                            pesos_categorias[cat_simple] += peso
                        except (ValueError, TypeError):
                            continue
            
            # Opción 2: Tiene categorías directas (sin 'promedios')
            elif any(cat in metricas_json for cat in mapeo_categorias.keys()):
                for cat_plural, cat_simple in mapeo_categorias.items():
                    if cat_plural in metricas_json and isinstance(metricas_json[cat_plural], dict):
                        # Convertir valores a float de forma segura
                        valores = []
                        for v in metricas_json[cat_plural].values():
                            try:
                                valor_float = float(v)
                                if valor_float > 0:
                                    valores.append(valor_float)
                            except (ValueError, TypeError):
                                continue
                        
                        if valores:
                            promedio = sum(valores) / len(valores)
                            suma_categorias[cat_simple] += promedio * peso
                            pesos_categorias[cat_simple] += peso
    
    # Preparar resultado
    etiquetas = ['Técnica', 'Táctica', 'Físico', 'Mental']
    valores = []
    
    # Promedios de categorías
    for cat in ['tecnico', 'tactico', 'fisico', 'mental']:
        if pesos_categorias[cat] > 0:
            valores.append(round(suma_categorias[cat] / pesos_categorias[cat], 1))
        else:
            valores.append(5.0)
    
    # Añadir métricas específicas
    for metrica in metricas_especificas:
        if valores_metricas[metrica]:
            promedio = round(sum(valores_metricas[metrica]) / len(valores_metricas[metrica]), 1)
            etiqueta = metrica.replace('_', ' ').title()
            # Simplificar etiquetas
            etiqueta = etiqueta.replace('Vision De Juego', 'Visión')
            etiqueta = etiqueta.replace('Trabajo Defensivo', 'Trabajo Def.')
            etiqueta = etiqueta.replace('Juego Aereo', 'J. Aéreo')
            etiqueta = etiqueta.replace('Apoyo Ofensivo', 'Apoyo Of.')
            
            etiquetas.append(etiqueta)
            valores.append(promedio)
    
    return {
        'etiquetas': etiquetas,
        'valores': valores,
        'modo': 'basico'
    }

def crear_radar_hibrido(informes_ordenados, posicion, num_campo, num_video):
    """
    Crea radar híbrido combinando ambos tipos de evaluaciones
    MEJORADO: Usa BeSoccer como fallback para posición
    """
    print(f"🔄 Creando radar híbrido para posición: {posicion}")
    
    # CORRECCIÓN: Si la posición es None, intentar obtenerla
    if not posicion or posicion == 'None' or posicion == 'N/A':
        # 1. Intentar desde los informes
        for informe in informes_ordenados:
            pos_temp = informe.get('posicion') or informe.get('posicion_evaluada') or informe.get('posicion_real')
            if pos_temp and pos_temp not in ['None', 'N/A', '', None]:
                posicion = pos_temp
                print(f"📍 Posición recuperada del informe: {posicion}")
                break
        
        # 2. Si aún no hay posición, intentar BeSoccer
        if not posicion or posicion in ['None', 'N/A', '', None]:
            print("🔍 Buscando posición en BeSoccer...")
            
            # Buscar URL de BeSoccer en los informes
            url_besoccer = None
            for informe in informes_ordenados:
                url_temp = informe.get('url_besoccer')
                if url_temp:
                    url_besoccer = url_temp
                    break
            
            if url_besoccer:
                try:
                    from utils.besoccer_scraper import BeSoccerScraper
                    scraper = BeSoccerScraper()
                    datos_besoccer = scraper.obtener_datos_perfil_jugador(url_besoccer)
                    
                    if datos_besoccer:
                        # Intentar posición principal primero
                        pos_besoccer = datos_besoccer.get('posicion_principal')
                        if pos_besoccer and pos_besoccer not in ['None', 'N/A', '', None]:
                            posicion = pos_besoccer
                            print(f"✅ Posición obtenida de BeSoccer: {posicion}")
                        else:
                            # Intentar posición secundaria
                            pos_secundaria = datos_besoccer.get('posicion_secundaria')
                            if pos_secundaria and pos_secundaria not in ['None', 'N/A', '', None]:
                                posicion = pos_secundaria
                                print(f"✅ Posición secundaria de BeSoccer: {posicion}")
                except Exception as e:
                    print(f"⚠️ Error obteniendo posición de BeSoccer: {e}")
        
        # 3. Si todo falla, usar por defecto basado en métricas evaluadas
        if not posicion or posicion in ['None', 'N/A', '', None]:
            # Intentar inferir la posición basándose en las métricas evaluadas
            posicion_inferida = inferir_posicion_por_metricas(informes_ordenados)
            if posicion_inferida:
                posicion = posicion_inferida
                print(f"🎯 Posición inferida por métricas: {posicion}")
            else:
                posicion = 'Mediocentro'
                print(f"⚠️ Usando posición por defecto: {posicion}")
    
    # [Resto del código permanece igual...]
    print(f"📊 Generando radar para posición final: {posicion}")
    
    # Intentar primero obtener métricas específicas de videos
    radar_especifico = crear_radar_metricas_especificas(informes_ordenados, posicion)
    
    # Obtener también las categorías básicas
    radar_basico = crear_radar_categorias_basicas(informes_ordenados, posicion)
    
    if radar_especifico and len(radar_especifico['valores']) >= 5:
        # Si tenemos suficientes métricas específicas, combinar con categorías principales
        etiquetas_finales = ['Técnica', 'Táctica', 'Físico', 'Mental']
        valores_finales = radar_basico['valores'][:4]  # Solo las 4 categorías
        
        # Añadir las mejores métricas específicas (hasta 6 más)
        mejores_indices = sorted(range(len(radar_especifico['valores'])), 
                               key=lambda i: radar_especifico['valores'][i], 
                               reverse=True)[:6]
        
        for idx in mejores_indices:
            etiquetas_finales.append(radar_especifico['etiquetas'][idx])
            valores_finales.append(radar_especifico['valores'][idx])
        
        return {
            'etiquetas': etiquetas_finales,
            'valores': valores_finales,
            'modo': 'hibrido'
        }
    else:
        # Si no hay suficientes métricas específicas, usar el básico
        return radar_basico
    
# def crear_radar_chart_jugador(datos_wyscout, nombre_jugador, equipo_jugador=None, informes_scout=None):
    """
    Versión mejorada del radar chart con sistema híbrido
    """
    try:
        # Cache para evitar búsquedas repetidas
        if not hasattr(st.session_state, 'wyscout_cache'):
            st.session_state.wyscout_cache = {}
        
        cache_key = f"{nombre_jugador}_{equipo_jugador or 'sin_equipo'}"
        
        print(f"🎯 Generando radar híbrido para {nombre_jugador}")

        jugador_wyscout = None
        usar_datos_wyscout = False
        fuente = "Evaluación Scout"
        grupo_posicion = "general"
        
        # === PROCESAR DATOS WYSCOUT ===
        if datos_wyscout is not None:
            print("📊 Procesando datos Wyscout...")
            
            # Convertir a diccionario si es necesario
            if isinstance(datos_wyscout, pd.Series):
                jugador_wyscout = datos_wyscout.to_dict()
            elif isinstance(datos_wyscout, dict):
                jugador_wyscout = datos_wyscout
            else:
                jugador_wyscout = None
            
            if jugador_wyscout:
                # Determinar grupo de posición
                pos_principal = jugador_wyscout.get('pos_principal', '')
                if pos_principal:
                    grupo_posicion = determinar_grupo_posicion_wyscout(pos_principal)
                    print(f"📍 Posición detectada: {pos_principal} → Grupo: {grupo_posicion}")
                
                # Obtener parámetros disponibles
                params_disponibles, etiquetas = obtener_parametros_radar_wyscout(
                    grupo_posicion, 
                    jugador_wyscout, 
                    mapping_wyscout
                )
                
                if len(params_disponibles) >= 4:  # Mínimo 4 métricas
                    print(f"✅ Métricas Wyscout disponibles: {len(params_disponibles)}")
                    
                    # Calcular percentiles
                    valores_jugador = calcular_percentiles_con_datos_reales(
                        jugador_wyscout, 
                        params_disponibles, 
                        grupo_posicion
                    )
                    
                    # Configurar para radar
                    params = etiquetas
                    min_range = [0] * len(params)
                    max_range = [100] * len(params)  # Percentiles van de 0 a 100
                    usar_percentiles = True
                    usar_datos_wyscout = True
                    fuente = "Datos Wyscout"
                else:
                    print(f"⚠️ Solo {len(params_disponibles)} métricas Wyscout, usando scout")
                    usar_datos_wyscout = False
        
        # === SI NO HAY WYSCOUT O NO SUFICIENTES DATOS, USAR SCOUT ===
        if not usar_datos_wyscout and informes_scout:
            print("📊 Usando evaluaciones del scout...")
            datos_reales = crear_datos_desde_evaluaciones_mejorado(informes_scout)
            
            if datos_reales and 'etiquetas' in datos_reales:
                params = datos_reales['etiquetas']
                valores_jugador = datos_reales['valores']
                min_range = [0] * len(params)
                max_range = [10] * len(params)
                usar_percentiles = False
                
                # Información del modo en la fuente
                num_eval = datos_reales.get('_num_evaluaciones', len(informes_scout))
                num_video = datos_reales.get('_num_video_completo', 0)
                modo = datos_reales.get('modo', 'basico')
                
                if modo == 'especifico':
                    fuente = f"Análisis detallado ({num_eval} eval, {num_video} video)"
                elif modo == 'hibrido':
                    fuente = f"Análisis mixto ({num_eval} eval: {num_video} video, {num_eval-num_video} campo)"
                else:
                    fuente = f"Evaluación campo ({num_eval} observaciones)"
            else:
                # Fallback al sistema original
                params = ['Técnica', 'Táctica', 'Físico', 'Mental', 'Finalización', 'Creatividad', 'Trabajo Def.', 'Liderazgo']
                min_range = [0] * 8
                max_range = [10] * 8
                valores_jugador = [5] * 8
                usar_percentiles = False
                fuente = "Evaluación Scout (datos limitados)"
        
        # === SI NO HAY NADA, VALORES POR DEFECTO ===
        if 'params' not in locals():
            print("⚠️ Sin datos suficientes, usando valores por defecto")
            params = ['Técnica', 'Táctica', 'Físico', 'Mental']
            valores_jugador = [5, 5, 5, 5]
            min_range = [0, 0, 0, 0]
            max_range = [10, 10, 10, 10]
            usar_percentiles = False
            fuente = "Sin datos"
        
        # === CREAR RADAR (código de visualización permanece igual) ===
        print(f"📊 Creando radar con {len(params)} parámetros")
        
        radar = Radar(
            params, 
            min_range, 
            max_range,
            round_int=[True] * len(params) if usar_percentiles else [False] * len(params),
            num_rings=4,
            ring_width=1, 
            center_circle_radius=1
        )
        
        # Setup axis
        fig, ax = radar.setup_axis()
        fig.set_size_inches(10, 8)
        
        # Colores según fuente
        if usar_datos_wyscout:
            color_principal = '#1e3a8a'
            color_secundario = '#3b82f6'
            titulo_adicional = f"Percentiles Liga - {grupo_posicion.replace('_', ' ').title()}"
        else:
            color_principal = '#059669'
            color_secundario = '#10b981'
            titulo_adicional = "Evaluación Scout"
        
        # Dibujar radar
        rings_inner = radar.draw_circles(ax=ax, facecolor='#f8fafc', edgecolor='#e2e8f0')
        
        radar_output = radar.draw_radar(
            valores_jugador, 
            ax=ax,
            kwargs_radar={
                'facecolor': color_principal, 
                'alpha': 0.3,
                'edgecolor': color_secundario,
                'linewidth': 2
            },
            kwargs_rings={'facecolor': color_secundario, 'alpha': 0.1}
        )
        
        radar_poly, rings_outer, vertices = radar_output
        
        # Puntos en vértices
        ax.scatter(vertices[:, 0], vertices[:, 1], 
                  c='#ef4444', s=50, zorder=5, 
                  edgecolors='white', linewidth=2)
        
        # Etiquetas
        radar.draw_range_labels(ax=ax, fontsize=9)
        radar.draw_param_labels(ax=ax, fontsize=10)
        
        # Título
        fig.suptitle(f'{nombre_jugador} - {titulo_adicional}', 
                    fontsize=14, color=color_principal, 
                    fontweight='bold', y=0.98)
        
        # Subtítulo
        plt.figtext(0.5, 0.94, f'Fuente: {fuente}', 
                   ha='center', fontsize=10, color='#64748b')
        
        # Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_path = tmp_file.name
        
        plt.savefig(tmp_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Radar híbrido generado exitosamente")
        return tmp_path
        
    except Exception as e:
        print(f"❌ Error generando radar: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def crear_radar_chart_jugador(datos_wyscout, nombre_jugador, equipo_jugador=None, informes_scout=None):
    """
    Versión mejorada del radar chart con sistema híbrido
    ACTUALIZADO: Siempre intenta usar el radar mejorado, incluso con 1 informe
    """
    try:
        # Cache para evitar búsquedas repetidas
        if not hasattr(st.session_state, 'wyscout_cache'):
            st.session_state.wyscout_cache = {}
        
        cache_key = f"{nombre_jugador}_{equipo_jugador or 'sin_equipo'}"
        
        print(f"🎯 Generando radar para {nombre_jugador}")

        jugador_wyscout = None
        usar_datos_wyscout = False
        fuente = "Evaluación Scout"
        grupo_posicion = "general"
        
        # === PROCESAR DATOS WYSCOUT ===
        if datos_wyscout is not None and not datos_wyscout.get('es_besoccer', False):
            print("📊 Procesando datos Wyscout reales...")
            
            # Convertir a diccionario si es necesario
            if isinstance(datos_wyscout, pd.Series):
                jugador_wyscout = datos_wyscout.to_dict()
            elif isinstance(datos_wyscout, dict):
                jugador_wyscout = datos_wyscout
            else:
                jugador_wyscout = None
            
            if jugador_wyscout and not jugador_wyscout.get('es_besoccer', False):
                # Determinar grupo de posición
                pos_principal = jugador_wyscout.get('pos_principal', '')
                if pos_principal:
                    grupo_posicion = determinar_grupo_posicion_wyscout(pos_principal)
                    print(f"📍 Posición detectada: {pos_principal} → Grupo: {grupo_posicion}")
                
                # Obtener parámetros disponibles
                params_disponibles, etiquetas = obtener_parametros_radar_wyscout(
                    grupo_posicion, 
                    jugador_wyscout, 
                    mapping_wyscout
                )
                
                if len(params_disponibles) >= 4:  # Mínimo 4 métricas
                    print(f"✅ Métricas Wyscout disponibles: {len(params_disponibles)}")
                    
                    # Calcular percentiles
                    valores_jugador = calcular_percentiles_con_datos_reales(
                        jugador_wyscout, 
                        params_disponibles, 
                        grupo_posicion
                    )
                    
                    # Configurar para radar
                    params = etiquetas
                    min_range = [0] * len(params)
                    max_range = [100] * len(params)  # Percentiles van de 0 a 100
                    usar_percentiles = True
                    usar_datos_wyscout = True
                    fuente = "Datos Wyscout"
                else:
                    print(f"⚠️ Solo {len(params_disponibles)} métricas Wyscout, usando scout")
                    usar_datos_wyscout = False
        
        # === SI NO HAY WYSCOUT O NO SUFICIENTES DATOS, USAR SCOUT ===
        if not usar_datos_wyscout and informes_scout:
            print("📊 Usando evaluaciones del scout...")
            
            # CAMBIO CLAVE: Convertir a lista si es necesario
            if isinstance(informes_scout, dict):
                informes_para_radar = [informes_scout]
            elif isinstance(informes_scout, list):
                informes_para_radar = informes_scout
            else:
                informes_para_radar = [informes_scout] if informes_scout else []
            
            # SIEMPRE intentar el radar mejorado primero
            if len(informes_para_radar) >= 1:
                print(f"📊 Intentando radar mejorado con {len(informes_para_radar)} informe(s)")
                
                # Usar el sistema mejorado
                datos_reales = crear_datos_desde_evaluaciones_mejorado(informes_para_radar)
                
                if datos_reales and 'etiquetas' in datos_reales:
                    params = datos_reales['etiquetas']
                    valores_jugador = datos_reales['valores']
                    min_range = [0] * len(params)
                    max_range = [10] * len(params)
                    usar_percentiles = False
                    
                    # Información del modo en la fuente
                    num_eval = datos_reales.get('_num_evaluaciones', len(informes_para_radar))
                    num_video = datos_reales.get('_num_video_completo', 0)
                    modo = datos_reales.get('modo', 'basico')
                    
                    if modo == 'especifico':
                        fuente = f"Análisis detallado ({num_eval} eval, {num_video} video)"
                    elif modo == 'hibrido':
                        fuente = f"Análisis mixto ({num_eval} eval: {num_video} video, {num_eval-num_video} campo)"
                    else:
                        fuente = f"Evaluación scout ({num_eval} observaciones)"
                        
                    print(f"✅ Radar mejorado generado: {len(params)} parámetros, modo: {modo}")
                else:
                    print("⚠️ No se pudo generar radar mejorado, usando fallback")
                    # Solo si falla completamente, usar el simple
                    params = ['Técnica', 'Táctica', 'Físico', 'Mental']
                    valores_jugador = [5, 5, 5, 5]
                    min_range = [0, 0, 0, 0]
                    max_range = [10, 10, 10, 10]
                    usar_percentiles = False
                    fuente = "Evaluación Scout (básica)"
        
        # === SI NO HAY NADA, VALORES POR DEFECTO ===
        if 'params' not in locals():
            print("⚠️ Sin datos suficientes, usando valores por defecto")
            params = ['Técnica', 'Táctica', 'Físico', 'Mental']
            valores_jugador = [5, 5, 5, 5]
            min_range = [0, 0, 0, 0]
            max_range = [10, 10, 10, 10]
            usar_percentiles = False
            fuente = "Sin datos"
        
        # === CREAR RADAR (código de visualización permanece igual) ===
        print(f"📊 Creando radar con {len(params)} parámetros")
        
        radar = Radar(
            params, 
            min_range, 
            max_range,
            round_int=[True] * len(params) if usar_percentiles else [False] * len(params),
            num_rings=4,
            ring_width=1, 
            center_circle_radius=1
        )
        
        # Setup axis
        fig, ax = radar.setup_axis()
        fig.set_size_inches(10, 8)
        
        # Colores según fuente
        if usar_datos_wyscout:
            color_principal = '#1e3a8a'
            color_secundario = '#3b82f6'
            titulo_adicional = f"Percentiles Liga - {grupo_posicion.replace('_', ' ').title()}"
        else:
            color_principal = '#059669'
            color_secundario = '#10b981'
            titulo_adicional = "Evaluación Scout"
        
        # Dibujar radar
        rings_inner = radar.draw_circles(ax=ax, facecolor='#f8fafc', edgecolor='#e2e8f0')
        
        radar_output = radar.draw_radar(
            valores_jugador, 
            ax=ax,
            kwargs_radar={
                'facecolor': color_principal, 
                'alpha': 0.3,
                'edgecolor': color_secundario,
                'linewidth': 2
            },
            kwargs_rings={'facecolor': color_secundario, 'alpha': 0.1}
        )
        
        radar_poly, rings_outer, vertices = radar_output
        
        # Puntos en vértices
        ax.scatter(vertices[:, 0], vertices[:, 1], 
                  c='#ef4444', s=50, zorder=5, 
                  edgecolors='white', linewidth=2)
        
        # Etiquetas
        radar.draw_range_labels(ax=ax, fontsize=9)
        radar.draw_param_labels(ax=ax, fontsize=10)
        
        # Título
        fig.suptitle(f'{nombre_jugador} - {titulo_adicional}', 
                    fontsize=14, color=color_principal, 
                    fontweight='bold', y=0.98)
        
        # Subtítulo
        plt.figtext(0.5, 0.94, f'Fuente: {fuente}', 
                   ha='center', fontsize=10, color='#64748b')
        
        # Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_path = tmp_file.name
        
        plt.savefig(tmp_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Radar generado exitosamente")
        return tmp_path
        
    except Exception as e:
        print(f"❌ Error generando radar: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
def crear_radar_chart_scout_individual(informe_data):
    """
    Crea un radar chart basado en las métricas del informe individual.
    Versión mejorada que maneja diferentes estructuras.
    """
    try:
        # Usar la función mejorada para obtener métricas
        metricas_data = obtener_metricas_para_pdf(informe_data)
        
        # Usar los promedios calculados
        params = ['Técnico', 'Táctico', 'Físico', 'Mental']
        values = [
            metricas_data['promedios']['tecnicos'],
            metricas_data['promedios']['tacticos'],
            metricas_data['promedios']['fisicos'],
            metricas_data['promedios']['mentales']
        ]
        
        print(f"✅ Valores para radar: {values}")

        # Crear radar chart
        N = len(params)
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
        values_plot = values + values[:1]
        angles += angles[:1]

        fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(polar=True))
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)

        # Configuración
        ax.set_ylim(0, 10)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(params, size=11)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(['2', '4', '6', '8', '10'], size=9)
        ax.grid(True, linestyle='--', alpha=0.6)

        # Dibujar
        ax.plot(angles, values_plot, 'o-', linewidth=2, color='#007bff')
        ax.fill(angles, values_plot, alpha=0.3, color='#007bff')

        # Valores en puntos
        for angle, value in zip(angles[:-1], values):
            ax.text(angle, value + 0.3, f'{value:.1f}', 
                   ha='center', va='center', fontsize=9, weight='bold')

        plt.title('Evaluación del Jugador', size=14, weight='bold', pad=20)

        # Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_path = tmp_file.name
        plt.savefig(tmp_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close(fig)

        return tmp_path

    except Exception as e:
        print(f"❌ Error creando radar chart: {e}")
        return None

def crear_datos_desde_evaluaciones_mejorado(informes_list):
    """
    Crea datos para el radar a partir de evaluaciones del scout
    VERSIÓN MEJORADA: Incluye fallback a BeSoccer para posición
    """
    if not informes_list:
        return None
    
    # Si recibimos un solo informe como dict, convertirlo a lista
    if isinstance(informes_list, dict):
        informes_list = [informes_list]
    
    print(f"📊 Procesando {len(informes_list)} informes para radar híbrido...")
    
    # Analizar tipos de evaluaciones
    num_campo = sum(1 for i in informes_list if i.get('tipo_evaluacion') != 'video_completo')
    num_video = sum(1 for i in informes_list if i.get('tipo_evaluacion') == 'video_completo')
    total_evaluaciones = len(informes_list)
    
    # Determinar el modo del radar
    porcentaje_video = (num_video / total_evaluaciones) * 100 if total_evaluaciones > 0 else 0
    
    print(f"📊 Evaluaciones: {num_campo} campo, {num_video} video ({porcentaje_video:.0f}% video)")
    
    # Obtener el informe más reciente y la posición
    informes_ordenados = sorted(informes_list, 
                               key=lambda x: x.get('fecha_creacion', ''), 
                               reverse=True)
    
    # MEJORADO: Búsqueda de posición con múltiples fallbacks
    posicion = None
    
    # 1. Buscar en los informes
    for informe in informes_ordenados:
        pos_temp = informe.get('posicion') or informe.get('posicion_evaluada') or informe.get('posicion_real')
        if pos_temp and pos_temp not in ['N/A', 'None', '', None]:
            posicion = pos_temp
            print(f"📍 Posición encontrada en informe: {posicion}")
            break
    
    # 2. Si no se encontró, buscar en BeSoccer
    if not posicion or posicion in ['N/A', 'None', '', None]:
        print("🔍 Posición no encontrada en informes, buscando en BeSoccer...")
        
        # Buscar URL de BeSoccer
        url_besoccer = None
        nombre_jugador = None
        for informe in informes_ordenados:
            if informe.get('url_besoccer'):
                url_besoccer = informe['url_besoccer']
                nombre_jugador = informe.get('jugador_nombre', '')
                break
        
        if url_besoccer:
            try:
                # Verificar cache primero
                cache_key = f"besoccer_pos_{url_besoccer}"
                if hasattr(st.session_state, 'besoccer_cache') and cache_key in st.session_state.besoccer_cache:
                    datos_besoccer = st.session_state.besoccer_cache[cache_key]
                    print("✅ Datos de BeSoccer obtenidos de cache")
                else:
                    from utils.besoccer_scraper import BeSoccerScraper
                    scraper = BeSoccerScraper()
                    datos_besoccer = scraper.obtener_datos_perfil_jugador(url_besoccer)
                    
                    # Guardar en cache
                    if not hasattr(st.session_state, 'besoccer_cache'):
                        st.session_state.besoccer_cache = {}
                    st.session_state.besoccer_cache[cache_key] = datos_besoccer
                
                if datos_besoccer:
                    pos_principal = datos_besoccer.get('posicion_principal')
                    pos_secundaria = datos_besoccer.get('posicion_secundaria')
                    
                    if pos_principal and pos_principal not in ['N/A', 'None', '', None]:
                        posicion = pos_principal
                        print(f"✅ Posición principal de BeSoccer: {posicion}")
                    elif pos_secundaria and pos_secundaria not in ['N/A', 'None', '', None]:
                        posicion = pos_secundaria
                        print(f"✅ Posición secundaria de BeSoccer: {posicion}")
                        
            except Exception as e:
                print(f"⚠️ Error obteniendo posición de BeSoccer: {e}")
    
    # 3. Si aún no hay posición, inferir por métricas
    if not posicion or posicion in ['N/A', 'None', '', None]:
        posicion_inferida = inferir_posicion_por_metricas(informes_ordenados)
        if posicion_inferida:
            posicion = posicion_inferida
            print(f"🎯 Posición inferida por métricas evaluadas: {posicion}")
        else:
            posicion = 'Mediocentro'
            print(f"⚠️ Sin posición definida, usando por defecto: {posicion}")
    
    # Decidir qué tipo de radar crear
    if porcentaje_video >= 70:
        print("🎥 Modo: Métricas específicas (mayoría video)")
        datos = crear_radar_metricas_especificas(informes_ordenados, posicion)
    elif porcentaje_video <= 30:
        print("⚽ Modo: Categorías + métricas básicas (mayoría campo)")
        datos = crear_radar_categorias_basicas(informes_ordenados, posicion)
    else:
        print("🔄 Modo: Híbrido (mezcla de evaluaciones)")
        datos = crear_radar_hibrido(informes_ordenados, posicion, num_campo, num_video)
    
    # Añadir metadatos
    if datos:
        datos['_num_evaluaciones'] = len(informes_list)
        datos['_num_video_completo'] = num_video
        datos['posicion'] = posicion
    
    return datos
    
def limpiar_texto_para_pdf(texto):
    """
    Limpia el texto de caracteres problemáticos para FPDF
    """
    if not isinstance(texto, str):
        return str(texto)
    
    # Diccionario de reemplazos
    reemplazos = {
        '€': 'EUR',
        '£': 'GBP',
        '$': 'USD',
        '📗': '[FICHAR]',
        '📘': '[SEGUIR]',
        '📙': '[ESPERAR]',
        '📕': '[DESCARTAR]',
        '✅': '[OK]',
        '❌': '[X]',
        '📊': '[STATS]',
        '🎯': '[TARGET]',
        '⚽': '[FUTBOL]',
        '🏟️': '[ESTADIO]',
        '👤': '[JUGADOR]',
        '📝': '[NOTA]',
        '⭐': '[STAR]',
        '💼': '[TRABAJO]',
        '🔍': '[BUSCAR]',
        '📋': '[INFORME]',
        '—': '-',
        '–': '-',
        '"': '"',
        '"': '"',
        ''': "'",
        ''': "'",
        '…': '...',
        '•': '-',
        '→': '->',
        '←': '<-',
        '↑': '^',
        '↓': 'v',
        '°': 'o',
        '±': '+/-',
        '×': 'x',
        '÷': '/',
        '≈': '~',
        '≤': '<=',
        '≥': '>=',
        '≠': '!=', 
        '↗': 'MEJORA',
        '↘': 'BAJA',
        '→': 'ESTABLE'

    }
    
    # Aplicar reemplazos
    texto_limpio = texto
    for char_original, char_reemplazo in reemplazos.items():
        texto_limpio = texto_limpio.replace(char_original, char_reemplazo)
    
    # Eliminar otros caracteres Unicode problemáticos
    texto_limpio = ''.join(char for char in texto_limpio if ord(char) < 256)
    
    return texto_limpio

def limpiar_texto_ia(texto):
    """Elimina asteriscos y formato markdown"""
    if not texto:
        return ""
    texto = texto.replace('**', '')
    texto = texto.replace('*', '')
    texto = texto.replace('###', '')
    texto = texto.replace('##', '')
    texto = texto.replace('#', '')
    return texto.strip()

def transformar_url_foto_para_pdf(url_original):
    if url_original is None:
        return None
    
    if "cdn.resfu.com" in url_original:
        # Reemplazar cualquier tamaño
        url_grande = re.sub(r"size=\d+x", "size=500x", url_original)
        url_grande = url_grande.replace("lossy=1", "lossy=0")

        # Si no había size
        if "size=" not in url_grande:
            url_grande += "?size=500x&lossy=0"
        
        return url_grande
    
    return url_original

def agregar_analisis_ia_mejorado(pdf, todos_informes_jugador, y_inicial=None):
    """
    Añade síntesis de observaciones del scout al PDF
    """
    if y_inicial:
        pdf.set_y(y_inicial)
    
    # Título sección
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(36, 40, 42)
    pdf.cell(0, 10, 'SINTESIS DE OBSERVACIONES', 0, 1, 'C')
    
    # Línea decorativa
    pdf.set_fill_color(0, 123, 191)
    pdf.rect(40, pdf.get_y(), 130, 1, 'F')
    pdf.ln(8)
    
    try:
        from utils.resumen_scouting_ia import ResumenScoutingIA
        ia_scout = ResumenScoutingIA()
        
        if ia_scout.verificar_conexion():
            # Indicador de número de informes
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 5, f'Analisis basado en {len(todos_informes_jugador)} evaluaciones del scout', 0, 1, 'C')
            pdf.ln(5)
            
            # 1. PATRONES OBSERVADOS
            patrones = ia_scout.generar_resumen_observaciones(
                todos_informes_jugador, 
                tipo_resumen="patron_observaciones"
            )
            
            if 'patron_observaciones' in patrones and patrones['patron_observaciones']:
                # Título consistente (sin números de palabras)
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(0, 123, 191)
                pdf.cell(0, 6, 'Patrones y Evolucion Observada', 0, 1)
                pdf.ln(2)
                
                # Texto
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(60, 60, 60)
                texto_patrones = limpiar_texto_para_pdf(patrones['patron_observaciones'])
                pdf.multi_cell(0, 5, texto_patrones, 0, 'J')
                pdf.ln(8)
            
            # 2. SÍNTESIS EJECUTIVA
            sintesis = ia_scout.generar_resumen_observaciones(
                todos_informes_jugador, 
                tipo_resumen="sintesis_ejecutiva"
            )
            
            if 'sintesis_ejecutiva' in sintesis and sintesis['sintesis_ejecutiva']:
                # Título consistente
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(0, 123, 191)
                pdf.cell(0, 6, 'Resumen Ejecutivo', 0, 1)
                pdf.ln(2)
                
                # Texto (sin caja gris)
                pdf.set_font('Helvetica', '', 10)
                pdf.set_text_color(60, 60, 60)
                texto_sintesis = limpiar_texto_para_pdf(sintesis['sintesis_ejecutiva'])
                pdf.multi_cell(0, 5, texto_sintesis, 0, 'J')
                pdf.ln(5)
            
            # Nota al pie sobre el análisis
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(150, 150, 150)
            pdf.cell(0, 5, '* Sintesis generada a partir de las observaciones textuales del scout', 0, 1, 'C')
                
    except Exception as e:
        print(f"Error en sintesis IA: {e}")
        
        # Fallback manual si falla la IA
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, 'Revise las observaciones individuales en cada informe para el analisis detallado.', 0, 'J')

def generar_pdf_profesional(informe_data, datos_wyscout=None, user_info=None, todos_informes_jugador=None):
    """
    Genera un PDF profesional compacto v3 - Compatible con estructura JSON
    """
    try:
        print("\n=== DEBUG PDF GENERATION ===")
        print(f"1. Jugador: {informe_data.get('jugador_nombre')}")
        print(f"2. Tiene datos Wyscout: {datos_wyscout is not None}")
        print(f"3. Número de informes totales: {len(todos_informes_jugador) if todos_informes_jugador else 0}")
        
        # Verificar estructura de métricas
        metricas_json = informe_data.get('metricas', {})
        if isinstance(metricas_json, str):
            try:
                metricas_json = json.loads(metricas_json)
                print(f"4. Métricas parseadas - Tipo: {metricas_json.get('tipo', 'N/A')}")
                print(f"5. Tiene promedios: {'promedios' in metricas_json}")
                print(f"6. Tiene evaluaciones: {'evaluaciones' in metricas_json}")
                print(f"7. Tiene categorías: {'categorias' in metricas_json}")
            except:
                print("4. ERROR parseando métricas")
                metricas_json = {}
        print("========================\n")
        # Cache para evitar búsquedas repetidas
        if not hasattr(st.session_state, 'wyscout_cache'):
            st.session_state.wyscout_cache = {}
        
        jugador_nombre = informe_data['jugador_nombre']
        equipo = informe_data['equipo']
        cache_key = f"{jugador_nombre}_{equipo}"
        
        print(f"📄 Generando PDF profesional para {jugador_nombre}...")
        
        # Preparar datos básicos (sin cambios)
        scout_nombre = limpiar_texto_para_pdf(user_info['nombre'] if user_info else 'Scout')
        jugador_nombre = limpiar_texto_para_pdf(informe_data['jugador_nombre'])
        equipo = limpiar_texto_para_pdf(informe_data['equipo'])
        posicion = limpiar_texto_para_pdf(informe_data.get('posicion', 'N/A'))    
        potencial = limpiar_texto_para_pdf(informe_data.get('potencial', 'N/A'))
        nota = limpiar_texto_para_pdf(informe_data.get('nota_general', 'N/A'))

        # Buscar datos en Wyscout si no vienen proporcionados
        if datos_wyscout is None or (isinstance(datos_wyscout, dict) and not datos_wyscout):
            # Primero verificar cache
            if cache_key in st.session_state.wyscout_cache:
                datos_wyscout = st.session_state.wyscout_cache[cache_key]
                print(f"✅ Datos Wyscout obtenidos de cache para {jugador_nombre}")
            else:
                print(f"🔍 Buscando en Wyscout para {jugador_nombre}...")
                
                try:
                    from utils.wyscout_data_extractor_personalizado import WyscoutExtractorPersonalizado
                    extractor = WyscoutExtractorPersonalizado()
                    
                    # Solo buscar con el nombre del informe
                    resultado = extractor.buscar_jugador_mejorado(jugador_nombre, equipo, umbral_minimo=0.75)
                    
                    if resultado is not None:
                        datos_wyscout = resultado
                        # Guardar en cache
                        st.session_state.wyscout_cache[cache_key] = datos_wyscout
                        print(f"✅ Datos encontrados y guardados en cache")
                        if isinstance(datos_wyscout, pd.Series):
                            datos_wyscout = datos_wyscout.to_dict()
                    else:
                        # Guardar None en cache para no buscar de nuevo
                        st.session_state.wyscout_cache[cache_key] = None
                        print(f"ℹ️ Sin datos Wyscout para {jugador_nombre}")
                        
                except Exception as e:
                    print(f"⚠️ Error buscando en Wyscout: {e}")

            # Si no encontramos datos en Wyscout, usar datos de BeSoccer como fallback
            if (datos_wyscout is None or not datos_wyscout) and 'url_besoccer' in informe_data:
                print(f"🔍 Sin datos Wyscout, usando datos de BeSoccer como fallback...")
                try:
                    # Verificar si ya tenemos los datos de BeSoccer del intento anterior
                    if 'datos_besoccer' in locals() and datos_besoccer:
                        print(f"✅ Reutilizando datos de BeSoccer ya obtenidos")
                    else:
                        from utils.besoccer_scraper import BeSoccerScraper
                        scraper = BeSoccerScraper()
                        datos_besoccer = scraper.obtener_datos_perfil_jugador(informe_data['url_besoccer'])
                    
                    if datos_besoccer:
                        # Mapear datos de BeSoccer al formato esperado
                        datos_wyscout = {
                            'edad': datos_besoccer.get('edad'),
                            'altura': datos_besoccer.get('altura'),
                            'peso': datos_besoccer.get('peso'),
                            'país_de_nacimiento': datos_besoccer.get('nacionalidad'),
                            'valor_de_mercado_(transfermarkt)': datos_besoccer.get('valor_mercado'),
                            'min': None,  # No disponible en BeSoccer
                            'partidos_jugados': None,  # No disponible en BeSoccer
                            'pos_principal': datos_besoccer.get('posicion_principal'),
                            'fuente': 'BeSoccer',
                            'es_besoccer': True,
                            'nombre_real': datos_besoccer.get('nombre_completo')  # Guardar para referencia
                        }
                        print(f"✅ Datos obtenidos de BeSoccer (fallback)")
                except Exception as e:
                    print(f"⚠️ Error obteniendo datos de BeSoccer: {e}")

        def extraer(d, col, default=''):
            """Extrae valor o retorna vacío para no mostrar N/A"""
            if d is not None:
                valor = None
                
                if hasattr(d, 'get') and hasattr(d, 'index'):
                    if col in d.index:
                        valor = d[col]
                elif isinstance(d, dict) and col in d:
                    valor = d[col]
                
                if valor is not None and pd.notna(valor):
                    valor_str = str(valor).strip()
                    if valor_str not in ['', 'N/A', 'nan', 'None', 'NaN']:
                        return valor_str
            
            return default
        
        # En la generación de PDF, usar verificación segura:
        if 'jugador_bd_id' in informe_data and informe_data.get('jugador_bd_id'):
            try:
                jugador_bd_id = informe_data['jugador_bd_id']
                if pd.notna(jugador_bd_id) and jugador_bd_id > 0:
                    jugador_bd = jugador_model.obtener_jugador_por_id(jugador_bd_id)
                    if jugador_bd:
                        datos_wyscout = jugador_bd
            except Exception as e:
                print(f"⚠️ No se pudo obtener datos de BD: {e}")

        # Extraer datos con los nombres correctos del Excel
        edad = extraer(datos_wyscout, 'edad')
        nacionalidad = extraer(datos_wyscout, 'país_de_nacimiento')
        minutos = extraer(datos_wyscout, 'min')
        valor = extraer(datos_wyscout, 'valor_de_mercado_(transfermarkt)')
        altura = extraer(datos_wyscout, 'altura')
        peso = extraer(datos_wyscout, 'peso')
        partidos = extraer(datos_wyscout, 'partidos_jugados')
        pos_principal = extraer(datos_wyscout, 'pos_principal')
        
        if pos_principal:
            posicion = pos_principal
        
        # Ruta del logo
        logo_path = os.path.join('C:\\Users\\manue\\OneDrive\\Escritorio\\WebScouting\\assets\\images\\identidad_MPR_1.png')
        
        # === CREAR PDF ===
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # ==================== PÁGINA 1: PRESENTACIÓN + RADAR ====================
        pdf.add_page()
        
        # Logo en esquina superior derecha
        if logo_path and os.path.exists(logo_path):
            try:
                pdf.image(logo_path, x=185, y=10, w=18)
            except:
                pass
        
        # Header compacto
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 15, 'INFORME DE SCOUTING', 0, 1, 'C')
        
        # Línea decorativa
        pdf.set_draw_color(220, 220, 220)
        pdf.set_line_width(0.4)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(8)
        
        # === SECCIÓN SUPERIOR: FOTO + DATOS ===
        y_top = pdf.get_y() + 5
        x_foto = 25
        ancho_foto = 48
        foto_mostrada = False
        
        # Transformar URL si es de BeSoccer
        url_foto_pdf = transformar_url_foto_para_pdf(informe_data.get('imagen_url'))

        if url_foto_pdf:
            try:
                response = requests.get(url_foto_pdf, timeout=5)
                if response.status_code == 200:
                    img = Image.open(BytesIO(response.content))

                    # Convertir a cuadrada si hace falta
                    ancho, alto = img.size
                    if ancho != alto:
                        lado = min(ancho, alto)
                        left = (ancho - lado) // 2
                        top = (alto - lado) // 2
                        img = img.crop((left, top, left + lado, top + lado))
                    
                    if img.format == "PNG":
                        img = img.convert("RGB")
                    
                    fd, temp_path = tempfile.mkstemp(suffix='.jpg')
                    os.close(fd)
                    
                    img.save(temp_path, 'JPEG', quality=95)
                    
                    pdf.image(temp_path, x=x_foto, y=y_top, w=ancho_foto, h=ancho_foto)
                    foto_mostrada = True

                    try:
                        os.unlink(temp_path)
                    except:
                        pass
            except Exception as e:
                print(f"⚠️ Error con foto: {e}")
        
        # Datos del jugador (al lado de la foto)
        x_datos = x_foto + ancho_foto + 10
        y_datos = y_top

        pdf.set_xy(x_datos, y_datos)       
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 9, jugador_nombre, 0, 1)
        
        pdf.set_x(x_datos)
        pdf.set_font('Helvetica', '', 12)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 8, f"{equipo} | {posicion}", ln=1)

        # Información adicional
        linea3_parts = []
        if edad:
            try:
                edad_num = int(float(edad))
                linea3_parts.append(f"{edad_num} años")
            except:
                linea3_parts.append(f"{edad} años")
                
        if nacionalidad:
            linea3_parts.append(nacionalidad)
            
        if altura and peso:
            try:
                altura_num = float(altura)
                peso_num = float(peso)
                if altura_num > 100:
                    linea3_parts.append(f"{int(altura_num)}cm / {int(peso_num)}kg")
                else:
                    linea3_parts.append(f"{altura_num:.2f}m / {int(peso_num)}kg")
            except:
                if altura or peso:
                    linea3_parts.append(f"{altura} / {peso}")
        
        if linea3_parts:
            pdf.set_x(x_datos)
            pdf.cell(0, 8, " | ".join(linea3_parts), ln=1)

        # Estadísticas
        linea4_parts = []
        if partidos:
            try:
                partidos_num = int(float(partidos))
                linea4_parts.append(f"Partidos: {partidos_num}")
            except:
                linea4_parts.append(f"Partidos: {partidos}")
                
        if minutos:
            try:
                minutos_num = int(float(minutos))
                linea4_parts.append(f"Minutos: {minutos_num:,}".replace(',', '.'))
            except:
                linea4_parts.append(f"Minutos: {minutos}")
        
        if linea4_parts:
            pdf.set_x(x_datos)
            pdf.cell(0, 8, " | ".join(linea4_parts), ln=1)

        # Valor de mercado
        if valor:
            pdf.set_x(x_datos)
            pdf.set_font('Helvetica', 'B', 12)
            try:
                valor_limpio = str(valor).upper()
                
                if 'M' in valor_limpio:
                    numero = valor_limpio.split('M')[0].strip()
                    valor_fmt = f"{numero}M EUR"
                elif 'K' in valor_limpio:
                    numero = valor_limpio.split('K')[0].strip()
                    valor_fmt = f"{numero}K EUR"
                else:
                    valor_numerico = valor_limpio.replace('€', '').replace('EUR', '').replace(',', '').replace('.', '').strip()
                    if valor_numerico.isdigit():
                        valor_num = float(valor_numerico)
                        if valor_num >= 1000000:
                            valor_fmt = f"{valor_num/1000000:.1f}M EUR"
                        elif valor_num >= 1000:
                            valor_fmt = f"{int(valor_num/1000)}K EUR"
                        else:
                            valor_fmt = f"{int(valor_num)} EUR"
                    else:
                        valor_fmt = valor_limpio.replace('€', 'EUR')
                
                pdf.cell(0, 8, f"Valor mercado: {valor_fmt}")
            except Exception as e:
                valor_sin_euro = str(valor).replace('€', 'EUR')
                pdf.cell(0, 8, f"Valor mercado: {valor_sin_euro}")
        
        # Ajustar la Y del PDF tras el bloque foto+datos
        altura_bloque = max(ancho_foto, 50)
        pdf.set_y(y_top + altura_bloque + 10)
        
        # === RADAR CHART SECTION ===
        print("🎯 Creando radar chart...")
        
        todos_informes_para_radar = todos_informes_jugador if todos_informes_jugador else [informe_data]

        # PRIORIDAD 1: Datos Wyscout REALES (no BeSoccer)
        if datos_wyscout and not datos_wyscout.get('es_besoccer', False):
            print("📊 Usando datos Wyscout reales para radar")
            radar_path = crear_radar_chart_jugador(
                datos_wyscout=datos_wyscout,
                nombre_jugador=informe_data['jugador_nombre'],
                equipo_jugador=informe_data['equipo'],
                informes_scout=None
            )
        else:
            # PRIORIDAD 2: Siempre usar el sistema mejorado con TODOS los informes
            print(f"📊 Usando evaluaciones del scout ({len(todos_informes_para_radar)} informes)")
            radar_path = crear_radar_chart_jugador(
                datos_wyscout=None,
                nombre_jugador=informe_data['jugador_nombre'],
                equipo_jugador=informe_data['equipo'],
                informes_scout=todos_informes_para_radar  # Siempre pasar la lista completa
            )
        
        # Insertar radar en PDF
        if radar_path and os.path.exists(radar_path):
            ancho_radar = 150
            x_radar = (pdf.w - ancho_radar) / 2
            pdf.image(radar_path, x=x_radar, y=pdf.get_y(), w=ancho_radar)
            pdf.set_y(pdf.get_y() + ancho_radar + 15)
            
            # Limpiar archivo temporal
            try:
                os.unlink(radar_path)
            except:
                pass
        
        # ==================== PÁGINA 2: EVALUACIÓN + ANÁLISIS IA ====================
        pdf.add_page()
        # Logo
        try:
            if os.path.exists(logo_path):
                pdf.image(logo_path, x=175, y=270, w=20)
        except:
            pass
        
        # Header
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 10, 'EVALUACION POR CATEGORIAS', 0, 1, 'C')
        
        pdf.set_fill_color(0, 123, 191)
        pdf.rect(15, 25, 180, 1, 'F')
        pdf.ln(10)
        
        # === BARRAS DE EVALUACIÓN - VERSIÓN JSON ===
        # Extraer métricas del JSON
        metricas_data = obtener_metricas_para_pdf(informe_data)

        # Si metricas es string, parsearlo
        if isinstance(metricas_json, str):
            try:
                metricas_json = json.loads(metricas_json)
                print(f"✅ Métricas parseadas de string")
            except:
                print(f"❌ Error parseando métricas")
                metricas_json = {}

        # Determinar los promedios
        categorias_promedios = []

        # Primero intentar desde el informe procesado
        tiene_promedios_directos = all(
            f'promedio_{cat}' in informe_data and informe_data[f'promedio_{cat}'] > 0
            for cat in ['tecnico', 'tactico', 'fisico', 'mental']
        )

        if tiene_promedios_directos:
            categorias_promedios = [
            ('TECNICO', metricas_data['promedios']['tecnicos']),
            ('TACTICO', metricas_data['promedios']['tacticos']),
            ('FISICO', metricas_data['promedios']['fisicos']),
            ('MENTAL', metricas_data['promedios']['mentales'])
        ]
            print(f"📊 Promedios para barras PDF: {categorias_promedios}")

        # Si no, intentar desde el JSON
        elif isinstance(metricas_json, dict):
            if 'promedios' in metricas_json:
                categorias_promedios = [
                    ('TECNICO', float(metricas_json['promedios'].get('tecnicos', 0))),
                    ('TACTICO', float(metricas_json['promedios'].get('tacticos', 0))),
                    ('FISICO', float(metricas_json['promedios'].get('fisicos', 0))),
                    ('MENTAL', float(metricas_json['promedios'].get('mentales', 0)))
                ]
                print(f"✅ Usando promedios del JSON")
            elif 'categorias' in metricas_json:
                # Calcular desde las categorías
                for cat_key, cat_nombre in [('tecnicos', 'TECNICO'), ('tacticos', 'TACTICO'), 
                                            ('fisicos', 'FISICO'), ('mentales', 'MENTAL')]:
                    if cat_key in metricas_json['categorias']:
                        valores = [float(v) for v in metricas_json['categorias'][cat_key].values() if v > 0]
                        promedio = sum(valores) / len(valores) if valores else 0
                    else:
                        promedio = 0
                    categorias_promedios.append((cat_nombre, promedio))
                print(f"✅ Calculado desde categorías del JSON")

        # Si aún no tenemos datos válidos, usar la nota general como base
        if not categorias_promedios or all(prom == 0 for _, prom in categorias_promedios):
            nota_general = float(informe_data.get('nota_general', 7.5))
            # Para Media Punta, distribuir según perfil típico
            categorias_promedios = [
                ('TECNICO', nota_general + 0.3),  # Media puntas suelen ser técnicos
                ('TACTICO', nota_general + 0.5),  # Y muy tácticos
                ('FISICO', nota_general - 0.5),  # Menos físicos
                ('MENTAL', nota_general)          # Mental promedio
            ]
            # Asegurar que estén en rango 0-10
            categorias_promedios = [(cat, max(0, min(10, prom))) for cat, prom in categorias_promedios]
            print(f"✅ Usando valores basados en nota general: {nota_general}")

        print(f"📊 Promedios finales para PDF: {categorias_promedios}")

        # Dibujar barras
        for i, (categoria, promedio) in enumerate(categorias_promedios):
            # Asegurar que promedio es un número válido
            try:
                promedio = float(promedio) if promedio else 0
            except:
                promedio = 0
            
            # Fondo alternado
            if i % 2 == 0:
                pdf.set_fill_color(248, 249, 250)
                pdf.rect(15, pdf.get_y() - 1, 180, 10, 'F')
            
            # Color de la barra según el valor
            if promedio >= 8:
                color_barra = (40, 167, 69)  # Verde
            elif promedio >= 6:
                color_barra = (255, 193, 7)  # Amarillo
            else:
                color_barra = (220, 53, 69)  # Rojo
            
            # Categoría
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(36, 40, 42)
            pdf.cell(45, 8, f"{categoria}:", 0, 0)
            
            # Barra de progreso
            if promedio > 0:
                pdf.set_fill_color(*color_barra)
                barra_width = (promedio / 10) * 100
                pdf.rect(65, pdf.get_y() + 1, barra_width, 6, 'F')
            
            # Borde de la barra
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(65, pdf.get_y() + 1, 100, 6, 'D')
            
            # Valor numérico
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(36, 40, 42)
            pdf.set_xy(170, pdf.get_y())
            pdf.cell(25, 8, f"{promedio:.1f}/10", 0, 1, 'R')

        pdf.ln(10)
        
        # === ANÁLISIS TÉCNICO-TÁCTICO (IA) ===
        if todos_informes_jugador and len(todos_informes_jugador) > 0:
            # Verificar espacio disponible
            espacio_necesario = 120  # Estimación del espacio necesario para la sección IA
            if pdf.get_y() + espacio_necesario > 270:
                pdf.add_page()
                # Logo en nueva página
                try:
                    if os.path.exists(logo_path):
                        pdf.image(logo_path, x=175, y=270, w=20)
                except:
                    pass
                pdf.ln(10)
            
            # Llamar a la nueva función de análisis IA
            agregar_analisis_ia_mejorado(pdf, todos_informes_jugador)
            
        else:
            # Si no hay informes, mostrar mensaje
            pdf.ln(10)
            pdf.set_font('Helvetica', 'I', 10)
            pdf.set_text_color(100, 100, 100)
            pdf.cell(0, 10, 'Analisis tecnico-tactico no disponible', 0, 1, 'C')
            pdf.ln(10)

        # === RECOMENDACIÓN FINAL ===
        espacio_para_recomendacion = 40
        espacio_disponible = 270 - pdf.get_y()
        
        if espacio_disponible < espacio_para_recomendacion:
            pdf.add_page()
            try:
                if os.path.exists(logo_path):
                    pdf.image(logo_path, x=175, y=270, w=20)
            except:
                pass
            pdf.set_y(120)
        else:
            pdf.set_y(max(pdf.get_y() + 15, 210))

        # Determinar recomendación
        recomendacion_raw = informe_data.get('recomendacion', 'Sin recomendacion')
        recomendacion = limpiar_texto_para_pdf(recomendacion_raw.replace('_', ' ').title())

        if 'fichar' in recomendacion.lower():
            color_recom = (0, 123, 191)
            mensaje_recom = "RECOMENDACION: FICHAR"
        elif any(word in recomendacion.lower() for word in ['seguir', 'observando']):
            color_recom = (255, 193, 7)
            mensaje_recom = "RECOMENDACION: SEGUIR OBSERVANDO"
        elif 'descartar' in recomendacion.lower():
            color_recom = (220, 53, 69)
            mensaje_recom = "RECOMENDACION: DESCARTAR"
        else:
            color_recom = (36, 40, 42)
            mensaje_recom = f"RECOMENDACION: {recomendacion.upper()}"

        # Caja de recomendación
        pdf.set_fill_color(*color_recom)
        pdf.rect(30, pdf.get_y(), 150, 20, 'F')

        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(30, pdf.get_y() + 5)
        pdf.cell(150, 10, mensaje_recom, 0, 1, 'C')

        # Footer
        pdf.set_y(250)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        pdf.cell(0, 5, f"Scout: {scout_nombre} | {fecha_actual}", 0, 1, 'C')   

        # === GUARDAR PDF ===
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
        
        pdf.output(tmp_path)
        
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        
        os.unlink(tmp_path)
        
        print("✅ PDF v3 (JSON) generado exitosamente")
        return pdf_bytes, "application/pdf", "pdf"
        
    except Exception as e:
        print(f"❌ Error generando PDF v3: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback a HTML
        return generar_html_fallback_mejorado(informe_data, datos_wyscout, user_info)

def generar_html_fallback_mejorado(informe_data, datos_wyscout=None, user_info=None):
    """
    Genera un HTML mejorado como fallback cuando falla el PDF
    """
    scout_nombre = user_info['nombre'] if user_info else 'Scout'
    
    # Calcular promedios por categorías
    categorias = {
        'Técnico': ['control_balon', 'primer_toque', 'pase_corto', 'pase_largo', 'finalizacion', 'regate'],
        'Táctico': ['vision_juego', 'posicionamiento', 'marcaje', 'pressing', 'transiciones'],
        'Físico': ['velocidad', 'resistencia', 'fuerza', 'salto', 'agilidad'],
        'Mental': ['concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision']
    }
    
    promedios = {}
    for categoria, campos in categorias.items():
        valores = [informe_data.get(campo, 0) for campo in campos if campo in informe_data]
        promedios[categoria] = sum(valores) / len(valores) if valores else 0
    
    # Generar HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe de Scouting - {informe_data['jugador_nombre']}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #007bbf 0%, #0056b3 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            .header h1 {{
                margin: 0 0 10px 0;
                font-size: 28px;
            }}
            .header h2 {{
                margin: 0 0 5px 0;
                font-size: 22px;
                font-weight: normal;
            }}
            .header p {{
                margin: 5px 0;
                opacity: 0.9;
            }}
            .info-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .info-item {{
                display: flex;
                justify-content: space-between;
            }}
            .info-label {{
                font-weight: bold;
                color: #007bbf;
            }}
            .section {{
                margin: 30px 0;
            }}
            .section-title {{
                color: #007bbf;
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 15px;
                padding-bottom: 5px;
                border-bottom: 2px solid #007bbf;
            }}
            .category {{
                margin: 15px 0;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 5px;
            }}
            .category-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 10px;
            }}
            .category-name {{
                font-weight: bold;
                font-size: 16px;
            }}
            .category-score {{
                font-weight: bold;
                color: #007bbf;
                font-size: 18px;
            }}
            .progress-bar {{
                width: 100%;
                height: 20px;
                background: #e0e0e0;
                border-radius: 10px;
                overflow: hidden;
            }}
            .progress-fill {{
                height: 100%;
                transition: width 0.3s ease;
            }}
            .progress-high {{ background: #28a745; }}
            .progress-medium {{ background: #ffc107; }}
            .progress-low {{ background: #dc3545; }}
            .observations {{
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                margin: 15px 0;
            }}
            .recommendation {{
                padding: 20px;
                text-align: center;
                font-size: 20px;
                font-weight: bold;
                color: white;
                border-radius: 8px;
                margin: 30px 0;
            }}
            .recommendation-fichar {{ background: #007bbf; }}
            .recommendation-seguir {{ background: #ffc107; }}
            .recommendation-descartar {{ background: #dc3545; }}
            .footer {{
                text-align: center;
                margin-top: 40px;
                padding-top: 20px;
                border-top: 1px solid #e0e0e0;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>INFORME DE SCOUTING PROFESIONAL</h1>
                <h2>{informe_data['jugador_nombre']}</h2>
                <p>{informe_data['equipo']} • {informe_data.get('posicion', 'N/A')}</p>
            </div>
            
            <div class="info-grid">
                <div class="info-item">
                    <span class="info-label">Scout:</span>
                    <span>{scout_nombre}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Fecha:</span>
                    <span>{informe_data.get('fecha_creacion', 'N/A')[:10]}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Nota General:</span>
                    <span>{informe_data.get('nota_general', 0)}/10</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Potencial:</span>
                    <span>{informe_data.get('potencial', 'N/A')}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Tipo Evaluación:</span>
                    <span>{informe_data.get('tipo_evaluacion', 'campo').replace('_', ' ').title()}</span>
                </div>
                <div class="info-item">
                    <span class="info-label">Minutos Observados:</span>
                    <span>{informe_data.get('minutos_observados', 90)}'</span>
                </div>
            </div>
            
            <div class="section">
                <div class="section-title">EVALUACIÓN POR CATEGORÍAS</div>
    """
    
    # Añadir categorías con barras de progreso
    for categoria, promedio in promedios.items():
        color_class = 'progress-high' if promedio >= 7 else 'progress-medium' if promedio >= 5 else 'progress-low'
        porcentaje = (promedio / 10) * 100
        
        html += f"""
                <div class="category">
                    <div class="category-header">
                        <span class="category-name">{categoria.upper()}</span>
                        <span class="category-score">{promedio:.1f}/10</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill {color_class}" style="width: {porcentaje}%"></div>
                    </div>
                </div>
        """
    
    html += f"""
            </div>
            
            <div class="section">
                <div class="section-title">ANÁLISIS CUALITATIVO</div>
                
                <div class="observations">
                    <h3 style="color: #28a745;">FORTALEZAS</h3>
                    <p>{informe_data.get('fortalezas', 'No especificadas')}</p>
                </div>
                
                <div class="observations">
                    <h3 style="color: #dc3545;">ÁREAS DE MEJORA</h3>
                    <p>{informe_data.get('debilidades', 'No especificadas')}</p>
                </div>
                
                <div class="observations">
                    <h3>OBSERVACIONES ADICIONALES</h3>
                    <p>{informe_data.get('observaciones', 'Sin observaciones adicionales')}</p>
                </div>
            </div>
    """
    
    # Recomendación
    recomendacion = informe_data.get('recomendacion', 'seguir_observando')
    if 'fichar' in recomendacion.lower():
        clase_recom = 'recommendation-fichar'
        texto_recom = 'RECOMENDACIÓN: FICHAR'
    elif 'descartar' in recomendacion.lower():
        clase_recom = 'recommendation-descartar'
        texto_recom = 'RECOMENDACIÓN: DESCARTAR'
    else:
        clase_recom = 'recommendation-seguir'
        texto_recom = 'RECOMENDACIÓN: SEGUIR OBSERVANDO'
    
    html += f"""
            <div class="recommendation {clase_recom}">
                {texto_recom}
            </div>
    """
    
    # Datos Wyscout si existen
    if datos_wyscout is not None and not (isinstance(datos_wyscout, pd.Series) and datos_wyscout.empty):
        # Si es una Serie, convertir a diccionario
        if isinstance(datos_wyscout, pd.Series):
            datos_wyscout = datos_wyscout.to_dict()
        
        html += f"""
            <div class="section">
                <div class="section-title">DATOS ESTADÍSTICOS (WYSCOUT)</div>
                <div class="info-grid">
                    <div class="info-item">
                        <span class="info-label">Partidos jugados:</span>
                        <span>{datos_wyscout.get('partidos_jugados', 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Minutos jugados:</span>
                        <span>{datos_wyscout.get('min', 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Goles:</span>
                        <span>{datos_wyscout.get('goles', 'N/A')}</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">Asistencias:</span>
                        <span>{datos_wyscout.get('asistencias', 'N/A')}</span>
                    </div>
                </div>
            </div>
        """
    
    html += f"""
            <div class="footer">
                <p>Sistema de Scouting Profesional</p>
                <p>Informe generado el {datetime.now().strftime("%d/%m/%Y %H:%M")} por {scout_nombre} por {scout_nombre}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html.encode('utf-8'), "text/html", "html"

# ✅ CARGAR INFORMES DEL USUARIO - VERSIÓN OPTIMIZADA
try:
    informes_data = partido_model.obtener_informes_por_usuario(current_user['usuario'])
    for inf in informes_data:
        metricas_raw = inf.get("metricas", None)

        if isinstance(metricas_raw, str):
            try:
                inf["metricas"] = json.loads(metricas_raw)
                print(f"✅ Métricas parseadas correctamente para {inf.get('jugador_nombre')}")
            except Exception as e:
                print(f"❌ Error al parsear JSON de {inf.get('jugador_nombre')}: {e}")
                inf["metricas"] = {}

        if isinstance(inf.get("metricas"), dict):
            if "promedios" in inf["metricas"]:
                print(f"📊 Promedios encontrados para {inf['jugador_nombre']}: {inf['metricas']['promedios']}")
            elif "evaluaciones" in inf["metricas"]:
                print(f"📋 Evaluaciones detectadas para {inf['jugador_nombre']}: {list(inf['metricas']['evaluaciones'].keys())}")
            else:
                print(f"⚠️ JSON sin 'promedios' ni 'evaluaciones' para {inf['jugador_nombre']}")
        else:
            print(f"❌ Campo 'metricas' no válido para {inf.get('jugador_nombre')}")
    
    if not informes_data:
        st.info("📝 **Aún no has creado ningún informe**")
        st.write("Los informes de scouting aparecerán aquí cuando evalúes jugadores.")
        
        if st.button("🏟️ Crear Mi Primer Informe", use_container_width=True):
            st.switch_page("pages/4_⚽_Centro de Scouting.py")
        st.stop()
    
    # Log inicial simplificado
    print(f"\n✅ Cargados {len(informes_data)} informes para {current_user['usuario']}")
    
    # Verificar estructura del primer informe (solo en modo debug)
    if st.secrets.get("debug_mode", True):  # Solo si está activado el debug
        primer_informe = informes_data[0]
        print(f"📊 Estructura primer informe: {list(primer_informe.keys())[:10]}...")
        if 'metricas' in primer_informe and isinstance(primer_informe['metricas'], dict):
            print(f"   - Métricas encontradas: {list(primer_informe['metricas'].keys())}")
    
    # Procesar informes
    informes_procesados = []
    
    for i, informe in enumerate(informes_data):
        informe_proc = dict(informe)
        
        # Usar la función mejorada para obtener métricas
        metricas_data = obtener_metricas_para_pdf(informe)
        
        # Asignar promedios directamente
        informe_proc['promedio_tecnico'] = metricas_data['promedios']['tecnicos']
        informe_proc['promedio_tactico'] = metricas_data['promedios']['tacticos']
        informe_proc['promedio_fisico'] = metricas_data['promedios']['fisicos']
        informe_proc['promedio_mental'] = metricas_data['promedios']['mentales']
        
        informes_procesados.append(informe_proc)
    
    # Convertir a DataFrame
    df_informes = pd.DataFrame(informes_procesados)
    
    # Asegurar columnas básicas
    columnas_basicas = ['id', 'jugador_nombre', 'equipo', 'posicion', 'nota_general', 
                       'potencial', 'recomendacion', 'fecha_creacion', 'tipo_evaluacion',
                       'jugador_bd_id', 'imagen_url', 'equipo_local', 'equipo_visitante',
                       'minutos_observados', 'fortalezas', 'debilidades', 'observaciones']
    
    for col in columnas_basicas:
        if col not in df_informes.columns:
            df_informes[col] = None
    
    print(f"✅ Procesamiento completado: {len(df_informes)} informes listos")
    st.markdown("---")
    
    # Filtros
    st.subheader("🔍 Filtros y Búsqueda")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        jugadores_disponibles = ['Todos'] + sorted(df_informes['jugador_nombre'].unique().tolist())
        jugador_filtro = st.selectbox("👤 Jugador", jugadores_disponibles)
    
    with filter_col2:
        equipos_disponibles = ['Todos'] + sorted(df_informes['equipo'].unique().tolist())
        equipo_filtro = st.selectbox("🏟️ Equipo", equipos_disponibles)
    
    with filter_col3:
        recomendaciones_disponibles = ['Todas'] + sorted(df_informes['recomendacion'].dropna().unique().tolist())
        recomendacion_filtro = st.selectbox("💼 Recomendación", recomendaciones_disponibles)
    
    with filter_col4:
        nota_min, nota_max = st.slider("🌟 Rango de Notas", 1, 10, (1, 10))
    
    # Aplicar filtros
    df_filtrado = df_informes.copy()
    
    if jugador_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['jugador_nombre'] == jugador_filtro]
    
    if equipo_filtro != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['equipo'] == equipo_filtro]
    
    if recomendacion_filtro != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['recomendacion'] == recomendacion_filtro]
    
    df_filtrado = df_filtrado[
        (df_filtrado['nota_general'] >= nota_min) & 
        (df_filtrado['nota_general'] <= nota_max)
    ]
    
    st.markdown("---")
    
    # Mostrar resultados
    if df_filtrado.empty:
        st.warning("🔍 No se encontraron informes con los filtros aplicados")
    else:
        st.subheader(f"📋 Informes Encontrados ({len(df_filtrado)})")
        
        # ✅ NUEVA SECCIÓN: EXPORTACIÓN PDF CON RADAR
        st.markdown("### 📄 Exportación a PDF con Radar Chart")
        
        export_col1, export_col2 = st.columns([2, 1])
        
        with export_col1:
            # Selector de informe para PDF
            opciones_pdf = []
            for idx, informe in df_filtrado.iterrows():
                opciones_pdf.append(f"#{informe['id']} - {informe['jugador_nombre']} ({informe['equipo']}) - {informe['nota_general']}/10")
            
            informe_pdf_seleccionado = st.selectbox(
                "📋 Selecciona informe para exportar:",
                options=range(len(opciones_pdf)),
                format_func=lambda x: opciones_pdf[x],
                key="selector_pdf"
            )
        
        with export_col2:
            if st.button("📄 Generar PDF", use_container_width=True, type="primary"):
                if informe_pdf_seleccionado is not None:
                    # IMPORTANTE: Convertir Serie a diccionario
                    informe_data = df_filtrado.iloc[informe_pdf_seleccionado].to_dict()
                    
                    with st.spinner("Generando informe profesional con radar chart..."):
                        try:
                            # Buscar datos Wyscout del jugador si están disponibles
                            datos_wyscout = None
                            
                            # Verificar si existe jugador_bd_id y es válido
                            if 'jugador_bd_id' in informe_data and informe_data.get('jugador_bd_id'):
                                try:
                                    jugador_bd_id = informe_data['jugador_bd_id']
                                    if pd.notna(jugador_bd_id) and jugador_bd_id > 0:
                                        jugador_bd = jugador_model.obtener_jugador_por_id(jugador_bd_id)
                                        if jugador_bd:
                                            datos_wyscout = jugador_bd
                                except Exception as e:
                                    print(f"⚠️ No se pudo obtener datos de BD: {e}")
                            
                            # Obtener TODOS los informes del jugador para radar ponderado
                            todos_informes_jugador = df_informes[
                                df_informes['jugador_nombre'] == informe_data['jugador_nombre']
                            ].to_dict('records')

                            # Asegurar que 'metricas' esté parseado si es string JSON
                            if 'metricas' in informe_data and isinstance(informe_data['metricas'], str):
                                try:
                                    informe_data['metricas'] = json.loads(informe_data['metricas'])
                                except:
                                    print("⚠️ No se pudo parsear métricas JSON")

                            file_bytes, mime_type, extension = generar_pdf_profesional(
                                informe_data, 
                                datos_wyscout, 
                                current_user,
                                todos_informes_jugador
                            )
                            
                            if file_bytes:
                                # Crear nombre de archivo seguro
                                fecha_informe = informe_data.get('fecha_creacion', datetime.now().strftime('%Y-%m-%d'))
                                if isinstance(fecha_informe, str) and len(fecha_informe) >= 10:
                                    fecha_informe = fecha_informe[:10]
                                else:
                                    fecha_informe = datetime.now().strftime('%Y-%m-%d')
                                
                                nombre_jugador_limpio = informe_data.get('jugador_nombre', 'Jugador').replace(' ', '_').replace('/', '_')
                                nombre_archivo = f"Informe_{nombre_jugador_limpio}_{fecha_informe}.{extension}"
                                
                                # Botón de descarga
                                st.download_button(
                                    label=f"📥 Descargar {'PDF' if extension == 'pdf' else 'HTML'}",
                                    data=file_bytes,
                                    file_name=nombre_archivo,
                                    mime=mime_type,
                                    use_container_width=True,
                                    key="download_pdf"
                                )
                                
                                st.success(f"✅ ¡Informe generado exitosamente como {extension.upper()}!")
                                
                        except Exception as e:
                            st.error(f"❌ Error generando informe: {str(e)}")
                            print(f"Error detallado: {e}")
                            import traceback
                            traceback.print_exc()

    # Separador visual
    st.markdown("---")

    # === SECCIÓN DE COMPARACIÓN DE JUGADORES ===
    if len(df_filtrado) >= 2:
        st.markdown("---")
        st.subheader("🔄 Comparación de Jugadores")
        
        # Agrupar por posición para comparaciones más precisas
        posiciones_disponibles = df_filtrado['posicion'].unique()
        posiciones_con_multiples = [pos for pos in posiciones_disponibles 
                                if len(df_filtrado[df_filtrado['posicion'] == pos]) >= 2]
        
        if posiciones_con_multiples:
            comp_col1, comp_col2 = st.columns([1, 3])
            
            with comp_col1:
                posicion_comparar = st.selectbox(
                    "Selecciona posición:",
                    posiciones_con_multiples,
                    key="posicion_comparar"
                )
            
            # Filtrar jugadores de esa posición
            df_posicion = df_filtrado[df_filtrado['posicion'] == posicion_comparar]
            jugadores_posicion = df_posicion.groupby('jugador_nombre').agg({
                'nota_general': 'mean',
                'id': 'count'
            }).reset_index()
            jugadores_posicion.columns = ['jugador_nombre', 'nota_promedio', 'num_informes']
            jugadores_posicion = jugadores_posicion.sort_values('nota_promedio', ascending=False)
            
            with comp_col2:
                st.write(f"**Jugadores disponibles en {posicion_comparar}:**")
                
                # Mostrar tabla comparativa simple
                tabla_comp = jugadores_posicion.copy()
                tabla_comp['nota_promedio'] = tabla_comp['nota_promedio'].round(1)
                tabla_comp.columns = ['Jugador', 'Nota Media', 'Evaluaciones']
                
                st.dataframe(
                    tabla_comp,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Nota Media": st.column_config.NumberColumn(
                            format="%.1f/10",
                            min_value=0,
                            max_value=10
                        )
                    }
                )
            
            # Seleccionar jugadores para comparación detallada
            if len(jugadores_posicion) >= 2:
                st.markdown("#### Comparación Detallada")
                
                comp_det_col1, comp_det_col2 = st.columns(2)
                
                with comp_det_col1:
                    jugador1 = st.selectbox(
                        "Jugador 1:",
                        jugadores_posicion['jugador_nombre'].tolist(),
                        index=0,
                        key="jugador1_comp"
                    )
                
                with comp_det_col2:
                    opciones_j2 = [j for j in jugadores_posicion['jugador_nombre'].tolist() if j != jugador1]
                    jugador2 = st.selectbox(
                        "Jugador 2:",
                        opciones_j2,
                        key="jugador2_comp"
                    )
                
                if jugador1 and jugador2:
                    # Obtener últimos informes de cada jugador
                    info_j1 = df_posicion[df_posicion['jugador_nombre'] == jugador1].iloc[0]
                    info_j2 = df_posicion[df_posicion['jugador_nombre'] == jugador2].iloc[0]
                    
                    # Extraer métricas del JSON
                    metricas_j1 = info_j1.get('metricas', {})
                    metricas_j2 = info_j2.get('metricas', {})
                    
                    # Comparación por categorías
                    st.markdown("##### Comparación por Categorías")
                    
                    categorias = ['tecnicos', 'tacticos', 'fisicos', 'mentales']
                    
                    # Crear DataFrame para comparación
                    data_comp = []
                    
                    for cat in categorias:
                        prom_j1 = 0
                        prom_j2 = 0
                        
                        if isinstance(metricas_j1, dict) and 'promedios' in metricas_j1:
                            prom_j1 = metricas_j1['promedios'].get(cat, 0)
                        
                        if isinstance(metricas_j2, dict) and 'promedios' in metricas_j2:
                            prom_j2 = metricas_j2['promedios'].get(cat, 0)
                        
                        data_comp.append({
                            'Categoría': cat.title().rstrip('s'),
                            jugador1: prom_j1,
                            jugador2: prom_j2,
                            'Diferencia': prom_j1 - prom_j2
                        })
                    
                    df_comp = pd.DataFrame(data_comp)
                    
                    # Mostrar gráfico de barras
                    fig = go.Figure()
                    
                    # Barras para jugador 1
                    fig.add_trace(go.Bar(
                        name=jugador1,
                        x=df_comp['Categoría'],
                        y=df_comp[jugador1],
                        text=df_comp[jugador1].round(1),
                        textposition='auto',
                        marker_color='#007bbf'
                    ))
                    
                    # Barras para jugador 2
                    fig.add_trace(go.Bar(
                        name=jugador2,
                        x=df_comp['Categoría'],
                        y=df_comp[jugador2],
                        text=df_comp[jugador2].round(1),
                        textposition='auto',
                        marker_color='#667eea'
                    ))
                    
                    fig.update_layout(
                        title=f"Comparación: {jugador1} vs {jugador2}",
                        xaxis_title="Categorías",
                        yaxis_title="Puntuación",
                        barmode='group',
                        yaxis_range=[0, 10],
                        height=400,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom",
                            y=1.02,
                            xanchor="right",
                            x=1
                        )
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla resumen
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric(
                            "Nota General",
                            f"{info_j1['nota_general']:.1f}/10",
                            f"{(info_j1['nota_general'] - info_j2['nota_general']):.1f}",
                            delta_color="normal"
                        )
                    
                    with col2:
                        st.metric(
                            "Promedio Total",
                            f"{df_comp[jugador1].mean():.1f}/10",
                            f"{(df_comp[jugador1].mean() - df_comp[jugador2].mean()):.1f}",
                            delta_color="normal"
                        )
                    
                    with col3:
                        ganador = jugador1 if info_j1['nota_general'] > info_j2['nota_general'] else jugador2
                        st.metric(
                            "Mejor Valorado",
                            ganador,
                            "✨"
                        )
                    
                    # Observaciones clave
                    with st.expander("💡 Análisis Comparativo"):
                        # Encontrar fortalezas relativas
                        fortalezas_j1 = []
                        fortalezas_j2 = []
                        
                        for idx, row in df_comp.iterrows():
                            if row['Diferencia'] > 1:
                                fortalezas_j1.append(f"{row['Categoría']} (+{row['Diferencia']:.1f})")
                            elif row['Diferencia'] < -1:
                                fortalezas_j2.append(f"{row['Categoría']} (+{abs(row['Diferencia']):.1f})")
                        
                        col_obs1, col_obs2 = st.columns(2)
                        
                        with col_obs1:
                            st.write(f"**Ventajas de {jugador1}:**")
                            if fortalezas_j1:
                                for f in fortalezas_j1:
                                    st.write(f"• {f}")
                            else:
                                st.write("• Sin ventajas significativas")
                        
                        with col_obs2:
                            st.write(f"**Ventajas de {jugador2}:**")
                            if fortalezas_j2:
                                for f in fortalezas_j2:
                                    st.write(f"• {f}")
                            else:
                                st.write("• Sin ventajas significativas")
                        
                        # Recomendaciones
                        st.write("**Recomendaciones:**")
                        recom_j1 = info_j1.get('recomendacion', 'N/A')
                        recom_j2 = info_j2.get('recomendacion', 'N/A')
                        
                        st.write(f"• {jugador1}: {recom_j1.replace('_', ' ').title()}")
                        st.write(f"• {jugador2}: {recom_j2.replace('_', ' ').title()}")
        else:
            st.info("📊 La comparación de jugadores requiere al menos 2 jugadores de la misma posición")
    else:
        st.info("📊 Necesitas al menos 2 informes para poder comparar jugadores")

    st.markdown("---")

    # === SECCIÓN DE ANÁLISIS CON IA ===
    if not df_filtrado.empty:
        mostrar_resumenes_ia_streamlit(df_filtrado)

    st.markdown("---")

except Exception as e:
    st.error(f"❌ Error cargando informes: {str(e)}")
    st.write("Detalles del error:", e)

# Sidebar con estadísticas
with st.sidebar:
    
    # Acciones rápidas
    st.markdown("### ⚡ Acciones Rápidas")
    
    if st.button("🔄 Actualizar Informes", use_container_width=True):
        st.rerun()
    
    if st.button("📝 Crear Nuevo Informe", use_container_width=True):
        st.switch_page("pages/4_⚽_Centro de Scouting.py")
    
    if st.button("🚪 Cerrar Sesión", use_container_width=True):
        login_manager.logout()

# Footer
st.markdown("---")
st.markdown("""
<div style='
    background: #f8f9fa;
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    margin-top: 20px;
'>
    <h4>💡 Sistema de Informes Profesional con Radar Charts</h4>
    <p>Combina evaluaciones subjetivas del scout con análisis visual de datos estadísticos objetivos de Wyscout.</p>
    <p><strong>🎯 Tip:</strong> Los informes PDF incluyen radar charts profesionales para presentaciones de alto nivel.</p>
</div>
""", unsafe_allow_html=True)