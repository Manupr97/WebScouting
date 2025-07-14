# models/partido_model.py - VERSIÓN CORREGIDA CON INTEGRACIÓN OPCIONAL

import sqlite3
import json
from datetime import datetime, date
import os
import logging
from models.jugador_model import JugadorModel

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PartidoModel:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path="data/partidos.db"):
        # Solo inicializar una vez
        if PartidoModel._initialized:
            return
            
        self.db_path = db_path
        self.init_database()
        
        # Inicializar modelo de jugadores para integración automática
        self.jugador_model = JugadorModel()
        
        # NUEVO: Flag para controlar la integración con Wyscout
        self.INTEGRACION_WYSCOUT_ACTIVA = True
        
        PartidoModel._initialized = True
        logger.info("✅ PartidoModel inicializado (Singleton)")
        logger.info(f"🔧 Integración Wyscout: {'ACTIVA' if self.INTEGRACION_WYSCOUT_ACTIVA else 'DESACTIVADA'}")
    
    def init_database(self):
        """Inicializa las tablas de partidos e informes"""
        # Crear carpeta data si no existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de partidos (sin cambios)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partidos (
                id TEXT PRIMARY KEY,
                fecha DATE NOT NULL,
                liga TEXT NOT NULL,
                equipo_local TEXT NOT NULL,
                equipo_visitante TEXT NOT NULL,
                estadio TEXT,
                hora TEXT,
                alineacion_local TEXT,  -- JSON
                alineacion_visitante TEXT,  -- JSON
                suplentes_local TEXT,  -- JSON
                suplentes_visitante TEXT,  -- JSON
                estado TEXT DEFAULT 'programado',  -- programado, en_vivo, finalizado
                resultado_local INTEGER DEFAULT 0,
                resultado_visitante INTEGER DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabla de informes de scouting MEJORADA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS informes_scouting (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partido_id TEXT NOT NULL,
                jugador_nombre TEXT NOT NULL,
                equipo TEXT NOT NULL,
                posicion TEXT,
                scout_usuario TEXT NOT NULL,
                
                -- Aspectos Técnicos
                control_balon INTEGER CHECK(control_balon BETWEEN 1 AND 10),
                primer_toque INTEGER CHECK(primer_toque BETWEEN 1 AND 10),
                pase_corto INTEGER CHECK(pase_corto BETWEEN 1 AND 10),
                pase_largo INTEGER CHECK(pase_largo BETWEEN 1 AND 10),
                finalizacion INTEGER CHECK(finalizacion BETWEEN 1 AND 10),
                regate INTEGER CHECK(regate BETWEEN 1 AND 10),
                
                -- Aspectos Tácticos
                vision_juego INTEGER CHECK(vision_juego BETWEEN 1 AND 10),
                posicionamiento INTEGER CHECK(posicionamiento BETWEEN 1 AND 10),
                marcaje INTEGER CHECK(marcaje BETWEEN 1 AND 10),
                pressing INTEGER CHECK(pressing BETWEEN 1 AND 10),
                transiciones INTEGER CHECK(transiciones BETWEEN 1 AND 10),
                
                -- Aspectos Físicos
                velocidad INTEGER CHECK(velocidad BETWEEN 1 AND 10),
                resistencia INTEGER CHECK(resistencia BETWEEN 1 AND 10),
                fuerza INTEGER CHECK(fuerza BETWEEN 1 AND 10),
                salto INTEGER CHECK(salto BETWEEN 1 AND 10),
                agilidad INTEGER CHECK(agilidad BETWEEN 1 AND 10),
                
                -- Aspectos Mentales
                concentracion INTEGER CHECK(concentracion BETWEEN 1 AND 10),
                liderazgo INTEGER CHECK(liderazgo BETWEEN 1 AND 10),
                comunicacion INTEGER CHECK(comunicacion BETWEEN 1 AND 10),
                presion INTEGER CHECK(presion BETWEEN 1 AND 10),
                decision INTEGER CHECK(decision BETWEEN 1 AND 10),
                
                -- Evaluación General
                nota_general INTEGER CHECK(nota_general BETWEEN 1 AND 10),
                potencial TEXT,  -- 'alto', 'medio', 'bajo'
                recomendacion TEXT,  -- 'contratar', 'seguir', 'descartar'
                
                -- Observaciones
                fortalezas TEXT,
                debilidades TEXT,
                observaciones TEXT,
                minutos_observados INTEGER,
                
                -- NUEVOS CAMPOS para integración
                jugador_bd_id INTEGER,  -- ID en la BD de jugadores (si se encontró)
                wyscout_match_confianza REAL,  -- % de confianza en la búsqueda
                wyscout_algoritmo TEXT,  -- Algoritmo usado para encontrar
                procesado_wyscout BOOLEAN DEFAULT 0,  -- Si ya se procesó la búsqueda
                
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partido_id) REFERENCES partidos (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def crear_informe_scouting(self, informe_data):
        """
        Crea un nuevo informe de scouting con INTEGRACIÓN OPCIONAL a Wyscout
        """
        # NUEVO: Primero guardar el partido si viene de un livescore
        partido_id = informe_data.get('partido_id', '')
        if partido_id.startswith('livescore_'):
            # Es un partido del scraper, necesitamos guardarlo
            partido_data = {
                'id': partido_id,
                'fecha': partido_id.split('_')[-1],  # Extraer fecha del ID
                'equipo_local': 'Por determinar',  # Necesitarías pasar estos datos
                'equipo_visitante': 'Por determinar',
                'liga': 'LiveScore'
            }
            # Aquí necesitarías los datos completos del partido
            # Por ahora, al menos guarda el ID para que no falle el JOIN
            self.guardar_partido_si_no_existe(partido_data)
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        logger.info(f"💾 Creando informe para: {informe_data['jugador_nombre']} ({informe_data['equipo']})")
        
        try:
            # 1. GUARDAR INFORME BÁSICO
            cursor.execute('''
                INSERT INTO informes_scouting (
                    partido_id, jugador_nombre, equipo, posicion, scout_usuario,
                    control_balon, primer_toque, pase_corto, pase_largo, finalizacion, regate,
                    vision_juego, posicionamiento, marcaje, pressing, transiciones,
                    velocidad, resistencia, fuerza, salto, agilidad,
                    concentracion, liderazgo, comunicacion, presion, decision,
                    nota_general, potencial, recomendacion,
                    fortalezas, debilidades, observaciones, minutos_observados,
                    tipo_evaluacion, imagen_url
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?, ?,
                    ?, ?
                )
            ''', (
                informe_data.get('partido_id'),
                informe_data.get('jugador_nombre'),
                informe_data.get('equipo'),
                informe_data.get('posicion'),
                informe_data.get('scout_usuario'),
                # Evaluaciones (usar valores por defecto si no vienen)
                informe_data.get('control_balon', 5),
                informe_data.get('primer_toque', 5),
                informe_data.get('pase_corto', 5),
                informe_data.get('pase_largo', 5),
                informe_data.get('finalizacion', 5),
                informe_data.get('regate', 5),
                informe_data.get('vision_juego', 5),
                informe_data.get('posicionamiento', 5),
                informe_data.get('marcaje', 5),
                informe_data.get('pressing', 5),
                informe_data.get('transiciones', 5),
                informe_data.get('velocidad', 5),
                informe_data.get('resistencia', 5),
                informe_data.get('fuerza', 5),
                informe_data.get('salto', 5),
                informe_data.get('agilidad', 5),
                informe_data.get('concentracion', 5),
                informe_data.get('liderazgo', 5),
                informe_data.get('comunicacion', 5),
                informe_data.get('presion', 5),
                informe_data.get('decision', 5),
                # General
                informe_data.get('nota_general'),
                informe_data.get('potencial'),
                informe_data.get('recomendacion'),
                informe_data.get('fortalezas'),
                informe_data.get('debilidades'),
                informe_data.get('observaciones'),
                informe_data.get('minutos_observados', 90),
                informe_data.get('tipo_evaluacion', 'campo'),
                informe_data.get('imagen_url', '')
            ))
            
            informe_id = cursor.lastrowid
            
            # IMPORTANTE: Hacer commit AQUÍ, antes de cualquier otra operación
            conn.commit()
            logger.info(f"✅ Informe guardado exitosamente con ID: {informe_id}")
            
            # 2. INTEGRACIÓN WYSCOUT (OPCIONAL - NO AFECTA EL GUARDADO)
            if self.INTEGRACION_WYSCOUT_ACTIVA:
                try:
                    logger.info("🔍 Integración Wyscout ACTIVA - Iniciando búsqueda...")
                    # ... código de integración Wyscout ...
                    # Si hay error aquí, NO hacer rollback
                    
                except Exception as e:
                    # Solo loguear el error, NO hacer rollback
                    logger.warning(f"⚠️ Error en integración Wyscout: {e}")
                    # El informe YA está guardado, así que continuamos
            
            conn.close()
            return informe_id
            
        except Exception as e:
            logger.error(f"❌ Error creando informe: {e}")
            conn.rollback()
            conn.close()
            return None
    
    def activar_integracion_wyscout(self, activar=True):
        """
        Activa o desactiva la integración con Wyscout
        
        Args:
            activar (bool): True para activar, False para desactivar
        """
        self.INTEGRACION_WYSCOUT_ACTIVA = activar
        logger.info(f"🔧 Integración Wyscout: {'ACTIVADA' if activar else 'DESACTIVADA'}")
    
    def obtener_informes_por_usuario(self, usuario):
        """Obtiene todos los informes de un scout CON datos de integración"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.*, p.equipo_local, p.equipo_visitante, p.fecha,
                CASE 
                    WHEN i.wyscout_match_confianza >= 90 THEN '🟢 Excelente'
                    WHEN i.wyscout_match_confianza >= 80 THEN '🟡 Buena'
                    WHEN i.wyscout_match_confianza >= 70 THEN '🟠 Aceptable'
                    WHEN i.wyscout_match_confianza = 0 THEN '🔴 No encontrado'
                    WHEN i.wyscout_match_confianza = -1 THEN '⚫ Error'
                    ELSE '⚪ Sin procesar'
                END as estado_wyscout
            FROM informes_scouting i
            LEFT JOIN partidos p ON i.partido_id = p.id
            WHERE i.scout_usuario = ?
            ORDER BY i.fecha_creacion DESC
        ''', (usuario,))
        
        # IMPORTANTE: Devolver como lista de tuplas para compatibilidad
        informes = cursor.fetchall()
        
        conn.close()
        
        logger.info(f"📊 Obtenidos {len(informes)} informes para usuario {usuario}")
        return informes
    
    def obtener_estadisticas_integracion(self):
        """Obtiene estadísticas de la integración con Wyscout"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute('''
            SELECT 
                COUNT(*) as total_informes,
                SUM(CASE WHEN procesado_wyscout = 1 THEN 1 ELSE 0 END) as procesados,
                SUM(CASE WHEN wyscout_match_confianza >= 70 THEN 1 ELSE 0 END) as matches_exitosos,
                SUM(CASE WHEN wyscout_match_confianza = 0 THEN 1 ELSE 0 END) as no_encontrados,
                AVG(CASE WHEN wyscout_match_confianza > 0 THEN wyscout_match_confianza END) as confianza_promedio
            FROM informes_scouting
        ''')
        
        stats = cursor.fetchone()
        
        # Estadísticas por algoritmo
        cursor.execute('''
            SELECT wyscout_algoritmo, 
                   COUNT(*) as cantidad,
                   AVG(wyscout_match_confianza) as confianza_promedio
            FROM informes_scouting 
            WHERE wyscout_algoritmo IS NOT NULL
            GROUP BY wyscout_algoritmo
            ORDER BY cantidad DESC
        ''')
        
        algoritmos = cursor.fetchall()
        
        conn.close()
        
        return {
            'generales': stats,
            'por_algoritmo': algoritmos
        }
    
    def reprocesar_informes_sin_wyscout(self):
        """Reprocesa informes que no pudieron ser vinculados a Wyscout"""
        if not self.INTEGRACION_WYSCOUT_ACTIVA:
            logger.warning("⚠️ La integración Wyscout está desactivada")
            return 0, 0
            
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener informes sin procesar o que fallaron
        cursor.execute('''
            SELECT id, jugador_nombre, equipo 
            FROM informes_scouting 
            WHERE procesado_wyscout = 0 OR wyscout_match_confianza = -1
        ''')
        
        informes_pendientes = cursor.fetchall()
        
        logger.info(f"🔄 Reprocesando {len(informes_pendientes)} informes...")
        
        exitosos = 0
        for informe_id, nombre, equipo in informes_pendientes:
            try:
                resultado_busqueda = self.jugador_model.buscar_jugador_en_wyscout(
                    nombre_jugador=nombre,
                    equipo_jugador=equipo,
                    umbral_confianza=70
                )
                
                if resultado_busqueda:
                    jugador_bd_id = self.jugador_model.añadir_jugador_observado(
                        datos_wyscout=resultado_busqueda['datos_jugador'],
                        confianza=resultado_busqueda['confianza'],
                        algoritmo=resultado_busqueda['algoritmo'],
                        informe_id=informe_id
                    )
                    
                    cursor.execute('''
                        UPDATE informes_scouting SET 
                            jugador_bd_id = ?,
                            wyscout_match_confianza = ?,
                            wyscout_algoritmo = ?,
                            procesado_wyscout = 1
                        WHERE id = ?
                    ''', (jugador_bd_id, resultado_busqueda['confianza'], 
                         resultado_busqueda['algoritmo'], informe_id))
                    
                    exitosos += 1
                else:
                    cursor.execute('''
                        UPDATE informes_scouting SET 
                            procesado_wyscout = 1,
                            wyscout_match_confianza = 0
                        WHERE id = ?
                    ''', (informe_id,))
                
            except Exception as e:
                logger.error(f"❌ Error reprocesando informe {informe_id}: {str(e)}")
                cursor.execute('''
                    UPDATE informes_scouting SET 
                        procesado_wyscout = 1,
                        wyscout_match_confianza = -1
                    WHERE id = ?
                ''', (informe_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ Reprocesamiento completado: {exitosos}/{len(informes_pendientes)} exitosos")
        return exitosos, len(informes_pendientes)
    
    def obtener_partidos_por_fecha(self, fecha=None):
        """Obtiene partidos filtrados por fecha"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if fecha:
            cursor.execute('''
                SELECT * FROM partidos WHERE fecha = ? ORDER BY hora
            ''', (fecha,))
        else:
            # Obtener partidos de hoy y próximos 3 días
            cursor.execute('''
                SELECT * FROM partidos 
                WHERE fecha >= date('now') 
                ORDER BY fecha, hora
            ''')
        
        partidos = []
        for row in cursor.fetchall():
            partido = {
                'id': row[0],
                'fecha': row[1],
                'liga': row[2],
                'equipo_local': row[3],
                'equipo_visitante': row[4],
                'estadio': row[5],
                'hora': row[6],
                'alineacion_local': json.loads(row[7]) if row[7] else [],
                'alineacion_visitante': json.loads(row[8]) if row[8] else [],
                'suplentes_local': json.loads(row[9]) if row[9] else [],
                'suplentes_visitante': json.loads(row[10]) if row[10] else [],
                'estado': row[11],
                'resultado_local': row[12],
                'resultado_visitante': row[13]
            }
            partidos.append(partido)
        
        conn.close()
        return partidos
    
    def obtener_partido_por_id(self, partido_id):
        """Obtiene un partido específico por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM partidos WHERE id = ?', (partido_id,))
        row = cursor.fetchone()
        
        if row:
            partido = {
                'id': row[0],
                'fecha': row[1],
                'liga': row[2],
                'equipo_local': row[3],
                'equipo_visitante': row[4],
                'estadio': row[5],
                'hora': row[6],
                'alineacion_local': json.loads(row[7]) if row[7] else [],
                'alineacion_visitante': json.loads(row[8]) if row[8] else [],
                'suplentes_local': json.loads(row[9]) if row[9] else [],
                'suplentes_visitante': json.loads(row[10]) if row[10] else [],
                'estado': row[11],
                'resultado_local': row[12],
                'resultado_visitante': row[13]
            }
            conn.close()
            return partido
        
        conn.close()
        return None
    
    def obtener_todos_informes(self):
        """
        Obtiene TODOS los informes de scouting de todos los scouts
        
        Returns:
            list: Lista de diccionarios con informes y datos de partido
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Query para obtener TODOS los informes con información del partido
        cursor.execute('''
            SELECT i.*, p.equipo_local, p.equipo_visitante, p.fecha, p.liga, p.estadio
            FROM informes_scouting i
            JOIN partidos p ON i.partido_id = p.id
            ORDER BY i.fecha_creacion DESC
        ''')
        
        # Obtener nombres de columnas
        columns = [description[0] for description in cursor.description]
        
        # Convertir resultados a lista de diccionarios
        informes = []
        for row in cursor.fetchall():
            informe_dict = dict(zip(columns, row))
            informes.append(informe_dict)
        
        conn.close()
        
        logger.info(f"📊 Obtenidos {len(informes)} informes totales")
        return informes

    def obtener_estadisticas_dashboard(self):
        """
        Obtiene estadísticas específicas para el dashboard principal
        
        Returns:
            dict: Diccionario con todas las estadísticas necesarias
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 1. ESTADÍSTICAS GENERALES
        cursor.execute('''
            SELECT 
                COUNT(*) as total_informes,
                COUNT(DISTINCT scout_usuario) as total_scouts,
                COUNT(DISTINCT partido_id) as partidos_scouted,
                AVG(nota_general) as nota_promedio,
                COUNT(CASE WHEN recomendacion = 'contratar' THEN 1 END) as recomendados_contratar,
                COUNT(CASE WHEN potencial = 'alto' THEN 1 END) as alto_potencial
            FROM informes_scouting
        ''')
        
        stats_generales = cursor.fetchone()
        
        # 2. INFORMES RECIENTES (últimas 24 horas)
        cursor.execute('''
            SELECT COUNT(*) 
            FROM informes_scouting 
            WHERE datetime(fecha_creacion) >= datetime('now', '-1 day')
        ''')
        
        informes_recientes = cursor.fetchone()[0]
        
        # 3. ESTADÍSTICAS POR SCOUT (top 5)
        cursor.execute('''
            SELECT 
                scout_usuario,
                COUNT(*) as cantidad_informes,
                AVG(nota_general) as nota_promedio,
                COUNT(CASE WHEN recomendacion = 'contratar' THEN 1 END) as recomendados
            FROM informes_scouting
            GROUP BY scout_usuario
            ORDER BY cantidad_informes DESC
            LIMIT 5
        ''')
        
        top_scouts = cursor.fetchall()
        
        # 4. ESTADÍSTICAS POR LIGA
        cursor.execute('''
            SELECT 
                p.liga,
                COUNT(i.id) as informes,
                AVG(i.nota_general) as nota_promedio
            FROM informes_scouting i
            JOIN partidos p ON i.partido_id = p.id
            GROUP BY p.liga
            ORDER BY informes DESC
        ''')
        
        stats_ligas = cursor.fetchall()
        
        # 5. DISTRIBUCIÓN DE RECOMENDACIONES
        cursor.execute('''
            SELECT 
                recomendacion,
                COUNT(*) as cantidad,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM informes_scouting), 1) as porcentaje
            FROM informes_scouting
            WHERE recomendacion IS NOT NULL
            GROUP BY recomendacion
        ''')
        
        distribucion_recomendaciones = cursor.fetchall()
        
        # 6. ESTADÍSTICAS DE INTEGRACIÓN WYSCOUT (si existen)
        cursor.execute('''
            SELECT 
                COUNT(CASE WHEN procesado_wyscout = 1 THEN 1 END) as procesados,
                COUNT(CASE WHEN wyscout_match_confianza >= 70 THEN 1 END) as matches_exitosos,
                COUNT(CASE WHEN wyscout_match_confianza = 0 THEN 1 END) as no_encontrados,
                AVG(CASE WHEN wyscout_match_confianza > 0 THEN wyscout_match_confianza END) as confianza_promedio
            FROM informes_scouting
        ''')
        
        stats_wyscout = cursor.fetchone()
        
        conn.close()
        
        # Organizar todas las estadísticas en un diccionario estructurado
        estadisticas = {
            'generales': {
                'total_informes': stats_generales[0] or 0,
                'total_scouts': stats_generales[1] or 0,
                'partidos_scouted': stats_generales[2] or 0,
                'nota_promedio': round(stats_generales[3] or 0, 1) if stats_generales[3] else 0,
                'recomendados_contratar': stats_generales[4] or 0,
                'alto_potencial': stats_generales[5] or 0,
                'informes_recientes': informes_recientes
            },
            'top_scouts': [
                {
                    'scout': scout[0],
                    'informes': scout[1],
                    'nota_promedio': round(scout[2] or 0, 1) if scout[2] else 0,
                    'recomendados': scout[3]
                } for scout in top_scouts
            ],
            'por_liga': [
                {
                    'liga': liga[0],
                    'informes': liga[1],
                    'nota_promedio': round(liga[2] or 0, 1) if liga[2] else 0
                } for liga in stats_ligas
            ],
            'recomendaciones': [
                {
                    'tipo': rec[0],
                    'cantidad': rec[1],
                    'porcentaje': rec[2]
                } for rec in distribucion_recomendaciones
            ],
            'wyscout': {
                'procesados': stats_wyscout[0] or 0,
                'matches_exitosos': stats_wyscout[1] or 0,
                'no_encontrados': stats_wyscout[2] or 0,
                'confianza_promedio': round(stats_wyscout[3] or 0, 1) if stats_wyscout[3] else 0
            }
        }
        
        logger.info("📈 Estadísticas del dashboard calculadas correctamente")
        return estadisticas

    def obtener_informes_recientes(self, dias=7):
        """
        Obtiene informes de los últimos N días
        
        Args:
            dias (int): Número de días hacia atrás (default: 7)
            
        Returns:
            list: Lista de diccionarios con informes recientes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.*, p.equipo_local, p.equipo_visitante, p.fecha
            FROM informes_scouting i
            JOIN partidos p ON i.partido_id = p.id
            WHERE datetime(i.fecha_creacion) >= datetime('now', '-{} days')
            ORDER BY i.fecha_creacion DESC
        '''.format(dias))
        
        # Convertir a diccionarios
        columns = [description[0] for description in cursor.description]
        informes_recientes = []
        
        for row in cursor.fetchall():
            informe_dict = dict(zip(columns, row))
            informes_recientes.append(informe_dict)
        
        conn.close()
        
        logger.info(f"📅 Obtenidos {len(informes_recientes)} informes de los últimos {dias} días")
        return informes_recientes

    def obtener_mejores_jugadores(self, limite=10):
        """
        Obtiene los jugadores mejor evaluados
        
        Args:
            limite (int): Número máximo de jugadores a retornar
            
        Returns:
            list: Lista de diccionarios con los mejores jugadores evaluados
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                jugador_nombre,
                equipo,
                AVG(nota_general) as nota_promedio,
                COUNT(*) as veces_observado,
                MAX(fecha_creacion) as ultima_observacion,
                GROUP_CONCAT(DISTINCT scout_usuario) as scouts,
                COUNT(CASE WHEN recomendacion = 'contratar' THEN 1 END) as recomendaciones_contratar
            FROM informes_scouting
            WHERE nota_general IS NOT NULL
            GROUP BY jugador_nombre, equipo
            HAVING COUNT(*) >= 1  -- Al menos 1 observación
            ORDER BY nota_promedio DESC, veces_observado DESC
            LIMIT ?
        ''', (limite,))
        
        # Convertir a diccionarios
        columns = [description[0] for description in cursor.description]
        mejores_jugadores = []
        
        for row in cursor.fetchall():
            jugador_dict = dict(zip(columns, row))
            jugador_dict['nota_promedio'] = round(jugador_dict['nota_promedio'], 1)
            mejores_jugadores.append(jugador_dict)
        
        conn.close()
        
        logger.info(f"🌟 Obtenidos los {len(mejores_jugadores)} mejores jugadores")
        return mejores_jugadores

    def obtener_resumen_actividad_semanal(self):
        """
        Obtiene un resumen de la actividad de scouting por días de la semana
        
        Returns:
            list: Lista de diccionarios con actividad por día de la semana
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CASE CAST(strftime('%w', fecha_creacion) AS INTEGER)
                    WHEN 0 THEN 'Domingo'
                    WHEN 1 THEN 'Lunes'
                    WHEN 2 THEN 'Martes'
                    WHEN 3 THEN 'Miércoles'
                    WHEN 4 THEN 'Jueves'
                    WHEN 5 THEN 'Viernes'
                    WHEN 6 THEN 'Sábado'
                END as dia_semana,
                COUNT(*) as informes,
                AVG(nota_general) as nota_promedio
            FROM informes_scouting
            WHERE fecha_creacion >= datetime('now', '-30 days')
            GROUP BY strftime('%w', fecha_creacion)
            ORDER BY CAST(strftime('%w', fecha_creacion) AS INTEGER)
        ''')
        
        # Convertir a diccionarios
        actividad_semanal = []
        for row in cursor.fetchall():
            actividad_semanal.append({
                'dia': row[0],
                'informes': row[1],
                'nota_promedio': round(row[2] or 0, 1) if row[2] else 0
            })
        
        conn.close()
        
        logger.info(f"📅 Obtenida actividad semanal: {len(actividad_semanal)} días con datos")
        return actividad_semanal

    def actualizar_wyscout_match(self, informe_id, estado, confianza=None):
        """
        Actualiza el estado de Wyscout Match en un informe
        
        Args:
            informe_id (int): ID del informe
            estado (str): "Encontrado" o "No encontrado" 
            confianza (float): % de confianza si fue encontrado
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if estado == "Encontrado" and confianza:
            wyscout_match = f"Encontrado ({confianza:.1f}%)"
        else:
            wyscout_match = "No encontrado"
        
        cursor.execute('''
            UPDATE informes_scouting 
            SET wyscout_match = ?
            WHERE id = ?
        ''', (wyscout_match, informe_id))
        
        conn.commit()
        conn.close()
        
        return wyscout_match
    
    def guardar_partido_si_no_existe(self, partido_data):
        """Guarda el partido en la BD si no existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Verificar si el partido ya existe
            cursor.execute("SELECT id FROM partidos WHERE id = ?", (partido_data['id'],))
            
            if cursor.fetchone() is None:
                # El partido no existe, guardarlo
                cursor.execute('''
                    INSERT INTO partidos (
                        id, fecha, liga, equipo_local, equipo_visitante,
                        estadio, hora, estado, resultado_local, resultado_visitante
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    partido_data['id'],
                    partido_data.get('fecha', ''),
                    partido_data.get('liga', 'LiveScore'),  # Por defecto
                    partido_data['equipo_local'],
                    partido_data['equipo_visitante'],
                    partido_data.get('estadio', 'N/A'),
                    partido_data.get('hora', 'TBD'),
                    partido_data.get('estado', 'finalizado'),
                    partido_data.get('resultado_local', 0),
                    partido_data.get('resultado_visitante', 0)
                ))
                
                conn.commit()
                logger.info(f"✅ Partido guardado: {partido_data['id']}")
                return True
            else:
                logger.info(f"ℹ️ Partido ya existe: {partido_data['id']}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error guardando partido: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()