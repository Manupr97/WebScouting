# utils/wyscout_data_extractor_personalizado.py

import pandas as pd
import numpy as np
from difflib import SequenceMatcher
import os
import unicodedata

class WyscoutExtractorPersonalizado:
    def __init__(self):
        """Inicializa el extractor con los datos de Wyscout"""
        self.df = None
        self.cargar_datos()
    
    def cargar_datos(self):
        """Carga los datos desde el Excel de Wyscout"""
        try:
            rutas_posibles = [
                'data/wyscout_LaLiga_limpio.xlsx',
                '../data/wyscout_LaLiga_limpio.xlsx',
                '../../data/wyscout_LaLiga_limpio.xlsx',
                os.path.join(os.path.dirname(__file__), '../data/wyscout_LaLiga_limpio.xlsx')
            ]
            
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    self.df = pd.read_excel(ruta)
                    # Solo log si es la primera vez
                    if not hasattr(self, '_datos_cargados'):
                        print(f"✅ Datos Wyscout cargados: {len(self.df)} jugadores")
                        self._datos_cargados = True
                    return
            
            print("❌ No se encontró el archivo de datos Wyscout")
            self.df = pd.DataFrame()
            
        except Exception as e:
            print(f"❌ Error cargando datos Wyscout: {e}")
            self.df = pd.DataFrame()
    
    def normalizar_texto(self, texto):
        """Normaliza texto para comparación (quita acentos, minúsculas, etc)"""
        if not texto:
            return ""
        
        # Convertir a string si no lo es
        texto = str(texto)
        
        # Quitar acentos
        texto = ''.join(c for c in unicodedata.normalize('NFD', texto) 
                       if unicodedata.category(c) != 'Mn')
        
        # Minúsculas y quitar espacios extra
        texto = texto.lower().strip()
        
        # Quitar caracteres especiales comunes
        texto = texto.replace("'", "").replace("-", " ").replace(".", "")
        
        return texto
    
    def calcular_similitud_compuesta(self, nombre1, equipo1, nombre2, equipo2):
        """
        Calcula similitud considerando TANTO nombre COMO equipo
        Retorna un score entre 0 y 1
        """
        # Normalizar todos los textos
        nombre1_norm = self.normalizar_texto(nombre1)
        nombre2_norm = self.normalizar_texto(nombre2)
        equipo1_norm = self.normalizar_texto(equipo1)
        equipo2_norm = self.normalizar_texto(equipo2)
        
        # Similitud del nombre (peso 70%)
        sim_nombre = SequenceMatcher(None, nombre1_norm, nombre2_norm).ratio()
        
        # Similitud del equipo (peso 30%)
        sim_equipo = SequenceMatcher(None, equipo1_norm, equipo2_norm).ratio()
        
        # Si los equipos no coinciden en absoluto, penalizar fuertemente
        if sim_equipo < 0.5:
            return sim_nombre * 0.3  # Reducir drásticamente el score
        
        # Score compuesto
        score_total = (sim_nombre * 0.7) + (sim_equipo * 0.3)
        
        return score_total
    
    def generar_variaciones_nombre(self, nombre):
        """Genera variaciones comunes del nombre"""
        variaciones = [nombre]
        partes = nombre.split()
        
        if len(partes) >= 2:
            # Apellido, Nombre
            variaciones.append(f"{partes[-1]}, {' '.join(partes[:-1])}")
            
            # Inicial + Apellido
            variaciones.append(f"{partes[0][0]}. {partes[-1]}")
            
            # Solo apellido (si es único)
            if len(partes[-1]) > 5:  # Apellido largo probablemente único
                variaciones.append(partes[-1])
        
        return variaciones

    def generar_variaciones_equipo(self, equipo):
        """Genera variaciones comunes del equipo"""
        if not equipo:
            return []
        
        variaciones = [equipo]
        
        # Diccionario de equivalencias comunes
        equivalencias = {
            'Real Madrid': ['R. Madrid', 'Real Madrid CF', 'Real Madrid C.F.', 'Madrid'],
            'FC Barcelona': ['Barcelona', 'Barça', 'F.C. Barcelona', 'Bar'],
            'Atlético Madrid': ['Atlético', 'Atl. Madrid', 'Atletico Madrid', 'ATM'],
            'Real Sociedad': ['R. Sociedad', 'Real Soc.', 'La Real'],
            'Athletic Bilbao': ['Athletic', 'Ath. Bilbao', 'Athletic Club'],
            'Villarreal': ['Villarreal CF', 'Villareal'],  # Error común
            'Real Betis': ['Betis', 'R. Betis', 'Real Betis Balompié'],
            'Valencia': ['Valencia CF', 'Valencia C.F.', 'VCF'],
            'Sevilla': ['Sevilla FC', 'Sevilla F.C.', 'SFC'],
            'Rayo Vallecano': ['Rayo', 'R. Vallecano']
        }
        
        # Buscar si el equipo está en nuestras equivalencias
        equipo_norm = self.normalizar_texto(equipo)
        for equipo_base, alternativas in equivalencias.items():
            if equipo_norm in self.normalizar_texto(equipo_base) or any(equipo_norm in self.normalizar_texto(alt) for alt in alternativas):
                variaciones.extend([equipo_base] + alternativas)
                break
        
        # Agregar variaciones genéricas
        if 'FC' in equipo or 'CF' in equipo:
            variaciones.append(equipo.replace('FC', '').replace('CF', '').strip())
        
        return list(set(variaciones))  # Eliminar duplicados

    def calcular_similitud_iniciales(self, nombre1, nombre2):
        """Calcula similitud considerando formato inicial + apellido"""
        partes1 = nombre1.split()
        partes2 = nombre2.split()
        
        if not partes1 or not partes2:
            return 0
        
        # Caso: "C. Ronaldo" vs "Cristiano Ronaldo"
        if len(partes1[0]) <= 2 and partes1[0].endswith('.'):
            inicial1 = partes1[0][0].lower()
            apellido1 = partes1[-1].lower() if len(partes1) > 1 else ""
            
            if partes2[0][0].lower() == inicial1 and partes2[-1].lower() == apellido1:
                return 0.9
        
        # Caso inverso
        if len(partes2[0]) <= 2 and partes2[0].endswith('.'):
            inicial2 = partes2[0][0].lower()
            apellido2 = partes2[-1].lower() if len(partes2) > 1 else ""
            
            if partes1[0][0].lower() == inicial2 and partes1[-1].lower() == apellido2:
                return 0.9
        
        return 0

    def calcular_similitud_tokens(self, nombre1, nombre2):
        """Calcula similitud basada en tokens compartidos"""
        tokens1 = set(self.normalizar_texto(nombre1).split())
        tokens2 = set(self.normalizar_texto(nombre2).split())
        
        if not tokens1 or not tokens2:
            return 0
        
        # Intersección de tokens
        comunes = tokens1.intersection(tokens2)
        union = tokens1.union(tokens2)
        
        return len(comunes) / len(union) if union else 0
    
    def buscar_jugador_mejorado(self, nombre_buscar, equipo_buscar=None, umbral_minimo=0.75):
        """
        Búsqueda mejorada con múltiples estrategias
        """
        if self.df is None or self.df.empty:
            return None
        
        # Preparar variaciones del nombre a buscar
        variaciones_nombre = self.generar_variaciones_nombre(nombre_buscar)
        variaciones_equipo = self.generar_variaciones_equipo(equipo_buscar) if equipo_buscar else []
        
        mejor_match = None
        mejor_score = 0
        detalles_match = {}
        
        # Columnas del dataset
        col_nombre = 'jugador' if 'jugador' in self.df.columns else self.df.columns[0]
        col_equipo = 'equipo_durante_el_período_seleccionado'
        
        for idx, row in self.df.iterrows():
            nombre_wyscout = str(row[col_nombre])
            equipo_wyscout = str(row[col_equipo]) if col_equipo in self.df.columns else ""
            
            # Calcular scores con diferentes métodos
            scores = []
            
            # 1. Match exacto normalizado
            score_exacto = self.calcular_similitud_exacta(nombre_buscar, nombre_wyscout)
            if score_exacto > 0.95:
                scores.append(('exacto', score_exacto, 1.5))  # Peso extra para match exacto
            
            # 2. Match por iniciales + apellido
            score_iniciales = self.calcular_similitud_iniciales(nombre_buscar, nombre_wyscout)
            if score_iniciales > 0.8:
                scores.append(('iniciales', score_iniciales, 1.2))
            
            # 3. Match por tokens (palabras individuales)
            score_tokens = self.calcular_similitud_tokens(nombre_buscar, nombre_wyscout)
            if score_tokens > 0.7:
                scores.append(('tokens', score_tokens, 1.0))
            
            # 4. Match por similitud difusa
            score_difuso = SequenceMatcher(None, 
                                        self.normalizar_texto(nombre_buscar), 
                                        self.normalizar_texto(nombre_wyscout)).ratio()
            scores.append(('difuso', score_difuso, 0.8))
            
            # Calcular score final del nombre
            if scores:
                score_nombre = max(s[1] * s[2] for s in scores)
                metodo_usado = next(s[0] for s in scores if s[1] * s[2] == score_nombre)
            else:
                score_nombre = 0
                metodo_usado = 'ninguno'
            
            # Score del equipo
            score_equipo = 0
            if equipo_buscar and equipo_wyscout:
                # Intentar con todas las variaciones del equipo
                for var_equipo in variaciones_equipo:
                    sim = SequenceMatcher(None, 
                                        self.normalizar_texto(var_equipo), 
                                        self.normalizar_texto(equipo_wyscout)).ratio()
                    score_equipo = max(score_equipo, sim)
            
            # Score compuesto
            if equipo_buscar:
                # Si tenemos equipo, es importante que coincida
                if score_equipo < 0.5:
                    score_total = score_nombre * 0.3  # Penalización fuerte
                else:
                    score_total = (score_nombre * 0.7) + (score_equipo * 0.3)
            else:
                # Sin equipo, solo usamos el nombre
                score_total = score_nombre
            
            # Actualizar mejor match
            if score_total > mejor_score:
                mejor_score = score_total
                mejor_match = row
                detalles_match = {
                    'metodo': metodo_usado,
                    'score_nombre': score_nombre,
                    'score_equipo': score_equipo,
                    'nombre_encontrado': nombre_wyscout,
                    'equipo_encontrado': equipo_wyscout
                }
        
        # Validar resultado
        if mejor_score >= umbral_minimo:
            print(f"✅ Match encontrado: {detalles_match['nombre_encontrado']}")
            print(f"   Método: {detalles_match['metodo']}")
            print(f"   Score total: {mejor_score:.3f}")
            return mejor_match
        else:
            print(f"❌ No se encontró match suficiente. Mejor score: {mejor_score:.3f}")
            if mejor_score > 0.5:
                print(f"   Candidato: {detalles_match.get('nombre_encontrado', 'N/A')}")
            return None
    
    def obtener_datos_completos_jugador(self, nombre_jugador, equipo_jugador=None):
        """
        Obtiene datos completos del jugador con validación estricta
        """
        # Buscar con umbral alto
        jugador = self.buscar_jugador_mejorado(nombre_jugador, equipo_jugador, umbral_minimo=0.85)
        
        if jugador is None:
            return None
        
        # Extraer métricas relevantes
        datos = {
            'nombre': jugador.get('jugador', nombre_jugador),
            'equipo': jugador.get('equipo_durante_el_período_seleccionado', equipo_jugador),
            'posicion': jugador.get('pos_principal', 'N/A'),
            'edad': jugador.get('edad', 'N/A'),
            'partidos_jugados': jugador.get('partidos_jugados', 0),
            'minutos_jugados': jugador.get('minutos_jugados', 0),
            
            # Métricas para radar
            'precision_pases': jugador.get('precisión_de_pases,_%', 75),
            'duelos_ganados_pct': jugador.get('duelos_ganados,_%', 50),
            'duelos_aereos_pct': jugador.get('duelos_aéreos_ganados,_%', 50),
            'goles': jugador.get('goles', 0) / max(jugador.get('partidos_jugados', 1), 1),  # Por partido
            'asistencias': jugador.get('asistencias', 0) / max(jugador.get('partidos_jugados', 1), 1),  # Por partido
            'xg': jugador.get('xg', 0) / max(jugador.get('partidos_jugados', 1), 1),  # Por partido
            'regates_completados': jugador.get('regates_completados_por_90', jugador.get('regates_completados', 0)),
            'interceptaciones': jugador.get('intercepciones_por_90', jugador.get('intercepciones', 0))
        }
        
        print(f"📊 Datos extraídos para radar:")
        for key in ['precision_pases', 'duelos_ganados_pct', 'duelos_aereos_pct', 'goles', 'asistencias', 'xg', 'regates_completados', 'interceptaciones']:
            print(f"   • {key}: {datos[key]}")
        
        return datos
    
    def validar_jugador_equipo(self, nombre_jugador, equipo_jugador):
        """
        Valida si un jugador pertenece a un equipo específico
        """
        jugador = self.buscar_jugador_mejorado(nombre_jugador, equipo_jugador, umbral_minimo=0.9)
        return jugador is not None