from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Event # Assuming Event model has 'event_type' and 'site_id' fields

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("")
def get_stats(site_id: str = Query(None), db: Session = Depends(get_db)):
    now = datetime.utcnow()

    # --- REUSABLE QUERY BUILDER FOR CLICKS ---
    # Clicks are defined as events where element is 'button' or 'a'
    def click_query_builder(session_db):
        q = session_db.query(Event).filter(Event.event_type == 'click')
        q = q.filter(Event.element.in_(["button", "a"]))
        if site_id:
            q = q.filter(Event.site_id == site_id)
        return q

    # --- REUSABLE QUERY BUILDER FOR PAGE VISITS ---
    # Visits are defined as events where event_type is 'page_view'
    def visit_query_builder(session_db):
        q = session_db.query(Event).filter(Event.event_type == 'page_view')
        if site_id:
            q = q.filter(Event.site_id == site_id)
        return q

    # --- 1. CLICK AGGREGATION ---
    
    # Function to count clicks since a given time period
    def count_clicks_since(days: int = 0, weeks: int = 0):
        q = click_query_builder(db).with_entities(func.count(Event.id))
        q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0

    total_clicks = click_query_builder(db).count() # Total all-time clicks
    day_clicks = count_clicks_since(days=1)
    week_clicks = count_clicks_since(weeks=1)
    month_clicks = count_clicks_since(days=30)
    year_clicks = count_clicks_since(days=365)

    # All click events for the 'all_clicks' list
    all_click_events = (
        click_query_builder(db)
        .with_entities(Event.element, Event.text, Event.page, Event.timestamp)
        .order_by(Event.timestamp.desc())
        .all()
    )

    # Grouped summary (Top Clicked Elements)
    grouped_clicks_query = (
        click_query_builder(db)
        .with_entities(Event.element, Event.text, func.count(Event.id).label("count"))
        .group_by(Event.element, Event.text)
        .order_by(func.count(Event.id).desc())
    )
    grouped_clicks = grouped_clicks_query.all()


    # =========================================================================
    # --- 2. PAGE VISIT AGGREGATION (NEW) ---
    # =========================================================================

    # Function to count page visits since a given time period
    def count_visits_since(days: int = 0, weeks: int = 0):
        q = visit_query_builder(db).with_entities(func.count(Event.id))
        q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0

    total_visits = visit_query_builder(db).count() # Total all-time page views
    day_visits = count_visits_since(days=1)
    week_visits = count_visits_since(weeks=1)
    month_visits = count_visits_since(days=30)
    year_visits = count_visits_since(days=365)


    # --- FINAL RESPONSE ---
    return {
        # Click Metrics (Existing)
        "total_clicks": total_clicks,
        "day_clicks": day_clicks,
        "week_clicks": week_clicks,
        "month_clicks": month_clicks,
        "year_clicks": year_clicks,

        # Page Visit Metrics (NEW)
        "total_visits": total_visits,
        "day_visits": day_visits,
        "week_visits": week_visits,
        "month_visits": month_visits,
        "year_visits": year_visits,

        # Detailed Click Data (Existing)
        "all_clicks": [
            {
                "element": e[0],
                "text": e[1],
                "page": e[2],
                "timestamp": e[3].isoformat() if e[3] else None
            }
            for e in all_click_events
        ],
        
        # Summary for Chart (Top Clicked Elements) (Existing)
        "summary": [
            {"element": g[0], "text": g[1], "count": g[2]}
            for g in grouped_clicks
        ],
    }