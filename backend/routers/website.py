# backend/routers/website.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import secrets

from ..models import Website
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/websites", tags=["websites"])

@router.post("/register")
def register_website(data: dict, db: Session = Depends(get_db), user = Depends(get_current_user)):
    # Generate a unique site_id
    site_id = secrets.token_hex(8)

    website = Website(
        site_id=site_id,
        name=data.get("name"),
        domain=data.get("domain"),
        owner=user
    )
    db.add(website)
    db.commit()
    db.refresh(website)

    snippet = f'<script src="http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/snippet/{site_id}.js"></script>'
    return {"site_id": site_id, "snippet": snippet}


@router.get("/")
def list_websites(db: Session = Depends(get_db), user = Depends(get_current_user)):
    websites = db.query(Website).filter(Website.owner == user).all()
    return [{"site_id": w.site_id, "name": w.name or w.domain} for w in websites]
