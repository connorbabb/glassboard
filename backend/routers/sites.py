# backend/routers/sites.py
from fastapi import APIRouter
from ..models import Site  # assuming you have this model
from ..database import get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/sites", tags=["Sites"])

@router.get("/")
def get_sites(db: Session = Depends(get_db)):
    # Later you’ll filter this by the logged-in user’s ID
    sites = db.query(Site).all()
    return [{"id": s.id, "site_id": s.site_id, "domain": s.domain} for s in sites]
