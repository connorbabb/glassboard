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
    allow_origins=[
        "http://127.0.0.1:5500",  # Local live server
        "http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com"  # Your EC2 frontend origin
    ],
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


# backend/main.py (Only the updated tracking_snippet function)

@app.get("/snippet/{site_id}.js", response_class=PlainTextResponse)
def tracking_snippet(site_id: str):
    # This snippet is the final, working JavaScript code.
    js_code = f"""
        (function() {{
            const SITE_ID = "{site_id}"; // Substituted by Python
            // We use the full, fixed endpoint URL here.
            const TRACKING_ENDPOINT = 'http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/track'; 

            // 1. CORE EVENT SENDER FUNCTION (Sends single, flat payload to /track)
            function sendEvent(eventType, elementDetails = {{}}) {{
                const payload = {{
                    site_id: SITE_ID,
                    event_type: eventType,
                    timestamp: new Date().toISOString(),
                    page: window.location.pathname,
                    referrer: (function () {{
                        try {{
                            if (!document.referrer) return "direct";
                            return new URL(document.referrer, window.location.origin).hostname;
                        }} catch {{
                            return "direct";
                        }}
                    }})(),

                    element: elementDetails.element || null,
                    text: elementDetails.text || null,
                    href: elementDetails.href || null,
                }};

                fetch(TRACKING_ENDPOINT, {{
                    method: "POST",
                    headers: {{ "Content-Type": "application/json" }},
                    body: JSON.stringify(payload),
                }})
                .then(res => res.json())
                .catch(err => console.error("Glassboard Tracking failed:", err));
            }}

            // 2. PAGE VIEW TRACKING (NEW)
            sendEvent('page_view');


            // 3. CLICK TRACKING (UPDATED)
            document.addEventListener("click", (e) => {{
                let element = e.target;
                
                // Traverse up the DOM to find the button or link
                while (element && element.tagName !== 'BUTTON' && element.tagName !== 'A' && element.tagName !== 'BODY') {{
                    element = element.parentElement;
                }}

                if (element && (element.tagName === 'BUTTON' || element.tagName === 'A')) {{
                    const details = {{
                        element: element.tagName.toLowerCase(),
                        text: element.innerText.substring(0, 100).trim() || element.getAttribute('aria-label') || 'N/A',
                        href: element.tagName === 'A' ? element.getAttribute('href') : null
                    }};
                    
                    // Send the 'click' event using the unified sender
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
