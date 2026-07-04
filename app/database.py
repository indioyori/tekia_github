"""
Base de datos SQLite para TEKIA.
Modelos: Document, Note, Tag, Alert
"""
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
from pathlib import Path
from .config import DB_PATH

# Base para modelos
Base = declarative_base()


class Document(Base):
    """Documento descargado (hegemónico o situado)."""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    url = Column(String(1000), unique=True, index=True)
    source_type = Column(String(20), index=True)  # 'hegemonic' o 'situated'
    file_path = Column(String(1000))  # Path al archivo local
    content = Column(Text)  # Contenido extraído (opcional, para búsqueda rápida)
    theme = Column(String(200), index=True)  # Tema asociado
    date_downloaded = Column(DateTime, default=datetime.utcnow)
    indexed = Column(Boolean, default=False)  # ¿Indexado en FAISS?
    
    # Relaciones
    notes = relationship("Note", back_populates="document")
    
    def __repr__(self):
        return f"<Document(id={self.id}, title={self.title[:30]}..., source_type={self.source_type})>"


class Note(Base):
    """Nota en el cuaderno de investigación."""
    __tablename__ = "notes"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), index=True)
    content = Column(Text)  # Contenido en Markdown
    theme = Column(String(200), index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    encrypted = Column(Boolean, default=False)  # ¿Contenido cifrado?
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    document = relationship("Document", back_populates="notes")
    tags = relationship("Tag", secondary="note_tags", back_populates="notes")
    
    def __repr__(self):
        return f"<Note(id={self.id}, title={self.title[:30]}...)>"


class Tag(Base):
    """Etiqueta para notas."""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    
    # Relaciones
    notes = relationship("Note", secondary="note_tags", back_populates="tags")
    
    def __repr__(self):
        return f"<Tag(id={self.id}, name={self.name})>"


class Alert(Base):
    """Alerta de seguimiento para temas."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    query = Column(String(500), index=True)  # Término de búsqueda
    theme = Column(String(200), index=True)
    last_triggered = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Alert(id={self.id}, query={self.query[:30]}...)>"


# Tabla intermedia para relación Note-Tag (many-to-many)
note_tags = relationship(
    "Note",
    secondary="note_tags",
    back_populates="tags"
)

# Tabla intermedia explícita
class NoteTag(Base):
    """Relación many-to-many entre Note y Tag."""
    __tablename__ = "note_tags"
    
    note_id = Column(Integer, ForeignKey("notes.id"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id"), primary_key=True)


# Inicialización de la base de datos
def init_db():
    """Inicializa la base de datos y crea tablas si no existen."""
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    return engine


# Sesión de base de datos
def get_db():
    """Generador de sesiones de base de datos."""
    engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Inicializar FTS5 para búsqueda full-text en notas
def init_fts5(db):
    """Crea tablas FTS5 para búsqueda full-text."""
    from sqlalchemy import text
    
    # Tabla FTS5 para notas
    db.execute(text("""
        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts 
        USING fts5(
            id UNINDEXED,
            title,
            content,
            theme,
            tokenize='unicode61 remove_diacritics 2'
        )
    """))
    
    # Triggers para mantener sincronizada notes_fts con notes
    db.execute(text("""
        CREATE TRIGGER IF NOT EXISTS notes_fts_insert 
        AFTER INSERT ON notes 
        BEGIN
            INSERT INTO notes_fts(id, title, content, theme) 
            VALUES (new.id, new.title, new.content, new.theme);
        END
    """))
    
    db.execute(text("""
        CREATE TRIGGER IF NOT EXISTS notes_fts_update 
        AFTER UPDATE ON notes 
        BEGIN
            UPDATE notes_fts 
            SET title = new.title, content = new.content, theme = new.theme 
            WHERE id = new.id;
        END
    """))
    
    db.execute(text("""
        CREATE TRIGGER IF NOT EXISTS notes_fts_delete 
        AFTER DELETE ON notes 
        BEGIN
            DELETE FROM notes_fts WHERE id = old.id;
        END
    """))
    
    db.commit()
