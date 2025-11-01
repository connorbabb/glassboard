from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from datetime import datetime

router = APIRouter(prefix="/events", tags=["Events"])

@router.delete("/reset")
def reset_events(db: Session = Depends(get_db)):
    deleted = db.query(models.Event).delete()
    db.commit()
    return {"status": "ok", "deleted_rows": deleted}

from datetime import datetime

@router.post("/")
def create_event(payload: schemas.EventCreate, db: Session = Depends(get_db)):
    print("Received batch:", payload.dict())
    for event in payload.events:
        timestamp_str = event.get("timestamp")
        timestamp = None
        
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        new_event = models.Event(
            site_id=payload.site_id,
            page=event["page"],
            element=event["element"],
            event_type=event["type"],
            timestamp=timestamp
        )
        db.add(new_event)

    db.commit()
    return {"message": "Events stored successfully"}
