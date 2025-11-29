async function ensureLoggedIn() {
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/me", {
        credentials: "include"
    });

    if (res.status !== 200) {
        window.location.href = "/frontend/login.html";
    }
}

setTimeout(ensureLoggedIn, 300);

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
      // === AGGREGATES: CLICKS ===
      document.getElementById("clicks").textContent = data.total_clicks;
      document.getElementById("dayClicks").textContent = data.day_clicks;
      document.getElementById("weekClicks").textContent = data.week_clicks;
      document.getElementById("monthClicks").textContent = data.month_clicks;
      document.getElementById("yearClicks").textContent = data.year_clicks;
      
      // ===================================
      // === NEW AGGREGATES: PAGE VISITS ===
      // ===================================
      // These assume your backend returns keys like total_visits, day_visits, etc.
      document.getElementById("totalVisits").textContent = data.total_visits || 0;
      document.getElementById("dayVisits").textContent = data.day_visits || 0;
      document.getElementById("weekVisits").textContent = data.week_visits || 0;
      document.getElementById("monthVisits").textContent = data.month_visits || 0;
      document.getElementById("yearVisits").textContent = data.year_visits || 0;

      // === Save summary for chart filtering ===
      allSummaryData = data.summary;

      // === Render chart based on current dropdown ===
      const range = document.getElementById("summaryRange").value;
      renderFilteredChart(range);

      // === Show all recorded events again ===
      const allList = document.getElementById("all");
      allList.innerHTML = "";
      // We will only show clicks for now, as showing all page views would be noisy
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

async function logout() {
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/logout", {
        method: "POST",
        credentials: "include"  // THIS IS REQUIRED to send the cookie
    });

    if (res.ok) {
        window.location.href = "/frontend/login.html";
    } else {
        alert("Logout failed");
    }
}

document.getElementById("logoutBtn").addEventListener("click", logout);


document.getElementById('registerWebsiteForm').addEventListener('submit', async (e) => {
  e.preventDefault();

  const name = document.getElementById('websiteName').value;
  const domain = document.getElementById('websiteDomain').value;

  if (!domain) {
    alert('Domain is required');
    return;
  }

  try {
    const res = await fetch('/websites/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: "include",
      body: JSON.stringify({ name, domain })
    });


    const data = await res.json();

    if (res.ok) {
      // Show snippet
      const snippetDiv = document.getElementById('snippetOutput');
      const snippetText = document.getElementById('snippetText');
      snippetText.value = data.snippet;
      snippetDiv.style.display = 'block';

      // Add new website to dropdown
      const dropdown = document.getElementById('siteSelect');
      const option = document.createElement('option');
      option.value = data.site_id;
      option.textContent = name || domain;
      dropdown.appendChild(option);

      // Clear form
      document.getElementById('websiteName').value = '';
      document.getElementById('websiteDomain').value = '';
    } else {
      alert(data.detail || 'Failed to register website');
    }
  } catch (err) {
    console.error(err);
    alert('Error registering website');
  }
});

async function loadWebsites() {
  const res = await fetch('/websites/', { credentials: 'include' });
  if (res.ok) {
    const sites = await res.json();
    const dropdown = document.getElementById('siteSelect');
    dropdown.innerHTML = '<option value="">All Sites</option>';
    sites.forEach(w => {
      const opt = document.createElement('option');
      opt.value = w.site_id;
      opt.textContent = w.name || w.domain;
      dropdown.appendChild(opt);
    });
  }
}
loadWebsites();