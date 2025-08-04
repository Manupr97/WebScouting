import sqlite3
import os

DB_PATH = "data/jugadores.db"

# Columnas necesarias (nombre: tipo)
REQUIRED_COLUMNS = {
    "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
    "jugador": "TEXT",
    "nombre_completo": "TEXT",
    "equipo": "TEXT",
    "posicion": "TEXT",
    "posicion_principal": "TEXT",
    "posicion_secundaria": "TEXT",
    "numero_camiseta": "INTEGER",
    "edad": "INTEGER",
    "nacionalidad": "TEXT",
    "liga": "TEXT",
    "pie_dominante": "TEXT",
    "altura": "INTEGER",
    "peso": "INTEGER",
    "valor_mercado": "TEXT",
    "elo_besoccer": "INTEGER",
    "imagen_url": "TEXT",
    "escudo_equipo": "TEXT",
    "veces_observado": "INTEGER DEFAULT 1",
    "estado": "TEXT DEFAULT 'Evaluado'",
    "nota_general": "REAL",
    "nota_promedio": "REAL",
    "mejor_nota": "REAL",
    "peor_nota": "REAL",
    "total_informes": "INTEGER",
    "ultima_fecha_visto": "DATE",
    "scout_agregado": "TEXT",
    "url_besoccer": "TEXT",
    "datos_json": "TEXT",  # 💡 Usado para PDF
    "ultimo_partido_id": "TEXT",  # 🆕 Identificador último partido
    "metricas": "TEXT",
    "fecha_agregado": "DATE DEFAULT CURRENT_DATE"# 🧠 JSON con métricas estructuradas
}

def tabla_existe(conn, tabla):
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (tabla,))
    return cursor.fetchone() is not None

def get_columnas_actuales(conn, tabla):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({tabla})")
    return [col[1] for col in cursor.fetchall()]

def crear_tabla_jugadores_observados(conn):
    cursor = conn.cursor()
    columnas_sql = ",\n".join([f"{col} {tipo}" for col, tipo in REQUIRED_COLUMNS.items()])
    cursor.execute(f"CREATE TABLE jugadores_observados ({columnas_sql})")
    print("✅ Tabla 'jugadores_observados' creada correctamente.")

def añadir_columnas_faltantes(conn, columnas_faltantes):
    cursor = conn.cursor()
    for col in columnas_faltantes:
        tipo = REQUIRED_COLUMNS[col]
        try:
            cursor.execute(f"ALTER TABLE jugadores_observados ADD COLUMN {col} {tipo}")
            print(f"✅ Columna añadida: {col} ({tipo})")
        except Exception as e:
            print(f"❌ Error añadiendo columna '{col}': {e}")

def main():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)

    if not tabla_existe(conn, "jugadores_observados"):
        crear_tabla_jugadores_observados(conn)
    else:
        print("ℹ️ La tabla 'jugadores_observados' ya existe.")
        columnas_actuales = get_columnas_actuales(conn, "jugadores_observados")
        columnas_faltantes = [col for col in REQUIRED_COLUMNS if col not in columnas_actuales]

        if columnas_faltantes:
            print(f"⚠️ Columnas faltantes detectadas: {columnas_faltantes}")
            añadir_columnas_faltantes(conn, columnas_faltantes)
        else:
            print("✅ La tabla 'jugadores_observados' ya tiene todas las columnas necesarias.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    main()
