# TEKIA - Dockerfile
# Sistema soberano de investigación

FROM python:3.10-slim

# Configuración básica
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    git \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias Python
RUN pip install --no-cache-dir -r requirements.txt

# Descargar modelo de spaCy para español
RUN python -m spacy download es_core_news_md

# Copiar el resto de la aplicación
COPY . .

# Crear directorios necesarios
RUN mkdir -p data/documents/hegemonic data/documents/situated data/embeddings keys models bias_vocab backups

# Configurar permisos
RUN chmod -R 755 /app

# Exponer puerto
EXPOSE 8100

# Configurar variable de entorno para macOS
ENV OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Comando de inicio
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8100"]
