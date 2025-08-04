import sqlite3

conn = sqlite3.connect('data/jugadores.db')
cursor = conn.cursor()

# Añadir la columna url_besoccer si no existe
try:
    cursor.execute("ALTER TABLE jugadores_observados ADD COLUMN url_besoccer TEXT")
    print("✅ Columna 'url_besoccer' añadida correctamente")
except Exception as e:
    print(f"⚠️ Ya existía o error: {e}")

conn.commit()
conn.close()