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
from uuid import UUID as py_UUID # Import the standard Python UUID type

router = APIRouter(prefix="/stats", tags=["Stats"])

# In backend/routers/stats.py

# In backend/routers/stats.py (inside get_stats)

@router.get("")
def get_stats(
    site_id: str = Query(None), 
    db: Session = Depends(get_db),
    user = Depends(get_current_user)  # The logged-in User object
):
    now = datetime.utcnow()
    
    # -----------------------------------------------------------------
    # --- 1. SET UP SECURE BASE QUERY AND IDOR CHECK ---
    # -----------------------------------------------------------------

    # **STEP 1: Start with the most secure, user-scoped query.**
    # This query ensures ALL subsequent steps are limited to the user's data.
    # Use Website.owner_id == user.id for maximum robustness.
    # If the user has no sites, this returns an empty set of Events.
    base_query_unfiltered = db.query(Event).join(Website).filter(
        Website.user_id == user.id
    )

    formatted_site_id = None
    
    if site_id:
        try:
            formatted_site_id = py_UUID(site_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid site_id format provided.")

        # **STEP 2: IDOR Check (Required for site_id)**
        website = db.query(Website).filter(
            Website.id == formatted_site_id
        ).first()

        if not website or website.user_id != user.id: # Note: Use .owner_id here too
            # This handles unauthorized access to a specific site.
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Website not found or access denied."
            )
            
        # **STEP 3: Apply site_id filter to the already secure query.**
        base_query_unfiltered = base_query_unfiltered.filter(
            Event.site_id == formatted_site_id
        )
    
    # At this point, base_query_unfiltered is GUARANTEED to be:
    # A) All events for all user's sites (if site_id is None) OR
    # B) All events for the single, authorized site (if site_id is present).

    # -----------------------------------------------------------------
    # --- 2. CONTINUE WITH IGNORED EVENTS / BASE QUERY FILTERED ---
    # -----------------------------------------------------------------
    
    # Build a list of Website IDs owned by the current user.
    user_website_ids = db.query(Website.id).filter(Website.user_id == user.id).all()
    user_website_ids = [id[0] for id in user_website_ids] # CORRECT: list of uuid.UUID objects

    if formatted_site_id:
        # Case: Specific Authorized Site Selected
        # We only want mutes that are Global OR are for this specific site.
        ignored_patterns_query = db.query(IgnoredEvent).filter(
            (IgnoredEvent.site_id.is_(None)) | 
            (IgnoredEvent.site_id == formatted_site_id)
        )
    else:
        # Case: All Sites Selected
        # We want mutes that are Global OR are for ANY of the user's sites.
        ignored_patterns_query = db.query(IgnoredEvent).filter(
            (IgnoredEvent.site_id.is_(None)) | 
            (IgnoredEvent.site_id.in_(user_website_ids))
        )

    ignored_patterns_query = ignored_patterns_query.all()
    
    # Convert ignored patterns to a list of tuples for exclusion filtering
    ignored_tuples = [(i.element.lower(), i.original_text.lower()) for i in ignored_patterns_query]

    # **CRITICAL: Remove the entire block that starts with `base_query_unfiltered = db.query(Event)`**
    # The variable is already correctly filtered from Step 1!

    base_query_filtered = base_query_unfiltered # Start applying the ignored filter here

    if ignored_tuples:
        # Create a list of tuples of (element, text) to exclude
        exclusion_filter = (
            tuple_(func.lower(Event.element), func.lower(Event.text)).notin_(ignored_tuples)
        )
        base_query_filtered = base_query_filtered.filter(exclusion_filter)

    # ... The rest of the function (Aggregation) now uses the SECURE `base_query_filtered`
    # =========================================================================
    # --- 1. CLICK AGGREGATION ---
    # =========================================================================

    # Clicks: Filtered by interactive elements (buttons and links)
    click_base_query = base_query_filtered.filter(func.lower(Event.event_type) == 'click')
    
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

# In backend/routers/stats.py (inside the loop for 'grouped' stats)

    summary = []
    for g in grouped:
        # 1. Start by querying EventLabel
        label_query = db.query(EventLabel) 
        
        # 2. Filter by the element and text
        label_query = label_query.filter(
            EventLabel.element == g.element,
            EventLabel.original_text == g.text
        )
        
        if formatted_site_id:
            # Case: Specific Authorized Site Selected
            # We only want labels that are Global OR are for this specific site.
            label_query = label_query.filter(
                (EventLabel.site_id.is_(None)) | 
                (EventLabel.site_id == formatted_site_id)
            )
        else:
            # Case: All Sites Selected
            # We want labels that are Global OR are for ANY of the user's sites.
            label_query = label_query.filter(
                (EventLabel.site_id.is_(None)) | 
                (EventLabel.site_id.in_(user_website_ids))
            )

        label = label_query.first()
        
        custom_text = label.custom_text if label else g.text

        summary.append({
            "element": g.element,
            "text": custom_text, 
            "original_text": g.text, 
            "count": g.count,
            "last_click": g.last_click.isoformat() if g.last_click else None
        })



    # =========================================================================
    # --- 2. PAGE VISIT AGGREGATION (NEW) ---
    # =========================================================================

    # Visits: Filtered by event_type == 'page_view'
    visit_base_query = base_query_unfiltered.filter(func.lower(Event.event_type) == 'page_view')
    total_visits = visit_base_query.count() # Total all-time page views

    # Function to count Page Visits since a given time period
    def count_visits_since(days: int = 0, weeks: int = 0):
        # This function correctly uses the pre-filtered visit_base_query
        q = visit_base_query.with_entities(func.count(Event.id))
        
        # Only filter by time period if a time limit is provided
        if days > 0 or weeks > 0:
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

    "summary": summary,
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
            <head>
                <meta charset="utf-8">
                <style>
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                        table-layout: fixed; /* Force fixed column widths */
                    }}
                    th, td {{
                        border: 1px solid #333;
                        padding: 4px;
                        font-size: 10pt;
                        word-wrap: break-word; /* Allow text to wrap */
                    }}
                </style>
            </head>
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
    

class LabelUpdate(BaseModel):
    site_id: Optional[str]
    element: str
    original_text: str
    custom_text: str

@router.post("/label")
def update_label(
    payload: LabelUpdate, 
    db: Session = Depends(get_db),
    user = Depends(get_current_user) # <-- CRITICAL: Dependency added
):
    
    # --- IDOR CHECK & SITE_ID VALIDATION ---
    formatted_site_id = None
    if payload.site_id:
        try:
            # 1. Validate the incoming site_id format and convert to UUID object
            formatted_site_id = py_UUID(payload.site_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid site_id format provided.")
            
        # 2. CRITICAL SECURITY CHECK: Ensure the site exists AND belongs to the user
        website = db.query(Website).filter(
            Website.id == formatted_site_id,
            Website.user_id == user.id 
        ).first()
        
        if not website:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Website not found or access denied."
            )
    # --- END IDOR CHECK ---

    # 1️⃣ Check for duplicate custom_text for this site
    # Note: Using formatted_site_id instead of payload.site_id
    existing_exact = db.query(EventLabel).filter_by(
        site_id=formatted_site_id, # <-- Using the validated UUID object
        element=payload.element,
        original_text=payload.original_text
    ).first()

    # If exact match exists and custom text is unchanged, OK
    if existing_exact and existing_exact.custom_text == payload.custom_text:
        return {"status": "ok", "custom_text": payload.custom_text}

    # 2️⃣ Fetch the current label (if any)
    label = (
        db.query(EventLabel)
        .filter_by(
            site_id=formatted_site_id, # <-- Using the validated UUID object
            element=payload.element,
            original_text=payload.original_text
        )
        .first()
    )

    if label:
        label.custom_text = payload.custom_text
    else:
        label = EventLabel(
            site_id=formatted_site_id, # <-- Using the validated UUID object
            element=payload.element,
            original_text=payload.original_text,
            custom_text=payload.custom_text
        )
        db.add(label)

    db.commit()
    return {"status": "ok", "custom_text": payload.custom_text}


# Insert this route in your stats router or a new admin router

class EventMute(BaseModel):
    site_id: Optional[str] # The site this mute applies to (can be null for global)
    element: str
    original_text: str

@router.post("/mute_event")
def mute_event(
    payload: EventMute, 
    db: Session = Depends(get_db),
    user = Depends(get_current_user) # ✅ ADDED: Get current user
):
    
    # --- IDOR CHECK ---
    formatted_site_id = None
    if payload.site_id:
        try:
            formatted_site_id = py_UUID(payload.site_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid site_id format provided.")
            
        # Check if the site exists AND belongs to the user
        website = db.query(Website).filter(
            Website.id == formatted_site_id,
            Website.user_id == user.id # ✅ CRITICAL IDOR CHECK
        ).first()
        
        if not website:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="Website not found or access denied."
            )
    # --- END IDOR CHECK ---
    
    # Check if the event pattern is already muted
    # Use the validated/formatted UUID here
    ignored = db.query(IgnoredEvent).filter_by(
        site_id=formatted_site_id, # Use validated/formatted ID
        element=payload.element,
        original_text=payload.original_text
    ).first()

    if ignored:
        # If found, UNMUTE (delete the record)
        db.delete(ignored)
        action = "unmuted"
    else:
        # If not found, MUTE (add the record)
        new_ignored = IgnoredEvent(
            site_id=formatted_site_id, # Use validated/formatted ID
            element=payload.element,
            original_text=payload.original_text
        )
        db.add(new_ignored)
        action = "muted"
    
    db.commit()
    return {"status": "ok", "action": action}

# Insert this new route anywhere in the file (e.g., just before /label)
@router.delete("/cleanup_stale_data")
def cleanup_stale_data(db: Session = Depends(get_db)):
    """
    Deletes IgnoredEvent and EventLabel records that refer to non-existent sites.
    (This is typically run by an admin/owner but is crucial for fixing pre-IDOR-fix data.)
    """
    
    # 1. Get all current, valid site IDs from the Website table
    valid_site_ids = db.query(Website.id).all()
    # Convert list of tuples to a flat list of UUIDs
    valid_site_ids = [id[0] for id in valid_site_ids] 
    
    # --- Cleanup IgnoredEvents (Mutes) ---
    
    # Identify records that have a site_id but that site_id is NOT in the list of valid sites
    stale_mutes_query = db.query(IgnoredEvent).filter(
        IgnoredEvent.site_id.isnot(None),
        IgnoredEvent.site_id.notin_(valid_site_ids)
    )
    
    deleted_mutes_count = stale_mutes_query.delete(synchronize_session=False)

    # --- Cleanup EventLabels (Nicknames) ---

    # Identify records that have a site_id but that site_id is NOT in the list of valid sites
    stale_labels_query = db.query(EventLabel).filter(
        EventLabel.site_id.isnot(None),
        EventLabel.site_id.notin_(valid_site_ids)
    )

    deleted_labels_count = stale_labels_query.delete(synchronize_session=False)

    db.commit()
    
    return {
        "status": "ok", 
        "message": "Stale data cleanup complete.",
        "deleted_ignored_events": deleted_mutes_count,
        "deleted_event_labels": deleted_labels_count
    }