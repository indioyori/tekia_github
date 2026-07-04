"""
Servicio de integración para TEKIA.
Conecta los diferentes módulos (RAG, Grieta, Notas, Alertas).
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from .rag_service import RAGService
from .grieta_service import GrietaService
from .note_service import NoteService
from .search_service import SearchService
from .alert_service import AlertService


class IntegrationService:
    """Servicio de integración entre módulos."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService(db)
        self.grieta_service = GrietaService(db)
        self.note_service = NoteService(db)
        self.search_service = SearchService(db)
        self.alert_service = AlertService(db)
    
    def create_note_from_document(self, document_id: int, 
                                  title: str = None, theme: str = None) -> Dict:
        """
        Crea una nota desde un documento, incluyendo análisis automático.
        """
        # Obtener documento
        doc = self.db.query(Document).get(document_id)
        if not doc:
            return {"error": "Documento no encontrado"}
        
        # Analizar documento
        analysis = self.rag_service.analyze_document(document_id)
        
        # Crear contenido de la nota
        content = f"""# Análisis de: {doc.title}

**URL:** {doc.url}
**Tipo:** {doc.source_type}
**Tema:** {doc.theme or theme or "Sin tema"}

---

## Resumen
{analysis.get("resumen", "")}

## Palabras clave
{", ".join(analysis.get("palabras_clave", []))}

## Entidades
- **Personas:** {", ".join(analysis.get("entidades", {}).get("PER", []))}
- **Organizaciones:** {", ".join(analysis.get("entidades", {}).get("ORG", []))}
- **Lugares:** {", ".join(analysis.get("entidades", {}).get("LOC", []))}
"""
        
        # Crear nota
        note = self.note_service.create(
            title=title or f"Análisis: {doc.title}",
            content=content,
            theme=theme or doc.theme,
            document_id=document_id
        )
        
        return {
            "note_id": note.id,
            "title": note.title,
            "content": content
        }
    
    def analyze_and_create_grieta(self, doc_ids_heg: List[int], doc_ids_sit: List[int],
                                  theme: str = None) -> Dict:
        """
        Analiza documentos y crea una nota con los resultados de la Grieta.
        """
        # Generar análisis de la Grieta
        grieta = self.grieta_service.generar(doc_ids_heg, doc_ids_sit)
        
        # Crear contenido de la nota
        content = f"""# La Grieta Epistémica: {theme or "Análisis"}

**Divergencia:** {grieta.get("divergencia", 0):.2%}

---

## Resúmenes

### Hegemónico
{grieta.get("resumen_heg", "")}

### Situado
{grieta.get("resumen_sit", "")}

---

## Léxico

### Términos exclusivos (Hegemónico)
{", ".join(grieta.get("lexicon", {}).get("exclusivo_heg", []))}

### Términos exclusivos (Situado)
{", ".join(grieta.get("lexicon", {}).get("exclusivo_sit", []))}

### Términos compartidos
{", ".join(grieta.get("lexicon", {}).get("compartido", []))}

---

## Silencios

### Hegemónico silencia
{", ".join(grieta.get("silencios", {}).get("heg_silencia", []))}

### Situado silencia
{", ".join(grieta.get("silencios", {}).get("sit_silencia", []))}

---

## Actores
"""
        
        for actor in grieta.get("actores", []):
            content += f"\n- **{actor['actor']}**: Hegemónico ({', '.join(actor['heg_verbos'])}) | Situado ({', '.join(actor['sit_verbos'])})"
        
        content += "\n\n---\n\n## Cronología\n"
        for event in grieta.get("cronologia", []):
            content += f"\n- **{event['year']}**: Hegemónico: {', '.join(event['heg'])} | Situado: {', '.join(event['sit'])}"
        
        # Crear nota
        note = self.note_service.create(
            title=f"Grieta: {theme or 'Análisis'}",
            content=content,
            theme=theme or "Grieta",
            tags=["grieta", "analisis", "hegemónico", "situado"]
        )
        
        return {
            "note_id": note.id,
            "grieta": grieta,
            "content": content
        }
    
    def create_alert_from_search(self, query: str, theme: str = None) -> Dict:
        """
        Crea una alerta desde una búsqueda.
        """
        # Buscar documentos relacionados
        doc_results = self.rag_service.search_web(query, max_results=3)
        
        # Crear alerta
        alert = self.alert_service.create(query=query, theme=theme)
        
        # Disparar alerta inmediatamente
        trigger_result = self.alert_service.trigger(alert.id)
        
        return {
            "alert_id": alert.id,
            "query": query,
            "theme": theme,
            "initial_results": trigger_result
        }
    
    def full_workflow(self, query: str, theme: str = None) -> Dict:
        """
        Ejecuta el flujo completo:
        1. Buscar en web
        2. Descargar documentos
        3. Generar Grieta
        4. Crear nota con análisis
        5. Crear alerta
        """
        results = {}
        
        # Paso 1: Buscar en web
        search_results = self.rag_service.search_web(query, max_results=8)
        results["search"] = search_results
        
        # Paso 2: Descargar documentos (simular descarga de los primeros 2 de cada tipo)
        doc_ids_heg = []
        doc_ids_sit = []
        
        for result in search_results[:4]:
            doc = self.rag_service.download_document(
                url=result["href"],
                source_type=result["auto_type"],
                theme=theme
            )
            if doc:
                if result["auto_type"] == "hegemonic":
                    doc_ids_heg.append(doc.id)
                else:
                    doc_ids_sit.append(doc.id)
        
        results["downloaded_docs"] = {
            "hegemonic": doc_ids_heg,
            "situated": doc_ids_sit
        }
        
        # Paso 3: Generar Grieta (si hay documentos de ambos tipos)
        if doc_ids_heg and doc_ids_sit:
            grieta_result = self.analyze_and_create_grieta(
                doc_ids_heg, doc_ids_sit, theme
            )
            results["grieta"] = grieta_result
        
        # Paso 4: Crear alerta
        alert_result = self.create_alert_from_search(query, theme)
        results["alert"] = alert_result
        
        return results
