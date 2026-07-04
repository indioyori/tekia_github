"""
Router para endpoints RAG (Investigar).
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Dict

from ..database import get_db
from ..services.rag_service import RAGService
from ..services.grieta_service import GrietaService
from ..services.integration import IntegrationService
from ..models import Document

router = APIRouter(prefix="/api/rag", tags=["RAG"])


@router.get("/search-web/")
def search_web(q: str, max_results: int = 8, db: Session = Depends(get_db)):
    """Busca en la web usando DuckDuckGo o fallbacks."""
    service = RAGService(db)
    results = service.search_web(q, max_results)
    return results


@router.post("/download/")
def download_document(
    url: str,
    source_type: str,
    theme: str = "",
    db: Session = Depends(get_db)
):
    """Descarga un documento y lo guarda localmente."""
    service = RAGService(db)
    doc = service.download_document(url, source_type, theme)
    
    if not doc:
        raise HTTPException(status_code=400, detail="Error descargando documento")
    
    return {
        "id": doc.id,
        "title": doc.title,
        "url": doc.url,
        "source_type": doc.source_type,
        "file_path": doc.file_path,
        "theme": doc.theme
    }


@router.post("/index/{doc_id}")
def index_document(doc_id: int, db: Session = Depends(get_db)):
    """Indexa un documento en FAISS."""
    service = RAGService(db)
    success = service.index_document(doc_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Error indexando documento")
    
    return {"status": "ok", "doc_id": doc_id}


@router.get("/search/")
def search_documents(q: str, k: int = 5, db: Session = Depends(get_db)):
    """Busca documentos usando FAISS."""
    service = RAGService(db)
    results = service.search_documents(q, k)
    return results


@router.get("/documents/")
def list_documents(
    source_type: str = None,
    theme: str = None,
    db: Session = Depends(get_db)
):
    """Lista todos los documentos."""
    query = db.query(Document)
    
    if source_type:
        query = query.filter(Document.source_type == source_type)
    if theme:
        query = query.filter(Document.theme == theme)
    
    docs = query.order_by(Document.date_downloaded.desc()).all()
    
    return [
        {
            "id": doc.id,
            "title": doc.title,
            "url": doc.url,
            "source_type": doc.source_type,
            "theme": doc.theme,
            "date_downloaded": doc.date_downloaded.isoformat(),
            "indexed": doc.indexed
        }
        for doc in docs
    ]


@router.post("/grieta/")
def generar_grieta(
    heg_ids: List[int],
    sit_ids: List[int],
    db: Session = Depends(get_db)
):
    """Genera el análisis de la Grieta entre documentos HEG y SIT."""
    service = GrietaService(db)
    result = service.generar(heg_ids, sit_ids)
    return result


@router.get("/analyze/{doc_id}")
def analyze_document(doc_id: int, db: Session = Depends(get_db)):
    """Analiza un documento (resumen, palabras clave, entidades)."""
    service = RAGService(db)
    result = service.analyze_document(doc_id)
    return result


@router.post("/full-workflow/")
def full_workflow(
    query: str,
    theme: str = None,
    db: Session = Depends(get_db)
):
    """Ejecuta el flujo completo: búsqueda, descarga, grieta, alerta."""
    service = IntegrationService(db)
    result = service.full_workflow(query, theme)
    return result
