(() => {
  const BACKEND_URL = "http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000";
  const SITE_ID = new URLSearchParams(location.search).get("site_id");

  if (!SITE_ID) {
    console.warn("Glassboard: SITE_ID missing in snippet.");
    return;
  }

  function sendEvent(element, text) {
    const payload = {
      site_id: SITE_ID,
      events: [{
        element,
        text,
        timestamp: new Date().toISOString(),
        page: window.location.pathname
      }]
    };

    fetch(`${BACKEND_URL}/events/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    })
    .then(res => res.json())
    .then(data => console.log("Event recorded:", data))
    .catch(err => console.error("Tracking failed:", err));
  }

  // Track buttons
  document.querySelectorAll("button").forEach(btn => {
    btn.addEventListener("click", () => sendEvent("button", btn.textContent));
  });

  // Track links
  document.querySelectorAll("a").forEach(link => {
    link.addEventListener("click", e => {
      console.log(`Link clicked: ${link.textContent}`);
      sendEvent("a", link.textContent);
    });
  });

})();
