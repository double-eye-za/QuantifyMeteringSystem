const BASE_URL = "/api/v1/persons";
const API_URL = "/api/v1/api/persons";

// Global table filter instance
let personsTableFilter = null;
let deletePersonId = null;

// Render a single person row for the table
function renderPersonRow(p) {
  const permissions = window.PERSON_PERMISSIONS || {};
  const personJson = JSON.stringify(p).replace(/'/g, "&#39;").replace(/"/g, "&quot;");

  // Build units HTML
  let unitsHtml = '';
  if (p.owned_units && p.owned_units.length > 0 || p.rented_units && p.rented_units.length > 0) {
    if (p.owned_units && p.owned_units.length > 0) {
      unitsHtml += `<div class="text-xs mb-1"><span class="font-semibold text-blue-600 dark:text-blue-400">Owns:</span>`;
      p.owned_units.forEach(unit => {
        unitsHtml += `<div class="ml-2 text-gray-900 dark:text-white">Unit ${unit.unit_number} - ${unit.estate_name} (${unit.ownership_percentage}%)</div>`;
      });
      unitsHtml += `</div>`;
    }
    if (p.rented_units && p.rented_units.length > 0) {
      unitsHtml += `<div class="text-xs"><span class="font-semibold text-green-600 dark:text-green-400">Rents:</span>`;
      p.rented_units.forEach(unit => {
        unitsHtml += `<div class="ml-2 text-gray-900 dark:text-white">Unit ${unit.unit_number} - ${unit.estate_name}</div>`;
      });
      unitsHtml += `</div>`;
    }
  } else {
    unitsHtml = `<span class="text-xs text-gray-500 dark:text-gray-400">No units</span>`;
  }

  // Build role badges HTML
  let roleBadgesHtml = '<div class="flex flex-col gap-1">';
  if (p.owned_units && p.owned_units.length > 0) {
    roleBadgesHtml += `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 dark:bg-blue-900/20 text-blue-800 dark:text-blue-400"><i class="fas fa-home mr-1"></i> Owner</span>`;
  }
  if (p.rented_units && p.rented_units.length > 0) {
    roleBadgesHtml += `<span class="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400"><i class="fas fa-user mr-1"></i> Tenant</span>`;
  }
  if ((!p.owned_units || p.owned_units.length === 0) && (!p.rented_units || p.rented_units.length === 0)) {
    roleBadgesHtml += `<span class="text-xs text-gray-500 dark:text-gray-400">-</span>`;
  }
  roleBadgesHtml += '</div>';

  // Build status badge
  const statusClass = p.is_active
    ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400'
    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400';
  const statusText = p.is_active ? 'Active' : 'Inactive';

  // Build actions HTML
  let actionsHtml = '<div class="flex items-center gap-3 text-sm">';
  if (permissions.canEdit) {
    actionsHtml += `<button class="text-primary hover:underline edit-person-btn" data-person="${personJson}"><i class="fas fa-edit mr-1"></i>Edit</button>`;
  }
  if (permissions.canDelete) {
    actionsHtml += `<button class="text-red-600 dark:text-red-400 hover:underline delete-person-btn" data-person="${personJson}"><i class="fas fa-trash mr-1"></i>Delete</button>`;
  }
  actionsHtml += '</div>';

  return `
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors" data-person="${personJson}">
      <td class="px-4 py-3">
        <div class="text-sm font-medium text-gray-900 dark:text-white">${p.first_name || ''} ${p.last_name || ''}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">${p.id_number || ''}</div>
      </td>
      <td class="px-4 py-3">
        <div class="text-sm text-gray-900 dark:text-gray-300">${p.email || ''}</div>
        <div class="text-xs text-gray-500 dark:text-gray-400">${p.phone || ''}</div>
      </td>
      <td class="px-4 py-3">${unitsHtml}</td>
      <td class="px-4 py-3">${roleBadgesHtml}</td>
      <td class="px-4 py-3">
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">
          ${statusText}
        </span>
      </td>
      <td class="px-4 py-3">${actionsHtml}</td>
    </tr>
  `;
}

// Attach event listeners to dynamically rendered action buttons
function attachPersonRowEventListeners() {
  // Edit buttons
  document.querySelectorAll(".edit-person-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const data = JSON.parse(this.dataset.person);
      openEditPersonFromData(data);
    });
  });

  // Delete buttons
  document.querySelectorAll(".delete-person-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const data = JSON.parse(this.dataset.person);
      deletePersonId = data.id;
      const modal = document.getElementById("personDeleteModal");
      modal.classList.remove("hidden");
      modal.classList.add("flex");
    });
  });
}

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
  openEditPersonFromData(data);
}

function openEditPersonFromData(data) {
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

// Refresh the table after CRUD operations
function refreshPersonsTable() {
  if (personsTableFilter) {
    personsTableFilter.refresh();
  } else {
    window.location.reload();
  }
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
  const url = hasId ? `${BASE_URL}/${payload.id}` : `${BASE_URL}`;
  const method = hasId ? "PUT" : "POST";
  delete payload.id;

  try {
    const resp = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await resp.json();

    if (resp.ok && (result.success || result.id)) {
      // Success - hide modal and refresh table
      hidePersonModal();
      showFlashMessage(successMessage, "success", false);
      refreshPersonsTable();
    } else {
      // Error - show message immediately WITHOUT reload
      const errorMessage = result.error || result.message || "Failed to save person. Please check the form and try again.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    // Network or parsing error
    console.error("Error submitting person:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
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

  try {
    const resp = await fetch(`${BASE_URL}/${deletePersonId}`, {
      method: "DELETE",
    });

    const result = await resp.json();

    if (resp.ok && result.success) {
      // Success - hide modal and refresh table
      hidePersonDelete();
      showFlashMessage("Person deleted successfully", "success", false);
      refreshPersonsTable();
    } else {
      // Error - show message immediately WITHOUT reload
      hidePersonDelete();
      const errorMessage = result.error || result.message || "Failed to delete person. They may be associated with units.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    // Network or parsing error
    hidePersonDelete();
    console.error("Error deleting person:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Initialize TableFilter for AJAX-based filtering
  personsTableFilter = new TableFilter({
    tableBodyId: 'personsTableBody',
    apiEndpoint: API_URL,
    filters: {
      search: { element: '#searchInput', param: 'q', debounce: true },
      unit: { element: '#unitFilter', param: 'unit_id' },
      owner: { element: '#ownerFilter', param: 'is_owner' },
      tenant: { element: '#tenantFilter', param: 'is_tenant' },
      status: { element: '#statusFilter', param: 'is_active' }
    },
    renderRow: renderPersonRow,
    colSpan: 6,
    onError: (error) => showFlashMessage(error, 'error', false),
    onAfterFetch: () => {
      // Re-attach event listeners after table is re-rendered
      attachPersonRowEventListeners();
    }
  });

  // Override attachRowEventListeners in the filter instance
  personsTableFilter.attachRowEventListeners = attachPersonRowEventListeners;

  // Clear filters button
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", function () {
      personsTableFilter.clearFilters();
    });
  }

  // Attach initial event listeners for server-rendered rows
  attachPersonRowEventListeners();
});
