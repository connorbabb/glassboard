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

    # --- REUSABLE BASE QUERY (Filtered ONLY by site_id) ---
    base_query_unfiltered = db.query(Event)
    if site_id:
        base_query_unfiltered = base_query_unfiltered.filter(Event.site_id == site_id)

    # =========================================================================
    # --- 1. CLICK AGGREGATION ---
    # =========================================================================

    # Clicks: Filtered by interactive elements (buttons and links)
    click_base_query = base_query_unfiltered.filter(Event.element.in_(["button", "a"]))

    # All click events for the "all_clicks" list
    all_events = (
        click_base_query
        .with_entities(Event.element, Event.text, Event.page, Event.referrer, Event.timestamp)
        .order_by(Event.timestamp.desc())
        .all()
    )

    total_clicks = len(all_events)

    # Function to count Clicks since a given time period
    def count_clicks_since(days: int = 0, weeks: int = 0):
        q = click_base_query.with_entities(func.count(Event.id))
        q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0

    day_clicks = count_clicks_since(days=1)
    week_clicks = count_clicks_since(weeks=1)
    month_clicks = count_clicks_since(days=30)
    year_clicks = count_clicks_since(days=365)

    # Grouped summary (Top Clicked Elements)
    grouped_query = (
        click_base_query
        .with_entities(Event.element, Event.text, func.count(Event.id).label("count"))
        .group_by(Event.element, Event.text)
        .order_by(func.count(Event.id).desc())
    )
    grouped = grouped_query.all()


    # =========================================================================
    # --- 2. PAGE VISIT AGGREGATION (NEW) ---
    # =========================================================================

    # Visits: Filtered by event_type == 'page_view'
    visit_base_query = base_query_unfiltered.filter(Event.event_type == 'page_view')

    # Function to count Page Visits since a given time period
    def count_visits_since(days: int = 0, weeks: int = 0):
        q = visit_base_query.with_entities(func.count(Event.id))
        q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0
    
    total_visits = visit_base_query.count() # Total all-time page views
    day_visits = count_visits_since(days=1)
    week_visits = count_visits_since(weeks=1)
    month_visits = count_visits_since(days=30)
    year_visits = count_visits_since(days=365)


    # --- FINAL RESPONSE ---
    return {
        # Click Metrics
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

        # Detailed Data
        "all_clicks": [
        {
            "element": e[0],
            "text": e[1],
            "page": e[2],
            "referrer": e[3],
            "timestamp": e[4].isoformat() if e[4] else None
        }
        for e in all_events
    ],

        
        # Summary for Chart
        "summary": [
            {"element": g[0], "text": g[1], "count": g[2]}
            for g in grouped
        ],
    }