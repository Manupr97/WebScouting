# models/partido_model.py - VERSIÓN JSON OPTIMIZADA

import sqlite3
import json
from datetime import datetime, date
import os
import logging
from typing import Dict, List, Optional, Any

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
        if PartidoModel._initialized:
            return
            
        self.db_path = db_path
        self.init_database()
        PartidoModel._initialized = True
        logger.info("✅ PartidoModel inicializado (Singleton)")
    
    def init_database(self):
        """Inicializa las tablas de partidos e informes"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabla de partidos
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partidos (
                id TEXT PRIMARY KEY,
                fecha DATE NOT NULL,
                liga TEXT NOT NULL,
                equipo_local TEXT NOT NULL,
                equipo_visitante TEXT NOT NULL,
                estadio TEXT,
                hora TEXT,
                alineacion_local TEXT,
                alineacion_visitante TEXT,
                suplentes_local TEXT,
                suplentes_visitante TEXT,
                estado TEXT DEFAULT 'programado',
                resultado_local INTEGER DEFAULT 0,
                resultado_visitante INTEGER DEFAULT 0,
                fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                url_besoccer TEXT,
                edad INTEGER,
                nacionalidad TEXT,
                liga_actual TEXT,
                altura INTEGER,
                peso INTEGER,
                valor_mercado TEXT,
                FOREIGN KEY (partido_id) REFERENCES partidos (id)
            )
        ''')
        
        conn.commit()
        conn.close()

    def crear_informe_scouting(self, informe_data):
        """
        Crea un nuevo informe con sistema JSON.
        Se asegura de que las métricas se guarden correctamente (campo y video_completo).
        """
        # Guardar el partido primero si viene de livescore
        partido_id = informe_data.get('partido_id', '')
        if partido_id.startswith('livescore_'):
            partido_data = {
                'id': partido_id,
                'fecha': partido_id.split('_')[-1],
                'equipo_local': 'Por determinar',
                'equipo_visitante': 'Por determinar',
                'liga': 'LiveScore'
            }
            self.guardar_partido_si_no_existe(partido_data)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # === MÉTRICAS ===
            if 'metricas' in informe_data:
                # Si metricas ya es un dict (campo o completo), usarlo tal cual
                if isinstance(informe_data['metricas'], str):
                    try:
                        metricas = json.loads(informe_data['metricas'])
                    except:
                        metricas = {}
                else:
                    metricas = informe_data['metricas']
            else:
                # Si no existe, inicializamos vacío
                metricas = {}
            
            # DEBUG
            print("=== DEBUG INFORME DATA ===")
            print(json.dumps(informe_data, indent=4, ensure_ascii=False))
            print("=== DEBUG METRICAS A GUARDAR ===")
            print(json.dumps(metricas, indent=4, ensure_ascii=False))
            
            # === METADATA ===
            metadata = {
                "version": "3.0",
                "dispositivo": "web",
                "fecha_guardado": datetime.now().isoformat()
            }
            
            # Insertar informe
            cursor.execute('''
                INSERT INTO informes_scouting (
                    partido_id, jugador_nombre, equipo, posicion_evaluada,
                    scout_usuario, tipo_evaluacion, minutos_observados,
                    imagen_url, nota_general, potencial, recomendacion,
                    fortalezas, debilidades, observaciones, metricas, metadata,
                    url_besoccer, edad, nacionalidad, liga_actual,
                    altura, peso, valor_mercado
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                informe_data.get('partido_id'),
                informe_data.get('jugador_nombre'),
                informe_data.get('equipo'),
                informe_data.get('posicion'),
                informe_data.get('scout_usuario'),
                informe_data.get('tipo_evaluacion'),
                informe_data.get('minutos_observados', 90),
                informe_data.get('imagen_url', ''),
                informe_data.get('nota_general'),
                informe_data.get('potencial', 'medio'),
                informe_data.get('recomendacion', 'seguir_observando'),
                informe_data.get('fortalezas', ''),
                informe_data.get('debilidades', ''),
                informe_data.get('observaciones', ''),
                json.dumps(metricas, ensure_ascii=False),  # Guardamos métricas en JSON
                json.dumps(metadata, ensure_ascii=False),
                informe_data.get('url_besoccer', ''),
                informe_data.get('edad'),
                informe_data.get('nacionalidad', ''),
                informe_data.get('liga_actual', ''),
                informe_data.get('altura'),
                informe_data.get('peso'),
                informe_data.get('valor_mercado', '')
            ))
            
            informe_id = cursor.lastrowid
            conn.commit()
            logger.info(f"✅ Informe JSON guardado con ID: {informe_id}")
            
            return informe_id
            
        except Exception as e:
            logger.error(f"❌ Error creando informe: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def _preparar_metricas_json(self, informe_data):
        """
        Prepara las métricas en formato JSON según tipo y posición
        """
        tipo = informe_data.get('tipo_evaluacion', 'campo')
        posicion = informe_data.get('posicion', 'Mediocentro')
        
        metricas = {
            "version": "3.0",
            "posicion": posicion,
            "tipo": tipo
        }
        
        if tipo == 'campo':
            # Para campo: 4 métricas específicas por posición
            evaluaciones = {}
            
            # Las métricas de campo vienen como aspecto_XXX
            for key, value in informe_data.items():
                if key.startswith('aspecto_') and value is not None:
                    nombre_limpio = key.replace('aspecto_', '').replace('_', ' ').title()
                    evaluaciones[nombre_limpio] = value
            
            metricas['evaluaciones'] = evaluaciones
            
        else:  # video_completo
            # Para video_completo: métricas específicas por posición
            categorias = self._obtener_metricas_por_posicion(posicion, informe_data)
            metricas['categorias'] = categorias
        
        # Calcular promedios
        metricas['promedios'] = self._calcular_promedios_metricas(metricas)
        # Log solo si hay promedios válidos
        if any(v > 0 for v in metricas['promedios'].values()):
            logger.info(f"✅ Métricas guardadas con promedios: {metricas['promedios']}")
        
        return metricas

    def _obtener_metricas_por_posicion(self, posicion, informe_data):
        """
        Obtiene las métricas específicas según la posición para video_completo
        Basado en obtener_aspectos_evaluacion_completa()
        """
        # Definir TODAS las métricas por posición
        metricas_por_posicion = {
            'Portero': {
                'tecnicos': ['finalizacion', 'control_balon', 'pase_corto', 'velocidad', 'salto', 'primer_toque'],
                'tacticos': ['posicionamiento', 'vision_juego', 'comunicacion', 'marcaje', 'decision', 'pressing'],
                'fisicos': ['agilidad', 'velocidad', 'salto', 'fuerza'],
                'mentales': ['concentracion', 'confianza', 'presion', 'liderazgo', 'personalidad', 'comunicacion']
            },
            'Central': {
                'tecnicos': ['salto', 'pase_largo', 'control_balon', 'pase_corto', 'marcaje', 'finalizacion'],
                'tacticos': ['marcaje', 'posicionamiento', 'vision_juego', 'decision', 'pressing', 'transiciones'],
                'fisicos': ['fuerza', 'salto', 'velocidad', 'resistencia'],
                'mentales': ['concentracion', 'liderazgo', 'comunicacion', 'presion', 'decision', 'personalidad']
            },
            'Lateral Derecho': {
                'tecnicos': ['pase_largo', 'control_balon', 'pase_corto', 'regate', 'marcaje', 'finalizacion'],
                'tacticos': ['velocidad', 'posicionamiento', 'vision_juego', 'marcaje', 'pressing', 'transiciones'],
                'fisicos': ['velocidad', 'resistencia', 'agilidad', 'fuerza'],
                'mentales': ['concentracion', 'decision', 'comunicacion', 'presion', 'personalidad', 'liderazgo']
            },
            'Lateral Izquierdo': {
                'tecnicos': ['pase_largo', 'control_balon', 'pase_corto', 'regate', 'marcaje', 'finalizacion'],
                'tacticos': ['velocidad', 'posicionamiento', 'vision_juego', 'marcaje', 'pressing', 'transiciones'],
                'fisicos': ['velocidad', 'resistencia', 'agilidad', 'fuerza'],
                'mentales': ['concentracion', 'decision', 'comunicacion', 'presion', 'personalidad', 'liderazgo']
            },
            'Mediocentro Defensivo': {
                'tecnicos': ['marcaje', 'pase_corto', 'pase_largo', 'control_balon', 'finalizacion', 'salto'],
                'tacticos': ['posicionamiento', 'vision_juego', 'marcaje', 'pressing', 'transiciones', 'decision'],
                'fisicos': ['resistencia', 'fuerza', 'agilidad', 'velocidad'],
                'mentales': ['concentracion', 'liderazgo', 'comunicacion', 'decision', 'personalidad', 'presion']
            },
            'Mediocentro': {
                'tecnicos': ['pase_corto', 'pase_largo', 'control_balon', 'regate', 'finalizacion', 'primer_toque'],
                'tacticos': ['vision_juego', 'posicionamiento', 'pressing', 'transiciones', 'marcaje', 'decision'],
                'fisicos': ['resistencia', 'velocidad', 'agilidad', 'fuerza'],
                'mentales': ['creatividad', 'personalidad', 'presion', 'decision', 'comunicacion', 'liderazgo']
            },
            'Media Punta': {
                'tecnicos': ['ultimo_pase', 'control_espacios_reducidos', 'regate_corto', 'tiro', 
                            'pase_entre_lineas', 'tecnica_depurada'],
                'tacticos': ['encontrar_espacios', 'asociacion', 'desmarque_apoyo', 'lectura_defensiva_rival',
                            'timing_pase', 'cambio_orientacion'],
                'fisicos': ['agilidad', 'cambio_ritmo', 'equilibrio', 'coordinacion'],
                'mentales': ['creatividad', 'vision', 'confianza', 'personalidad', 'presion', 'liderazgo_tecnico']
            },
            'Extremo Derecho': {
                'tecnicos': ['regate', 'pase_largo', 'finalizacion', 'control_balon', 'cambio_ritmo', 'tiro'],
                'tacticos': ['velocidad', 'vision_juego', 'posicionamiento', 'transiciones', 'pressing', 'decision'],
                'fisicos': ['velocidad', 'agilidad', 'resistencia', 'cambio_ritmo'],
                'mentales': ['confianza', 'decision', 'personalidad', 'presion', 'creatividad', 'comunicacion']
            },
            'Extremo Izquierdo': {
                'tecnicos': ['regate', 'pase_largo', 'finalizacion', 'control_balon', 'cambio_ritmo', 'tiro'],
                'tacticos': ['velocidad', 'vision_juego', 'posicionamiento', 'transiciones', 'pressing', 'decision'],
                'fisicos': ['velocidad', 'agilidad', 'resistencia', 'cambio_ritmo'],
                'mentales': ['confianza', 'decision', 'personalidad', 'presion', 'creatividad', 'comunicacion']
            },
            'Delantero': {
                'tecnicos': ['finalizacion', 'control_balon', 'primer_toque', 'regate', 'salto', 'tiro'],
                'tacticos': ['posicionamiento', 'vision_juego', 'pressing', 'transiciones', 'marcaje', 'decision'],
                'fisicos': ['velocidad', 'fuerza', 'salto', 'agilidad'],
                'mentales': ['confianza', 'presion', 'decision', 'personalidad', 'comunicacion', 'liderazgo']
            }
        }
        
        # Obtener configuración para la posición
        config_posicion = metricas_por_posicion.get(posicion, metricas_por_posicion['Mediocentro'])
        
        # Construir categorías con valores reales
        categorias = {
            'tecnicos': {},
            'tacticos': {},
            'fisicos': {},
            'mentales': {}
        }
        
        # Mapeo de nombres internos a nombres mostrados
        nombres_bonitos = {
            # Técnicos básicos
            'control_balon': 'Control de balón',
            'primer_toque': 'Primer toque',
            'pase_corto': 'Pase corto',
            'pase_largo': 'Pase largo',
            'finalizacion': 'Finalización',
            'regate': 'Regate',
            
            # Técnicos avanzados
            'ultimo_pase': 'Último pase',
            'control_espacios_reducidos': 'Control en espacios reducidos',
            'regate_corto': 'Regate corto',
            'tiro': 'Tiro',
            'pase_entre_lineas': 'Pase entre líneas',
            'tecnica_depurada': 'Técnica depurada',
            
            # Tácticos
            'vision_juego': 'Visión de juego',
            'posicionamiento': 'Posicionamiento',
            'marcaje': 'Marcaje',
            'pressing': 'Pressing',
            'transiciones': 'Transiciones',
            'encontrar_espacios': 'Encontrar espacios',
            'asociacion': 'Asociación',
            'desmarque_apoyo': 'Desmarque de apoyo',
            'lectura_defensiva_rival': 'Lectura defensiva del rival',
            'timing_pase': 'Timing de pase',
            'cambio_orientacion': 'Cambio de orientación',
            
            # Físicos
            'velocidad': 'Velocidad',
            'resistencia': 'Resistencia',
            'fuerza': 'Fuerza',
            'salto': 'Salto',
            'agilidad': 'Agilidad',
            'cambio_ritmo': 'Cambio de ritmo',
            'equilibrio': 'Equilibrio',
            'coordinacion': 'Coordinación',
            
            # Mentales
            'concentracion': 'Concentración',
            'liderazgo': 'Liderazgo',
            'comunicacion': 'Comunicación',
            'presion': 'Presión',
            'decision': 'Decisión',
            'creatividad': 'Creatividad',
            'vision': 'Visión',
            'confianza': 'Confianza',
            'personalidad': 'Personalidad',
            'liderazgo_tecnico': 'Liderazgo técnico'
        }
        
        # Extraer valores para cada categoría
        for categoria, campos in config_posicion.items():
            for campo in campos:
                if campo in informe_data and informe_data[campo] is not None:
                    nombre_mostrar = nombres_bonitos.get(campo, campo.replace('_', ' ').title())
                    categorias[categoria][nombre_mostrar] = informe_data[campo]
        
        return categorias
    
    def _calcular_promedios_metricas(self, metricas):
        """
        Calcula promedios de las métricas
        """
        promedios = {}
        
        if metricas['tipo'] == 'campo':
            valores = list(metricas.get('evaluaciones', {}).values())
            if valores:
                promedios['general'] = round(sum(valores) / len(valores), 1)
        else:
            # Para video_completo
            for categoria, valores_cat in metricas.get('categorias', {}).items():
                if valores_cat:
                    valores = list(valores_cat.values())
                    promedios[categoria] = round(sum(valores) / len(valores), 1)
            
            # Promedio general
            if promedios:
                valores_promedios = [v for k, v in promedios.items() if k != 'general']
                if valores_promedios:
                    promedios['general'] = round(sum(valores_promedios) / len(valores_promedios), 1)
        
        return promedios
    
    def obtener_informes_por_usuario(self, usuario):
        """
        Obtiene informes parseando JSON automáticamente
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.*, p.equipo_local, p.equipo_visitante, p.fecha
            FROM informes_scouting i
            LEFT JOIN partidos p ON i.partido_id = p.id
            WHERE i.scout_usuario = ?
            ORDER BY i.fecha_creacion DESC
        ''', (usuario,))
        
        columnas = [description[0] for description in cursor.description]
        informes = []
        
        for row in cursor.fetchall():
            informe = dict(zip(columnas, row))
            
            # Parsear JSON automáticamente
            if informe.get('metricas'):
                try:
                    informe['metricas'] = json.loads(informe['metricas'])
                except:
                    informe['metricas'] = {}
            
            if informe.get('metadata'):
                try:
                    informe['metadata'] = json.loads(informe['metadata'])
                except:
                    informe['metadata'] = {}
                    
            if informe.get('integraciones'):
                try:
                    informe['integraciones'] = json.loads(informe['integraciones'])
                except:
                    informe['integraciones'] = {}
            
            informes.append(informe)
        
        conn.close()
        logger.info(f"📊 Obtenidos {len(informes)} informes para usuario {usuario}")
        return informes
    
    def obtener_partidos_por_fecha(self, fecha=None):
        """Obtiene partidos filtrados por fecha"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if fecha:
            cursor.execute('''
                SELECT * FROM partidos WHERE fecha = ? ORDER BY hora
            ''', (fecha,))
        else:
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
    
    def guardar_partido_si_no_existe(self, partido_data):
        """Guarda el partido en la BD si no existe"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT id FROM partidos WHERE id = ?", (partido_data['id'],))
            
            if cursor.fetchone() is None:
                cursor.execute('''
                    INSERT INTO partidos (
                        id, fecha, liga, equipo_local, equipo_visitante,
                        estadio, hora, estado, resultado_local, resultado_visitante
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    partido_data['id'],
                    partido_data.get('fecha', ''),
                    partido_data.get('liga', 'LiveScore'),
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
    
    def obtener_todos_informes(self):
        """Obtiene TODOS los informes de scouting"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT i.*, p.equipo_local, p.equipo_visitante, p.fecha
            FROM informes_scouting i
            LEFT JOIN partidos p ON i.partido_id = p.id
            ORDER BY i.fecha_creacion DESC
        ''')
        
        columns = [description[0] for description in cursor.description]
        informes = []
        
        for row in cursor.fetchall():
            informe = dict(zip(columns, row))
            
            # Parsear JSONs
            for campo_json in ['metricas', 'metadata', 'integraciones']:
                if informe.get(campo_json):
                    try:
                        informe[campo_json] = json.loads(informe[campo_json])
                    except:
                        informe[campo_json] = {}
            
            informes.append(informe)
        
        conn.close()
        logger.info(f"📊 Obtenidos {len(informes)} informes totales")
        return informes

    def obtener_estadisticas_dashboard(self):
        """Obtiene estadísticas para el dashboard"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Estadísticas generales
        cursor.execute('''
            SELECT 
                COUNT(*) as total_informes,
                COUNT(DISTINCT scout_usuario) as total_scouts,
                COUNT(DISTINCT partido_id) as partidos_scouted,
                AVG(nota_general) as nota_promedio
            FROM informes_scouting
        ''')
        
        stats = cursor.fetchone()
        
        # Top scouts
        cursor.execute('''
            SELECT 
                scout_usuario,
                COUNT(*) as cantidad_informes,
                AVG(nota_general) as nota_promedio
            FROM informes_scouting
            GROUP BY scout_usuario
            ORDER BY cantidad_informes DESC
            LIMIT 5
        ''')
        
        top_scouts = cursor.fetchall()
        
        conn.close()
        
        return {
            'generales': {
                'total_informes': stats[0] or 0,
                'total_scouts': stats[1] or 0,
                'partidos_scouted': stats[2] or 0,
                'nota_promedio': round(stats[3] or 0, 1) if stats[3] else 0
            },
            'top_scouts': [
                {
                    'scout': scout[0],
                    'informes': scout[1],
                    'nota_promedio': round(scout[2] or 0, 1) if scout[2] else 0
                } for scout in top_scouts
            ]
        }