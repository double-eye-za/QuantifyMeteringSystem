const BASE_URL = "/api/v1/persons";

let deletePersonId = null;

function showCreatePerson() {
  const modal = document.getElementById("personModal");
  document.getElementById("personModalTitle").textContent = "New Person";
  modal.querySelector("form").reset();
  modal.querySelector('select[name="is_active"]').value = "true";
  modal
    .querySelector('select[name="is_active"]')
    .dispatchEvent(new Event("change"));
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hidePersonModal() {
  const m = document.getElementById("personModal");
  m.classList.add("hidden");
  m.classList.remove("flex");
}

function openEditPerson(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-person"));
  const form = document.getElementById("personForm");
  document.getElementById("personModalTitle").textContent = "Edit Person";
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
  form.elements.is_active.value = data.is_active ? "true" : "false";
  const m = document.getElementById("personModal");
  m.classList.remove("hidden");
  m.classList.add("flex");
}

async function submitPerson() {
  const form = document.getElementById("personForm");
  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());

  // Convert is_active to boolean
  payload.is_active = payload.is_active === "true";

  const hasId = !!payload.id;
  const successMessage = hasId
    ? "Person updated successfully"
    : "Person created successfully";
  const errorMessage = hasId
    ? "Failed to update person"
    : "Failed to create person";
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

  hidePersonModal();
  window.location.reload();
  showFlashMessage(successMessage, "success", true);
}

function confirmDeletePerson(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-person"));
  deletePersonId = data.id;
  const modal = document.getElementById("personDeleteModal");
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hidePersonDelete() {
  const modal = document.getElementById("personDeleteModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

async function performPersonDelete() {
  if (!deletePersonId) return;
  const resp = await fetch(`${BASE_URL}/${deletePersonId}`, {
    method: "DELETE",
  });

  if (!resp.ok) {
    const errorData = await resp.json();
    const message = errorData.message || "Failed to delete person";
    showFlashMessage(message, "error", true);
    hidePersonDelete();
    return;
  }

  hidePersonDelete();
  window.location.reload();
  showFlashMessage("Person deleted successfully", "success", true);
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
