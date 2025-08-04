import sqlite3

conn = sqlite3.connect("data/jugadores.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS jugadores_observados (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jugador TEXT,
        nombre_completo TEXT,
        equipo TEXT,
        posicion TEXT,
        posicion_principal TEXT,
        posicion_secundaria TEXT,
        numero_camiseta INTEGER,
        edad INTEGER,
        nacionalidad TEXT,
        liga TEXT,
        pie_dominante TEXT,
        altura INTEGER,
        peso INTEGER,
        valor_mercado TEXT,
        elo_besoccer INTEGER,
        imagen_url TEXT,
        escudo_equipo TEXT,
        veces_observado INTEGER DEFAULT 1,
        estado TEXT DEFAULT 'Evaluado',
        nota_general REAL,
        nota_promedio REAL,
        mejor_nota REAL,
        peor_nota REAL,
        total_informes INTEGER,
        ultima_fecha_visto DATE,
        scout_agregado TEXT,
        url_besoccer TEXT
    )
''')

conn.commit()
conn.close()

print("✅ Tabla jugadores_observados creada (si no existía)")
