# verify_code_version.py
# Verifica qué versión del código se está ejecutando

import os

def verify_code_version():
    """Verifica la versión del código en partido_model.py"""
    
    print("🔍 VERIFICANDO VERSIÓN DEL CÓDIGO")
    print("=" * 60)
    
    # Buscar el archivo
    partido_model_path = "models/partido_model.py"
    
    if not os.path.exists(partido_model_path):
        print(f"❌ No se encuentra {partido_model_path}")
        return
    
    # Leer el archivo
    with open(partido_model_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar indicadores clave
    print("\n1️⃣ VERIFICANDO CÓDIGO PARA JUGADORES NO ENCONTRADOS:")
    
    # Buscar el código nuevo
    if "datos_jugador_manual" in content:
        print("✅ Código NUEVO detectado (añade jugadores manuales)")
        
        # Buscar específicamente la parte que añade jugadores manuales
        if "manual_no_encontrado" in content:
            print("✅ Tiene la versión completa corregida")
        else:
            print("⚠️ Tiene código parcial, falta actualización completa")
    else:
        print("❌ Código ANTIGUO (NO añade jugadores cuando no encuentra en Wyscout)")
    
    # Verificar si tiene los logs correctos
    print("\n2️⃣ VERIFICANDO LOGS:")
    
    if "Jugador añadido manualmente a BD personal" in content:
        print("✅ Tiene logs de jugador manual")
    else:
        print("❌ No tiene logs de jugador manual")
    
    # Mostrar la sección relevante
    print("\n3️⃣ BUSCANDO SECCIÓN else DESPUÉS DE resultado_busqueda:")
    
    # Buscar el else después de "if resultado_busqueda:"
    start_index = content.find("if resultado_busqueda:")
    if start_index != -1:
        # Buscar el else correspondiente
        else_index = content.find("else:", start_index)
        if else_index != -1:
            # Mostrar las siguientes 20 líneas después del else
            lines = content[else_index:].split('\n')[:20]
            print("\nCódigo actual en el else:")
            print("-" * 40)
            for i, line in enumerate(lines):
                print(f"{i:2d}: {line}")
            print("-" * 40)
    
    print("\n4️⃣ RECOMENDACIÓN:")
    if "datos_jugador_manual" not in content:
        print("❌ NECESITAS actualizar partido_model.py con el código corregido")
        print("   Copia el código del artifact 'Método crear_informe_scouting completo corregido'")
    else:
        print("✅ El código parece estar actualizado")
        print("   Si aún no funciona, reinicia Streamlit para recargar los cambios")

if __name__ == "__main__":
    verify_code_version()