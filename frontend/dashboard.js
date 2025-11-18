async function ensureLoggedIn() {
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/me", {
        credentials: "include"
    });

    if (res.status !== 200) {
        window.location.href = "/frontend/login.html";
    }
}

ensureLoggedIn();

let chartInstance = null;
let allSummaryData = []; // stores all-time summary for chart

function updateDashboard() {
  const siteId = document.getElementById("siteSelect").value;
  const url = siteId
    ? `http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/stats?site_id=${siteId}`
    : `http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/stats`;


  fetch(url)
    .then(res => res.json())
    .then(data => {
      // === Aggregates ===
      document.getElementById("clicks").textContent = data.total_clicks;
      document.getElementById("dayClicks").textContent = data.day_clicks;
      document.getElementById("weekClicks").textContent = data.week_clicks;
      document.getElementById("monthClicks").textContent = data.month_clicks;
      document.getElementById("yearClicks").textContent = data.year_clicks;

      // === Save summary for chart filtering ===
      allSummaryData = data.summary;

      // === Render chart based on current dropdown ===
      const range = document.getElementById("summaryRange").value;
      renderFilteredChart(range);

      // === Show all recorded events again ===
      const allList = document.getElementById("all");
      allList.innerHTML = "";
      data.all_clicks.forEach(ev => {
        // Only show button or <a> clicks if you wanted that filter
        if (ev.element === "button" || ev.element === "a") {
          const li = document.createElement("li");
          li.textContent = `[${ev.page}] ${ev.element}: "${ev.text}" — ${ev.timestamp}`;
          allList.appendChild(li);
        }
      });
    })
    .catch(err => console.error("Error loading stats:", err));
}

// Filter the summary data depending on the dropdown selection
function renderFilteredChart(range) {
  const now = new Date();
  const filtered = allSummaryData.filter(item => {
    if (!item.timestamp) return true; // keep if no timestamp
    const ts = new Date(item.timestamp);
    const diffDays = (now - ts) / (1000 * 60 * 60 * 24);

    switch (range) {
      case "day": return diffDays <= 1;
      case "week": return diffDays <= 7;
      case "month": return diffDays <= 30;
      case "year": return diffDays <= 365;
      default: return true; // all time
    }
  });

  const topFive = filtered.slice(0, 5);
  renderChart(topFive);
}

function renderChart(summaryData) {
  const ctx = document.getElementById("topChart").getContext("2d");
  if (chartInstance) chartInstance.destroy();

  const labels = summaryData.map(item => item.text || item.element);
  const counts = summaryData.map(item => item.count);

  chartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Top Clicked Elements",
        data: counts,
        backgroundColor: "rgba(56, 189, 248, 0.6)",
        borderColor: "#0ea5e9",
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: { beginAtZero: true }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// Update chart when dropdown changes
document.getElementById("summaryRange").addEventListener("change", () => {
  const range = document.getElementById("summaryRange").value;
  renderFilteredChart(range);
});

updateDashboard();
setInterval(updateDashboard, 5000);
document.getElementById("siteSelect").addEventListener("change", updateDashboard);

document.getElementById("logoutBtn").addEventListener("click", async () => {
    await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/logout", {
        method: "POST",
        credentials: "include"
    });

    window.location.href = "/frontend/login.html";
});
