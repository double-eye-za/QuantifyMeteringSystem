const BASE_URL = "/api/v1/units";
const API_URL = "/api/v1/api/units";

// Global table filter instance
let unitsTableFilter = null;

// Track persons to be added to the unit
let addedPersons = [];

// Helper to format numbers
function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '0.00';
  return parseFloat(num).toFixed(decimals);
}

// Render meter cell with balance and status
function renderMeterCell(meterId, balance, isVacant, lowBalanceThreshold) {
  const meterIdDisplay = meterId || '—';
  // Use wallet's low_balance_threshold, default to 50 if not set
  const threshold = parseFloat(lowBalanceThreshold) || 50;

  if (isVacant) {
    return `
      <div class="flex flex-col items-center">
        <span class="text-xs font-mono text-gray-600 dark:text-gray-400">${meterIdDisplay}</span>
        <span class="text-xs font-semibold text-gray-500">-</span>
        <span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 mt-1">
          <i class="fas fa-pause-circle mr-1" style="font-size: 8px"></i>
          Inactive
        </span>
      </div>
    `;
  }

  const balanceNum = parseFloat(balance) || 0;
  let colorClass, statusClass, statusText, icon;

  if (balanceNum <= 0) {
    colorClass = 'text-red-600 dark:text-red-400';
    statusClass = 'bg-red-100 dark:bg-red-900/20 text-red-800 dark:text-red-400';
    statusText = 'Disconnected';
    icon = 'fa-times-circle';
  } else if (balanceNum < threshold) {
    colorClass = 'text-yellow-600 dark:text-yellow-400';
    statusClass = 'bg-yellow-100 dark:bg-yellow-900/20 text-yellow-800 dark:text-yellow-400';
    statusText = 'Low';
    icon = 'fa-exclamation-triangle';
  } else {
    colorClass = 'text-gray-900 dark:text-white';
    statusClass = 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400';
    statusText = 'Active';
    icon = 'fa-circle';
  }

  return `
    <div class="flex flex-col items-center">
      <span class="text-xs font-mono text-gray-600 dark:text-gray-400">${meterIdDisplay}</span>
      <span class="text-xs font-semibold ${colorClass}">R ${formatNumber(balanceNum)}</span>
      <span class="inline-flex items-center px-1.5 py-0.5 rounded text-xs mt-1 ${statusClass}">
        <i class="fas ${icon} mr-1" style="font-size: 8px"></i>
        ${statusText}
      </span>
    </div>
  `;
}

// Render a single unit row for the table
function renderUnitRow(u) {
  const permissions = window.UNIT_PERMISSIONS || {};
  const estatesMap = window.ESTATES_MAP || {};
  const unitJson = JSON.stringify(u).replace(/'/g, "&#39;").replace(/"/g, "&quot;");

  const estateName = estatesMap[u.estate_id] || '';
  const isVacant = u.occupancy_status === 'vacant';

  // Wallet data
  const wallet = u.wallet || {};
  const electricityBalance = wallet.electricity_balance || 0;
  const waterBalance = wallet.water_balance || 0;
  const hotWaterBalance = wallet.hot_water_balance || 0;
  const solarBalance = wallet.solar_balance || 0;
  const lowBalanceThreshold = wallet.low_balance_threshold || 50;

  // Build tenants HTML
  let tenantsHtml = '';
  if (u.tenants && u.tenants.length > 0) {
    tenantsHtml = u.tenants.map((tenant, idx) => {
      const separator = idx < u.tenants.length - 1 ? '<div class="border-t border-gray-200 dark:border-gray-700 my-1"></div>' : '';
      return `
        <p class="text-sm text-gray-900 dark:text-white">${tenant.first_name || ''} ${tenant.last_name || ''}</p>
        <p class="text-xs text-gray-500 dark:text-gray-400">${tenant.phone || ''}</p>
        ${separator}
      `;
    }).join('');
  } else if (!isVacant) {
    tenantsHtml = '<p class="text-sm text-gray-500 dark:text-gray-400">No tenant assigned</p>';
  } else {
    tenantsHtml = '<p class="text-sm text-gray-500 dark:text-gray-400">Vacant</p>';
  }

  // Build status badge
  const statusClass = u.occupancy_status === 'occupied'
    ? 'bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400'
    : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400';
  const statusText = u.occupancy_status ? u.occupancy_status.charAt(0).toUpperCase() + u.occupancy_status.slice(1) : '';

  // Build actions HTML
  let actionsHtml = '<div class="flex items-center gap-2">';
  actionsHtml += `<a href="/api/v1/units/${u.id}" class="text-primary hover:underline text-sm"><i class="fas fa-eye mr-1"></i>View</a>`;

  if (isVacant) {
    actionsHtml += `<button type="button" onclick="assignResident()" class="text-green-600 dark:text-green-400 hover:underline text-sm">Assign</button>`;
  } else if (permissions.canEdit) {
    actionsHtml += `<button type="button" class="edit-unit-btn text-gray-600 dark:text-gray-400 hover:text-primary text-sm" data-unit="${unitJson}"><i class="fas fa-edit mr-1"></i>Edit</button>`;
  }

  if (permissions.canDelete) {
    actionsHtml += `<button type="button" onclick="confirmDeleteUnit(${u.id})" class="text-red-600 dark:text-red-400 hover:underline text-sm"><i class="fas fa-trash mr-1"></i>Delete</button>`;
  }
  actionsHtml += '</div>';

  return `
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors" data-unit="${unitJson}">
      <td class="px-4 py-3"><input type="checkbox" class="rounded border-gray-300 dark:border-gray-600"/></td>
      <td class="px-4 py-3">
        <div>
          <a href="/api/v1/units/${u.id}" class="text-sm font-medium text-primary hover:text-blue-700 hover:underline cursor-pointer">Unit ${u.unit_number || ''}</a>
          <p class="text-xs text-gray-500 dark:text-gray-400">${u.floor || ''}</p>
        </div>
      </td>
      <td class="px-4 py-3 text-sm text-gray-900 dark:text-gray-300">${estateName}</td>
      <td class="px-4 py-3">
        <div>${tenantsHtml}</div>
      </td>
      <td class="px-4 py-3 text-center">${renderMeterCell(u.electricity_meter_id, electricityBalance, isVacant, lowBalanceThreshold)}</td>
      <td class="px-4 py-3 text-center">${renderMeterCell(u.water_meter_id, waterBalance, isVacant, lowBalanceThreshold)}</td>
      <td class="px-4 py-3 text-center">${renderMeterCell(u.hot_water_meter_id, hotWaterBalance, isVacant, lowBalanceThreshold)}</td>
      <td class="px-4 py-3 text-center">${renderMeterCell(u.solar_meter_id, solarBalance, isVacant, lowBalanceThreshold)}</td>
      <td class="px-4 py-3"><span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusClass}">${statusText}</span></td>
      <td class="px-4 py-3">${actionsHtml}</td>
    </tr>
  `;
}

// Attach event listeners to dynamically rendered action buttons
function attachUnitRowEventListeners() {
  // Edit buttons
  document.querySelectorAll(".edit-unit-btn").forEach((button) => {
    button.addEventListener("click", function () {
      const data = JSON.parse(this.dataset.unit);
      editUnitFromData(data);
    });
  });
}

// Edit unit from data object (instead of DOM traversal)
function editUnitFromData(data) {
  const modal = document.getElementById("editUnitModal");
  if (modal && data && data.id) modal.dataset.unitId = data.id;

  const editUnitNumber = document.getElementById("edit_unit_number");
  const editUnitFloor = document.getElementById("edit_unit_floor");
  const editUnitEstate = document.getElementById("edit_unit_estate");
  const editEmeter = document.getElementById("edit_unit_emeter");
  const editWmeter = document.getElementById("edit_unit_wmeter");
  const editHwmeter = document.getElementById("edit_unit_hwmeter");
  const editSmeter = document.getElementById("edit_unit_smeter");

  if (editUnitNumber) editUnitNumber.value = data.unit_number || "";
  if (editUnitFloor) editUnitFloor.value = data.floor || "";
  if (editUnitEstate) editUnitEstate.value = data.estate_id || "";
  if (editEmeter) editEmeter.value = data.electricity_meter_id || "";
  if (editWmeter) editWmeter.value = data.water_meter_id || "";
  if (editHwmeter) editHwmeter.value = data.hot_water_meter_id || "";
  if (editSmeter) editSmeter.value = data.solar_meter_id || "";

  showEditUnitModal();
}

// Refresh the table after CRUD operations
function refreshUnitsTable() {
  if (unitsTableFilter) {
    unitsTableFilter.refresh();
  } else {
    window.location.reload();
  }
}

function showAddUnitModal() {
  addedPersons = []; // Reset on open
  renderAddedPersonsList();
  document.getElementById("addUnitModal").classList.remove("hidden");
}

function hideAddUnitModal() {
  addedPersons = []; // Clear on close
  renderAddedPersonsList();
  document.getElementById("addUnitModal").classList.add("hidden");
}

// Add a person to the unit with their role
function addPersonToUnit() {
  const personSelect = document.getElementById("addPersonSelect");
  const roleSelect = document.getElementById("addPersonRole");

  const personId = personSelect.value;
  const personName = personSelect.options[personSelect.selectedIndex]?.text;
  const role = roleSelect.value;

  if (!personId) {
    showFlashMessage("Please select a person", "error", true);
    return;
  }

  // Check if person already added
  const exists = addedPersons.find(p => p.person_id === personId);
  if (exists) {
    showFlashMessage("This person is already added", "warning", true);
    return;
  }

  // Add to list
  addedPersons.push({
    person_id: personId,
    person_name: personName,
    role: role
  });

  // Reset selects
  personSelect.value = "";
  roleSelect.value = "tenant";

  // Re-render list
  renderAddedPersonsList();
}

// Remove a person from the list
function removePersonFromUnit(index) {
  addedPersons.splice(index, 1);
  renderAddedPersonsList();
}

// Render the list of added persons
function renderAddedPersonsList() {
  const container = document.getElementById("addedPeopleList");
  if (!container) return;

  if (addedPersons.length === 0) {
    container.innerHTML = '<p class="text-sm text-gray-500 dark:text-gray-400">No people assigned yet. Use the form below to add owners or tenants.</p>';
    return;
  }

  container.innerHTML = addedPersons.map((person, index) => `
    <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
      <div class="flex items-center gap-3">
        <i class="fas ${person.role === 'owner' ? 'fa-home text-blue-500' : 'fa-user text-green-500'}"></i>
        <div>
          <p class="text-sm font-medium text-gray-900 dark:text-white">${person.person_name}</p>
          <p class="text-xs text-gray-500 dark:text-gray-400">${person.role === 'owner' ? 'Owner' : 'Tenant'}</p>
        </div>
      </div>
      <button
        type="button"
        onclick="removePersonFromUnit(${index})"
        class="text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
      >
        <i class="fas fa-times"></i>
      </button>
    </div>
  `).join('');
}

function saveUnit() {
  (async () => {
    try {
      // Client-side required validation
      const addModal = document.getElementById("addUnitModal");
      const requiredSelectors = [
        "select[name=estate_id]",
        "input[name=unit_number]",
      ];
      const missingLabels = [];
      requiredSelectors.forEach((sel) => {
        const el = addModal ? addModal.querySelector(sel) : null;
        if (!el) return;

        el.classList.remove("ring-2", "ring-red-500", "border-red-500");
        const val = (el.value || "").trim();
        if (!val) {
          el.classList.add("ring-2", "ring-red-500", "border-red-500");

          const name = el.getAttribute("name") || sel;
          missingLabels.push(name.replace(/_/g, " "));
        }
      });
      if (missingLabels.length) {
        showFlashMessage(
          `Please fill required fields: ${missingLabels.join(", ")}`,
          "error",
          true
        );
        return;
      }

      const payload = collectUnitFormPayload();

      const resp = await fetch(`${BASE_URL}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await resp.json();

      if (resp.ok && data.data) {
        // Success - hide modal and refresh table
        hideAddUnitModal();

        // Show warnings if any
        if (data.warnings && data.warnings.length > 0) {
          const warningMsg = `Unit created but with warnings:\n${data.warnings.join('\n')}`;
          showFlashMessage(warningMsg, "warning", false);
        } else {
          showFlashMessage("Unit created successfully", "success", false);
        }

        refreshUnitsTable();
      } else {
        // Error - show message immediately WITHOUT reload
        const errorMessage = data.error || data.message || "Failed to create unit. Please check the form and try again.";
        showFlashMessage(errorMessage, "error", false);
      }
    } catch (e) {
      // Network or parsing error
      console.error("Error creating unit:", e);
      showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
    }
  })();
}

function viewUnitDetails() {
  window.location.href = "meters.html";
}

function showEditUnitModal() {
  const modal = document.getElementById("editUnitModal");
  if (modal) modal.classList.remove("hidden");
}

function hideEditUnitModal() {
  const modal = document.getElementById("editUnitModal");
  if (modal) modal.classList.add("hidden");
}

function editUnit(buttonEl) {
  const row = buttonEl ? buttonEl.closest("tr") : null;
  if (row) {
    try {
      const data = JSON.parse(row.getAttribute("data-unit"));
      const modal = document.getElementById("editUnitModal");
      if (modal && data && data.id) modal.dataset.unitId = data.id;
    } catch (_) {}
    const unitLink = row.querySelector("td:nth-child(2) a");
    const floorText = row.querySelector("td:nth-child(2) p");
    const estateCell = row.querySelector("td:nth-child(3)");
    const emeter = row.querySelector("td:nth-child(5) span.font-mono");
    const wmeter = row.querySelector("td:nth-child(6) span.font-mono");
    const hwmeter = row.querySelector("td:nth-child(7) span.font-mono");
    const smeter = row.querySelector("td:nth-child(8) span.font-mono");

    const unitNumber = unitLink
      ? unitLink.textContent.trim().replace(/^Unit\s+/i, "")
      : "";
    const floor = floorText ? floorText.textContent.trim() : "";
    const estate = estateCell ? estateCell.textContent.trim() : "";

    const editUnitNumber = document.getElementById("edit_unit_number");
    const editUnitFloor = document.getElementById("edit_unit_floor");
    const editUnitEstate = document.getElementById("edit_unit_estate");
    const editEmeter = document.getElementById("edit_unit_emeter");
    const editWmeter = document.getElementById("edit_unit_wmeter");
    const editHwmeter = document.getElementById("edit_unit_hwmeter");
    const editSmeter = document.getElementById("edit_unit_smeter");
    const editResident = document.getElementById("edit_unit_resident");

    if (editUnitNumber) editUnitNumber.value = unitNumber || "";
    if (editUnitFloor) editUnitFloor.value = floor || "";
    if (editUnitEstate) {
      Array.from(editUnitEstate.options).forEach((opt) => {
        opt.selected = opt.textContent.trim() === estate;
      });
    }
    if (editEmeter && emeter) editEmeter.value = emeter.textContent.trim();
    if (editWmeter && wmeter) editWmeter.value = wmeter.textContent.trim();
    if (editHwmeter && hwmeter) editHwmeter.value = hwmeter.textContent.trim();
    if (editSmeter && smeter) editSmeter.value = smeter.textContent.trim();
    if (editResident && row.hasAttribute("data-unit")) {
      try {
        const udata = JSON.parse(row.getAttribute("data-unit"));
        if (udata && udata.resident && udata.resident.id) {
          editResident.value = String(udata.resident.id);
        } else {
          editResident.value = "";
        }
      } catch (_) {
        editResident.value = "";
      }
    }
  }

  showEditUnitModal();
}

function saveEditedUnit() {
  (async () => {
    try {
      // Client-side required validation for edit modal
      const editModal = document.getElementById("editUnitModal");
      const requiredIds = [
        "#edit_unit_number",
        "#edit_unit_estate",
      ];
      const missing = [];
      requiredIds.forEach((sel) => {
        const el = editModal ? editModal.querySelector(sel) : null;
        if (!el) return;
        el.classList.remove("ring-2", "ring-red-500", "border-red-500");
        const val = (el.value || "").trim();
        if (!val) {
          el.classList.add("ring-2", "ring-red-500", "border-red-500");
          missing.push(sel.replace(/^#edit_unit_/, "").replace(/_/g, " "));
        }
      });
      if (missing.length) {
        showFlashMessage(
          `Please fill required fields: ${missing.join(", ")}`,
          "error",
          true
        );
        return;
      }

      const modal = document.getElementById("editUnitModal");
      const unitDataAttr =
        modal && modal.dataset && modal.dataset.unitId
          ? { id: modal.dataset.unitId }
          : null;

      let unitId = unitDataAttr ? unitDataAttr.id : null;
      if (!unitId) {
        const anySelected = document.querySelector("tr[data-unit]");
        if (anySelected) {
          try {
            unitId = JSON.parse(anySelected.getAttribute("data-unit")).id;
          } catch (_) {}
        }
      }
      if (!unitId) {
        alert("Missing unit id");
        return;
      }

      const payload = collectEditUnitFormPayload();
      const resp = await fetch(`${BASE_URL}/${unitId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const result = await resp.json();

      if (resp.ok && result.data) {
        // Success - hide modal and refresh table
        hideEditUnitModal();
        showFlashMessage("Unit updated successfully", "success", false);
        refreshUnitsTable();
      } else {
        // Error - show message immediately WITHOUT reload
        const errorMessage = result.error || result.message || "Failed to update unit. Please try again.";
        showFlashMessage(errorMessage, "error", false);
      }
    } catch (e) {
      // Network or parsing error
      console.error("Error updating unit:", e);
      showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
    }
  })();
}

function collectUnitFormPayload() {
  const modal = document.getElementById("addUnitModal");
  const inputs = modal.querySelectorAll("input, select");
  const payload = {};
  inputs.forEach((el) => {
    const name = el.name || el.placeholder || el.id;
    // Skip person-related inputs as they're handled separately
    if (name && name !== 'addPersonSelect' && name !== 'addPersonRole') {
      // Convert empty strings to null for meter IDs and other optional fields
      const value = el.value.trim();
      payload[name] = value === "" ? null : value;
    }
  });

  // Add owners and tenants arrays
  payload.owners = addedPersons.filter(p => p.role === 'owner').map(p => ({
    person_id: parseInt(p.person_id, 10)
  }));
  payload.tenants = addedPersons.filter(p => p.role === 'tenant').map(p => ({
    person_id: parseInt(p.person_id, 10)
  }));

  return payload;
}

function collectEditUnitFormPayload() {
  const modal = document.getElementById("editUnitModal");

  // Helper to convert empty string to null
  const valueOrNull = (value) => (value && value.trim() !== "" ? value : null);

  const payload = {
    unit_number: document.getElementById("edit_unit_number")?.value || "",
    floor: document.getElementById("edit_unit_floor")?.value || "",
    estate_id: valueOrNull(document.getElementById("edit_unit_estate")?.value),
    electricity_meter_id: valueOrNull(document.getElementById("edit_unit_emeter")?.value),
    water_meter_id: valueOrNull(document.getElementById("edit_unit_wmeter")?.value),
    hot_water_meter_id: valueOrNull(document.getElementById("edit_unit_hwmeter")?.value),
    solar_meter_id: valueOrNull(document.getElementById("edit_unit_smeter")?.value),
  };
  return payload;
}

function assignResident() {
  alert("Assign resident modal would open here");
}

let deleteUnitId = null;
window.confirmDeleteUnit = function (unitId) {
  try {
    deleteUnitId = unitId;
    const modal = document.getElementById("deleteUnitModal");
    if (modal) {
      modal.classList.remove("hidden");
      modal.classList.add("flex");
    }
  } catch (e) {
    console.error(e);
  }
};
window.hideDeleteUnitModal = function () {
  try {
    const modal = document.getElementById("deleteUnitModal");
    if (modal) {
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }
  } catch (e) {
    console.error(e);
  }
};
window.performDeleteUnit = async function () {
  try {
    if (!deleteUnitId) return;

    const resp = await fetch(`${BASE_URL}/${deleteUnitId}`, {
      method: "DELETE",
    });

    const result = await resp.json();

    if (resp.ok) {
      // Success - hide modal and refresh table
      window.hideDeleteUnitModal();
      showFlashMessage("Unit deleted successfully", "success", false);
      refreshUnitsTable();
    } else {
      // Error - show message immediately WITHOUT reload
      window.hideDeleteUnitModal();
      const errorMessage = result.error || result.message || "Failed to delete unit. It may be associated with meters or other data.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (e) {
    // Network or parsing error
    window.hideDeleteUnitModal();
    console.error("Error deleting unit:", e);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
};

document.addEventListener("DOMContentLoaded", function () {
  // Initialize TableFilter for AJAX-based filtering
  unitsTableFilter = new TableFilter({
    tableBodyId: 'unitsTableBody',
    apiEndpoint: API_URL,
    filters: {
      search: { element: '#searchInput', param: 'q', debounce: true },
      estate: { element: '#estateFilter', param: 'estate_id' },
      status: { element: '#statusFilter', param: 'occupancy_status' }
    },
    renderRow: renderUnitRow,
    colSpan: 10,
    onError: (error) => showFlashMessage(error, 'error', false),
    onAfterFetch: () => {
      // Re-attach event listeners after table is re-rendered
      attachUnitRowEventListeners();
    }
  });

  // Override attachRowEventListeners in the filter instance
  unitsTableFilter.attachRowEventListeners = attachUnitRowEventListeners;

  // Clear filters button
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", function () {
      unitsTableFilter.clearFilters();
    });
  }

  // Attach initial event listeners for server-rendered rows
  attachUnitRowEventListeners();
});
