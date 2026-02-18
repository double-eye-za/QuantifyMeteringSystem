const BASE_URL = "/api/v1/residents";

let deleteResidentId = null;
function showCreateResident() {
  const modal = document.getElementById("residentModal");
  document.getElementById("residentModalTitle").textContent = "New Resident";
  modal.querySelector("form").reset();
  modal.querySelector('select[name="status"]').value = "active";
  modal
    .querySelector('select[name="status"]')
    .dispatchEvent(new Event("change"));
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hideResidentModal() {
  const m = document.getElementById("residentModal");
  m.classList.add("hidden");
  m.classList.remove("flex");
}

function openEditResident(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-resident"));
  const form = document.getElementById("residentForm");
  document.getElementById("residentModalTitle").textContent = "Edit Resident";
  form.elements.id.value = data.id;
  form.elements.first_name.value = data.first_name || "";
  form.elements.last_name.value = data.last_name || "";
  form.elements.email.value = data.email || "";
  form.elements.phone.value = data.phone || "";
  form.elements.id_number.value = data.id_number || "";
  form.elements.alternate_phone.value = data.alternate_phone || "";
  form.elements.emergency_contact_name.value =
    data.emergency_contact_name || "";
  form.elements.emergency_contact_phone.value =
    data.emergency_contact_phone || "";
  form.elements.lease_start_date.value =
    (data.lease_start_date || "").split("T")[0] || "";
  form.elements.lease_end_date.value =
    (data.lease_end_date || "").split("T")[0] || "";
  form.elements.status.value =
    data.status || (data.is_active ? "active" : "vacated");
  const m = document.getElementById("residentModal");
  m.classList.remove("hidden");
  m.classList.add("flex");
}

async function submitResident() {
  const form = document.getElementById("residentForm");
  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());
  // Normalize booleans/dates
  if (payload.lease_start_date === "") delete payload.lease_start_date;
  if (payload.lease_end_date === "") delete payload.lease_end_date;
  const hasId = !!payload.id;
  const successMessage = hasId
    ? "Resident updated successfully"
    : "Resident created successfully";
  const errorMessage = hasId
    ? "Failed to update resident"
    : "Failed to create resident";
  const url = hasId ? `${BASE_URL}/${payload.id}` : `${BASE_URL}`;
  const method = hasId ? "PUT" : "POST";
  delete payload.id;
  const resp = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    showFlashMessage(errorMessage, "error", true);
    return;
  }
  hideResidentModal();
  window.location.reload();
  showFlashMessage(successMessage, "success", true);
}

function confirmDeleteResident(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-resident"));
  deleteResidentId = data.id;
  const modal = document.getElementById("residentDeleteModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}
function hideResidentDelete() {
  const modal = document.getElementById("residentDeleteModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}
async function performResidentDelete() {
  if (!deleteResidentId) return;
  const resp = await fetch(`${BASE_URL}/${deleteResidentId}`, {
    method: "DELETE",
  });
  if (!resp.ok) {
    showFlashMessage("Failed to delete resident", "error", true);
    return;
  }
  hideResidentDelete();
  window.location.reload();
  showFlashMessage("Resident deleted successfully", "success", true);
}

function applyFilters() {
  const form = document.getElementById("filters");
  form.submit();
}

function clearFilters() {
  window.location.href = BASE_URL;
}

document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("searchInput");
  if (searchInput) {
    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        applyFilters();
      }
    });
  }
});
