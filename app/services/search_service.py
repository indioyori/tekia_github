"""
Servicio de búsqueda unificada para TEKIA.
Combina búsqueda en documentos (FAISS) y notas (FTS5).
"""
from typing import List, Dict
from sqlalchemy.orm import Session

from .rag_service import RAGService
from .note_service import NoteService


class SearchService:
    """Servicio de búsqueda unificada."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService(db)
        self.note_service = NoteService(db)
    
    def search_documents(self, query: str, k: int = 5) -> List[Dict]:
        """Busca en documentos usando FAISS."""
        return self.rag_service.search_documents(query, k)
    
    def search_notes(self, query: str, limit: int = 20) -> List[Dict]:
        """Busca en notas usando FTS5."""
        notes = self.note_service.search(query, limit)
        return [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content[:200] + "...",
                "theme": note.theme,
                "type": "note"
            }
            for note in notes
        ]
    
    def unified_search(self, query: str, types: str = "documents,notes", 
                       doc_limit: int = 5, note_limit: int = 10) -> List[Dict]:
        """
        Búsqueda unificada en documentos y/o notas.
        
        Args:
            query: Término de búsqueda
            types: "documents", "notes" o "documents,notes"
            doc_limit: Límite de resultados para documentos
            note_limit: Límite de resultados para notas
        
        Returns:
            Lista de resultados combinados
        """
        results = []
        
        if "documents" in types:
            doc_results = self.search_documents(query, doc_limit)
            for doc in doc_results:
                results.append({
                    **doc,
                    "type": "document"
                })
        
        if "notes" in types:
            note_results = self.search_notes(query, note_limit)
            results.extend(note_results)
        
        # Ordenar por relevancia (documentos primero, luego notas)
        results.sort(key=lambda x: (
            0 if x["type"] == "document" else 1,
            -x.get("score", 0)
        ))
        
        return results
    
    def search_by_theme(self, theme: str, types: str = "documents,notes") -> List[Dict]:
        """Busca por tema en documentos y/o notas."""
        results = []
        
        if "documents" in types:
            docs = self.db.query(Document).filter(Document.theme == theme).all()
            for doc in docs:
                results.append({
                    "id": doc.id,
                    "title": doc.title,
                    "url": doc.url,
                    "source_type": doc.source_type,
                    "theme": doc.theme,
                    "type": "document"
                })
        
        if "notes" in types:
            notes = self.note_service.get_all(theme=theme)
            for note in notes:
                results.append({
                    "id": note.id,
                    "title": note.title,
                    "content": note.content[:200] + "...",
                    "theme": note.theme,
                    "type": "note"
                })
        
        return results
    
    def search_by_tag(self, tag: str) -> List[Dict]:
        """Busca notas por etiqueta."""
        notes = self.note_service.get_all(tag=tag)
        return [
            {
                "id": note.id,
                "title": note.title,
                "content": note.content[:200] + "...",
                "theme": note.theme,
                "type": "note"
            }
            for note in notes
        ]
