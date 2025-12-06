from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Event
import csv
import io
from weasyprint import HTML

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
        .with_entities(
            Event.element,
            Event.text,
            func.count(Event.id).label("count"),
            func.max(Event.timestamp).label("last_click")  # ← Add this
        )
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

        "all_visits": [
        {
            "page": v.page,
            "referrer": v.referrer,
            "timestamp": v.timestamp.isoformat() if v.timestamp else None
        }
        for v in visit_base_query.all()
    ],

        # Summary for Chart
        "summary": [
        {
            "element": g[0],
            "text": g[1],
            "count": g[2],
            "last_click": g[3].isoformat() if g[3] else None
        }
        for g in grouped
    ],

    }

# ---------------- CSV Export Route ----------------
@router.get("/export/csv")
def export_csv(site_id: str = Query(None), db: Session = Depends(get_db)):
    base_query = db.query(Event)
    if site_id:
        base_query = base_query.filter(Event.site_id == site_id)

    events = base_query.order_by(Event.timestamp.desc()).all()

    if not events:
        return Response(content="No events found", media_type="text/plain")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id","event_type","page","referrer","element","text","href","timestamp"])
    writer.writeheader()

    for e in events:
        writer.writerow({
            "id": e.id,
            "event_type": e.event_type,
            "page": e.page,
            "referrer": e.referrer,
            "element": e.element,
            "text": e.text,
            "href": e.href,
            "timestamp": e.timestamp.isoformat() if e.timestamp else ""
        })

    filename = f"events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ---------------- PDF Export Route ----------------
@router.get("/export/pdf")
def export_pdf(site_id: str = Query(None), db: Session = Depends(get_db)):
    base_query = db.query(Event)
    if site_id:
        base_query = base_query.filter(Event.site_id == site_id)

    events = base_query.order_by(Event.timestamp.desc()).all()

    if not events:
        return Response(content="No events found", media_type="text/plain")

    # Build simple HTML table
    rows = ""
    for e in events:
        rows += "<tr>" + "".join(
            f"<td>{v}</td>" for v in [
                e.id, e.event_type, e.page, e.referrer, e.element, e.text, e.href,
                e.timestamp.isoformat() if e.timestamp else ""
            ]
        ) + "</tr>"

    html = f"""
    <html>
        <head><meta charset="utf-8"></head>
        <body>
            <h1>Event Export</h1>
            <table border="1" cellspacing="0" cellpadding="4">
                <tr>
                    <th>id</th><th>event_type</th><th>page</th><th>referrer</th>
                    <th>element</th><th>text</th><th>href</th><th>timestamp</th>
                </tr>
                {rows}
            </table>
        </body>
    </html>
    """

    pdf = HTML(string=html).write_pdf()
    filename = f"events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )