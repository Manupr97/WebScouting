import pandas as pd
import streamlit as st
from pathlib import Path
import os
import time

# FUNCIÓN GLOBAL PARA CACHE DE STREAMLIT
@st.cache_data(ttl=3600)
def cargar_datos_wyscout(data_path):
    """Carga los datos del archivo XLSX - CACHEADO POR STREAMLIT"""
    try:
        if not os.path.exists(data_path):
            return pd.DataFrame(), {}
        
        # Cargar el archivo XLSX
        df = pd.read_excel(data_path)
        
        # Limpiar nombres de columnas
        df.columns = df.columns.str.strip()
        
        # Detectar columnas automáticamente
        column_patterns = {
            'player': ['player', 'name', 'nombre', 'jugador', 'full name', 'apellidos'],
            'team': ['team', 'club', 'equipo', 'squad'],
            'position': ['position', 'pos', 'posicion', 'posición', 'role'],
            'age': ['age', 'edad', 'años'],
            'goals': ['goals', 'goles', 'goal'],
            'assists': ['assists', 'asistencias', 'assist'],
            'minutes': ['minutes', 'minutos', 'min', 'minutes played'],
            'matches': ['matches', 'partidos', 'games', 'apps', 'appearances']
        }
        
        detected = {}
        df_columns_lower = [col.lower().strip() for col in df.columns]
        
        for key, patterns in column_patterns.items():
            for pattern in patterns:
                for i, col_lower in enumerate(df_columns_lower):
                    if pattern in col_lower:
                        detected[key] = df.columns[i]
                        break
                if key in detected:
                    break
        
        return df, detected
        
    except Exception as e:
        st.error(f"❌ Error al cargar el archivo: {str(e)}")
        return pd.DataFrame(), {}

class WyscoutModel:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Solo inicializar una vez
        if not WyscoutModel._initialized:
            self.data_path = Path("data/wyscout_LaLiga_limpio.xlsx")
            self._df = None
            self._detected_columns = {}
            self._column_mapping = {}
            WyscoutModel._initialized = True
    
    def load_data(self):
        """Carga los datos usando la función cacheada global"""
        # ESTO ES LO IMPORTANTE: Usar la función global cacheada
        self._df, self._detected_columns = cargar_datos_wyscout(str(self.data_path))
        return self._df, self._detected_columns
    
    def get_all_players(self):
        """Lee directamente del Excel cada vez"""
        return pd.read_excel('data\wyscout_LaLiga_limpio.xlsx')
    
    def get_detected_columns(self):
        """Obtiene el mapeo de columnas detectadas"""
        if not self._detected_columns:
            self.load_data()
        return self._detected_columns
    
    def get_column_name(self, standard_name):
        """Obtiene el nombre real de la columna basado en el nombre estándar"""
        detected = self.get_detected_columns()
        return detected.get(standard_name.lower(), standard_name)
    
    def get_filtered_players(self, filters=None):
        """Aplica filtros a los datos usando nombres de columnas detectados"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        
        if df.empty or filters is None:
            return df
        
        filtered_df = df.copy()
        
        # Filtro por equipo
        if filters.get('teams') and len(filters['teams']) > 0:
            team_col = detected_cols.get('team')
            if team_col and team_col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[team_col].isin(filters['teams'])]
        
        # Filtro por posición
        if filters.get('positions') and len(filters['positions']) > 0:
            position_col = detected_cols.get('position')
            if position_col and position_col in filtered_df.columns:
                filtered_df = filtered_df[filtered_df[position_col].isin(filters['positions'])]
        
        # Filtro por edad
        if filters.get('age_range'):
            age_col = detected_cols.get('age')
            if age_col and age_col in filtered_df.columns:
                min_age, max_age = filters['age_range']
                filtered_df = filtered_df[
                    (filtered_df[age_col] >= min_age) & 
                    (filtered_df[age_col] <= max_age)
                ]
        
        # Filtro por nombre
        if filters.get('player_name'):
            player_col = detected_cols.get('player')
            if player_col and player_col in filtered_df.columns:
                name_filter = filters['player_name'].lower()
                filtered_df = filtered_df[
                    filtered_df[player_col].str.lower().str.contains(name_filter, na=False)
                ]
        
        return filtered_df
    
    def get_unique_teams(self):
        """Obtiene lista única de equipos"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        team_col = detected_cols.get('team')
        
        if team_col and team_col in df.columns:
            return sorted(df[team_col].dropna().unique().tolist())
        return []
    
    def get_unique_positions(self):
        """Obtiene lista única de posiciones"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        position_col = detected_cols.get('position')
        
        if position_col and position_col in df.columns:
            return sorted(df[position_col].dropna().unique().tolist())
        return []
    
    def get_player_details(self, player_name):
        """Obtiene detalles de un jugador específico"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        player_col = detected_cols.get('player')
        
        if not player_col or player_col not in df.columns:
            return None
        
        player_data = df[df[player_col] == player_name]
        
        if not player_data.empty:
            return player_data.iloc[0].to_dict()
        return None
    
    def get_data_summary(self):
        """Obtiene resumen estadístico de los datos"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        
        if df.empty:
            return {}
        
        # Usar columnas detectadas o columnas disponibles
        team_col = detected_cols.get('team', 'Team')
        position_col = detected_cols.get('position', 'Position')
        age_col = detected_cols.get('age', 'Age')
        
        summary = {
            'total_players': len(df),
            'total_teams': len(df[team_col].unique()) if team_col in df.columns else 0,
            'total_positions': len(df[position_col].unique()) if position_col in df.columns else 0,
            'age_stats': {},
            'columns': list(df.columns),
            'detected_columns': detected_cols
        }
        
        # Calcular estadísticas de edad si la columna existe
        if age_col in df.columns and not df[age_col].isna().all():
            summary['age_stats'] = {
                'min': df[age_col].min(),
                'max': df[age_col].max(),
                'mean': round(df[age_col].mean(), 1)
            }
        
        return summary
    
    def search_players(self, query, max_results=10):
        """Busca jugadores por nombre"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        player_col = detected_cols.get('player')
        
        if df.empty or not query or not player_col or player_col not in df.columns:
            return df.head(max_results)
        
        # Búsqueda flexible por nombre
        mask = df[player_col].str.lower().str.contains(query.lower(), na=False)
        results = df[mask].head(max_results)
        
        return results
    
    def get_team_players(self, team_name):
        """Obtiene todos los jugadores de un equipo específico"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        team_col = detected_cols.get('team')
        
        if not team_col or team_col not in df.columns:
            return pd.DataFrame()
        
        return df[df[team_col] == team_name]
    
    def get_position_players(self, position):
        """Obtiene todos los jugadores de una posición específica"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        position_col = detected_cols.get('position')
        
        if not position_col or position_col not in df.columns:
            return pd.DataFrame()
        
        return df[df[position_col] == position]
    
    def get_available_stats_columns(self):
        """Obtiene las columnas de estadísticas disponibles"""
        df = self.get_all_players()
        detected_cols = self.get_detected_columns()
        
        # Excluir columnas básicas
        basic_cols = [detected_cols.get(key, key) for key in ['player', 'team', 'position', 'age']]
        basic_cols = [col for col in basic_cols if col in df.columns]
        
        # Obtener columnas de estadísticas
        stats_cols = [col for col in df.columns if col not in basic_cols]
        
        return stats_cols
    
    def force_refresh(self):
        """Fuerza una recarga del cache"""
        WyscoutModel._cache_timestamp = None
        self._df = None
        self._detected_columns = {}
        self.get_all_players()  # Esto recargará los datos
    
    def get_cache_info(self):
        """Retorna información sobre el estado del cache"""
        if WyscoutModel._cache_timestamp:
            elapsed = time.time() - WyscoutModel._cache_timestamp
            remaining = max(0, self._cache_duration - elapsed)
            return {
                'cached': True,
                'elapsed_seconds': elapsed,
                'remaining_seconds': remaining,
                'total_players': len(WyscoutModel._data_cache) if WyscoutModel._data_cache is not None else 0
            }
        return {
            'cached': False,
            'elapsed_seconds': 0,
            'remaining_seconds': 0,
            'total_players': 0
        }