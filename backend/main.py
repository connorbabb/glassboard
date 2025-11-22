# backend/main.py

from fastapi import FastAPI, Request, Depends
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .auth import get_current_user

from .routers import events, stats, website
from .models import Base, User
from .database import engine, get_db
from sqlalchemy import text

import os

from .auth import router as auth_router
from .routers.website import router as website_router


# Create tables
Base.metadata.create_all(bind=engine)

# Create app
app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend"))
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

# API routers
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(website_router)
app.include_router(auth_router)

@app.get("/")
def root():
    return RedirectResponse(url="/frontend/login.html")


@app.get("/snippet/{site_id}.js", response_class=PlainTextResponse)
def tracking_snippet(site_id: str):
    js_code = f"""
    (function() {{
        const SITE_ID = "{site_id}";
        const BASE_URL = window.location.origin; // dynamically uses current host

        document.addEventListener('click', async (event) => {{
            const target = event.target;
            if (target.tagName === 'BUTTON' || target.tagName === 'A') {{
                const payload = {{
                    site_id: SITE_ID,
                    element: target.tagName.toLowerCase(),
                    text: target.textContent.trim(),
                    page: window.location.pathname,
                    timestamp: new Date().toISOString()
                }};
                try {{
                    await fetch(`${{BASE_URL}}/events/`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{ site_id: SITE_ID, events: [payload] }})
                    }});
                    console.log('Sent click event:', payload);
                }} catch (err) {{
                    console.error('Tracking failed:', err);
                }}
            }}
        }});
    }})();
    """
    return js_code


@app.get("/test-db")
def test_db():
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()
            return {"status": "connected", "version": version[0]}
    except Exception as e:
        return {"status": "failed", "error": str(e)}

@app.get("/dashboard")
def dashboard(request: Request, user=Depends(get_current_user)):
    return RedirectResponse(url="/frontend/index.html")
