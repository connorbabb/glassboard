from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, List
from ..database import get_db
from ..models import Event
from datetime import datetime
from uuid import UUID as py_UUID # Standard Python UUID library

# --- Pydantic Model to enforce structure and validate incoming data ---
class IncomingEvent(BaseModel):
    site_id: str
    event_type: str = Field(alias='event_type')
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
    try:
        # The py_UUID(payload.site_id) constructor correctly formats the 32-char hex string
        # into the required hyphenated UUID object (e.g., 'xxxxxxxx-xxxx-...' )
        formatted_site_id = py_UUID(payload.site_id)
    except ValueError:
        # Return a 400 Bad Request if the site_id is not a valid 32-char hex string
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid site_id format received: '{payload.site_id}'. Expected 32-character hex."
        )

    # Convert timestamp string (like '2025-11-07T21:20:33.230Z') to datetime
    ts = datetime.utcnow()
    try:
        # Use .timestamp from the Pydantic model
        ts = datetime.fromisoformat(payload.timestamp.replace("Z", "+00:00"))
    except Exception:
        pass # Fallback to current time if parsing fails
            
    db_event = Event(
        site_id=formatted_site_id, # <-- FIX 2: Use the formatted UUID object
        event_type=payload.event_type,
        page=payload.page,
        element=payload.element,
        text=payload.text,
        href=payload.href,
        referrer=payload.referrer,
        timestamp=ts,
    )
    db.add(db_event)
    
    # Commit within the request handler is acceptable for a tracking endpoint
    db.commit() 
    return {"status": "ok"}

# Keeping reset route for convenience
@router.delete("/reset")
async def reset_events(db: Session = Depends(get_db)):
    db.query(Event).delete()
    db.commit()
    return {"status": "reset"}