# TEKIA - Sistema Soberano de Investigación

![TEKIA Logo](https://img.shields.io/badge/TEKIA-Sistema_Soberano-085041?style=for-the-badge)
![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)

**TEKIA** es un **sistema local soberano** de investigación diseñado para científicos de datos, arquitectos RAG, investigadores autónomos y miembros del CLACSO. Permite descargar, indexar, analizar y vincular fuentes de información **hegemónicas** (medios tradicionales) y **situadas** (voces locales/comunitarias) a un cuaderno de notas 100% local.

## 🎯 Objetivos Principales

1. **Descargar** documentos de medios hegemónicos y situados (páginas web o PDFs)
2. **Organizar** los documentos en carpetas locales (`hegemonic/`, `situated/`)
3. **Analizar** los documentos (sin LLM, solo Python) para extraer:
   - Resúmenes (LexRank)
   - Palabras clave (TF-IDF)
   - Patrones (fechas, nombres, sesgos epistémicos)
   - Entidades (personas, organizaciones, lugares) con spaCy
4. **Generar La Grieta**: Análisis cruzado entre corpus hegemónicos y situados
5. **Sistema de Notas**: Cuaderno local con búsqueda full-text (FTS5), etiquetas y exportación
6. **Alertas**: Notificaciones para seguimiento de temas

## ⚡ Características Clave

- ✅ **100% Local**: Todo se guarda en tu máquina (SQLite + FAISS + archivos)
- ✅ **Sin Nube**: Ningún dato sale de tu equipo
- ✅ **Sin LLM**: Análisis basado en técnicas clásicas de NLP (TF-IDF, LexRank, spaCy)
- ✅ **Sin Telemetría**: Ningún rastreo o recolección de datos
- ✅ **Soberanía Digital**: Tú controlas tus datos y tu infraestructura
- ✅ **Rápido**: Búsqueda vectorial con FAISS y búsqueda full-text con FTS5
- ✅ **Extensible**: Arquitectura modular para añadir nuevos métodos de análisis

## 🏗️ Arquitectura

```
tekia/
├── app/                          # Backend (FastAPI)
│   ├── main.py                   # Punto de entrada
│   ├── config.py                 # Configuración
│   ├── database.py               # SQLite + ORM
│   ├── models/                   # Modelos de datos
│   ├── services/                 # Lógica de negocio
│   │   ├── rag_service.py        # Descarga e indexación de documentos
│   │   ├── grieta_service.py     # Análisis cruzado HEG/SIT
│   │   ├── note_service.py       # Gestión de notas
│   │   ├── search_service.py     # Búsqueda unificada
│   │   ├── alert_service.py      # Alertas de seguimiento
│   │   ├── crypto_service.py     # Cifrado de notas
│   │   └── integration.py        # Integración entre módulos
│   ├── routers/                  # Endpoints API
│   │   ├── rag.py                # /api/rag/*
│   │   ├── notes.py              # /api/notes/*
│   │   └── alerts.py             # /api/alerts/*
│   └── templates/                # Frontend (Jinja2)
│       ├── base.html             # Layout base
│       ├── index.html            # Página principal
│       ├── rag.html              # Investigación
│       ├── notes.html            # Cuaderno
│       └── alerts.html           # Alertas
│
├── app/static/                   # Archivos estáticos
│   ├── css/                      # Estilos CSS
│   └── js/                       # JavaScript
│
├── data/                         # Datos locales
│   ├── tekia.db                  # Base de datos SQLite
│   ├── documents/                # Documentos descargados
│   │   ├── hegemonic/            # Fuentes hegemónicas
│   │   └── situated/             # Fuentes situadas
│   └── embeddings/               # Índice FAISS
│       ├── documents.faiss       # Vectores
│       └── documents_mapping.json # Mapeo FAISS → SQLite
│
├── models/                       # Modelos de ML
│   └── paraphrase-multilingual-MiniLM-L12-v2/  # Embeddings
│
├── bias_vocab/                   # Vocabulario de sesgo
│   ├── hegemonic_terms.txt       # Términos hegemónicos
│   └── situated_terms.txt        # Términos situados
│
├── keys/                         # Claves de cifrado
│   └── secret.key                # Clave Fernet
│
├── backups/                      # Backups automáticos
│
├── requirements.txt              # Dependencias Python
├── Dockerfile                    # Contenedor Docker
├── docker-compose.yml            # Orquestación Docker
├── install.sh                    # Script de instalación
└── README.md                     # Este archivo
```

## 📦 Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)
- Git (opcional, para clonar el repositorio)
- Docker (opcional, para despliegue en contenedores)

## 🚀 Instalación

### Opción 1: Instalación Local

1. **Clonar el repositorio** (o descargar el ZIP):
   ```bash
   git clone https://github.com/indioyori/tekia_github.git
   cd tekia_github
   ```

2. **Ejecutar el script de instalación**:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```
   
   Esto instalará:
   - Todas las dependencias Python
   - Modelo de spaCy para español (`es_core_news_md`)
   - Modelo de embeddings (`paraphrase-multilingual-MiniLM-L12-v2`)
   - Generará la clave de cifrado
   - Inicializará la base de datos

3. **Iniciar TEKIA**:
   ```bash
   # En macOS (evitar problemas con fork)
   OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES uvicorn app.main:app --port 8100
   
   # En Linux/Windows
   uvicorn app.main:app --port 8100
   ```

4. **Acceder a TEKIA**:
   Abre tu navegador y ve a [http://localhost:8100](http://localhost:8100)

### Opción 2: Docker (Recomendado)

1. **Construir la imagen**:
   ```bash
   docker-compose build
   ```

2. **Iniciar el contenedor**:
   ```bash
   docker-compose up -d
   ```

3. **Acceder a TEKIA**:
   Abre tu navegador y ve a [http://localhost:8100](http://localhost:8100)

## 🎨 Interfaz de Usuario

### 1. **Investigar** (`/rag`)
- **Búsqueda Web**: Busca en DuckDuckGo (con fallbacks a SearXNG o Google CSE)
- **Clasificación Automática**: Los resultados se clasifican como **Hegemónicos** o **Situados** usando:
  - Dominios predefinidos (ampliado para México y Latinoamérica)
  - Vocabulario de sesgo (`bias_vocab/hegemonic_terms.txt` y `situated_terms.txt`)
- **Descarga de Documentos**: Descarga PDFs o HTML a tu máquina local
- **La Grieta**: Análisis cruzado automático cuando hay documentos de ambos tipos

### 2. **Cuaderno** (`/notes`)
- **Notas en Markdown**: Editor con soporte para formato Markdown
- **Organización**: Por temas y etiquetas
- **Búsqueda Full-Text**: Usando FTS5 de SQLite
- **Exportación**: A Markdown, HTML o PDF
- **Vinculación**: Notas vinculadas a documentos
- **Cifrado**: Opcional (Fernet)

### 3. **Alertas** (`/alerts`)
- **Alertas de Seguimiento**: Configura alertas para temas de interés
- **Disparo Manual/Automático**: Busca nuevos resultados periódicamente
- **Notificaciones Locales**: Usando plyer (opcional)

## 🔍 Análisis de La Grieta

Cuando descargas documentos de **ambos tipos (hegemónico y situado)**, TEKIA genera automáticamente **La Grieta**, un análisis cruzado que incluye:

1. **Resúmenes**: Usando LexRank para cada corpus
2. **Léxico**: Términos exclusivos y compartidos (TF-IDF)
3. **Silencios Epistémicos**: Términos del vocabulario de sesgo ausentes en cada corpus
4. **Actores Clave**: Entidades (PER, ORG, GPE) con verbos asociados
5. **Cronología**: Extracción de fechas y eventos
6. **Divergencia**: Similaridad coseno entre corpus (0% = idénticos, 100% = opuestos)
7. **Sesgos Epistémicos**: Detector de dominancia de vocabulario

## 📊 Endpoints API

### RAG (Investigación)
- `GET /api/rag/search-web/?q={query}&max_results={n}` - Buscar en web
- `POST /api/rag/download/` - Descargar documento
- `POST /api/rag/index/{doc_id}` - Indexar documento en FAISS
- `GET /api/rag/search/?q={query}&k={n}` - Buscar en documentos (FAISS)
- `GET /api/rag/documents/` - Listar documentos
- `POST /api/rag/grieta/` - Generar análisis de La Grieta
- `GET /api/rag/analyze/{doc_id}` - Analizar documento

### Notas (Cuaderno)
- `POST /api/notes/` - Crear nota
- `GET /api/notes/{note_id}` - Obtener nota
- `GET /api/notes/` - Listar notas
- `PUT /api/notes/{note_id}` - Actualizar nota
- `DELETE /api/notes/{note_id}` - Eliminar nota
- `GET /api/notes/search/?q={query}` - Buscar notas (FTS5)
- `GET /api/notes/tags/` - Listar etiquetas
- `GET /api/notes/by-document/{doc_id}` - Notas por documento
- `GET /api/notes/export/{note_id}?format={md|html|pdf}` - Exportar nota

### Alertas
- `POST /api/alerts/` - Crear alerta
- `GET /api/alerts/{alert_id}` - Obtener alerta
- `GET /api/alerts/` - Listar alertas
- `PUT /api/alerts/{alert_id}` - Actualizar alerta
- `DELETE /api/alerts/{alert_id}` - Eliminar alerta
- `POST /api/alerts/{alert_id}/trigger` - Disparar alerta
- `POST /api/alerts/trigger-all/` - Disparar todas las alertas
- `GET /api/alerts/inactive/` - Alertas inactivas

### Utilidades
- `GET /api/health` - Estado del sistema
- `GET /api/info` - Estadísticas (documentos, notas, alertas)

## 🔧 Configuración

### Variables de Entorno

Crea un archivo `.env` en el directorio raíz:

```env
# Configuración de SearXNG (fallback para búsqueda)
SEARXNG_ENABLED=true
SEARXNG_URL=http://localhost:8888

# Configuración de Google Custom Search (opcional)
GOOGLE_CSE_ENABLED=true
GOOGLE_CSE_API_KEY=tu_api_key
GOOGLE_CSE_CX=tu_cx_id

# Configuración de cifrado
ENCRYPTION_ENABLED=true

# Configuración de backups
BACKUP_ENABLED=true
BACKUP_INTERVAL=24
```

### Vocabulario de Sesgo

Los archivos `bias_vocab/hegemonic_terms.txt` y `bias_vocab/situated_terms.txt` contienen los términos usados para:
1. **Clasificación automática** de documentos
2. **Detección de silencios epistémicos** en La Grieta

Puedes personalizar estos archivos para adaptarlos a tu dominio de investigación.

### Dominios Hegemónicos

El archivo `app/config.py` contiene la lista `HEG_DOMAINS` con dominios de medios tradicionales. Puedes ampliarla según tus necesidades.

## 🛡️ Seguridad

- **Cifrado**: Las notas se pueden cifrar usando Fernet (AES-128)
- **Privacidad**: Ningún dato sale de tu máquina
- **Backups**: Configura backups automáticos en `app/config.py`
- **Claves**: La clave de cifrado se genera automáticamente en `keys/secret.key`

## 📈 Rendimiento

- **FAISS**: Índice vectorial para búsqueda semántica
- **FTS5**: Búsqueda full-text en SQLite
- **Caching**: Los modelos de ML se cargan una vez (lazy loading)
- **Procesamiento en segundo plano**: Usa Celery o BackgroundTasks para tareas pesadas

## 🤝 Contribuir

1. Haz un fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -m 'Añade nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.

## 🙏 Agradecimientos

- **FronterIA-Lab**: Por el apoyo en el desarrollo inicial
- **Yoremnokki**: Por la visión y conceptualización
- **CLACSO**: Por la inspiración en investigación crítica
- **Comunidad de Software Libre**: Por las herramientas que hacen posible este proyecto

## 📞 Contacto

Para preguntas, sugerencias o reportes de errores:
- Abre un **Issue** en [GitHub](https://github.com/indioyori/tekia_github/issues)
- Contacta al equipo de desarrollo

---

**TEKIA** - *Por una investigación soberana y crítica*

*Sin nube. Sin LLM. Sin telemetría.*
