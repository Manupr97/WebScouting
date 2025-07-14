# utils/db_helpers.py - VERSIÓN CORREGIDA
import sqlite3
import json
from datetime import datetime
from models.partido_model import PartidoModel

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
        conn = sqlite3.connect('data/jugadores.db')
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
            
            # Actualizar registro
            cursor.execute("""
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
            """, (
                jugador_data.get('numero', ''),
                jugador_data.get('imagen_url', ''),
                partido_data.get('escudo_equipo', ''),
                partido_data['id'],
                datetime.now().strftime('%Y-%m-%d'),
                partido_data.get('besoccer_id', ''),
                json.dumps(datos_adicionales),
                jugador_data.get('posicion', ''),
                jugador_id
            ))
            
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
            
            cursor.execute("""
                INSERT INTO jugadores_observados (
                    jugador, equipo, posicion, numero_camiseta,
                    imagen_url, escudo_equipo, ultimo_partido_id,
                    ultima_fecha_visto, scout_agregado, besoccer_id,
                    datos_json, fecha_agregado, estado, veces_observado,
                    nombre_completo, nota_general
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
            ))
            
            print(f"✅ Nuevo jugador: {jugador_data['nombre']} ({partido_data['equipo']})")
        
        conn.commit()
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
    Actualiza las estadísticas de un jugador basándose en todos sus informes
    """
    try:
        conn = sqlite3.connect('data/jugadores.db')
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
        
        # CORREGIDO: Usar la tabla correcta y la base de datos correcta
        conn_partidos = sqlite3.connect('data/partidos.db')
        cursor_partidos = conn_partidos.cursor()
        
        # Calcular estadísticas desde la tabla informes_scouting en partidos.db
        cursor_partidos.execute("""
            SELECT 
                AVG(CAST(nota_general AS REAL)) as promedio,
                MAX(CAST(nota_general AS REAL)) as mejor,
                MIN(CAST(nota_general AS REAL)) as peor,
                COUNT(*) as total,
                GROUP_CONCAT(recomendacion) as recomendaciones
            FROM informes_scouting
            WHERE jugador_nombre = ? AND equipo = ?
        """, (nombre_jugador, equipo))
        
        stats = cursor_partidos.fetchone()
        conn_partidos.close()
        
        if stats and stats[0] is not None:  # Si hay estadísticas
            promedio, mejor, peor, total, recomendaciones = stats
            
            # Determinar recomendación final basada en las recomendaciones
            if recomendaciones:
                rec_list = recomendaciones.split(',')
                if rec_list.count('fichar') >= total/2:
                    recomendacion_final = 'fichar'
                elif rec_list.count('descartar') >= total/2:
                    recomendacion_final = 'descartar'
                else:
                    recomendacion_final = 'seguir_observando'
            else:
                recomendacion_final = 'seguir_observando'
            
            # Actualizar jugador con las estadísticas
            cursor.execute("""
                UPDATE jugadores_observados
                SET nota_promedio = ?,
                    mejor_nota = ?,
                    peor_nota = ?,
                    total_informes = ?,
                    nota_general = ?
                WHERE jugador = ? AND equipo = ?
            """, (
                round(promedio, 1),
                mejor,
                peor,
                total,
                round(promedio, 0),  # nota_general como entero
                nombre_jugador,
                equipo
            ))
            
            conn.commit()
            print(f"✅ Estadísticas actualizadas para {nombre_jugador}: Promedio {promedio:.1f}, Total informes: {total}")
            
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
        conn = sqlite3.connect('data/jugadores.db')
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
            
            # Actualizar registro
            cursor.execute("""
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
            """, (
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
            ))
            
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
            
            cursor.execute("""
                INSERT INTO jugadores_observados (
                    jugador, equipo, posicion, numero_camiseta,
                    imagen_url, escudo_equipo, ultimo_partido_id,
                    ultima_fecha_visto, scout_agregado, besoccer_id,
                    datos_json, fecha_agregado, estado, veces_observado,
                    nombre_completo, nota_general, total_informes, liga
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
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
            ))
            
            print(f"✅ Nuevo jugador añadido desde informe: {jugador_data['nombre']} ({partido_data['equipo']})")
        
        # Actualizar estadísticas del jugador
        actualizar_estadisticas_desde_informes(jugador_data['nombre'], partido_data['equipo'])
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error actualizando jugador desde informe: {e}")
        import traceback
        traceback.print_exc()
        return False