# app/routes/website.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Website
import uuid
from ..auth import get_current_user

router = APIRouter(prefix="/website", tags=["Websites"])

@router.post("/register")
def register_website(name: str = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    user_id = user.id
    site_id = f"site_{uuid.uuid4().hex[:8]}"

    new_site = Website(
        site_id=site_id,
        user_id=user_id,
        name=name
    )
    db.add(new_site)
    db.commit()
    db.refresh(new_site)

    snippet = f"""
    <script>
      (function() {{
        const SITE_ID = "{site_id}";
        const SCRIPT_URL = "http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/tracking.js?site_id=" + SITE_ID;
        const s = document.createElement("script");
        s.src = SCRIPT_URL;
        s.async = true;
        document.head.appendChild(s);
      }})();
    </script>
    """

    return {"site_id": site_id, "snippet": snippet}
