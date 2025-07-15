import requests
import json

def test_ollama():
    """Prueba rápida para verificar que Ollama funciona"""
    
    print("🔍 Verificando conexión con Ollama...")
    
    # 1. Verificar que el servicio está activo
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✅ Ollama está funcionando")
            
            # Mostrar modelos instalados
            modelos = response.json()
            print("\n📦 Modelos disponibles:")
            for modelo in modelos.get('models', []):
                print(f"  - {modelo['name']} ({modelo['size'] // 1024 // 1024} MB)")
        else:
            print("❌ Ollama no responde correctamente")
            return False
    except Exception as e:
        print(f"❌ No se puede conectar con Ollama: {e}")
        print("\n💡 Soluciones:")
        print("  1. Verifica que Ollama esté instalado")
        print("  2. Reinicia tu computadora después de instalar")
        print("  3. Ejecuta 'ollama serve' en una terminal")
        return False
    
    # 2. Hacer una prueba de generación
    print("\n🤖 Probando generación de texto...")
    
    try:
        payload = {
            "model": "llama3.2",  # o "phi3:mini" si instalaste ese
            "prompt": "Resume en una frase: El fútbol es el deporte más popular del mundo.",
            "stream": False
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            respuesta = response.json()
            print(f"✅ Respuesta: {respuesta.get('response', 'Sin respuesta')}")
            return True
        else:
            print(f"❌ Error en la generación: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error al generar texto: {e}")
        return False

# Ejecutar test
if __name__ == "__main__":
    print("=== TEST DE OLLAMA ===\n")
    
    if test_ollama():
        print("\n🎉 ¡Todo funciona correctamente!")
        print("\nAhora puedes usar la integración de IA en tu sistema de scouting.")
    else:
        print("\n⚠️ Hay problemas con la configuración.")
        print("\nPasos para solucionar:")
        print("1. Asegúrate de haber instalado Ollama")
        print("2. Reinicia VS Code o tu computadora")
        print("3. Ejecuta 'ollama pull llama3.2' en la terminal")