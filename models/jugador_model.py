# models/jugador_model.py - VERSIÓN CON SINGLETON Y CACHE

import sqlite3
import pandas as pd
import os
from datetime import datetime
import random
from fuzzywuzzy import fuzz, process
import logging
import time
import streamlit as st

# Configurar logging para debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FUNCIÓN GLOBAL CACHEADA PARA STREAMLIT
@st.cache_data(ttl=3600)
def cargar_wyscout_global(wyscout_path):
    """Carga datos de Wyscout - CACHEADO POR STREAMLIT"""
    try:
        if not os.path.exists(wyscout_path):
            logging.error(f"❌ Archivo no encontrado: {wyscout_path}")
            return pd.DataFrame()
        
        logging.info("📂 Cargando Wyscout desde archivo...")
        start_time = time.time()
        
        # Cargar Excel
        df = pd.read_excel(wyscout_path, engine='openpyxl')
        
        load_time = time.time() - start_time
        logging.info(f"✅ Wyscout cargado: {len(df)} jugadores en {load_time:.2f}s")
        
        return df
        
    except Exception as e:
        logging.error(f"❌ Error cargando Wyscout: {str(e)}")
        return pd.DataFrame()

class JugadorModel:
    _instance = None
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path="data/jugadores.db", wyscout_path="data/wyscout_LaLiga_limpio.xlsx"):
        # Solo inicializar una vez
        if JugadorModel._initialized:
            return
            
        self.db_path = db_path
        self.wyscout_path = wyscout_path
        self._wyscout_cache = None
        
        # MAPEO DE COLUMNAS (guardarlo como atributo de instancia)
        self.column_mapping = {
            'nombre': 'jugador',
            'equipo': 'equipo_durante_el_período_seleccionado',
            'posicion': 'pos_principal',
            'posicion_secundaria': 'pos_secundaria',
            'edad': 'edad',
            'fecha_nacimiento': 'fecha_nac',
            'altura': 'altura',
            'peso': 'peso',
            'valor_mercado': 'valor_de_mercado_(transfermarkt)',
            'pais': 'país_de_nacimiento',
            'pasaporte': 'pasaporte',
            'pie_preferido': 'pie',
            'contrato_hasta': 'vencimiento_contrato',
            'en_prestamo': 'en_prestamo',
            
            # Estadísticas básicas
            'partidos_jugados': 'partidos_jugados',
            'minutos': 'min',
            'goles': 'goles',
            'asistencias': 'asistencias',
            'tarjetas_amarillas': 'tarjetas_amarillas',
            'tarjetas_rojas': 'tarjetas_rojas',
            
            # Estadísticas avanzadas
            'xg': 'xg',
            'xa': 'xa',
            'remates': 'remates',
            'duelos_ganados_pct': '%duelos_ganados,_',
            'precision_pases_pct': '%precisión_pases,_',
            'regates_realizados_pct': '%regates_realizados,_',
            'duelos_aereos_pct': '%duelos_aéreos_ganados,_'
        }
        
        # Guardar referencias a columnas clave
        self.name_column = self.column_mapping['nombre']
        self.team_column = self.column_mapping['equipo']
        self.position_column = self.column_mapping['posicion']
        
        # Inicializar base de datos
        self.init_database()
        
        JugadorModel._initialized = True
        logger.info("✅ JugadorModel inicializado (Singleton)")
    
    def _load_wyscout_data(self):
        """Carga datos de Wyscout usando cache global"""
        # Usar la función global cacheada
        return cargar_wyscout_global(self.wyscout_path)
    
    @property
    def wyscout_data(self):
        """Lazy loading de datos Wyscout"""
        if self._wyscout_cache is None:
            self._wyscout_cache = self._load_wyscout_data()
        return self._wyscout_cache
    
    @wyscout_data.setter
    def wyscout_data(self, value):
        """Setter para wyscout_data"""
        self._wyscout_cache = value
    
    def debug_column_mapping(self):
        """🔍 Función de debug para verificar el mapeo"""
        if self.wyscout_data is None or self.wyscout_data.empty:
            return "❌ No hay datos cargados"
        
        debug_info = []
        debug_info.append("🔍 VERIFICACIÓN DE MAPEO:")
        debug_info.append(f"📊 Total jugadores: {len(self.wyscout_data)}")
        debug_info.append(f"📋 Total columnas: {len(self.wyscout_data.columns)}")
        debug_info.append("")
        
        # Verificar columnas clave
        for key, col_name in self.column_mapping.items():
            if col_name in self.wyscout_data.columns:
                sample_value = self.wyscout_data[col_name].iloc[0] if len(self.wyscout_data) > 0 else "N/A"
                debug_info.append(f"✅ {key}: '{col_name}' → Ejemplo: {sample_value}")
            else:
                debug_info.append(f"❌ {key}: '{col_name}' → NO ENCONTRADA")
        
        debug_info.append("")
        debug_info.append("👥 PRIMEROS 5 JUGADORES:")
        for i in range(min(5, len(self.wyscout_data))):
            nombre = self.wyscout_data[self.column_mapping['nombre']].iloc[i]
            equipo = self.wyscout_data[self.column_mapping['equipo']].iloc[i]
            posicion = self.wyscout_data[self.column_mapping['posicion']].iloc[i]
            debug_info.append(f"{i+1}. {nombre} ({equipo}) - {posicion}")
        
        return "\n".join(debug_info)
    
    def buscar_jugador_en_wyscout(self, nombre_jugador, equipo_jugador=None, umbral_confianza=70):
        """Alias para mantener compatibilidad"""
        return self.buscar_jugador_en_wyscout_mejorado(nombre_jugador, equipo_jugador, umbral_confianza)
    
    def buscar_jugador_en_wyscout_mejorado(self, nombre_jugador, equipo_jugador=None, umbral_confianza=70):
        """
        🔧 VERSIÓN MEJORADA de búsqueda en Wyscout
        """
        if self.wyscout_data is None or self.wyscout_data.empty:
            logger.warning("⚠️ No hay datos de Wyscout cargados")
            return None
            
        logger.info(f"🔍 Buscando: '{nombre_jugador}'" + (f" en '{equipo_jugador}'" if equipo_jugador else ""))
        
        # Preparar datos para búsqueda
        nombre_limpio = self._limpiar_nombre(nombre_jugador)
        equipo_limpio = self._limpiar_nombre(equipo_jugador) if equipo_jugador else None
        
        # Obtener columnas relevantes
        col_nombre = self.column_mapping['nombre']  # 'jugador'
        col_equipo = self.column_mapping['equipo']  # 'equipo_durante_el_período_seleccionado'
        
        mejores_matches = []
        
        # ALGORITMO 1: Coincidencia exacta por nombre
        logger.info(f"🎯 Buscando coincidencia exacta: '{nombre_limpio}'")
        exact_matches = self.wyscout_data[
            self.wyscout_data[col_nombre].str.lower().str.strip() == nombre_limpio.lower()
        ]
        
        if not exact_matches.empty:
            for _, jugador in exact_matches.iterrows():
                confianza = 100.0
                if equipo_jugador:
                    # Si se especifica equipo, verificar coincidencia
                    equipo_encontrado = str(jugador[col_equipo]).lower().strip()
                    if equipo_limpio.lower() in equipo_encontrado or equipo_encontrado in equipo_limpio.lower():
                        confianza = 100.0
                    else:
                        confianza = 90.0  # Penalizar ligeramente si no coincide el equipo
                
                mejores_matches.append({
                    'jugador': jugador,
                    'confianza': confianza,
                    'algoritmo': 'exacto_nombre'
                })
        
        # ALGORITMO 2: Fuzzy matching por nombre
        if len(mejores_matches) == 0:
            logger.info(f"🔄 Aplicando fuzzy matching...")
            for _, jugador in self.wyscout_data.iterrows():
                nombre_wyscout = str(jugador[col_nombre]).lower().strip()
                confianza_nombre = fuzz.token_sort_ratio(nombre_limpio.lower(), nombre_wyscout)
                
                if confianza_nombre >= umbral_confianza:
                    confianza_final = confianza_nombre
                    
                    # Bonus si coincide el equipo
                    if equipo_jugador:
                        equipo_wyscout = str(jugador[col_equipo]).lower().strip()
                        if equipo_limpio.lower() in equipo_wyscout or equipo_wyscout in equipo_limpio.lower():
                            confianza_final = min(100.0, confianza_final + 10)
                    
                    mejores_matches.append({
                        'jugador': jugador,
                        'confianza': confianza_final,
                        'algoritmo': 'fuzzy_nombre'
                    })
        
        # ALGORITMO 3: Búsqueda parcial (apellidos, nombres)
        if len(mejores_matches) == 0:
            logger.info(f"🔄 Buscando por partes del nombre...")
            palabras_busqueda = nombre_limpio.split()
            
            for _, jugador in self.wyscout_data.iterrows():
                nombre_wyscout = str(jugador[col_nombre]).lower().strip()
                
                # Verificar si alguna palabra del nombre buscado está en el nombre de Wyscout
                matches_parciales = 0
                for palabra in palabras_busqueda:
                    if len(palabra) >= 3 and palabra in nombre_wyscout:
                        matches_parciales += 1
                
                if matches_parciales > 0:
                    confianza = (matches_parciales / len(palabras_busqueda)) * 80  # Máximo 80%
                    
                    if confianza >= umbral_confianza:
                        mejores_matches.append({
                            'jugador': jugador,
                            'confianza': confianza,
                            'algoritmo': 'parcial_nombre'
                        })
        
        # Ordenar por confianza y seleccionar el mejor
        if mejores_matches:
            mejores_matches.sort(key=lambda x: x['confianza'], reverse=True)
            mejor_match = mejores_matches[0]
            
            nombre_encontrado = mejor_match['jugador'][col_nombre]
            equipo_encontrado = mejor_match['jugador'][col_equipo]
            
            logger.info(f"✅ ENCONTRADO: '{nombre_encontrado}' ({equipo_encontrado}) "
                       f"- Confianza: {mejor_match['confianza']:.1f}% ({mejor_match['algoritmo']})")
            
            # Guardar búsqueda para debug
            self._guardar_busqueda(
                nombre_jugador, equipo_jugador or "N/A",
                nombre_encontrado, equipo_encontrado,
                mejor_match['confianza'], mejor_match['algoritmo']
            )
            
            return {
                'datos_jugador': mejor_match['jugador'],
                'confianza': mejor_match['confianza'],
                'algoritmo': mejor_match['algoritmo']
            }
        
        logger.warning(f"❌ NO ENCONTRADO: '{nombre_jugador}'" + (f" en '{equipo_jugador}'" if equipo_jugador else ""))
        self._sugerir_nombres_similares(nombre_jugador)
        return None
    
    def _sugerir_nombres_similares(self, nombre_buscado, limite=5):
        """Sugiere nombres similares para ayudar con el debug"""
        if self.wyscout_data is None or self.wyscout_data.empty:
            return
        
        col_nombre = self.column_mapping['nombre']
        nombres_disponibles = self.wyscout_data[col_nombre].astype(str).tolist()
        
        # Usar fuzzywuzzy para encontrar los más similares
        matches = process.extract(nombre_buscado, nombres_disponibles, limit=limite)
        
        if matches:
            logger.info(f"💡 ¿Quisiste decir alguno de estos?")
            for nombre, confianza in matches:
                logger.info(f"   • {nombre} ({confianza}%)")
    
    def init_database(self):
        """Inicializa la base de datos - COMPATIBLE CON BD ACTUAL"""
        # Crear carpeta data si no existe
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # ✅ USAR ESTRUCTURA BÁSICA COMPATIBLE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jugadores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                apellidos TEXT,
                nombre_completo TEXT,
                edad INTEGER,
                posicion TEXT,
                equipo TEXT,
                liga TEXT,
                pais TEXT,
                altura INTEGER,
                peso INTEGER,
                pie_preferido TEXT,
                valor_mercado REAL,
                salario REAL,
                partidos_jugados INTEGER,
                minutos_jugados INTEGER,
                goles INTEGER,
                asistencias INTEGER,
                tarjetas_amarillas INTEGER,
                tarjetas_rojas INTEGER,
                origen_datos TEXT,
                confianza_match REAL,
                veces_observado INTEGER DEFAULT 1,
                ultimo_informe_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jugadores_observados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                jugador TEXT,
                nombre_completo TEXT,
                equipo TEXT,
                posicion TEXT,
                posicion_principal TEXT,
                posicion_secundaria TEXT,
                numero_camiseta INTEGER,
                edad INTEGER,
                nacionalidad TEXT,
                liga TEXT,
                pie_dominante TEXT,
                altura INTEGER,
                peso INTEGER,
                valor_mercado TEXT,
                elo_besoccer INTEGER,
                imagen_url TEXT,
                escudo_equipo TEXT,
                veces_observado INTEGER DEFAULT 1,
                estado TEXT DEFAULT 'Evaluado',
                nota_general REAL,
                nota_promedio REAL,
                mejor_nota REAL,
                peor_nota REAL,
                total_informes INTEGER,
                ultima_fecha_visto DATE,
                scout_agregado TEXT,
                url_besoccer TEXT,
                datos_json TEXT,
                ultimo_partido_id TEXT,
                metricas TEXT,
                fecha_agregado DATE DEFAULT CURRENT_DATE
            )
        ''')
        
        # Crear tabla de historial de coincidencias (para debug)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS busquedas_wyscout (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre_buscado TEXT,
                equipo_buscado TEXT,
                nombre_encontrado TEXT,
                equipo_encontrado TEXT,
                confianza REAL,
                algoritmo TEXT,
                fecha_busqueda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                jugador_id INTEGER,
                FOREIGN KEY (jugador_id) REFERENCES jugadores (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Poblar con datos de ejemplo si está vacía
        self.poblar_datos_ejemplo()
    
    def añadir_jugador_observado(self, datos, informe_data=None):
        """
        Inserta o actualiza un jugador en la tabla jugadores_observados
        usando datos combinados de Wyscout o BeSoccer + informe
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        nombre = str(datos.get("jugador", "")).strip()
        equipo = str(datos.get("equipo_actual", "")).strip() or str(datos.get("equipo", "")).strip()
        nombre_completo = nombre  # En muchos casos no tienes nombre + apellidos
        
        # Buscar jugador existente
        cursor.execute('''
            SELECT id, veces_observado, nota_promedio, mejor_nota, peor_nota, total_informes
            FROM jugadores_observados
            WHERE LOWER(TRIM(nombre_completo)) = LOWER(TRIM(?)) AND LOWER(TRIM(equipo)) = LOWER(TRIM(?))
        ''', (nombre_completo, equipo))
        
        jugador_existente = cursor.fetchone()
        
        # Sacamos la nota del informe (por defecto 5 si no hay)
        nueva_nota = informe_data.get("nota_general", 5) if informe_data else 5
        scout = informe_data.get("scout_usuario", "admin") if informe_data else "admin"
        fecha_actual = datetime.now().strftime('%Y-%m-%d')
        
        try:
            if jugador_existente:
                jugador_id, veces_observado, nota_promedio, mejor_nota, peor_nota, total_informes = jugador_existente
                veces_observado += 1
                total_informes = (total_informes or 0) + 1
                
                nueva_nota_prom = ((nota_promedio or 0) * (veces_observado - 1) + nueva_nota) / veces_observado
                mejor_nota = max(mejor_nota or nueva_nota, nueva_nota)
                peor_nota = min(peor_nota or nueva_nota, nueva_nota)
                
                cursor.execute('''
                    UPDATE jugadores_observados SET
                        veces_observado = ?,
                        total_informes = ?,
                        nota_general = ?,
                        nota_promedio = ?,
                        mejor_nota = ?,
                        peor_nota = ?,
                        ultima_fecha_visto = ?,
                        scout_agregado = ?,
                        url_besoccer = COALESCE(?, url_besoccer),
                        imagen_url = COALESCE(?, imagen_url),
                        escudo_equipo = COALESCE(?, escudo_equipo)
                    WHERE id = ?
                ''', (
                    veces_observado, total_informes, nueva_nota, nueva_nota_prom,
                    mejor_nota, peor_nota, fecha_actual, scout,
                    datos.get("url_besoccer", ""),
                    datos.get("imagen_url", ""),
                    datos.get("escudo_equipo", ""),
                    jugador_id
                ))
                logger.info(f"🔁 Jugador actualizado: {nombre} ({equipo})")
            
            else:
                # Insertar nuevo
                cursor.execute('''
                    INSERT INTO jugadores_observados (
                        jugador, nombre_completo, equipo, posicion_principal, posicion_secundaria,
                        edad, nacionalidad, liga, pie_dominante, altura, peso,
                        valor_mercado, elo_besoccer, imagen_url, escudo_equipo,
                        veces_observado, estado, nota_general, nota_promedio,
                        mejor_nota, peor_nota, total_informes,
                        ultima_fecha_visto, scout_agregado, url_besoccer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    nombre, nombre_completo, equipo,
                    datos.get("posicion_principal", ""),
                    datos.get("posicion_secundaria", ""),
                    datos.get("edad"),
                    datos.get("nacionalidad", ""),
                    datos.get("liga_actual", ""),
                    datos.get("pie_preferido", ""),
                    datos.get("altura"),
                    datos.get("peso"),
                    datos.get("valor_mercado", ""),
                    datos.get("elo"),
                    datos.get("imagen_url", ""),
                    datos.get("escudo_equipo", ""),
                    1, 'Evaluado',
                    nueva_nota, nueva_nota, nueva_nota, nueva_nota, 1,
                    fecha_actual, scout, datos.get("url_besoccer", "")
                ))
                jugador_id = cursor.lastrowid
                logger.info(f"✅ Nuevo jugador añadido: {nombre} ({equipo}) - ID: {jugador_id}")
            
            conn.commit()
            return jugador_id
        
        except Exception as e:
            logger.error(f"❌ Error añadiendo jugador observado: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def añadir_jugador_manual(self, nombre, equipo, posicion='N/A', nota_promedio=5, scout='admin', informe_id=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Ver si ya existe
            cursor.execute('''
                SELECT id, veces_observado, nota_general 
                FROM jugadores_observados 
                WHERE (jugador = ? OR nombre_completo = ?) AND equipo = ?
            ''', (nombre, nombre, equipo))

            existe = cursor.fetchone()

            if existe:
                jugador_id, veces_actual, nota_anterior = existe
                nueva_nota = ((nota_anterior or 0) * veces_actual + nota_promedio) / (veces_actual + 1)

                cursor.execute('''
                    UPDATE jugadores_observados SET
                        veces_observado = veces_observado + 1,
                        nota_general = ?,
                        nota_promedio = ?,
                        mejor_nota = MAX(mejor_nota, ?),
                        peor_nota = MIN(peor_nota, ?),
                        total_informes = total_informes + 1,
                        ultima_fecha_visto = ?,
                        scout_agregado = ?
                    WHERE id = ?
                ''', (
                    nueva_nota, nueva_nota, nota_promedio, nota_promedio,
                    datetime.now().strftime('%Y-%m-%d'), scout, jugador_id
                ))

            else:
                # Crear jugador nuevo con todos los campos mínimos
                cursor.execute('''
                    INSERT INTO jugadores_observados (
                        jugador, nombre_completo, equipo, posicion_principal,
                        edad, nacionalidad, liga, pie_dominante, altura, peso,
                        valor_mercado, elo_besoccer, imagen_url, escudo_equipo,
                        veces_observado, estado, nota_general, nota_promedio,
                        mejor_nota, peor_nota, total_informes,
                        ultima_fecha_visto, scout_agregado, url_besoccer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    nombre, nombre, equipo, posicion,
                    None, '', '', '', None, None,
                    '', '', '', '',
                    1, 'Evaluado', nota_promedio, nota_promedio,
                    nota_promedio, nota_promedio, 1,
                    datetime.now().strftime('%Y-%m-%d'), scout, ''
                ))

                jugador_id = cursor.lastrowid

            conn.commit()
            logger.info(f"✅ Jugador {'actualizado' if existe else 'añadido'}: {nombre} (ID: {jugador_id})")
            return jugador_id

        except Exception as e:
            logger.error(f"❌ Error: {str(e)}")
            conn.rollback()
            raise

        finally:
            conn.close()
    
    def _limpiar_nombre(self, texto):
        """Limpia texto para comparación"""
        import re
        if pd.isna(texto) or texto is None:
            return ""
        
        # Convertir a string y limpiar
        texto = str(texto).strip()
        # Remover caracteres especiales pero mantener acentos
        texto = re.sub(r'[^\w\sáéíóúñü]', '', texto, flags=re.IGNORECASE)
        # Normalizar espacios
        texto = ' '.join(texto.split())
        
        return texto
    
    def _safe_int(self, valor):
        """Convierte valor a int de forma segura"""
        try:
            if pd.isna(valor) or valor is None or valor == '':
                return None
            return int(float(valor))
        except (ValueError, TypeError):
            return None
    
    def _safe_float(self, valor):
        """Convierte valor a float de forma segura"""
        try:
            if pd.isna(valor) or valor is None or valor == '':
                return None
            return float(valor)
        except (ValueError, TypeError):
            return None
    
    def _guardar_busqueda(self, nombre_buscado, equipo_buscado, nombre_encontrado, 
                         equipo_encontrado, confianza, algoritmo, jugador_id=None):
        """Guarda registro de búsqueda para debug"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO busquedas_wyscout (
                nombre_buscado, equipo_buscado, nombre_encontrado, 
                equipo_encontrado, confianza, algoritmo, jugador_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            nombre_buscado, equipo_buscado, nombre_encontrado,
            equipo_encontrado, confianza, algoritmo, jugador_id
        ))
        
        conn.commit()
        conn.close()
    
    # === MÉTODOS EXISTENTES (mantener todos) ===
    
    def obtener_jugadores_observados_con_informes(self):
        """
        Obtiene SOLO jugadores que tienen informes reales asociados
        """
        conn = sqlite3.connect(self.db_path)
        
        # Query que une jugadores con informes para asegurar que solo mostramos 
        # jugadores con informes reales
        df = pd.read_sql_query('''
            SELECT DISTINCT j.*, 
                COUNT(DISTINCT i.id) as total_informes,
                MAX(i.fecha_creacion) as ultimo_informe,
                AVG(i.nota_general) as nota_promedio,
                CASE 
                    WHEN j.veces_observado = 1 THEN 'Nuevo'
                    WHEN j.veces_observado <= 3 THEN 'Seguimiento'
                    ELSE 'Objetivo'
                END as estado_observacion
            FROM jugadores j
            INNER JOIN informes_scouting i ON (
                LOWER(TRIM(j.nombre_completo)) = LOWER(TRIM(i.jugador_nombre))
                AND LOWER(TRIM(j.equipo)) = LOWER(TRIM(i.equipo))
            )
            GROUP BY j.id
            ORDER BY ultimo_informe DESC
        ''', conn)
        
        conn.close()
        
        logger.info(f"📊 Obtenidos {len(df)} jugadores con informes reales")
        return df
    
    def obtener_jugadores_observados(self):
        """Obtiene todos los jugadores observados por el scout"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT *, 
                CASE 
                    WHEN veces_observado = 1 THEN 'Nuevo'
                    WHEN veces_observado <= 3 THEN 'Seguimiento'
                    ELSE 'Objetivo'
                END as estado_observacion
            FROM jugadores_observados
            ORDER BY ultima_fecha_visto DESC
        ''', conn)
        conn.close()
        return df
    
    def obtener_estadisticas_busquedas(self):
        """Obtiene estadísticas de las búsquedas realizadas"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query('''
            SELECT algoritmo, 
                   COUNT(*) as total_busquedas,
                   AVG(confianza) as confianza_promedio,
                   MIN(confianza) as confianza_minima,
                   MAX(confianza) as confianza_maxima
            FROM busquedas_wyscout 
            GROUP BY algoritmo
            ORDER BY total_busquedas DESC
        ''', conn)
        conn.close()
        return df
    
    def poblar_datos_ejemplo(self):
        """Puebla la base de datos con datos de ejemplo realistas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM jugadores")
        if cursor.fetchone()[0] > 0:
            conn.close()
            return
        
        # Datos de ejemplo realistas
        jugadores_ejemplo = [
            {
                'nombre': 'Lionel', 'apellidos': 'Messi', 'nombre_completo': 'Lionel Messi',
                'edad': 36, 'posicion': 'Extremo derecho', 'equipo': 'Inter Miami', 
                'liga': 'MLS', 'pais': 'Argentina', 'altura': 170, 'peso': 72,
                'pie_preferido': 'Izquierdo', 'valor_mercado': 25000000, 'salario': 50000000,
                'partidos_jugados': 25, 'minutos_jugados': 2100, 'goles': 18, 'asistencias': 12,
                'tarjetas_amarillas': 2, 'tarjetas_rojas': 0
            },
            {
                'nombre': 'Kylian', 'apellidos': 'Mbappé', 'nombre_completo': 'Kylian Mbappé',
                'edad': 25, 'posicion': 'Delantero centro', 'equipo': 'Real Madrid', 
                'liga': 'La Liga', 'pais': 'Francia', 'altura': 178, 'peso': 73,
                'pie_preferido': 'Derecho', 'valor_mercado': 180000000, 'salario': 25000000,
                'partidos_jugados': 28, 'minutos_jugados': 2450, 'goles': 22, 'asistencias': 8,
                'tarjetas_amarillas': 3, 'tarjetas_rojas': 0
            }
        ]
        
        # Insertar jugadores de ejemplo
        for jugador in jugadores_ejemplo:
            cursor.execute('''
                INSERT INTO jugadores (
                    nombre, apellidos, nombre_completo, edad, posicion, equipo, liga, pais, 
                    altura, peso, pie_preferido, valor_mercado, salario, partidos_jugados, 
                    minutos_jugados, goles, asistencias, tarjetas_amarillas, tarjetas_rojas,
                    origen_datos
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                jugador['nombre'], jugador['apellidos'], jugador['nombre_completo'],
                jugador['edad'], jugador['posicion'], jugador['equipo'], jugador['liga'],
                jugador['pais'], jugador['altura'], jugador['peso'], jugador['pie_preferido'],
                jugador['valor_mercado'], jugador['salario'], jugador['partidos_jugados'],
                jugador['minutos_jugados'], jugador['goles'], jugador['asistencias'],
                jugador['tarjetas_amarillas'], jugador['tarjetas_rojas'], 'manual'
            ))
        
        conn.commit()
        conn.close()
    
    def obtener_todos_jugadores(self):
        """Obtiene todos los jugadores"""
        conn = sqlite3.connect(self.db_path)
        df = pd.read_sql_query("SELECT * FROM jugadores", conn)
        conn.close()
        return df
    
    def buscar_jugadores(self, nombre=None, posicion=None, equipo=None, liga=None, pais=None):
        """Busca jugadores con filtros"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM jugadores WHERE 1=1"
        params = []
        
        if nombre:
            query += " AND (nombre LIKE ? OR apellidos LIKE ? OR nombre_completo LIKE ?)"
            params.extend([f"%{nombre}%", f"%{nombre}%", f"%{nombre}%"])
        
        if posicion:
            query += " AND posicion = ?"
            params.append(posicion)
        
        if equipo:
            query += " AND equipo LIKE ?"
            params.append(f"%{equipo}%")
        
        if liga:
            query += " AND liga = ?"
            params.append(liga)
        
        if pais:
            query += " AND pais = ?"
            params.append(pais)
        
        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df
    
    def obtener_jugador_por_id(self, jugador_id):
        """Obtiene un jugador específico por ID"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM jugadores WHERE id = ?", (jugador_id,))
        resultado = cursor.fetchone()
        
        if resultado:
            # Convertir a diccionario
            columnas = [desc[0] for desc in cursor.description]
            jugador = dict(zip(columnas, resultado))
        else:
            jugador = None
        
        conn.close()
        return jugador
    
    def obtener_posiciones(self):
        """Obtiene todas las posiciones únicas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT posicion FROM jugadores WHERE posicion IS NOT NULL ORDER BY posicion")
        posiciones = [row[0] for row in cursor.fetchall()]
        conn.close()
        return posiciones
    
    def obtener_ligas(self):
        """Obtiene todas las ligas únicas"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT liga FROM jugadores WHERE liga IS NOT NULL ORDER BY liga")
        ligas = [row[0] for row in cursor.fetchall()]
        conn.close()
        return ligas
    
    def obtener_paises(self):
        """Obtiene todos los países únicos"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT pais FROM jugadores WHERE pais IS NOT NULL ORDER BY pais")
        paises = [row[0] for row in cursor.fetchall()]
        conn.close()
        return paises
    
    def get_all_wyscout_players(self):
        """
        Obtiene todos los jugadores de Wyscout con cache inteligente
        """
        return self.wyscout_data.copy() if self.wyscout_data is not None else pd.DataFrame()
    
    def clear_wyscout_cache(self):
        """Limpia el cache de Wyscout (para admin)"""
        st.cache_data.clear()
        self._wyscout_cache = None
        logging.info("🗑️ Cache de Wyscout limpiado")