const BASE_URL = "/api/v1/meters";
function showCreateMeter() {
  const modal = document.getElementById("createMeterModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hideCreateMeter() {
  const modal = document.getElementById("createMeterModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

function openEditMeter(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-meter"));
  const editModal = document.getElementById("editMeterModal");
  const form = document.getElementById("editMeterForm");
  form.elements.id.value = data.id;
  form.elements.serial_number.value = data.serial_number || "";
  form.elements.meter_type.value = data.meter_type || "";
  form.elements.installation_date.value =
    (data.installation_date || "").split("T")[0] || "";
  form.elements.status.value = data.is_active ? "active" : "inactive";
  // preselect estate if available via unit
  if (data.unit && data.unit.estate_id) {
    form.elements.estate_id.value = data.unit.estate_id;
  }
  if (data.unit && data.unit.id) {
    form.elements.unit_id.value = data.unit.id;
  }
  editModal.classList.remove("hidden");
  editModal.classList.add("flex");
  refreshUnitDisableState(form);
}

function hideEditMeter() {
  const editModal = document.getElementById("editMeterModal");
  editModal.classList.add("hidden");
  editModal.classList.remove("flex");
}

function confirmDeleteMeter(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-meter"));
  window._deleteMeterId = data.id;
  const deleteModal = document.getElementById("deleteMeterModal");
  deleteModal.classList.remove("hidden");
  deleteModal.classList.add("flex");
}

function hideDeleteMeter() {
  const deleteModal = document.getElementById("deleteMeterModal");
  deleteModal.classList.add("hidden");
  deleteModal.classList.remove("flex");
}

function refreshUnitDisableState(scope) {
  const form = scope || document.getElementById("createMeterForm");
  const type = form.elements.meter_type.value;
  const unitSelect = form.elements.unit_id;
  Array.from(unitSelect.options).forEach((opt) => {
    if (!opt.value) return;
    const hasElec = opt.getAttribute("data-has-electricity") === "1";
    const hasWater = opt.getAttribute("data-has-water") === "1";
    const hasSolar = opt.getAttribute("data-has-solar") === "1";
    let disabled = false;
    if (type === "electricity" && hasElec) disabled = true;
    if (type === "water" && hasWater) disabled = true;
    if (type === "solar" && hasSolar) disabled = true;
    opt.disabled = disabled;
  });
}

document
  .getElementById("createMeterForm")
  ?.elements.meter_type?.addEventListener("change", () =>
    refreshUnitDisableState(document.getElementById("createMeterForm"))
  );
document
  .getElementById("editMeterForm")
  ?.elements.meter_type?.addEventListener("change", () =>
    refreshUnitDisableState(document.getElementById("editMeterForm"))
  );

async function submitCreateMeter() {
  const form = document.getElementById("createMeterForm");
  const payload = Object.fromEntries(new FormData(form).entries());
  if (payload.installation_date === "") delete payload.installation_date;
  const resp = await fetch(`${BASE_URL}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    showFlashMessage("Failed to create meter", "error", true);
    return;
  }
  hideCreateMeter();
  window.location.reload();
  showFlashMessage("Meter created successfully", "success", true);
}

async function submitEditMeter() {
  const form = document.getElementById("editMeterForm");
  const payload = Object.fromEntries(new FormData(form).entries());
  const id = payload.id;
  delete payload.id;
  if (payload.installation_date === "") delete payload.installation_date;
  const resp = await fetch(`${BASE_URL}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    showFlashMessage("Failed to update meter details", "error", true);
    return;
  }
  hideEditMeter();
  window.location.reload();
  showFlashMessage("Meter updated successfully", "success", true);
}

async function performDeleteMeter() {
  const id = window._deleteMeterId;
  if (!id) return;
  const resp = await fetch(`${BASE_URL}/${id}`, { method: "DELETE" });
  if (!resp.ok) {
    showFlashMessaged("Failed to delete meter", "error", true);
    return;
  }
  hideDeleteMeter();
  window.location.reload();
  showFlashMessage("Meter deleted successfully", "success", true);
}

function applyFilters() {
  const form = document.getElementById("meterFilters");
  form.submit();
}

function clearFilters() {
  window.location.href = BASE_URL;
}
