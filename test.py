import sqlite3
import logging
from datetime import datetime
from models.jugador_model import JugadorModel
from pathlib import Path

# CONFIGURACIÓN
DB_PATH = "data/jugadores.db"
NOMBRE = "Julián Álvarez"
EQUIPO = "Atlético"
URL_BESOC = "https://es.besoccer.com/jugador/j-alvarez-772644"
FAKE_SCOUT = "test_user"
FAKE_NOTA = 7.5
FAKE_POSICION = "Delantero"
FAKE_FECHA = datetime.now().strftime("%Y-%m-%d")

# INICIALIZAR MODELO
jm = JugadorModel(db_path=DB_PATH)

# 1. BORRAR SI YA EXISTE
def borrar_jugador():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM jugadores_observados WHERE nombre_completo = ? AND equipo = ?", (NOMBRE, EQUIPO))
    conn.commit()
    conn.close()
    print(f"🗑️ Jugador anterior '{NOMBRE}' borrado de jugadores_observados.")

# 2. CARGAR DATOS DE BESOCCER (simulado o real)
def simular_datos_besoccer():
    return {
        "nombre_completo": NOMBRE,
        "jugador": NOMBRE,
        "equipo": EQUIPO,
        "posicion_principal": FAKE_POSICION,
        "posicion_secundaria": "Mediapunta",
        "numero_camiseta": 19,
        "edad": 25,
        "nacionalidad": "ARG",
        "liga": "Primera División",
        "pie_dominante": "Pie derecho",
        "altura": 170,
        "peso": 68,
        "valor_mercado": "92.02 M€",
        "elo_besoccer": 92,
        "imagen_url": "https://cdn.resfu.com/img_data/players/medium/772644.jpg?size=60x&lossy=1",
        "escudo_equipo": "https://cdn.resfu.com/img_data/equipos/369.png?size=60x&lossy=1",
        "url_besoccer": URL_BESOC
    }

# 3. GUARDAR EN LA BD PERSONAL
def guardar_en_bd_personal(datos):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO jugadores_observados (
                jugador, nombre_completo, equipo, posicion_principal, 
                posicion_secundaria, numero_camiseta, edad, nacionalidad, liga, 
                pie_dominante, altura, peso, valor_mercado, elo_besoccer,
                imagen_url, escudo_equipo, veces_observado, estado, nota_general,
                nota_promedio, mejor_nota, peor_nota, total_informes, 
                ultima_fecha_visto, scout_agregado, url_besoccer
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datos["jugador"], datos["nombre_completo"], datos["equipo"],
            datos["posicion_principal"], datos["posicion_secundaria"], datos["numero_camiseta"],
            datos["edad"], datos["nacionalidad"], datos["liga"],
            datos["pie_dominante"], datos["altura"], datos["peso"], datos["valor_mercado"],
            datos["elo_besoccer"], datos["imagen_url"], datos["escudo_equipo"],
            1, "Evaluado", FAKE_NOTA, FAKE_NOTA, FAKE_NOTA, FAKE_NOTA, 1,
            FAKE_FECHA, FAKE_SCOUT, datos["url_besoccer"]
        ))
        conn.commit()
        print("✅ Jugador guardado correctamente en jugadores_observados.")
    except Exception as e:
        print("❌ Error guardando jugador:", e)
    finally:
        conn.close()

# 4. VERIFICAR QUE ESTÁ GUARDADO
def verificar_guardado():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jugadores_observados WHERE nombre_completo = ? AND equipo = ?", (NOMBRE, EQUIPO))
    resultado = cursor.fetchone()
    conn.close()

    if resultado:
        print("✅ Verificación completada: jugador está guardado.")
    else:
        print("❌ Verificación fallida: jugador NO está en la tabla.")

# === FLUJO COMPLETO ===
if __name__ == "__main__":
    print("🚀 INICIO DEL TEST")
    borrar_jugador()
    datos = simular_datos_besoccer()
    guardar_en_bd_personal(datos)
    verificar_guardado()
    print("✅ TEST FINALIZADO")
