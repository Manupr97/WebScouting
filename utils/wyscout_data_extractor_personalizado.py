# utils/wyscout_data_extractor_personalizado.py

import pandas as pd
import os
import logging
from difflib import SequenceMatcher

class WyscoutExtractorPersonalizado:
    """
    Extractor especializado para tu archivo wyscout_LaLiga_limpio.xlsx
    """
    
    def __init__(self, xlsx_path="data/wyscout_LaLiga_limpio.xlsx"):
        self.xlsx_path = xlsx_path
        self.df_wyscout = None
        self.logger = logging.getLogger(__name__)
        self._cargar_datos()
    
    def _cargar_datos(self):
        """Carga los datos del archivo xlsx de Wyscout"""
        try:
            if os.path.exists(self.xlsx_path):
                self.df_wyscout = pd.read_excel(self.xlsx_path, sheet_name=0)
                print(f"✅ Datos Wyscout cargados: {len(self.df_wyscout)} jugadores con {len(self.df_wyscout.columns)} métricas")
            else:
                print(f"❌ No se encontró el archivo: {self.xlsx_path}")
                self.df_wyscout = pd.DataFrame()
        except Exception as e:
            print(f"❌ Error cargando datos Wyscout: {str(e)}")
            self.df_wyscout = pd.DataFrame()
    
    def buscar_jugador(self, nombre_jugador, equipo=None, threshold_similarity=0.6):
        """
        Busca un jugador en los datos de Wyscout con fuzzy matching
        """
        if self.df_wyscout.empty:
            print("❌ No hay datos cargados")
            return None
        
        try:
            def similarity(a, b):
                return SequenceMatcher(None, a.lower(), b.lower()).ratio()
            
            # Buscar coincidencias en la columna 'jugador'
            mejores_matches = []
            
            for idx, row in self.df_wyscout.iterrows():
                nombre_wyscout = str(row['jugador']).strip()
                sim_score = similarity(nombre_jugador, nombre_wyscout)
                
                # Si también tenemos equipo, considerarlo
                if equipo and pd.notna(row['equipo']):
                    equipo_wyscout = str(row['equipo']).strip()
                    equipo_sim = similarity(equipo, equipo_wyscout)
                    # Promedio ponderado: 70% nombre, 30% equipo
                    sim_score = (sim_score * 0.7) + (equipo_sim * 0.3)
                
                if sim_score >= threshold_similarity:
                    mejores_matches.append((idx, sim_score, row))
            
            # Ordenar por similitud y devolver el mejor
            if mejores_matches:
                mejores_matches.sort(key=lambda x: x[1], reverse=True)
                _, score, jugador_data = mejores_matches[0]
                
                print(f"✅ Jugador encontrado: {jugador_data['jugador']} ({jugador_data['equipo']}) - Similitud: {score:.2f}")
                return jugador_data
            else:
                print(f"❌ No se encontró '{nombre_jugador}' en datos Wyscout")
                
                # Sugerir nombres similares
                todos_nombres = self.df_wyscout['jugador'].tolist()
                from difflib import get_close_matches
                similares = get_close_matches(nombre_jugador, todos_nombres, n=3, cutoff=0.4)
                
                if similares:
                    print(f"💡 Nombres similares: {', '.join(similares)}")
                
                return None
                
        except Exception as e:
            print(f"❌ Error buscando jugador: {str(e)}")
            return None
    
    def extraer_datos_radar(self, jugador_data):
        """
        VERSIÓN CORREGIDA: Extrae datos específicos para el radar chart
        """
        if jugador_data is None:
            return None
        
        try:
            def safe_get(column_name, default=0):
                """Obtiene valor de forma segura"""
                valor = jugador_data.get(column_name, default)
                
                if pd.isna(valor) or valor == '-' or valor == '':
                    return default
                
                if isinstance(valor, bool):
                    return 1 if valor else 0
                
                if isinstance(valor, (int, float)):
                    if column_name.startswith('%') and valor <= 1:
                        return valor * 100
                    return float(valor)
                
                if isinstance(valor, str):
                    try:
                        return float(valor.replace('%', '').replace(',', ''))
                    except:
                        return default
                
                try:
                    return float(valor)
                except:
                    return default
            
            # Datos básicos
            partidos = safe_get('partidos_jugados', 1)
            minutos_totales = safe_get('min', 90)
            
            # Extraer métricas para radar
            datos_extraidos = {
                'precision_pases': safe_get('%precisión_pases,_', 75),
                'duelos_ganados_pct': safe_get('%duelos_ganados,_', 50),
                'duelos_aereos_pct': safe_get('%duelos_aéreos_ganados,_', 50),
                'goles': safe_get('goles/90', 0),
                'asistencias': safe_get('asistencias/90', 0),
                'xg': safe_get('xg/90', 0),
                'regates_completados': safe_get('regates/90', 0),
                'interceptaciones': safe_get('intercep/90', 0),
                'partidos_jugados': partidos,
                'minutos_jugados': minutos_totales,
                'equipo': str(jugador_data.get('equipo', 'N/A')),
                'posicion': str(jugador_data.get('pos_principal', 'N/A')),
                'edad': safe_get('edad', 0)
            }
            
            # Validar datos
            metricas_principales = ['precision_pases', 'duelos_ganados_pct', 'goles', 'asistencias']
            if all(datos_extraidos[m] == 0 for m in metricas_principales):
                print("⚠️ No se pudieron extraer datos válidos")
                return None
            
            print("📊 Datos extraídos para radar:")
            for key, value in datos_extraidos.items():
                if key in metricas_principales + ['duelos_aereos_pct', 'xg', 'regates_completados', 'interceptaciones']:
                    print(f"   • {key}: {value}")
            
            return datos_extraidos
            
        except Exception as e:
            print(f"❌ Error extrayendo datos: {str(e)}")
            return None
    
    def obtener_datos_completos_jugador(self, nombre_jugador, equipo=None):
        """
        Método principal: busca jugador y extrae datos para radar
        """
        print(f"🔍 Buscando '{nombre_jugador}' en base de datos Wyscout...")
        
        # Buscar jugador
        jugador_data = self.buscar_jugador(nombre_jugador, equipo)
        
        if jugador_data is None:
            return None
        
        # Extraer datos para radar
        datos_radar = self.extraer_datos_radar(jugador_data)
        
        return datos_radar
    
    def obtener_jugadores_por_equipo(self, equipo):
        """
        Obtiene todos los jugadores de un equipo específico
        """
        if self.df_wyscout.empty:
            return []
        
        try:
            jugadores = self.df_wyscout[self.df_wyscout['equipo'].str.contains(equipo, case=False, na=False)]
            return jugadores['jugador'].tolist()
        except Exception as e:
            print(f"❌ Error obteniendo jugadores del equipo {equipo}: {str(e)}")
            return []
    
    def obtener_top_jugadores_por_metrica(self, metrica, top_n=10):
        """
        Obtiene los mejores jugadores según una métrica específica
        """
        if self.df_wyscout.empty:
            return []
        
        try:
            # Mapeo de métricas comunes
            metrica_mapping = {
                'goles': 'goles/90',
                'asistencias': 'asistencias/90',
                'pases': '%precisión_pases,_',
                'regates': 'regates/90',
                'duelos': '%duelos_ganados,_'
            }
            
            col_name = metrica_mapping.get(metrica, metrica)
            
            if col_name in self.df_wyscout.columns:
                top_players = self.df_wyscout.nlargest(top_n, col_name)
                return [(row['jugador'], row['equipo'], row[col_name]) for _, row in top_players.iterrows()]
            else:
                print(f"❌ Métrica '{metrica}' no encontrada")
                return []
                
        except Exception as e:
            print(f"❌ Error obteniendo top jugadores: {str(e)}")
            return []
    
    def debug_jugador_especifico(self, nombre_jugador):
        """
        Debug completo de un jugador específico
        """
        print(f"\n🔍 DEBUG COMPLETO PARA: {nombre_jugador}")
        print("=" * 50)
        
        jugador_data = self.buscar_jugador(nombre_jugador)
        
        if jugador_data is not None:
            print(f"✅ JUGADOR ENCONTRADO: {jugador_data['jugador']}")
            print(f"🏟️ Equipo: {jugador_data['equipo']}")
            print(f"📍 Posición: {jugador_data['pos_principal']}")
            print(f"👤 Edad: {jugador_data['edad']} años")
            print(f"⚽ Partidos: {jugador_data['partidos_jugados']}")
            print(f"⏱️ Minutos: {jugador_data['min']}")
            print(f"🥅 Goles/90: {jugador_data['goles/90']}")
            print(f"🎯 Asistencias/90: {jugador_data['asistencias/90']}")
            print(f"📊 Precisión pases: {jugador_data['%precisión_pases,_'] * 100:.1f}%")
            print(f"🤼 Duelos ganados: {jugador_data['%duelos_ganados,_'] * 100:.1f}%")
            
            # Extraer datos del radar
            datos_radar = self.extraer_datos_radar(jugador_data)
            if datos_radar:
                print(f"\n📊 DATOS PARA RADAR EXTRAÍDOS EXITOSAMENTE")
            else:
                print(f"\n❌ ERROR EXTRAYENDO DATOS PARA RADAR")
        
        return jugador_data