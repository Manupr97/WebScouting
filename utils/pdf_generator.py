# utils/pdf_generator.py
"""
Generador de PDFs profesionales para informes de scouting
"""

import os
import re
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from datetime import datetime
import tempfile
from PIL import Image as PILImage
import requests
from io import BytesIO
import pandas as pd
from fpdf import FPDF
from mplsoccer import Radar
import matplotlib.pyplot as plt
import numpy as np
import tempfile
import os
import json

# Obtener el directorio padre para las rutas
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

class PDFGenerator:
    def __init__(self, logo_path="assets/images/identidad_MPR_1.png"):
        self.logo_path = logo_path
        self.primary_color = colors.HexColor("#24282a")
        self.secondary_color = colors.HexColor("#007bff")  # Color de acento
        
        # Estilos personalizados
        self.styles = getSampleStyleSheet()
        
        # Estilo para título principal
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=self.primary_color,
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=self.primary_color,
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['BodyText'],
            fontSize=12,
            textColor=colors.black,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        
        # Estilo para información destacada
        self.styles.add(ParagraphStyle(
            name='InfoBox',
            parent=self.styles['BodyText'],
            fontSize=12,
            textColor=self.primary_color,
            alignment=TA_LEFT,
            leftIndent=20,
            spaceAfter=6
        ))

    def add_header_footer(self, canvas, doc):
        """Agrega header y footer a cada página"""
        canvas.saveState()
        
        # Footer con logo MPR en esquina inferior derecha
        if os.path.exists(self.logo_path):
            try:
                # Logo pequeño en esquina inferior derecha
                logo_size = 0.8 * inch  # Tamaño pequeño
                x_position = doc.width + doc.rightMargin - logo_size - 10
                y_position = 15
                
                canvas.drawImage(self.logo_path, 
                               x_position, 
                               y_position,
                               width=logo_size, 
                               height=logo_size,
                               preserveAspectRatio=True,
                               mask='auto')
            except Exception as e:
                print(f"Error añadiendo logo: {e}")
        
        # Información del footer (centrada, arriba del logo)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        
        # Fecha de generación a la izquierda
        canvas.drawString(doc.leftMargin, 
                         25, 
                         f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
        
        # Número de página centrado
        canvas.drawCentredString(doc.width / 2 + doc.leftMargin, 
                                25, 
                                f"Página {doc.page}")
        
        canvas.restoreState()
    
    def _extraer_valor_wyscout(self, datos, columnas_posibles, tipo='texto'):
        """
        Extrae un valor de los datos de Wyscout probando múltiples nombres de columna
        """
        # Asegura dict
        if isinstance(datos, pd.Series):
            datos = datos.to_dict()
        if isinstance(datos, pd.DataFrame):
            if len(datos) > 0:
                datos = datos.iloc[0].to_dict()
            else:
                datos = {}
        if not datos:
            return ''
        
        for columna in columnas_posibles:
            if columna in datos and datos[columna] is not None and pd.notna(datos[columna]):
                valor = datos[columna]
                
                # Procesar según el tipo
                if tipo == 'edad':
                    try:
                        return str(int(float(valor)))
                    except:
                        return str(valor)
                
                elif tipo == 'altura':
                    try:
                        altura_num = float(valor)
                        if altura_num > 100:  # está en cm
                            return f"{int(altura_num)}cm"
                        else:  # está en metros
                            return f"{altura_num:.2f}m"
                    except:
                        return str(valor) if valor else ''
                
                elif tipo == 'peso':
                    try:
                        return f"{int(float(valor))}kg"
                    except:
                        return str(valor) if valor else ''
                
                elif tipo == 'valor':
                    return self._formatear_valor_mercado(valor)
                
                elif tipo == 'numero':
                    try:
                        return str(int(float(valor)))
                    except:
                        return str(valor)
                
                else:  # texto
                    return str(valor)
        
        return ''
    
    def _transformar_url_foto_para_pdf(self, url_original):
        """Transforma URL de BeSoccer para obtener máxima calidad"""
        if url_original is None:
            return None
        
        if "cdn.resfu.com" in url_original:
            # Reemplazar cualquier tamaño por 500x
            import re
            url_grande = re.sub(r"size=\d+x", "size=500x", url_original)
            url_grande = url_grande.replace("lossy=1", "lossy=0")
            
            # Si no había size, agregarlo
            if "size=" not in url_grande:
                if "?" in url_grande:
                    url_grande += "&size=500x&lossy=0"
                else:
                    url_grande += "?size=500x&lossy=0"
            
            return url_grande
        
        return url_original
    
    def crear_radar_chart_scout_individual(self, informe_data):
        """
        Crea un radar chart con mplsoccer para el informe individual.
        Soporta métricas con categorías (video_completo) o simples (campo).
        """
        try:

            print("🔍 DEBUG: Iniciando radar con mplsoccer")

            # --- 1. Extraer métricas ---
            metricas_raw = informe_data.get('metricas', {})
            if isinstance(metricas_raw, str):
                try:
                    metricas = json.loads(metricas_raw)
                except json.JSONDecodeError:
                    print("❌ ERROR: No se pudo parsear métricas JSON")
                    return None
            else:
                metricas = metricas_raw

            if not metricas:
                print("⚠ No hay métricas disponibles")
                return None

            # --- 2. Determinar si hay categorías ---
            tiene_categorias = all(k in metricas for k in ['tecnicos', 'tacticos', 'fisicos', 'mentales'])
            params, values = [], []

            if tiene_categorias:
                print("🔍 DEBUG: Radar de informe completo")
                categorias = ['tecnicos', 'tacticos', 'fisicos', 'mentales']
                labels = ['Técnico', 'Táctico', 'Físico', 'Mental']

                for cat, label in zip(categorias, labels):
                    valores = [v for v in metricas.get(cat, {}).values() if isinstance(v, (int, float))]
                    promedio = np.mean(valores) if valores else 5
                    params.append(label)
                    values.append(promedio)
            else:
                print("🔍 DEBUG: Radar de informe campo")
                for i, (k, v) in enumerate(metricas.items()):
                    if isinstance(v, (int, float)) and i < 8:
                        params.append(str(k)[:15])
                        values.append(float(v))

            if not params or not values:
                print("⚠ No hay valores numéricos para radar")
                return None

            # --- 3. Crear radar ---
            low = [0] * len(params)
            high = [10] * len(params)

            radar = Radar(
                params, low, high,
                num_rings=4, ring_width=1, center_circle_radius=1
            )

            fig, ax = radar.setup_axis()
            radar.draw_circles(ax=ax, facecolor="#B8BABC", edgecolor="#24282a")
            radar.draw_radar(
                values, ax=ax,
                kwargs_radar={'facecolor': '#007bff', 'alpha': 0.6},
                kwargs_rings={'facecolor': "#048676", 'alpha': 0.2}
            )
            radar.draw_range_labels(ax=ax, fontsize=12)
            radar.draw_param_labels(ax=ax, fontsize=14, fontweight='bold', color='#24282a')

            # --- 4. Guardar radar ---
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp:
                radar_path = tmp.name
                plt.savefig(radar_path, dpi=150, bbox_inches='tight', facecolor='white')
                plt.close(fig)

            print(f"✅ Radar guardado en {radar_path}")
            return radar_path

        except Exception as e:
            print(f"❌ ERROR Radar mplsoccer: {e}")
            return None
    
    def _dibujar_barra_progreso_pdf(self, pdf, valor, maximo, width=100, height=8, color=None):
        """
        Dibuja una barra de progreso con color dinámico según el valor
        """
        # Calcular porcentaje
        porcentaje = (valor / maximo) * 100 if maximo > 0 else 0
        
        # Color automático si no se especifica
        if color is None:
            if valor >= 7:
                color = (34, 197, 94)  # Verde
            elif valor >= 5:
                color = (251, 191, 36)  # Naranja/Amarillo
            else:
                color = (239, 68, 68)  # Rojo
        
        # Posición actual
        x_start = pdf.get_x()
        y_start = pdf.get_y()
        
        # Fondo de la barra (gris claro)
        pdf.set_fill_color(229, 231, 235)  # Gris claro
        pdf.rect(x_start, y_start, width, height, 'F')
        
        # Borde de la barra
        pdf.set_draw_color(156, 163, 175)  # Gris medio
        pdf.rect(x_start, y_start, width, height, 'D')
        
        # Relleno de progreso
        if porcentaje > 0:
            progress_width = (porcentaje / 100) * width
            pdf.set_fill_color(*color)
            pdf.rect(x_start, y_start, progress_width, height, 'F')
        
        # Texto del valor sobre la barra
        pdf.set_xy(x_start, y_start)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(width, height, f"{valor:.1f}", 0, 0, 'C')
        
        # Restaurar color de texto
        pdf.set_text_color(0, 0, 0)
        
        # Mover el cursor debajo de la barra
        pdf.set_xy(x_start, y_start + height)


    def _dibujar_evaluacion_pdf(self, pdf, informe_data):
        """
        Dibuja la sección de Evaluación Detallada con barras de progreso mejoradas
        """
        # Título de la sección
        pdf.set_font('Helvetica', 'B', 16)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 12, "Evaluación Detallada", 0, 1, 'L')
        pdf.ln(5)
        
        # Obtener métricas
        metricas = informe_data.get('metricas', {})
        if isinstance(metricas, str):
            try:
                import json
                metricas = json.loads(metricas)
            except:
                metricas = {}
        
        tipo_eval = informe_data.get('tipo_evaluacion', 'campo')
        
        if tipo_eval == 'video_completo':
            # === MODO COMPLETO: Categorías con promedios y métricas en línea ===
            categorias_info = {
                'tecnicos': {'nombre': 'Aspectos Técnicos', 'color': (59, 130, 246)},  # Azul
                'tacticos': {'nombre': 'Aspectos Tácticos', 'color': (16, 185, 129)},  # Verde
                'fisicos': {'nombre': 'Aspectos Físicos', 'color': (239, 68, 68)},    # Rojo
                'mentales': {'nombre': 'Aspectos Mentales', 'color': (168, 85, 247)}  # Púrpura
            }
            
            for categoria, info in categorias_info.items():
                valores = metricas.get(categoria, {})
                if not valores:
                    continue
                
                # Calcular promedio
                valores_num = [v for v in valores.values() if isinstance(v, (int, float))]
                if not valores_num:
                    continue
                
                promedio = round(sum(valores_num) / len(valores_num), 1)
                
                # Título de categoría con promedio
                pdf.set_font('Helvetica', 'B', 12)
                pdf.set_text_color(36, 40, 42)
                pdf.cell(100, 8, f"{info['nombre']}:", 0, 0, 'L')
                
                # Valor del promedio
                pdf.set_font('Helvetica', 'B', 14)
                # Color del texto según valor
                if promedio >= 7:
                    pdf.set_text_color(34, 197, 94)
                elif promedio >= 5:
                    pdf.set_text_color(251, 191, 36)
                else:
                    pdf.set_text_color(239, 68, 68)
                
                pdf.cell(30, 8, f"{promedio}/10", 0, 1, 'L')
                
                # Barra de progreso
                self._dibujar_barra_progreso_pdf(pdf, promedio, 10, width=150, height=10)
                pdf.ln(3)
                
                # Métricas individuales en línea horizontal
                pdf.set_font('Helvetica', '', 9)
                pdf.set_text_color(75, 85, 99)
                
                # Construir línea de métricas
                metricas_texto = []
                for nombre_metrica, valor in valores.items():
                    if isinstance(valor, (int, float)):
                        # Limpiar nombre de métrica
                        nombre_limpio = nombre_metrica.replace('_', ' ').title()
                        metricas_texto.append(f"{nombre_limpio}: {valor}")
                
                # Escribir todas las métricas en una línea
                if metricas_texto:
                    linea_metricas = " | ".join(metricas_texto)
                    pdf.multi_cell(0, 5, linea_metricas, 0, 'L')
                
                # Separador entre categorías
                pdf.ln(3)
                pdf.set_draw_color(229, 231, 235)
                pdf.line(20, pdf.get_y(), 190, pdf.get_y())
                pdf.ln(3)
        
        else:
            # === MODO CAMPO: Cada métrica con su propia barra ===
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(36, 40, 42)
            
            # Contar métricas válidas
            metricas_validas = [(k, v) for k, v in metricas.items() if isinstance(v, (int, float))]
            
            if not metricas_validas:
                pdf.set_font('Helvetica', 'I', 10)
                pdf.cell(0, 8, "No hay métricas disponibles", 0, 1, 'C')
                return
            
            # Mostrar cada métrica
            for i, (nombre, valor) in enumerate(metricas_validas):
                # Limpiar nombre
                nombre_limpio = nombre.replace('_', ' ').title()
                
                # Nombre de la métrica
                pdf.set_font('Helvetica', 'B', 11)
                pdf.set_text_color(36, 40, 42)
                pdf.cell(80, 8, f"{nombre_limpio}:", 0, 0, 'L')
                
                # Valor con color
                pdf.set_font('Helvetica', 'B', 12)
                if valor >= 7:
                    pdf.set_text_color(34, 197, 94)
                elif valor >= 5:
                    pdf.set_text_color(251, 191, 36)
                else:
                    pdf.set_text_color(239, 68, 68)
                
                pdf.cell(30, 8, f"{valor}/10", 0, 1, 'L')
                
                # Barra de progreso
                self._dibujar_barra_progreso_pdf(pdf, valor, 10, width=120, height=8)
    
    def limpiar_texto_para_pdf(self, texto):
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
    
    def generar_informe_pdf(self, informe_data, jugador_data, datos_wyscout=None, radar_path=None):
        """
        Genera un PDF para un informe individual de scouting
        Acepta datos_wyscout que en realidad pueden ser datos de BeSoccer.
        """
        try:
            from fpdf import FPDF
            import tempfile
            import os
            from datetime import datetime
            from PIL import Image as PILImage
            import requests
            from io import BytesIO

            # --- Datos del jugador con BeSoccer ---
            datos_besoccer = datos_wyscout or {}

            jugador_nombre = self.limpiar_texto_para_pdf(
                jugador_data.get("nombre_completo", informe_data.get("jugador_nombre", "N/A"))
            )

            equipo = self.limpiar_texto_para_pdf(
                datos_besoccer.get("equipo_actual", jugador_data.get("equipo", "N/A"))
            )

            edad = datos_besoccer.get("edad", jugador_data.get("edad", "N/A"))
            nacionalidad = self.limpiar_texto_para_pdf(
                datos_besoccer.get("nacionalidad", jugador_data.get("nacionalidad", "N/A"))
            )

            altura = datos_besoccer.get("altura", jugador_data.get("altura", "N/A"))
            peso = datos_besoccer.get("peso", jugador_data.get("peso", "N/A"))

            liga = self.limpiar_texto_para_pdf(
                datos_besoccer.get("liga_actual", jugador_data.get("liga", "N/A"))
            )

            valor_mercado = datos_besoccer.get("valor_mercado", jugador_data.get("valor_mercado", "N/A"))
            if valor_mercado:
                valor_mercado = valor_mercado.replace(" M€", " Mill. EUR").replace(" K€", " mil EUR")
                valor_mercado = self.limpiar_texto_para_pdf(valor_mercado)

            elo = datos_besoccer.get("elo", jugador_data.get("elo_besoccer", "N/A"))

            pos_principal = self.limpiar_texto_para_pdf(
                datos_besoccer.get("posicion_principal", jugador_data.get("posicion", "N/A"))
            )

            pos_secundaria = self.limpiar_texto_para_pdf(
                datos_besoccer.get("posicion_secundaria", jugador_data.get("posicion_secundaria", ""))
            )

            pie_preferido = self.limpiar_texto_para_pdf(
                datos_besoccer.get("pie_preferido", jugador_data.get("pie_dominante", "N/A"))
            )

            posicion_completa = (
                f"{pos_principal} ({pos_secundaria})" if pos_secundaria else pos_principal
            )

            scout = informe_data.get("scout_usuario", "N/A")
            fecha_partido = informe_data.get("fecha_creacion", datetime.now().strftime("%Y-%m-%d"))[:10]
            nota_general = informe_data.get("nota_general", 0)

            # Crear PDF
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # Logo (si existe)
            logo_path = 'assets/images/identidad_MPR_1.png'
            if os.path.exists(logo_path):
                try:
                    pdf.image(logo_path, x=185, y=10, w=15)
                except:
                    pass

            # === HEADER ===
            pdf.set_font('Helvetica', 'B', 20)
            pdf.set_text_color(36, 40, 42)
            pdf.cell(0, 12, 'INFORME INDIVIDUAL DE SCOUTING', 0, 1, 'C')

            # Línea decorativa
            pdf.set_draw_color(102, 126, 234)
            pdf.set_line_width(0.5)
            pdf.line(20, pdf.get_y(), 190, pdf.get_y())
            pdf.ln(8)

            # === FOTO Y DATOS (LADO A LADO) ===
            y_inicio = pdf.get_y()
            x_foto = 25
            ancho_foto = 40
            x_datos = x_foto + ancho_foto + 10

            # Procesar y mostrar foto
            imagen_url = jugador_data.get('imagen_url', '') or informe_data.get('imagen_url', '')
            if imagen_url:
                try:
                    # Ajuste de calidad para fotos BeSoccer
                    if "cdn.resfu.com" in imagen_url:
                        imagen_url = self._transformar_url_foto_para_pdf(imagen_url)

                    if imagen_url.startswith('http'):
                        response = requests.get(imagen_url, timeout=10)
                        img = PILImage.open(BytesIO(response.content))
                    else:
                        img = PILImage.open(imagen_url)

                    # Hacer cuadrada y redimensionar
                    ancho, alto = img.size
                    if ancho != alto:
                        lado = min(ancho, alto)
                        left = (ancho - lado) // 2
                        top = (alto - lado) // 2
                        img = img.crop((left, top, left + lado, top + lado))
                    img = img.resize((500, 500), PILImage.Resampling.LANCZOS)

                    # Convertir a RGB si es necesario
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = PILImage.new('RGB', img.size, (255, 255, 255))
                        img = img.convert('RGBA') if img.mode == 'P' else img
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                        img = rgb_img

                    # Guardar temporalmente
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_img:
                        temp_path = temp_img.name
                        img.save(temp_img, 'JPEG', quality=95)
                    pdf.image(temp_path, x=x_foto, y=y_inicio, w=ancho_foto, h=ancho_foto)
                    os.unlink(temp_path)
                except Exception as e:
                    print(f"⚠️ Error con la imagen: {e}")
            else:
                # Placeholder si no hay imagen
                pdf.set_fill_color(240, 240, 240)
                pdf.rect(x_foto, y_inicio, ancho_foto, ancho_foto, 'F')
                pdf.set_draw_color(200, 200, 200)
                pdf.rect(x_foto, y_inicio, ancho_foto, ancho_foto, 'D')
                pdf.set_font('Helvetica', '', 20)
                pdf.set_text_color(180, 180, 180)
                pdf.set_xy(x_foto, y_inicio + (ancho_foto / 2) - 5)
                pdf.cell(ancho_foto, 10, 'USER', 0, 0, 'C')

            # Datos a la derecha
            pdf.set_xy(x_datos, y_inicio)
            pdf.set_font('Helvetica', 'B', 16)
            pdf.set_text_color(36, 40, 42)
            pdf.cell(0, 8, jugador_nombre, 0, 1)

            pdf.set_x(x_datos)
            pdf.set_font('Helvetica', '', 12)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 6, f"{equipo} | {posicion_completa} | Pie: {pie_preferido}", 0, 1)

            pdf.set_x(x_datos)
            pdf.set_font('Helvetica', '', 10)
            linea_fisica = []
            if edad: linea_fisica.append(f"{edad} años")
            if nacionalidad: linea_fisica.append(nacionalidad)
            if altura and peso: linea_fisica.append(f"{altura}cm / {peso}kg")
            pdf.cell(0, 5, " | ".join(linea_fisica), 0, 1)

            pdf.set_x(x_datos)
            linea_extra = []
            if liga: linea_extra.append(liga)
            if valor_mercado: linea_extra.append(f"Valor: {valor_mercado}")
            if elo: linea_extra.append(f"ELO: {elo}")
            pdf.set_font('Helvetica', 'I', 9)
            pdf.cell(0, 5, " | ".join(linea_extra), 0, 1)

            # Mover Y debajo del bloque foto/datos
            pdf.set_y(y_inicio + ancho_foto + 10)

            # Datos del partido
            pdf.set_font('Helvetica', '', 10)
            pdf.set_text_color(60, 60, 60)
            partido_texto = f"{informe_data.get('equipo_local', 'N/A')} vs {informe_data.get('equipo_visitante', 'N/A')}"
            pdf.cell(0, 5, partido_texto, 0, 1, 'C')
            pdf.cell(0, 5, f"Fecha: {fecha_partido} | Scout: {scout}", 0, 1, 'C')
            tipo_eval = 'Análisis con Video' if informe_data.get('tipo_evaluacion') == 'video_completo' else 'Evaluación en Campo'
            pdf.cell(0, 5, f"{tipo_eval} | {informe_data.get('minutos_observados', 90)} minutos observados", 0, 1, 'C')

            pdf.ln(10)

            # NOTA GENERAL
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(36, 40, 42)
            pdf.cell(0, 8, f"NOTA GENERAL: {nota_general}/10", 0, 1, 'C')

            # Radar chart (si existe)
            radar_path = self.crear_radar_chart_scout_individual(informe_data)
            if radar_path and os.path.exists(radar_path):
                ancho_radar = 170
                x_radar = (pdf.w - ancho_radar) / 2
                pdf.image(radar_path, x=x_radar, y=pdf.get_y() + 5, w=ancho_radar, h=ancho_radar)
                pdf.set_y(pdf.get_y() + ancho_radar + 15)
                os.unlink(radar_path)
            else:
                print("⚠️ Radar chart no generado.")

            # Segunda página con evaluación detallada
            pdf.add_page()

            # Evaluación Detallada
            # Llamada corregida - pasamos informe_data completo
            self._dibujar_evaluacion_pdf(pdf, informe_data)

            # Observaciones del scout
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 10, "Observaciones del Scout", 0, 1)
            pdf.set_font('Helvetica', '', 10)
            pdf.multi_cell(0, 6, informe_data.get('observaciones', 'Sin observaciones'))

            return bytes(pdf.output(dest='S'))
        except Exception as e:
            print(f"❌ Error generando PDF: {e}")
            return None
    
    def _get_foto_element(self, imagen_url):
        """Obtiene la foto del jugador como elemento para el PDF"""
        if not imagen_url:
            return None
        
        try:
            if imagen_url.startswith('http'):
                # Descargar imagen
                response = requests.get(imagen_url, timeout=5)
                img = PILImage.open(BytesIO(response.content))
            else:
                # Imagen local
                img = PILImage.open(imagen_url)
            
            # Redimensionar a tamaño apropiado
            img.thumbnail((150, 150), PILImage.Resampling.LANCZOS)
            
            # Guardar temporalmente
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
            img.save(temp_img.name, 'PNG')
            
            # Crear elemento Image de reportlab
            return Image(temp_img.name, width=1.5*inch, height=1.5*inch)
            
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            return None
    
    def _get_foto_element_mejorada(self, imagen_url):
        """Obtiene la foto del jugador mejorada para el PDF - Tamaño grande y alta calidad"""
        if not imagen_url:
            return None
        
        try:
            # Transformar URL para obtener mejor calidad
            if "cdn.resfu.com" in imagen_url:
                imagen_url = self._transformar_url_foto_para_pdf(imagen_url)
            
            if imagen_url.startswith('http'):
                # Descargar imagen con timeout mayor
                response = requests.get(imagen_url, timeout=10)
                img = PILImage.open(BytesIO(response.content))
            else:
                # Imagen local
                img = PILImage.open(imagen_url)
            
            # Procesar imagen para hacerla cuadrada (crop centrado)
            ancho, alto = img.size
            if ancho != alto:
                # Calcular el tamaño del cuadrado (el lado menor)
                lado = min(ancho, alto)
                
                # Calcular las coordenadas para centrar el crop
                left = (ancho - lado) // 2
                top = (alto - lado) // 2
                right = left + lado
                bottom = top + lado
                
                # Hacer el crop
                img = img.crop((left, top, right, bottom))
            
            # Redimensionar a tamaño grande (300x300) con alta calidad
            img = img.resize((300, 300), PILImage.Resampling.LANCZOS)
            
            # Convertir a RGB si es necesario (para evitar problemas con PNG transparentes)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = PILImage.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Guardar temporalmente con alta calidad
            temp_img = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
            img.save(temp_img.name, 'JPEG', quality=95)
            
            # Crear elemento Image de reportlab con tamaño grande
            return Image(temp_img.name, width=2.5*inch, height=2.5*inch)
            
        except Exception as e:
            print(f"Error cargando imagen mejorada: {e}")
            return None
    
    def _formatear_valor_mercado(self, valor_raw):
        """Formatea el valor de mercado de manera legible"""
        try:
            valor_str = str(valor_raw).upper().strip()
            
            # Si ya tiene formato (180M, 50K, etc)
            if 'M' in valor_str:
                numero = valor_str.split('M')[0].strip()
                return f"{numero}M EUR"
            elif 'K' in valor_str:
                numero = valor_str.split('K')[0].strip()
                return f"{numero}K EUR"
            else:
                # Intentar parsear como número
                valor_limpio = valor_str.replace('€', '').replace('EUR', '').replace(',', '').replace('.', '').strip()
                if valor_limpio.isdigit():
                    valor_num = float(valor_limpio)
                    if valor_num >= 1000000:
                        return f"{valor_num/1000000:.1f}M EUR"
                    elif valor_num >= 1000:
                        return f"{int(valor_num/1000)}K EUR"
                    else:
                        return f"{int(valor_num)} EUR"
                else:
                    return valor_str.replace('€', 'EUR')
        except:
            return "N/A"
    
    def _crear_barra_progreso(self, valor, maximo, width=200, height=20):
        """Crea una barra de progreso visual para el PDF"""
        from reportlab.graphics.shapes import Drawing
        from reportlab.graphics import shapes
        
        drawing = Drawing(width, height)
        
        # Calcular porcentaje
        porcentaje = (valor / maximo) * 100 if maximo > 0 else 0
        
        # Color según el valor
        if porcentaje >= 80:
            color = colors.green
        elif porcentaje >= 60:
            color = colors.orange
        else:
            color = colors.red
        
        # Fondo de la barra
        drawing.add(shapes.Rect(0, 0, width, height, 
                               fillColor=colors.lightgrey, 
                               strokeColor=colors.grey,
                               strokeWidth=1))
        
        # Progreso
        if porcentaje > 0:
            progress_width = (porcentaje / 100) * width
            drawing.add(shapes.Rect(0, 0, progress_width, height,
                                   fillColor=color,
                                   strokeColor=None,
                                   strokeWidth=0))
        
        # Texto del porcentaje
        drawing.add(shapes.String(width/2, height/2 - 4, f"{porcentaje:.0f}%",
                                 textAnchor='middle',
                                 fontSize=10,
                                 fillColor=colors.white if porcentaje > 50 else colors.black))
        
        return drawing
    
    def _get_color_nota(self, nota):
        """Devuelve el color según la nota"""
        if nota >= 8:
            return colors.green
        elif nota >= 6:
            return colors.orange
        else:
            return colors.red
        
    def _crear_radar_simple(self, informe_data):
        """
        Crea un radar chart simple como fallback
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
            
            # Extraer promedios del informe
            metricas_json = informe_data.get('metricas', {})
            if isinstance(metricas_json, str):
                try:
                    import json
                    metricas_json = json.loads(metricas_json)
                except:
                    metricas_json = {}
            
            # Obtener valores
            valores = []
            etiquetas = ['Técnico', 'Táctico', 'Físico', 'Mental']
            
            if isinstance(metricas_json, dict) and 'promedios' in metricas_json:
                valores = [
                    metricas_json['promedios'].get('tecnicos', 5),
                    metricas_json['promedios'].get('tacticos', 5),
                    metricas_json['promedios'].get('fisicos', 5),
                    metricas_json['promedios'].get('mentales', 5)
                ]
            else:
                # Usar nota general como base
                nota = float(informe_data.get('nota_general', 5))
                valores = [nota, nota, nota, nota]
            
            # Configurar el radar
            angles = np.linspace(0, 2 * np.pi, len(etiquetas), endpoint=False).tolist()
            valores += valores[:1]  # Cerrar el polígono
            angles += angles[:1]
            
            # Crear figura
            fig, ax = plt.subplots(figsize=(6, 6), subplot_kw=dict(projection='polar'))
            
            # Configurar el área del gráfico
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            
            # Dibujar el radar
            ax.plot(angles, valores, 'o-', linewidth=2, color='#667eea', markersize=8)
            ax.fill(angles, valores, alpha=0.25, color='#667eea')
            
            # Configurar las etiquetas
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(etiquetas, size=11)
            
            # Configurar el rango
            ax.set_ylim(0, 10)
            ax.set_yticks([2, 4, 6, 8, 10])
            ax.set_yticklabels(['2', '4', '6', '8', '10'], size=9)
            ax.grid(True, linestyle='--', alpha=0.7)
            
            # Añadir valores
            for angle, valor, etiqueta in zip(angles[:-1], valores[:-1], etiquetas):
                ax.text(angle, valor + 0.3, f'{valor:.1f}', 
                       horizontalalignment='center', verticalalignment='center',
                       size=10, weight='bold')
            
            plt.tight_layout()
            
            # Guardar
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_path = tmp_file.name
            
            plt.savefig(tmp_path, dpi=150, bbox_inches='tight', facecolor='white')
            plt.close()
            
            return tmp_path
            
        except Exception as e:
            print(f"Error creando radar simple: {e}")
            return None