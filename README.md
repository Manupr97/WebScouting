# ⚽ WebScouting - Sistema Profesional de Scouting de Fútbol

<div align="center">
  <img src="assets/images/identidad_MPR_1.png" alt="WebScouting Logo" width="200"/>
  
  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
  [![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)](LICENSE)
</div>

## 📖 Descripción

WebScouting es una plataforma integral de análisis y scouting de fútbol desarrollada con Streamlit. Integra datos reales de **574 jugadores de LaLiga** procedentes de Wyscout, permitiendo a scouts profesionales, directores deportivos y analistas tomar decisiones informadas basadas en datos.

## 🌟 Características Principales

### 📊 Base de Datos Wyscout LaLiga
- **574 jugadores** con estadísticas completas y actualizadas
- **20 equipos** de LaLiga con análisis detallado
- **+100 métricas** por jugador (técnicas, tácticas, físicas)
- Integración automática con informes de scouting

### 🔍 Discovery Hub - Exploración Inteligente
- Sistema de tarjetas interactivas para descubrir talentos
- Filtros avanzados por edad, posición, equipo y estadísticas
- Algoritmo de recomendación de jugadores similares
- Vista previa rápida con estadísticas clave

### 📈 Visualizaciones Avanzadas
- **Gráficos de Radar**: Comparación multidimensional de habilidades
- **Análisis de Dispersión**: Correlación entre métricas clave
- **Mapas de Calor**: Matrices de correlación interactivas
- **Gráficos de Barras Dinámicos**: Rankings y comparativas
- **Análisis por Posición**: Estadísticas especializadas por rol

### ⚽ Centro de Scouting en Vivo
- Integración con **BeSoccer** para partidos en tiempo real
- Sistema de evaluación durante el partido
- Plantillas de informes pre-configuradas
- Seguimiento de jugadores objetivo en partidos

### 📋 Sistema de Informes Profesional
- **Evaluación completa**: 21 aspectos evaluables (técnicos, tácticos, físicos, mentales)
- **Integración Wyscout automática**: Vinculación inteligente de jugadores evaluados
- **Búsqueda fuzzy**: Encuentra jugadores incluso con nombres aproximados
- **Histórico completo**: Seguimiento de evolución del jugador

### 👀 Lista de Visualización
- Gestión de jugadores objetivo
- Estados de seguimiento (Pendiente, En observación, Evaluado)
- Integración con informes existentes
- Exportación de listas para compartir

### 🔐 Sistema Multiusuario
- Roles diferenciados (Admin, Scout, Analista)
- Gestión de permisos por funcionalidad
- Trazabilidad de acciones por usuario
- Panel de administración

### 📊 Dashboard Ejecutivo
- Métricas en tiempo real del sistema
- Top performers por categoría
- Actividad reciente del equipo de scouting
- Insights automáticos sobre la base de datos

## 🛠️ Tecnologías Utilizadas

### Core
- **Frontend**: Streamlit 1.31.0
- **Base de Datos**: SQLite3
- **Procesamiento**: Pandas 2.0+, NumPy

### Visualización
- **Plotly**: Gráficos interactivos
- **Matplotlib/Seaborn**: Análisis estadístico
- **MPLSoccer**: Visualizaciones específicas de fútbol

### Integraciones
- **Wyscout**: Datos profesionales de LaLiga
- **BeSoccer**: Información de partidos en vivo
- **FuzzyWuzzy**: Búsqueda inteligente de jugadores

### Utilidades
- **Streamlit-extras**: Componentes adicionales
- **Openpyxl**: Procesamiento de Excel
- **BeautifulSoup4**: Web scraping

## 📦 Instalación

### Requisitos Previos
- Python 3.8 o superior
- Git

### Pasos de Instalación

1. **Clonar el repositorio:**
```bash
git clone https://github.com/Manupr97/WebScouting.git
cd WebScouting
```

2. **Crear entorno virtual:**
```bash
python -m venv venv_scouting
```

3. **Activar el entorno virtual:**
```bash
# Windows
venv_scouting\Scripts\activate

# macOS/Linux
source venv_scouting/bin/activate
```

4. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

5. **Ejecutar la aplicación:**
```bash
streamlit run Home.py
```

La aplicación se abrirá en `http://localhost:8501`

## 🔑 Credenciales de Acceso

### Usuario Administrador
- **Usuario**: `admin`
- **Contraseña**: `admin123`

### Usuario Scout
- **Usuario**: `scout1`
- **Contraseña**: `scout123`

## 📂 Estructura del Proyecto

```
WebScouting/
├── 📁 assets/              # Recursos estáticos
│   └── images/            # Imágenes y logos
├── 📁 common/              # Módulos compartidos
│   ├── login.py          # Sistema de autenticación
│   └── cache_helpers.py  # Gestión de caché
├── 📁 data/                # Datos de la aplicación
│   └── wyscout_LaLiga_limpio.xlsx  # Base de datos principal
├── 📁 models/              # Modelos de datos
│   ├── jugador_model.py  # Gestión de jugadores
│   ├── partido_model.py  # Gestión de partidos e informes
│   └── wyscout_model.py  # Integración Wyscout
├── 📁 pages/               # Páginas de la aplicación
│   ├── 1_🔍_Jugadores.py
│   ├── 2_📊_Bases_Datos_Unificadas.py
│   ├── 3_📊_Visualizaciones.py
│   ├── 4_⚽_Centro_de_Scouting.py
│   ├── 5_📋_Mis_Informes.py
│   └── 6_👀_Lista_Visualizacion.py
├── 📁 utils/               # Utilidades
│   ├── besoccer_scraper.py
│   └── monitor_performance.py
├── 📄 Home.py              # Página principal
├── 📄 requirements.txt     # Dependencias
└── 📄 README.md           # Este archivo
```

## 🚀 Uso de la Aplicación

### 1. Dashboard Principal
- Vista general del sistema
- Métricas principales
- Actividad reciente
- Accesos rápidos a funcionalidades

### 2. Discovery Hub (🔍 Jugadores)
- Explorar jugadores con filtros avanzados
- Descubrir talentos ocultos
- Análisis rápido de estadísticas

### 3. Base de Datos (📊)
- Vista completa de todos los jugadores
- Exportación de datos
- Búsqueda avanzada

### 4. Visualizaciones (📊)
- Crear gráficos personalizados
- Comparar jugadores visualmente
- Análisis de correlaciones

### 5. Centro de Scouting (⚽)
- Seguir partidos en vivo
- Evaluar jugadores en tiempo real
- Crear informes durante el partido

### 6. Mis Informes (📋)
- Gestionar informes creados
- Ver histórico de evaluaciones
- Exportar informes

### 7. Lista de Visualización (👀)
- Gestionar jugadores objetivo
- Seguimiento de estado
- Planificar observaciones

## 🔧 Configuración Avanzada

### Personalización de Datos
- Reemplazar `data/wyscout_LaLiga_limpio.xlsx` con tus propios datos
- Mantener la estructura de columnas existente

### Configuración de Caché
- Modificar duración en `models/wyscout_model.py`
- Ajustar `_cache_duration` según necesidades

### Integración con APIs Externas
- Configurar credenciales en `utils/besoccer_scraper.py`
- Adaptar scrapers según fuentes de datos

## 🤝 Contribución

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## 👨‍💻 Autor

**Manuel Pérez Ruda**
- Email: perezrudamanuel@gmail.com
- GitHub: [@Manupr97](https://github.com/Manupr97)
- LinkedIn: [Manuel Pérez Ruda](https://linkedin.com/in/manuel-perez-ruda)

## 🙏 Agradecimientos

- **Wyscout** por proporcionar datos profesionales de LaLiga
- **Streamlit** por el framework de desarrollo
- **Comunidad Python** por las librerías utilizadas

---

<div align="center">
  Desarrollado con ❤️ para revolucionar el scouting en el fútbol
  
  ⭐ Si te gusta este proyecto, no olvides darle una estrella en GitHub ⭐
</div>