from fastapi import FastAPI, Request, Depends
from fastapi.responses import PlainTextResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from auth import get_current_user
from routers import events, stats
from models import Base
from database import engine, get_db
from sqlalchemy import text

import os

# Import routers - ensuring correct paths
from auth import router as auth_router
from routers.website import router as website_router

# Create tables
Base.metadata.create_all(bind=engine)

# Create app
app = FastAPI()

# --- 1. FIXED CORS SETTINGS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "https://glassboard-hjhr.onrender.com", # Your Live URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 2. IMPROVED FRONTEND MOUNTING ---
# We are checking two common locations where Render might put the folder
current_dir = os.path.dirname(os.path.abspath(__file__)) # /backend
parent_dir = os.path.dirname(current_dir)                # / (root)

# Location 1: /frontend (sibling to backend)
path_option_1 = os.path.join(parent_dir, "frontend")
# Location 2: /backend/frontend (inside backend)
path_option_2 = os.path.join(current_dir, "frontend")

if os.path.exists(path_option_1):
    print(f"DEBUG: Found frontend at {path_option_1}")
    app.mount("/frontend", StaticFiles(directory=path_option_1), name="frontend")
elif os.path.exists(path_option_2):
    print(f"DEBUG: Found frontend at {path_option_2}")
    app.mount("/frontend", StaticFiles(directory=path_option_2), name="frontend")
else:
    # This will print in your Render logs so we can see the actual path
    print(f"DEBUG: Frontend NOT found. Looked in: {path_option_1} and {path_option_2}")
    print(f"DEBUG: Files in root: {os.listdir(parent_dir)}")

# API routers
app.include_router(events.router)
app.include_router(stats.router)
app.include_router(website_router)
app.include_router(auth_router)

@app.get("/")
def root():
    # Redirect to the login page in the frontend folder
    return RedirectResponse(url="/frontend/login.html")

# --- 3. FIXED TRACKING SNIPPET URL ---
@app.get("/snippet/{site_id}.js", response_class=PlainTextResponse)
def tracking_snippet(site_id: str):
    # This snippet now points to your LIVE Render backend
    js_code = f"""
        (function() {{
            const SITE_ID = "{site_id}";
            const TRACKING_ENDPOINT = 'https://glassboard-hjhr.onrender.com/track/'; 

            function sendEvent(eventType, elementDetails = {{}}) {{
                const payload = {{
                    site_id: SITE_ID,
                    event_type: eventType,
                    timestamp: new Date().toISOString(),
                    page: window.location.pathname,
                    referrer: document.referrer || null,
                    element: elementDetails.element || null,
                    text: elementDetails.text || null,
                    href: elementDetails.href || null,
                }};

                fetch(TRACKING_ENDPOINT, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify(payload),
                }})
                .then(res => res.json())
                .catch(err => console.error("Glassboard Tracking failed:", err));
            }}

            sendEvent('page_view');

            document.addEventListener("click", (e) => {{
                let element = e.target;
                while (element && element.tagName !== 'BUTTON' && element.tagName !== 'A' && element.tagName !== 'BODY') {{
                    element = element.parentElement;
                }}

                if (element && (element.tagName === 'BUTTON' || element.tagName === 'A')) {{
                    const details = {{
                        element: element.tagName.toLowerCase(),
                        text: element.innerText.substring(0, 100).trim() || element.getAttribute('aria-label') || 'N/A',
                        href: element.tagName === 'A' ? element.getAttribute('href') : null
                    }};
                    sendEvent('click', details);
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