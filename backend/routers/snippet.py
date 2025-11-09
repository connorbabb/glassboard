from fastapi import APIRouter, Response

router = APIRouter(prefix="/snippet", tags=["Snippet"])

@router.get("/{site_id}.js")
def get_snippet(site_id: str):
    js_code = f"""
    (function() {{
        const SITE_ID = "{site_id}";

        document.addEventListener("click", (e) => {{
            // Get element info safely
            const element = e.target.tagName.toLowerCase();
            const text = (e.target.innerText || e.target.textContent || "").trim().slice(0, 100) || "(no text)";
            const href = e.target.getAttribute("href") || null;

            // Build payload
            const data = {{
                site_id: SITE_ID,
                events: [{{
                    type: "click",
                    element: element,
                    text: text,
                    href: href,
                    page: window.location.pathname,
                    timestamp: new Date().toISOString()
                }}]
            }};

            // Send event to backend
            fetch("http://127.0.0.1:8000/events/", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(data)
            }}).catch(err => console.error("Tracking failed:", err));
        }});
    }})();
    """
    return Response(content=js_code, media_type="application/javascript")
