"""
Servicio de alertas para TEKIA.
Maneja alertas de seguimiento para temas de investigación.
"""
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pathlib import Path

from ..models import Alert, Document
from .rag_service import RAGService
from .note_service import NoteService
from ..config import ALERT_SERVICE_ENABLED


class AlertService:
    """Servicio para gestión de alertas."""
    
    def __init__(self, db: Session):
        self.db = db
        self.rag_service = RAGService(db)
        self.note_service = NoteService(db)
    
    def create(self, query: str, theme: str = "") -> Alert:
        """Crea una nueva alerta."""
        alert = Alert(
            query=query,
            theme=theme,
            active=True,
            created_at=datetime.utcnow()
        )
        
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        
        return alert
    
    def get(self, alert_id: int) -> Optional[Alert]:
        """Obtiene una alerta por ID."""
        return self.db.query(Alert).get(alert_id)
    
    def get_all(self, active: bool = True) -> List[Alert]:
        """Obtiene todas las alertas."""
        query = self.db.query(Alert)
        if active:
            query = query.filter(Alert.active == True)
        return query.order_by(Alert.created_at.desc()).all()
    
    def update(self, alert_id: int, query: str = None, theme: str = None, 
               active: bool = None) -> Optional[Alert]:
        """Actualiza una alerta."""
        alert = self.db.query(Alert).get(alert_id)
        if not alert:
            return None
        
        if query:
            alert.query = query
        if theme:
            alert.theme = theme
        if active is not None:
            alert.active = active
        
        self.db.commit()
        self.db.refresh(alert)
        return alert
    
    def delete(self, alert_id: int) -> bool:
        """Elimina una alerta."""
        alert = self.db.query(Alert).get(alert_id)
        if not alert:
            return False
        
        self.db.delete(alert)
        self.db.commit()
        return True
    
    def trigger(self, alert_id: int) -> Dict:
        """
        Dispara una alerta: busca nuevos documentos y notas relacionados.
        """
        alert = self.get(alert_id)
        if not alert or not alert.active:
            return {"error": "Alerta no encontrada o inactiva"}
        
        # Buscar documentos relacionados
        doc_results = self.rag_service.search_web(alert.query, max_results=5)
        
        # Buscar notas relacionadas
        note_results = self.note_service.search(alert.query, limit=5)
        
        # Marcar como disparada
        alert.last_triggered = datetime.utcnow()
        self.db.commit()
        
        return {
            "alert": alert.id,
            "query": alert.query,
            "theme": alert.theme,
            "triggered_at": alert.last_triggered.isoformat(),
            "new_documents": len(doc_results),
            "new_notes": len(note_results),
            "documents": doc_results,
            "notes": [
                {
                    "id": note.id,
                    "title": note.title,
                    "content": note.content[:200] + "..."
                }
                for note in note_results
            ]
        }
    
    def check_inactivity(self, days: int = 7) -> List[Dict]:
        """
        Verifica alertas inactivas (sin disparar en X días).
        """
        inactive_alerts = []
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        alerts = self.get_all(active=True)
        for alert in alerts:
            if alert.last_triggered and alert.last_triggered < cutoff:
                inactive_alerts.append({
                    "id": alert.id,
                    "query": alert.query,
                    "theme": alert.theme,
                    "last_triggered": alert.last_triggered,
                    "days_inactive": (datetime.utcnow() - alert.last_triggered).days
                })
        
        return inactive_alerts
    
    def trigger_all(self) -> List[Dict]:
        """Dispara todas las alertas activas."""
        alerts = self.get_all(active=True)
        results = []
        
        for alert in alerts:
            result = self.trigger(alert.id)
            results.append(result)
        
        return results
    
    def notify(self, alert_id: int) -> bool:
        """
        Envía notificación local (usando plyer).
        """
        if not ALERT_SERVICE_ENABLED:
            return False
        
        try:
            from plyer import notification
            
            alert = self.get(alert_id)
            if not alert:
                return False
            
            notification.notify(
                title=f"TEKIA - Alerta: {alert.query}",
                message=f"Nuevos resultados para tu búsqueda: {alert.query}",
                app_name="TEKIA",
                timeout=10
            )
            return True
        except Exception as e:
            print(f"Error enviando notificación: {e}")
            return False
