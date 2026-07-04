#!/bin/bash

# TEKIA - Script de Instalación
# Sistema soberano de investigación

set -e

echo "=========================================="
echo "  TEKIA - Instalación"
echo "=========================================="
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "   Instala Python 3.10 o superior antes de continuar"
    exit 1
fi

# Verificar pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ Error: pip no está instalado"
    echo "   Instala pip antes de continuar"
    exit 1
fi

# Crear entorno virtual (opcional)
read -p "¿Crear entorno virtual? (s/n) [s]: " CREATE_VENV
CREATE_VENV=${CREATE_VENV:-s}

if [ "$CREATE_VENV" = "s" ] || [ "$CREATE_VENV" = "S" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
    source .venv/bin/activate
    echo "✓ Entorno virtual creado y activado"
fi

# Instalar dependencias
echo ""
echo "Instalando dependencias..."
pip3 install --upgrade pip
pip3 install -r requirements.txt

# Descargar modelo de spaCy
echo ""
echo "Descargando modelo de spaCy para español..."
python3 -m spacy download es_core_news_md

# Descargar modelo de embeddings (MiniLM)
echo ""
echo "Descargando modelo de embeddings (MiniLM)..."
python3 -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); model.save('models/paraphrase-multilingual-MiniLM-L12-v2')"

# Crear directorios necesarios
echo ""
echo "Creando directorios..."
mkdir -p data/documents/hegemonic data/documents/situated data/embeddings keys models bias_vocab backups

# Generar clave de cifrado
echo ""
echo "Generando clave de cifrado..."
python3 -c "from cryptography.fernet import Fernet; key = Fernet.generate_key(); open('keys/secret.key', 'wb').write(key); print('✓ Clave generada en keys/secret.key')"

# Inicializar base de datos
echo ""
echo "Inicializando base de datos..."
python3 -c "from app.database import init_db; init_db(); print('✓ Base de datos inicializada')"

# Verificar instalación
echo ""
echo "=========================================="
echo "  ✓ Instalación completada"
echo "=========================================="
echo ""
echo "Para iniciar TEKIA:"
echo ""
if [ "$CREATE_VENV" = "s" ] || [ "$CREATE_VENV" = "S" ]; then
    echo "  source .venv/bin/activate  # Activar entorno virtual"
fi
echo "  uvicorn app.main:app --port 8100"
echo ""
echo "O con Docker:"
echo "  docker-compose up -d"
echo ""
echo "Accede a TEKIA en: http://localhost:8100"
echo ""
