from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import os
import tempfile
import base64
import io

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configurar estilos personalizados para el PDF"""
        # Estilo para títulos principales
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f77b4')
        ))
        
        # Estilo para subtítulos
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=20,
            textColor=colors.HexColor('#2c3e50')
        ))
        
        # Estilo para texto normal
        self.styles.add(ParagraphStyle(
            name='CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=12,
            alignment=TA_LEFT
        ))
    
    def generar_informe_jugador(self, jugador_data, comparacion_data=None):
        """Genera un informe PDF completo de un jugador"""
        
        # Convertir Series a dict si es necesario
        if hasattr(jugador_data, 'to_dict'):
            jugador_data = jugador_data.to_dict()
        
        if comparacion_data is not None and hasattr(comparacion_data, 'to_dict'):
            comparacion_data = comparacion_data.to_dict()
        
        # Crear archivo temporal para el PDF
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        
        # Crear documento PDF
        doc = SimpleDocTemplate(
            temp_file.name,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Lista para almacenar el contenido
        story = []
        
        # 1. ENCABEZADO
        self._agregar_encabezado(story, jugador_data)
        
        # 2. INFORMACIÓN PERSONAL Y PROFESIONAL
        self._agregar_info_personal(story, jugador_data)
        
        # 3. ESTADÍSTICAS DE RENDIMIENTO
        self._agregar_estadisticas(story, jugador_data)
        
        # 4. ANÁLISIS DE FORTALEZAS Y DEBILIDADES
        self._agregar_analisis(story, jugador_data)
        
        # 5. COMPARACIÓN (si se proporciona)
        if comparacion_data:
            self._agregar_comparacion(story, jugador_data, comparacion_data)
        
        # 6. RECOMENDACIÓN FINAL
        self._agregar_recomendacion(story, jugador_data)
        
        # 7. PIE DE PÁGINA
        self._agregar_pie_pagina(story)
        
        # Construir el PDF
        doc.build(story)
        
        return temp_file.name
    
    def _agregar_encabezado(self, story, data):
        """Agregar encabezado del informe"""
        # Título principal
        titulo = f"INFORME DE SCOUTING: {data['nombre'].upper()} {data['apellidos'].upper()}"
        story.append(Paragraph(titulo, self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Información básica en tabla
        datos_basicos = [
            ['JUGADOR', f"{data['nombre']} {data['apellidos']}"],
            ['POSICIÓN', data['posicion']],
            ['EQUIPO ACTUAL', data['equipo']],
            ['LIGA', data['liga']],
            ['FECHA DEL INFORME', datetime.now().strftime('%d/%m/%Y')]
        ]
        
        tabla_basica = Table(datos_basicos, colWidths=[2*inch, 3*inch])
        tabla_basica.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('BACKGROUND', (1, 0), (1, -1), colors.HexColor('#ecf0f1')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla_basica)
        story.append(Spacer(1, 30))
    
    def _agregar_info_personal(self, story, data):
        """Agregar información personal y profesional"""
        story.append(Paragraph("INFORMACIÓN DEL JUGADOR", self.styles['CustomSubtitle']))
        
        # Información personal
        info_personal = [
            ['CARACTERÍSTICA', 'VALOR'],
            ['Edad', f"{data['edad']} años"],
            ['Altura', f"{data['altura']} cm"],
            ['Peso', f"{data['peso']} kg"],
            ['Pie preferido', data['pie_preferido']],
            ['Nacionalidad', data['pais']],
            ['Valor de mercado', f"€{data['valor_mercado']:,.0f}"],
        ]
        
        tabla_personal = Table(info_personal, colWidths=[2.5*inch, 2.5*inch])
        tabla_personal.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(tabla_personal)
        story.append(Spacer(1, 20))
    
    def _agregar_estadisticas(self, story, data):
        """Agregar estadísticas de rendimiento"""
        story.append(Paragraph("ESTADÍSTICAS DE RENDIMIENTO", self.styles['CustomSubtitle']))
        
        # Estadísticas generales
        stats_generales = [
            ['CATEGORÍA', 'ESTADÍSTICA', 'VALOR'],
            ['Participación', 'Partidos jugados', f"{data['partidos_jugados']}"],
            ['', 'Minutos jugados', f"{data['minutos_jugados']:,}"],
            ['Ataque', 'Goles', f"{data['goles']}"],
            ['', 'Asistencias', f"{data['asistencias']}"],
            ['Disciplina', 'Tarjetas amarillas', f"{data['tarjetas_amarillas']}"],
            ['', 'Tarjetas rojas', f"{data['tarjetas_rojas']}"],
            ['Pases', 'Pases completados', f"{data['pases_completados']:,}"],
            ['', 'Precisión de pases', f"{data['precision_pases']:.1f}%"],
            ['Técnica', 'Regates completados', f"{data['regates_completados']}"],
            ['', 'Regates intentados', f"{data['regates_intentados']}"],
            ['Defensa', 'Interceptaciones', f"{data['interceptaciones']}"],
            ['', 'Recuperaciones', f"{data['recuperaciones']}"],
            ['Juego aéreo', 'Duelos aéreos ganados', f"{data['duelos_aereos_ganados']}/{data['duelos_aereos_totales']}"]
        ]
        
        tabla_stats = Table(stats_generales, colWidths=[1.5*inch, 2*inch, 1.5*inch])
        tabla_stats.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(tabla_stats)
        story.append(Spacer(1, 20))
    
    def _agregar_analisis(self, story, data):
        """Agregar análisis de fortalezas y debilidades"""
        story.append(Paragraph("ANÁLISIS TÉCNICO", self.styles['CustomSubtitle']))
        
        # Calcular ratios importantes
        minutos_por_gol = data['minutos_jugados'] / max(data['goles'], 1)
        efectividad_regates = (data['regates_completados'] / max(data['regates_intentados'], 1)) * 100
        efectividad_aerea = (data['duelos_aereos_ganados'] / max(data['duelos_aereos_totales'], 1)) * 100
        
        # Análisis automático basado en estadísticas
        fortalezas = []
        debilidades = []
        
        # Análisis de goles
        if data['goles'] >= 15:
            fortalezas.append("Excelente capacidad goleadora")
        elif data['goles'] >= 8:
            fortalezas.append("Buena contribución en goles")
        else:
            debilidades.append("Necesita mejorar su aporte goleador")
        
        # Análisis de asistencias
        if data['asistencias'] >= 10:
            fortalezas.append("Gran creador de juego")
        elif data['asistencias'] >= 5:
            fortalezas.append("Buen aporte en asistencias")
        
        # Análisis de precisión de pases
        if data['precision_pases'] >= 90:
            fortalezas.append("Excelente precisión en el pase")
        elif data['precision_pases'] >= 80:
            fortalezas.append("Buena técnica de pase")
        else:
            debilidades.append("Debe mejorar la precisión en los pases")
        
        # Análisis de regates
        if efectividad_regates >= 70:
            fortalezas.append("Muy efectivo en situaciones 1vs1")
        elif efectividad_regates >= 50:
            fortalezas.append("Buena técnica individual")
        
        # Análisis defensivo
        if data['interceptaciones'] >= 30:
            fortalezas.append("Excelente lectura del juego defensivo")
        elif data['interceptaciones'] >= 15:
            fortalezas.append("Buena contribución defensiva")
        
        # Crear tabla de análisis
        analisis_data = [['FORTALEZAS', 'ÁREAS DE MEJORA']]
        
        max_items = max(len(fortalezas), len(debilidades))
        for i in range(max_items):
            fortaleza = f"• {fortalezas[i]}" if i < len(fortalezas) else ""
            debilidad = f"• {debilidades[i]}" if i < len(debilidades) else ""
            analisis_data.append([fortaleza, debilidad])
        
        tabla_analisis = Table(analisis_data, colWidths=[2.5*inch, 2.5*inch])
        tabla_analisis.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#27ae60')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla_analisis)
        story.append(Spacer(1, 20))
    
    def _agregar_recomendacion(self, story, data):
        """Agregar recomendación final"""
        story.append(Paragraph("RECOMENDACIÓN DE SCOUTING", self.styles['CustomSubtitle']))
        
        # Convertir Series a dict si es necesario
        if hasattr(data, 'to_dict'):
            data = data.to_dict()
        
        # Calcular puntuación general (simplificada)
        puntuacion_ofensiva = min((data['goles'] + data['asistencias']) * 2, 40)
        puntuacion_tecnica = min(data['precision_pases'] / 2.5, 40)
        puntuacion_experiencia = min(data['partidos_jugados'], 20)
        
        puntuacion_total = puntuacion_ofensiva + puntuacion_tecnica + puntuacion_experiencia
        
        # Determinar recomendación
        if puntuacion_total >= 80:
            recomendacion = "FICHAJE ALTAMENTE RECOMENDADO"
            color_recom = colors.HexColor('#27ae60')
            justificacion = "Jugador con excelentes estadísticas en múltiples aspectos. Representa una oportunidad de inversión de alto valor para el equipo."
        elif puntuacion_total >= 60:
            recomendacion = "JUGADOR INTERESANTE - SEGUIR OBSERVANDO"
            color_recom = colors.HexColor('#f39c12')
            justificacion = "Jugador con buen potencial que merece seguimiento continuo. Considerar contexto del equipo y liga antes de decisión final."
        else:
            recomendacion = "NO RECOMENDADO EN ESTE MOMENTO"
            color_recom = colors.HexColor('#e74c3c')
            justificacion = "Las estadísticas actuales no justifican una inversión inmediata. Recomendable reevaluar en temporadas futuras."
        
        # Tabla de recomendación con mejor formato
        recom_data = [
            ['PUNTUACIÓN GENERAL', f"{puntuacion_total:.0f}/100"],
            ['RECOMENDACIÓN', recomendacion]
        ]
        
        tabla_recom = Table(recom_data, colWidths=[2*inch, 3*inch])
        tabla_recom.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#34495e')),
            ('BACKGROUND', (1, 1), (1, 1), color_recom),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('TEXTCOLOR', (1, 1), (1, 1), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(tabla_recom)
        story.append(Spacer(1, 15))
        
        # Justificación en párrafo separado (mejor formato)
        story.append(Paragraph("JUSTIFICACIÓN:", self.styles['CustomSubtitle']))
        
        justificacion_style = ParagraphStyle(
            'JustificacionStyle',
            parent=self.styles['CustomNormal'],
            fontSize=10,
            spaceAfter=12,
            alignment=TA_LEFT,
            leftIndent=20,
            rightIndent=20,
            borderWidth=1,
            borderColor=colors.HexColor('#bdc3c7'),
            borderPadding=10,
            backColor=colors.HexColor('#f8f9fa')
        )
        
        story.append(Paragraph(justificacion, justificacion_style))
        story.append(Spacer(1, 20))
    
    def _agregar_pie_pagina(self, story):
        """Agregar pie de página"""
        story.append(Spacer(1, 30))
        
        pie_texto = f"""
        <para align="center">
        <b>Scouting Pro - Sistema de Análisis Deportivo</b><br/>
        Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}<br/>
        <i>Este informe es confidencial y está destinado exclusivamente para uso interno del club.</i>
        </para>
        """
        
        story.append(Paragraph(pie_texto, self.styles['CustomNormal']))
    
    def _agregar_comparacion(self, story, jugador1, jugador2):
        """Agregar sección de comparación entre dos jugadores"""
        story.append(Paragraph("COMPARACIÓN CON OTRO JUGADOR", self.styles['CustomSubtitle']))
        
        # Convertir Series a dict si es necesario
        if hasattr(jugador1, 'to_dict'):
            j1 = jugador1.to_dict()
        else:
            j1 = jugador1
            
        if hasattr(jugador2, 'to_dict'):
            j2 = jugador2.to_dict()
        else:
            j2 = jugador2
        
        # Tabla comparativa
        comparacion_data = [
            ['ESTADÍSTICA', f"{j1['nombre']} {j1['apellidos']}", f"{j2['nombre']} {j2['apellidos']}"],
            ['Edad', f"{j1['edad']} años", f"{j2['edad']} años"],
            ['Valor de mercado', f"€{j1['valor_mercado']:,.0f}", f"€{j2['valor_mercado']:,.0f}"],
            ['Partidos jugados', f"{j1['partidos_jugados']}", f"{j2['partidos_jugados']}"],
            ['Goles', f"{j1['goles']}", f"{j2['goles']}"],
            ['Asistencias', f"{j1['asistencias']}", f"{j2['asistencias']}"],
            ['Precisión pases', f"{j1['precision_pases']:.1f}%", f"{j2['precision_pases']:.1f}%"],
            ['Interceptaciones', f"{j1['interceptaciones']}", f"{j2['interceptaciones']}"]
        ]
        
        tabla_comp = Table(comparacion_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        tabla_comp.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
        ]))
        
        story.append(tabla_comp)
        story.append(Spacer(1, 20))