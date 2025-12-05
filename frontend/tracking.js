// --- GLASSBOARD TRACKING SNIPPET ---

// NOTE: This file assumes the backend expects a payload for a single event at /track
// and that the site_id placeholder is replaced by your backend during snippet generation.

(() => {
    // 1. CONFIGURATION (Placeholder must be replaced by your backend)
    const BACKEND_URL = "http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/track";
    // This MUST be substituted with the user's unique ID by your FastAPI register endpoint
    const SITE_ID = 'YOUR_UNIQUE_SITE_ID_HERE'; 

    if (SITE_ID === 'YOUR_UNIQUE_SITE_ID_HERE') {
        // console.error("Glassboard: SITE_ID not substituted in snippet.");
        return; 
    }

    // 2. CORE EVENT SENDER
    // Now takes the eventType and element details (which will be null for page_view)
    function sendEvent(eventType, elementDetails = {}) {
        // The payload structure is simplified to match the Event model in your FastAPI
        const payload = {
            site_id: SITE_ID,
            event_type: eventType,
            timestamp: new Date().toISOString(),
            page: window.location.pathname,
            referrer: (function() {
                try {
                    if (!document.referrer) return "direct";
                    return new URL(document.referrer).hostname;
                } catch {
                    return "direct";
                }
            })(),
            element: elementDetails.element || null,
            text: elementDetails.text || null,
            href: elementDetails.href || null,
        };


        fetch(`${BACKEND_URL}/track`, { // <-- Assuming you use a dedicated /track endpoint
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
        .then(res => res.json())
        .then(data => { /* console.log(`Glassboard ${eventType} recorded:`, data) */ })
        .catch(err => console.error("Glassboard Tracking failed:", err));
    }

    // ===================================
    // 3. PAGE VIEW TRACKING (NEW)
    // ===================================
    // Send a 'page_view' event immediately when the script executes
    sendEvent('page_view');


    // ===================================
    // 4. CLICK TRACKING (UPDATED)
    // ===================================
    document.addEventListener("click", (e) => {
        let element = e.target;
        
        // Traverse up the DOM to find the button or link
        while (element && element.tagName !== 'BUTTON' && element.tagName !== 'A' && element.tagName !== 'BODY') {
            element = element.parentElement;
        }

        if (element && (element.tagName === 'BUTTON' || element.tagName === 'A')) {
            const details = {
                element: element.tagName.toLowerCase(),
                text: element.innerText.substring(0, 100).trim() || element.getAttribute('aria-label') || 'N/A',
                href: element.tagName === 'A' ? element.getAttribute('href') : null
            };
            
            // Send the 'click' event using the unified sender
            sendEvent('click', details);
        }
    });

})();