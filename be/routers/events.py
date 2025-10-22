from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db


router = APIRouter(prefix="/events", tags=["Events"])

@router.delete("/reset")
def reset_events(db: Session = Depends(get_db)):
    deleted = db.query(models.Event).delete()
    db.commit()
    return {"status": "ok", "deleted_rows": deleted}

@router.post("/")
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    print("Received batch:", payload.dict())
    for event in payload.events:
        new_event = models.Event(
            site_id=payload.site_id,
            page=event["page"],
            element=event["element"],
            event_type=event["type"],
        )
        db.add(new_event)
    db.commit()
    return {"message": "Events stored successfully"}
