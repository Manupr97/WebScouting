import pandas as pd
import json
import os

# === 1. Función para normalizar nombres ===

def normalizar_nombre_metrica(nombre):
    """
    Convierte el nombre de columna Wyscout en un nombre legible
    Ej:
      'goles/90' → 'Goles cada 90 min'
      '%precisión_pases,_' → 'Pases precisos, %'
    """
    if not isinstance(nombre, str):
        return str(nombre)

    original = nombre

    nombre = nombre.lower().strip()

    # Reemplazos frecuentes
    nombre = nombre.replace('%', '')
    nombre = nombre.replace('_', ' ')
    nombre = nombre.replace(',', '')
    nombre = nombre.replace('/', ' cada ')
    nombre = nombre.replace('  ', ' ')

    if ' cada 90' in nombre:
        nombre = nombre.replace(' cada 90', ' cada 90 min')

    nombre = nombre.strip().capitalize()

    # Correcciones específicas
    correcciones = {
        'precision pases': 'Pases precisos, %',
        'duelos ganados ': 'Duelos ganados, %',
        'duelos aereos ganados ': 'Duelos aéreos ganados, %',
        'pases clave cada 90 min': 'Pases clave cada 90 min',
        'intercep cada 90 min': 'Intercepciones cada 90 min',
        'regates cada 90 min': 'Regates completados cada 90 min',
        'tiros a porteria cada 90 min': 'Tiros a portería cada 90 min',
        'xa cada 90 min': 'xA cada 90 min',
        'xg cada 90 min': 'xG cada 90 min',
        'goles cada 90 min': 'Goles cada 90 min',
        'asistencias cada 90 min': 'Asistencias cada 90 min',
        # Añade más si encuentras excepciones
    }

    nombre_corr = correcciones.get(nombre, nombre)

    # Debug opcional
    # print(f"→ {original} → {nombre_corr}")

    return nombre_corr

def generar_o_cargar_mapping_wyscout(excel_path, json_path):
    """
    Genera el mapping_wyscout desde el Excel si no existe el JSON.
    Si existe el JSON, lo carga.
    """
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            mapping = json.load(f)
    else:
        print("⚠️ Mapping JSON no encontrado. Generando nuevo mapping desde Excel...")
        df = pd.read_excel(excel_path, nrows=1)
        from utils.normalizacion import normalizar_nombre_metrica
        
        mapping = {}
        for col in df.columns:
            nombre_legible = normalizar_nombre_metrica(col)
            mapping[nombre_legible] = col

        # Guardar el JSON
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"✅ Mapping guardado en JSON: {json_path}")

    return mapping