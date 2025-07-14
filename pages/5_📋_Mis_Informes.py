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

def crear_radar_chart_jugador(datos_wyscout, nombre_jugador):
    """
    Versión corregida según documentación oficial de mplsoccer
    """
    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from mplsoccer import Radar
        import tempfile
        import sys
        import os
        
        print(f"🔍 Generando radar para {nombre_jugador}")
        
        # Importar extractor
        current_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(current_dir)
        utils_path = os.path.join(parent_dir, 'utils')
        if utils_path not in sys.path:
            sys.path.append(utils_path)
        
        try:
            from wyscout_data_extractor_personalizado import WyscoutExtractorPersonalizado
            extractor = WyscoutExtractorPersonalizado()
            
            equipo = None
            if isinstance(datos_wyscout, dict):
                equipo = datos_wyscout.get('equipo')
            
            datos_reales = extractor.obtener_datos_completos_jugador(nombre_jugador, equipo)
            
            if datos_reales:
                print(f"✅ Datos encontrados en Wyscout")
                usar_datos_wyscout = True
            else:
                print(f"⚠️ Usando datos estimados")
                datos_reales = datos_wyscout if isinstance(datos_wyscout, dict) else {}
                usar_datos_wyscout = False
                
        except ImportError:
            print(f"⚠️ Extractor no disponible")
            datos_reales = datos_wyscout if isinstance(datos_wyscout, dict) else {}
            usar_datos_wyscout = False
        
        # === CONFIGURACIÓN SEGÚN DOCUMENTACIÓN OFICIAL ===
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
        
        # Usar min_range y max_range como en la documentación
        min_range = [60, 30, 20, 0, 0, 0, 0, 0]
        max_range = [95, 70, 80, 1.2, 0.8, 1.0, 10, 5]
        
        # === EXTRAER VALORES ===
        if usar_datos_wyscout and 'precision_pases' in datos_reales:
            # Datos reales de Wyscout
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
            equipo_info = str(datos_reales.get('equipo', 'N/A'))
            posicion_info = str(datos_reales.get('posicion', 'N/A'))
            fuente = "Wyscout"
        else:
            # Datos estimados
            print("📊 Usando datos estimados")
            valores_jugador = [78, 52, 42, 0.3, 0.2, 0.25, 3.5, 2.1]
            equipo_info = str(datos_reales.get('equipo', 'N/A')) if isinstance(datos_reales, dict) else 'N/A'
            posicion_info = str(datos_reales.get('posicion', 'N/A')) if isinstance(datos_reales, dict) else 'N/A'
            fuente = "Estimación"
        
        # Asegurar valores en rangos
        for i, (valor, min_val, max_val) in enumerate(zip(valores_jugador, min_range, max_range)):
            valores_jugador[i] = max(min_val, min(max_val, valor))
        
        print(f"📊 Valores: {[f'{v:.1f}' for v in valores_jugador]}")
        
        # === CREAR RADAR SEGÚN DOCUMENTACIÓN ===
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
        
        # Colores
        color_principal = '#1e3a8a'
        color_secundario = '#3b82f6'
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
                  c='#ef4444', s=60, zorder=5, 
                  edgecolors='white', linewidth=2)
        
        # Etiquetas
        range_labels = radar.draw_range_labels(ax=ax, fontsize=10)
        param_labels = radar.draw_param_labels(ax=ax, fontsize=11)
        
        # Título
        fig.suptitle(f'{equipo_info} - {nombre_jugador}', 
                    fontsize=16, color=color_principal, 
                    fontweight='bold', y=0.95)
        
        # Subtítulo
        plt.figtext(0.5, 0.91, 
                   f'{posicion_info} | Fuente: {fuente}', 
                   ha='center', fontsize=12, color='#64748b')
        
        # Footer
        plt.figtext(0.5, 0.02, 
                   'Sistema de Scouting Profesional', 
                   ha='center', fontsize=10, color='#94a3b8')
        
        # Guardar
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_path = tmp_file.name
        
        plt.savefig(tmp_path, dpi=300, bbox_inches='tight', 
                   facecolor='white', edgecolor='none')
        plt.close()
        
        print(f"✅ Radar generado exitosamente")
        return tmp_path
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

# === FUNCIÓN PDF MEJORADA ===
# REEMPLAZA la función generar_pdf_con_radar con esta versión final mejorada

def generar_pdf_con_radar(informe_data, datos_wyscout=None, user_info=None):
    """
    PDF final con colores de marca y mejoras visuales
    """
    try:
        from fpdf import FPDF
        import tempfile
        import os
        
        print(f"📄 Generando PDF profesional para {informe_data['jugador_nombre']}...")
        
        scout_nombre = user_info['nombre'] if user_info else 'Scout'
        
        # === CREAR RADAR CHART ===
        radar_path = None
        try:
            print("🎯 Creando radar chart...")
            radar_path = crear_radar_chart_jugador(datos_wyscout, informe_data['jugador_nombre'])
            
            if radar_path and os.path.exists(radar_path):
                print("✅ Radar chart creado exitosamente")
        except Exception as e:
            print(f"❌ Error creando radar: {str(e)}")
        
        # === CREAR PDF ===
        pdf = FPDF()
        
        # ==================== PÁGINA 1: INFORMACIÓN Y RADAR ====================
        pdf.add_page()
        
        # === HEADER CON COLORES DE MARCA ===
        pdf.set_font('Arial', 'B', 22)
        pdf.set_text_color(36, 40, 42)  # #24282a
        pdf.cell(0, 15, 'INFORME DE SCOUTING PROFESIONAL', 0, 1, 'C')
        
        # Línea decorativa con color de marca
        pdf.set_fill_color(0, 123, 191)  # #007bbf
        pdf.rect(15, 25, 180, 3, 'F')
        pdf.ln(15)
        
        # === INFORMACIÓN DEL JUGADOR ===
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(0, 123, 191)  # #007bbf
        pdf.cell(0, 12, f"{informe_data['jugador_nombre']} - {informe_data['equipo']}", 0, 1, 'C')
        pdf.ln(8)
        
        # Información básica con mejor diseño
        pdf.set_font('Arial', '', 12)
        pdf.set_text_color(36, 40, 42)  # #24282a
        
        info_items = [
            ("Posición:", informe_data['posicion']),
            ("Scout:", scout_nombre),
            ("Fecha:", informe_data['fecha_creacion'][:10] if informe_data['fecha_creacion'] else 'N/A'),
            ("Nota General:", f"{informe_data['nota_general']}/10"),
            ("Potencial:", informe_data.get('potencial', 'N/A')),
            ("Min Observados:", f"{informe_data.get('minutos_observados', 90)}'")
        ]
        
        # Layout en 2 columnas con fondo alternado
        for i in range(0, len(info_items), 2):
            y_pos = pdf.get_y()
            
            # Fondo alternado sutil
            if i % 4 == 0:
                pdf.set_fill_color(248, 249, 250)  # Gris muy claro
                pdf.rect(15, y_pos - 1, 180, 9, 'F')
            
            # Columna izquierda
            if i < len(info_items):
                label, value = info_items[i]
                pdf.set_xy(25, y_pos)
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(0, 123, 191)  # #007bbf
                pdf.cell(35, 8, label, 0, 0)
                pdf.set_font('Arial', '', 11)
                pdf.set_text_color(36, 40, 42)  # #24282a
                pdf.cell(50, 8, str(value), 0, 0)
            
            # Columna derecha
            if i + 1 < len(info_items):
                label, value = info_items[i + 1]
                pdf.set_xy(115, y_pos)
                pdf.set_font('Arial', 'B', 11)
                pdf.set_text_color(0, 123, 191)  # #007bbf
                pdf.cell(35, 8, label, 0, 0)
                pdf.set_font('Arial', '', 11)
                pdf.set_text_color(36, 40, 42)  # #24282a
                pdf.cell(50, 8, str(value), 0, 0)
            
            pdf.ln(10)
        
        pdf.ln(10)
        
        # === RADAR CHART ===
        if radar_path and os.path.exists(radar_path):
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(0, 123, 191)  # #007bbf
            pdf.cell(0, 8, 'ANÁLISIS RADAR - PERFIL TÉCNICO-TÁCTICO', 0, 1, 'C')
            pdf.ln(5)
            
            try:
                # Radar centrado
                page_width = 210
                image_width = 160
                x_centered = (page_width - image_width) / 2
                
                pdf.image(radar_path, x=x_centered, y=pdf.get_y(), w=image_width)
                
                os.unlink(radar_path)
                
            except Exception as e:
                print(f"⚠️ Error insertando radar: {str(e)}")

        pdf.image(r'C:\Users\manue\OneDrive\Escritorio\WebScouting\identidad_MPR_1.png', x=170, y=280, w=25)
        
        # ==================== PÁGINA 2: EVALUACIONES Y OBSERVACIONES ====================
        pdf.add_page()
        
        # === HEADER PÁGINA 2 ===
        pdf.set_font('Arial', 'B', 18)
        pdf.set_text_color(36, 40, 42)  # #24282a
        pdf.cell(0, 12, f"EVALUACIÓN DETALLADA - {informe_data['jugador_nombre']}", 0, 1, 'C')
        
        # Línea decorativa
        pdf.set_fill_color(0, 123, 191)  # #007bbf
        pdf.rect(15, 25, 180, 2, 'F')
        pdf.ln(15)
        
        # === EVALUACIONES POR CATEGORÍAS MEJORADAS ===
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 123, 191)  # #007bbf
        pdf.cell(0, 8, 'EVALUACIÓN POR CATEGORÍAS', 0, 1, 'C')
        pdf.ln(8)
        
        categorias = {
            'TÉCNICO': ['control_balon', 'primer_toque', 'pase_corto', 'pase_largo', 'finalizacion', 'regate'],
            'TÁCTICO': ['vision_juego', 'posicionamiento', 'marcaje', 'pressing', 'transiciones'],
            'FÍSICO': ['velocidad', 'resistencia', 'fuerza', 'salto', 'agilidad'],
            'MENTAL': ['concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision']
        }
        
        for i, (categoria, campos) in enumerate(categorias.items()):
            try:
                valores = [informe_data.get(campo, 0) for campo in campos if campo in informe_data]
                promedio = sum(valores) / len(valores) if valores else 0
                
                # Fondo alternado para las categorías
                y_pos = pdf.get_y()
                if i % 2 == 0:
                    pdf.set_fill_color(248, 249, 250)
                    pdf.rect(15, y_pos - 1, 180, 12, 'F')
                
                # Color según promedio con tu paleta
                if promedio >= 8:
                    color_barra = (0, 123, 191)      # Tu azul principal
                elif promedio >= 6:
                    color_barra = (40, 167, 69)      # Verde
                elif promedio >= 4:
                    color_barra = (255, 193, 7)      # Amarillo
                else:
                    color_barra = (220, 53, 69)      # Rojo
                
                # Etiqueta de categoría
                pdf.set_font('Arial', 'B', 13)
                pdf.set_text_color(36, 40, 42)  # #24282a
                pdf.cell(50, 12, f"{categoria}:", 0, 0)
                
                # Barra visual mejorada
                pdf.set_fill_color(*color_barra)
                barra_width = (promedio / 10) * 100
                pdf.rect(65, pdf.get_y() + 3, barra_width, 6, 'F')
                
                # Borde de la barra
                pdf.set_draw_color(36, 40, 42)  # #24282a
                pdf.set_line_width(0.5)
                pdf.rect(65, pdf.get_y() + 3, 100, 6)
                
                # Valor numérico
                pdf.set_font('Arial', 'B', 13)
                pdf.set_text_color(0, 123, 191)  # #007bbf
                pdf.set_xy(170, pdf.get_y())
                pdf.cell(30, 12, f"{promedio:.1f}/10", 0, 1)
                
            except Exception as e:
                print(f"Error en categoría {categoria}: {str(e)}")
                pdf.cell(0, 12, f"{categoria}: Error", 0, 1)
        
        pdf.ln(10)
        
        # === OBSERVACIONES MEJORADAS ===
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(0, 123, 191)  # #007bbf
        pdf.cell(0, 8, 'OBSERVACIONES DEL SCOUT', 0, 1, 'C')
        pdf.ln(5)
        
        observaciones = [
            ("FORTALEZAS IDENTIFICADAS:", informe_data.get('fortalezas', 'No especificadas')),
            ("ÁREAS DE MEJORA:", informe_data.get('debilidades', 'No especificadas')),
            ("OBSERVACIONES ADICIONALES:", informe_data.get('observaciones', 'Sin observaciones'))
        ]
        
        for titulo, texto in observaciones:
            pdf.set_font('Arial', 'B', 12)
            pdf.set_text_color(36, 40, 42)  # #24282a
            pdf.cell(0, 8, titulo, 0, 1)
            
            pdf.set_font('Arial', '', 10)
            pdf.set_text_color(80, 80, 80)  # Gris para el texto
            
            # Texto con wrapping
            if texto and len(str(texto)) > 2:
                palabras = str(texto).split(' ')
                linea_actual = ''
                
                for palabra in palabras:
                    if len(linea_actual + ' ' + palabra) <= 90:
                        linea_actual += (' ' + palabra if linea_actual else palabra)
                    else:
                        if linea_actual:
                            pdf.cell(0, 5, linea_actual, 0, 1)
                        linea_actual = palabra
                
                if linea_actual:
                    pdf.cell(0, 5, linea_actual, 0, 1)
            
            pdf.ln(5)
        
        # === RECOMENDACIÓN FINAL MEJORADA ===
        pdf.ln(10)
        recomendacion_raw = informe_data.get('recomendacion', 'Sin recomendación')
        
        # Limpiar recomendación (quitar guiones bajos y mejorar formato)
        recomendacion = recomendacion_raw.replace('_', ' ').title()
        
        # Color según recomendación con tu paleta
        if 'contratar' in recomendacion.lower():
            color_recom = (0, 123, 191)       # Tu azul principal
        elif any(word in recomendacion.lower() for word in ['interes', 'seguir', 'observando']):
            color_recom = (255, 193, 7)       # Amarillo
        elif 'descartar' in recomendacion.lower():
            color_recom = (220, 53, 69)       # Rojo
        else:
            color_recom = (36, 40, 42)        # Tu gris principal
        
        # Caja de recomendación con gradiente simulado
        pdf.set_fill_color(*color_recom)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 16)
        
        y_pos = pdf.get_y()
        # Sombra sutil
        pdf.set_fill_color(0, 0, 0)
        pdf.rect(17, y_pos + 2, 180, 20, 'F')
        # Caja principal
        pdf.set_fill_color(*color_recom)
        pdf.rect(15, y_pos, 180, 20, 'F')
        
        pdf.set_xy(15, y_pos + 5)
        pdf.cell(180, 10, f"RECOMENDACIÓN FINAL: {recomendacion.upper()}", 0, 1, 'C')
        
        # === LOGO Y FOOTER MEJORADO ===
        pdf.ln(15)
        
        # Información del footer
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(100, 100, 100)
        
        import datetime
        fecha_actual = datetime.datetime.now().strftime("%d/%m/%Y %H:%M")
        pdf.cell(0, 5, f"Informe generado el {fecha_actual} por {scout_nombre}", 0, 1, 'C')
        
        # Línea separadora
        pdf.set_draw_color(0, 123, 191)  # #007bbf
        pdf.line(50, pdf.get_y() + 3, 160, pdf.get_y() + 3)
        
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(0, 123, 191)  # #007bbf
        pdf.cell(0, 5, 'SISTEMA DE SCOUTING PROFESIONAL', 0, 1, 'C')
        
        # Placeholder para logo (esquina inferior derecha)
        # Si tienes un logo, descomenta estas líneas:
        # try:
        pdf.image(r'C:\Users\manue\OneDrive\Escritorio\WebScouting\identidad_MPR_1.png', x=170, y=280, w=25)
        # except:
        #     # Texto como logo temporal
        pdf.set_xy(160, 275)
        pdf.set_font('Arial', 'B', 8)
        pdf.set_text_color(0, 123, 191)
        
        # === GUARDAR PDF ===
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            tmp_path = tmp_file.name
        
        pdf.output(tmp_path)
        
        with open(tmp_path, 'rb') as f:
            pdf_bytes = f.read()
        
        os.unlink(tmp_path)
        
        print("✅ PDF final con marca personalizada generado exitosamente")
        return pdf_bytes, "application/pdf", "pdf"
        
    except ImportError:
        print("❌ fpdf2 no está instalado")
        return generar_html_fallback_simple(informe_data, datos_wyscout)
        
    except Exception as e:
        print(f"❌ Error generando PDF: {str(e)}")
        return generar_html_fallback_simple(informe_data, datos_wyscout)

# ✅ FUNCIÓN HTML FALLBACK
def generar_html_fallback_simple(informe_data, datos_wyscout=None):
    """Genera HTML simple como fallback"""
    
    # Calcular promedios
    promedio_tecnico = (informe_data['control_balon'] + informe_data['primer_toque'] + 
                      informe_data['pase_corto'] + informe_data['pase_largo'] + 
                      informe_data['finalizacion'] + informe_data['regate']) / 6
    
    promedio_tactico = (informe_data['vision_juego'] + informe_data['posicionamiento'] + 
                      informe_data['marcaje'] + informe_data['pressing'] + 
                      informe_data['transiciones']) / 5
    
    promedio_fisico = (informe_data['velocidad'] + informe_data['resistencia'] + 
                     informe_data['fuerza'] + informe_data['salto'] + 
                     informe_data['agilidad']) / 5
    
    promedio_mental = (informe_data['concentracion'] + informe_data['liderazgo'] + 
                     informe_data['comunicacion'] + informe_data['presion'] + 
                     informe_data['decision']) / 5
    
    # Datos Wyscout
    wyscout_section = ""
    if datos_wyscout:
        wyscout_section = f"""
        <div class="section">
            <h2>DATOS ESTADISTICOS (WYSCOUT)</h2>
            <table>
                <tr><td><strong>Partidos:</strong></td><td>{datos_wyscout.get('partidos_jugados', 'N/A')}</td></tr>
                <tr><td><strong>Goles:</strong></td><td>{datos_wyscout.get('goles', 'N/A')}</td></tr>
                <tr><td><strong>Asistencias:</strong></td><td>{datos_wyscout.get('asistencias', 'N/A')}</td></tr>
                <tr><td><strong>Edad:</strong></td><td>{datos_wyscout.get('edad', 'N/A')} años</td></tr>
            </table>
        </div>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Informe de Scouting - {informe_data['jugador_nombre']}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.5; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; text-align: center; border-radius: 8px; margin-bottom: 20px; }}
            .section {{ background: white; margin: 15px 0; padding: 20px; border: 2px solid #667eea; border-radius: 8px; }}
            table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            td {{ padding: 10px; border: 1px solid #ddd; }}
            tr:nth-child(even) {{ background-color: #f8f9fa; }}
            h2 {{ color: #667eea; margin-top: 0; border-bottom: 2px solid #667eea; padding-bottom: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>INFORME DE SCOUTING PROFESIONAL</h1>
            <h2>{informe_data['jugador_nombre']}</h2>
            <p>Scout: {current_user['nombre']} | Fecha: {informe_data['fecha_creacion'][:10] if informe_data['fecha_creacion'] else 'N/A'}</p>
        </div>
        
        <div class="section">
            <h2>RESUMEN POR CATEGORIAS</h2>
            <table>
                <tr><td><strong>TECNICO:</strong></td><td>{promedio_tecnico:.1f}/10</td></tr>
                <tr><td><strong>TACTICO:</strong></td><td>{promedio_tactico:.1f}/10</td></tr>
                <tr><td><strong>FISICO:</strong></td><td>{promedio_fisico:.1f}/10</td></tr>
                <tr><td><strong>MENTAL:</strong></td><td>{promedio_mental:.1f}/10</td></tr>
            </table>
        </div>
        
        {wyscout_section}
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
                            file_bytes, mime_type, extension = generar_pdf_con_radar(
                                informe_data, 
                                datos_wyscout, 
                                current_user  # Pasar current_user como parámetro
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