# reset_databases.py
# Script para resetear las bases de datos con la estructura correcta

import os
import sqlite3
import shutil
from datetime import datetime

def backup_existing_databases():
    """Hacer backup de las BD existentes"""
    backup_folder = f"data/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_folder, exist_ok=True)
    
    files_to_backup = ['data/jugadores.db', 'data/partidos.db', 'data/usuarios.db']
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = os.path.join(backup_folder, os.path.basename(file_path))
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backup creado: {backup_path}")
    
    return backup_folder

def reset_jugadores_db():
    """Recrear jugadores.db con estructura correcta"""
    if os.path.exists('data/jugadores.db'):
        os.remove('data/jugadores.db')
    
    conn = sqlite3.connect('data/jugadores.db')
    cursor = conn.cursor()
    
    # Crear tabla de jugadores con estructura completa
    cursor.execute('''
        CREATE TABLE jugadores (
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
            
            -- Estadísticas avanzadas
            pases_completados INTEGER DEFAULT 0,
            pases_intentados INTEGER DEFAULT 0,
            precision_pases REAL DEFAULT 0,
            regates_completados INTEGER DEFAULT 0,
            regates_intentados INTEGER DEFAULT 0,
            duelos_aereos_ganados INTEGER DEFAULT 0,
            duelos_aereos_totales INTEGER DEFAULT 0,
            interceptaciones INTEGER DEFAULT 0,
            recuperaciones INTEGER DEFAULT 0,
            
            -- Información de scouting (NUEVAS COLUMNAS)
            veces_observado INTEGER DEFAULT 1,
            primer_informe_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ultimo_informe_fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            origen_datos TEXT DEFAULT 'wyscout',
            confianza_match REAL DEFAULT 100.0,
            
            -- Información adicional
            fecha_actualizacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            lesionado BOOLEAN DEFAULT 0,
            agente TEXT,
            contrato_hasta DATE
        )
    ''')
    
    # Crear tabla de historial de búsquedas
    cursor.execute('''
        CREATE TABLE busquedas_wyscout (
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
    print("✅ jugadores.db recreado con estructura correcta")

def reset_partidos_db():
    """Recrear partidos.db con estructura correcta"""
    if os.path.exists('data/partidos.db'):
        os.remove('data/partidos.db')
    
    conn = sqlite3.connect('data/partidos.db')
    cursor = conn.cursor()
    
    # Tabla de partidos
    cursor.execute('''
        CREATE TABLE partidos (
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
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de informes (ESTRUCTURA COMPLETA)
    cursor.execute('''
        CREATE TABLE informes_scouting (
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
            potencial TEXT,
            recomendacion TEXT,
            
            -- Observaciones
            fortalezas TEXT,
            debilidades TEXT,
            observaciones TEXT,
            minutos_observados INTEGER,
            
            -- Integración Wyscout (NUEVAS COLUMNAS)
            jugador_bd_id INTEGER,
            wyscout_match_confianza REAL,
            wyscout_algoritmo TEXT,
            procesado_wyscout BOOLEAN DEFAULT 0,
            
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partido_id) REFERENCES partidos (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ partidos.db recreado con estructura correcta")

def create_mock_partidos():
    """Crear partidos mock"""
    from models.partido_model import PartidoModel
    
    partido_model = PartidoModel()
    # Esto ejecutará crear_partidos_mock() automáticamente
    print("✅ Partidos mock creados")

def main():
    """Función principal"""
    print("🔄 Iniciando reset de bases de datos...")
    
    # 1. Hacer backup
    backup_folder = backup_existing_databases()
    print(f"📁 Backups guardados en: {backup_folder}")
    
    # 2. Recrear BD
    reset_jugadores_db()
    reset_partidos_db()
    
    # 3. Crear partidos mock
    create_mock_partidos()
    
    print("\n✅ ¡RESET COMPLETADO!")
    print("🎯 Ahora puedes usar las páginas sin errores.")
    print("📁 Backups guardados por seguridad.")

if __name__ == "__main__":
    main()