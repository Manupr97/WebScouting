import sqlite3

# Ruta a tu base de datos
db_path = "data/jugadores.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Solo se ejecuta si no existe la columna
    cursor.execute("PRAGMA table_info(jugadores_observados)")
    columnas = [col[1] for col in cursor.fetchall()]
    
    if "fecha_observacion" not in columnas:
        cursor.execute("ALTER TABLE jugadores_observados ADD COLUMN fecha_observacion DATE")
        conn.commit()
        print("✅ Columna 'fecha_observacion' añadida")
    else:
        print("ℹ️ La columna 'fecha_observacion' ya existe")
except Exception as e:
    print(f"❌ Error: {e}")
finally:
    conn.close()
