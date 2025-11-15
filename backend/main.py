# backend/main.py

from fastapi import FastAPI, Request, Depends
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from .auth import get_current_user

from .routers import events, stats, snippet
from .models import Base, User
from .database import engine, get_db
from sqlalchemy import text

import os

# Import the auth router
from .auth import router as auth_router


# Create tables
Base.metadata.create_all(bind=engine)

# Create app
app = FastAPI()

# Attach auth routes
app.include_router(auth_router)

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
app.mount("/frontend", StaticFiles(directory=frontend_path, html=True), name="frontend")

# API routers
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(snippet.router)


@app.get("/")
def root():
    return {"message": "Glassboard backend running!"}


@app.get("/snippet/{site_id}.js", response_class=PlainTextResponse)
def tracking_snippet(site_id: str):
    js_code = f"""
    document.addEventListener('click', async (event) => {{
        const target = event.target;
        if (target.tagName === 'BUTTON' || target.tagName === 'A') {{
            const payload = {{
                site_id: "{site_id}",
                element: target.tagName.toLowerCase(),
                text: target.textContent.trim(),
                page: window.location.pathname
            }};
            try {{
                await fetch('http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/events/', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ site_id: "{site_id}", events: [payload] }})
                }});
                console.log('Sent click event:', payload);
            }} catch (err) {{
                console.error('Error sending click event:', err);
            }}
        }}
    }});
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
