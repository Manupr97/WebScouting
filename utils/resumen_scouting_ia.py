# utils/resumen_scouting_ia.py
"""
Sistema de Resúmenes Inteligentes con Ollama para Scouting de Fútbol
"""

import requests
import json
from typing import List, Dict, Optional

class ResumenScoutingIA:
    """
    Clase para generar resúmenes inteligentes de informes de scouting usando Ollama
    """
    
    def __init__(self, modelo="llama3.2:latest", url_base="http://localhost:11434"):
        """
        Inicializa el cliente de Ollama
        
        Args:
            modelo: Modelo de Ollama a usar (llama3.2:latest, openchat:latest, etc.)
            url_base: URL donde está corriendo Ollama
        """
        self.modelo = modelo
        self.url_base = url_base
        self.endpoint = f"{url_base}/api/generate"
        
    def verificar_conexion(self) -> bool:
        """Verifica que Ollama esté disponible"""
        try:
            response = requests.get(f"{self.url_base}/api/tags")
            return response.status_code == 200
        except:
            return False
    
    def verificar_modelo(self) -> bool:
        """Verifica que el modelo esté instalado"""
        try:
            response = requests.get(f"{self.url_base}/api/tags")
            if response.status_code == 200:
                modelos = response.json()
                return any(m['name'] == self.modelo for m in modelos.get('models', []))
            return False
        except:
            return False
    
    def generar_resumen_observaciones(self, informes: List[Dict], tipo_resumen="completo") -> Dict[str, str]:
        """
        Genera un resumen inteligente de múltiples informes de un jugador
        
        Args:
            informes: Lista de informes del jugador
            tipo_resumen: "completo", "tecnico", "tactico", "fisico", "mental"
            
        Returns:
            Dict con resúmenes por categoría
        """
        if not self.verificar_conexion():
            return {"error": "No se pudo conectar con Ollama. Asegúrate de que esté ejecutándose."}
        
        if not self.verificar_modelo():
            return {"error": f"El modelo {self.modelo} no está instalado. Instálalo con: ollama pull {self.modelo}"}
        
        # Preparar datos para el análisis
        jugador_nombre = informes[0]['jugador_nombre'] if informes else "Jugador"
        equipo = informes[0]['equipo'] if informes else "Equipo"
        num_informes = len(informes)
        
        # Agrupar observaciones por categoría
        observaciones = {
            'tecnicas': [],
            'tacticas': [],
            'fisicas': [],
            'mentales': [],
            'generales': [],
            'fortalezas': [],
            'debilidades': []
        }
        
        # Recopilar todas las observaciones
        for informe in informes:
            tipo_eval = "Video completo" if informe.get('tipo_evaluacion') == 'video_completo' else "Campo"
            fecha = informe.get('fecha_creacion', 'N/A')[:10]
            nota = informe.get('nota_general', 'N/A')
            
            # Observaciones generales
            if informe.get('observaciones'):
                obs_texto = informe['observaciones']
                
                # Intentar identificar secciones en las observaciones
                if 'TECNICA' in obs_texto.upper() or 'TÉCNICA' in obs_texto.upper():
                    observaciones['tecnicas'].append(f"[{fecha} - {tipo_eval} - Nota: {nota}/10] {obs_texto}")
                elif 'TACTICA' in obs_texto.upper() or 'TÁCTICA' in obs_texto.upper():
                    observaciones['tacticas'].append(f"[{fecha} - {tipo_eval} - Nota: {nota}/10] {obs_texto}")
                elif 'FISICA' in obs_texto.upper() or 'FÍSICA' in obs_texto.upper():
                    observaciones['fisicas'].append(f"[{fecha} - {tipo_eval} - Nota: {nota}/10] {obs_texto}")
                elif 'MENTAL' in obs_texto.upper():
                    observaciones['mentales'].append(f"[{fecha} - {tipo_eval} - Nota: {nota}/10] {obs_texto}")
                else:
                    observaciones['generales'].append(f"[{fecha} - {tipo_eval} - Nota: {nota}/10] {obs_texto}")
            
            # Fortalezas y debilidades
            if informe.get('fortalezas'):
                observaciones['fortalezas'].append(f"[{fecha}] {informe['fortalezas']}")
            if informe.get('debilidades'):
                observaciones['debilidades'].append(f"[{fecha}] {informe['debilidades']}")
        
        # Generar resúmenes por categoría
        resumenes = {}
        
        if tipo_resumen == "completo":
            # Resumen ejecutivo general
            prompt_ejecutivo = self._crear_prompt_ejecutivo(jugador_nombre, equipo, num_informes, observaciones)
            resumenes['ejecutivo'] = self._llamar_ollama(prompt_ejecutivo)
            
            # Resumen de fortalezas consolidadas
            if observaciones['fortalezas']:
                prompt_fortalezas = self._crear_prompt_fortalezas(jugador_nombre, observaciones['fortalezas'])
                resumenes['fortalezas'] = self._llamar_ollama(prompt_fortalezas)
            
            # Resumen de áreas de mejora
            if observaciones['debilidades']:
                prompt_debilidades = self._crear_prompt_debilidades(jugador_nombre, observaciones['debilidades'])
                resumenes['areas_mejora'] = self._llamar_ollama(prompt_debilidades)
            
            # Evolución del jugador (si hay múltiples informes)
            if num_informes > 1:
                prompt_evolucion = self._crear_prompt_evolucion(jugador_nombre, informes)
                resumenes['evolucion'] = self._llamar_ollama(prompt_evolucion)
            
            # Recomendación consolidada
            prompt_recomendacion = self._crear_prompt_recomendacion(jugador_nombre, informes)
            resumenes['recomendacion_final'] = self._llamar_ollama(prompt_recomendacion)
        
        return resumenes
    
    def _crear_prompt_ejecutivo(self, jugador: str, equipo: str, num_informes: int, observaciones: Dict) -> str:
        """Crea el prompt para el resumen ejecutivo"""
        return f"""Eres un director deportivo profesional analizando informes de scouting. 
Analiza los siguientes informes de {jugador} del {equipo} basados en {num_informes} evaluaciones.

OBSERVACIONES GENERALES:
{chr(10).join(observaciones['generales'][:5]) if observaciones['generales'] else 'Sin observaciones generales'}

FORTALEZAS IDENTIFICADAS:
{chr(10).join(observaciones['fortalezas'][:3]) if observaciones['fortalezas'] else 'No especificadas'}

ÁREAS DE MEJORA:
{chr(10).join(observaciones['debilidades'][:3]) if observaciones['debilidades'] else 'No especificadas'}

Genera un resumen ejecutivo de MÁXIMO 120 palabras que:
1. Defina el perfil del jugador en una frase
2. Destaque sus 2-3 principales fortalezas
3. Mencione 1-2 áreas clave de mejora
4. Sugiera en qué tipo de equipo encajaría mejor

Sé directo, profesional y específico. NO uses frases introductorias como "Basándome en los informes..." o similares."""
    
    def _crear_prompt_fortalezas(self, jugador: str, fortalezas: List[str]) -> str:
        """Crea el prompt para consolidar fortalezas"""
        return f"""Como scout profesional, analiza las fortalezas de {jugador} identificadas en múltiples evaluaciones:

{chr(10).join(fortalezas)}

Resume en MÁXIMO 80 palabras:
1. Las 3 fortalezas más consistentes
2. Cómo se complementan entre sí
3. Su valor diferencial

Sé específico y técnico. Evita generalidades."""
    
    def _crear_prompt_debilidades(self, jugador: str, debilidades: List[str]) -> str:
        """Crea el prompt para consolidar áreas de mejora"""
        return f"""Como scout profesional, analiza las áreas de mejora de {jugador}:

{chr(10).join(debilidades)}

Resume en MÁXIMO 80 palabras:
1. Las 2 áreas de mejora prioritarias
2. Si son entrenables o limitaciones estructurales
3. Una recomendación específica

Sé constructivo y profesional."""
    
    def _crear_prompt_evolucion(self, jugador: str, informes: List[Dict]) -> str:
        """Crea el prompt para analizar la evolución"""
        # Ordenar informes por fecha
        informes_ordenados = sorted(informes, key=lambda x: x.get('fecha_creacion', ''))
        
        evolucion_texto = []
        for inf in informes_ordenados[:5]:  # Máximo 5 informes más recientes
            fecha = inf.get('fecha_creacion', 'N/A')[:10]
            nota = inf.get('nota_general', 'N/A')
            tipo = "Video" if inf.get('tipo_evaluacion') == 'video_completo' else "Campo"
            evolucion_texto.append(f"{fecha} - Nota: {nota}/10 ({tipo})")
        
        return f"""Analiza la evolución de {jugador} según estas evaluaciones cronológicas:

{chr(10).join(evolucion_texto)}

En MÁXIMO 60 palabras describe:
1. Tendencia general (mejora/estable/declive)
2. Consistencia del rendimiento
3. Proyección futura

Basa el análisis SOLO en los datos proporcionados."""
    
    def _crear_prompt_recomendacion(self, jugador: str, informes: List[Dict]) -> str:
        """Crea el prompt para la recomendación final consolidada"""
        # Contar recomendaciones
        recomendaciones = [inf.get('recomendacion', '') for inf in informes]
        fichas = sum(1 for r in recomendaciones if 'fichar' in r.lower())
        seguir = sum(1 for r in recomendaciones if 'seguir' in r.lower() or 'observando' in r.lower())
        descartar = sum(1 for r in recomendaciones if 'descartar' in r.lower())
        
        nota_promedio = sum(inf.get('nota_general', 0) for inf in informes) / len(informes) if informes else 0
        
        return f"""Como director deportivo, basándote en {len(informes)} evaluaciones de {jugador}:
- Nota promedio: {nota_promedio:.1f}/10
- Recomendaciones: {fichas} fichar, {seguir} seguir observando, {descartar} descartar

Genera una recomendación final en MÁXIMO 50 palabras que incluya:
1. Decisión clara (FICHAR / SEGUIR OBSERVANDO / DESCARTAR)
2. Razón principal
3. Condición o plazo si aplica

Sé categórico y directo."""
    
    def _llamar_ollama(self, prompt: str) -> str:
        """Realiza la llamada a Ollama y devuelve la respuesta"""
        try:
            payload = {
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "num_predict": 300  # Límite de tokens
                }
            }
            
            response = requests.post(self.endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                return response.json().get('response', 'No se pudo generar el resumen').strip()
            else:
                return f"Error: {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "Error: Tiempo de espera agotado (intenta con un modelo más pequeño)"
        except Exception as e:
            return f"Error: {str(e)}"


def agregar_resumenes_ia_al_pdf(pdf, informes_jugador, jugador_nombre):
    """
    Añade una página con resúmenes generados por IA al PDF
    
    Args:
        pdf: Objeto FPDF
        informes_jugador: Lista de todos los informes del jugador
        jugador_nombre: Nombre del jugador
    """
    try:
        # Función de limpieza de texto incluida aquí para evitar problemas de importación
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
        
        # Inicializar el generador de resúmenes
        ia_scout = ResumenScoutingIA()
        
        # Verificar conexión
        if not ia_scout.verificar_conexion():
            print("⚠️ Ollama no disponible, omitiendo resúmenes IA")
            return
        
        print(f"🤖 Generando resúmenes inteligentes para {jugador_nombre}...")
        
        # Generar resúmenes
        resumenes = ia_scout.generar_resumen_observaciones(informes_jugador, tipo_resumen="completo")
        
        if 'error' in resumenes:
            print(f"⚠️ {resumenes['error']}")
            return
        
        # Añadir página al PDF
        pdf.add_page()
        
        # Header
        pdf.set_font('Helvetica', 'B', 18)
        pdf.set_text_color(36, 40, 42)
        pdf.cell(0, 15, 'ANALISIS INTELIGENTE (IA)', 0, 1, 'C')
        
        # Línea decorativa
        pdf.set_fill_color(0, 123, 191)
        pdf.rect(15, 25, 180, 2, 'F')
        pdf.ln(15)
        
        # Resumen Ejecutivo
        if 'ejecutivo' in resumenes and resumenes['ejecutivo']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(0, 123, 191)
            pdf.cell(0, 10, 'RESUMEN EJECUTIVO', 0, 1)
            
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, limpiar_texto_para_pdf(resumenes['ejecutivo']), 0, 'J')
            pdf.ln(8)
        
        # Fortalezas Consolidadas
        if 'fortalezas' in resumenes and resumenes['fortalezas']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(40, 167, 69)
            pdf.cell(0, 10, 'FORTALEZAS CONSOLIDADAS', 0, 1)
            
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, limpiar_texto_para_pdf(resumenes['fortalezas']), 0, 'J')
            pdf.ln(8)
        
        # Áreas de Mejora
        if 'areas_mejora' in resumenes and resumenes['areas_mejora']:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(220, 53, 69)
            pdf.cell(0, 10, 'AREAS DE MEJORA', 0, 1)
            
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, limpiar_texto_para_pdf(resumenes['areas_mejora']), 0, 'J')
            pdf.ln(8)
        
        # Evolución (si hay múltiples informes)
        if 'evolucion' in resumenes and resumenes['evolucion'] and len(informes_jugador) > 1:
            pdf.set_font('Helvetica', 'B', 14)
            pdf.set_text_color(0, 123, 191)
            pdf.cell(0, 10, 'EVOLUCION DEL JUGADOR', 0, 1)
            
            pdf.set_font('Helvetica', '', 11)
            pdf.set_text_color(60, 60, 60)
            pdf.multi_cell(0, 6, limpiar_texto_para_pdf(resumenes['evolucion']), 0, 'J')
            pdf.ln(8)
        
        # Recomendación Final IA
        if 'recomendacion_final' in resumenes and resumenes['recomendacion_final']:
            # Determinar color según recomendación
            texto_recom = resumenes['recomendacion_final'].upper()
            if 'FICHAR' in texto_recom:
                color_recom = (0, 123, 191)
            elif 'SEGUIR' in texto_recom:
                color_recom = (255, 193, 7)
            else:
                color_recom = (220, 53, 69)
            
            pdf.ln(5)
            pdf.set_fill_color(*color_recom)
            pdf.rect(30, pdf.get_y(), 150, 30, 'F')
            
            pdf.set_font('Helvetica', 'B', 12)
            pdf.set_text_color(255, 255, 255)
            pdf.set_xy(30, pdf.get_y() + 5)
            pdf.multi_cell(150, 6, limpiar_texto_para_pdf(resumenes['recomendacion_final']), 0, 'C')
        
        # Footer informativo
        pdf.set_y(-35)
        pdf.set_font('Helvetica', 'I', 9)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 5, f'Analisis generado por IA ({ia_scout.modelo}) basado en {len(informes_jugador)} evaluaciones', 0, 1, 'C')
        
        print("✅ Resúmenes IA añadidos al PDF")
        
    except Exception as e:
        print(f"⚠️ Error generando resúmenes IA: {str(e)}")
        import traceback
        traceback.print_exc()


def mostrar_resumenes_ia_streamlit(df_filtrado, container=None):
    """
    Muestra los resúmenes generados por IA en la interfaz de Streamlit
    
    Args:
        df_filtrado: DataFrame con los informes filtrados
        container: Contenedor de Streamlit donde mostrar (opcional)
    """
    import streamlit as st
    
    # Usar el container proporcionado o st directamente
    ctx = container if container else st
    
    # Selector de jugador
    jugadores_con_multiples = df_filtrado.groupby('jugador_nombre').size()
    jugadores_con_multiples = jugadores_con_multiples[jugadores_con_multiples > 1].index.tolist()
    
    if not jugadores_con_multiples:
        ctx.info("💡 Los análisis con IA están disponibles para jugadores con múltiples evaluaciones")
        return
    
    ctx.markdown("### 🤖 Análisis Inteligente con IA")
    
    col1, col2 = ctx.columns([3, 1])
    
    with col1:
        jugador_seleccionado = st.selectbox(
            "Selecciona un jugador para análisis IA:",
            options=jugadores_con_multiples,
            key="jugador_ia_select"
        )
    
    with col2:
        if st.button("🔍 Generar Análisis", type="primary", use_container_width=True):
            # Obtener informes del jugador
            informes_jugador = df_filtrado[df_filtrado['jugador_nombre'] == jugador_seleccionado].to_dict('records')
            
            # Inicializar IA
            ia_scout = ResumenScoutingIA()
            
            # Verificar conexión
            if not ia_scout.verificar_conexion():
                st.error("❌ Ollama no está disponible. Asegúrate de que esté ejecutándose.")
                st.code("# En una terminal:\nollama serve", language="bash")
                return
            
            # Generar resúmenes
            with st.spinner(f"🤖 Analizando {len(informes_jugador)} informes de {jugador_seleccionado}..."):
                resumenes = ia_scout.generar_resumen_observaciones(informes_jugador, tipo_resumen="completo")
            
            if 'error' in resumenes:
                st.error(resumenes['error'])
                return
            
            # Mostrar resultados
            ctx.markdown(f"#### 📊 Análisis de {jugador_seleccionado}")
            ctx.caption(f"Basado en {len(informes_jugador)} evaluaciones")
            
            # Tabs para organizar la información
            tab1, tab2, tab3, tab4 = ctx.tabs(["📋 Resumen", "💪 Fortalezas", "📈 Evolución", "🎯 Recomendación"])
            
            with tab1:
                if 'ejecutivo' in resumenes and resumenes['ejecutivo']:
                    st.markdown("**Resumen Ejecutivo:**")
                    st.write(resumenes['ejecutivo'])
            
            with tab2:
                col1, col2 = st.columns(2)
                with col1:
                    if 'fortalezas' in resumenes and resumenes['fortalezas']:
                        st.markdown("**🟢 Fortalezas:**")
                        st.success(resumenes['fortalezas'])
                
                with col2:
                    if 'areas_mejora' in resumenes and resumenes['areas_mejora']:
                        st.markdown("**🟡 Áreas de Mejora:**")
                        st.warning(resumenes['areas_mejora'])
            
            with tab3:
                if 'evolucion' in resumenes and resumenes['evolucion']:
                    st.markdown("**📊 Evolución del Rendimiento:**")
                    st.info(resumenes['evolucion'])
                    
                    # Mini gráfico de evolución
                    import plotly.graph_objects as go
                    
                    fechas = []
                    notas = []
                    for inf in informes_jugador:
                        fechas.append(inf['fecha_creacion'][:10])
                        notas.append(inf.get('nota_general', 0))
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=fechas, 
                        y=notas,
                        mode='lines+markers',
                        name='Nota General',
                        line=dict(color='#007bbf', width=3),
                        marker=dict(size=10)
                    ))
                    
                    fig.update_layout(
                        title=f"Evolución de {jugador_seleccionado}",
                        xaxis_title="Fecha",
                        yaxis_title="Nota",
                        yaxis=dict(range=[0, 10.5]),
                        height=300
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
            
            with tab4:
                if 'recomendacion_final' in resumenes and resumenes['recomendacion_final']:
                    st.markdown("**🎯 Recomendación Final:**")
                    
                    # Color según recomendación
                    texto = resumenes['recomendacion_final'].upper()
                    if 'FICHAR' in texto:
                        st.success(resumenes['recomendacion_final'])
                    elif 'SEGUIR' in texto:
                        st.warning(resumenes['recomendacion_final'])
                    else:
                        st.error(resumenes['recomendacion_final'])
            
            # Información del modelo
            ctx.caption(f"💡 Análisis generado con {ia_scout.modelo}")