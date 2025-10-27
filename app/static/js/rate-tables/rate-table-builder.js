let currentStep = 1;
let tierCount = 1;

function nextStep() {
  if (currentStep < 3) {
    document
      .getElementById(`step${currentStep}Content`)
      .classList.add("hidden");
    currentStep++;
    document
      .getElementById(`step${currentStep}Content`)
      .classList.remove("hidden");
    document
      .getElementById(`step${currentStep}`)
      .classList.remove("bg-gray-300", "dark:bg-gray-600");
    document.getElementById(`step${currentStep}`).classList.add("bg-primary");

    if (currentStep > 1) {
      document.getElementById("prevBtn").classList.remove("hidden");
    }

    if (currentStep === 3) {
      document.getElementById("nextBtn").classList.add("hidden");
      document.getElementById("createBtn").classList.remove("hidden");
      generatePreview();
    }
  }
}

function previousStep() {
  if (currentStep > 1) {
    document
      .getElementById(`step${currentStep}Content`)
      .classList.add("hidden");
    document
      .getElementById(`step${currentStep}`)
      .classList.remove("bg-primary");
    document
      .getElementById(`step${currentStep}`)
      .classList.add("bg-gray-300", "dark:bg-gray-600");
    currentStep--;
    document
      .getElementById(`step${currentStep}Content`)
      .classList.remove("hidden");

    if (currentStep === 1) {
      document.getElementById("prevBtn").classList.add("hidden");
    }

    if (currentStep < 3) {
      document.getElementById("nextBtn").classList.remove("hidden");
      document.getElementById("createBtn").classList.add("hidden");
    }
  }
}

function togglePricingModel(model) {
  const section = document.getElementById(`${model}Section`);
  const checkbox = document.getElementById(`${model}Pricing`);

  if (checkbox.checked) {
    section.classList.remove("hidden");
  } else {
    section.classList.add("hidden");
  }
}

function addTier() {
  tierCount++;
  const tieredRates = document.getElementById("tieredRates");
  const newTier = document.createElement("div");
  newTier.className = "flex items-center gap-3";
  newTier.innerHTML = `
                <span class="text-sm font-medium w-20 text-gray-900 dark:text-white">Tier ${tierCount}:</span>
                <input type="number" placeholder="From" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <span class="text-gray-900 dark:text-white">-</span>
                <input type="number" placeholder="To" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <span class="text-sm text-gray-900 dark:text-white">kWh</span>
                <span class="text-sm text-gray-900 dark:text-white">@</span>
                <span class="text-sm text-gray-900 dark:text-white">R</span>
                <input type="number" step="0.01" placeholder="Rate" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <span class="text-sm text-gray-900 dark:text-white">/kWh</span>
                <button onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700">
                    <i class="fas fa-trash"></i>
                </button>
            `;
  tieredRates.appendChild(newTier);
}

function generatePreview() {
  const previewContent = document.getElementById("previewContent");
  const rateName =
    document.getElementById("rateName").value || "Unnamed Rate Table";
  const resourceType =
    document.getElementById("resourceType").value || "electricity";

  let previewHTML = `
                <div class="mb-4">
                    <h3 class="font-semibold text-lg text-gray-900 dark:text-white">${rateName}</h3>
                    <p class="text-sm text-gray-600 dark:text-gray-400">Resource: ${
                      resourceType.charAt(0).toUpperCase() +
                      resourceType.slice(1)
                    }</p>
                </div>
                <div class="space-y-2">
            `;

  // Add configured pricing models to preview
  if (document.getElementById("tieredPricing").checked) {
    previewHTML += `
                    <div class="p-3 bg-white dark:bg-gray-800 rounded">
                        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white">✓ Tiered Pricing Structure</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Multiple consumption tiers configured</p>
                    </div>
                `;
  }

  if (document.getElementById("touPricing").checked) {
    previewHTML += `
                    <div class="p-3 bg-white dark:bg-gray-800 rounded">
                        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white">✓ Time of Use Pricing</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Peak, Standard, and Off-Peak rates</p>
                    </div>
                `;
  }

  previewHTML += "</div>";
  previewContent.innerHTML = previewHTML;
}

function previewRates() {
  generatePreview();
  alert("Preview updated in Step 3");
}

function collectTieredStructure() {
  const rows = Array.from(document.getElementById("tieredRates").children);
  if (!document.getElementById("tieredPricing").checked || rows.length === 0)
    return null;
  const tiers = [];
  let currentFrom = 0;
  rows.forEach((row, idx) => {
    const inputs = row.querySelectorAll("input");
    const toVal = parseFloat(inputs[1]?.value || "0");
    const rateVal = parseFloat(inputs[2]?.value || "0");
    const entry = {
      from: currentFrom,
      to: isFinite(toVal) ? toVal : null,
      rate: rateVal,
    };
    tiers.push(entry);
    currentFrom = isFinite(toVal) ? toVal : currentFrom;
  });
  return { tiers };
}

function collectFlatStructure() {
  if (!document.getElementById("flatPricing").checked) return null;
  const rateInput = document.querySelector('#flatSection input[type="number"]');
  const rate = parseFloat(rateInput?.value || "0");
  return { flat_rate: rate };
}

function collectSeasonalStructure() {
  if (!document.getElementById("seasonalPricing").checked) return null;
  const seasonalSection = document.getElementById("seasonalSection");
  if (!seasonalSection || seasonalSection.classList.contains("hidden"))
    return null;
  const inputs = seasonalSection.querySelectorAll("input[type='number']");
  const summer = parseFloat(inputs[0]?.value || "0");
  const winter = parseFloat(inputs[1]?.value || "0");
  if (summer === 0 && winter === 0) return null;
  return { seasonal: { summer, winter } };
}

function collectTouStructure() {
  if (!document.getElementById("touPricing").checked) return null;
  const touSection = document.getElementById("touSection");
  if (!touSection || touSection.classList.contains("hidden")) return null;
  const rows = touSection.querySelectorAll("div.flex.items-center.gap-3");
  const periods = [];
  rows.forEach((row) => {
    const inputs = row.querySelectorAll("input");
    const labelSpan = row.querySelector("span.text-sm.font-medium");
    const name = labelSpan?.textContent?.replace(":", "").trim() || "Unknown";
    const start = inputs[0]?.value || "00:00";
    const end = inputs[1]?.value || "00:00";
    const rate = parseFloat(inputs[2]?.value || "0");
    if (rate > 0) {
      periods.push({
        period_name: name,
        start_time: start,
        end_time: end,
        rate,
      });
    }
  });
  if (periods.length === 0) return null;
  return { time_of_use: periods };
}

function collectFixedChargeStructure() {
  if (!document.getElementById("fixedPricing").checked) return null;
  const fixedSection = document.getElementById("fixedSection");
  if (!fixedSection || fixedSection.classList.contains("hidden")) return null;
  const input = fixedSection.querySelector("input[type='number']");
  const charge = parseFloat(input?.value || "0");
  if (charge === 0) return null;
  return { fixed_charge: charge };
}

function collectDemandChargeStructure() {
  if (!document.getElementById("demandPricing").checked) return null;
  const demandSection = document.getElementById("demandSection");
  if (!demandSection || demandSection.classList.contains("hidden")) return null;
  const input = demandSection.querySelector("input[type='number']");
  const charge = parseFloat(input?.value || "0");
  if (charge === 0) return null;
  return { demand_charge: charge };
}

function collectStructure() {
  const out = {};
  const tiered = collectTieredStructure();
  if (tiered) Object.assign(out, tiered);
  const flat = collectFlatStructure();
  if (flat) Object.assign(out, flat);
  const seasonal = collectSeasonalStructure();
  if (seasonal) Object.assign(out, seasonal);
  const tou = collectTouStructure();
  if (tou) Object.assign(out, tou);
  const fixed = collectFixedChargeStructure();
  if (fixed) Object.assign(out, fixed);
  const demand = collectDemandChargeStructure();
  if (demand) Object.assign(out, demand);
  return out;
}

async function createRateTable() {
  try {
    const name = document.getElementById("rateName").value.trim();
    const utility = document.getElementById("resourceType").value;
    const effFrom = document.getElementById("effectiveDate").value;
    const effTo = document.getElementById("effectiveTo").value;
    if (!name || !utility || !effFrom) {
      showFlashMessage("Please complete the required fields", "error");
      return;
    }
    const structure = collectStructure();
    if (Object.keys(structure).length === 0) {
      showFlashMessage(
        "Please configure at least one pricing structure",
        "error"
      );
      return;
    }
    const payload = {
      name,
      utility_type: utility,
      effective_from: effFrom,
      effective_to: effTo || null,
      is_active: true,
      rate_structure: structure,
    };
    const res = await fetch("/api/v1/api/rate-tables", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const out = await res.json();
    if (!res.ok) throw new Error(out.error || "Failed to create");
    showFlashMessage("Rate table created", "success", true);
    window.location = "/api/v1/rate-tables";
  } catch (e) {
    showFlashMessage(e.message || "Failed to create rate table", "error");
  }
}
