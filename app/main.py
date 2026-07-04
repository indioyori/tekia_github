"""
TEKIA - Sistema Soberano de Investigación
Punto de entrada principal (FastAPI).
"""
import warnings
warnings.filterwarnings("ignore")

from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import uvicorn
import os

from .config import STATIC_DIR, TEMPLATES_DIR
from .database import init_db, get_db
from .services.rag_service import _get_model
from .routers.rag import router as rag_router
from .routers.notes import router as notes_router
from .routers.alerts import router as alerts_router

# Inicializar aplicación FastAPI
app = FastAPI(
    title="TEKIA",
    description="Sistema local soberano de investigación: descarga, indexa, analiza y vincula fuentes hegemónicas y situadas a un cuaderno de notas.",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Configurar templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Incluir routers
app.include_router(rag_router)
app.include_router(notes_router)
app.include_router(alerts_router)


# Eventos de ciclo de vida
@app.on_event("startup")
async def startup():
    """Inicialización al iniciar la aplicación."""
    # Inicializar base de datos
    init_db()
    
    # Cargar modelo de embeddings (pre-carga)
    try:
        _get_model()
        print("✓ Modelo de embeddings cargado")
    except Exception as e:
        print(f"⚠ Error cargando modelo de embeddings: {e}")
    
    print("✓ TEKIA inicializado correctamente")


@app.on_event("shutdown")
async def shutdown():
    """Limpieza al detener la aplicación."""
    print("✓ TEKIA detenido")


# Rutas de páginas principales
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """Página principal (redirige a /rag)."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/rag", response_class=HTMLResponse)
def investigar(request: Request):
    """Página de Investigación."""
    return templates.TemplateResponse("rag.html", {"request": request})


@app.get("/notes", response_class=HTMLResponse)
def cuaderno(request: Request):
    """Página del Cuaderno de Notas."""
    return templates.TemplateResponse("notes.html", {"request": request})


@app.get("/alerts", response_class=HTMLResponse)
def alertas(request: Request):
    """Página de Alertas."""
    return templates.TemplateResponse("alerts.html", {"request": request})


# Endpoints de salud y utilidades
@app.get("/api/health")
def health():
    """Endpoint de salud."""
    return {
        "status": "ok",
        "version": "2.1.0",
        "name": "TEKIA"
    }


@app.get("/api/info")
def info(db: Session = Depends(get_db)):
    """Información del sistema."""
    from .models import Document, Note, Alert
    
    doc_count = db.query(Document).count()
    note_count = db.query(Note).count()
    alert_count = db.query(Alert).count()
    
    return {
        "documents": doc_count,
        "notes": note_count,
        "alerts": alert_count,
        "version": "2.1.0"
    }


# Punto de entrada para ejecución directa
if __name__ == "__main__":
    # Configuración para macOS (evitar problemas con fork)
    os.environ["OBJC_DISABLE_INITIALIZE_FORK_SAFETY"] = "YES"
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8100,
        reload=True,
        log_level="info"
    )
