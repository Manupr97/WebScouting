# utils/besoccer_scraper.py
# ==========================================
# BESOCCER SCRAPER - VERSIÓN CORREGIDA Y OPTIMIZADA
# CORREGIDO: Elimina </div> en titulares y mejora posiciones de suplentes
# ==========================================

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import json
import time
import os
import re

class BeSoccerScraper:
    """Scraper optimizado que usa únicamente livescore de BeSoccer - VERSIÓN CORREGIDA"""
    def __init__(self):
        self.session = requests.Session()
        # Headers para simular navegador real
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # URLs optimizadas - SOLO livescore de BeSoccer
        self.urls_livescore = [
            'https://es.besoccer.com/livescore',
            'https://es.besoccer.com/partidos/hoy',
            'https://es.besoccer.com/resultados/hoy'
        ]
        
        # Cache optimizado
        self.cache = {}
        self.cache_timeout = 1800  # 30 minutos
        
        # Cache específico para URLs oficiales (más largo)
        self.cache_urls_oficiales = {}
        self.cache_urls_timeout = 3600  # 1 hora

    def _limpiar_texto_html(self, texto):
        """
        FUNCIÓN CRÍTICA: Limpia completamente caracteres HTML del texto
        """
        if not texto:
            return ""
        
        # Convertir a string si no lo es
        texto_str = str(texto)
        
        # Eliminar TODOS los tags HTML incluyendo </div>
        import re
        texto_limpio = re.sub(r'<[^>]+>', '', texto_str)
        
        # Eliminar espacios extra y caracteres especiales
        texto_limpio = re.sub(r'\s+', ' ', texto_limpio).strip()
        
        # Eliminar caracteres de control
        texto_limpio = ''.join(char for char in texto_limpio if char.isprintable())
        
        return texto_limpio
    
    def obtener_alineaciones_partido(self, match_id_o_url, equipo_local="", equipo_visitante=""):
        """
        Obtiene alineaciones usando URLs oficiales extraídas de livescore
        CORREGIDO: Soluciona problemas de búsqueda y extracción
        """
        try:
            print(f"🔍 Procesando partido: {match_id_o_url}")
            
            # Determinar match_id
            if match_id_o_url.startswith('http'):
                match_id = self._extraer_match_id_de_url(match_id_o_url)
                url_partido_oficial = match_id_o_url
            else:
                match_id = match_id_o_url
                url_partido_oficial = None
            
            # Verificar cache de alineaciones
            cache_key = f"alineaciones_{match_id}"
            if self._verificar_cache(cache_key):
                print(f"✅ Usando alineaciones del cache")
                return self.cache[cache_key]['data']
            
            # PASO 1: Obtener URL oficial (cache o búsqueda)
            if not url_partido_oficial:
                print(f"🔍 Buscando URL oficial para partido {match_id}...")
                url_partido_oficial = self._obtener_url_oficial_optimizada(match_id, equipo_local, equipo_visitante)
                
                if not url_partido_oficial:
                    # FALLBACK: Construir URL directa si tenemos el match_id
                    if match_id and match_id != 'unknown':
                        url_partido_oficial = f"https://es.besoccer.com/partido/{match_id}"
                        print(f"🔄 Usando URL directa: {url_partido_oficial}")
                    else:
                        print("❌ No se encontró URL oficial del partido")
                        return {
                            'encontrado': False,
                            'error': 'URL oficial no encontrada',
                            'alineacion_local': [],
                            'alineacion_visitante': [],
                            'mensaje': 'No se pudo encontrar la URL oficial del partido en livescore'
                        }
            
            print(f"✅ URL oficial: {url_partido_oficial}")
            
            # PASO 2: Construir URL de alineaciones
            url_alineaciones = self._construir_url_alineaciones_desde_oficial(url_partido_oficial)
            print(f"🎯 URL de alineaciones: {url_alineaciones}")
            
            # PASO 3: Obtener alineaciones con manejo de errores mejorado
            try:
                response = self.session.get(url_alineaciones, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                alineaciones_info = self._extraer_alineaciones_besoccer_corregido(soup)
                
                if not alineaciones_info['encontrado']:
                    # Intentar método alternativo
                    print("🔄 Intentando método alternativo...")
                    alineaciones_info = self._extraer_alineaciones_metodo_alternativo(soup)
                
                if not alineaciones_info['encontrado']:
                    alineaciones_info = self._analizar_estructura_alineaciones(soup, url_alineaciones)
                
                # Guardar en cache si se encontraron alineaciones
                if alineaciones_info['encontrado']:
                    self._guardar_cache(cache_key, alineaciones_info)
                    # También guardar la URL oficial en cache
                    self._guardar_url_oficial_cache(match_id, url_partido_oficial)
                
                return alineaciones_info
                
            except requests.exceptions.RequestException as e:
                print(f"❌ Error de conexión: {str(e)}")
                return {
                    'encontrado': False,
                    'error': f'Error de conexión: {str(e)}',
                    'alineacion_local': [],
                    'alineacion_visitante': [],
                    'mensaje': f'No se pudo conectar a la página de alineaciones'
                }
            
        except Exception as e:
            print(f"❌ Error obteniendo alineaciones para {match_id_o_url}: {e}")
            return {
                'encontrado': False,
                'error': str(e),
                'alineacion_local': [],
                'alineacion_visitante': [],
                'mensaje': f'Error al obtener alineaciones: {str(e)}'
            }

    def _extraer_alineaciones_besoccer_corregido(self, soup):
        """
        VERSIÓN CORREGIDA: Extrae alineaciones con búsqueda mejorada
        CORREGIDO: panel-bench está SEPARADO del panel-lineup
        """
        print("🔍 Extrayendo alineaciones con versión CORREGIDA...")
        
        # PASO 1: Buscar panel-lineup para TITULARES
        panel_lineup = soup.find('div', class_='panel panel-lineup')
        
        # PASO 2: Buscar panel-bench para SUPLENTES (separado)
        panel_bench = soup.find('div', class_='panel panel-bench')
        
        print(f"  🔸 Panel lineup encontrado: {panel_lineup is not None}")
        print(f"  🔸 Panel bench encontrado: {panel_bench is not None}")
        
        if panel_lineup:
            resultado_titulares = self._extraer_titulares_desde_panel_lineup(panel_lineup)
            
            # Agregar suplentes si existe panel-bench
            if panel_bench:
                suplentes_procesados = self._extraer_suplentes_desde_panel_bench_separado(panel_bench)
                
                # Combinar titulares y suplentes
                for jugador_suplente in suplentes_procesados:
                    equipo = jugador_suplente.get('equipo', 'desconocido')
                    
                    if equipo == 'local':
                        resultado_titulares['alineacion_local'].append(jugador_suplente)
                    elif equipo == 'visitante':
                        resultado_titulares['alineacion_visitante'].append(jugador_suplente)
                    else:
                        # Distribución equilibrada
                        suplentes_local = len([j for j in resultado_titulares['alineacion_local'] if not j['es_titular']])
                        suplentes_visitante = len([j for j in resultado_titulares['alineacion_visitante'] if not j['es_titular']])
                        
                        if suplentes_local <= suplentes_visitante:
                            resultado_titulares['alineacion_local'].append(jugador_suplente)
                        else:
                            resultado_titulares['alineacion_visitante'].append(jugador_suplente)
                
                # Actualizar mensaje y método
                local_total = len(resultado_titulares['alineacion_local'])
                visitante_total = len(resultado_titulares['alineacion_visitante'])
                local_titulares = len([j for j in resultado_titulares['alineacion_local'] if j.get('es_titular', True)])
                local_suplentes = local_total - local_titulares
                visitante_titulares = len([j for j in resultado_titulares['alineacion_visitante'] if j.get('es_titular', True)])
                visitante_suplentes = visitante_total - visitante_titulares
                
                resultado_titulares['metodo'] = 'panel_lineup_y_bench_separados'
                resultado_titulares['mensaje'] = f'Completo: Local {local_titulares}T+{local_suplentes}S vs Visitante {visitante_titulares}T+{visitante_suplentes}S'
                
                print(f"  ✅ COMPLETO: Local {local_titulares}T+{local_suplentes}S, Visitante {visitante_titulares}T+{visitante_suplentes}S")
            
            return resultado_titulares
        
        # MÉTODO 2: Buscar con selectores originales si no hay panel-lineup
        titulares = soup.select('[data-cy="fieldPlayer"]')
        suplentes = soup.select('[data-cy="benchPlayer"]')
        
        print(f"  🔸 Titulares data-cy encontrados: {len(titulares)}")
        print(f"  🔸 Suplentes data-cy encontrados: {len(suplentes)}")
        
        if not titulares:
            titulares = soup.select('.lineup.local .player-wrapper a, .lineup.visitor .player-wrapper a')
            print(f"  🔄 Fallback - Titulares encontrados: {len(titulares)}")
        
        if not titulares:
            return {'encontrado': False}
        
        return self._procesar_jugadores_estandar(titulares, suplentes)

    def _extraer_titulares_desde_panel_lineup(self, panel_lineup):
        """
        Extrae SOLO titulares desde panel-lineup
        """
        print("🔍 Extrayendo titulares desde panel-lineup...")
        
        player_wrappers = panel_lineup.find_all('div', class_='player-wrapper')
        print(f"  🔸 Player-wrappers (titulares) encontrados: {len(player_wrappers)}")
        
        if not player_wrappers:
            return {'encontrado': False}
        
        alineacion_local = []
        alineacion_visitante = []
        
        # Procesar SOLO titulares
        for wrapper in player_wrappers:
            jugador = self._extraer_jugador_desde_wrapper(wrapper, es_titular=True)
            if jugador:
                equipo = self._determinar_equipo_jugador(wrapper)
                
                if equipo == 'local':
                    alineacion_local.append(jugador)
                elif equipo == 'visitante':
                    alineacion_visitante.append(jugador)
                else:
                    # Distribución alternada
                    if len(alineacion_local) <= len(alineacion_visitante):
                        alineacion_local.append(jugador)
                    else:
                        alineacion_visitante.append(jugador)
        
        print(f"  ✅ Titulares procesados: Local {len(alineacion_local)}, Visitante {len(alineacion_visitante)}")
        
        return {
            'encontrado': True,
            'metodo': 'solo_titulares',
            'alineacion_local': alineacion_local,
            'alineacion_visitante': alineacion_visitante,
            'mensaje': f'Solo titulares: {len(alineacion_local)} vs {len(alineacion_visitante)}'
        }

    def _extraer_suplentes_desde_panel_bench_separado(self, panel_bench):
        """
        NUEVA FUNCIÓN: Extrae suplentes desde panel-bench SEPARADO
        """
        print("🔍 Extrayendo suplentes desde panel-bench separado...")
        
        suplentes_procesados = []
        
        # Buscar todos los enlaces de suplentes en col-bench
        suplentes_links = panel_bench.find_all('a', class_='col-bench')
        print(f"  🔸 Enlaces de suplentes encontrados: {len(suplentes_links)}")
        
        for link in suplentes_links:
            jugador_suplente = self._extraer_suplente_desde_col_bench(link)
            if jugador_suplente:
                suplentes_procesados.append(jugador_suplente)
        
        print(f"  ✅ Suplentes procesados: {len(suplentes_procesados)}")
        return suplentes_procesados

    def _extraer_posicion_suplente_mejorada(self, link):
        """
        Extrae posición de suplente desde role-box → t-up
        ACTUALIZADO: Mejor manejo de la estructura HTML y extracción del texto de posición
        """
        try:
            # Buscar role-box
            role_box = link.find('div', class_='role-box')
            if not role_box:
                print(f"      ⚠️ No se encontró role-box")
                return "N/A"
            
            # Buscar span t-up dentro de role-box (NOTA: es span, no div)
            t_up = role_box.find('span', class_='t-up')
            if not t_up:
                print(f"      ⚠️ No se encontró span.t-up en role-box")
                return "N/A"
            
            # Método 1: Obtener el texto directo del t-up
            # Clonar el elemento para no modificar el original
            t_up_clone = t_up.__copy__()
            
            # Remover el span del número si existe
            numero_span = t_up_clone.find('span', class_='number bold mr3')
            if numero_span:
                numero_span.decompose()  # Eliminar el elemento del árbol
            
            # Obtener el texto restante (que debería ser la posición)
            posicion_texto = t_up_clone.get_text(strip=True)
            
            # Si no obtuvimos nada con el método 1, intentar método 2
            if not posicion_texto:
                # Método 2: Obtener todo el contenido y procesarlo
                contenido_completo = t_up.get_text(separator=' ', strip=True)
                # Dividir por espacios
                partes = contenido_completo.split()
                
                # Si hay al menos 2 partes, la posición suele ser la última
                if len(partes) >= 2:
                    # Filtrar partes que sean números
                    partes_no_numericas = [p for p in partes if not p.isdigit()]
                    if partes_no_numericas:
                        posicion_texto = partes_no_numericas[-1]  # Tomar la última parte no numérica
                    else:
                        posicion_texto = partes[-1]  # Si todo falla, tomar la última parte
                elif len(partes) == 1 and not partes[0].isdigit():
                    posicion_texto = partes[0]
                else:
                    posicion_texto = ""
            
            # Debug
            print(f"      🔍 Posición extraída del suplente: '{posicion_texto}'")
            
            # Limpiar y mapear la posición
            if posicion_texto and len(posicion_texto) <= 10:  # Validar longitud razonable
                posicion_limpia = self._limpiar_texto_html(posicion_texto)
                posicion_final = self._mapear_posicion(posicion_limpia) if posicion_limpia else "N/A"
                print(f"      ✅ Posición final del suplente: {posicion_final}")
                return posicion_final
            else:
                print(f"      ⚠️ Posición no válida o muy larga: '{posicion_texto}'")
                return "N/A"
                
        except Exception as e:
            print(f"      ❌ Error extrayendo posición de suplente: {e}")
            import traceback
            traceback.print_exc()
            return "N/A"
    
    def _extraer_suplente_desde_col_bench(self, link):
        """
        FUNCIÓN ACTUALIZADA: Extrae suplentes con posición MEJORADA
        Incluye mejor debug y manejo de errores
        """
        try:
            print(f"    🔍 Procesando suplente desde col-bench")
            
            # Determinar equipo desde las clases
            clases = link.get('class', [])
            equipo = 'desconocido'
            
            if 'local' in clases:
                equipo = 'local'
            elif 'visitor' in clases:
                equipo = 'visitante'
            
            print(f"    🔸 Equipo detectado: {equipo}")
            
            # PRIORIDAD 1: JSON-LD
            json_data = self._extraer_json_ld_jugador(link)
            
            if json_data:
                print(f"    ✅ JSON-LD encontrado para suplente: {json_data.get('name', 'Sin nombre')}")
                
                # En suplentes, el JSON-LD a veces no tiene la posición
                posicion_json = json_data.get('jobTitle') or json_data.get('jobtitle', '')
                
                # Si no hay posición en JSON-LD, buscarla en el HTML
                if not posicion_json or posicion_json == '':
                    print(f"    🔄 Posición vacía en JSON-LD, buscando en HTML...")
                    posicion = self._extraer_posicion_suplente_mejorada(link)
                else:
                    posicion = self._mapear_posicion(self._limpiar_texto_html(posicion_json))
                
                numero = self._extraer_numero_desde_wrapper(link)
                
                return {
                    'nombre': self._limpiar_texto_html(json_data.get('name', 'Sin nombre')),
                    'numero': numero,
                    'posicion': posicion,
                    'es_titular': False,
                    'imagen_url': json_data.get('image', ''),
                    'equipo': equipo
                }
            
            # PRIORIDAD 2: Método tradicional MEJORADO para suplentes
            print(f"    🔄 No hay JSON-LD, usando método tradicional")
            
            nombre = self._extraer_nombre_desde_wrapper(link)
            if not nombre:
                print(f"    ⚠️ No se pudo extraer nombre de suplente")
                return None
            
            # BUSCAR POSICIÓN ESPECÍFICAMENTE con el método actualizado
            posicion = self._extraer_posicion_suplente_mejorada(link)
            
            # Extraer número
            numero = "?"
            numero_elem = link.find('span', class_='number bold mr3')
            if numero_elem:
                numero = self._limpiar_texto_html(numero_elem.get_text())
            
            # Extraer imagen
            imagen_url = ""
            img_elem = link.find('img')
            if img_elem:
                imagen_url = img_elem.get('src', '')
            
            print(f"    ✅ Suplente procesado: {nombre} - #{numero} - Posición: {posicion}")
            
            return {
                'nombre': self._limpiar_texto_html(nombre),
                'numero': numero,
                'posicion': posicion,
                'es_titular': False,
                'imagen_url': imagen_url,
                'equipo': equipo
            }
            
        except Exception as e:
            print(f"    ❌ Error procesando suplente desde col-bench: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _extraer_jugador_desde_wrapper(self, wrapper, es_titular=True):
        """
        CORREGIDO: Extrae datos de jugador desde player-wrapper con limpieza de HTML
        Elimina </div> de titulares
        """
        try:
            print(f"    🔍 Extrayendo jugador desde wrapper (titular: {es_titular})")
            
            # PASO 1: Buscar JSON-LD (PRIORITARIO para posiciones exactas)
            json_data = self._extraer_json_ld_jugador(wrapper)
            
            if json_data:
                print(f"    ✅ JSON-LD encontrado: {json_data.get('name', 'Sin nombre')}")
                
                # Extraer posición del JSON-LD
                posicion_json = json_data.get('jobTitle') or json_data.get('jobtitle') or ''
                print(f"    📍 Posición en JSON-LD: '{posicion_json}'")
                
                # Si la posición está vacía en JSON-LD, buscarla en el HTML
                if not posicion_json or posicion_json == '':
                    print(f"    🔄 Posición vacía en JSON-LD, buscando en HTML...")
                    posicion = self._extraer_posicion_desde_wrapper(wrapper)
                else:
                    posicion = self._mapear_posicion(self._limpiar_texto_html(posicion_json))
                
                return {
                    'nombre': self._limpiar_texto_html(json_data.get('name', 'Sin nombre')),
                    'numero': self._extraer_numero_desde_wrapper(wrapper),
                    'posicion': posicion,
                    'es_titular': es_titular,
                    'imagen_url': json_data.get('image', '')
                }
            
            # PASO 2: Método tradicional si no hay JSON-LD (CON LIMPIEZA)
            nombre = self._extraer_nombre_desde_wrapper(wrapper)
            if not nombre:
                return None
            
            return {
                'nombre': self._limpiar_texto_html(nombre),
                'numero': self._extraer_numero_desde_wrapper(wrapper),
                'posicion': self._limpiar_texto_html(self._extraer_posicion_desde_wrapper(wrapper)),
                'es_titular': es_titular,
                'imagen_url': self._extraer_imagen_desde_wrapper(wrapper)
            }
            
        except Exception as e:
            print(f"    ❌ Error extrayendo jugador desde wrapper: {e}")
            return None

    def _extraer_nombre_desde_wrapper(self, wrapper):
        """
        FUNCIÓN CORREGIDA: Extrae nombre con limpieza HTML GARANTIZADA
        """
        try:
            # Estrategia 1: Selectores específicos
            nombre_elem = wrapper.select_one('.name-lineups, .name, .player-name')
            if nombre_elem:
                nombre_sucio = nombre_elem.get_text().strip()
                nombre_limpio = self._limpiar_texto_html(nombre_sucio)
                if nombre_limpio:
                    return nombre_limpio
            
            # Estrategia 2: Enlaces dentro del wrapper
            link = wrapper.select_one('a')
            if link:
                texto_sucio = link.get_text().strip()
                texto_limpio = self._limpiar_texto_html(texto_sucio)
                if texto_limpio and len(texto_limpio) > 2:
                    return texto_limpio.split('\n')[0].strip()
            
            # Estrategia 3: Buscar en texto general
            texto_completo = wrapper.get_text()
            texto_limpio = self._limpiar_texto_html(texto_completo)
            lineas = [linea.strip() for linea in texto_limpio.split('\n') if linea.strip()]
            
            for linea in lineas:
                if (len(linea) > 2 and 
                    re.match(r'^[A-Za-záéíóúñÁÉÍÓÚÑ\s\.\-\']+$', linea) and
                    not linea.isdigit() and 
                    not re.match(r'^\d+:\d+$', linea)):
                    return linea
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Error extrayendo nombre: {e}")
            return None

    def _extraer_posicion_desde_wrapper(self, wrapper):
        """
        CORREGIDO: Extrae posición desde player-wrapper con limpieza de HTML
        """
        try:
            # Estrategia 1: Selectores específicos
            pos_elem = wrapper.select_one('.role-box .t-up, .position, .player-position')
            if pos_elem:
                posicion_sucia = pos_elem.get_text().strip()
                posicion_limpia = self._limpiar_texto_html(posicion_sucia)  # Cambiar _limpiar_texto por _limpiar_texto_html
                if posicion_limpia and not posicion_limpia.isdigit():
                    return self._mapear_posicion(posicion_limpia)
            
            # Estrategia 2: Buscar en atributos
            for attr in ['data-position', 'data-role']:
                valor = wrapper.get(attr)
                if valor:
                    valor_limpio = self._limpiar_texto_html(valor)  # Cambiar aquí también
                    return self._mapear_posicion(valor_limpio)
            
            # Estrategia 3: Buscar en texto
            texto_completo = wrapper.get_text()
            texto_limpio = self._limpiar_texto_html(texto_completo)  # Y aquí
            posiciones_conocidas = ['POR', 'DEF', 'MED', 'DEL', 'Portero', 'Defensa', 'Medio', 'Delantero']
            for pos in posiciones_conocidas:
                if pos in texto_limpio:
                    return self._mapear_posicion(pos)
            
            return "N/A"
            
        except Exception as e:
            print(f"    ⚠️ Error extrayendo posición: {e}")
            return "N/A"

    def _extraer_json_ld_jugador(self, wrapper):
        """
        Extrae datos desde JSON-LD (application/ld+json) como el ejemplo que diste
        MEJORADO: Soporte para tanto jobtitle como jobTitle
        """
        try:
            # Buscar script con JSON-LD en el wrapper o sus hijos
            json_scripts = wrapper.find_all('script', type='application/ld+json')
            
            for script in json_scripts:
                try:
                    json_text = script.get_text().strip()
                    if json_text:
                        data = json.loads(json_text)
                        
                        # Verificar que sea de tipo Person (como en tu ejemplo)
                        if data.get('@type') == 'Person' and data.get('name'):
                            # MEJORADO: Soportar tanto jobtitle como jobTitle
                            job_title = data.get('jobTitle') or data.get('jobtitle', 'N/A')
                            
                            print(f"    🎯 JSON-LD extraído: {data.get('name')} - Posición: {job_title}")

                            return {
                                'name': data.get('name'),
                                'jobTitle': job_title,
                                'jobtitle': job_title,  # Compatibilidad
                                'image': data.get('image', ''),
                                'url': data.get('url', '')
                            }
                except json.JSONDecodeError as e:
                    print(f"    ⚠️ Error decodificando JSON-LD: {e}")
                    pass
            
            return None
            
        except Exception as e:
            print(f"    ⚠️ Error extrayendo JSON-LD: {e}")
            return None

    def _extraer_numero_desde_wrapper(self, wrapper):
        """Extrae número desde player-wrapper"""
        try:
            # Estrategia 1: Selectores específicos
            numero_elem = wrapper.select_one('.number, .player-number')
            if numero_elem:
                numero_texto = numero_elem.get_text().strip()
                numero_limpio = self._limpiar_texto_html(numero_texto)
                if numero_limpio.isdigit():
                    return numero_limpio
            
            # Estrategia 2: Buscar en atributos
            for attr in ['data-number', 'data-player-number']:
                valor = wrapper.get(attr)
                if valor and valor.isdigit():
                    return valor
            
            # Estrategia 3: Regex en HTML
            html_text = str(wrapper)
            numero_match = re.search(r'<span[^>]*class="[^"]*number[^"]*"[^>]*>(\d+)</span>', html_text)
            if numero_match:
                return numero_match.group(1)
            
            # Estrategia 4: Buscar números en texto
            texto = wrapper.get_text()
            texto_limpio = self._limpiar_texto_html(texto)
            numero_match = re.search(r'#(\d+)', texto_limpio)
            if not numero_match:
                numero_match = re.search(r'\b(\d{1,2})\b', texto_limpio)
            
            if numero_match:
                numero = numero_match.group(1)
                if 1 <= int(numero) <= 99:
                    return numero
            
            return "?"
            
        except Exception as e:
            print(f"    ⚠️ Error extrayendo número: {e}")
            return "?"

    def _extraer_imagen_desde_wrapper(self, wrapper):
        """Extrae imagen desde player-wrapper"""
        try:
            img_elem = wrapper.select_one('img')
            if img_elem:
                imagen_url = img_elem.get('src') or img_elem.get('data-src')
                if imagen_url:
                    if imagen_url.startswith('/'):
                        if 'cdn.resfu.com' in imagen_url:
                            return f"https://cdn.resfu.com{imagen_url}"
                        else:
                            return f"https://es.besoccer.com{imagen_url}"
                    elif not imagen_url.startswith('http'):
                        return f"https://es.besoccer.com/{imagen_url}"
                    return imagen_url
            return ""
        except:
            return ""

    def _determinar_si_titular(self, wrapper):
        """Determina si un jugador es titular o suplente"""
        try:
            # Buscar en clases y atributos
            clases = wrapper.get('class', [])
            
            if any('titular' in clase.lower() for clase in clases):
                return True
            if any('suplente' in clase.lower() or 'bench' in clase.lower() for clase in clases):
                return False
            
            # Buscar en contenedor padre
            current = wrapper
            for _ in range(5):
                if current.parent:
                    current = current.parent
                    parent_classes = current.get('class', [])
                    
                    if any('lineup' in clase.lower() for clase in parent_classes):
                        return True
                    if any('bench' in clase.lower() or 'suplent' in clase.lower() for clase in parent_classes):
                        return False
                else:
                    break
            
            # Por defecto, considerar titular
            return True
            
        except:
            return True

    def _extraer_alineaciones_metodo_alternativo(self, soup):
        """Método alternativo para extraer alineaciones"""
        print("🔄 Método alternativo de extracción...")
        
        # Buscar cualquier estructura que contenga jugadores
        jugadores_elems = soup.select('.player, .jugador, [data-player], [data-jugador]')
        
        if not jugadores_elems:
            return {'encontrado': False}
        
        alineacion_local = []
        alineacion_visitante = []
        
        for elem in jugadores_elems:
            jugador = self._extraer_datos_jugador_mejorado(elem)
            if jugador:
                equipo = self._determinar_equipo_jugador(elem)
                if equipo == 'local':
                    alineacion_local.append(jugador)
                else:
                    alineacion_visitante.append(jugador)
        
        if len(alineacion_local) >= 3 and len(alineacion_visitante) >= 3:
            return {
                'encontrado': True,
                'metodo': 'alternativo',
                'alineacion_local': alineacion_local,
                'alineacion_visitante': alineacion_visitante,
                'mensaje': f'Método alternativo: {len(alineacion_local)} vs {len(alineacion_visitante)}'
            }
        
        return {'encontrado': False}

    def _procesar_jugadores_estandar(self, titulares, suplentes):
        """Procesa jugadores con el método estándar"""
        alineacion_local = []
        alineacion_visitante = []
        
        # Procesar titulares
        for titular in titulares:
            jugador = self._extraer_datos_jugador_mejorado(titular, es_titular=True)
            if jugador:
                equipo = self._determinar_equipo_jugador(titular)
                
                if equipo == 'local':
                    alineacion_local.append(jugador)
                elif equipo == 'visitante':
                    alineacion_visitante.append(jugador)
                else:
                    if len(alineacion_local) <= len(alineacion_visitante):
                        alineacion_local.append(jugador)
                    else:
                        alineacion_visitante.append(jugador)
        
        # Procesar suplentes
        for suplente in suplentes:
            jugador = self._extraer_datos_jugador_mejorado(suplente, es_titular=False)
            if jugador:
                equipo = self._determinar_equipo_jugador(suplente)
                
                if equipo == 'local':
                    alineacion_local.append(jugador)
                elif equipo == 'visitante':
                    alineacion_visitante.append(jugador)
                else:
                    suplentes_local = len([j for j in alineacion_local if not j['es_titular']])
                    suplentes_visitante = len([j for j in alineacion_visitante if not j['es_titular']])
                    
                    if suplentes_local <= suplentes_visitante:
                        alineacion_local.append(jugador)
                    else:
                        alineacion_visitante.append(jugador)
        
        # Contar titulares
        titulares_local = len([j for j in alineacion_local if j['es_titular']])
        titulares_visitante = len([j for j in alineacion_visitante if j['es_titular']])
        
        print(f"  ✅ Equipo local: {titulares_local} titulares, {len(alineacion_local) - titulares_local} suplentes")
        print(f"  ✅ Equipo visitante: {titulares_visitante} titulares, {len(alineacion_visitante) - titulares_visitante} suplentes")
        
        if titulares_local >= 3 and titulares_visitante >= 3:
            return {
                'encontrado': True,
                'metodo': 'estandar',
                'alineacion_local': alineacion_local,
                'alineacion_visitante': alineacion_visitante,
                'mensaje': f'Método estándar: {titulares_local}+{len(alineacion_local) - titulares_local} vs {titulares_visitante}+{len(alineacion_visitante) - titulares_visitante}'
            }
        
        return {'encontrado': False}

    def _extraer_datos_jugador_mejorado(self, elemento, es_titular=True):
        """
        FUNCIÓN CORREGIDA: Extracción con limpieza HTML GARANTIZADA
        """
        try:
            print(f"    🔍 Extrayendo jugador (titular: {es_titular})")
            
            # EXTRAER NOMBRE con limpieza GARANTIZADA
            nombre = None
            nombre_elem = elemento.select_one('.name-lineups, .name, [data-cy="player-name"]')
            
            if nombre_elem:
                nombre_sucio = nombre_elem.get_text().strip()
                nombre = self._limpiar_texto_html(nombre_sucio)
            elif elemento.name == 'a':
                texto_directo_sucio = elemento.get_text().strip()
                nombre = self._limpiar_texto_html(texto_directo_sucio)
                if nombre and len(nombre) > 2:
                    nombre = nombre.split('\n')[0].strip()
            
            if not nombre:
                texto_elemento_sucio = elemento.get_text()
                texto_elemento = self._limpiar_texto_html(texto_elemento_sucio)
                lineas = [linea.strip() for linea in texto_elemento.split('\n') if linea.strip()]
                
                for linea in lineas:
                    linea_limpia = self._limpiar_texto_html(linea)
                    if (len(linea_limpia) > 2 and 
                        re.match(r'^[A-Za-záéíóúñÁÉÍÓÚÑ\s\.\-\']+$', linea_limpia) and
                        not linea_limpia.isdigit() and 
                        not re.match(r'^\d+:\d+$', linea_limpia)):
                        nombre = linea_limpia
                        break
            
            if not nombre or len(nombre) < 2:
                print(f"    ⚠️ No se pudo extraer nombre válido")
                return None
            
            # GARANTIZAR que no hay </div> en el nombre
            nombre = self._limpiar_texto_html(nombre)
            print(f"    ✅ Nombre LIMPIO extraído: {nombre}")
            
            # EXTRAER NÚMERO
            numero = "?"
            numero_elem = elemento.select_one('.number.bold, .number, [data-cy="player-number"]')
            
            if numero_elem:
                numero_texto_sucio = numero_elem.get_text().strip()
                numero_texto = self._limpiar_texto_html(numero_texto_sucio)
                if numero_texto.isdigit():
                    numero = numero_texto
            
            if numero == "?":
                numero_match = re.search(r'<span[^>]*class="[^"]*number[^"]*"[^>]*>(\d+)</span>', str(elemento))
                if numero_match:
                    numero = numero_match.group(1)
            
            if numero == "?":
                texto_elemento_sucio = elemento.get_text()
                texto_elemento = self._limpiar_texto_html(texto_elemento_sucio)
                numero_match = re.search(r'#(\d+)', texto_elemento)
                if not numero_match:
                    numero_match = re.search(r'\b(\d{1,2})\b', texto_elemento)
                if numero_match:
                    numero_candidato = numero_match.group(1)
                    if 1 <= int(numero_candidato) <= 99:
                        numero = numero_candidato
            
            print(f"    ✅ Número extraído: {numero}")
            
            # EXTRAER POSICIÓN con limpieza MEJORADA ESPECÍFICA
            posicion = "N/A"
            
            # PRIORIDAD 1: role-box -> t-up (para suplentes principalmente)
            role_box = elemento.find('div', class_='role-box')
            if role_box:
                t_up_elem = role_box.find('div', class_='t-up')
                if t_up_elem:
                    posicion_sucio = t_up_elem.get_text().strip()
                    posicion_limpio = self._limpiar_texto_html(posicion_sucio)
                    # CRÍTICO: Evitar números del type="number bold mr3"
                    if posicion_limpio and not posicion_limpio.isdigit() and len(posicion_limpio) > 1:
                        posicion = self._mapear_posicion(posicion_limpio)
                        print(f"    ✅ Posición de role-box->t-up: {posicion}")
            
            # PRIORIDAD 2: Otros selectores si no encontró en role-box
            if posicion == "N/A":
                posicion_elem = elemento.select_one('.position, [data-cy="player-position"]')
                if posicion_elem:
                    posicion_sucio = posicion_elem.get_text().strip()
                    posicion_limpio = self._limpiar_texto_html(posicion_sucio)
                    if posicion_limpio and not posicion_limpio.isdigit():
                        posicion = self._mapear_posicion(posicion_limpio)
            
            # PRIORIDAD 3: Buscar en texto general
            if posicion == "N/A":
                texto_elemento_sucio = elemento.get_text()
                texto_elemento = self._limpiar_texto_html(texto_elemento_sucio)
                posiciones_conocidas = ['POR', 'DEF', 'MED', 'DEL', 'Portero', 'Defensa', 'Medio', 'Delantero']
                for pos in posiciones_conocidas:
                    if pos in texto_elemento:
                        posicion = self._mapear_posicion(pos)
                        break
            
            # PRIORIDAD 4: JSON-LD con limpieza
            if posicion == "N/A":
                script_elem = elemento.select_one('script[type="application/ld+json"]')
                if script_elem:
                    try:
                        json_data = json.loads(script_elem.get_text())
                        if 'jobTitle' in json_data:
                            posicion_sucio = json_data['jobTitle']
                            posicion = self._mapear_posicion(self._limpiar_texto_html(posicion_sucio))
                        elif 'jobtitle' in json_data:
                            posicion_sucio = json_data['jobtitle']
                            posicion = self._mapear_posicion(self._limpiar_texto_html(posicion_sucio))
                    except:
                        pass
            
            # GARANTIZAR que posición no tiene HTML
            posicion = self._limpiar_texto_html(posicion)
            print(f"    ✅ Posición LIMPIA extraída: {posicion}")
            
            # EXTRAER IMAGEN
            imagen_url = ""
            img_elem = elemento.select_one('.player-img, img.player, [data-cy="player-image"], img')
            
            if img_elem:
                imagen_url = img_elem.get('src', '') or img_elem.get('data-src', '')
            
            if imagen_url:
                if imagen_url.startswith('/'):
                    if 'cdn.resfu.com' in imagen_url:
                        imagen_url = f"https://cdn.resfu.com{imagen_url}"
                    else:
                        imagen_url = f"https://es.besoccer.com{imagen_url}"
                elif not imagen_url.startswith('http'):
                    imagen_url = f"https://es.besoccer.com{imagen_url}"
            
            print(f"    ✅ Imagen extraída: {imagen_url[:50]}..." if imagen_url else "    ❌ Sin imagen")
            
            # JUGADOR DATA FINAL con limpieza GARANTIZADA
            jugador_data = {
                'nombre': self._limpiar_texto_html(nombre),
                'numero': numero,
                'posicion': self._limpiar_texto_html(posicion),
                'es_titular': es_titular,
                'imagen_url': imagen_url
            }
            
            print(f"    ✅ Jugador procesado LIMPIO: {jugador_data['nombre']} #{jugador_data['numero']} ({jugador_data['posicion']})")
            return jugador_data
            
        except Exception as e:
            print(f"    ❌ Error extrayendo datos del jugador: {e}")
            return None

    def _mapear_posicion(self, posicion_texto):
        """Mapea abreviaciones y variaciones de posiciones a nombres estándar"""
        if not posicion_texto:
            return "N/A"
        
        pos_lower = posicion_texto.lower().strip()
        
        if pos_lower in ['por', 'portero', 'goalkeeper', 'gk', 'keeper']:
            return 'Portero'
        elif pos_lower in ['def', 'defensa', 'defender', 'defence', 'cb', 'lb', 'rb']:
            return 'Defensa'
        elif pos_lower in ['med', 'medio', 'midfielder', 'mid', 'cm', 'dm', 'am']:
            return 'Medio'
        elif pos_lower in ['del', 'delantero', 'forward', 'striker', 'fw', 'st', 'lw', 'rw']:
            return 'Delantero'
        else:
            return posicion_texto.title()

    def obtener_partidos_por_fecha(self, fecha_str):
        """Método principal optimizado - USA SOLO livescore de BeSoccer"""
        try:
            print(f"🔍 Obteniendo partidos para {fecha_str} desde livescore...")
            
            cache_key = f"partidos_livescore_{fecha_str}"
            if self._verificar_cache(cache_key):
                print(f"✅ Usando datos del cache para {fecha_str}")
                return self.cache[cache_key]['data']
            
            scraper_livescore = BeSoccerAlineacionesScraper()
            partidos_encontrados = scraper_livescore.buscar_partidos_en_fecha(fecha_str)
            
            partidos_formateados = self._formatear_partidos_livescore(partidos_encontrados, fecha_str)
            
            if partidos_formateados:
                self._guardar_cache(cache_key, partidos_formateados)
            
            print(f"✅ {len(partidos_formateados)} partidos encontrados desde livescore")
            return partidos_formateados
            
        except Exception as e:
            print(f"❌ Error obteniendo partidos desde livescore: {e}")
            return []

    def _formatear_partidos_livescore(self, partidos_livescore, fecha_str):
        """Formatea partidos de livescore para el sistema"""
        partidos_formateados = []
        
        for partido in partidos_livescore:
            try:
                # CORREGIR: besoccer_id en lugar de besocrer_id
                partido_formateado = {
                    'id': f"livescore_{partido['match_id']}",
                    'fecha': fecha_str,
                    'hora': partido.get('hora', 'TBD'),
                    'equipo_local': partido['equipo_local'],
                    'equipo_visitante': partido['equipo_visitante'],
                    'liga': 'Partidos Globales',
                    'competicion': 'Livescore BeSoccer',
                    'estado': partido.get('estado', 'programado'),
                    'estadio': f"Estadio {partido['equipo_local']}",
                    'escudo_local': partido.get('escudo_local', ''),
                    'escudo_visitante': partido.get('escudo_visitante', ''),
                    'besoccer_id': partido['match_id'],  # CORREGIDO
                    'url_partido': partido.get('url_partido', ''),
                    'url_alineaciones': partido.get('url_alineaciones', ''),
                    'resultado_local': partido.get('resultado_local'),
                    'resultado_visitante': partido.get('resultado_visitante'),
                    'alineacion_local': [],
                    'alineacion_visitante': []
                }
                
                partidos_formateados.append(partido_formateado)
                
            except Exception as e:
                print(f"⚠️ Error formateando partido: {e}")
                continue
        
        return partidos_formateados

    def _analizar_estructura_alineaciones(self, soup, url):
        """Analiza estructura de la página cuando no se encuentran alineaciones"""
        print("🔍 Analizando estructura de la página...")
        
        elementos_con_texto = soup.find_all(string=True)
        textos_limpio = [t.strip() for t in elementos_con_texto if t.strip() and len(t.strip()) > 2]
        
        posibles_nombres = []
        patron_nombre = re.compile(r'^[A-Za-záéíóúñÁÉÍÓÚÑ\s\.]+$')
        
        for texto in textos_limpio:
            texto_limpio = self._limpiar_texto_html(texto)
            if 5 <= len(texto_limpio) <= 30 and patron_nombre.match(texto_limpio):
                if not any(palabra in texto_limpio.lower() for palabra in 
                          ['target', 'endtarget', 'google', 'facebook', 'tag', 'manager', 
                           'taboola', 'partidos', 'noticias', 'competiciones']):
                    posibles_nombres.append(texto_limpio)
        
        return {
            'encontrado': False,
            'metodo': 'analisis_estructura',
            'debug_info': {
                'url': url,
                'posibles_nombres': posibles_nombres[:10],
                'total_elementos': len(soup.find_all()),
                'mensaje': 'Alineaciones no disponibles o partido no iniciado'
            }
        }

    # ==========================================
    # MÉTODOS AUXILIARES (mantener iguales)
    # ==========================================
    
    def _obtener_url_oficial_optimizada(self, match_id, equipo_local="", equipo_visitante=""):
        """Obtiene URL oficial de forma optimizada usando cache y livescore únicamente"""
        try:
            print(f"🔍 Búsqueda optimizada para {match_id} ({equipo_local} vs {equipo_visitante})")
            
            cache_key = f"url_oficial_{match_id}"
            if self._verificar_cache_urls_oficiales(cache_key):
                print("✅ URL oficial encontrada en cache")
                return self.cache_urls_oficiales[cache_key]['url']
            
            urls_a_buscar = self._generar_urls_livescore_fecha()
            
            print(f"🔍 Buscando en {len(urls_a_buscar)} URLs de livescore...")
            
            for url_busqueda in urls_a_buscar:
                try:
                    print(f"  🔍 Buscando en: {url_busqueda}")
                    url_encontrada = self._extraer_url_desde_livescore(url_busqueda, match_id, equipo_local, equipo_visitante)
                    
                    if url_encontrada:
                        print(f"  ✅ URL oficial encontrada: {url_encontrada}")
                        self._guardar_url_oficial_cache(match_id, url_encontrada)
                        return url_encontrada
                    
                    time.sleep(0.3)
                    
                except Exception as e:
                    print(f"  ⚠️ Error en {url_busqueda}: {e}")
                    continue
            
            print("❌ URL oficial no encontrada en livescore")
            return None
            
        except Exception as e:
            print(f"❌ Error en búsqueda optimizada: {e}")
            return None

    def _generar_urls_livescore_fecha(self):
        """Genera URLs de livescore para diferentes fechas"""
        urls = []
        urls.extend(self.urls_livescore)
        
        fechas_busqueda = [
            datetime.now(),
            datetime.now() - timedelta(days=1),
            datetime.now() + timedelta(days=1),
            datetime.now() - timedelta(days=2),
            datetime.now() + timedelta(days=2)
        ]
        
        for fecha in fechas_busqueda:
            fecha_str = fecha.strftime('%Y-%m-%d')
            urls.extend([
                f'https://es.besoccer.com/livescore?date={fecha_str}',
                f'https://es.besoccer.com/partidos/{fecha_str}',
                f'https://es.besoccer.com/resultados/{fecha_str}'
            ])
        
        return urls

    def _extraer_url_desde_livescore(self, url_pagina, match_id, equipo_local="", equipo_visitante=""):
        """Extrae URL oficial desde livescore siguiendo la estructura tableMatches"""
        try:
            response = self.session.get(url_pagina, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            table_matches = soup.find('div', id='tableMatches')
            if not table_matches:
                print(f"    ⚠️ No se encontró tableMatches en {url_pagina}")
                return None
            
            print(f"    ✅ tableMatches encontrado")
            
            mod_panels = table_matches.find_all('div', id='mod_panel')
            print(f"    🔸 Encontrados {len(mod_panels)} mod_panel")
            
            for panel in mod_panels:
                panel_body = panel.find('div', class_='panel-body p0 match-list-new panel view-more')
                if not panel_body:
                    continue
                
                match_links = panel_body.find_all('a', class_='match-link match-home')
                
                if match_links:
                    print(f"    🔸 Encontrados {len(match_links)} match-link en panel")
                
                for link in match_links:
                    if self._verificar_match_link_optimizado(link, match_id, equipo_local, equipo_visitante):
                        href = link.get('href')
                        if href:
                            if href.startswith('/'):
                                url_completa = f"https://es.besoccer.com{href}"
                            else:
                                url_completa = href
                            
                            print(f"    ✅ Match-link encontrado: {url_completa}")
                            return url_completa
            
            return None
            
        except Exception as e:
            print(f"    ❌ Error extrayendo desde livescore: {e}")
            return None

    def _verificar_match_link_optimizado(self, link, match_id, equipo_local="", equipo_visitante=""):
        """Verificación optimizada de match-link"""
        try:
            href = link.get('href', '')
            if match_id in href:
                print(f"      ✅ Match ID {match_id} encontrado en href")
                return True
            
            element_id = link.get('id', '')
            if match_id in element_id:
                print(f"      ✅ Match ID {match_id} encontrado en id")
                return True
            
            for attr_name, attr_value in link.attrs.items():
                if attr_name.startswith('data-') and match_id in str(attr_value):
                    print(f"      ✅ Match ID encontrado en {attr_name}")
                    return True
            
            return False
            
        except Exception as e:
            print(f"      ⚠️ Error verificando match-link: {e}")
            return False

    def _construir_url_alineaciones_desde_oficial(self, url_oficial):
        """Construye la URL de alineaciones desde la URL oficial del partido"""
        try:
            if url_oficial.endswith('/alineaciones'):
                return url_oficial
            
            url_limpia = url_oficial.split('#')[0].split('?')[0]
            
            if url_limpia.endswith('/'):
                return f"{url_limpia}alineaciones"
            else:
                return f"{url_limpia}/alineaciones"
                
        except Exception as e:
            print(f"⚠️ Error construyendo URL de alineaciones: {e}")
            return f"{url_oficial}/alineaciones"

    def _determinar_equipo_jugador(self, elemento):
        """Determina si un jugador pertenece al equipo local o visitante"""
        try:
            current = elemento
            for _ in range(10):
                if current.parent:
                    current = current.parent
                    clases = current.get('class', [])
                    
                    if 'local' in clases or 'local' in str(clases):
                        return 'local'
                    
                    if 'visitor' in clases or 'visitante' in clases or 'visitor' in str(clases):
                        return 'visitante'
                    
                    html_contenedor = str(current)
                    if 'class="lineup local"' in html_contenedor or 'col-bench local' in html_contenedor:
                        return 'local'
                    elif 'class="lineup visitor"' in html_contenedor or 'col-bench visitor' in html_contenedor:
                        return 'visitante'
                else:
                    break
            
            return 'desconocido'
            
        except Exception as e:
            print(f"⚠️ Error determinando equipo: {e}")
            return 'desconocido'

    # ==========================================
    # MÉTODOS DE CACHE (mantener iguales)
    # ==========================================
    
    def _verificar_cache(self, cache_key):
        """Verifica cache general"""
        if cache_key not in self.cache:
            return False
        
        timestamp = self.cache[cache_key]['timestamp']
        if time.time() - timestamp > self.cache_timeout:
            del self.cache[cache_key]
            return False
        
        return True

    def _guardar_cache(self, cache_key, data):
        """Guarda en cache general"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }

    def _verificar_cache_urls_oficiales(self, cache_key):
        """Verifica cache de URLs oficiales (más duradero)"""
        if cache_key not in self.cache_urls_oficiales:
            return False
        
        timestamp = self.cache_urls_oficiales[cache_key]['timestamp']
        if time.time() - timestamp > self.cache_urls_timeout:
            del self.cache_urls_oficiales[cache_key]
            return False
        
        return True

    def _guardar_url_oficial_cache(self, match_id, url_oficial):
        """Guarda URL oficial en cache específico"""
        cache_key = f"url_oficial_{match_id}"
        self.cache_urls_oficiales[cache_key] = {
            'url': url_oficial,
            'timestamp': time.time()
        }

    def _extraer_match_id_de_url(self, url):
        """Extrae match_id de una URL"""
        partes = url.split('/')
        for parte in partes:
            if parte.isdigit() and len(parte) >= 8:
                return parte
        return 'unknown'

    def limpiar_cache(self):
        """Limpia todos los caches"""
        self.cache = {}
        self.cache_urls_oficiales = {}
        print("🗑️ Cache completo limpiado")

# ==========================================
# CLASE AUXILIAR PARA LIVESCORE - MANTENIDA IGUAL
# ==========================================

class BeSoccerAlineacionesScraper:
    """Scraper especializado para livescore de BeSoccer - VERSIÓN CORREGIDA"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.base_url = "https://es.besoccer.com"
        self.livescore_url = "https://es.besoccer.com/livescore"
        self.cache = {}
        self.cache_timeout = 900

    def buscar_partidos_en_fecha(self, fecha_str):
        """Busca partidos en livescore para una fecha específica"""
        try:
            print(f"🌐 Buscando partidos en livescore para {fecha_str}...")
            
            cache_key = f"livescore_{fecha_str}"
            if self._verificar_cache(cache_key):
                print(f"✅ Usando datos de livescore del cache")
                return self.cache[cache_key]['data']
            
            partidos_encontrados = []
            
            partidos_livescore = self._buscar_en_livescore(fecha_str)
            partidos_encontrados.extend(partidos_livescore)
            
            partidos_fecha = self._buscar_por_fecha_directa(fecha_str)
            partidos_encontrados.extend(partidos_fecha)
            
            partidos_unicos = self._eliminar_duplicados(partidos_encontrados)
            
            if partidos_unicos:
                self._guardar_cache(cache_key, partidos_unicos)
            
            print(f"🎉 Encontrados {len(partidos_unicos)} partidos únicos para {fecha_str}")
            return partidos_unicos
            
        except Exception as e:
            print(f"❌ Error en búsqueda de livescore: {e}")
            return []

    def _buscar_en_livescore(self, fecha_str):
        """Busca partidos en la página de livescore principal"""
        try:
            print("🔍 Buscando en livescore principal...")
            
            fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d')
            fecha_param = fecha_obj.strftime('%Y-%m-%d')
            
            url_livescore = f"{self.livescore_url}?date={fecha_param}"
            
            response = self.session.get(url_livescore, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            partidos = []
            
            table_matches = soup.find('div', id='tableMatches')
            if table_matches:
                mod_panels = table_matches.find_all('div', id='mod_panel')
                
                for panel in mod_panels:
                    panel_body = panel.find('div', class_='panel-body p0 match-list-new panel view-more')
                    if panel_body:
                        match_links = panel_body.find_all('a', class_='match-link match-home')
                        
                        for link in match_links:
                            partido_data = self._extraer_partido_desde_link_corregido(link)
                            if partido_data:
                                partidos.append(partido_data)
            
            if not partidos:
                partidos_html = soup.select('[id^="match-"], .match-row, .match-item')
                for partido_elem in partidos_html:
                    partido_data = self._extraer_partido_livescore(partido_elem)
                    if partido_data:
                        partidos.append(partido_data)
            
            print(f"  ✅ Partidos extraídos de livescore: {len(partidos)}")
            return partidos
            
        except Exception as e:
            print(f"⚠️ Error en livescore: {e}")
            return []

    def _extraer_partido_desde_link_corregido(self, link):
        """Extrae partido desde match-link usando la estructura correcta"""
        try:
            href = link.get('href', '')
            if not href:
                return None
            
            if href.startswith('/'):
                url_partido = f"https://es.besoccer.com{href}"
            else:
                url_partido = href
            
            match_id = None
            element_id = link.get('id', '')
            if element_id:
                match_id = element_id.replace('match-', '')
            
            if not match_id:
                partes = href.split('/')
                for parte in partes:
                    if parte.isdigit() and len(parte) >= 8:
                        match_id = parte
                        break
            
            if not match_id:
                return None
            
            team_box = link.find('div', class_='team-box')
            if not team_box:
                print(f"    ⚠️ No se encontró team-box en match {match_id}")
                return None
            
            team_infos = team_box.find_all('div', class_='team-info')
            if len(team_infos) < 2:
                print(f"    ⚠️ No se encontraron 2 team-info en match {match_id}")
                return None
            
            # Extraer equipos
            equipo_local_info = team_infos[0]
            equipo_local_name = equipo_local_info.find('div', class_='team-name')
            equipo_local = equipo_local_name.get_text().strip() if equipo_local_name else "Equipo Local"
            
            escudo_local_img = equipo_local_info.find('img', class_='pv3 va-m team-shield')
            escudo_local = escudo_local_img.get('src', '') if escudo_local_img else ''
            
            equipo_visitante_info = team_infos[1]
            equipo_visitante_name = equipo_visitante_info.find('div', class_='team-name')
            equipo_visitante = equipo_visitante_name.get_text().strip() if equipo_visitante_name else "Equipo Visitante"
            
            escudo_visitante_img = equipo_visitante_info.find('img', class_='pv3 va-m team-shield')
            escudo_visitante = escudo_visitante_img.get('src', '') if escudo_visitante_img else ''
            
            # Extraer estado y resultado
            marker = team_box.find('div', class_='marker')
            hora = "TBD"
            estado = "programado"
            resultado_local = None
            resultado_visitante = None
            
            if marker:
                hora_elem = marker.find('p', class_='match_hour time')
                if hora_elem:
                    hora = hora_elem.get_text().strip()
                    estado = "programado"
                else:
                    resultado_span = marker.find('span')
                    if resultado_span:
                        resultado_texto = resultado_span.get_text().strip()
                        resultado_match = re.search(r'(\d+)-(\d+)', resultado_texto)
                        if resultado_match:
                            resultado_local = int(resultado_match.group(1))
                            resultado_visitante = int(resultado_match.group(2))
                            hora = "FIN"
                            estado = "finalizado"
                        else:
                            r1_elem = resultado_span.find('span', class_='r1')
                            r2_elem = resultado_span.find('span', class_='r2')
                            if r1_elem and r2_elem:
                                try:
                                    resultado_local = int(r1_elem.get_text().strip())
                                    resultado_visitante = int(r2_elem.get_text().strip())
                                    hora = "FIN"
                                    estado = "finalizado"
                                except:
                                    pass
            
            # Detectar estado adicional
            date_elem = link.find('div', class_='date ta-c')
            if date_elem:
                tag_elem = date_elem.find('span', class_='tag-nobg')
                if tag_elem:
                    tag_text = tag_elem.get_text().strip().lower()
                    if 'fin' in tag_text:
                        estado = "finalizado"
                    elif 'en vivo' in tag_text or 'live' in tag_text:
                        estado = "en_vivo"
            
            data_status = link.get('data-status', '')
            if data_status == '1':
                estado = "finalizado"
            elif data_status == '0':
                estado = "en_vivo"
            elif data_status == '-1':
                estado = "programado"
            
            return {
                'match_id': match_id,
                'equipo_local': equipo_local,
                'equipo_visitante': equipo_visitante,
                'hora': hora,
                'estado': estado,
                'escudo_local': escudo_local,
                'escudo_visitante': escudo_visitante,
                'resultado_local': resultado_local,
                'resultado_visitante': resultado_visitante,
                'url_partido': url_partido,
                'fuente': 'livescore_corregido'
            }
            
        except Exception as e:
            print(f"⚠️ Error extrayendo desde link corregido: {e}")
            return None

    def _buscar_por_fecha_directa(self, fecha_str):
        """Busca partidos usando URL directa de fecha"""
        try:
            print("🔍 Buscando por fecha directa...")
            
            urls_fecha = [
                f"{self.base_url}/partidos/{fecha_str}",
                f"{self.base_url}/resultados/{fecha_str}"
            ]
            
            partidos = []
            
            for url in urls_fecha:
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        partidos_html = soup.select('[id^="match-"], .match-container, .fixture')
                        
                        for partido_elem in partidos_html:
                            partido_data = self._extraer_partido_generico(partido_elem)
                            if partido_data:
                                partidos.append(partido_data)
                        
                        if partidos:
                            print(f"  ✅ {len(partidos)} partidos de {url}")
                            break
                            
                except:
                    continue
            
            return partidos
            
        except Exception as e:
            print(f"⚠️ Error en búsqueda directa: {e}")
            return []

    def _extraer_partido_livescore(self, elemento):
        """Extrae datos de partido desde elemento de livescore"""
        try:
            match_id = elemento.get('id', '').replace('match-', '')
            if not match_id:
                link = elemento.select_one('a')
                if link:
                    href = link.get('href', '')
                    match_numbers = re.findall(r'\d{7,}', href)
                    if match_numbers:
                        match_id = match_numbers[0]
            
            if not match_id:
                return None
            
            equipos = elemento.select('.team-name, .team_name, .name')
            if len(equipos) < 2:
                texto_completo = elemento.get_text()
                patron_vs = re.search(r'([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)\s+(?:vs|v|-|\|)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)', texto_completo)
                if patron_vs:
                    equipo_local = patron_vs.group(1).strip()
                    equipo_visitante = patron_vs.group(2).strip()
                else:
                    return None
            else:
                equipo_local = equipos[0].get_text().strip()
                equipo_visitante = equipos[1].get_text().strip()
            
            hora_elem = elemento.select_one('.time, .match-time, .hora')
            hora = hora_elem.get_text().strip() if hora_elem else "TBD"
            
            url_partido = f"https://es.besoccer.com/partido/{match_id}"
            
            return {
                'match_id': match_id,
                'equipo_local': equipo_local,
                'equipo_visitante': equipo_visitante,
                'hora': hora,
                'estado': 'programado',
                'escudo_local': '',
                'escudo_visitante': '',
                'url_partido': url_partido,
                'fuente': 'livescore_tradicional'
            }
            
        except Exception as e:
            print(f"⚠️ Error extrayendo partido de livescore: {e}")
            return None

    def _extraer_partido_generico(self, elemento):
        """Extrae datos de partido de forma genérica"""
        try:
            texto = elemento.get_text()
            
            match_id = None
            for attr in ['id', 'data-id', 'data-match-id']:
                valor = elemento.get(attr, '')
                if valor:
                    numeros = re.findall(r'\d{7,}', valor)
                    if numeros:
                        match_id = numeros[0]
                        break
            
            if not match_id:
                links = elemento.select('a')
                for link in links:
                    href = link.get('href', '')
                    numeros = re.findall(r'\d{7,}', href)
                    if numeros:
                        match_id = numeros[0]
                        break
            
            if not match_id:
                return None
            
            patron_equipos = re.search(r'([A-Za-záéíóúñÁÉÍÓÚÑ\s]{3,30})\s+(?:vs|v|vs\.|contra|-)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]{3,30})', texto)
            
            if not patron_equipos:
                return None
            
            equipo_local = patron_equipos.group(1).strip()
            equipo_visitante = patron_equipos.group(2).strip()
            
            patron_hora = re.search(r'(\d{1,2}:\d{2})', texto)
            hora = patron_hora.group(1) if patron_hora else "TBD"
            
            return {
                'match_id': match_id,
                'equipo_local': equipo_local,
                'equipo_visitante': equipo_visitante,
                'hora': hora,
                'estado': 'programado',
                'escudo_local': '',
                'escudo_visitante': '',
                'url_partido': f"https://es.besoccer.com/partido/{match_id}",
                'fuente': 'generico'
            }
            
        except Exception as e:
            print(f"⚠️ Error en extracción genérica: {e}")
            return None

    def _eliminar_duplicados(self, partidos):
        """Elimina partidos duplicados basándose en match_id"""
        vistos = set()
        unicos = []
        
        for partido in partidos:
            match_id = partido.get('match_id')
            if match_id and match_id not in vistos:
                vistos.add(match_id)
                unicos.append(partido)
        
        return unicos

    def _verificar_cache(self, cache_key):
        """Verifica si hay datos válidos en cache"""
        if cache_key not in self.cache:
            return False
        
        timestamp = self.cache[cache_key]['timestamp']
        if time.time() - timestamp > self.cache_timeout:
            del self.cache[cache_key]
            return False
        
        return True

    def _guardar_cache(self, cache_key, data):
        """Guarda datos en cache con timestamp"""
        self.cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }

# ==========================================
# FUNCIONES HELPER PARA INTEGRACIÓN - CORREGIDAS
# ==========================================

def obtener_partidos_besoccer(fecha_str):
    """Función helper optimizada - usa solo livescore"""
    try:
        scraper = BeSoccerScraper()
        partidos = scraper.obtener_partidos_por_fecha(fecha_str)
        return partidos
    except Exception as e:
        print(f"❌ Error en obtener_partidos_besoccer: {e}")
        return []

def obtener_alineaciones_besoccer(besoccer_id, equipo_local="", equipo_visitante=""):
    """Función helper optimizada para alineaciones con extracción mejorada"""
    try:
        print(f"🔍 obtener_alineaciones_besoccer llamada con: {besoccer_id}")
        scraper = BeSoccerScraper()
        resultado = scraper.obtener_alineaciones_partido(besoccer_id, equipo_local, equipo_visitante)
        return resultado
    except Exception as e:
        print(f"❌ Error en obtener_alineaciones_besoccer: {e}")
        return {
            'encontrado': False,
            'error': str(e),
            'alineacion_local': [],
            'alineacion_visitante': [],
            'mensaje': 'Error al obtener alineaciones'
        }

# ==========================================
# TESTING MEJORADO Y CORREGIDO
# ==========================================

if __name__ == "__main__":
    print("🧪 Testing BeSoccer Scraper CORREGIDO - Sin </div> y Posiciones Suplentes...")
    
    # Test con el partido que funciona
    print("\n1️⃣ Testing Manchester City vs Al-Hilal con correcciones aplicadas...")
    scraper = BeSoccerScraper()
    
    resultado = scraper.obtener_alineaciones_partido(
        "2025301346", 
        "Manchester City", 
        "Al-Hilal SFC"
    )
    
    print(f"   📊 Resultado: {resultado['encontrado']}")
    if resultado['encontrado']:
        local_total = len(resultado['alineacion_local'])
        visitante_total = len(resultado['alineacion_visitante'])
        
        # Contar titulares y suplentes
        local_titulares = len([j for j in resultado['alineacion_local'] if j.get('es_titular', True)])
        local_suplentes = local_total - local_titulares
        visitante_titulares = len([j for j in resultado['alineacion_visitante'] if j.get('es_titular', True)])
        visitante_suplentes = visitante_total - visitante_titulares
        
        print(f"   ✅ Local: {local_titulares} titulares + {local_suplentes} suplentes = {local_total}")
        print(f"   ✅ Visitante: {visitante_titulares} titulares + {visitante_suplentes} suplentes = {visitante_total}")
        print(f"   ✅ Método: {resultado.get('metodo', 'N/A')}")
        
        # Verificar que no hay </div> en titulares
        print("\n   🔍 VERIFICANDO LIMPIEZA DE </div> EN TITULARES:")
        titulares_local = [j for j in resultado['alineacion_local'] if j.get('es_titular', True)]
        for i, jugador in enumerate(titulares_local[:3]):  # Solo primeros 3
            nombre_limpio = '</div>' not in jugador['nombre']
            posicion_limpia = '</div>' not in jugador['posicion']
            print(f"   {'✅' if nombre_limpio and posicion_limpia else '❌'} Titular {i+1}: {jugador['nombre']} ({jugador['posicion']}) - Limpio: {nombre_limpio and posicion_limpia}")
        
        # Verificar posiciones de suplentes
        print("\n   🔍 VERIFICANDO POSICIONES DE SUPLENTES:")
        suplentes_local = [j for j in resultado['alineacion_local'] if not j.get('es_titular', True)]
        suplentes_visitante = [j for j in resultado['alineacion_visitante'] if not j.get('es_titular', True)]
        
        for i, suplente in enumerate(suplentes_local[:3]):  # Solo primeros 3
            posicion_valida = suplente['posicion'] != 'N/A' and suplente['posicion'] != ''
            print(f"   {'✅' if posicion_valida else '❌'} Suplente Local {i+1}: {suplente['nombre']} - Posición: {suplente['posicion']}")
        
        for i, suplente in enumerate(suplentes_visitante[:3]):  # Solo primeros 3
            posicion_valida = suplente['posicion'] != 'N/A' and suplente['posicion'] != ''
            print(f"   {'✅' if posicion_valida else '❌'} Suplente Visitante {i+1}: {suplente['nombre']} - Posición: {suplente['posicion']}")
    else:
        print(f"   ❌ Error: {resultado.get('mensaje', 'Sin mensaje')}")
    
    print("\n2️⃣ Testing función helper corregida...")
    resultado_helper = obtener_alineaciones_besoccer("2025301346", "Manchester City", "Al-Hilal SFC")
    print(f"   📊 Helper resultado: {resultado_helper['encontrado']}")
    
    print("\n🎉 Testing CORREGIDO completado!")
    print("📋 CORRECCIONES APLICADAS:")
    print("   ✅ Eliminación de </div> en nombres y posiciones de titulares")
    print("   ✅ Mejora en extracción de posiciones de suplentes desde role-box → t-up")
    print("   ✅ Función _limpiar_texto() para filtrar caracteres HTML")
    print("   ✅ Evitar capturar class='number bold mr3' en posiciones")