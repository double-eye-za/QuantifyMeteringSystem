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

function updateRateTypes() {
  const resourceType = document.getElementById("resourceType").value;
  const hotWaterSection = document.getElementById("hotWaterSection");
  const pricingModels = document.getElementById("pricingModelsContainer");

  if (resourceType === "hot_water") {
    // Hide standard pricing models and their sections
    if (pricingModels) pricingModels.classList.add("hidden");
    ["tieredSection", "touSection", "seasonalSection", "flatSection", "fixedSection", "demandSection"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add("hidden");
    });
    // Show hot water section
    if (hotWaterSection) hotWaterSection.classList.remove("hidden");
  } else {
    // Show standard pricing models, hide hot water section
    if (pricingModels) pricingModels.classList.remove("hidden");
    if (hotWaterSection) hotWaterSection.classList.add("hidden");
  }
}

function toggleHotWaterModel(component) {
  if (component === "water") {
    const model = document.querySelector('input[name="hwWaterModel"]:checked')?.value || "flat";
    const flatDiv = document.getElementById("hwWaterFlat");
    const tieredDiv = document.getElementById("hwWaterTiered");
    if (model === "flat") {
      flatDiv.classList.remove("hidden");
      tieredDiv.classList.add("hidden");
    } else {
      flatDiv.classList.add("hidden");
      tieredDiv.classList.remove("hidden");
      // Add initial tier if none exist
      if (document.getElementById("hwWaterTiers").children.length === 0) {
        addHwWaterTier();
      }
    }
  }
}

function addHwWaterTier() {
  const container = document.getElementById("hwWaterTiers");
  const idx = container.children.length + 1;
  const div = document.createElement("div");
  div.className = "flex items-center gap-3";
  div.innerHTML = `
    <span class="text-sm font-medium w-16 text-gray-900 dark:text-white">Tier ${idx}:</span>
    <input type="number" placeholder="From" class="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${idx === 1 ? 0 : ''}" />
    <span class="text-gray-900 dark:text-white">-</span>
    <input type="number" placeholder="To" class="w-20 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    <span class="text-sm text-gray-900 dark:text-white">kL @ R</span>
    <input type="number" step="0.01" placeholder="Rate" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" />
    <span class="text-sm text-gray-900 dark:text-white">/kL</span>
    <button onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700"><i class="fas fa-trash"></i></button>
  `;
  container.appendChild(div);
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

function calculateBillForUsage(usage, structure) {
  let total = 0;

  // Hot water dual-component
  if (structure.water_component) {
    const volumeKl = usage / 1000.0; // usage in liters for hot water
    const conversionFactor = structure.conversion_factor || 0.065;
    const elecKwh = usage * conversionFactor;

    // Water cost
    const wc = structure.water_component;
    if (wc.flat_rate) {
      total += volumeKl * wc.flat_rate;
    } else if (wc.tiers && wc.tiers.length > 0) {
      let remaining = volumeKl;
      for (const tier of wc.tiers) {
        const from = tier.from || 0;
        const to = tier.to || Infinity;
        const range = to - from;
        const units = Math.min(remaining, range);
        if (units > 0) total += units * (tier.rate || 0);
        remaining -= units;
        if (remaining <= 0) break;
      }
    }

    // Electricity cost
    const ec = structure.electricity_component || {};
    if (ec.flat_rate) {
      total += elecKwh * ec.flat_rate;
    }

    return total;
  }

  // Tiered pricing
  if (structure.tiers && structure.tiers.length > 0) {
    let remaining = usage;
    for (const tier of structure.tiers) {
      const tierFrom = tier.from || 0;
      const tierTo = tier.to || Infinity;
      const tierRange = tierTo - tierFrom;
      const unitsInTier = Math.min(remaining, tierRange);
      if (unitsInTier > 0) {
        total += unitsInTier * (tier.rate || 0);
        remaining -= unitsInTier;
      }
      if (remaining <= 0) break;
    }
  }
  // Flat rate
  else if (structure.flat_rate) {
    total = usage * structure.flat_rate;
  }
  // Seasonal (use average of summer/winter)
  else if (structure.seasonal) {
    const avgRate = ((structure.seasonal.summer || 0) + (structure.seasonal.winter || 0)) / 2;
    total = usage * avgRate;
  }

  // Add fixed charge if present
  if (structure.fixed_charge) {
    total += structure.fixed_charge;
  }

  return total;
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

  // Hot water dual-component preview
  if (resourceType === "hot_water") {
    const structure = collectStructure();
    const wc = structure.water_component || {};
    const ec = structure.electricity_component || {};
    const cf = structure.conversion_factor || 0.065;

    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-tint text-blue-500 mr-1"></i> Water Component</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">${wc.flat_rate ? 'R ' + wc.flat_rate.toFixed(2) + '/kL (flat rate)' : wc.tiers ? wc.tiers.length + ' tier(s) configured' : 'Not configured'}</p>
      </div>
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-bolt text-yellow-500 mr-1"></i> Electricity Component (Heating)</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">${ec.flat_rate ? 'R ' + ec.flat_rate.toFixed(2) + '/kWh' : 'Not configured'}</p>
      </div>
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-exchange-alt text-gray-500 mr-1"></i> Conversion Factor</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">${cf} kWh/L</p>
      </div>
    `;
    previewHTML += "</div>";
    previewContent.innerHTML = previewHTML;
    updateSampleBills();
    return;
  }

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

  if (document.getElementById("seasonalPricing").checked) {
    previewHTML += `
                    <div class="p-3 bg-white dark:bg-gray-800 rounded">
                        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white">✓ Seasonal Pricing</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Summer and Winter rates configured</p>
                    </div>
                `;
  }

  if (document.getElementById("flatPricing").checked) {
    previewHTML += `
                    <div class="p-3 bg-white dark:bg-gray-800 rounded">
                        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white">✓ Flat Rate Pricing</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Single rate for all consumption</p>
                    </div>
                `;
  }

  if (document.getElementById("fixedPricing").checked) {
    previewHTML += `
                    <div class="p-3 bg-white dark:bg-gray-800 rounded">
                        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white">✓ Fixed Charge</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Monthly fixed fee included</p>
                    </div>
                `;
  }

  if (document.getElementById("demandPricing").checked) {
    previewHTML += `
                    <div class="p-3 bg-white dark:bg-gray-800 rounded">
                        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white">✓ Demand Charge</p>
                        <p class="text-xs text-gray-600 dark:text-gray-400">Peak demand pricing configured</p>
                    </div>
                `;
  }

  previewHTML += "</div>";
  previewContent.innerHTML = previewHTML;

  // Update sample bill calculations
  updateSampleBills();
}

function updateSampleBills() {
  const structure = collectStructure();
  const resourceType = document.getElementById("resourceType").value;
  const markup = document.getElementById("applyMarkup")?.checked ?
    parseFloat(document.querySelector('#step3Content input[type="number"]')?.value || "20") / 100 : 0;
  const vat = document.getElementById("includeVAT")?.checked ? 0.15 : 0;

  // For hot water, sample usage is in liters; for others, kWh or kL
  const isHotWater = resourceType === "hot_water";
  const usageLevels = isHotWater ? [100, 300, 600] : [50, 250, 500];
  const elementIds = ["sampleBillLow", "sampleBillMid", "sampleBillHigh"];
  const unit = isHotWater ? "L" : (resourceType === "water" ? "kL" : "kWh");

  // Update sample labels
  const labels = document.querySelectorAll("#step3Content .text-xs.text-gray-600");
  const labelTexts = isHotWater
    ? [`Low Usage (${usageLevels[0]}${unit})`, `Average (${usageLevels[1]}${unit})`, `High Usage (${usageLevels[2]}${unit})`]
    : [`Low Usage (${usageLevels[0]} ${unit})`, `Average (${usageLevels[1]} ${unit})`, `High Usage (${usageLevels[2]} ${unit})`];

  usageLevels.forEach((usage, idx) => {
    let bill = calculateBillForUsage(usage, structure);
    bill = bill * (1 + markup);
    bill = bill * (1 + vat);

    const el = document.getElementById(elementIds[idx]);
    if (el) {
      el.textContent = `R ${bill.toFixed(2)}`;
    }
  });
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

function collectHotWaterStructure() {
  const resourceType = document.getElementById("resourceType").value;
  if (resourceType !== "hot_water") return null;

  const structure = {};

  // Water component
  const waterModel = document.querySelector('input[name="hwWaterModel"]:checked')?.value || "flat";
  if (waterModel === "flat") {
    const rate = parseFloat(document.getElementById("hwWaterRate")?.value || "0");
    if (rate > 0) structure.water_component = { flat_rate: rate };
  } else {
    const rows = Array.from(document.getElementById("hwWaterTiers")?.children || []);
    const tiers = rows.map(r => {
      const inputs = r.querySelectorAll("input");
      return {
        from: parseFloat(inputs[0]?.value || "0"),
        to: inputs[1]?.value === "" ? null : parseFloat(inputs[1]?.value || "0"),
        rate: parseFloat(inputs[2]?.value || "0"),
      };
    }).filter(t => t.rate > 0);
    if (tiers.length > 0) structure.water_component = { tiers };
  }

  // Electricity component
  const elecRate = parseFloat(document.getElementById("hwElecRate")?.value || "0");
  if (elecRate > 0) structure.electricity_component = { flat_rate: elecRate };

  // Conversion factor
  structure.conversion_factor = parseFloat(document.getElementById("hwConversionFactor")?.value || "0.065");

  return Object.keys(structure).length > 0 ? structure : null;
}

function collectStructure() {
  // Hot water uses its own dual-component structure
  const hotWater = collectHotWaterStructure();
  if (hotWater) return hotWater;

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
