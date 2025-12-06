// ============================
// Dashboard.js - Clean Version
// ============================

// 1️⃣ Ensure user is logged in
async function ensureLoggedIn() {
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/me", {
        credentials: "include"
    });
    if (res.status !== 200) {
        window.location.href = "/frontend/login.html";
    }
}
ensureLoggedIn();

// 2️⃣ Globals
let chartInstance = null;
let allSummaryData = []; // all-time summary
const customLabels = JSON.parse(localStorage.getItem("customLabels") || "{}");
const editingElements = new Set();

// ============================
// 3️⃣ Update Dashboard
// ============================
async function updateDashboard() {
    const siteId = document.getElementById("siteSelect").value;
    const url = siteId ? `/stats?site_id=${siteId}` : `/stats`;

    try {
        const res = await fetch(url);
        const data = await res.json();

        // Save summary data
        allSummaryData = data.summary.map(item => ({
            ...item,
            text: customLabels[item.element] || item.custom_text || item.text || item.element
        }));

        // Render chart
        const range = document.getElementById("summaryRange").value;
        renderFilteredChart(range);

        // Update aggregates in UI
        ["total_clicks", "day_clicks", "week_clicks", "month_clicks", "year_clicks"].forEach(key => {
            const el = document.getElementById(key.replace("_", ""));
            if (el) el.textContent = data[key] ?? 0;
        });

        ["total_visits", "day_visits", "week_visits", "month_visits", "year_visits"].forEach(key => {
            const el = document.getElementById(key);
            if (el) el.textContent = data[key] ?? 0;
        });

        // Render recent events
        const allList = document.getElementById("all");
        allList.innerHTML = "";
        const recentEvents = data.all_clicks.slice().reverse().slice(0, 10);
        recentEvents.forEach(ev => {
            const li = document.createElement("li");
            li.textContent = ev.element 
                ? `[CLICK] ${ev.element}: "${ev.text}" on page ${ev.page} — ${ev.timestamp}`
                : `[PAGE VIEW] on page ${ev.page} — ${ev.timestamp}`;
            allList.appendChild(li);
        });

        // Render referrers
        renderReferrers([...(data.all_visits || []), ...(data.all_clicks || [])]);

    } catch (err) {
        console.error("Error loading stats:", err);
    }
}

// ============================
// 4️⃣ Filtered Chart
// ============================
function renderFilteredChart(range) {
    const now = new Date();
    const filtered = allSummaryData
        .map(item => ({ ...item })) // clone to avoid mutation
        .filter(item => {
            if (!item.last_click) return true;
            const diffDays = (now - new Date(item.last_click)) / (1000 * 60 * 60 * 24);
            switch (range) {
                case "day": return diffDays <= 1;
                case "week": return diffDays <= 7;
                case "month": return diffDays <= 30;
                case "year": return diffDays <= 365;
                default: return true;
            }
        });
    renderChart(filtered.slice(0, 5));
}

// ============================
// 5️⃣ Render Chart + Editable Labels
// ============================
function renderChart(summaryData) {
    const ctx = document.getElementById("topChart").getContext("2d");
    if (chartInstance) chartInstance.destroy();

    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: summaryData.map(item => item.text),
            datasets: [{
                label: "Top Clicked Elements",
                data: summaryData.map(item => item.count),
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

    summaryData.forEach(item => {
        const li = document.createElement("li");
        const span = document.createElement("span");
        span.className = "label";
        span.dataset.key = `${item.element}::${item.original_text}`;
        span.dataset.element = item.element;
        span.dataset.originalText = item.original_text;
        span.innerText = item.text;

        // Click-to-edit
        span.onclick = () => {
            if (editingElements.has(item.element)) return;
            editingElements.add(item.element);

            const input = document.createElement("input");
            input.value = span.innerText;
            span.replaceWith(input);
            input.focus();

            input.addEventListener("blur", async () => {
                const newText = input.value;
                span.innerText = newText;
                input.replaceWith(span);
                editingElements.delete(item.element);

                // Update chart label
                const idx = summaryData.findIndex(d => `${d.element}::${d.original_text}` === span.dataset.key);
                if (idx !== -1) {
                    chartInstance.data.labels[idx] = newText;
                    chartInstance.update();
                }

                // Save locally
                customLabels[item.element] = newText;
                localStorage.setItem("customLabels", JSON.stringify(customLabels));

                // Save to backend
                const siteValue = document.getElementById("siteSelect").value || null;
                try {
                    await fetch("/stats/label", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            site_id: siteValue,
                            element: item.element,
                            original_text: item.original_text,
                            custom_text: newText
                        })
                    });
                } catch (err) {
                    console.error(err);
                    alert("Failed to update label on server");
                }
            });
        };

        li.appendChild(span);
        topLabelsUl.appendChild(li);
    });
}

// ============================
// 6️⃣ Referrers
// ============================
function renderReferrers(events) {
    const refList = document.getElementById("referrerList");
    refList.innerHTML = "";
    const counts = {};
    events.forEach(ev => { if(ev.referrer) counts[ev.referrer] = (counts[ev.referrer] || 0) + 1; });
    Object.entries(counts).sort((a,b)=>b[1]-a[1]).slice(0,5).forEach(([ref,count])=>{
        const li = document.createElement("li");
        li.textContent = `${ref}: ${count}`;
        refList.appendChild(li);
    });
}

// ============================
// 7️⃣ Event Listeners
// ============================
document.getElementById("summaryRange").addEventListener("change", () => {
    renderFilteredChart(document.getElementById("summaryRange").value);
});
document.getElementById("siteSelect").addEventListener("change", updateDashboard);

// Auto-refresh
updateDashboard();
setInterval(updateDashboard, 5000);

// Logout
document.getElementById("logoutBtn").addEventListener("click", async () => {
    const res = await fetch("http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000/logout", { method:"POST", credentials:"include" });
    if(res.ok) window.location.href="/frontend/login.html";
    else alert("Logout failed");
});

// Register Website
document.getElementById('registerWebsiteForm').addEventListener('submit', async e => {
    e.preventDefault();
    const name = document.getElementById('websiteName').value;
    const domain = document.getElementById('websiteDomain').value;
    if(!domain) { alert('Domain is required'); return; }

    try {
        const res = await fetch('/websites/register', {
            method:'POST',
            headers:{'Content-Type':'application/json'},
            credentials:"include",
            body:JSON.stringify({name, domain})
        });
        const data = await res.json();
        if(res.ok){
            document.getElementById('snippetText').value = data.snippet;
            document.getElementById('snippetOutput').style.display='block';

            const dropdown = document.getElementById('siteSelect');
            const option = document.createElement('option');
            option.value = data.site_id;
            option.textContent = name||domain;
            dropdown.appendChild(option);

            document.getElementById('websiteName').value='';
            document.getElementById('websiteDomain').value='';
        } else alert(data.detail||'Failed to register website');
    } catch(err) { console.error(err); alert('Error registering website'); }
});

// Load Websites
async function loadWebsites() {
    const res = await fetch('/websites/', {credentials:'include'});
    if(res.ok){
        const sites = await res.json();
        const dropdown = document.getElementById('siteSelect');
        dropdown.innerHTML = '<option value="">All Sites</option>';
        sites.forEach(w=>{
            const opt = document.createElement('option');
            opt.value=w.site_id;
            opt.textContent=w.name||w.domain;
            dropdown.appendChild(opt);
        });
    }
}
loadWebsites();

// Reset Button
document.getElementById("resetButton").addEventListener("click", ()=>{
    const BASE_URL = 'http://ec2-44-231-42-67.us-west-2.compute.amazonaws.com:8000';
    const endpoint = `${BASE_URL}/track/reset`;
    if(confirm("Are you sure you want to delete ALL tracking data? This cannot be undone.")){
        fetch(endpoint,{method:'DELETE'})
        .then(res=>{
            if(res.ok){ alert("All events reset."); window.location.reload(); }
            else alert("Failed to reset data."); 
        }).catch(err=>{ console.error(err); alert("Connection error."); });
    }
});
