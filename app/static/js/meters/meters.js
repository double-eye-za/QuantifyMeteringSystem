const BASE_URL = "/api/v1/meters";
const API_URL = "/api/v1/api/meters";
const UNITS_API_URL = "/api/v1/api/meters/units-availability";

// Global table filter instance
let metersTableFilter = null;

// Helper to format numbers
function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '0.00';
  return parseFloat(num).toFixed(decimals);
}

// Render a single meter row for the table
function renderMeterRow(m) {
  const permissions = window.METER_PERMISSIONS || {};
  const meterJson = JSON.stringify(m).replace(/'/g, "&#39;").replace(/"/g, "&quot;");

  const deviceId = m.device_eui || m.serial_number;
  const unit = m.unit;
  const assignedEstate = m.assigned_estate;
  const balance = m.balance || 0;
  const creditStatus = m.credit_status || 'ok';

  // Unit/Location cell
  let locationHtml = '';
  if (unit) {
    locationHtml = `
      <div class="text-sm font-medium text-gray-900 dark:text-white">${unit.unit_number || ''}</div>
      <div class="text-xs text-gray-500 dark:text-gray-400">${unit.estate_name || ''}</div>
    `;
  } else if (assignedEstate) {
    locationHtml = `
      <div class="text-sm font-medium text-gray-900 dark:text-white">${assignedEstate.name || ''}</div>
      <div class="text-xs text-gray-500 dark:text-gray-400"></div>
    `;
  } else {
    locationHtml = `
      <div class="text-sm font-medium text-gray-900 dark:text-white">Unassigned</div>
      <div class="text-xs text-gray-500 dark:text-gray-400"></div>
    `;
  }

  // Type badge
  let typeClass, typeIcon;
  switch (m.meter_type) {
    case 'electricity':
      typeClass = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300';
      typeIcon = 'fa-bolt';
      break;
    case 'water':
      typeClass = 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300';
      typeIcon = 'fa-tint';
      break;
    case 'solar':
      typeClass = 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
      typeIcon = 'fa-solar-panel';
      break;
    default:
      typeClass = 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
      typeIcon = 'fa-battery-full';
  }
  const typeName = (m.meter_type || '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());

  // Status badge
  const statusClass = m.is_active
    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
    : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  const statusIcon = m.is_active ? 'fa-circle' : 'fa-minus-circle';
  const statusText = m.is_active ? 'Active' : 'Inactive';

  // Credit color based on status
  let creditClass;
  if (creditStatus === 'ok') {
    creditClass = 'text-gray-900 dark:text-white';
  } else if (creditStatus === 'low') {
    creditClass = 'text-yellow-600 dark:text-yellow-400';
  } else {
    creditClass = 'text-red-600';
  }

  // Communication status
  const commClass = m.communication_status === 'online' ? 'text-green-600' : 'text-gray-500';
  const commStatus = m.communication_status ? m.communication_status.charAt(0).toUpperCase() + m.communication_status.slice(1) : '';

  // Actions
  let actionsHtml = `<a class="text-primary hover:text-blue-700 mr-3" title="View Details" href="/api/v1/meters/${m.device_eui || m.id}/details"><i class="fas fa-eye"></i></a>`;
  if (permissions.canEdit) {
    actionsHtml += `<button class="text-primary hover:text-blue-700 mr-3 edit-meter-btn" title="Edit" data-meter="${meterJson}"><i class="fas fa-edit"></i></button>`;
  }
  if (permissions.canDelete) {
    actionsHtml += `<button class="text-red-600 dark:text-red-400 hover:text-red-700 delete-meter-btn" title="Delete" data-meter="${meterJson}"><i class="fas fa-trash"></i></button>`;
  }

  return `
    <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600" data-meter="${meterJson}">
      <td class="px-6 py-4 font-mono text-xs text-gray-900 dark:text-white">${deviceId}</td>
      <td class="px-6 py-4">${locationHtml}</td>
      <td class="px-6 py-4">
        <span class="inline-flex items-center px-2 py-1 rounded text-xs ${typeClass}">
          <i class="fas ${typeIcon} mr-1"></i>${typeName}
        </span>
      </td>
      <td class="px-6 py-4">
        <span class="inline-flex items-center px-2 py-1 rounded text-xs ${statusClass}">
          <i class="fas ${statusIcon} mr-1"></i>${statusText}
        </span>
      </td>
      <td class="px-6 py-4">
        <div class="text-sm font-semibold ${creditClass}">R ${formatNumber(balance)}</div>
        <div class="text-xs text-gray-500">&nbsp;</div>
      </td>
      <td class="px-6 py-4">
        <div class="text-sm text-gray-500">--</div>
        <div class="text-xs text-gray-500">&nbsp;</div>
      </td>
      <td class="px-6 py-4">
        <div class="text-sm text-gray-900 dark:text-white">${m.last_reading_date || '--'}</div>
        <div class="text-xs ${commClass}">${commStatus}</div>
      </td>
      <td class="px-6 py-4">${actionsHtml}</td>
    </tr>
  `;
}

// Attach event listeners to dynamically rendered action buttons
function attachMeterRowEventListeners() {
  // Edit buttons
  document.querySelectorAll(".edit-meter-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const data = JSON.parse(this.dataset.meter);
      openEditMeterFromData(data);
    });
  });

  // Delete buttons
  document.querySelectorAll(".delete-meter-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const data = JSON.parse(this.dataset.meter);
      window._deleteMeterId = data.id;
      const deleteModal = document.getElementById("deleteMeterModal");
      deleteModal.classList.remove("hidden");
      deleteModal.classList.add("flex");
    });
  });
}

// Edit meter from data object
function openEditMeterFromData(data) {
  const editModal = document.getElementById("editMeterModal");
  const form = document.getElementById("editMeterForm");
  form.elements.id.value = data.id;
  form.elements.device_eui.value = data.device_eui || "";
  form.elements.serial_number.value = data.serial_number || "";
  form.elements.meter_type.value = data.meter_type || "";
  form.elements.installation_date.value =
    (data.installation_date || "").split("T")[0] || "";
  form.elements.status.value = data.is_active ? "active" : "inactive";
  // preselect estate if available via unit
  if (data.unit && data.unit.estate_id) {
    form.elements.estate_id.value = data.unit.estate_id;
  } else if (data.assigned_estate && data.assigned_estate.id) {
    form.elements.estate_id.value = data.assigned_estate.id;
  } else {
    form.elements.estate_id.value = "";
  }
  // Filter units by estate first, then set the unit value
  filterUnitsByEstate(form);
  if (data.unit && data.unit.id) {
    form.elements.unit_id.value = data.unit.id;
  } else {
    form.elements.unit_id.value = "";
  }
  editModal.classList.remove("hidden");
  editModal.classList.add("flex");
  refreshUnitDisableState(form);
}

// Refresh the table after CRUD operations
function refreshMetersTable() {
  if (metersTableFilter) {
    metersTableFilter.refresh();
  } else {
    window.location.reload();
  }
}

// Refresh unit dropdowns with fresh data from server
async function refreshUnitDropdowns() {
  try {
    const resp = await fetch(UNITS_API_URL);
    if (!resp.ok) return;
    const data = await resp.json();
    const units = data.units || [];

    // Update both create and edit form dropdowns
    ['createMeterForm', 'editMeterForm'].forEach(formId => {
      const form = document.getElementById(formId);
      if (!form) return;
      const unitSelect = form.elements.unit_id;
      if (!unitSelect) return;

      // Preserve current selection
      const currentValue = unitSelect.value;

      // Clear existing options except the first "Unassigned" option
      while (unitSelect.options.length > 1) {
        unitSelect.remove(1);
      }

      // Add fresh unit options
      units.forEach(u => {
        const opt = document.createElement('option');
        opt.value = u.id;
        opt.textContent = `Unit ${u.unit_number} (${u.estate_name})`;
        opt.setAttribute('data-estate-id', u.estate_id);
        opt.setAttribute('data-has-electricity', u.has_electricity ? '1' : '0');
        opt.setAttribute('data-has-water', u.has_water ? '1' : '0');
        opt.setAttribute('data-has-solar', u.has_solar ? '1' : '0');
        opt.setAttribute('data-has-hot-water', u.has_hot_water ? '1' : '0');
        unitSelect.appendChild(opt);
      });

      // Restore selection if it still exists
      if (currentValue) {
        unitSelect.value = currentValue;
      }
    });
  } catch (e) {
    console.error('Error refreshing unit dropdowns:', e);
  }
}

function openEditMeter(btn) {
  const row = btn.closest("tr");
  const data = JSON.parse(row.getAttribute("data-meter"));
  const editModal = document.getElementById("editMeterModal");
  const form = document.getElementById("editMeterForm");
  form.elements.id.value = data.id;
  form.elements.device_eui.value = data.device_eui || "";
  form.elements.serial_number.value = data.serial_number || "";
  form.elements.meter_type.value = data.meter_type || "";
  form.elements.installation_date.value =
    (data.installation_date || "").split("T")[0] || "";
  form.elements.status.value = data.is_active ? "active" : "inactive";
  // preselect estate if available via unit
  if (data.unit && data.unit.estate_id) {
    form.elements.estate_id.value = data.unit.estate_id;
  } else if (data.assigned_estate && data.assigned_estate.id) {
    form.elements.estate_id.value = data.assigned_estate.id;
  } else {
    form.elements.estate_id.value = "";
  }
  // Filter units by estate first, then set the unit value
  filterUnitsByEstate(form);
  if (data.unit && data.unit.id) {
    form.elements.unit_id.value = data.unit.id;
  } else {
    form.elements.unit_id.value = "";
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
  const form = scope || document.getElementById("editMeterForm");
  if (!form || !form.elements.meter_type || !form.elements.unit_id) return;
  const type = form.elements.meter_type.value;
  const unitSelect = form.elements.unit_id;
  Array.from(unitSelect.options).forEach((opt) => {
    if (!opt.value) return;
    const hasElec = opt.getAttribute("data-has-electricity") === "1";
    const hasWater = opt.getAttribute("data-has-water") === "1";
    const hasSolar = opt.getAttribute("data-has-solar") === "1";
    const hasHotWater = opt.getAttribute("data-has-hot-water") === "1";
    let disabled = false;
    if (type === "electricity" && hasElec) disabled = true;
    if (type === "water" && hasWater) disabled = true;
    if (type === "solar" && hasSolar) disabled = true;
    if (type === "hot_water" && hasHotWater) disabled = true;
    opt.disabled = disabled;
  });
}

// Filter units dropdown by selected estate
function filterUnitsByEstate(form) {
  const estateSelect = form.elements.estate_id;
  const unitSelect = form.elements.unit_id;
  const selectedEstateId = estateSelect.value;
  const currentUnitId = unitSelect.value;

  // Show/hide unit options based on estate
  Array.from(unitSelect.options).forEach((opt) => {
    if (!opt.value) {
      // Always show the "-- Unassigned --" option
      opt.style.display = "";
      return;
    }
    const optEstateId = opt.getAttribute("data-estate-id");
    if (!selectedEstateId || optEstateId === selectedEstateId) {
      opt.style.display = "";
    } else {
      opt.style.display = "none";
      // If currently selected unit is now hidden, reset selection
      if (opt.value === currentUnitId) {
        unitSelect.value = "";
      }
    }
  });

  // Also refresh the disable state based on meter type
  refreshUnitDisableState(form);
}

document
  .getElementById("editMeterForm")
  ?.elements.meter_type?.addEventListener("change", () =>
    refreshUnitDisableState(document.getElementById("editMeterForm"))
  );
document
  .getElementById("editMeterForm")
  ?.elements.estate_id?.addEventListener("change", () =>
    filterUnitsByEstate(document.getElementById("editMeterForm"))
  );

async function submitEditMeter() {
  const form = document.getElementById("editMeterForm");
  const payload = Object.fromEntries(new FormData(form).entries());
  const id = payload.id;
  delete payload.id;
  if (payload.installation_date === "") delete payload.installation_date;

  try {
    const resp = await fetch(`${BASE_URL}/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await resp.json();

    if (resp.ok) {
      // Success - hide modal and refresh table and unit dropdowns
      hideEditMeter();
      const successMessage = result.message || "Meter updated successfully";
      showFlashMessage(successMessage, "success", false);
      refreshMetersTable();
      refreshUnitDropdowns();
    } else {
      // Error - show message immediately WITHOUT reload
      const errorMessage = result.error || result.message || "Failed to update meter. Please try again.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (e) {
    // Network or parsing error
    console.error("Error updating meter:", e);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

async function performDeleteMeter() {
  const id = window._deleteMeterId;
  if (!id) return;

  try {
    const resp = await fetch(`${BASE_URL}/${id}`, { method: "DELETE" });

    const result = await resp.json();

    if (resp.ok && result.success) {
      // Success - hide modal and refresh table and unit dropdowns
      hideDeleteMeter();
      showFlashMessage("Meter deleted successfully", "success", false);
      refreshMetersTable();
      refreshUnitDropdowns();
    } else {
      // Error - show message immediately WITHOUT reload
      hideDeleteMeter();
      const errorMessage = result.error || result.message || "Failed to delete meter. It may be associated with units or readings.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (e) {
    // Network or parsing error
    hideDeleteMeter();
    console.error("Error deleting meter:", e);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // Initialize TableFilter for AJAX-based filtering
  metersTableFilter = new TableFilter({
    tableBodyId: 'metersTableBody',
    apiEndpoint: API_URL,
    filters: {
      search: { element: '#searchInput', param: 'search', debounce: true },
      estate: { element: '#estateFilter', param: 'estate_id' },
      meterType: { element: '#meterTypeFilter', param: 'meter_type' },
      commStatus: { element: '#commStatusFilter', param: 'communication_status' },
      creditStatus: { element: '#creditStatusFilter', param: 'credit_status' }
    },
    renderRow: renderMeterRow,
    colSpan: 8,
    onError: (error) => showFlashMessage(error, 'error', false),
    onAfterFetch: () => {
      // Re-attach event listeners after table is re-rendered
      attachMeterRowEventListeners();
    }
  });

  // Override attachRowEventListeners in the filter instance
  metersTableFilter.attachRowEventListeners = attachMeterRowEventListeners;

  // Clear filters button
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", function () {
      metersTableFilter.clearFilters();
    });
  }

  // Attach initial event listeners for server-rendered rows
  attachMeterRowEventListeners();
});
