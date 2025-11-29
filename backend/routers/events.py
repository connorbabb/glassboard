from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from ..database import get_db
from ..models import Event
from datetime import datetime

# --- Pydantic Model to enforce structure and validate incoming data ---
# This ensures that all required fields are present and typed correctly.
class IncomingEvent(BaseModel):
    site_id: str
    event_type: str = Field(alias='event_type') # Matches JS key
    timestamp: str
    page: str
    referrer: Optional[str] = None
    element: Optional[str] = None
    text: Optional[str] = None
    href: Optional[str] = None

# Renaming router prefix to /track for clarity
router = APIRouter(prefix="/track", tags=["Tracking"])

@router.post("/")
async def record_single_event(payload: IncomingEvent, db: Session = Depends(get_db)):
    """
    Handles a single event payload sent directly from the JS snippet.
    """
    
    # Convert timestamp string (like '2025-11-07T21:20:33.230Z') to datetime
    ts = datetime.utcnow()
    try:
        # Use .timestamp from the Pydantic model
        ts = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
    except Exception:
        pass # Fallback to current time if parsing fails
            
    db_event = Event(
        site_id=payload.site_id,
        event_type=payload.event_type, # <-- Correct key from Pydantic model
        page=payload.page,
        element=payload.element,
        text=payload.text,
        href=payload.href,
        timestamp=ts,
    )
    db.add(db_event)
    
    # Commit within the request handler is acceptable for a tracking endpoint
    # to ensure data persistence immediately.
    db.commit() 
    return {"status": "ok"}


# Keeping reset route for convenience (you might move this to /events or /admin)
@router.delete("/reset")
async def reset_events(db: Session = Depends(get_db)):
    db.query(Event).delete()
    db.commit()
    return {"status": "reset"}