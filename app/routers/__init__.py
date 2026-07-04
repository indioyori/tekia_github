# Routers de TEKIA
from .rag import router as rag_router
from .notes import router as notes_router
from .alerts import router as alerts_router

__all__ = ["rag_router", "notes_router", "alerts_router"]
