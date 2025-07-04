# check_jugadores_db.py
# Verificar el contenido real de la BD de jugadores

import sqlite3
import pandas as pd

def check_jugadores_db():
    """Verifica qué hay realmente en la BD de jugadores"""
    
    print("🔍 VERIFICANDO BD DE JUGADORES")
    print("=" * 60)
    
    conn = sqlite3.connect("data/jugadores.db")
    
    # 1. Contar total
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM jugadores")
    total = cursor.fetchone()[0]
    print(f"\n1️⃣ TOTAL JUGADORES EN BD: {total}")
    
    # 2. Ver todos los jugadores
    print("\n2️⃣ JUGADORES EN LA BD:")
    df = pd.read_sql_query("""
        SELECT id, nombre, apellidos, nombre_completo, equipo, 
               veces_observado, origen_datos, fecha_actualizacion
        FROM jugadores
        ORDER BY fecha_actualizacion DESC
    """, conn)
    
    if not df.empty:
        print(df.to_string())
    else:
        print("❌ No hay jugadores en la BD")
    
    # 3. Verificar si hay jugadores sin nombre_completo
    cursor.execute("SELECT COUNT(*) FROM jugadores WHERE nombre_completo IS NULL")
    sin_nombre = cursor.fetchone()[0]
    print(f"\n3️⃣ JUGADORES SIN nombre_completo: {sin_nombre}")
    
    # 4. Ver informes y sus jugadores
    print("\n4️⃣ RELACIÓN INFORMES -> JUGADORES:")
    conn_partidos = sqlite3.connect("data/partidos.db")
    
    df_informes = pd.read_sql_query("""
        SELECT id, jugador_nombre, equipo, jugador_bd_id, procesado_wyscout
        FROM informes_scouting
        ORDER BY id DESC
    """, conn_partidos)
    
    print(df_informes.to_string())
    
    # 5. Sincronización pendiente
    print("\n5️⃣ SINCRONIZACIÓN PENDIENTE:")
    
    # Informes sin jugador_bd_id
    cursor_p = conn_partidos.cursor()
    cursor_p.execute("""
        SELECT COUNT(*) FROM informes_scouting 
        WHERE jugador_bd_id IS NULL OR jugador_bd_id = 0
    """)
    sin_vincular = cursor_p.fetchone()[0]
    print(f"Informes sin vincular a BD personal: {sin_vincular}")
    
    conn.close()
    conn_partidos.close()
    
    print("\n" + "=" * 60)
    
    if sin_vincular > 0:
        print("⚠️ HAY INFORMES SIN VINCULAR A LA BD PERSONAL")
        print("Ejecuta: python reset_and_sync_db.py")

if __name__ == "__main__":
    check_jugadores_db()