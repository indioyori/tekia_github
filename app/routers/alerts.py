"""
Router para endpoints de Alertas.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services.alert_service import AlertService
from ..models import Alert

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


@router.post("/")
def create_alert(
    query: str,
    theme: str = "",
    db: Session = Depends(get_db)
):
    """Crea una nueva alerta."""
    service = AlertService(db)
    alert = service.create(query, theme)
    
    return {
        "id": alert.id,
        "query": alert.query,
        "theme": alert.theme,
        "active": alert.active,
        "created_at": alert.created_at.isoformat()
    }


@router.get("/{alert_id}")
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Obtiene una alerta por ID."""
    service = AlertService(db)
    alert = service.get(alert_id)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {
        "id": alert.id,
        "query": alert.query,
        "theme": alert.theme,
        "active": alert.active,
        "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None,
        "created_at": alert.created_at.isoformat()
    }


@router.get("/")
def list_alerts(active: bool = True, db: Session = Depends(get_db)):
    """Lista todas las alertas."""
    service = AlertService(db)
    alerts = service.get_all(active)
    
    return [
        {
            "id": alert.id,
            "query": alert.query,
            "theme": alert.theme,
            "active": alert.active,
            "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None
        }
        for alert in alerts
    ]


@router.put("/{alert_id}")
def update_alert(
    alert_id: int,
    query: str = None,
    theme: str = None,
    active: bool = None,
    db: Session = Depends(get_db)
):
    """Actualiza una alerta."""
    service = AlertService(db)
    alert = service.update(alert_id, query, theme, active)
    
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {
        "id": alert.id,
        "query": alert.query,
        "theme": alert.theme,
        "active": alert.active
    }


@router.delete("/{alert_id}")
def delete_alert(alert_id: int, db: Session = Depends(get_db)):
    """Elimina una alerta."""
    service = AlertService(db)
    success = service.delete(alert_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    
    return {"status": "ok", "message": "Alerta eliminada"}


@router.post("/{alert_id}/trigger")
def trigger_alert(alert_id: int, db: Session = Depends(get_db)):
    """Dispara una alerta manualmente."""
    service = AlertService(db)
    result = service.trigger(alert_id)
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return result


@router.post("/trigger-all/")
def trigger_all_alerts(db: Session = Depends(get_db)):
    """Dispara todas las alertas activas."""
    service = AlertService(db)
    results = service.trigger_all()
    
    return {
        "triggered": len(results),
        "results": results
    }


@router.get("/inactive/")
def list_inactive_alerts(days: int = 7, db: Session = Depends(get_db)):
    """Lista alertas inactivas (sin disparar en X días)."""
    service = AlertService(db)
    inactive = service.check_inactivity(days)
    
    return {"inactive_alerts": inactive}


@router.post("/{alert_id}/notify")
def notify_alert(alert_id: int, db: Session = Depends(get_db)):
    """Envía notificación local para una alerta."""
    service = AlertService(db)
    success = service.notify(alert_id)
    
    if not success:
        raise HTTPException(status_code=400, detail="Error enviando notificación")
    
    return {"status": "ok", "message": "Notificación enviada"}
