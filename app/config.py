"""
Configuración central de TEKIA.
"""
from pathlib import Path
from typing import Set

# Directorios base
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
HEGEMONIC_DIR = DOCUMENTS_DIR / "hegemonic"
SITUATED_DIR = DOCUMENTS_DIR / "situated"
EMBEDDINGS_DIR = DATA_DIR / "embeddings"
KEYS_DIR = BASE_DIR / "keys"
BIAS_VOCAB_DIR = BASE_DIR / "bias_vocab"
MODELS_DIR = BASE_DIR / "models"
BACKUPS_DIR = BASE_DIR / "backups"
STATIC_DIR = BASE_DIR / "app" / "static"
TEMPLATES_DIR = BASE_DIR / "app" / "templates"

# Base de datos
DB_PATH = DATA_DIR / "tekia.db"

# Modelos de embedding
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
EMBEDDING_DIM = 384  # Dimensión de MiniLM

# Dominios hegemónicos (ampliado para México y Latinoamérica)
HEG_DOMAINS: Set[str] = {
    # Medios tradicionales mexicanos
    "reforma.com", "eleconomista.com.mx", "milenio.com", "eluniversal.com.mx",
    "expansion.mx", "forbes.com.mx", "reuters.com", "bbc.com", "nytimes.com",
    "larazon.com.mx", "excelsior.com.mx", "informador.mx", "jornada.com.mx",
    "sinembargo.mx", "proceso.com.mx", "aristeguinoticias.com",
    "animalpolitico.com", "elfinanciero.com.mx", "heraldo.mx",
    # Dominios adicionales para México
    "soysinaloa.com", "gpo.com.mx", "launion.com.mx", "noroeste.com.mx",
    "eldebate.com.mx", "elmanana.com.mx", "vanguardia.com.mx",
    "elheraldodechihuahua.com.mx", "elheraldo.com.mx", "elimparcial.com",
    "elpais.com", "elconfidencial.com", "lavanguardia.com",
    # Medios internacionales hegemónicos
    "cnn.com", "foxnews.com", "washingtonpost.com", "theguardian.com",
    "lemonde.fr", "elpais.com", "clarin.com", "lanacion.com.ar",
    # Agencias de noticias
    "apnews.com", "afp.com", "dpa.com", "ansalatina.com",
}

# Configuración de SearXNG (fallback para búsqueda)
SEARXNG_ENABLED = False  # Cambiar a True si se usa SearXNG
SEARXNG_URL = "http://localhost:8888"  # URL local de SearXNG

# Configuración de Google Custom Search (opcional, requiere API key)
GOOGLE_CSE_ENABLED = False
GOOGLE_CSE_API_KEY = None  # Almacenar en keys/google_api_key.txt
GOOGLE_CSE_CX = None       # Custom Search Engine ID

# Configuración de cifrado
ENCRYPTION_ENABLED = True  # Habilitar cifrado por defecto

# Configuración de backups
BACKUP_ENABLED = True
BACKUP_INTERVAL = 24  # Horas entre backups

# Configuración de logging
LOG_LEVEL = "INFO"
LOG_FILE = DATA_DIR / "tekia.log"

# Inicializar directorios
for dir_path in [DATA_DIR, DOCUMENTS_DIR, HEGEMONIC_DIR, SITUATED_DIR, EMBEDDINGS_DIR, 
                 KEYS_DIR, BIAS_VOCAB_DIR, MODELS_DIR, BACKUPS_DIR, STATIC_DIR, TEMPLATES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
