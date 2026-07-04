"""
Router para endpoints de Notas (Cuaderno).
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from ..database import get_db
from ..services.note_service import NoteService
from ..models import Note

router = APIRouter(prefix="/api/notes", tags=["Notes"])


@router.post("/")
def create_note(
    title: str,
    content: str,
    theme: str = "",
    document_id: Optional[int] = None,
    tags: List[str] = None,
    db: Session = Depends(get_db)
):
    """Crea una nueva nota."""
    service = NoteService(db)
    note = service.create(title, content, theme, document_id, tags)
    return {
        "id": note.id,
        "title": note.title,
        "theme": note.theme,
        "created_at": note.created_at.isoformat()
    }


@router.get("/{note_id}")
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Obtiene una nota por ID."""
    service = NoteService(db)
    note = service.get(note_id)
    
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "theme": note.theme,
        "document_id": note.document_id,
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat()
    }


@router.get("/")
def list_notes(
    theme: str = None,
    tag: str = None,
    db: Session = Depends(get_db)
):
    """Lista todas las notas."""
    service = NoteService(db)
    notes = service.get_all(theme, tag)
    
    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content[:200] + "...",
            "theme": note.theme,
            "created_at": note.created_at.isoformat()
        }
        for note in notes
    ]


@router.put("/{note_id}")
def update_note(
    note_id: int,
    title: str = None,
    content: str = None,
    theme: str = None,
    tags: List[str] = None,
    db: Session = Depends(get_db)
):
    """Actualiza una nota."""
    service = NoteService(db)
    note = service.update(note_id, title, content, theme, tags)
    
    if not note:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    
    return {
        "id": note.id,
        "title": note.title,
        "theme": note.theme,
        "updated_at": note.updated_at.isoformat()
    }


@router.delete("/{note_id}")
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """Elimina una nota."""
    service = NoteService(db)
    success = service.delete(note_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    
    return {"status": "ok", "message": "Nota eliminada"}


@router.get("/search/")
def search_notes(q: str, limit: int = 20, db: Session = Depends(get_db)):
    """Busca notas usando FTS5."""
    service = NoteService(db)
    notes = service.search(q, limit)
    
    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content[:200] + "...",
            "theme": note.theme
        }
        for note in notes
    ]


@router.get("/tags/")
def list_tags(db: Session = Depends(get_db)):
    """Lista todas las etiquetas."""
    service = NoteService(db)
    tags = service.get_tags()
    
    return [{"id": tag.id, "name": tag.name} for tag in tags]


@router.get("/by-document/{document_id}")
def get_notes_by_document(document_id: int, db: Session = Depends(get_db)):
    """Obtiene notas vinculadas a un documento."""
    service = NoteService(db)
    notes = service.get_notes_by_document(document_id)
    
    return [
        {
            "id": note.id,
            "title": note.title,
            "content": note.content[:200] + "...",
            "theme": note.theme
        }
        for note in notes
    ]


@router.get("/export/{note_id}")
def export_note(note_id: int, format: str = "markdown", db: Session = Depends(get_db)):
    """Exporta una nota en el formato especificado."""
    service = NoteService(db)
    content = service.export_note(note_id, format)
    
    if not content:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    
    return {"format": format, "content": content}


@router.post("/from-document/{document_id}")
def create_note_from_document(
    document_id: int,
    title: str = None,
    theme: str = None,
    db: Session = Depends(get_db)
):
    """Crea una nota desde un documento con análisis automático."""
    service = NoteService(db)
    note = service.create_from_document(document_id, title, theme)
    
    return {
        "id": note.id,
        "title": note.title,
        "theme": note.theme
    }
