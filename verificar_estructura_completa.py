import sqlite3

# Conectar a la BD
conn = sqlite3.connect('data/partidos.db')
cursor = conn.cursor()

print("=== VERIFICACIÓN DE INFORMES ===\n")

# 1. Total de informes
cursor.execute("SELECT COUNT(*) FROM informes_scouting WHERE scout_usuario = 'admin'")
total = cursor.fetchone()[0]
print(f"Total informes de admin: {total}")

# 2. Ver partido_ids
print("\n--- Partido IDs en informes ---")
cursor.execute("SELECT DISTINCT partido_id FROM informes_scouting")
for row in cursor.fetchall():
    print(f"  - {row[0]}")

# 3. Ver partidos existentes
print("\n--- IDs en tabla partidos ---")
cursor.execute("SELECT id FROM partidos")
partidos = cursor.fetchall()
if partidos:
    for row in partidos:
        print(f"  - {row[0]}")
else:
    print("  ❌ Tabla partidos está vacía!")

# 4. Informes sin partido asociado
print("\n--- Informes SIN partido en tabla partidos ---")
cursor.execute('''
    SELECT i.id, i.jugador_nombre, i.equipo, i.partido_id 
    FROM informes_scouting i
    LEFT JOIN partidos p ON i.partido_id = p.id
    WHERE p.id IS NULL
''')
huerfanos = cursor.fetchall()
if huerfanos:
    for row in huerfanos:
        print(f"  ID: {row[0]} - {row[1]} ({row[2]}) - partido_id: {row[3]}")
else:
    print("  ✅ Todos los informes tienen partido asociado")

conn.close()