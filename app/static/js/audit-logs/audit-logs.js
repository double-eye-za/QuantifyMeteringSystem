function showDetails() {
  document.getElementById("detailsModal").classList.remove("hidden");
}

function hideDetails() {
  document.getElementById("detailsModal").classList.add("hidden");
}

async function viewLog(id) {
  try {
    const resp = await fetch(`/api/v1/api/audit-logs/${id}`);
    if (!resp.ok) return;
    const { data } = await resp.json();
    // Populate event info fields
    document.getElementById("event-id").textContent = data.id;
    document.getElementById("event-ts").textContent = data.created_at || "";
    document.getElementById("event-action").textContent = data.action || "";
    document.getElementById("event-ip").textContent = data.ip_address || "";
    document.getElementById("event-user").textContent =
      data.user_name || data.user_id || "-";
    // Format user agent
    const ua = data.user_agent || "";
    document.getElementById("event-ua").textContent = ua;

    // Parse old/new values if they are JSON strings
    let oldVals = data.old_values;
    let newVals = data.new_values;
    try {
      if (typeof oldVals === "string") oldVals = JSON.parse(oldVals);
    } catch (_) {}
    try {
      if (typeof newVals === "string") newVals = JSON.parse(newVals);
    } catch (_) {}

    // Render a simple diff two-column block
    const changesEl = document.getElementById("changesContent");
    const keys = Array.from(
      new Set([
        ...(oldVals ? Object.keys(oldVals) : []),
        ...(newVals ? Object.keys(newVals) : []),
      ])
    ).sort();
    let html = '<div class="grid grid-cols-1 md:grid-cols-2 gap-4">';
    html +=
      '<div><div class="font-semibold mb-1">Before</div><pre class="whitespace-pre-wrap">' +
      (oldVals ? JSON.stringify(oldVals, null, 2) : "-") +
      "</pre></div>";
    html +=
      '<div><div class="font-semibold mb-1">After</div><pre class="whitespace-pre-wrap">' +
      (newVals ? JSON.stringify(newVals, null, 2) : "-") +
      "</pre></div>";
    html += "</div>";
    changesEl.innerHTML = html;
    showDetails();
  } catch (e) {
    console.error(e);
  }
}

function applyFilters() {
  const form = document.getElementById("auditFilters");
  form.submit();
}

function clearFilters() {
  window.location.href = "/api/v1/audit-logs";
}
