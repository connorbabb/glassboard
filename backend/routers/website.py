# backend/routers/website.py

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session  
from sqlalchemy import func
import secrets

from ..database import get_db
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

@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_website(
    identifier: str, # The domain or name provided by the user
    db: Session = Depends(get_db)
):
    """
    Deletes a website and all associated events, labels, and ignored patterns.
    The website is identified by its domain or its friendly name (case-insensitive).
    """
    
    # 1. Find the website by domain or name (case-insensitive search)
    # We use func.lower() on both sides to ensure a robust match
    website = db.query(Website).filter(
        (func.lower(Website.domain) == func.lower(identifier)) |
        (func.lower(Website.name) == func.lower(identifier))
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Website with identifier '{identifier}' not found."
        )

    # 2. Delete the website object
    # The 'cascade' rule in models.py handles the deletion of all related data
    db.delete(website)
    db.commit()

    # 3. Return 204 No Content
    return Response(status_code=status.HTTP_204_NO_CONTENT)