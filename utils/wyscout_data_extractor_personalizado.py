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
            # Buscar el archivo en diferentes rutas posibles
            rutas_posibles = [
                'data/wyscout_LaLiga_limpio.xlsx',
                '../data/wyscout_LaLiga_limpio.xlsx',
                '../../data/wyscout_LaLiga_limpio.xlsx',
                os.path.join(os.path.dirname(__file__), '../data/wyscout_LaLiga_limpio.xlsx')
            ]
            
            for ruta in rutas_posibles:
                if os.path.exists(ruta):
                    self.df = pd.read_excel(ruta)
                    print(f"✅ Datos Wyscout cargados: {len(self.df)} jugadores con {len(self.df.columns)} métricas")
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
    
    def buscar_jugador_mejorado(self, nombre_buscar, equipo_buscar=None, umbral_minimo=0.85):
        """
        Busca jugador con matching mejorado de nombre + equipo
        
        Args:
            nombre_buscar: Nombre del jugador
            equipo_buscar: Equipo del jugador (opcional pero recomendado)
            umbral_minimo: Similitud mínima requerida (default 0.85)
        
        Returns:
            dict con datos del jugador o None si no hay match suficiente
        """
        if self.df is None or self.df.empty:
            print("❌ No hay datos de Wyscout cargados")
            return None
        
        print(f"🔍 Buscando '{nombre_buscar}' del '{equipo_buscar}' en base de datos Wyscout...")
        
        mejor_match = None
        mejor_score = 0
        
        # Columnas de nombre y equipo en el dataset
        col_nombre = 'jugador' if 'jugador' in self.df.columns else self.df.columns[0]
        col_equipo = 'equipo_durante_el_período_seleccionado' if 'equipo_durante_el_período_seleccionado' in self.df.columns else 'equipo'
        
        for idx, row in self.df.iterrows():
            nombre_wyscout = row[col_nombre]
            equipo_wyscout = row[col_equipo] if col_equipo in self.df.columns else None
            
            if equipo_buscar and equipo_wyscout:
                # Matching compuesto (nombre + equipo)
                score = self.calcular_similitud_compuesta(
                    nombre_buscar, equipo_buscar,
                    nombre_wyscout, equipo_wyscout
                )
            else:
                # Solo matching de nombre si no hay equipo
                score = SequenceMatcher(None, 
                                      self.normalizar_texto(nombre_buscar), 
                                      self.normalizar_texto(nombre_wyscout)).ratio()
            
            if score > mejor_score:
                mejor_score = score
                mejor_match = row
        
        # Validar si el match es suficientemente bueno
        if mejor_score >= umbral_minimo:
            print(f"✅ Jugador encontrado: {mejor_match[col_nombre]} ({mejor_match[col_equipo] if col_equipo in mejor_match else 'N/A'}) - Similitud: {mejor_score:.2f}")
            return mejor_match
        else:
            print(f"❌ No se encontró match suficiente. Mejor score: {mejor_score:.2f} < {umbral_minimo}")
            if mejor_match is not None and mejor_score > 0.5:
                print(f"   Mejor candidato descartado: {mejor_match[col_nombre]} ({mejor_match[col_equipo] if col_equipo in mejor_match else 'N/A'})")
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