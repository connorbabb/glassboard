from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from .. import models

router = APIRouter(prefix="/stats", tags=["Stats"])

@router.get("")
def get_stats(db: Session = Depends(get_db)):
    total_clicks = db.query(models.Event).count()
    top_elements = (
        db.query(models.Event.element, func.count(models.Event.id).label("count"))
        .group_by(models.Event.element)
        .order_by(func.count(models.Event.id).desc())
        .limit(3)
        .all()
    )
    return {
        "total_clicks": total_clicks,
        "top_elements": [{"element": e, "count": c} for e, c in top_elements]
    }
