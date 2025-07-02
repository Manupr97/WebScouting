# ⚽ Scouting Pro - Sistema de Análisis Deportivo

## 📖 Descripción

Scouting Pro es una aplicación web profesional desarrollada con Streamlit para el análisis y evaluación de jugadores de fútbol. Diseñada específicamente para scouts, analistas deportivos, directores técnicos y profesionales del fútbol que necesitan tomar decisiones informadas sobre fichajes y rendimiento de jugadores.

## 🚀 Características Principales

### 🔍 Base de Datos de Jugadores
- Búsqueda avanzada con filtros múltiples (posición, liga, país, nombre)
- Información detallada de cada jugador (estadísticas, valor de mercado, datos personales)
- Filtros persistentes que se mantienen durante la navegación
- Vista detallada con métricas de rendimiento

### 📊 Visualizaciones Interactivas
- **Gráfico de Radar:** Análisis completo de habilidades individuales
- **Análisis de Goles vs Asistencias:** Contribución ofensiva comparativa
- **Distribución por Posición:** Estadísticas por rol de juego
- **Valor de Mercado por Liga:** Análisis económico del mercado
- **Precisión vs Edad:** Relación entre experiencia y técnica
- **Rendimiento por Equipo:** Análisis colectivo de plantillas

### 🔄 Comparador de Jugadores
- Comparación lado a lado de hasta 2 jugadores
- Múltiples modos de comparación (completa, ataque, defensa, pases)
- Gráficos de radar comparativos
- Análisis automático de ventajas y desventajas
- Métricas normalizadas para comparación justa

### 📄 Generación de Informes PDF
- **Informes Individuales:** Análisis completo de un jugador
- **Informes Comparativos:** Comparación detallada entre jugadores
- Formato profesional listo para presentaciones
- Recomendaciones automáticas basadas en estadísticas
- Análisis de fortalezas y debilidades

### 🔐 Sistema de Autenticación
- Login seguro con base de datos SQLite
- Gestión de sesiones
- Control de acceso a las funcionalidades

## 🛠️ Tecnologías Utilizadas

- **Frontend:** Streamlit
- **Base de Datos:** SQLite
- **Visualizaciones:** Plotly, Matplotlib, Seaborn
- **Generación PDF:** ReportLab
- **Procesamiento de Datos:** Pandas
- **Análisis Estadístico:** Statsmodels

## 🚀 Instalación y Configuración

### Requisitos Previos
- Python 3.7 o superior
- pip (gestor de paquetes de Python)

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone [URL_DEL_REPOSITORIO]
cd mi_app_scouting

2. **Crear entorno virtual:**

python -m venv venv_scouting

3. **Activar el entorno virtual**

# Windows
venv_scouting\Scripts\activate

# macOS/Linux
source venv_scouting/bin/activate

4. **Instalar dependencias**

pip install -r requirements.txt

5. **Ejecutar la aplicación**

streamlit run Home.py

👤 Credenciales de Acceso
Usuario de prueba:

Usuario: admin
Contraseña: admin123

📊 Datos de Ejemplo
La aplicación incluye una base de datos de ejemplo con jugadores destacados:

Lionel Messi (Inter Miami)
Kylian Mbappé (Real Madrid)
Pedri González (FC Barcelona)
Virgil van Dijk (Liverpool)
Gavi Páez (FC Barcelona)

🔧 Configuración Avanzada
Personalización de Tema
Editar .streamlit/config.toml para personalizar colores y apariencia.
Base de Datos Personalizada
Modificar models/jugador_model.py para conectar con fuentes de datos externas.
🚀 Funcionalidades Futuras

 Integración con APIs de WyScout y BeSoccer PRO
 Análisis predictivo con Machine Learning
 Mapas de calor del campo de juego
 Análisis de video integrado
 Dashboard en tiempo real
 Exportación a Excel
 Notificaciones automáticas
 Análisis de lesiones

🤝 Contribución
Este proyecto fue desarrollado como Trabajo de Fin de Máster. Para contribuciones o mejoras, contactar con el desarrollador.
📄 Licencia
Proyecto académico - Todos los derechos reservados.
📞 Contacto
Desarrollador: Manuel Pérez Ruda
Email: perezrudamanuel@gmail.com
Máster: Máster en Python Avanzado Aplicado al Deporte

Desarrollado con ❤️ para profesionales del fútbol