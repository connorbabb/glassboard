fetch("http://127.0.0.1:8000/stats/")
  .then(res => res.json())
  .then(data => {
    document.getElementById("clicks").textContent = data.total_clicks;
    const topList = document.getElementById("top");
    data.top_elements.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.element}: ${item.count}`;
      topList.appendChild(li);
    });
  });

function resetData() {
  fetch("http://127.0.0.1:8000/events/reset", { method: "DELETE" })
    .then(res => res.json())
    .then(data => console.log("Deleted:", data.deleted_rows));
}
