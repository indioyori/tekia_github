"""
Servicio de notas para TEKIA.
Maneja CRUD, búsqueda full-text (FTS5), etiquetas y cifrado.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from pathlib import Path

from ..models import Note, Tag, Document, NoteTag
from ..database import init_fts5
from .crypto_service import crypto_service


class NoteService:
    """Servicio para gestión de notas."""
    
    def __init__(self, db: Session):
        self.db = db
        # Inicializar FTS5 si no existe
        init_fts5(db)
    
    def create(self, title: str, content: str, theme: str = "", 
               document_id: Optional[int] = None, tags: List[str] = None) -> Note:
        """Crea una nueva nota."""
        # Cifrar contenido si está habilitado
        encrypted_content = crypto_service.encrypt(content)
        
        note = Note(
            title=title,
            content=encrypted_content,
            theme=theme,
            document_id=document_id,
            encrypted=crypto_service.is_encrypted(encrypted_content),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        
        # Añadir etiquetas
        if tags:
            self._add_tags_to_note(note.id, tags)
        
        return note
    
    def get(self, note_id: int) -> Optional[Note]:
        """Obtiene una nota por ID."""
        note = self.db.query(Note).get(note_id)
        if note:
            # Descifrar contenido
            note.content = crypto_service.decrypt(note.content)
        return note
    
    def get_all(self, theme: str = None, tag: str = None) -> List[Note]:
        """Obtiene todas las notas, opcionalmente filtradas por tema o etiqueta."""
        query = self.db.query(Note)
        
        if theme:
            query = query.filter(Note.theme == theme)
        
        if tag:
            # Filtrar por etiqueta (usando la relación many-to-many)
            query = query.join(Note.tags).filter(Tag.name == tag)
        
        notes = query.order_by(Note.updated_at.desc()).all()
        
        # Descifrar contenido
        for note in notes:
            note.content = crypto_service.decrypt(note.content)
        
        return notes
    
    def update(self, note_id: int, title: str = None, content: str = None, 
               theme: str = None, tags: List[str] = None) -> Optional[Note]:
        """Actualiza una nota."""
        note = self.db.query(Note).get(note_id)
        if not note:
            return None
        
        if title:
            note.title = title
        if content:
            note.content = crypto_service.encrypt(content)
        if theme:
            note.theme = theme
        
        note.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(note)
        
        # Actualizar etiquetas
        if tags is not None:
            self._set_tags_for_note(note.id, tags)
        
        # Descifrar para devolver
        note.content = crypto_service.decrypt(note.content)
        return note
    
    def delete(self, note_id: int) -> bool:
        """Elimina una nota."""
        note = self.db.query(Note).get(note_id)
        if not note:
            return False
        
        # Eliminar relaciones con etiquetas
        self.db.query(NoteTag).filter(NoteTag.note_id == note_id).delete()
        
        self.db.delete(note)
        self.db.commit()
        return True
    
    def search(self, query: str, limit: int = 20) -> List[Note]:
        """Busca notas usando FTS5."""
        from sqlalchemy import text
        
        # Buscar en la tabla FTS5
        fts_query = f'"{query}"'
        sql = f"""
            SELECT id FROM notes_fts 
            WHERE notes_fts MATCH :query 
            ORDER BY rank 
            LIMIT :limit
        """
        
        result = self.db.execute(text(sql), {"query": fts_query, "limit": limit})
        note_ids = [row[0] for row in result.fetchall()]
        
        # Obtener notas completas
        notes = self.db.query(Note).filter(Note.id.in_(note_ids)).all()
        
        # Descifrar contenido
        for note in notes:
            note.content = crypto_service.decrypt(note.content)
        
        return notes
    
    def _add_tags_to_note(self, note_id: int, tag_names: List[str]):
        """Añade etiquetas a una nota."""
        for tag_name in tag_names:
            # Obtener o crear etiqueta
            tag = self.db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                self.db.add(tag)
                self.db.commit()
                self.db.refresh(tag)
            
            # Verificar si la relación ya existe
            existing = self.db.query(NoteTag).filter(
                NoteTag.note_id == note_id,
                NoteTag.tag_id == tag.id
            ).first()
            
            if not existing:
                note_tag = NoteTag(note_id=note_id, tag_id=tag.id)
                self.db.add(note_tag)
        
        self.db.commit()
    
    def _set_tags_for_note(self, note_id: int, tag_names: List[str]):
        """Establece las etiquetas de una nota (reemplaza las existentes)."""
        # Eliminar etiquetas existentes
        self.db.query(NoteTag).filter(NoteTag.note_id == note_id).delete()
        
        # Añadir nuevas etiquetas
        self._add_tags_to_note(note_id, tag_names)
    
    def get_tags(self) -> List[Tag]:
        """Obtiene todas las etiquetas."""
        return self.db.query(Tag).order_by(Tag.name).all()
    
    def get_notes_by_document(self, document_id: int) -> List[Note]:
        """Obtiene todas las notas vinculadas a un documento."""
        notes = self.db.query(Note).filter(Note.document_id == document_id).all()
        for note in notes:
            note.content = crypto_service.decrypt(note.content)
        return notes
    
    def export_note(self, note_id: int, format: str = "markdown") -> str:
        """Exporta una nota en el formato especificado."""
        note = self.get(note_id)
        if not note:
            return ""
        
        if format == "markdown":
            return f"# {note.title}\n\n{note.content}\n\n---\n*Tema: {note.theme}*\n*Creado: {note.created_at}*"
        elif format == "html":
            import markdown
            md = f"# {note.title}\n\n{note.content}\n\n---\n*Tema: {note.theme}*\n*Creado: {note.created_at}*"
            return markdown.markdown(md)
        else:
            return note.content
    
    def create_from_document(self, document_id: int, title: str = None, 
                             content: str = None, theme: str = None) -> Note:
        """Crea una nota vinculada a un documento."""
        doc = self.db.query(Document).get(document_id)
        if not doc:
            raise ValueError("Documento no encontrado")
        
        if not title:
            title = f"Análisis: {doc.title}"
        if not content:
            content = f"# Análisis de: {doc.title}\n\nURL: {doc.url}\n\n---\n"
        if not theme:
            theme = doc.theme
        
        return self.create(
            title=title,
            content=content,
            theme=theme,
            document_id=document_id
        )
