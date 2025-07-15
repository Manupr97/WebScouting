# utils/db_helpers.py - VERSIÓN CORREGIDA
import sqlite3
import json
from datetime import datetime
from models.partido_model import PartidoModel
import time

def ejecutar_con_reintentos(conn, query, params=None, max_reintentos=5):
    """
    Ejecuta una query con reintentos en caso de database lock
    """
    for intento in range(max_reintentos):
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            conn.commit()
            return cursor
        except sqlite3.OperationalError as e:
            if "locked" in str(e):
                if intento < max_reintentos - 1:
                    print(f"⚠️ Base de datos bloqueada, reintentando en {0.5 * (intento + 1)} segundos...")
                    time.sleep(0.5 * (intento + 1))  # Espera incremental
                    continue
                else:
                    print(f"❌ Error después de {max_reintentos} intentos: {e}")
                    raise
            else:
                raise

def crear_informe_scouting(informe_data):
    """
    Crea un nuevo informe de scouting usando PartidoModel
    """
    try:
        # Usar PartidoModel para crear el informe
        partido_model = PartidoModel()
        informe_id = partido_model.crear_informe_scouting(informe_data)
        
        if informe_id:
            print(f"✅ Informe creado exitosamente con ID: {informe_id}")
            
            # Preparar datos para actualizar jugador
            jugador_data = {
                'nombre': informe_data.get('jugador_nombre'),
                'numero': informe_data.get('numero_camiseta', ''),
                'posicion': informe_data.get('posicion', ''),
                'imagen_url': informe_data.get('imagen_url', '')
            }
            
            partido_data = {
                'id': informe_data.get('partido_id'),
                'fecha': datetime.now().strftime('%Y-%m-%d'),
                'equipo': informe_data.get('equipo'),
                'escudo_equipo': informe_data.get('escudo_equipo', ''),
                'nota_evaluacion': informe_data.get('nota_general'),
                'recomendacion': informe_data.get('recomendacion'),
                'competicion': informe_data.get('liga', 'Desconocida')
            }
            
            # Actualizar jugador en base personal
            actualizar_jugador_desde_informe(
                jugador_data, 
                partido_data, 
                informe_data.get('scout_usuario'),
                informe_id
            )
            
        return informe_id
        
    except Exception as e:
        print(f"❌ Error creando informe: {e}")
        import traceback
        traceback.print_exc()
        return None

def actualizar_jugador_desde_scraper(jugador_data, partido_data, scout_usuario):
    """
    Actualiza o crea un jugador con datos del scraper de alineaciones
    
    Args:
        jugador_data: dict con datos del jugador del scraper
        partido_data: dict con datos del partido
        scout_usuario: usuario que está haciendo scouting
    """
    try:
        conn = sqlite3.connect('data/jugadores.db', timeout=20.0)
        conn.execute("PRAGMA busy_timeout = 10000")  # 10 segundos
        cursor = conn.cursor()
        
        # Verificar si el jugador ya existe
        cursor.execute("""
            SELECT id, veces_observado, datos_json 
            FROM jugadores_observados 
            WHERE jugador = ? AND equipo = ?
        """, (jugador_data['nombre'], partido_data['equipo']))
        
        jugador_existente = cursor.fetchone()
        
        if jugador_existente:
            # ACTUALIZAR jugador existente
            jugador_id, veces_observado, datos_json_str = jugador_existente
            
            # Parsear datos JSON existentes
            datos_adicionales = json.loads(datos_json_str) if datos_json_str else {}
            
            # Agregar información del partido actual
            if 'partidos_observados' not in datos_adicionales:
                datos_adicionales['partidos_observados'] = []
            
            datos_adicionales['partidos_observados'].append({
                'partido_id': partido_data['id'],
                'fecha': partido_data['fecha'],
                'fue_titular': jugador_data.get('es_titular', True)
            })
            
            # Actualizar registro con reintentos
            update_query = """
                UPDATE jugadores_observados
                SET numero_camiseta = COALESCE(?, numero_camiseta),
                    imagen_url = ?,
                    escudo_equipo = ?,
                    ultimo_partido_id = ?,
                    ultima_fecha_visto = ?,
                    veces_observado = veces_observado + 1,
                    besoccer_id = COALESCE(?, besoccer_id),
                    datos_json = ?,
                    posicion = COALESCE(?, posicion)
                WHERE id = ?
            """
            
            params = (
                jugador_data.get('numero', ''),
                jugador_data.get('imagen_url', ''),
                partido_data.get('escudo_equipo', ''),
                partido_data['id'],
                datetime.now().strftime('%Y-%m-%d'),
                partido_data.get('besoccer_id', ''),
                json.dumps(datos_adicionales),
                jugador_data.get('posicion', ''),
                jugador_id
            )
            
            ejecutar_con_reintentos(conn, update_query, params)
            
            print(f"✅ Actualizado: {jugador_data['nombre']} (observado {veces_observado + 1} veces)")
            
        else:
            # CREAR nuevo jugador
            datos_adicionales = {
                'partidos_observados': [{
                    'partido_id': partido_data['id'],
                    'fecha': partido_data['fecha'],
                    'fue_titular': jugador_data.get('es_titular', True)
                }],
                'origen': 'scraper_alineaciones'
            }
            
            insert_query = """
                INSERT INTO jugadores_observados (
                    jugador, equipo, posicion, numero_camiseta,
                    imagen_url, escudo_equipo, ultimo_partido_id,
                    ultima_fecha_visto, scout_agregado, besoccer_id,
                    datos_json, fecha_agregado, estado, veces_observado,
                    nombre_completo, nota_general
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                jugador_data['nombre'],
                partido_data['equipo'],
                jugador_data.get('posicion', 'Por determinar'),
                jugador_data.get('numero', ''),
                jugador_data.get('imagen_url', ''),
                partido_data.get('escudo_equipo', ''),
                partido_data['id'],
                datetime.now().strftime('%Y-%m-%d'),
                scout_usuario,
                partido_data.get('besoccer_id', ''),
                json.dumps(datos_adicionales),
                datetime.now(),
                'Nuevo',
                1,
                jugador_data['nombre'],  # nombre_completo
                0  # nota_general inicial
            )
            
            ejecutar_con_reintentos(conn, insert_query, params)
            
            print(f"✅ Nuevo jugador: {jugador_data['nombre']} ({partido_data['equipo']})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando jugador: {e}")
        import traceback
        traceback.print_exc()
        return False


def procesar_alineaciones_completas(partido_data, alineacion_local, alineacion_visitante, scout_usuario):
    """
    Procesa todas las alineaciones de un partido
    """
    jugadores_procesados = 0
    
    # Preparar datos del partido para equipo local
    partido_local = {
        **partido_data,
        'equipo': partido_data['equipo_local'],
        'escudo_equipo': partido_data.get('escudo_local', '')
    }
    
    # Procesar equipo local
    for jugador in alineacion_local:
        if actualizar_jugador_desde_scraper(jugador, partido_local, scout_usuario):
            jugadores_procesados += 1
    
    # Preparar datos del partido para equipo visitante
    partido_visitante = {
        **partido_data,
        'equipo': partido_data['equipo_visitante'],
        'escudo_equipo': partido_data.get('escudo_visitante', '')
    }
    
    # Procesar equipo visitante
    for jugador in alineacion_visitante:
        if actualizar_jugador_desde_scraper(jugador, partido_visitante, scout_usuario):
            jugadores_procesados += 1
    
    print(f"📊 Total jugadores procesados: {jugadores_procesados}")
    return jugadores_procesados

def actualizar_estadisticas_desde_informes(nombre_jugador, equipo):
    """
    VERSIÓN CORREGIDA: Actualiza las estadísticas con promedio ponderado
    """
    try:
        conn = sqlite3.connect('data/jugadores.db', timeout=20.0)
        conn.execute("PRAGMA busy_timeout = 10000")
        cursor = conn.cursor()
        
        # Primero verificar que el jugador existe
        cursor.execute("""
            SELECT id FROM jugadores_observados 
            WHERE jugador = ? AND equipo = ?
        """, (nombre_jugador, equipo))
        
        jugador = cursor.fetchone()
        if not jugador:
            print(f"⚠️ Jugador {nombre_jugador} no encontrado en Base Personal")
            return False
        
        jugador_id = jugador[0]
        
        # Conectar a partidos.db para obtener informes
        conn_partidos = sqlite3.connect('data/partidos.db', timeout=20.0)
        conn_partidos.execute("PRAGMA busy_timeout = 10000")
        cursor_partidos = conn_partidos.cursor()
        
        # Obtener TODOS los informes con sus tipos para calcular promedio ponderado
        cursor_partidos.execute("""
            SELECT 
                nota_general,
                tipo_evaluacion,
                recomendacion
            FROM informes_scouting
            WHERE jugador_nombre = ? AND equipo = ?
        """, (nombre_jugador, equipo))
        
        informes = cursor_partidos.fetchall()
        conn_partidos.close()
        
        if informes:
            # Calcular promedio ponderado
            notas = []
            pesos = []
            recomendaciones = []
            
            for nota, tipo, recomendacion in informes:
                if nota and nota > 0:
                    # Ponderar más los análisis completos
                    peso = 2.0 if tipo == 'video_completo' else 1.0
                    notas.append(float(nota))
                    pesos.append(peso)
                    recomendaciones.append(recomendacion)
            
            if notas:
                # Promedio ponderado
                total_peso = sum(pesos)
                promedio = sum(n * p for n, p in zip(notas, pesos)) / total_peso
                mejor = max(notas)
                peor = min(notas)
                total = len(informes)
                
                # Determinar recomendación final
                if recomendaciones.count('fichar') >= total/2:
                    recomendacion_final = 'fichar'
                elif recomendaciones.count('descartar') >= total/2:
                    recomendacion_final = 'descartar'
                else:
                    recomendacion_final = 'seguir_observando'
                
                # Actualizar jugador con reintentos
                update_query = """
                    UPDATE jugadores_observados
                    SET nota_promedio = ?,
                        mejor_nota = ?,
                        peor_nota = ?,
                        total_informes = ?,
                        nota_general = ?
                    WHERE id = ?
                """
                
                params = (
                    round(promedio, 1),
                    mejor,
                    peor,
                    total,
                    round(promedio, 0),  # nota_general como entero
                    jugador_id
                )
                
                ejecutar_con_reintentos(conn, update_query, params)
                
                print(f"✅ Estadísticas actualizadas para {nombre_jugador}: Promedio {promedio:.1f} (ponderado), Total informes: {total}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando estadísticas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
def actualizar_jugador_desde_informe(jugador_data, partido_data, scout_usuario, informe_id):
    """
    Actualiza o crea un jugador en la base personal SOLO cuando se guarda un informe
    Esta es la ÚNICA función que debe añadir jugadores a la base personal
    
    Args:
        jugador_data: dict con datos del jugador del scraper
        partido_data: dict con datos del partido
        scout_usuario: usuario que está haciendo scouting
        informe_id: ID del informe recién creado
    """
    try:
        conn = sqlite3.connect('data/jugadores.db', timeout=20.0)
        conn.execute("PRAGMA busy_timeout = 10000")
        cursor = conn.cursor()
        
        # Verificar si el jugador ya existe
        cursor.execute("""
            SELECT id, veces_observado, datos_json, total_informes
            FROM jugadores_observados 
            WHERE jugador = ? AND equipo = ?
        """, (jugador_data['nombre'], partido_data['equipo']))
        
        jugador_existente = cursor.fetchone()
        
        if jugador_existente:
            # ACTUALIZAR jugador existente
            jugador_id, veces_observado, datos_json_str, total_informes = jugador_existente
            
            # Parsear datos JSON existentes
            datos_adicionales = json.loads(datos_json_str) if datos_json_str else {}
            
            # Agregar información del informe actual
            if 'informes_realizados' not in datos_adicionales:
                datos_adicionales['informes_realizados'] = []
            
            datos_adicionales['informes_realizados'].append({
                'informe_id': informe_id,
                'partido_id': partido_data['id'],
                'fecha': partido_data['fecha'],
                'nota': partido_data.get('nota_evaluacion', 0),
                'recomendacion': partido_data.get('recomendacion', ''),
                'scout': scout_usuario,
                'fecha_informe': datetime.now().isoformat()
            })
            
            # Incrementar contadores
            nuevo_veces_observado = veces_observado + 1
            nuevo_total_informes = (total_informes or 0) + 1
            
            # Actualizar registro con reintentos
            update_query = """
                UPDATE jugadores_observados
                SET numero_camiseta = COALESCE(NULLIF(?, ''), numero_camiseta),
                    imagen_url = COALESCE(NULLIF(?, ''), imagen_url),
                    escudo_equipo = COALESCE(NULLIF(?, ''), escudo_equipo),
                    ultimo_partido_id = ?,
                    ultima_fecha_visto = ?,
                    veces_observado = ?,
                    total_informes = ?,
                    besoccer_id = COALESCE(NULLIF(?, ''), besoccer_id),
                    datos_json = ?,
                    posicion = COALESCE(NULLIF(?, ''), posicion),
                    scout_agregado = COALESCE(scout_agregado, ?)
                WHERE id = ?
            """
            
            params = (
                jugador_data.get('numero', ''),
                jugador_data.get('imagen_url', ''),
                partido_data.get('escudo_equipo', ''),
                partido_data['id'],
                datetime.now().strftime('%Y-%m-%d'),
                nuevo_veces_observado,
                nuevo_total_informes,
                partido_data.get('besoccer_id', ''),
                json.dumps(datos_adicionales),
                jugador_data.get('posicion', ''),
                scout_usuario,
                jugador_id
            )
            
            ejecutar_con_reintentos(conn, update_query, params)
            
            print(f"✅ Jugador actualizado: {jugador_data['nombre']} - Informe #{nuevo_total_informes}")
            
        else:
            # CREAR nuevo jugador - SOLO cuando se crea un informe
            datos_adicionales = {
                'informes_realizados': [{
                    'informe_id': informe_id,
                    'partido_id': partido_data['id'],
                    'fecha': partido_data['fecha'],
                    'nota': partido_data.get('nota_evaluacion', 0),
                    'recomendacion': partido_data.get('recomendacion', ''),
                    'scout': scout_usuario,
                    'fecha_informe': datetime.now().isoformat()
                }],
                'origen': 'informe_scouting',
                'fecha_primera_observacion': datetime.now().isoformat()
            }
            
            # Determinar liga del partido
            liga = partido_data.get('competicion', 'Desconocida')
            
            insert_query = """
                INSERT INTO jugadores_observados (
                    jugador, equipo, posicion, numero_camiseta,
                    imagen_url, escudo_equipo, ultimo_partido_id,
                    ultima_fecha_visto, scout_agregado, besoccer_id,
                    datos_json, fecha_agregado, estado, veces_observado,
                    nombre_completo, nota_general, total_informes, liga
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            params = (
                jugador_data['nombre'],
                partido_data['equipo'],
                jugador_data.get('posicion', 'Por determinar'),
                jugador_data.get('numero', ''),
                jugador_data.get('imagen_url', ''),
                partido_data.get('escudo_equipo', ''),
                partido_data['id'],
                datetime.now().strftime('%Y-%m-%d'),
                scout_usuario,
                partido_data.get('besoccer_id', ''),
                json.dumps(datos_adicionales),
                datetime.now(),
                'Evaluado',  # Estado inicial cuando se crea desde informe
                1,  # Primera vez observado
                jugador_data['nombre'],  # nombre_completo
                partido_data.get('nota_evaluacion', 0),  # nota_general inicial
                1,  # Primer informe
                liga
            )
            
            ejecutar_con_reintentos(conn, insert_query, params)
            
            print(f"✅ Nuevo jugador añadido desde informe: {jugador_data['nombre']} ({partido_data['equipo']})")
        
        # IMPORTANTE: Actualizar estadísticas del jugador SIEMPRE
        conn.close()  # Cerrar antes de llamar a actualizar_estadisticas
        actualizar_estadisticas_desde_informes(jugador_data['nombre'], partido_data['equipo'])
        
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando jugador desde informe: {e}")
        import traceback
        traceback.print_exc()
        return False