from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, Response, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.sql import tuple_
from ..database import get_db
from ..models import Event, EventLabel, IgnoredEvent, Website
from ..auth import get_current_user
import csv
import io
from weasyprint import HTML
from pydantic import BaseModel
from typing import Optional
from uuid import UUID as py_UUID

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("")
def get_stats(
    site_id: str = Query(None), 
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    now = datetime.utcnow()
    
    # --- 1. BASE QUERY (Securely scoped to User) ---
    base_query_unfiltered = db.query(Event).join(Website).filter(
        Website.user_id == user.id
    )

    formatted_site_id = None
    if site_id:
        try:
            formatted_site_id = py_UUID(site_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid site_id format provided.")

        # IDOR Check
        website = db.query(Website).filter(
            Website.id == formatted_site_id
        ).first()

        if not website or website.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Website not found or access denied."
            )
            
        base_query_unfiltered = base_query_unfiltered.filter(
            Event.site_id == formatted_site_id
        )
    
    # --- 2. IGNORED EVENTS (MUTES) ---
    
    # Build list of User's Website IDs
    user_website_ids = db.query(Website.id).filter(Website.user_id == user.id).all()
    user_website_ids = [id[0] for id in user_website_ids]

    # 🚨 FIX: REMOVED 'IgnoredEvent.site_id.is_(None)'
    # We ONLY load mutes that belong to the user's specific sites.
    # This prevents User A's global mute from leaking to User B.
    
    if formatted_site_id:
        # Case: Specific Site Selected -> Only load mutes for this site
        ignored_patterns_query = db.query(IgnoredEvent).filter(
            IgnoredEvent.site_id == formatted_site_id
        )
    else:
        # Case: All Sites Selected -> Only load mutes for ANY of the user's sites
        # If user has no sites, this list is empty, and that's correct.
        ignored_patterns_query = db.query(IgnoredEvent).filter(
            IgnoredEvent.site_id.in_(user_website_ids)
        )

    ignored_patterns_query = ignored_patterns_query.all()
    
    ignored_tuples = [(i.element.lower(), i.original_text.lower()) for i in ignored_patterns_query]

    # Apply Mute Filter
    base_query_filtered = base_query_unfiltered
    if ignored_tuples:
        exclusion_filter = (
            tuple_(func.lower(Event.element), func.lower(Event.text)).notin_(ignored_tuples)
        )
        base_query_filtered = base_query_filtered.filter(exclusion_filter)

    # --- 3. CLICK AGGREGATION ---
    click_base_query = base_query_filtered.filter(func.lower(Event.event_type) == 'click')
    
    all_events = (
        click_base_query
        .with_entities(Event.element, Event.text, Event.page, Event.referrer, Event.timestamp)
        .order_by(Event.timestamp.desc())
        .all()
    )

    total_clicks = len(all_events)

    def count_clicks_since(days: int = 0, weeks: int = 0):
        q = click_base_query.with_entities(func.count(Event.id))
        q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0

    day_clicks = count_clicks_since(days=1)
    week_clicks = count_clicks_since(weeks=1)
    month_clicks = count_clicks_since(days=30)
    year_clicks = count_clicks_since(days=365)

    # --- Group top clicked elements ---
    grouped_query = (
        click_base_query
        .with_entities(
            Event.element,
            Event.text,
            func.count(Event.id).label("count"),
            func.max(Event.timestamp).label("last_click")
        )
        .group_by(Event.element, Event.text)
        .order_by(func.count(Event.id).desc())
    )
    grouped = grouped_query.all()

    summary = []
    for g in grouped:
        # 🚨 FIX: Same logic for Labels - REMOVED global lookup
        label_query = db.query(EventLabel).filter(
            EventLabel.element == g.element,
            EventLabel.original_text == g.text
        )
        
        if formatted_site_id:
            label_query = label_query.filter(EventLabel.site_id == formatted_site_id)
        else:
            label_query = label_query.filter(EventLabel.site_id.in_(user_website_ids))

        label = label_query.first()
        custom_text = label.custom_text if label else g.text

        summary.append({
            "element": g.element,
            "text": custom_text,
            "original_text": g.text,
            "count": g.count,
            "last_click": g.last_click.isoformat() if g.last_click else None
        })

    # --- 4. PAGE VISITS ---
    visit_base_query = base_query_unfiltered.filter(func.lower(Event.event_type) == 'page_view')
    
    def count_visits_since(days: int = 0, weeks: int = 0):
        q = visit_base_query.with_entities(func.count(Event.id))
        if days > 0 or weeks > 0:
            q = q.filter(Event.timestamp >= now - timedelta(days=days, weeks=weeks))
        return q.scalar() or 0
    
    total_visits = visit_base_query.count()
    day_visits = count_visits_since(days=1)
    week_visits = count_visits_since(weeks=1)
    month_visits = count_visits_since(days=30)
    year_visits = count_visits_since(days=365)

    return {
        "total_clicks": total_clicks, "day_clicks": day_clicks, "week_clicks": week_clicks, "month_clicks": month_clicks, "year_clicks": year_clicks,
        "total_visits": total_visits, "day_visits": day_visits, "week_visits": week_visits, "month_visits": month_visits, "year_visits": year_visits,
        "all_clicks": [{"element": e[0], "text": e[1], "page": e[2], "referrer": e[3], "timestamp": e[4].isoformat() if e[4] else None} for e in all_events],
        "all_visits": [{"page": v.page, "referrer": v.referrer, "timestamp": v.timestamp.isoformat() if v.timestamp else None} for v in visit_base_query.all()],
        "summary": summary,
    }

# ---------------- EXPORT ROUTES (Apply same filtering logic) ----------------
@router.get("/export/csv")
def export_csv(site_id: str = Query(None), db: Session = Depends(get_db), user = Depends(get_current_user)):
    # 1. Base Security
    base_query = db.query(Event).join(Website).filter(Website.user_id == user.id)
    
    # 2. Site ID Filtering
    if site_id:
        base_query = base_query.filter(Event.site_id == site_id)

    events = base_query.order_by(Event.timestamp.desc()).all()

    if not events:
        return Response(content="No events found", media_type="text/plain")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id","event_type","page","referrer","element","text","href","timestamp"])
    writer.writeheader()
    for e in events:
        writer.writerow({"id": e.id, "event_type": e.event_type, "page": e.page, "referrer": e.referrer, "element": e.element, "text": e.text, "href": e.href, "timestamp": e.timestamp.isoformat() if e.timestamp else ""})

    filename = f"events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(content=output.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={filename}"})

@router.get("/export/pdf")
def export_pdf(site_id: str = Query(None), db: Session = Depends(get_db), user = Depends(get_current_user)):
    base_query = db.query(Event).join(Website).filter(Website.user_id == user.id)
    if site_id:
        base_query = base_query.filter(Event.site_id == site_id)

    events = base_query.order_by(Event.timestamp.desc()).all()
    if not events:
        return Response(content="No events found", media_type="text/plain")

    rows = ""
    for e in events:
        rows += "<tr>" + "".join(f"<td>{v}</td>" for v in [e.id, e.event_type, e.page, e.referrer, e.element, e.text, e.href, e.timestamp.isoformat() if e.timestamp else ""]) + "</tr>"

    html = f"<html><head><meta charset='utf-8'><style>table{{border-collapse:collapse;width:100%;table-layout:fixed;}}th,td{{border:1px solid #333;padding:4px;font-size:10pt;word-wrap:break-word;}}</style></head><body><h1>Event Export</h1><table border='1' cellspacing='0' cellpadding='4'><tr><th>id</th><th>event_type</th><th>page</th><th>referrer</th><th>element</th><th>text</th><th>href</th><th>timestamp</th></tr>{rows}</table></body></html>"
    
    pdf = HTML(string=html).write_pdf()
    filename = f"events_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(content=pdf, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

# ---------------- UPDATE LABEL & MUTE (CREATION) ----------------

class LabelUpdate(BaseModel):
    site_id: str # 🚨 CHANGED: Made required (removed Optional)
    element: str
    original_text: str
    custom_text: str

@router.post("/label")
def update_label(payload: LabelUpdate, db: Session = Depends(get_db), user = Depends(get_current_user)):
    
    # 🚨 SECURITY FIX: Require valid site_id owned by user
    try:
        formatted_site_id = py_UUID(payload.site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site_id format.")

    website = db.query(Website).filter(Website.id == formatted_site_id, Website.user_id == user.id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found or access denied.")

    existing_exact = db.query(EventLabel).filter_by(site_id=formatted_site_id, element=payload.element, original_text=payload.original_text).first()
    if existing_exact and existing_exact.custom_text == payload.custom_text:
        return {"status": "ok", "custom_text": payload.custom_text}

    label = db.query(EventLabel).filter_by(site_id=formatted_site_id, element=payload.element, original_text=payload.original_text).first()

    if label:
        label.custom_text = payload.custom_text
    else:
        label = EventLabel(site_id=formatted_site_id, element=payload.element, original_text=payload.original_text, custom_text=payload.custom_text)
        db.add(label)

    db.commit()
    return {"status": "ok", "custom_text": payload.custom_text}

class EventMute(BaseModel):
    site_id: str # 🚨 CHANGED: Made required (removed Optional)
    element: str
    original_text: str

@router.post("/mute_event")
def mute_event(payload: EventMute, db: Session = Depends(get_db), user = Depends(get_current_user)):
    
    # 🚨 SECURITY FIX: Require valid site_id owned by user. Global mutes (None) are disabled.
    try:
        formatted_site_id = py_UUID(payload.site_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid site_id format.")

    website = db.query(Website).filter(Website.id == formatted_site_id, Website.user_id == user.id).first()
    if not website:
        raise HTTPException(status_code=404, detail="Website not found or access denied.")

    ignored = db.query(IgnoredEvent).filter_by(site_id=formatted_site_id, element=payload.element, original_text=payload.original_text).first()

    if ignored:
        db.delete(ignored)
        action = "unmuted"
    else:
        new_ignored = IgnoredEvent(site_id=formatted_site_id, element=payload.element, original_text=payload.original_text)
        db.add(new_ignored)
        action = "muted"
    
    db.commit()
    return {"status": "ok", "action": action}

@router.delete("/cleanup_stale_data")
def cleanup_stale_data(db: Session = Depends(get_db), user = Depends(get_current_user)):
    # Simple check to ensure only authenticated users run this (though admin check is better)
    valid_site_ids = [id[0] for id in db.query(Website.id).all()]
    
    # Delete records with invalid site_ids
    db.query(IgnoredEvent).filter(IgnoredEvent.site_id.isnot(None), IgnoredEvent.site_id.notin_(valid_site_ids)).delete(synchronize_session=False)
    db.query(EventLabel).filter(EventLabel.site_id.isnot(None), EventLabel.site_id.notin_(valid_site_ids)).delete(synchronize_session=False)
    
    # 🚨 ALSO DELETE GLOBAL ORPHANS (optional, but recommended if you want to purge old leakage)
    # db.query(IgnoredEvent).filter(IgnoredEvent.site_id.is_(None)).delete(synchronize_session=False)
    # db.query(EventLabel).filter(EventLabel.site_id.is_(None)).delete(synchronize_session=False)

    db.commit()
    return {"status": "ok", "message": "Cleanup complete"}