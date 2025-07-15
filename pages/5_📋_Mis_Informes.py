# pages/📋_Mis_Informes.py - COMPLETO CON RADAR CHART

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os


# Añadir el directorio raíz al path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from common.login import LoginManager
# Justo después de current_user = login_manager.get_current_user()
from models.partido_model import PartidoModel
from models.jugador_model import JugadorModel
# Después de las importaciones existentes, añade:
from utils.resumen_scouting_ia import (
    ResumenScoutingIA, 
    agregar_resumenes_ia_al_pdf, 
    mostrar_resumenes_ia_streamlit
)

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

# REEMPLAZA TODA la función crear_radar_chart_jugador con esta versión corregida

def crear_radar_chart_jugador(datos_wyscout, nombre_jugador, equipo_jugador=None, informes_scout=None):
    """
    Versión mejorada que puede crear radar desde Wyscout O desde evaluaciones del scout
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from mplsoccer import Radar
        import tempfile
        import sys
        import os
        
        print(f"🔍 Generando radar para {nombre_jugador} ({equipo_jugador})")
        
        # Intentar obtener datos de Wyscout primero
        datos_reales = None
        usar_datos_wyscout = False
        fuente = "Evaluación Scout"
        
        # Importar extractor mejorado
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        utils_path = os.path.join(parent_dir, 'utils')
        if utils_path not in sys.path:
            sys.path.append(utils_path)
        
        try:
            from wyscout_data_extractor_personalizado import WyscoutExtractorPersonalizado
            extractor = WyscoutExtractorPersonalizado()
            
            # Buscar con nombre Y equipo
            datos_reales = extractor.obtener_datos_completos_jugador(nombre_jugador, equipo_jugador)
            
            if datos_reales:
                print(f"✅ Datos encontrados en Wyscout para {nombre_jugador} ({equipo_jugador})")
                usar_datos_wyscout = True
                fuente = "Wyscout LaLiga"
            else:
                print(f"⚠️ No se encontraron datos Wyscout, usando evaluaciones del scout")
                
        except ImportError as e:
            print(f"⚠️ Extractor no disponible: {e}")
        
        # Si no hay datos Wyscout, crear desde evaluaciones del scout
        if not usar_datos_wyscout and informes_scout:
            # CAMBIO PRINCIPAL: Usar la función mejorada con ponderación
            datos_reales = crear_datos_desde_evaluaciones_mejorado(informes_scout)
            
            # CAMBIO PRINCIPAL: Mostrar información detallada de la ponderación
            if datos_reales and '_num_evaluaciones' in datos_reales:
                num_eval = datos_reales['_num_evaluaciones']
                num_video = datos_reales['_num_video_completo']
                peso_total = datos_reales.get('_peso_total', 0)
                
                if num_video > 0:
                    fuente = f"Promedio ponderado de {num_eval} evaluaciones ({num_video} video completo)"
                else:
                    fuente = f"Promedio de {num_eval} evaluaciones de campo"
                    
                # Si queremos ser más específicos, podemos añadir el peso total
                # fuente += f" | Peso: {peso_total:.1f}"
            else:
                fuente = f"Promedio de {len(informes_scout)} evaluaciones"
        
        # === CONFIGURACIÓN DEL RADAR === (Sin cambios desde aquí)
        if usar_datos_wyscout:
            # Parámetros para datos objetivos (Wyscout)
            params = [
                'Precisión Pases',
                'Duelos Ganados', 
                'Duelos Aéreos',
                'Goles p/90',
                'Asistencias p/90',
                'xG p/90',
                'Regates p/90',
                'Interceptaciones p/90'
            ]
            
            min_range = [60, 30, 20, 0, 0, 0, 0, 0]
            max_range = [95, 70, 80, 1.2, 0.8, 1.0, 10, 5]
            
            valores_jugador = [
                datos_reales.get('precision_pases', 75),
                datos_reales.get('duelos_ganados_pct', 50),
                datos_reales.get('duelos_aereos_pct', 45),
                datos_reales.get('goles', 0.2),
                datos_reales.get('asistencias', 0.1),
                datos_reales.get('xg', 0.15),
                datos_reales.get('regates_completados', 2),
                datos_reales.get('interceptaciones', 1.5)
            ]
            
        else:
            # Parámetros para evaluación subjetiva (Scout)
            params = [
                'Técnica',
                'Táctica',
                'Físico',
                'Mental',
                'Finalización',
                'Creatividad',
                'Trabajo Def.',
                'Liderazgo'
            ]
            
            min_range = [0] * 8
            max_range = [10] * 8
            
            if datos_reales:
                valores_jugador = [
                    datos_reales.get('promedio_tecnico', 5),
                    datos_reales.get('promedio_tactico', 5),
                    datos_reales.get('promedio_fisico', 5),
                    datos_reales.get('promedio_mental', 5),
                    datos_reales.get('finalizacion', 5),
                    datos_reales.get('creatividad', 5),
                    datos_reales.get('trabajo_defensivo', 5),
                    datos_reales.get('liderazgo', 5)
                ]
            else:
                # Valores por defecto si no hay datos
                valores_jugador = [5] * 8
        
        # Asegurar valores en rangos
        for i, (valor, min_val, max_val) in enumerate(zip(valores_jugador, min_range, max_range)):
            valores_jugador[i] = max(min_val, min(max_val, valor))
        
        print(f"📊 Valores para radar: {[f'{v:.1f}' for v in valores_jugador]}")
        print(f"📊 Fuente de datos: {fuente}")
        
        # === CREAR RADAR ===
        radar = Radar(
            params, 
            min_range, 
            max_range,
            round_int=[False] * len(params),
            num_rings=4,
            ring_width=1, 
            center_circle_radius=1
        )
        
        # Setup axis
        fig, ax = radar.setup_axis()
        fig.set_size_inches(12, 10)
        
        # Colores según fuente
        if usar_datos_wyscout:
            color_principal = '#1e3a8a'  # Azul oscuro para datos objetivos
            color_secundario = '#3b82f6'
        else:
            color_principal = '#059669'  # Verde para evaluaciones scout
            color_secundario = '#10b981'
        
        color_fondo = '#f8fafc'
        
        # Dibujar círculos internos
        rings_inner = radar.draw_circles(
            ax=ax, 
            facecolor=color_fondo, 
            edgecolor='#e2e8f0'
        )
        
        # Dibujar radar
        radar_output = radar.draw_radar(
            valores_jugador, 
            ax=ax,
            kwargs_radar={
                'facecolor': color_principal, 
                'alpha': 0.3,
                'edgecolor': color_secundario,
                'linewidth': 2
            },
            kwargs_rings={
                'facecolor': color_secundario, 
                'alpha': 0.1
            }
        )
        
        radar_poly, rings_outer, vertices = radar_output
        
        # Añadir puntos en vértices
        ax.scatter(vertices[:, 0], vertices[:, 1], 
                  c='#007bff', s=60, zorder=5, 
                  edgecolors='white', linewidth=2)
        
        # Etiquetas
        range_labels = radar.draw_range_labels(ax=ax, fontsize=10)
        param_labels = radar.draw_param_labels(ax=ax, fontsize=11)
        
        # Información del jugador
        equipo_info = equipo_jugador or 'N/A'
        posicion_info = datos_reales.get('posicion', 'N/A') if datos_reales else 'N/A'
        
        # Título
        fig.suptitle(f'{equipo_info} - {nombre_jugador}', 
                    fontsize=16, color=color_principal, 
                    fontweight='bold', y=0.95)
        
        # Subtítulo con fuente
        plt.figtext(0.5, 0.91, 
                   f'{posicion_info} | Fuente: {fuente}', 
                   ha='center', fontsize=12, color='#007bff')
        
        # Footer
        plt.figtext(0.5, 0.02, 
                   'Sistema de Scouting Profesional', 
                   ha='center', fontsize=10, color='#24282a')
        
        # Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_path = tmp_file.name
        
        plt.savefig(tmp_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Radar generado exitosamente ({fuente})")
        return tmp_path
        
    except Exception as e:
        print(f"❌ Error generando radar: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    
def crear_datos_desde_evaluaciones_mejorado(informes_list):
    """
    Crea datos para el radar a partir de evaluaciones del scout
    Sistema de ponderación mejorado:
    - Video completo: peso 2.0
    - Campo: peso 1.0
    - Bonus por minutos observados
    - Considera la fecha (más recientes = más peso)
    """
    if not informes_list:
        return None
    
    print(f"📊 Procesando {len(informes_list)} informes para crear radar ponderado...")
    
    # Inicializar acumuladores detallados
    suma_ponderada = {
        # Promedios generales
        'tecnico': 0, 'tactico': 0, 'fisico': 0, 'mental': 0,
        # Métricas específicas para el radar
        'finalizacion': 0, 'creatividad': 0, 'trabajo_defensivo': 0, 'liderazgo': 0,
        # Contadores para validación
        'count_tecnico': 0, 'count_tactico': 0, 'count_fisico': 0, 'count_mental': 0
    }
    
    peso_total = 0
    detalles_ponderacion = []  # Para debug/información
    
    # Ordenar informes por fecha (más recientes primero)
    informes_ordenados = sorted(informes_list, 
                               key=lambda x: x.get('fecha_creacion', ''), 
                               reverse=True)
    
    for idx, informe in enumerate(informes_ordenados):
        # Calcular peso base
        if informe.get('tipo_evaluacion') == 'video_completo':
            peso_base = 2.0
            tipo = "Video Completo"
        else:
            peso_base = 1.0
            tipo = "Campo"
        
        # Factor por minutos observados (0.7 a 1.0)
        minutos = informe.get('minutos_observados', 90)
        factor_minutos = 0.7 + (0.3 * min(minutos / 90, 1.0))
        
        # Factor por antigüedad (informes más recientes pesan más)
        # El más reciente = 1.0, decrece hasta 0.8 para los más antiguos
        factor_recencia = 1.0 - (0.2 * (idx / max(len(informes_ordenados) - 1, 1)))
        
        # Peso final
        peso = peso_base * factor_minutos * factor_recencia
        peso_total += peso
        
        # Guardar detalles para debug
        detalles_ponderacion.append({
            'fecha': informe.get('fecha_creacion', 'N/A')[:10],
            'tipo': tipo,
            'minutos': minutos,
            'peso_base': peso_base,
            'factor_minutos': round(factor_minutos, 2),
            'factor_recencia': round(factor_recencia, 2),
            'peso_final': round(peso, 2)
        })
        
        # TÉCNICO - Mejorado con validación
        valores_tecnicos = []
        if informe.get('control_balon', 0) > 0:
            valores_tecnicos.append(informe['control_balon'])
        if informe.get('primer_toque', 0) > 0:
            valores_tecnicos.append(informe['primer_toque'])
        if informe.get('pase_corto', 0) > 0:
            valores_tecnicos.append(informe['pase_corto'])
        if informe.get('pase_largo', 0) > 0:
            valores_tecnicos.append(informe['pase_largo'])
        if informe.get('finalizacion', 0) > 0:
            valores_tecnicos.append(informe['finalizacion'])
        if informe.get('regate', 0) > 0:
            valores_tecnicos.append(informe['regate'])
        
        if valores_tecnicos:
            promedio_tecnico = sum(valores_tecnicos) / len(valores_tecnicos)
            suma_ponderada['tecnico'] += promedio_tecnico * peso
            suma_ponderada['count_tecnico'] += peso
        
        # TÁCTICO
        valores_tacticos = []
        if informe.get('vision_juego', 0) > 0:
            valores_tacticos.append(informe['vision_juego'])
        if informe.get('posicionamiento', 0) > 0:
            valores_tacticos.append(informe['posicionamiento'])
        if informe.get('marcaje', 0) > 0:
            valores_tacticos.append(informe['marcaje'])
        if informe.get('pressing', 0) > 0:
            valores_tacticos.append(informe['pressing'])
        if informe.get('transiciones', 0) > 0:
            valores_tacticos.append(informe['transiciones'])
        
        if valores_tacticos:
            promedio_tactico = sum(valores_tacticos) / len(valores_tacticos)
            suma_ponderada['tactico'] += promedio_tactico * peso
            suma_ponderada['count_tactico'] += peso
        
        # FÍSICO
        valores_fisicos = []
        if informe.get('velocidad', 0) > 0:
            valores_fisicos.append(informe['velocidad'])
        if informe.get('resistencia', 0) > 0:
            valores_fisicos.append(informe['resistencia'])
        if informe.get('fuerza', 0) > 0:
            valores_fisicos.append(informe['fuerza'])
        if informe.get('salto', 0) > 0:
            valores_fisicos.append(informe['salto'])
        if informe.get('agilidad', 0) > 0:
            valores_fisicos.append(informe['agilidad'])
        
        if valores_fisicos:
            promedio_fisico = sum(valores_fisicos) / len(valores_fisicos)
            suma_ponderada['fisico'] += promedio_fisico * peso
            suma_ponderada['count_fisico'] += peso
        
        # MENTAL
        valores_mentales = []
        if informe.get('concentracion', 0) > 0:
            valores_mentales.append(informe['concentracion'])
        if informe.get('liderazgo', 0) > 0:
            valores_mentales.append(informe['liderazgo'])
        if informe.get('comunicacion', 0) > 0:
            valores_mentales.append(informe['comunicacion'])
        if informe.get('presion', 0) > 0:
            valores_mentales.append(informe['presion'])
        if informe.get('decision', 0) > 0:
            valores_mentales.append(informe['decision'])
        
        if valores_mentales:
            promedio_mental = sum(valores_mentales) / len(valores_mentales)
            suma_ponderada['mental'] += promedio_mental * peso
            suma_ponderada['count_mental'] += peso
        
        # Métricas específicas para el radar
        if informe.get('finalizacion', 0) > 0:
            suma_ponderada['finalizacion'] += informe['finalizacion'] * peso
        
        if informe.get('vision_juego', 0) > 0:
            suma_ponderada['creatividad'] += informe['vision_juego'] * peso
        
        # Trabajo defensivo = promedio de marcaje y pressing
        trabajo_def_valores = []
        if informe.get('marcaje', 0) > 0:
            trabajo_def_valores.append(informe['marcaje'])
        if informe.get('pressing', 0) > 0:
            trabajo_def_valores.append(informe['pressing'])
        if trabajo_def_valores:
            suma_ponderada['trabajo_defensivo'] += (sum(trabajo_def_valores) / len(trabajo_def_valores)) * peso
        
        if informe.get('liderazgo', 0) > 0:
            suma_ponderada['liderazgo'] += informe['liderazgo'] * peso
    
    # Mostrar detalles de ponderación
    print("\n📊 Detalles de ponderación:")
    for detalle in detalles_ponderacion:
        print(f"  - {detalle['fecha']} | {detalle['tipo']} | "
              f"{detalle['minutos']}min | Peso: {detalle['peso_final']}")
    
    # Calcular promedios ponderados finales
    if peso_total > 0:
        datos = {
            'promedio_tecnico': round(suma_ponderada['tecnico'] / suma_ponderada['count_tecnico'], 1) 
                               if suma_ponderada['count_tecnico'] > 0 else 5.0,
            'promedio_tactico': round(suma_ponderada['tactico'] / suma_ponderada['count_tactico'], 1) 
                               if suma_ponderada['count_tactico'] > 0 else 5.0,
            'promedio_fisico': round(suma_ponderada['fisico'] / suma_ponderada['count_fisico'], 1) 
                              if suma_ponderada['count_fisico'] > 0 else 5.0,
            'promedio_mental': round(suma_ponderada['mental'] / suma_ponderada['count_mental'], 1) 
                              if suma_ponderada['count_mental'] > 0 else 5.0,
            'finalizacion': round(suma_ponderada['finalizacion'] / peso_total, 1),
            'creatividad': round(suma_ponderada['creatividad'] / peso_total, 1),
            'trabajo_defensivo': round(suma_ponderada['trabajo_defensivo'] / peso_total, 1),
            'liderazgo': round(suma_ponderada['liderazgo'] / peso_total, 1)
        }
        
        # Información adicional para el radar
        datos['_peso_total'] = round(peso_total, 2)
        datos['_num_evaluaciones'] = len(informes_list)
        datos['_num_video_completo'] = sum(1 for i in informes_list 
                                          if i.get('tipo_evaluacion') == 'video_completo')
        
        print(f"\n✅ Datos calculados con ponderación avanzada:")
        print(f"   - Peso total acumulado: {peso_total:.2f}")
        print(f"   - Evaluaciones: {datos['_num_evaluaciones']} "
              f"({datos['_num_video_completo']} video completo)")
        print(f"   - Promedios: Téc={datos['promedio_tecnico']}, "
              f"Tác={datos['promedio_tactico']}, "
              f"Fís={datos['promedio_fisico']}, "
              f"Men={datos['promedio_mental']}")
        
        return datos
    
    return None

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
        'á': 'a',
        'é': 'e',
        'í': 'i',
        'ó': 'o',
        'ú': 'u',
        'ñ': 'n',
        'Á': 'A',
        'É': 'E',
        'Í': 'I',
        'Ó': 'O',
        'Ú': 'U',
        'Ñ': 'N'
    }
    
    # Aplicar reemplazos
    texto_limpio = texto
    for char_original, char_reemplazo in reemplazos.items():
        texto_limpio = texto_limpio.replace(char_original, char_reemplazo)
    
    # Eliminar otros caracteres Unicode problemáticos
    texto_limpio = ''.join(char for char in texto_limpio if ord(char) < 256)
    
    return texto_limpio


def generar_pdf_profesional(informe_data, datos_wyscout=None, user_info=None, todos_informes_jugador=None):
    """
    Genera un PDF profesional con toda la información del informe de scouting
    """
    try:
        from fpdf import FPDF
        import tempfile
        import os
        import datetime
        
        print(f"📄 Generando PDF profesional para {informe_data['jugador_nombre']}...")
        
        # Preparar datos básicos
        scout_nombre = limpiar_texto_para_pdf(user_info['nombre'] if user_info else 'Scout')
        jugador_nombre = limpiar_texto_para_pdf(informe_data['jugador_nombre'])
        equipo = limpiar_texto_para_pdf(informe_data['equipo'])
        posicion = limpiar_texto_para_pdf(informe_data.get('posicion', 'N/A'))
        
        # === CREAR RADAR CHART ===
        radar_path = None
        try:
            print("🎯 Creando radar chart...")
            
            # Si tenemos múltiples informes del jugador, usarlos para el radar
            informes_para_radar = todos_informes_jugador if todos_informes_jugador else [informe_data]
            
            # Crear radar con la función mejorada
            radar_path = crear_radar_chart_jugador(
                datos_wyscout=datos_wyscout,
                nombre_jugador=informe_data['jugador_nombre'],
                equipo_jugador=informe_data['equipo'],
                informes_scout=informes_para_radar
            )
            
            if radar_path and os.path.exists(radar_path):
                print("✅ Radar chart creado exitosamente")
        except Exception as e:
            print(f"⚠️ Error creando radar: {str(e)}")
            radar_path = None
        
        # === CREAR PDF ===
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # ==================== PÁGINA 1: PORTADA Y RADAR ====================
        pdf.add_page()
        
        # Header principal
        pdf.set_font('Helvetica', 'B', 24)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 20, 'INFORME DE SCOUTING PROFESIONAL', 0, 1, 'C')
        
        # Línea decorativa
        pdf.set_fill_color(0, 123, 191)
        pdf.rect(15, 30, 180, 3, 'F')
        pdf.ln(20)
        
        # Información del jugador
        pdf.set_font('Helvetica', 'B', 20)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(0, 15, f"{jugador_nombre}", 0, 1, 'C')
        
        pdf.set_font('Helvetica', '', 16)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 10, f"{equipo} - {posicion}", 0, 1, 'C')
        pdf.ln(10)
        
        # Información básica en caja
        pdf.set_fill_color(248, 249, 250)
        pdf.rect(20, pdf.get_y(), 170, 50, 'F')
        
        y_inicial = pdf.get_y()
        
        # Primera fila de información
        pdf.set_xy(30, y_inicial + 5)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(40, 8, 'Scout:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(60, 8, scout_nombre, 0, 0)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(30, 8, 'Fecha:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        fecha_informe = informe_data.get('fecha_creacion', '')[:10] if informe_data.get('fecha_creacion') else 'N/A'
        pdf.cell(40, 8, fecha_informe, 0, 1)
        
        # Segunda fila
        pdf.set_x(30)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(40, 8, 'Nota General:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(60, 8, f"{informe_data.get('nota_general', 0)}/10", 0, 0)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(30, 8, 'Potencial:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(40, 8, limpiar_texto_para_pdf(informe_data.get('potencial', 'N/A')), 0, 1)
        
        # Tercera fila
        pdf.set_x(30)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(40, 8, 'Tipo Evaluacion:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        tipo_eval = informe_data.get('tipo_evaluacion', 'campo').replace('_', ' ').title()
        pdf.cell(60, 8, tipo_eval, 0, 0)
        
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(30, 8, 'Minutos:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(40, 8, f"{informe_data.get('minutos_observados', 90)}'", 0, 1)
        
        # Cuarta fila
        num_informes = len(todos_informes_jugador) if todos_informes_jugador else 1
        pdf.set_x(30)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(40, 8, 'Total Informes:', 0, 0)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(60, 8, str(num_informes), 0, 1)
        
        pdf.ln(20)
        
        # === RADAR CHART ===
        if radar_path and os.path.exists(radar_path):
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(0, 123, 191)
            pdf.cell(0, 10, 'ANALISIS RADAR - PERFIL TECNICO-TACTICO', 0, 1, 'C')
            pdf.ln(5)
            
            try:
                # Calcular posición centrada
                page_width = 210
                image_width = 160
                x_centered = (page_width - image_width) / 2
                
                # Verificar espacio disponible
                espacio_disponible = 290 - pdf.get_y() - 20  # 290 es altura A4, 20 margen inferior
                altura_imagen = 120  # Altura deseada de la imagen
                
                if espacio_disponible < altura_imagen:
                    pdf.add_page()
                    pdf.ln(10)
                
                pdf.image(radar_path, x=x_centered, y=pdf.get_y(), w=image_width)
                
                # Limpiar archivo temporal
                os.unlink(radar_path)
                
            except Exception as e:
                print(f"⚠️ Error insertando radar: {str(e)}")
        
        # ==================== PÁGINA 2: EVALUACIONES DETALLADAS ====================
        pdf.add_page()
        
        # Header de página 2
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 15, f"EVALUACION DETALLADA", 0, 1, 'C')
        
        # Línea decorativa
        pdf.set_fill_color(0, 123, 191)
        pdf.rect(15, 25, 180, 2, 'F')
        pdf.ln(15)
        
        # === EVALUACIONES POR CATEGORÍAS ===
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(0, 10, 'EVALUACION POR CATEGORIAS', 0, 1, 'C')
        pdf.ln(5)
        
        categorias = {
            'TECNICO': ['control_balon', 'primer_toque', 'pase_corto', 'pase_largo', 'finalizacion', 'regate'],
            'TACTICO': ['vision_juego', 'posicionamiento', 'marcaje', 'pressing', 'transiciones'],
            'FISICO': ['velocidad', 'resistencia', 'fuerza', 'salto', 'agilidad'],
            'MENTAL': ['concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision']
        }
        
        for i, (categoria, campos) in enumerate(categorias.items()):
            # Calcular promedio
            valores = [informe_data.get(campo, 0) for campo in campos if campo in informe_data]
            promedio = sum(valores) / len(valores) if valores else 0
            
            # Fondo alternado
            if i % 2 == 0:
                pdf.set_fill_color(248, 249, 250)
                pdf.rect(15, pdf.get_y() - 1, 180, 12, 'F')
            
            # Color de la barra según promedio
            if promedio >= 8:
                color_barra = (0, 123, 191)
            elif promedio >= 6:
                color_barra = (40, 167, 69)
            elif promedio >= 4:
                color_barra = (255, 193, 7)
            else:
                color_barra = (220, 53, 69)
            
            # Nombre de categoría
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(36, 40, 42)
            pdf.cell(50, 10, f"{categoria}:", 0, 0)
            
            # Barra de progreso
            pdf.set_fill_color(*color_barra)
            barra_width = (promedio / 10) * 80
            pdf.rect(70, pdf.get_y() + 2, barra_width, 6, 'F')
            
            # Borde de la barra
            pdf.set_draw_color(200, 200, 200)
            pdf.rect(70, pdf.get_y() + 2, 80, 6, 'D')
            
            # Valor numérico
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 123, 191)
            pdf.set_xy(160, pdf.get_y())
            pdf.cell(30, 10, f"{promedio:.1f}/10", 0, 1)
        
        pdf.ln(10)
        
        # === FORTALEZAS Y DEBILIDADES ===
        pdf.set_font('Helvetica', 'B', 14)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(0, 10, 'ANALISIS CUALITATIVO', 0, 1, 'C')
        pdf.ln(5)
        
        # Fortalezas
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(40, 167, 69)
        pdf.cell(0, 8, 'FORTALEZAS PRINCIPALES:', 0, 1)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        fortalezas_texto = limpiar_texto_para_pdf(informe_data.get('fortalezas', 'No especificadas'))
        pdf.multi_cell(0, 5, fortalezas_texto, 0, 'L')
        pdf.ln(5)
        
        # Debilidades
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(220, 53, 69)
        pdf.cell(0, 8, 'AREAS DE MEJORA:', 0, 1)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        debilidades_texto = limpiar_texto_para_pdf(informe_data.get('debilidades', 'No especificadas'))
        pdf.multi_cell(0, 5, debilidades_texto, 0, 'L')
        pdf.ln(5)
        
        # ==================== PÁGINA 3: OBSERVACIONES Y RECOMENDACIÓN ====================
        pdf.add_page()
        
        # Header de página 3
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 15, 'OBSERVACIONES Y RECOMENDACION', 0, 1, 'C')
        
        # Línea decorativa
        pdf.set_fill_color(0, 123, 191)
        pdf.rect(15, 25, 180, 2, 'F')
        pdf.ln(15)
        
        # Observaciones del scout
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 8, 'OBSERVACIONES DETALLADAS DEL SCOUT:', 0, 1)
        
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(60, 60, 60)
        observaciones_texto = limpiar_texto_para_pdf(informe_data.get('observaciones', 'Sin observaciones adicionales'))
        
        # Dividir observaciones largas en párrafos
        if len(observaciones_texto) > 500:
            # Buscar puntos para dividir
            parrafos = observaciones_texto.split('. ')
            for parrafo in parrafos:
                if parrafo.strip():
                    pdf.multi_cell(0, 5, parrafo.strip() + '.', 0, 'L')
                    pdf.ln(3)
        else:
            pdf.multi_cell(0, 5, observaciones_texto, 0, 'L')
        
        pdf.ln(10)
        
        # === RECOMENDACIÓN FINAL ===
        recomendacion_raw = informe_data.get('recomendacion', 'Sin recomendacion')
        recomendacion = limpiar_texto_para_pdf(recomendacion_raw.replace('_', ' ').title())
        
        # Color según recomendación
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
        
        # Caja de recomendación destacada
        pdf.ln(10)
        pdf.set_fill_color(*color_recom)
        pdf.rect(30, pdf.get_y(), 150, 25, 'F')
        
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(30, pdf.get_y() + 7)
        pdf.cell(150, 10, mensaje_recom, 0, 1, 'C')
        
        # === RESUMEN EJECUTIVO (si existe en observaciones) ===
        pdf.ln(20)
        
        # Información de datos Wyscout si existen
        if datos_wyscout:
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(0, 123, 191)
            pdf.cell(0, 8, 'DATOS ESTADISTICOS (WYSCOUT):', 0, 1)
            
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(60, 60, 60)
            
            estadisticas = [
                ('Partidos jugados', datos_wyscout.get('partidos_jugados', 'N/A')),
                ('Minutos jugados', datos_wyscout.get('minutos_jugados', 'N/A')),
                ('Goles', datos_wyscout.get('goles', 'N/A')),
                ('Asistencias', datos_wyscout.get('asistencias', 'N/A')),
                ('Edad', f"{datos_wyscout.get('edad', 'N/A')} años" if datos_wyscout.get('edad') else 'N/A')
            ]
            
            for etiqueta, valor in estadisticas:
                pdf.cell(60, 6, f"{etiqueta}:", 0, 0)
                pdf.cell(40, 6, str(valor), 0, 1)
        

        # === PÁGINA 4: ANÁLISIS INTELIGENTE (si hay múltiples informes) ===
        if todos_informes_jugador and len(todos_informes_jugador) > 1:
            agregar_resumenes_ia_al_pdf(pdf, todos_informes_jugador, informe_data['jugador_nombre'])

        # === FOOTER ===
        # Posicionar en la parte inferior
        pdf.set_y(-40)
        
        # Línea separadora
        pdf.set_draw_color(0, 123, 191)
        pdf.line(20, pdf.get_y(), 190, pdf.get_y())
        pdf.ln(5)
        
        # Información del footer
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 5, f"Informe generado el {fecha_actual} por {scout_nombre}", 0, 1, 'C')
        
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(0, 5, 'SISTEMA DE SCOUTING PROFESIONAL', 0, 1, 'C')
        
        # === GUARDAR PDF ===
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
        
        pdf.output(tmp_path)
        
        # Leer archivo y eliminar temporal
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        
        os.unlink(tmp_path)
        
        print("✅ PDF profesional generado exitosamente")
        return pdf_bytes, "application/pdf", "pdf"
        
    except Exception as e:
        print(f"❌ Error generando PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Si falla el PDF, generar HTML como fallback
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
    if datos_wyscout:
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
                        <span>{datos_wyscout.get('minutos_jugados', 'N/A')}</span>
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
                <p>Informe generado el {datetime.datetime.now().strftime("%d/%m/%Y %H:%M")} por {scout_nombre}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html.encode('utf-8'), "text/html", "html"

# ✅ CARGAR INFORMES DEL USUARIO
try:
    informes_data = partido_model.obtener_informes_por_usuario(current_user['usuario'])
    
    if not informes_data:
        st.info("📝 **Aún no has creado ningún informe**")
        st.write("Los informes de scouting aparecerán aquí cuando evalúes jugadores.")
        
        if st.button("🏟️ Crear Mi Primer Informe", use_container_width=True):
            st.switch_page("pages/4_⚽_Centro de Scouting.py")
        st.stop()
    
    # Convertir a DataFrame para análisis
    columns = [
        'id', 'partido_id', 'jugador_nombre', 'equipo', 'posicion', 'scout_usuario',
        'control_balon', 'primer_toque', 'pase_corto', 'pase_largo', 'finalizacion', 'regate',
        'vision_juego', 'posicionamiento', 'marcaje', 'pressing', 'transiciones',
        'velocidad', 'resistencia', 'fuerza', 'salto', 'agilidad',
        'concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision',
        'nota_general', 'potencial', 'recomendacion',
        'fortalezas', 'debilidades', 'observaciones', 'minutos_observados',
        'jugador_bd_id', 'wyscout_match_confianza', 'wyscout_algoritmo', 'procesado_wyscout',
        'fecha_creacion', 'tipo_evaluacion', 'imagen_url',  # AÑADIDAS ESTAS DOS COLUMNAS
        'equipo_local', 'equipo_visitante', 'fecha_partido', 'estado_wyscout'
    ]
    
    # Verificar número de columnas antes de crear DataFrame
    if informes_data:
        num_columnas_datos = len(informes_data[0])
        num_columnas_definidas = len(columns)
        
        if num_columnas_datos != num_columnas_definidas:
            print(f"⚠️ Advertencia: {num_columnas_datos} columnas en datos vs {num_columnas_definidas} definidas")
            # Usar solo las columnas que coincidan
            columns_to_use = columns[:num_columnas_datos]
        else:
            columns_to_use = columns
            
        df_informes = pd.DataFrame(informes_data, columns=columns_to_use)
    else:
        df_informes = pd.DataFrame(columns=columns)
    
    # Estadísticas generales
    total_informes = len(df_informes)
    jugadores_unicos = df_informes['jugador_nombre'].nunique()
    equipos_observados = df_informes['equipo'].nunique()
    nota_promedio = df_informes['nota_general'].mean()
    
    # Métricas principales
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric("📝 Total Informes", total_informes)
    
    with metric_col2:
        st.metric("👥 Jugadores Únicos", jugadores_unicos)
    
    with metric_col3:
        st.metric("🏟️ Equipos Observados", equipos_observados)
    
    with metric_col4:
        st.metric("📊 Nota Promedio", f"{nota_promedio:.1f}/10" if not pd.isna(nota_promedio) else "N/A")
    
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
                    informe_data = df_filtrado.iloc[informe_pdf_seleccionado]
                    
                    with st.spinner("Generando informe profesional con radar chart..."):
                        try:
                            # Buscar datos Wyscout del jugador si están disponibles
                            datos_wyscout = None
                            if pd.notna(informe_data['jugador_bd_id']) and informe_data['jugador_bd_id'] > 0:
                                jugador_bd = jugador_model.obtener_jugador_por_id(informe_data['jugador_bd_id'])
                                if jugador_bd:
                                    datos_wyscout = jugador_bd
                            
                            # ✅ GENERAR PDF CON RADAR
                            # Obtener TODOS los informes del jugador para radar ponderado
                            todos_informes_jugador = df_informes[
                                df_informes['jugador_nombre'] == informe_data['jugador_nombre']
                            ].to_dict('records')

                            file_bytes, mime_type, extension = generar_pdf_profesional(
                                informe_data, 
                                datos_wyscout, 
                                current_user,
                                todos_informes_jugador  # Pasar todos los informes
                            )
                            
                            if file_bytes:
                                # Crear nombre de archivo
                                nombre_archivo = f"Informe_{informe_data['jugador_nombre'].replace(' ', '_')}_{informe_data['fecha_creacion'][:10]}.{extension}"
                                
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
                                
                                # Mostrar información del contenido
                                if datos_wyscout:
                                    st.info("📊 **Informe incluye radar chart con datos estadísticos de Wyscout**")
                                else:
                                    st.info("📝 **Informe basado en evaluación del scout (sin datos Wyscout)**")
                                
                        except Exception as e:
                            st.error(f"❌ Error generando informe: {str(e)}")

    # Separador visual
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
    st.markdown("### 📊 Estadísticas de Integración")
    
    try:
        stats_integracion = partido_model.obtener_estadisticas_integracion()
        
        if stats_integracion and stats_integracion['generales']:
            stats = stats_integracion['generales']
            st.metric("🔍 Informes Procesados", f"{stats[1]}/{stats[0]}")
            st.metric("✅ Matches Exitosos", stats[2])
            st.metric("❌ No Encontrados", stats[3])
            if stats[4]:
                st.metric("🎯 Confianza Promedio", f"{stats[4]:.1f}%")
    
    except Exception as e:
        st.warning("⚠️ Error cargando estadísticas de integración")
    
    st.markdown("---")
    
    # ✅ INFORMACIÓN SOBRE PDF CON RADAR
    st.markdown("### 📄 Exportación PDF Avanzada")
    st.info("""
    **📋 Contenido del informe:**
    ✅ Radar chart profesional con datos Wyscout  
    ✅ Evaluaciones completas del scout  
    ✅ Observaciones y recomendaciones  
    ✅ Colores de marca personalizados
    ✅ Formato profesional para presentar  
    
    **🔧 Requiere:** pip install fpdf2 mplsoccer matplotlib
    """)
    
    st.markdown("---")
    
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