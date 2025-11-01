from fastapi import APIRouter, Response

router = APIRouter(prefix="/snippet", tags=["Snippet"])

@router.get("/{site_id}.js")
def get_snippet(site_id: str):
    js_code = f"""
    (function() {{
        const SITE_ID = "{site_id}";
        document.addEventListener("click", (e) => {{
            const data = {{
                site_id: SITE_ID,
                events: [{{
                    type: "click",
                    element: e.target.tagName.toLowerCase(),
                    page: window.location.pathname,
                    timestamp: new Date().toISOString()
                }}]
            }};
            fetch("http://127.0.0.1:8000/events/", {{
                method: "POST",
                headers: {{ "Content-Type": "application/json" }},
                body: JSON.stringify(data)
            }});
        }});
    }})();
    """
    return Response(content=js_code, media_type="application/javascript")
