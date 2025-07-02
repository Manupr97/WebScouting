# models/jugador_model.py - VERSIÓN COMPATIBLE CON BD ACTUAL

import sqlite3
import pandas as pd
import os
from datetime import datetime
import random
from fuzzywuzzy import fuzz, process
import logging
import time

# Configurar logging para debug
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JugadorModel:
    def __init__(self, db_path="data/jugadores.db", wyscout_path="data/wyscout_LaLiga_limpio.xlsx"):
        self.db_path = db_path
        self.wyscout_path = wyscout_path
        self.wyscout_data = None  # Cache para evitar recargar
        self._wyscout_cache = None
        self._wyscout_cache_time = None
        self._cache_duration = 3600  # 1 hora en segundos
        
        # Inicializar base de datos primero
        self.init_database()
        
        # Cargar datos de Wyscout
        self.wyscout_data = self._load_wyscout_data()
    
    def _load_wyscout_data(self):
        """Carga datos de Wyscout desde archivo Excel"""
        try:
            wyscout_path = 'data/wyscout_LaLiga_limpio.xlsx'
            
            if not os.path.exists(wyscout_path):
                logging.error(f"❌ Archivo no encontrado: {wyscout_path}")
                return pd.DataFrame()
            
            logging.info("📂 Cargando Wyscout desde archivo...")
            start_time = time.time()
            
            # Cargar Excel
            df = pd.read_excel(wyscout_path, engine='openpyxl')
            
            # APLICAR TU MAPEO DE COLUMNAS COMPLETO
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
            
            # Guardar en cache
            self._wyscout_cache = df
            self._wyscout_cache_time = time.time()
            
            load_time = time.time() - start_time
            logging.info(f"✅ Wyscout cargado: {len(df)} jugadores en {load_time:.2f}s")
            
            # Solo debug si está activado
            if logging.getLogger().isEnabledFor(logging.DEBUG):
                logging.debug("📋 Mapeo corregido aplicado exitosamente")
                logging.debug(f"🎯 Columnas clave: nombre='{self.name_column}', equipo='{self.team_column}', posicion='{self.position_column}'")
            
            return df.copy()
            
        except Exception as e:
            logging.error(f"❌ Error cargando Wyscout: {str(e)}")
            return pd.DataFrame()
    
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
                nombre TEXT NOT NULL,
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
                
                -- Estadísticas básicas
                partidos_jugados INTEGER DEFAULT 0,
                minutos_jugados INTEGER DEFAULT 0,
                goles INTEGER DEFAULT 0,
                asistencias INTEGER DEFAULT 0,
                tarjetas_amarillas INTEGER DEFAULT 0,
                tarjetas_rojas INTEGER DEFAULT 0,
                
                -- Estadísticas avanzadas básicas
                pases_completados INTEGER DEFAULT 0,
                pases_intentados INTEGER DEFAULT 0,
                precision_pases REAL DEFAULT 0,
                regates_completados INTEGER DEFAULT 0,
                regates_intentados INTEGER DEFAULT 0,
                duelos_aereos_ganados INTEGER DEFAULT 0,
                duelos_aereos_totales INTEGER DEFAULT 0,
                interceptaciones INTEGER DEFAULT 0,
                recuperaciones INTEGER DEFAULT 0,
                
                -- Información de scouting
                veces_observado INTEGER DEFAULT 1,
                primer_informe_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ultimo_informe_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                origen_datos TEXT DEFAULT 'wyscout',
                confianza_match REAL DEFAULT 100.0,
                
                -- Información adicional
                fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                lesionado BOOLEAN DEFAULT 0,
                agente TEXT
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
    
    def añadir_jugador_observado(self, datos_wyscout, confianza, algoritmo, informe_id=None):
        """
        ✅ VERSIÓN COMPATIBLE - Añade jugador usando solo columnas existentes
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extraer datos usando el mapeo correcto
        nombre_completo = str(datos_wyscout.get(self.column_mapping['nombre'], ''))
        partes_nombre = nombre_completo.split(' ', 1)
        primer_nombre = partes_nombre[0] if partes_nombre else ''
        apellidos = partes_nombre[1] if len(partes_nombre) > 1 else ''
        
        equipo = str(datos_wyscout.get(self.column_mapping['equipo'], ''))
        
        # Verificar si el jugador ya existe
        cursor.execute('''
            SELECT id, veces_observado FROM jugadores 
            WHERE nombre_completo = ? AND equipo = ?
        ''', (nombre_completo, equipo))
        
        jugador_existente = cursor.fetchone()
        
        if jugador_existente:
            # Actualizar jugador existente
            jugador_id, veces_observado = jugador_existente
            cursor.execute('''
                UPDATE jugadores SET 
                    veces_observado = ?,
                    ultimo_informe_fecha = CURRENT_TIMESTAMP,
                    confianza_match = ?
                WHERE id = ?
            ''', (veces_observado + 1, confianza, jugador_id))
            
            logger.info(f"📝 Jugador actualizado: {nombre_completo} (observado {veces_observado + 1} veces)")
            
        else:
            # ✅ INSERTAR SOLO COLUMNAS QUE EXISTEN EN LA BD ACTUAL
            cursor.execute('''
                INSERT INTO jugadores (
                    nombre, apellidos, nombre_completo, edad, posicion,
                    equipo, pais, altura, peso, pie_preferido, valor_mercado,
                    partidos_jugados, minutos_jugados, goles, asistencias, 
                    tarjetas_amarillas, tarjetas_rojas,
                    origen_datos, confianza_match
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                primer_nombre, apellidos, nombre_completo,
                self._safe_int(datos_wyscout.get(self.column_mapping['edad'])),
                str(datos_wyscout.get(self.column_mapping['posicion'], '')),
                equipo,
                str(datos_wyscout.get(self.column_mapping['pais'], '')),
                self._safe_int(datos_wyscout.get(self.column_mapping['altura'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['peso'])),
                str(datos_wyscout.get(self.column_mapping['pie_preferido'], '')),
                self._safe_float(datos_wyscout.get(self.column_mapping['valor_mercado'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['partidos_jugados'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['minutos'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['goles'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['asistencias'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['tarjetas_amarillas'])),
                self._safe_int(datos_wyscout.get(self.column_mapping['tarjetas_rojas'])),
                'wyscout',
                confianza
            ))
            
            jugador_id = cursor.lastrowid
            logger.info(f"✅ Nuevo jugador añadido: {nombre_completo} (ID: {jugador_id})")
        
        conn.commit()
        conn.close()
        
        return jugador_id
    
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
            FROM jugadores 
            ORDER BY ultimo_informe_fecha DESC
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
        NO recarga si ya está en memoria
        """
        # Verificar cache
        if self._wyscout_cache is not None:
            if self._wyscout_cache_time and (time.time() - self._wyscout_cache_time) < self._cache_duration:
                # Cache válido, retornar copia
                logging.debug("📦 Usando cache de Wyscout")
                return self._wyscout_cache.copy()
        
        # Cache inválido o no existe, cargar datos
        return self._load_wyscout_data()
    
    def clear_wyscout_cache(self):
        """Limpia el cache de Wyscout (para admin)"""
        self._wyscout_cache = None
        self._wyscout_cache_time = None
        logging.info("🗑️ Cache de Wyscout limpiado")