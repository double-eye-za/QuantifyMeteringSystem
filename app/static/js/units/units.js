const BASE_URL = "/api/v1/units";

function showAddUnitModal() {
  document.getElementById("addUnitModal").classList.remove("hidden");
}

function hideAddUnitModal() {
  document.getElementById("addUnitModal").classList.add("hidden");
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
      if (!resp.ok) {
        showFlashMessage("Failed to create unit", "error", true);
      }
      await resp.json();
      hideAddUnitModal();
      window.location.reload();
      showFlashMessage("Unit created successfully", "success", true);
    } catch (e) {
      showFlashMessage("Failed to create unit", "error", true);
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
      if (!resp.ok) {
        showFlashMessage("Failed to update unit", "error", true);
      }
      await resp.json();
      hideEditUnitModal();
      window.location.reload();
      showFlashMessage("Unit updated successfully", "success", true);
    } catch (e) {
      showFlashMessage("Failed to update unit", "error", true);
    }
  })();
}

function collectUnitFormPayload() {
  const modal = document.getElementById("addUnitModal");
  const inputs = modal.querySelectorAll("input, select");
  const payload = {};
  inputs.forEach((el) => {
    const name = el.name || el.placeholder || el.id;
    if (name) {
      // Convert empty strings to null for meter IDs and other optional fields
      const value = el.value.trim();
      payload[name] = value === "" ? null : value;
    }
  });
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
    if (!resp.ok) {
      showFlashMessage("Failed to delete unit", "error", true);
    }
    window.hideDeleteUnitModal();
    window.location.reload();
    showFlashMessage("Unit deleted successfully.", "success", true);
  } catch (e) {
    console.error(e);
    showFlashMessage("Error deleting unit. Try again later.", "error", true);
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
