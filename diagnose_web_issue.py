# diagnose_web_issue.py
# Diagnóstico específico del problema web vs script

import sqlite3
import streamlit as st
from datetime import datetime

def diagnose_web_issue():
    """Diagnóstico del problema en la aplicación web"""
    
    print("🔍 DIAGNÓSTICO WEB vs SCRIPT")
    print("=" * 60)
    
    # 1. Verificar el usuario actual en session_state
    print("\n1️⃣ VERIFICANDO SESSION_STATE:")
    
    # Simular lo que debería haber en session_state
    print("Simulando session_state después de login:")
    print("  - authenticated: True")
    print("  - usuario: 'admin'")
    print("  - nombre: 'Administrador'")
    print("  - rol: 'admin'")
    
    # 2. Verificar la BD después del reset
    conn = sqlite3.connect("data/partidos.db")
    cursor = conn.cursor()
    
    print("\n2️⃣ ESTADO DE LA BD DESPUÉS DEL RESET:")
    
    # Contar partidos
    cursor.execute("SELECT COUNT(*) FROM partidos")
    num_partidos = cursor.fetchone()[0]
    print(f"  Partidos: {num_partidos}")
    
    # Contar informes
    cursor.execute("SELECT COUNT(*) FROM informes_scouting")
    num_informes = cursor.fetchone()[0]
    print(f"  Informes: {num_informes}")
    
    # Ver últimos informes si hay
    if num_informes > 0:
        print("\n  Últimos informes:")
        cursor.execute("""
            SELECT id, jugador_nombre, scout_usuario, fecha_creacion 
            FROM informes_scouting 
            ORDER BY id DESC LIMIT 5
        """)
        for inf in cursor.fetchall():
            print(f"    ID: {inf[0]}, Jugador: {inf[1]}, Scout: {inf[2]}, Fecha: {inf[3]}")
    
    # 3. Verificar el método get_current_user
    print("\n3️⃣ VERIFICANDO get_current_user():")
    
    # Verificar qué retorna el método en login.py
    print("""
    El método get_current_user() debe retornar:
    {
        'usuario': 'admin',      # <-- ESTE ES CRÍTICO
        'nombre': 'Administrador',
        'rol': 'admin'
    }
    """)
    
    # 4. Posibles problemas
    print("\n4️⃣ POSIBLES PROBLEMAS:")
    print("  ❓ current_user['usuario'] podría ser None")
    print("  ❓ st.session_state.usuario no se está guardando en login")
    print("  ❓ El formulario no está llamando a crear_informe_scouting")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("SOLUCIONES:")
    print("1. Añadir prints de debug en Centro de Scouting")
    print("2. Verificar que current_user no es None")
    print("3. Añadir logging al guardar informe")

if __name__ == "__main__":
    diagnose_web_issue()