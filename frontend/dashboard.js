// dashboard.js

// --- 1. GLOBAL VARIABLES & CONSTANTS ---
let chartInstance = null;
let allSummaryData = []; // stores all-time summary for chart

// Load custom labels from localStorage (runs immediately on script load)
const customLabels = JSON.parse(localStorage.getItem("customLabels") || "{}");
const editingElements = new Set();


// --- 2. AUTHENTICATION & CORE FUNCTIONS ---

async function ensureLoggedIn() {
    // IMPORTANT: Make sure this URL is correct for your EC2 instance
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/me", {
        credentials: "include"
    });

    if (res.status !== 200) {
        window.location.href = "/frontend/login.html";
    }
}

// dashboard.js

/**
 * Fetches stats data from the server, updates the global summary data,
 * assigns all metric totals to the relevant HTML elements, and triggers the chart render.
 */
function updateDashboard() {
    const siteId = document.getElementById("siteSelect").value;
    const url = siteId
        ? `/stats?site_id=${siteId}`
        : `/stats`;

    fetch(url)
        .then(res => {
            if (!res.ok) {
                console.error(`Stats API returned status: ${res.status}`);
                throw new Error("Failed to fetch stats data.");
            }
            return res.json();
        })
        .then(data => {
            
            // --- 1. CORE DATA ASSIGNMENT (Clean Data Flow) ---
            if (!data || !data.summary) {
                console.error("API returned invalid data structure.", data);
                allSummaryData = [];
            } else {
                // **CRITICAL: Take the clean data directly from the backend.**
                allSummaryData = data.summary;
            }

            // --- 2. METRICS DISPLAY (The Counts) ---
            
            const getCount = (value) => (value || 0).toLocaleString();

            document.getElementById("totalClicks").innerText = getCount(data.total_clicks);
            document.getElementById("dayClicks").innerText = getCount(data.day_clicks);
            document.getElementById("weekClicks").innerText = getCount(data.week_clicks);
            document.getElementById("monthClicks").innerText = getCount(data.month_clicks);
            document.getElementById("yearClicks").innerText = getCount(data.year_clicks);
            
            document.getElementById("totalVisits").innerText = getCount(data.total_visits);
            document.getElementById("dayVisits").innerText = getCount(data.day_visits);
            document.getElementById("weekVisits").innerText = getCount(data.week_visits);
            document.getElementById("monthVisits").innerText = getCount(data.month_visits);
            document.getElementById("yearVisits").innerText = getCount(data.year_visits);

            // --- 3. RENDER CHART AND REFERRERS ---
            
            // The chart rendering functions handle any necessary local label overrides.
            renderFilteredChart(document.getElementById("summaryRange").value);
            
            // Assuming this function exists to show referrer list
            renderReferrers(data.all_visits); // Use all_visits or all_clicks data for referrer list
            renderAllEvents(data.all_clicks, data.all_visits); // ADD THIS LINE
            
        })
        .catch(err => console.error("Error loading stats:", err));
}

function renderFilteredChart(range) {
    const now = new Date();
    const filtered = allSummaryData
        .filter(item => {
            // The logic for filtering by time range
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
        .map(item => ({ ...item })); // Create deep copy

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
            scales: { y: { beginAtZero: true } },
            plugins: { legend: { display: false } }
        }
  });

    const topLabelsUl = document.getElementById("topLabels");
    topLabelsUl.innerHTML = "";

    summaryData.forEach((item, i) => {
        const li = document.createElement("li");
        const span = document.createElement("span");
        const muteBtn = document.createElement("button"); // 🌟 NEW BUTTON

        span.className = "label";
        span.dataset.key = `${item.element}::${item.original_text}`;
        span.dataset.element = item.element;
        span.dataset.originalText = item.original_text;
        span.innerText = item.text;

        muteBtn.innerText = "Mute"; // Initial state (we can improve this later)
        muteBtn.className = "mute-btn";
        muteBtn.onclick = () => muteEvent(item.element, item.original_text); // 🌟 NEW CLICK HANDLER

        li.appendChild(span);
        li.appendChild(muteBtn); // 🌟 APPEND BUTTON
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

                // save to localStorage
                customLabels[span.dataset.key] = newText;
                localStorage.setItem("customLabels", JSON.stringify(customLabels));

                // send to backend
                const siteValue = document.getElementById("siteSelect").value;

                try {
                    await fetch("/stats/label", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            // Send null if siteValue is empty string ("All Sites")
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


// --- 3. UTILITY FUNCTIONS ---

async function logout() {
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/logout", {
        method: "POST",
        credentials: "include"
    });

    if (res.ok) {
        window.location.href = "/frontend/login.html";
    } else {
        alert("Logout failed");
    }
}

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


// --- 4. INITIALIZATION (Ensure code runs only after DOM is loaded) ---

document.addEventListener('DOMContentLoaded', () => {
    // Check login status immediately
    ensureLoggedIn();
    
    // Load existing websites into the dropdown
    loadWebsites();
    
    // Start the first data fetch and render the initial chart
    updateDashboard(); 
    
    // Set up recurring data fetch
    setInterval(updateDashboard, 5000);
    
    // --- Event Listeners ---
    
    // Filter by time range
    document.getElementById("summaryRange").addEventListener("change", (e) => {
        renderFilteredChart(e.target.value);
    });
    
    // Filter by site selection
    document.getElementById("siteSelect").addEventListener("change", updateDashboard);

    // Logout button
    document.getElementById("logoutBtn").addEventListener("click", logout);
    
    // Reset button logic
    document.getElementById("resetButton").addEventListener("click", () => {
        const BASE_URL = 'http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000';
        const endpoint = `${BASE_URL}/track/reset`;

        if (confirm("Are you sure you want to delete ALL tracking data? This cannot be undone.")) {
            fetch(endpoint, { method: 'DELETE' })
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

    // Register Website Form submission
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
});

// --- NEW DELETION EVENT LISTENER (Add this to dashboard.js) ---
document.getElementById("deleteWebsiteButton").addEventListener("click", () => {
    const identifierInput = document.getElementById("websiteIdentifierInput");
    const identifier = identifierInput.value.trim();

    if (identifier) {
        // This calls the deleteWebsite function, which constructs the correct URL
        deleteWebsite(identifier); 
        identifierInput.value = ''; // Clear input after triggering deletion
    } else {
        // Optionally provide user feedback
        alert("Please enter a Website Name or Domain to delete.");
    }
});
// ------------------------------------

// --- 3. UTILITY FUNCTIONS --- 
// ... (Your other utility functions like logout, loadWebsites, renderReferrers)

/**
 * Renders the list of the 10 most recent events (clicks and page views).
 * @param {Array} clicks - Array of click events from data.all_clicks
 * @param {Array} visits - Array of page view events from data.all_visits
 */
function renderAllEvents(clicks, visits) {
    const allList = document.getElementById("all");
    if (!allList) return; 

    allList.innerHTML = ""; // Clear existing list

    // Combine and sort events by timestamp descending
    const allEvents = [...clicks, ...visits]
        .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
        .slice(0, 10); // Limit to 10 most recent events

    allEvents.forEach(event => {
        const li = document.createElement("li");
        
        // Format time and date
        const time = new Date(event.timestamp).toLocaleTimeString();
        const date = new Date(event.timestamp).toLocaleDateString();

        let eventDetail = '';
        
        // --- FINAL, CORRECTED NAMING CHECK ---
        
        // Use the presence of the 'element' field to distinguish click from page_view
        if (event.element) { 
            // This is a CLICK event
            const textDisplay = event.text ? `"${event.text}"` : 'NO TEXT';
            eventDetail = `CLICKED: ${textDisplay} on <${event.element}>`;
            
        } else if (event.page) {
            // This is a PAGE VIEW event (or lacks click details, but has a page)
            eventDetail = `VIEWED: ${event.page}`; // Use event.page for the URL
        }
        
        // If the backend didn't set event_type, this logic handles it based on data present.
        
        // Final list item output
        li.textContent = `[${date} ${time}] - ${eventDetail}`;
        allList.appendChild(li);
    });
}

async function muteEvent(element, originalText) {
    // Get the current site ID (null means global mute)
    const siteId = document.getElementById("siteSelect").value || null; 
    
    const payload = {
        site_id: siteId,
        element: element,
        original_text: originalText
    };

    const actionText = `element "${element}" with text "${originalText}"`;
    
    if (!confirm(`Are you sure you want to toggle tracking for ${actionText}? This will update the stats immediately.`)) {
        return;
    }

    try {
        const res = await fetch("/stats/mute_event", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            credentials: "include",
            body: JSON.stringify(payload)
        });

        if (res.ok) {
            const data = await res.json();
            alert(`Event pattern successfully ${data.action} for site ${siteId || 'globally'}.`);
            // Refresh dashboard to show excluded stats
            updateDashboard(); 
        } else {
            alert("Failed to mute/unmute event. Check to make sure you have a specific site selected.");
        }
    } catch (err) {
        console.error("Error toggling mute status:", err);
    }
}

// Add this new function to your dashboard.js file
async function deleteWebsite(identifier) {
    if (!confirm(`Are you sure you want to delete the website "${identifier}"? This action is irreversible.`)) {
        return; // User cancelled
    }
    
    // Construct the URL using the identifier as a Query Parameter
    // This is the CRITICAL FIX that makes the frontend talk to your fixed backend function!
    const url = `/websites/?identifier=${encodeURIComponent(identifier)}`;

    try {
        const res = await fetch(url, { 
            method: 'DELETE',
            credentials: 'include' // Required for sending the authentication cookie
        });

        if (res.status === 204) {
            alert(`Website "${identifier}" successfully deleted.`);
            // After successful deletion, reload the website list
            await loadWebsites(); 
            // Also refresh your dashboard data
            updateDashboard();
        } else {
            // Read the error detail from the server response (e.g., "not found or you do not own it.")
            const data = await res.json();
            alert(data.detail || `Failed to delete website "${identifier}".`);
        }
    } catch (err) {
        console.error('Error deleting website:', err);
        alert('Connection error occurred.');
    }
}