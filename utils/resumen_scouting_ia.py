# utils/resumen_scouting_ia_mejorado.py

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional
import os
import requests
import json
from datetime import datetime

class ResumenScoutingIA:
    """
    Clase para generar resúmenes inteligentes de informes de scouting usando Ollama
    """
    
    def __init__(self, modelo="mistral:7b-instruct", url_base="http://localhost:11434"):
        """
        Inicializa el cliente de Ollama
        
        Args:
            modelo: Modelo de Ollama a usar (mistral:7b-instruct es mejor para español)
            url_base: URL donde está corriendo Ollama
        """
        self.modelo = modelo
        self.url_base = url_base
        self.endpoint = f"{url_base}/api/generate"
        self.extractor_wyscout = None
        
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
    
    def obtener_datos_wyscout_jugador(self, nombre_jugador: str, equipo: str) -> Optional[Dict]:
        """
        Obtiene datos de Wyscout para el jugador si están disponibles
        """
        try:
            if self.extractor_wyscout is None:
                from utils.wyscout_data_extractor_personalizado import WyscoutExtractorPersonalizado
                self.extractor_wyscout = WyscoutExtractorPersonalizado()
            
            jugador_data = self.extractor_wyscout.buscar_jugador_mejorado(nombre_jugador, equipo)
            
            if jugador_data is not None:
                # Convertir a dict si es necesario
                if hasattr(jugador_data, 'to_dict'):
                    return jugador_data.to_dict()
                return dict(jugador_data)
            
        except Exception as e:
            print(f"Error obteniendo datos Wyscout: {e}")
        
        return None
    
    def generar_contexto_wyscout(self, datos_wyscout: Dict, grupo_posicion: str) -> str:
        """
        Genera contexto relevante de los datos Wyscout para la IA
        """
        if not datos_wyscout:
            return ""
        
        contexto = "\n\nDATOS OBJETIVOS WYSCOUT:\n"
        
        # Función auxiliar para convertir valores a float de forma segura
        def safe_float(value, default=0.0):
            try:
                if pd.isna(value) or value is None or value == '':
                    return default
                return float(value)
            except (ValueError, TypeError):
                return default
        
        # Función auxiliar para convertir valores a int de forma segura
        def safe_int(value, default=0):
            try:
                if pd.isna(value) or value is None or value == '':
                    return default
                return int(float(value))  # float primero por si viene como "5.0"
            except (ValueError, TypeError):
                return default
        
        # Datos generales (para todas las posiciones)
        partidos = safe_int(datos_wyscout.get('partidos_jugados', 0))
        minutos = safe_int(datos_wyscout.get('min', 0))
        contexto += f"- Partidos jugados: {partidos}\n"
        contexto += f"- Minutos totales: {minutos}\n"
        
        # MÉTRICAS ESPECÍFICAS POR POSICIÓN
        
        if grupo_posicion == 'portero':
            contexto += f"\nMÉTRICAS DE PORTERO:\n"
            
            # Paradas y goles
            goles_encajados = safe_int(datos_wyscout.get('goles_concedidos', 0))
            goles_encajados_90 = safe_float(datos_wyscout.get('goles_concedidos/90', 0))
            paradas = safe_int(datos_wyscout.get('paradas', 0))
            paradas_90 = safe_float(datos_wyscout.get('paradas/90', 0))
            
            if goles_encajados_90 > 0:
                contexto += f"- Goles encajados: {goles_encajados} total ({goles_encajados_90:.2f} por 90min)\n"
            if paradas > 0:
                contexto += f"- Paradas: {paradas} total ({paradas_90:.2f} por 90min)\n"
            
            # Porcentaje de paradas
            if 'salvadas_%' in datos_wyscout:
                salvadas_pct = safe_float(datos_wyscout['salvadas_%'])
                if salvadas_pct > 0:
                    contexto += f"- Porcentaje de paradas: {salvadas_pct:.1f}%\n"
            
            # Salidas
            if 'salidas/90' in datos_wyscout:
                salidas_90 = safe_float(datos_wyscout['salidas/90'])
                if salidas_90 > 0:
                    contexto += f"- Salidas por 90min: {salidas_90:.1f}\n"
            
            # Juego con pies
            if '%precisión_pases_largos,_' in datos_wyscout:
                pases_largos_pct = safe_float(datos_wyscout['%precisión_pases_largos,_'])
                if pases_largos_pct > 0:
                    contexto += f"- Precisión pases largos: {pases_largos_pct:.1f}%\n"
                    
            # Penaltis
            if 'penaltis_parados' in datos_wyscout:
                pen_parados = safe_int(datos_wyscout['penaltis_parados'])
                if pen_parados > 0:
                    contexto += f"- Penaltis parados: {pen_parados}\n"
        
        elif grupo_posicion == 'defensa_central':
            contexto += f"\nMÉTRICAS DEFENSIVAS CENTRALES:\n"
            
            # Duelos
            duelos_pct = safe_float(datos_wyscout.get('%duelos_ganados,_', 0))
            duelos_aereos_pct = safe_float(datos_wyscout.get('%duelos_aéreos_ganados,_', 0))
            
            if duelos_pct > 0:
                contexto += f"- Duelos ganados: {duelos_pct:.1f}%\n"
            if duelos_aereos_pct > 0:
                contexto += f"- Duelos aéreos ganados: {duelos_aereos_pct:.1f}%\n"
            
            # Acciones defensivas
            intercep_90 = safe_float(datos_wyscout.get('intercep/90', 0))
            despejes_90 = safe_float(datos_wyscout.get('despejes/90', 0))
            bloqueos_90 = safe_float(datos_wyscout.get('tiros_interceptados/90', 0))
            
            if intercep_90 > 0:
                contexto += f"- Intercepciones por 90min: {intercep_90:.1f}\n"
            if despejes_90 > 0:
                contexto += f"- Despejes por 90min: {despejes_90:.1f}\n"
            if bloqueos_90 > 0:
                contexto += f"- Bloqueos por 90min: {bloqueos_90:.1f}\n"
            
            # Faltas y tarjetas
            faltas_90 = safe_float(datos_wyscout.get('faltas/90', 0))
            if faltas_90 > 0:
                contexto += f"- Faltas por 90min: {faltas_90:.1f}\n"
            
            # Construcción
            pases_largos_pct = safe_float(datos_wyscout.get('%precisión_pases_largos,_', 0))
            if pases_largos_pct > 0:
                contexto += f"- Precisión pases largos: {pases_largos_pct:.1f}%\n"
        
        elif grupo_posicion == 'lateral':
            contexto += f"\nMÉTRICAS DE LATERAL:\n"
            
            # Defensa
            duelos_pct = safe_float(datos_wyscout.get('%duelos_ganados,_', 0))
            intercep_90 = safe_float(datos_wyscout.get('intercep/90', 0))
            entradas_90 = safe_float(datos_wyscout.get('entradas/90', 0))
            
            if duelos_pct > 0:
                contexto += f"- Duelos ganados: {duelos_pct:.1f}%\n"
            if intercep_90 > 0:
                contexto += f"- Intercepciones por 90min: {intercep_90:.1f}\n"
            if entradas_90 > 0:
                contexto += f"- Entradas por 90min: {entradas_90:.1f}\n"
            
            # Ataque
            centros_pct = safe_float(datos_wyscout.get('%precisión_centros,_', 0))
            asistencias_90 = safe_float(datos_wyscout.get('asistencias/90', 0))
            pases_clave_90 = safe_float(datos_wyscout.get('jugadas_claves/90', 0))
            
            if centros_pct > 0:
                contexto += f"- Precisión de centros: {centros_pct:.1f}%\n"
            if asistencias_90 > 0:
                contexto += f"- Asistencias por 90min: {asistencias_90:.2f}\n"
            if pases_clave_90 > 0:
                contexto += f"- Pases clave por 90min: {pases_clave_90:.1f}\n"
            
            # Velocidad y progresión
            aceleraciones_90 = safe_float(datos_wyscout.get('aceleraciones/90', 0))
            if aceleraciones_90 > 0:
                contexto += f"- Aceleraciones por 90min: {aceleraciones_90:.1f}\n"
        
        elif grupo_posicion == 'mediocentro':
            contexto += f"\nMÉTRICAS DE MEDIOCENTRO:\n"
            
            # Control y distribución
            pases_pct = safe_float(datos_wyscout.get('%precisión_pases,_', 0))
            pases_90 = safe_float(datos_wyscout.get('pases/90', 0))
            pases_progre_90 = safe_float(datos_wyscout.get('pases_adelante/90', 0))
            
            if pases_pct > 0:
                contexto += f"- Precisión de pases: {pases_pct:.1f}%\n"
            if pases_90 > 0:
                contexto += f"- Pases por 90min: {pases_90:.1f}\n"
            if pases_progre_90 > 0:
                contexto += f"- Pases progresivos por 90min: {pases_progre_90:.1f}\n"
            
            # Defensivo
            duelos_pct = safe_float(datos_wyscout.get('%duelos_ganados,_', 0))
            intercep_90 = safe_float(datos_wyscout.get('intercep/90', 0))
            recuperaciones_90 = safe_float(datos_wyscout.get('posesión_conquistada_después_de_una_interceptación', 0))
            
            if duelos_pct > 0:
                contexto += f"- Duelos ganados: {duelos_pct:.1f}%\n"
            if intercep_90 > 0:
                contexto += f"- Intercepciones por 90min: {intercep_90:.1f}\n"
            if recuperaciones_90 > 0:
                contexto += f"- Recuperaciones por 90min: {recuperaciones_90:.1f}\n"
            
            # Creación
            pases_clave_90 = safe_float(datos_wyscout.get('jugadas_claves/90', 0))
            xa_90 = safe_float(datos_wyscout.get('xa/90', 0))
            
            if pases_clave_90 > 0:
                contexto += f"- Pases clave por 90min: {pases_clave_90:.1f}\n"
            if xa_90 > 0:
                contexto += f"- xA por 90min: {xa_90:.2f}\n"
        
        elif grupo_posicion == 'mediapunta':
            contexto += f"\nMÉTRICAS DE MEDIAPUNTA:\n"
            
            # Creatividad
            pases_clave_90 = safe_float(datos_wyscout.get('jugadas_claves/90', 0))
            asistencias = safe_int(datos_wyscout.get('asistencias', 0))
            asistencias_90 = safe_float(datos_wyscout.get('asistencias/90', 0))
            xa_90 = safe_float(datos_wyscout.get('xa/90', 0))
            
            if pases_clave_90 > 0:
                contexto += f"- Pases clave por 90min: {pases_clave_90:.1f}\n"
            if asistencias > 0:
                contexto += f"- Asistencias: {asistencias} total ({asistencias_90:.2f} por 90min)\n"
            if xa_90 > 0:
                contexto += f"- xA por 90min: {xa_90:.2f}\n"
            
            # Goles
            goles = safe_int(datos_wyscout.get('goles', 0))
            goles_90 = safe_float(datos_wyscout.get('goles/90', 0))
            xg_90 = safe_float(datos_wyscout.get('xg/90', 0))
            
            if goles > 0:
                contexto += f"- Goles: {goles} total ({goles_90:.2f} por 90min)\n"
            if xg_90 > 0:
                contexto += f"- xG por 90min: {xg_90:.2f}\n"
            
            # Regates y tiros
            regates_90 = safe_float(datos_wyscout.get('regates/90', 0))
            tiros_90 = safe_float(datos_wyscout.get('remates/90', 0))
            
            if regates_90 > 0:
                contexto += f"- Regates por 90min: {regates_90:.1f}\n"
            if tiros_90 > 0:
                contexto += f"- Tiros por 90min: {tiros_90:.1f}\n"
        
        elif grupo_posicion == 'extremo':
            contexto += f"\nMÉTRICAS DE EXTREMO:\n"
            
            # Desborde
            regates_90 = safe_float(datos_wyscout.get('regates/90', 0))
            regates_pct = safe_float(datos_wyscout.get('%regates_realizados,_', 0))
            aceleraciones_90 = safe_float(datos_wyscout.get('aceleraciones/90', 0))
            
            if regates_90 > 0:
                contexto += f"- Regates por 90min: {regates_90:.1f}\n"
            if regates_pct > 0:
                contexto += f"- Éxito en regates: {regates_pct:.1f}%\n"
            if aceleraciones_90 > 0:
                contexto += f"- Aceleraciones por 90min: {aceleraciones_90:.1f}\n"
            
            # Centros y asistencias
            centros_pct = safe_float(datos_wyscout.get('%precisión_centros,_', 0))
            asistencias_90 = safe_float(datos_wyscout.get('asistencias/90', 0))
            xa_90 = safe_float(datos_wyscout.get('xa/90', 0))
            
            if centros_pct > 0:
                contexto += f"- Precisión de centros: {centros_pct:.1f}%\n"
            if asistencias_90 > 0:
                contexto += f"- Asistencias por 90min: {asistencias_90:.2f}\n"
            if xa_90 > 0:
                contexto += f"- xA por 90min: {xa_90:.2f}\n"
            
            # Goles
            goles = safe_int(datos_wyscout.get('goles', 0))
            goles_90 = safe_float(datos_wyscout.get('goles/90', 0))
            xg_90 = safe_float(datos_wyscout.get('xg/90', 0))
            
            if goles > 0:
                contexto += f"- Goles: {goles} total ({goles_90:.2f} por 90min)\n"
            if xg_90 > 0:
                contexto += f"- xG por 90min: {xg_90:.2f}\n"
        
        elif grupo_posicion == 'delantero':
            contexto += f"\nMÉTRICAS DE DELANTERO:\n"
            
            # Finalización
            goles = safe_int(datos_wyscout.get('goles', 0))
            goles_90 = safe_float(datos_wyscout.get('goles/90', 0))
            xg = safe_float(datos_wyscout.get('xg', 0))
            xg_90 = safe_float(datos_wyscout.get('xg/90', 0))
            
            if goles > 0:
                contexto += f"- Goles: {goles} total ({goles_90:.2f} por 90min)\n"
            if xg > 0:
                contexto += f"- xG: {xg:.1f} total ({xg_90:.2f} por 90min)\n"
                # Eficiencia
                eficiencia = (goles / xg) * 100
                contexto += f"- Eficiencia goleadora: {eficiencia:.0f}% (goles/xG)\n"
            
            # Tiros
            tiros_90 = safe_float(datos_wyscout.get('remates/90', 0))
            tiros_puerta_pct = safe_float(datos_wyscout.get('%tiros_a_la_portería,_', 0))
            toques_area_90 = safe_float(datos_wyscout.get('toques_en_el_área_de_penalti/90', 0))
            
            if tiros_90 > 0:
                contexto += f"- Tiros por 90min: {tiros_90:.1f}\n"
            if tiros_puerta_pct > 0:
                contexto += f"- Tiros a puerta: {tiros_puerta_pct:.1f}%\n"
            if toques_area_90 > 0:
                contexto += f"- Toques en área por 90min: {toques_area_90:.1f}\n"
            
            # Juego aéreo
            duelos_aereos_pct = safe_float(datos_wyscout.get('%duelos_aéreos_ganados,_', 0))
            if duelos_aereos_pct > 0:
                contexto += f"- Duelos aéreos ganados: {duelos_aereos_pct:.1f}%\n"
            
            # Asociación
            asistencias_90 = safe_float(datos_wyscout.get('asistencias/90', 0))
            if asistencias_90 > 0:
                contexto += f"- Asistencias por 90min: {asistencias_90:.2f}\n"
        
        else:  # general o posición no especificada
            contexto += f"\nMÉTRICAS GENERALES:\n"
            
            # Mix de métricas básicas
            if 'goles/90' in datos_wyscout:
                goles_90 = safe_float(datos_wyscout['goles/90'])
                contexto += f"- Goles por 90min: {goles_90:.2f}\n"
            
            if 'asistencias/90' in datos_wyscout:
                asist_90 = safe_float(datos_wyscout['asistencias/90'])
                contexto += f"- Asistencias por 90min: {asist_90:.2f}\n"
            
            if '%duelos_ganados,_' in datos_wyscout:
                duelos_pct = safe_float(datos_wyscout['%duelos_ganados,_'])
                contexto += f"- Duelos ganados: {duelos_pct:.1f}%\n"
            
            if '%precisión_pases,_' in datos_wyscout:
                pases_pct = safe_float(datos_wyscout['%precisión_pases,_'])
                contexto += f"- Precisión de pases: {pases_pct:.1f}%\n"
        
        return contexto
    
    def generar_resumen_observaciones(self, informes_list: List[Dict], tipo_resumen: str = "analisis_profesional") -> Dict:
        """
        Genera resúmenes usando IA con enfoque directivo profesional
        """
        if not self.verificar_conexion():
            return {"error": "API no configurada"}
        
        if not informes_list:
            return {"error": "No hay informes para analizar"}
        
        # Obtener datos del jugador
        primer_informe = informes_list[0]
        nombre_jugador = primer_informe.get('jugador_nombre', 'Jugador')
        equipo = primer_informe.get('equipo', '')
        
        # Intentar obtener datos Wyscout
        datos_wyscout = self.obtener_datos_wyscout_jugador(nombre_jugador, equipo)
        grupo_posicion = 'general'
        
        if datos_wyscout:
            # Determinar posición para contexto relevante
            posicion = datos_wyscout.get('pos_principal', 'N/A')
            grupo_posicion = self._determinar_grupo_posicion(posicion)
        
        # Preparar contexto
        contexto_base = self._preparar_contexto_informes(informes_list)
        contexto_wyscout = self.generar_contexto_wyscout(datos_wyscout, grupo_posicion)
        contexto_completo = contexto_base + contexto_wyscout
        
        recomendacion_principal = informes_list[0].get('recomendacion', 'N/A') if informes_list else 'N/A'
        
        # CONTEXTO FUTBOLÍSTICO PROFESIONAL
        contexto_terminologia = """
    IMPORTANTE - USA SIEMPRE ESTA TERMINOLOGÍA PROFESIONAL:

    NUNCA DIGAS: "buen jugador", "juega bien", "tiene calidad", "corre mucho"

    CONCEPTOS TÉCNICOS:
    - Primer toque, control orientado, conducción en velocidad
    - Golpeo con ambas piernas, definición en el área
    - Centros al primer/segundo palo, pase filtrado

    CONCEPTOS TÁCTICOS:
    - Juego entre líneas, tercer hombre, desdoblamiento
    - Presión alta/media/baja, bloque defensivo, línea de pase
    - Transición defensa-ataque, repliegue, basculación

    CONCEPTOS FÍSICOS:
    - Capacidad de repetir esfuerzos, potencia en el duelo aéreo
    - Velocidad en los primeros metros, resistencia a la intensidad

    CONCEPTOS MENTALES:
    - Lectura del juego, timing de llegada, personalidad con balón
    - Concentración en momentos clave, liderazgo en campo

    POR POSICIÓN:
    - Portero: reflejos, blocaje, juego con pies, salidas
    - Central: anticipación, salida de balón, juego aéreo defensivo
    - Lateral: proyección ofensiva, repliegue, centro desde banda
    - Mediocentro: distribución, equilibrio entre líneas, recuperación
    - Mediapunta: último pase, espacios entre líneas, llegada al área
    - Extremo: uno contra uno, diagonal al área, amplitud
    - Delantero: definición, desmarque de ruptura, referencia en área
    """
        
        # NUEVOS PROMPTS MEJORADOS CON CONTEXTO
        prompts = {
        "analisis_profesional": f"""
    Eres un asistente que ayuda a sintetizar las observaciones de múltiples informes de scouting.

    IMPORTANTE: Tu análisis debe basarse EXCLUSIVAMENTE en:
    1. Las OBSERVACIONES escritas por el scout (fortalezas, debilidades, observaciones adicionales)
    2. Las notas numéricas como contexto secundario
    3. Los datos Wyscout solo para complementar

    DATOS DE LOS INFORMES:
    {contexto_completo}

    INSTRUCCIONES:
    - Resume y agrupa las observaciones del scout de todos los partidos
    - Identifica patrones: ¿qué aspectos se repiten en múltiples informes?
    - Destaca la evolución: ¿mejoró o empeoró en algo según las observaciones?
    - Si el scout menciona situaciones específicas de partidos, inclúyelas
    - NO inventes información que no esté en las observaciones del scout
    - Máximo 250 palabras

    SÍNTESIS DE OBSERVACIONES:""",

            "patron_observaciones": f"""
    Analiza las observaciones del scout en los {len(informes_list)} informes disponibles.

    OBSERVACIONES DEL SCOUT:
    {contexto_completo}

    Identifica y resume:
    1. ASPECTOS CONSISTENTES (mencionados en 3+ informes)
    2. EVOLUCIÓN OBSERVADA (cambios entre primeros y últimos informes)
    3. SITUACIONES DESTACADAS (momentos específicos que el scout resaltó)
    4. CONTEXTO VS RIVALES (cómo varió el rendimiento según el rival)

    Basa TODO en las observaciones textuales del scout. No inventes.""",

            "sintesis_ejecutiva": f"""
    Resume en 100 palabras las observaciones clave de {len(informes_list)} informes de scouting.

    OBSERVACIONES COMPLETAS:
    {contexto_completo}

    Extrae SOLO lo que el scout escribió sobre:
    - Principal fortaleza observada (la más mencionada)
    - Principal debilidad detectada (la más recurrente)
    - Evolución entre el primer y último informe
    - Recomendación final del scout

    Usa las palabras del scout, no inventes análisis propios."""
        }
        
        try:
            # Generar resumen según tipo
            prompt = prompts.get(tipo_resumen, prompts['analisis_profesional'])
            
            payload = {
                "model": self.modelo,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.6,      # Más bajo para Mistral (más consistente)
                    "num_predict": 500,      # Un poco más para Mistral
                    "top_p": 0.85,          # Ajustado para mejor español
                    "repeat_penalty": 1.2,   # Mayor para evitar repeticiones
                    "seed": 42              # Para reproducibilidad
                }
            }
            
            response = requests.post(self.endpoint, json=payload)
            
            if response.status_code == 200:
                resultado = response.json()
                texto_generado = resultado.get('response', '').strip()
                
                # Para tipo "perfil_rendimiento", asegurar dos párrafos
                if tipo_resumen == "perfil_rendimiento":
                    # Verificar que tenga estructura de dos párrafos
                    if '\n\n' not in texto_generado:
                        # Forzar separación si no existe
                        palabras = texto_generado.split()
                        mitad = len(palabras) // 2
                        parte1 = ' '.join(palabras[:mitad])
                        parte2 = ' '.join(palabras[mitad:])
                        texto_generado = f"{parte1}\n\n{parte2}"
                
                return {
                    tipo_resumen: texto_generado,
                    'tiene_datos_wyscout': datos_wyscout is not None,
                    'grupo_posicion': grupo_posicion
                }
            else:
                return {"error": f"Error en respuesta: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"Error generando resumen con Ollama: {str(e)}"}
    
    def _preparar_contexto_informes(self, informes_list: List[Dict]) -> str:
        """
        Prepara el contexto PRIORIZANDO las observaciones textuales del scout
        """
        contexto = f"RESUMEN DE {len(informes_list)} INFORMES DE SCOUTING:\n\n"
        
        # Ordenar por fecha
        informes_ordenados = sorted(informes_list, key=lambda x: x.get('fecha_creacion', ''))
        
        for i, informe in enumerate(informes_ordenados, 1):
            # Datos básicos del partido
            equipo_jugador = informe.get('equipo', '')
            equipo_local = informe.get('equipo_local', '')
            equipo_visitante = informe.get('equipo_visitante', '')
            
            rival = equipo_visitante if equipo_jugador == equipo_local else equipo_local
            fecha = informe.get('fecha_partido', informe.get('fecha_creacion', 'N/A'))[:10]
            
            contexto += f"═══ INFORME {i}/{len(informes_list)} - vs {rival} ({fecha}) ═══\n"
            contexto += f"Nota general: {informe.get('nota_general', 0)}/10 | "
            contexto += f"Tipo: {informe.get('tipo_evaluacion', 'campo')} | "
            contexto += f"Minutos: {informe.get('minutos_observados', 90)}'\n\n"
            
            # PRIORIDAD 1: OBSERVACIONES TEXTUALES
            contexto += "OBSERVACIONES DEL SCOUT:\n"
            
            if informe.get('fortalezas'):
                contexto += f"→ FORTALEZAS: {informe['fortalezas']}\n"
            
            if informe.get('debilidades'):
                contexto += f"→ DEBILIDADES: {informe['debilidades']}\n"
            
            if informe.get('observaciones'):
                contexto += f"→ NOTAS ADICIONALES: {informe['observaciones']}\n"
            
            # Si no hay observaciones textuales, indicarlo
            if not any([informe.get('fortalezas'), informe.get('debilidades'), informe.get('observaciones')]):
                contexto += "→ Sin observaciones textuales detalladas en este informe\n"
            
            # Datos numéricos como contexto secundario
            if informe.get('nota_general', 0) >= 8:
                contexto += f"→ Rendimiento destacado (Nota: {informe.get('nota_general')}/10)\n"
            elif informe.get('nota_general', 0) <= 5:
                contexto += f"→ Rendimiento bajo (Nota: {informe.get('nota_general')}/10)\n"
            
            contexto += "\n"
        
        return contexto
    
    def _calcular_promedio_categoria(self, informe: Dict, categoria: str) -> float:
        """Calcula el promedio de una categoría específica"""
        campos_por_categoria = {
            'tecnico': ['control_balon', 'primer_toque', 'pase_corto', 'pase_largo', 'finalizacion', 'regate'],
            'tactico': ['vision_juego', 'posicionamiento', 'marcaje', 'pressing', 'transiciones'],
            'fisico': ['velocidad', 'resistencia', 'fuerza', 'salto', 'agilidad'],
            'mental': ['concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision']
        }
        
        campos = campos_por_categoria.get(categoria, [])
        valores = [informe.get(campo, 0) for campo in campos if campo in informe and informe[campo] > 0]
        
        return sum(valores) / len(valores) if valores else 0
    
    def _determinar_grupo_posicion(self, pos_principal):
        """
        Determina el grupo de posición basándose en la columna pos_principal
        Versión local para evitar importación con emojis
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
        elif pos in ['LW', 'RW', 'LM', 'RM', 'WF', 'EXTREMO', 'WINGER', 'AML', 'AMR', 'EXT', 'ED', 'EI']:
            return 'extremo'
        elif pos in ['CF', 'ST', 'FW', 'DC', 'DEL', 'DELANTERO', 'STRIKER', 'FORWARD', 'SS']:
            return 'delantero'
        else:
            return 'general'


def agregar_resumenes_ia_al_pdf(pdf, resumenes, y_position=None):
    """
    Agrega los resúmenes de IA al PDF
    
    Args:
        pdf: Objeto FPDF
        resumenes: Dict con los resúmenes generados por IA
        y_position: Posición Y donde empezar (None = posición actual)
    """
    if not resumenes or 'error' in resumenes:
        return
    
    if y_position:
        pdf.set_y(y_position)
    
    # Título de sección
    pdf.set_font('Helvetica', 'B', 14)
    pdf.set_text_color(36, 40, 42)
    pdf.cell(0, 10, 'ANALISIS INTELIGENTE (IA)', 0, 1, 'C')
    pdf.ln(5)
    
    # Resumen ejecutivo
    if 'ejecutivo' in resumenes and resumenes['ejecutivo']:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 123, 191)
        pdf.cell(0, 6, 'Resumen Ejecutivo:', 0, 1)
        
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5, resumenes['ejecutivo'], 0, 'J')
        pdf.ln(5)
    
    # Fortalezas y áreas de mejora en columnas
    y_antes = pdf.get_y()
    
    # Fortalezas
    pdf.set_xy(15, y_antes)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(40, 167, 69)
    pdf.cell(85, 6, 'Fortalezas:', 0, 1)
    
    if 'fortalezas' in resumenes and resumenes['fortalezas']:
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.set_x(15)
        pdf.multi_cell(85, 4, resumenes['fortalezas'], 0, 'L')
    
    # Áreas de mejora
    pdf.set_xy(105, y_antes)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(220, 53, 69)
    pdf.cell(85, 6, 'Areas de mejora:', 0, 1)
    
    if 'areas_mejora' in resumenes and resumenes['areas_mejora']:
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(60, 60, 60)
        pdf.set_x(105)
        pdf.multi_cell(85, 4, resumenes['areas_mejora'], 0, 'L')
    
    pdf.ln(10)


def mostrar_resumenes_ia_streamlit(df_filtrado):
    """
    Muestra los resúmenes de IA en Streamlit con enfoque directivo
    """
    if df_filtrado.empty:
        return
    
    st.markdown("### 🤖 Análisis Técnico-Táctico con IA")
    
    # Selector de jugador para análisis
    jugadores_con_multiples = df_filtrado.groupby('jugador_nombre').size()
    jugadores_con_multiples = jugadores_con_multiples[jugadores_con_multiples >= 2].index.tolist()
    
    if not jugadores_con_multiples:
        st.info("💡 El análisis con IA requiere al menos 2 informes del mismo jugador")
        return
    
    col_ia1, col_ia2 = st.columns([2, 1])
    
    with col_ia1:
        jugador_analizar = st.selectbox(
            "Selecciona jugador para análisis:",
            jugadores_con_multiples,
            key="jugador_ia_analisis"
        )
    
    with col_ia2:
        tipo_resumen = st.selectbox(
            "Tipo de análisis:",
            ["analisis_profesional", "ejecutivo", "proyeccion"],
            format_func=lambda x: {
                "analisis_profesional": "Análisis Completo",
                "ejecutivo": "Resumen Ejecutivo",
                "proyeccion": "Proyección y Potencial"
            }[x],
            key="tipo_resumen_ia"
        )
    
    if st.button("🔍 Generar Análisis IA", type="primary", use_container_width=True):
        # Filtrar informes del jugador
        informes_jugador = df_filtrado[df_filtrado['jugador_nombre'] == jugador_analizar]
        
        # Convertir a lista de diccionarios
        informes_list = informes_jugador.to_dict('records')
        
        with st.spinner(f"🤖 Analizando {len(informes_list)} informes de {jugador_analizar}..."):
            try:
                ia_scout = ResumenScoutingIA()
                
                if ia_scout.verificar_conexion():
                    resultado = ia_scout.generar_resumen_observaciones(
                        informes_list, 
                        tipo_resumen=tipo_resumen
                    )
                    
                    if 'error' not in resultado:
                        st.success("✅ Análisis generado exitosamente")
                        
                        # Mostrar según tipo de análisis
                        if tipo_resumen == "ejecutivo":
                            with st.container():
                                st.markdown("#### 📊 Resumen Ejecutivo para Dirección Deportiva")
                                st.info(resultado.get('ejecutivo', 'No disponible'))
                        
                        elif tipo_resumen == "analisis_profesional":
                            with st.container():
                                st.markdown("#### 📋 Informe Técnico-Táctico Completo")
                                
                                # Crear expander para mejor visualización
                                with st.expander("Ver análisis completo", expanded=True):
                                    st.write(resultado.get('analisis_profesional', 'No disponible'))
                                
                                # Indicador de datos Wyscout
                                if resultado.get('tiene_datos_wyscout'):
                                    st.success("📈 Análisis enriquecido con datos estadísticos de Wyscout")
                        
                        elif tipo_resumen == "proyeccion":
                            with st.container():
                                st.markdown("#### 🔮 Proyección y Valoración de Potencial")
                                
                                # Mostrar en columnas para mejor lectura
                                col1, col2 = st.columns([3, 1])
                                
                                with col1:
                                    st.write(resultado.get('proyeccion', 'No disponible'))
                                
                                with col2:
                                    # Extraer recomendación del primer informe
                                    recom = informes_list[0].get('recomendacion', 'N/A')
                                    
                                    st.markdown("**Decisión Scout:**")
                                    if 'fichar' in recom.lower():
                                        st.success("✅ FICHAR")
                                    elif 'seguir' in recom.lower():
                                        st.warning("👀 SEGUIR")
                                    elif 'descartar' in recom.lower():
                                        st.error("❌ DESCARTAR")
                                    else:
                                        st.info("❔ " + recom.upper())
                        
                        # Botón para descargar análisis
                        texto_descarga = f"""ANÁLISIS TÉCNICO-TÁCTICO
Jugador: {jugador_analizar}
Fecha: {datetime.now().strftime("%d/%m/%Y")}
Tipo: {tipo_resumen.replace('_', ' ').title()}

{resultado.get(tipo_resumen, 'No disponible')}

---
Generado por Sistema de Scouting Profesional con IA"""
                        
                        st.download_button(
                            label="📥 Descargar Análisis",
                            data=texto_descarga,
                            file_name=f"analisis_{jugador_analizar}_{datetime.now().strftime('%Y%m%d')}.txt",
                            mime="text/plain",
                            key="download_analisis_ia"
                        )
                        
                    else:
                        st.error(f"❌ Error: {resultado.get('error', 'Error desconocido')}")
                else:
                    st.error("❌ No se pudo conectar con el servicio de IA (Ollama)")
                    st.info("Asegúrate de que Ollama esté ejecutándose en http://localhost:11434")
                    
            except Exception as e:
                st.error(f"❌ Error generando análisis: {str(e)}")
                print(f"Error detallado: {e}")
                import traceback
                traceback.print_exc()

def crear_tabla_comparativa(informes_jugador, datos_wyscout):
    """
    Crea una tabla comparativa entre evaluaciones del scout y datos Wyscout
    """
    # Preparar datos para la comparación
    comparacion_data = []
    
    # Métricas técnicas
    if datos_wyscout:
        comparacion_data.append({
            "Categoría": "TÉCNICA",
            "Evaluación Scout (promedio)": calcular_promedio_categoria_informes(informes_jugador, 'tecnico'),
            "Dato Wyscout relacionado": f"{datos_wyscout.get('%precisión_pases,_', 'N/A')}% precisión pases",
            "Observación": "Coherencia entre control/pases del scout y precisión objetiva"
        })
        
        # Capacidad ofensiva
        comparacion_data.append({
            "Categoría": "FINALIZACIÓN",
            "Evaluación Scout (promedio)": calcular_promedio_campo(informes_jugador, 'finalizacion'),
            "Dato Wyscout relacionado": f"{datos_wyscout.get('goles/90', 'N/A')} goles/90",
            "Observación": "Relación entre valoración de finalización y producción goleadora"
        })
        
        # Creatividad
        comparacion_data.append({
            "Categoría": "VISIÓN DE JUEGO",
            "Evaluación Scout (promedio)": calcular_promedio_campo(informes_jugador, 'vision_juego'),
            "Dato Wyscout relacionado": f"{datos_wyscout.get('jugadas_claves/90', 'N/A')} pases clave/90",
            "Observación": "Creatividad observada vs pases clave generados"
        })
    
    # Mostrar tabla
    if comparacion_data:
        df_comparacion = pd.DataFrame(comparacion_data)
        st.dataframe(df_comparacion, use_container_width=True)
        
        # Insights adicionales
        st.markdown("##### 💡 Insights de la comparación:")
        st.markdown("""
        - **Alta coherencia**: Las evaluaciones del scout coinciden con los datos objetivos
        - **Discrepancias**: Pueden indicar aspectos no capturados por las estadísticas
        - **Valor agregado del scout**: Identifica potencial y aspectos cualitativos
        """)


def calcular_promedio_categoria_informes(informes, categoria):
    """Calcula el promedio de una categoría en todos los informes"""
    valores = []
    campos_map = {
        'tecnico': ['control_balon', 'primer_toque', 'pase_corto', 'pase_largo', 'finalizacion', 'regate'],
        'tactico': ['vision_juego', 'posicionamiento', 'marcaje', 'pressing', 'transiciones'],
        'fisico': ['velocidad', 'resistencia', 'fuerza', 'salto', 'agilidad'],
        'mental': ['concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision']
    }
    
    for informe in informes:
        for campo in campos_map.get(categoria, []):
            if campo in informe and informe[campo] > 0:
                valores.append(informe[campo])
    
    return f"{sum(valores)/len(valores):.1f}/10" if valores else "N/A"


def calcular_promedio_campo(informes, campo):
    """Calcula el promedio de un campo específico"""
    valores = [inf[campo] for inf in informes if campo in inf and inf[campo] > 0]
    return f"{sum(valores)/len(valores):.1f}/10" if valores else "N/A"

def _preparar_datos_para_prompt(self, informes_df):
    """
    Prepara los datos de los informes para el prompt de la IA
    Versión actualizada para estructura JSON
    """
    datos_procesados = []
    
    for _, informe in informes_df.iterrows():
        # Información básica
        datos_informe = {
            'fecha': informe.get('fecha_creacion', 'N/A')[:10],
            'rival': f"{informe.get('equipo_local', 'N/A')} vs {informe.get('equipo_visitante', 'N/A')}",
            'posicion': informe.get('posicion', 'N/A'),
            'nota_general': informe.get('nota_general', 0),
            'tipo': informe.get('tipo_evaluacion', 'campo'),
            'minutos': informe.get('minutos_observados', 90),
            'fortalezas_texto': informe.get('fortalezas', ''),
            'debilidades_texto': informe.get('debilidades', ''),
            'observaciones': informe.get('observaciones', '')
        }
        
        # Extraer métricas del JSON
        metricas_json = informe.get('metricas', {})
        
        if isinstance(metricas_json, str):
            try:
                import json
                metricas_json = json.loads(metricas_json)
            except:
                metricas_json = {}
        
        if metricas_json:
            # Añadir promedios si existen
            if 'promedios' in metricas_json:
                datos_informe['promedios'] = metricas_json['promedios']
            
            # Para evaluación de campo
            if metricas_json.get('tipo') == 'campo' and 'evaluaciones' in metricas_json:
                datos_informe['evaluaciones_campo'] = metricas_json['evaluaciones']
            
            # Para video completo
            elif metricas_json.get('tipo') == 'video_completo' and 'categorias' in metricas_json:
                # Extraer métricas destacadas
                metricas_destacadas = {}
                
                for categoria, metricas_cat in metricas_json['categorias'].items():
                    # Encontrar las 2 mejores y 2 peores de cada categoría
                    if metricas_cat:
                        items_ordenados = sorted(metricas_cat.items(), key=lambda x: x[1], reverse=True)
                        
                        # Mejores
                        if len(items_ordenados) >= 2:
                            metricas_destacadas[f'{categoria}_mejores'] = [
                                f"{items_ordenados[0][0]} ({items_ordenados[0][1]}/10)",
                                f"{items_ordenados[1][0]} ({items_ordenados[1][1]}/10)"
                            ]
                        
                        # Peores
                        if len(items_ordenados) >= 4:
                            metricas_destacadas[f'{categoria}_peores'] = [
                                f"{items_ordenados[-2][0]} ({items_ordenados[-2][1]}/10)",
                                f"{items_ordenados[-1][0]} ({items_ordenados[-1][1]}/10)"
                            ]
                
                datos_informe['metricas_destacadas'] = metricas_destacadas
        
        datos_procesados.append(datos_informe)
    
    return datos_procesados