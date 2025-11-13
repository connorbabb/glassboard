from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Event
from datetime import datetime

router = APIRouter(prefix="/events", tags=["Events"])

@router.post("/")
async def record_events(data: dict, db: Session = Depends(get_db)):
    site_id = data.get("site_id")
    events = data.get("events", [])

    for e in events:
        # Convert timestamp string (like '2025-11-07T21:20:33.230Z') to datetime
        ts = None
        if e.get("timestamp"):
            try:
                ts = datetime.fromisoformat(e.get("timestamp").replace("Z", "+00:00"))
            except Exception:
                ts = datetime.utcnow()  # fallback if parsing fails
                
        db_event = Event(
            site_id=site_id,
            page=e.get("page"),
            element=e.get("element"),
            text=e.get("text"),      # 👈 store text
            href=e.get("href"),      # 👈 store href
            event_type=e.get("type"),
            timestamp=ts,            # 👈 use parsed datetime, not raw string
        )
        db.add(db_event)

    db.commit()
    return {"status": "ok"}


@router.delete("/reset")
async def reset_events(db: Session = Depends(get_db)):
    db.query(Event).delete()
    db.commit()
    return {"status": "reset"}
