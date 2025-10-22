(function() {
  const siteId = "demo123";
  const buffer = [];
  const endpoint = "http://127.0.0.1:8000/events/";

  function sendBatch() {
    if (buffer.length === 0) return;
    fetch(endpoint, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({ site_id: siteId, events: buffer.splice(0) })
    });
  }

  document.addEventListener("click", (e) => {
    const event = {
      type: "click",
      element: e.target.tagName.toLowerCase(),
      page: window.location.pathname,
      timestamp: new Date().toISOString()
    };
    buffer.push(event);
    if (buffer.length >= 5) sendBatch();
  });

  setInterval(sendBatch, 5000); // flush periodically
})();
