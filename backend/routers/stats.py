from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Event

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("")
def get_stats(site_id: str = Query(None), db: Session = Depends(get_db)):
    now = datetime.utcnow()

    base_query = db.query(Event)
    if site_id:
        base_query = base_query.filter(Event.site_id == site_id)

    # Only include interactive elements (buttons + links)
    base_query = base_query.filter(Event.element.in_(["button", "a"]))

    # All events for this site (filtered)
    all_events = (
        base_query
        .with_entities(Event.element, Event.text, Event.page, Event.timestamp)
        .order_by(Event.timestamp.desc())
        .all()
    )

    total_clicks = len(all_events)

    def count_since(days: int = 0, weeks: int = 0):
        q = db.query(func.count(Event.id)).filter(Event.element.in_(["button", "a"]))
        if site_id:
            q = q.filter(Event.site_id == site_id)
        q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0

    day_clicks = count_since(days=1)
    week_clicks = count_since(weeks=1)
    month_clicks = count_since(days=30)
    year_clicks = count_since(days=365)

    # Grouped summary (still filtered)
    grouped_query = (
        db.query(Event.element, Event.text, func.count(Event.id).label("count"))
        .filter(Event.element.in_(["button", "a"]))
    )
    if site_id:
        grouped_query = grouped_query.filter(Event.site_id == site_id)

    grouped = (
        grouped_query
        .group_by(Event.element, Event.text)
        .order_by(func.count(Event.id).desc())
        .all()
    )

    return {
        "total_clicks": total_clicks,
        "day_clicks": day_clicks,
        "week_clicks": week_clicks,
        "month_clicks": month_clicks,
        "year_clicks": year_clicks,
        "all_clicks": [
            {
                "element": e[0],
                "text": e[1],
                "page": e[2],
                "timestamp": e[3].isoformat() if e[3] else None
            }
            for e in all_events
        ],
        "summary": [
            {"element": g[0], "text": g[1], "count": g[2]}
            for g in grouped
        ],
    }
