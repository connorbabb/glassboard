// dashboard.js

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

// 1️⃣ Load custom labels from localStorage
const customLabels = JSON.parse(localStorage.getItem("customLabels") || "{}");

// 2️⃣ Track currently editing elements
const editingElements = new Set();

// 3️⃣ Update dashboard function (fetches data and updates aggregates)
function updateDashboard() {
    const siteId = document.getElementById("siteSelect").value;
    const url = siteId
        ? `/stats?site_id=${siteId}`
        : `/stats`;

    fetch(url)
        .then(res => res.json())
        .then(data => {
            allSummaryData = data.summary;

            // Apply saved labels
            allSummaryData.forEach(item => {
                // ✅ FIX 1: Calculate the unique key here
                const uniqueKey = `${item.element}::${item.original_text}`; 

                if (customLabels[uniqueKey]) { // ✅ Fix: Use uniqueKey for retrieval
                    item.text = customLabels[uniqueKey];
                } else if (item.custom_text) {
                    item.text = item.custom_text;
                    
                    // Also update the save key to the unique one when loading custom_text from backend
                    customLabels[uniqueKey] = item.custom_text; // ✅ Fix: Use uniqueKey for storage
                    localStorage.setItem('customLabels', JSON.stringify(customLabels));
                } else {
                    item.text = item.text || item.element;
                }
            });

            // ... rest of the function
        })
        .catch(err => console.error("Error loading stats:", err));
}

// 6️⃣ Initialize
updateDashboard();
setInterval(updateDashboard, 5000);
document.getElementById("summaryRange").addEventListener("change", () => renderFilteredChart(document.getElementById("summaryRange").value));
document.getElementById("siteSelect").addEventListener("change", updateDashboard);


  function renderFilteredChart(range) {
    const now = new Date();
    const filtered = allSummaryData
      .filter(item => {
        const uniqueKey = `${item.element}::${item.original_text}`; // Calculate key here
        if (customLabels[uniqueKey] && !editingElements.has(item.element)) {
            item.text = customLabels[uniqueKey];
        }
        if (!item.last_click) return true;
        const ts = new Date(item.last_click);
        const diffDays = (now - ts) / (1000 * 60 * 60 * 24);

        switch (range) {
          case "day": return diffDays <= 1;
          case "week": return diffDays <= 7;
          case "month": return diffDays <= 30;
          case "year": return diffDays <= 365;
          default: return true;
        }
      })
      .map(item => ({ ...item }));

    const topFive = filtered.slice(0, 5);
    renderChart(topFive);
  }

  // Load from localStorage if available
  const saved = localStorage.getItem('customLabels');
  if (saved) Object.assign(customLabels, JSON.parse(saved));

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
            scales: { y: { beginAtZero: true } },
            plugins: { legend: { display: false } }
        }
    });

    const topLabelsUl = document.getElementById("topLabels");
    topLabelsUl.innerHTML = "";

    summaryData.forEach((item, i) => {
        const li = document.createElement("li");
        const span = document.createElement("span");

        span.className = "label";
        span.dataset.key = `${item.element}::${item.original_text}`;
        span.dataset.element = item.element;
        span.dataset.originalText = item.original_text;
        span.innerText = item.text;

        li.appendChild(span);
        topLabelsUl.appendChild(li);

        span.onclick = () => {
          const input = document.createElement("input");
          input.value = span.innerText;

          span.replaceWith(input);
          input.focus();

          input.addEventListener("blur", async () => {
            const newText = input.value;

            // restore span
            span.innerText = newText;
            input.replaceWith(span);

            // stable key logic
            const key = span.dataset.key;
            const labelIndex = chartInstance.data.labels.findIndex((_, idx) => {
              const d = summaryData[idx];
              return `${d.element}::${d.original_text}` === key;
            });

            if (labelIndex !== -1) {
              chartInstance.data.labels[labelIndex] = newText;
              chartInstance.update();
            }

            // save
            customLabels[span.dataset.key] = newText;
            localStorage.setItem("customLabels", JSON.stringify(customLabels));

            // send to backend
            const siteValue = document.getElementById("siteSelect").value;

            try {
              await fetch("/stats/label", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  site_id: siteValue || null,
                  element: span.dataset.element,
                  original_text: span.dataset.originalText,
                  custom_text: newText
                })
              });
            } catch (err) {
              console.error(err);
              alert("Failed to update label");
            }
          });
        };
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


  // dashboard.js (Add this at the end of the file)
  document.getElementById("resetButton").addEventListener("click", () => {
      // IMPORTANT: Ensure this base URL is correct for your EC2 instance
      const BASE_URL = 'http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000';

      // The correct endpoint is /track/reset
      const endpoint = `${BASE_URL}/track/reset`;

      if (confirm("Are you sure you want to delete ALL tracking data? This cannot be undone.")) {
          fetch(endpoint, {
              method: 'DELETE',
          })
          .then(response => {
              if (response.ok) {
                  alert("All events have been successfully reset.");
                  window.location.reload(); 
              } else {
                  alert("Failed to reset data. Check server logs.");
              }
          })
          .catch(error => {
              console.error('Error resetting data:', error);
              alert("Connection error occurred.");
          });
      }
  });

  function renderReferrers(events) {
      const refList = document.getElementById("referrerList");
      refList.innerHTML = "";

      const counts = {};

      events.forEach(ev => {
          if (!ev.referrer) return;
          counts[ev.referrer] = (counts[ev.referrer] || 0) + 1;
      });

      const sorted = Object.entries(counts)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 5);

      sorted.forEach(([ref, count]) => {
          const li = document.createElement("li");
          li.textContent = `${ref}: ${count}`;
          refList.appendChild(li);
      });
  }
