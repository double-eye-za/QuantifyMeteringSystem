const BASE_URL = "/api/v1";

async function saveEstateAssignment(estateId) {
  const body = {
    electricity_rate_table_id:
      document.getElementById(`elec_rate_${estateId}`).value || null,
    water_rate_table_id:
      document.getElementById(`water_rate_${estateId}`).value || null,
    electricity_markup_percentage: parseFloat(
      document.getElementById(`elec_markup_${estateId}`).value || "0"
    ),
    water_markup_percentage: parseFloat(
      document.getElementById(`water_markup_${estateId}`).value || "0"
    ),
    solar_free_allocation_kwh: parseFloat(
      document.getElementById(`solar_free_${estateId}`).value || "0"
    ),
  };
  try {
    const res = await fetch(
      `${BASE_URL}/api/estates/${estateId}/rate-assignment`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    );
    const result = await res.json();
    if (res.ok) {
      showFlashMessage("Estate rate assignment saved", "success");
    } else {
      showFlashMessage(result.error || "Failed to save assignment", "error");
    }
  } catch (e) {
    showFlashMessage("Network error while saving assignment", "error");
  }
}

// Rate Preview Calculator wiring
async function previewRates() {
  const estateSelect = document.querySelector("#previewEstate");
  const elecInput = document.querySelector("#previewKwh");
  const waterInput = document.querySelector("#previewKl");
  try {
    const estateId = estateSelect ? estateSelect.value || null : null;
    let elecRtId = null,
      waterRtId = null,
      elecMarkup = 0,
      waterMarkup = 0,
      fee = 0;
    if (estateId) {
      const res = await fetch(`${BASE_URL}/estates/${estateId}`);
      const js = await res.json();
      if (res.ok && js.data) {
        const e = js.data;
        elecRtId = e.electricity_rate_table_id || null;
        waterRtId = e.water_rate_table_id || null;
        elecMarkup = e.electricity_markup_percentage || 0;
        waterMarkup = e.water_markup_percentage || 0;
        fee = 0;
      }
    }
    const payload = {
      electricity_kwh: parseFloat(elecInput ? elecInput.value || "0" : "0"),
      water_kl: parseFloat(waterInput ? waterInput.value || "0" : "0"),
      electricity_rate_table_id: elecRtId,
      water_rate_table_id: waterRtId,
      electricity_markup_percentage: elecMarkup,
      water_markup_percentage: waterMarkup,
      service_fee: fee,
    };
    const resp = await fetch(`${BASE_URL}/api/rate-tables/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    let out = await resp.json();
    if (resp.status === 404) {
      const resp2 = await fetch(`${BASE_URL}/rate-tables/preview`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      out = await resp2.json();
      if (!resp2.ok) throw new Error(out.error || "Failed preview");
      resp.ok = resp2.ok;
    }
    if (!resp.ok) throw new Error(out.error || "Failed preview");
    const d = out.data || {};
    const elecEl = document.querySelector("#previewElecTotal");
    const waterEl = document.querySelector("#previewWaterTotal");
    const feeEl = document.querySelector("#previewServiceFee");
    const totalEl = document.querySelector("#previewTotal");
    if (elecEl)
      elecEl.textContent = `R ${Number(d.electricity_total || 0).toFixed(2)}`;
    if (waterEl)
      waterEl.textContent = `R ${Number(d.water_total || 0).toFixed(2)}`;
    if (feeEl) feeEl.textContent = `R ${Number(d.service_fee || 0).toFixed(2)}`;
    if (totalEl) totalEl.textContent = `R ${Number(d.total || 0).toFixed(2)}`;
  } catch (err) {
    showFlashMessage("Failed to preview rates", "error");
  }
}

// Unit Overrides wiring
async function applyUnitOverrides() {
  const estateSelect = document.querySelector("#overrideEstate");
  const unitSelect = document.querySelector("#overrideUnitId");
  const rateSelect = document.querySelector("#overrideRateTable");
  const payload = {
    estate_id: estateSelect ? estateSelect.value || null : null,
    unit_ids:
      unitSelect && unitSelect.value ? [parseInt(unitSelect.value, 10)] : [],
    rate_table_id: rateSelect ? rateSelect.value || null : null,
  };
  try {
    const res = await fetch(`${BASE_URL}/api/units/overrides`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const result = await res.json();
    if (res.ok) {
      showFlashMessage("Override applied", "success");
      await refreshOverrides();
    } else {
      showFlashMessage(result.error || "Failed to apply override", "error");
    }
  } catch (e) {
    showFlashMessage("Network error while applying override", "error");
  }
}

async function refreshOverrides() {
  try {
    const res = await fetch(`${BASE_URL}/api/units/overrides`);
    const js = await res.json();
    const data = js.data || {};
    const container = document.querySelector("#currentOverrides");
    if (!container) return;
    container.innerHTML = "";
    const entries = Object.entries(data);
    if (!entries.length) {
      container.innerHTML =
        '<p class="text-xs text-gray-500">No overrides found</p>';
      return;
    }
    for (const [unitId, entry] of entries) {
      const label = `Unit ${unitId}`;
      const rtTags = [
        entry.electricity_rate_table_id
          ? `<span class=\"px-2 py-1 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 text-xs rounded-full\">Elec: #${entry.electricity_rate_table_id}</span>`
          : "",
        entry.water_rate_table_id
          ? `<span class=\"px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 text-xs rounded-full\">Water: #${entry.water_rate_table_id}</span>`
          : "",
      ]
        .filter(Boolean)
        .join(" ");
      const row = document.createElement("div");
      row.className =
        "flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700/50 rounded";
      row.innerHTML = `<div class=\"flex items-center gap-4\"><span class=\"text-sm font-medium text-gray-900 dark:text-white\">${label}</span>${rtTags}</div>`;
      container.appendChild(row);
    }
  } catch (_) {
    console.error("Failed to refresh overrides");
  }
}

async function openEditRateTable(id) {
  try {
    const res = await fetch(`${BASE_URL}/api/rate-tables/${id}/details`);
    const js = await res.json();
    if (!res.ok) throw new Error(js.error || "Failed to fetch");
    const d = js.data || {};
    document.getElementById("editRateId").value = d.id;
    document.getElementById("editRateName").value = d.name || "";
    document.getElementById("editRateUtility").value =
      d.utility_type || "electricity";
    document.getElementById("editRateFrom").value = (
      d.effective_from || ""
    ).substring(0, 10);
    document.getElementById("editRateTo").value = (
      d.effective_to || ""
    ).substring(0, 10);
    document.getElementById("editRateActive").checked = !!d.is_active;
    const tiers =
      d.tiers && d.tiers.length ? { tiers: d.tiers } : d.rate_structure || {};
    document.getElementById("editRateTiers").value = JSON.stringify(
      tiers,
      null,
      2
    );
    const modal = document.getElementById("editRateModal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  } catch (e) {
    showFlashMessage(e.message || "Failed to load rate table", "error");
  }
}

function hideEditRateModal() {
  const modal = document.getElementById("editRateModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

document
  .getElementById("editRateForm")
  ?.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const id = document.getElementById("editRateId").value;
    try {
      const payload = {
        name: document.getElementById("editRateName").value,
        utility_type: document.getElementById("editRateUtility").value,
        effective_from: document.getElementById("editRateFrom").value || null,
        effective_to: document.getElementById("editRateTo").value || null,
        is_active: document.getElementById("editRateActive").checked,
        rate_structure: JSON.parse(
          document.getElementById("editRateTiers").value || "{}"
        ),
      };
      const resp = await fetch(`${BASE_URL}/api/rate-tables/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const out = await resp.json();
      if (!resp.ok) throw new Error(out.error || "Save failed");
      showFlashMessage("Rate table saved", "success");
      hideEditRateModal();
      location.reload();
    } catch (e) {
      console.error("Error saving rate table:", e);
      showFlashMessage(e.message || "Failed to save rate table", "error");
    }
  });

function gotoEditRateTable(id) {
  window.location = `${BASE_URL}/rate-tables/${id}/edit`;
}

function openDeleteRateTable(id, name) {
  const modal = document.getElementById("deleteRateModal");
  document.getElementById(
    "deleteRateText"
  ).textContent = `Are you sure you want to delete "${name}"? This cannot be undone.`;
  modal.dataset.id = id;
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hideDeleteRateTable() {
  const modal = document.getElementById("deleteRateModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
  delete modal.dataset.id;
}

document
  .getElementById("confirmDeleteBtn")
  ?.addEventListener("click", async () => {
    const modal = document.getElementById("deleteRateModal");
    const id = modal.dataset.id;
    if (!id) return;
    try {
      const resp = await fetch(`${BASE_URL}/api/rate-tables/${id}`, {
        method: "DELETE",
      });
      const out = await resp.json().catch(() => ({}));
      if (!resp.ok) throw new Error(out.error || "Delete failed");
      showFlashMessage("Rate table deleted", "success");
      hideDeleteRateTable();
      location.reload();
    } catch (e) {
      console.error("Error deleting rate table:", e);
      showFlashMessage(e.message || "Failed to delete rate table", "error");
    }
  });

document.addEventListener("DOMContentLoaded", () => {
  const calcBtn = document.querySelector("#previewCalcBtn");
  if (calcBtn) calcBtn.addEventListener("click", previewRates);
  const applyBtn = document.querySelector("#applyOverrideBtn");
  if (applyBtn) applyBtn.addEventListener("click", applyUnitOverrides);
  const estateSel = document.querySelector("#overrideEstate");
  if (estateSel) {
    estateSel.addEventListener("change", async (e) => {
      const estId = e.target.value;
      const unitSel = document.querySelector("#overrideUnitId");
      if (!unitSel) return;
      unitSel.innerHTML = '<option value="">Loading units...</option>';
      if (!estId) {
        unitSel.innerHTML = '<option value="">Select Unit</option>';
        return;
      }
      try {
        const res = await fetch(
          `${BASE_URL}/api/units?estate_id=${encodeURIComponent(estId)}`
        );
        const js = await res.json();
        const items = js.data || [];
        unitSel.innerHTML = '<option value="">Select Unit</option>';
        for (const u of items) {
          const opt = document.createElement("option");
          opt.value = u.id;
          opt.textContent = u.unit_number || `Unit ${u.id}`;
          unitSel.appendChild(opt);
        }
      } catch (err) {
        console.error("Failed to load units for estate:", err);
        unitSel.innerHTML = '<option value="">Select Unit</option>';
      }
    });
  }
  refreshOverrides();
});
