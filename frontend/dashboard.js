function updateDashboard() {
  const siteId = document.getElementById("siteSelect").value; // from dropdown
  const url = siteId
    ? `http://127.0.0.1:8000/stats?site_id=${siteId}`
    : "http://127.0.0.1:8000/stats/";

  fetch(url)
    .then(res => res.json())
    .then(data => {
      document.getElementById("clicks").textContent = data.total_clicks;
      const topList = document.getElementById("top");
      topList.innerHTML = "";
      data.top_elements.forEach(item => {
        const li = document.createElement("li");
        li.textContent = `${item.element}: ${item.count}`;
        topList.appendChild(li);
      });
    })
    .catch(err => console.error("Error loading stats:", err));
}

function resetData() {
  fetch("http://127.0.0.1:8000/events/reset", { method: "DELETE" })
    .then(res => res.json())
    .then(data => {
      console.log("Deleted:", data.deleted_rows);
      updateDashboard();
    })
    .catch(err => console.error("Error resetting data:", err));
}

// Initial load
updateDashboard();
// Refresh every 5 seconds
setInterval(updateDashboard, 5000);

// Re-run when switching sites
document.getElementById("siteSelect").addEventListener("change", updateDashboard);
