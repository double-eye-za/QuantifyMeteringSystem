const BASE_URL = "/api/v1/units";

// Track persons to be added to the unit
let addedPersons = [];

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

      if (resp.ok && (data.success || data.id)) {
        // Success - hide modal and reload with success message
        hideAddUnitModal();

        // Show warnings if any
        if (data.warnings && data.warnings.length > 0) {
          const warningMsg = `Unit created but with warnings:\n${data.warnings.join('\n')}`;
          showFlashMessage(warningMsg, "warning", true);
        } else {
          showFlashMessage("Unit created successfully", "success", true);
        }

        window.location.reload();
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

      if (resp.ok && result.success) {
        // Success - hide modal and reload with success message
        hideEditUnitModal();
        showFlashMessage("Unit updated successfully", "success", true);
        window.location.reload();
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

    if (resp.ok && result.success) {
      // Success - hide modal and reload with success message
      window.hideDeleteUnitModal();
      showFlashMessage("Unit deleted successfully", "success", true);
      window.location.reload();
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

function applyFilters() {
  const form = document.getElementById("unitFilters");
  form.submit();
}

function clearFilters() {
  document.getElementById("searchInput").value = "";
  document.getElementById("estateFilter").value = "";
  document.getElementById("statusFilter").value = "";
  const form = document.getElementById("unitFilters");
  form.submit();
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
