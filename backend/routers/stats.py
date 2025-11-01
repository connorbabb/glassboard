from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from ..database import get_db
from .. import models

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("")
def get_stats(
    site_id: str | None = Query(None, description="The site_id to get stats for"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Event)
    
    if site_id:
        query = query.filter(models.Event.site_id == site_id)
    
    total_clicks = query.count()

    # Example for last_day
    now = datetime.utcnow()
    last_day = now - timedelta(days=1)
    events_last_day = query.filter(models.Event.timestamp >= last_day).count()

    # Repeat for last_week, last_month, etc.
    top_elements = (
        query
        .with_entities(models.Event.element, func.count(models.Event.id).label("count"))
        .group_by(models.Event.element)
        .order_by(func.count(models.Event.id).desc())
        .limit(3)
        .all()
    )

    return {
        "site_id": site_id or "all",
        "total_clicks": total_clicks,
        "events_last_24h": events_last_day,
        # ... last_week, last_month, last_year ...
        "top_elements": [{"element": e, "count": c} for e, c in top_elements]
    }