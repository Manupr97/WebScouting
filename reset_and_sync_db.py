# reset_and_sync_db.py
# Script para sincronizar la BD personal con los informes existentes

import sqlite3
import pandas as pd
from datetime import datetime

def reset_and_sync():
    """Resetea la BD personal y la sincroniza con los informes existentes"""
    
    print("🔄 SINCRONIZACIÓN DE BASES DE DATOS")
    print("=" * 60)
    
    # Confirmar
    respuesta = input("\n⚠️ Esto sincronizará la BD personal con todos los informes.\n¿Continuar? (s/n): ")
    if respuesta.lower() != 's':
        print("Operación cancelada")
        return
    
    # Conectar a ambas BDs
    conn_jugadores = sqlite3.connect("data/jugadores.db")
    conn_partidos = sqlite3.connect("data/partidos.db")
    
    cursor_j = conn_jugadores.cursor()
    cursor_p = conn_partidos.cursor()
    
    print("\n1️⃣ EXTRAYENDO JUGADORES DE INFORMES...")
    
    # Obtener todos los jugadores únicos de los informes
    cursor_p.execute("""
        SELECT DISTINCT 
            jugador_nombre,
            equipo,
            posicion,
            COUNT(*) as veces_observado,
            AVG(nota_general) as nota_promedio,
            MAX(fecha_creacion) as ultima_observacion,
            MIN(fecha_creacion) as primera_observacion
        FROM informes_scouting
        WHERE jugador_nombre IS NOT NULL AND jugador_nombre != ''
        GROUP BY jugador_nombre, equipo
        ORDER BY jugador_nombre
    """)
    
    jugadores = cursor_p.fetchall()
    print(f"📊 Encontrados {len(jugadores)} jugadores únicos en informes")
    
    print("\n2️⃣ SINCRONIZANDO CON BD PERSONAL...")
    
    contador_nuevos = 0
    contador_actualizados = 0
    
    for jugador in jugadores:
        nombre_completo = jugador[0]
        equipo = jugador[1]
        posicion = jugador[2] or 'N/A'
        veces_observado = jugador[3]
        nota_promedio = jugador[4]
        ultima_obs = jugador[5]
        primera_obs = jugador[6]
        
        # Verificar si ya existe
        cursor_j.execute("""
            SELECT id, veces_observado FROM jugadores 
            WHERE nombre_completo = ? AND equipo = ?
        """, (nombre_completo, equipo))
        
        jugador_existente = cursor_j.fetchone()
        
        if jugador_existente:
            # Actualizar existente
            jugador_id = jugador_existente[0]
            cursor_j.execute("""
                UPDATE jugadores SET 
                    veces_observado = ?,
                    ultimo_informe_fecha = ?,
                    fecha_actualizacion = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (veces_observado, ultima_obs, jugador_id))
            contador_actualizados += 1
            print(f"  📝 Actualizado: {nombre_completo} ({equipo}) - {veces_observado} observaciones")
        else:
            # Crear nuevo
            # Separar nombre y apellidos
            partes = nombre_completo.split(' ', 1)
            nombre = partes[0] if partes else nombre_completo
            apellidos = partes[1] if len(partes) > 1 else ''
            
            cursor_j.execute("""
                INSERT INTO jugadores (
                    nombre, apellidos, nombre_completo, equipo, posicion,
                    veces_observado, origen_datos, confianza_match,
                    primer_informe_fecha, ultimo_informe_fecha,
                    fecha_actualizacion
                ) VALUES (?, ?, ?, ?, ?, ?, 'informe_sync', 0, ?, ?, CURRENT_TIMESTAMP)
            """, (
                nombre, apellidos, nombre_completo, equipo, posicion,
                veces_observado, primera_obs, ultima_obs
            ))
            
            jugador_id = cursor_j.lastrowid
            contador_nuevos += 1
            print(f"  ✅ Nuevo: {nombre_completo} ({equipo}) - {veces_observado} observaciones")
        
        # Actualizar todos los informes de este jugador con el ID
        cursor_p.execute("""
            UPDATE informes_scouting 
            SET jugador_bd_id = ?
            WHERE jugador_nombre = ? AND equipo = ? AND jugador_bd_id IS NULL
        """, (jugador_id, nombre_completo, equipo))
    
    # Commit de ambas bases
    conn_jugadores.commit()
    conn_partidos.commit()
    
    print(f"\n✅ SINCRONIZACIÓN COMPLETADA:")
    print(f"  - {contador_nuevos} jugadores nuevos añadidos")
    print(f"  - {contador_actualizados} jugadores actualizados")
    
    # 3. VERIFICACIÓN FINAL
    print("\n3️⃣ VERIFICACIÓN FINAL:")
    
    # Contar totales
    cursor_j.execute("SELECT COUNT(*) FROM jugadores")
    total_jugadores = cursor_j.fetchone()[0]
    
    cursor_p.execute("SELECT COUNT(*) FROM informes_scouting")
    total_informes = cursor_p.fetchone()[0]
    
    cursor_p.execute("SELECT COUNT(*) FROM informes_scouting WHERE jugador_bd_id IS NOT NULL")
    informes_vinculados = cursor_p.fetchone()[0]
    
    cursor_p.execute("SELECT COUNT(*) FROM informes_scouting WHERE jugador_bd_id IS NULL")
    informes_sin_vincular = cursor_p.fetchone()[0]
    
    print(f"📊 Total jugadores en BD personal: {total_jugadores}")
    print(f"📋 Total informes: {total_informes}")
    print(f"🔗 Informes con jugador vinculado: {informes_vinculados}")
    print(f"❌ Informes sin vincular: {informes_sin_vincular}")
    
    if informes_sin_vincular > 0:
        print("\n⚠️ INFORMES SIN VINCULAR:")
        cursor_p.execute("""
            SELECT id, jugador_nombre, equipo, fecha_creacion
            FROM informes_scouting 
            WHERE jugador_bd_id IS NULL
            LIMIT 10
        """)
        
        for informe in cursor_p.fetchall():
            print(f"  - ID: {informe[0]}, Jugador: {informe[1]} ({informe[2]})")
    
    # Mostrar algunos jugadores
    print("\n📌 JUGADORES EN BD PERSONAL (últimos 10):")
    cursor_j.execute("""
        SELECT nombre_completo, equipo, veces_observado 
        FROM jugadores 
        ORDER BY fecha_actualizacion DESC 
        LIMIT 10
    """)
    
    for i, (nombre, equipo, veces) in enumerate(cursor_j.fetchall(), 1):
        print(f"  {i}. {nombre} ({equipo}) - Observado {veces} veces")
    
    conn_jugadores.close()
    conn_partidos.close()
    
    print("\n" + "=" * 60)
    print("✅ PROCESO COMPLETADO")
    print("🔄 Reinicia Streamlit para ver los cambios")

if __name__ == "__main__":
    reset_and_sync()
    