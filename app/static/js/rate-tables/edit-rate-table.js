let currentStep = 1;
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
    if (currentStep > 1)
      document.getElementById("prevBtn").classList.remove("hidden");
    if (currentStep === 3) {
      document.getElementById("nextBtn").classList.add("hidden");
      document.getElementById("saveBtn").classList.remove("hidden");
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
    if (currentStep < 3) {
      document.getElementById("nextBtn").classList.remove("hidden");
      document.getElementById("saveBtn").classList.add("hidden");
    }
    if (currentStep === 1) {
      document.getElementById("prevBtn").classList.add("hidden");
    }
  }
}

function toggleModel(model) {
  const section = document.getElementById(`${model}Section`);
  const checked = document.getElementById(`${model}Pricing`).checked;
  if (checked) section.classList.remove("hidden");
  else section.classList.add("hidden");
}

function updateRateTypes() {
  const resourceType = document.getElementById("rtUtility").value;
  const hotWaterSection = document.getElementById("hotWaterSection");
  const pricingModels = document.getElementById("pricingModelsContainer");

  if (resourceType === "hot_water") {
    if (pricingModels) pricingModels.classList.add("hidden");
    ["tieredSection", "touSection", "seasonalSection", "flatSection", "fixedSection", "demandSection"].forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add("hidden");
    });
    if (hotWaterSection) hotWaterSection.classList.remove("hidden");
  } else {
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

function addTierRow(row) {
  const container = document.getElementById("tieredRates");
  const div = document.createElement("div");
  div.className = "flex items-center gap-3";
  div.innerHTML = `
      <span class="text-sm font-medium w-20 text-gray-900 dark:text-white">Tier:</span>
      <input type="number" placeholder="From" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.from ?? 0
      }" />
      <span class="text-gray-900 dark:text-white">-</span>
      <input type="number" placeholder="To" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.to ?? ""
      }" />
      <span class="text-sm text-gray-900 dark:text-white">@</span>
      <span class="text-sm text-gray-900 dark:text-white">R</span>
      <input type="number" step="0.01" placeholder="Rate" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.rate ?? 0
      }" />
      <button onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700"><i class="fas fa-trash"></i></button>
    `;
  container.appendChild(div);
}

function addTouRow(row) {
  const container = document.getElementById("touRates");
  const div = document.createElement("div");
  div.className = "flex items-center gap-3";
  div.innerHTML = `
      <input type="text" placeholder="Period name" class="w-32 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.period_name ?? ""
      }" />
      <input type="time" class="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.start_time ?? ""
      }" />
      <span class="text-gray-900 dark:text-white">to</span>
      <input type="time" class="px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.end_time ?? ""
      }" />
      <label class="text-xs flex items-center gap-1 text-gray-900 dark:text-white"><input type="checkbox" ${
        row?.weekdays ? "checked" : ""
      }/> Weekdays</label>
      <label class="text-xs flex items-center gap-1 text-gray-900 dark:text-white"><input type="checkbox" ${
        row?.weekends ? "checked" : ""
      }/> Weekends</label>
      <span class="text-sm text-gray-900 dark:text-white">R</span>
      <input type="number" step="0.01" placeholder="Rate" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white" value="${
        row?.rate ?? 0
      }" />
      <button onclick="this.parentElement.remove()" class="text-red-500 hover:text-red-700"><i class="fas fa-trash"></i></button>
    `;
  container.appendChild(div);
}

function collectSeasonalStructure() {
  if (!document.getElementById("seasonalPricing")?.checked) return null;
  const seasonalSection = document.getElementById("seasonalSection");
  if (!seasonalSection || seasonalSection.classList.contains("hidden"))
    return null;
  const inputs = seasonalSection.querySelectorAll("input[type='number']");
  const summer = parseFloat(inputs[0]?.value || "0");
  const winter = parseFloat(inputs[1]?.value || "0");
  if (summer === 0 && winter === 0) return null;
  return { seasonal: { summer, winter } };
}

function collectFixedChargeStructure() {
  if (!document.getElementById("fixedPricing")?.checked) return null;
  const fixedSection = document.getElementById("fixedSection");
  if (!fixedSection || fixedSection.classList.contains("hidden")) return null;
  const input = fixedSection.querySelector("input[type='number']");
  const charge = parseFloat(input?.value || "0");
  if (charge === 0) return null;
  return { fixed_charge: charge };
}

function collectDemandChargeStructure() {
  if (!document.getElementById("demandPricing")?.checked) return null;
  const demandSection = document.getElementById("demandSection");
  if (!demandSection || demandSection.classList.contains("hidden")) return null;
  const input = demandSection.querySelector("input[type='number']");
  const charge = parseFloat(input?.value || "0");
  if (charge === 0) return null;
  return { demand_charge: charge };
}

function collectHotWaterStructure() {
  const resourceType = document.getElementById("rtUtility")?.value;
  if (resourceType !== "hot_water") return null;

  const structure = {};
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

  const elecRate = parseFloat(document.getElementById("hwElecRate")?.value || "0");
  if (elecRate > 0) structure.electricity_component = { flat_rate: elecRate };

  structure.conversion_factor = parseFloat(document.getElementById("hwConversionFactor")?.value || "0.065");

  return Object.keys(structure).length > 0 ? structure : null;
}

function collectStructure() {
  // Hot water uses its own dual-component structure
  const hotWater = collectHotWaterStructure();
  if (hotWater) return hotWater;

  const structure = {};
  if (document.getElementById("tieredPricing")?.checked) {
    const rows = Array.from(
      document.getElementById("tieredRates")?.children || []
    );
    const tiers = rows
      .map((r) => {
        const inputs = r.querySelectorAll("input");
        return {
          from: parseFloat(inputs[0]?.value || "0"),
          to:
            inputs[1]?.value === ""
              ? null
              : parseFloat(inputs[1]?.value || "0"),
          rate: parseFloat(inputs[3]?.value || "0"),
        };
      })
      .filter((t) => t.from !== undefined && t.rate !== undefined);
    if (tiers.length > 0) structure.tiers = tiers;
  }
  if (document.getElementById("flatPricing")?.checked) {
    const rate = parseFloat(document.getElementById("flatRate")?.value || "0");
    if (rate > 0) structure.flat_rate = rate;
  }
  if (document.getElementById("touPricing")?.checked) {
    const rows = Array.from(
      document.getElementById("touRates")?.children || []
    );
    const tou = rows
      .map((r) => {
        const inputs = r.querySelectorAll("input");
        return {
          period_name: inputs[0]?.value || "",
          start_time: inputs[1]?.value || "",
          end_time: inputs[2]?.value || "",
          weekdays: inputs[3]?.checked || false,
          weekends: inputs[4]?.checked || false,
          rate: parseFloat(inputs[5]?.value || "0"),
        };
      })
      .filter((p) => p.period_name && p.start_time && p.end_time && p.rate > 0);
    if (tou.length > 0) structure.time_of_use = tou;
  }

  const seasonal = collectSeasonalStructure();
  if (seasonal) Object.assign(structure, seasonal);
  const fixed = collectFixedChargeStructure();
  if (fixed) Object.assign(structure, fixed);
  const demand = collectDemandChargeStructure();
  if (demand) Object.assign(structure, demand);

  return structure;
}

// ── Review / Preview ────────────────────────────────────────────────

function generatePreview() {
  const name = document.getElementById("rtName")?.value || "Unnamed Rate Table";
  const utilityRaw = document.getElementById("rtUtility")?.value || "electricity";
  const utilityLabel = utilityRaw.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
  const effFrom = document.getElementById("rtFrom")?.value || "—";
  const effTo = document.getElementById("rtTo")?.value || "Open-ended";
  const category = document.getElementById("rtCategory")?.value || "—";
  const isActive = document.getElementById("rtActive")?.checked;
  const description = document.getElementById("rtDescription")?.value || "";

  // ── Basic info summary ──
  const basicInfo = document.getElementById("reviewBasicInfo");
  basicInfo.innerHTML = `
    <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Name</p>
      <p class="text-sm font-semibold text-gray-900 dark:text-white">${escapeHtml(name)}</p>
    </div>
    <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Resource Type</p>
      <p class="text-sm font-semibold text-gray-900 dark:text-white">${escapeHtml(utilityLabel)}</p>
    </div>
    <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Category</p>
      <p class="text-sm font-semibold text-gray-900 dark:text-white">${escapeHtml(category)}</p>
    </div>
    <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Effective Period</p>
      <p class="text-sm font-semibold text-gray-900 dark:text-white">${escapeHtml(effFrom)} → ${escapeHtml(effTo)}</p>
    </div>
    <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Status</p>
      <p class="text-sm font-semibold ${isActive ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}">
        <i class="fas fa-circle text-xs mr-1"></i>${isActive ? "Active" : "Inactive"}
      </p>
    </div>
    ${description ? `
    <div class="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <p class="text-xs text-gray-500 dark:text-gray-400 mb-1">Description</p>
      <p class="text-sm text-gray-900 dark:text-white">${escapeHtml(description)}</p>
    </div>` : ""}
  `;

  // ── Rate structure preview ──
  const previewContent = document.getElementById("previewContent");
  const structure = collectStructure();
  let previewHTML = `
    <div class="mb-4">
      <h3 class="font-semibold text-lg text-gray-900 dark:text-white">${escapeHtml(name)}</h3>
      <p class="text-sm text-gray-600 dark:text-gray-400">Resource: ${escapeHtml(utilityLabel)}</p>
    </div>
    <div class="space-y-2">
  `;

  // Hot water dual-component preview
  if (utilityRaw === "hot_water") {
    const wc = structure.water_component || {};
    const ec = structure.electricity_component || {};
    const cf = structure.conversion_factor || 0.065;
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-tint text-blue-500 mr-1"></i> Water Component</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">${wc.flat_rate ? "R " + wc.flat_rate.toFixed(2) + "/kL (flat rate)" : wc.tiers ? wc.tiers.length + " tier(s) configured" : "Not configured"}</p>
      </div>
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-bolt text-yellow-500 mr-1"></i> Electricity Component (Heating)</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">${ec.flat_rate ? "R " + ec.flat_rate.toFixed(2) + "/kWh" : "Not configured"}</p>
      </div>
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-exchange-alt text-gray-500 mr-1"></i> Conversion Factor</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">${cf} kWh/L</p>
      </div>
    `;
    previewHTML += "</div>";
    previewContent.innerHTML = previewHTML;
    updateSampleBills(structure, utilityRaw);
    checkWarnings(structure, utilityRaw);
    return;
  }

  // Standard pricing models
  if (structure.tiers && structure.tiers.length > 0) {
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-layer-group text-blue-500 mr-1"></i> Tiered Pricing</p>
        <div class="space-y-1">
          ${structure.tiers.map((t, i) => `
            <p class="text-xs text-gray-600 dark:text-gray-400">
              Tier ${i + 1}: ${t.from}${t.to !== null ? " – " + t.to : "+"} ${utilityRaw === "water" ? "kL" : "kWh"} @ R ${(t.rate || 0).toFixed(2)}/${utilityRaw === "water" ? "kL" : "kWh"}
            </p>
          `).join("")}
        </div>
      </div>
    `;
  }

  if (structure.flat_rate) {
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-equals text-purple-500 mr-1"></i> Flat Rate</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">R ${structure.flat_rate.toFixed(2)} per ${utilityRaw === "water" ? "kL" : "kWh"}</p>
      </div>
    `;
  }

  if (structure.time_of_use && structure.time_of_use.length > 0) {
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-clock text-yellow-500 mr-1"></i> Time of Use</p>
        <div class="space-y-1">
          ${structure.time_of_use.map(p => `
            <p class="text-xs text-gray-600 dark:text-gray-400">
              ${escapeHtml(p.period_name)}: ${p.start_time} – ${p.end_time}
              ${p.weekdays ? "(Weekdays)" : ""} ${p.weekends ? "(Weekends)" : ""}
              @ R ${(p.rate || 0).toFixed(2)}/kWh
            </p>
          `).join("")}
        </div>
      </div>
    `;
  }

  if (structure.seasonal) {
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-calendar-alt text-green-500 mr-1"></i> Seasonal Pricing</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">Summer (Dec–Feb): R ${(structure.seasonal.summer || 0).toFixed(2)}/kWh</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">Winter (Jun–Aug): R ${(structure.seasonal.winter || 0).toFixed(2)}/kWh</p>
      </div>
    `;
  }

  if (structure.fixed_charge) {
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-lock text-red-500 mr-1"></i> Fixed Charge</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">R ${structure.fixed_charge.toFixed(2)} per period</p>
      </div>
    `;
  }

  if (structure.demand_charge) {
    previewHTML += `
      <div class="p-3 bg-white dark:bg-gray-800 rounded">
        <p class="font-medium text-sm mb-2 text-gray-900 dark:text-white"><i class="fas fa-chart-line text-orange-500 mr-1"></i> Demand Charge</p>
        <p class="text-xs text-gray-600 dark:text-gray-400">R ${structure.demand_charge.toFixed(2)} per kW of peak demand</p>
      </div>
    `;
  }

  // Empty state
  if (Object.keys(structure).length === 0) {
    previewHTML += `
      <div class="p-3 bg-red-50 dark:bg-red-900/20 rounded text-center">
        <p class="text-sm text-red-600 dark:text-red-400"><i class="fas fa-exclamation-circle mr-1"></i>No pricing models configured</p>
      </div>
    `;
  }

  previewHTML += "</div>";
  previewContent.innerHTML = previewHTML;
  updateSampleBills(structure, utilityRaw);
  checkWarnings(structure, utilityRaw);
}

function calculateBillForUsage(usage, structure) {
  let total = 0;

  // Hot water dual-component
  if (structure.water_component) {
    const volumeKl = usage / 1000.0;
    const conversionFactor = structure.conversion_factor || 0.065;
    const elecKwh = usage * conversionFactor;

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
  // Seasonal (average of summer/winter)
  else if (structure.seasonal) {
    const avgRate = ((structure.seasonal.summer || 0) + (structure.seasonal.winter || 0)) / 2;
    total = usage * avgRate;
  }

  // Fixed charge
  if (structure.fixed_charge) {
    total += structure.fixed_charge;
  }

  return total;
}

function updateSampleBills(structure, utilityType) {
  const isHotWater = utilityType === "hot_water";
  const isWater = utilityType === "water";
  const usageLevels = isHotWater ? [100, 300, 600] : (isWater ? [5, 15, 30] : [50, 250, 500]);
  const unit = isHotWater ? "L" : (isWater ? "kL" : "kWh");
  const labels = [
    { id: "sampleLabelLow", text: `Low Usage (${usageLevels[0]} ${unit})` },
    { id: "sampleLabelMid", text: `Average (${usageLevels[1]} ${unit})` },
    { id: "sampleLabelHigh", text: `High Usage (${usageLevels[2]} ${unit})` },
  ];
  const billIds = ["sampleBillLow", "sampleBillMid", "sampleBillHigh"];

  labels.forEach(l => {
    const el = document.getElementById(l.id);
    if (el) el.textContent = l.text;
  });

  usageLevels.forEach((usage, idx) => {
    const bill = calculateBillForUsage(usage, structure);
    const el = document.getElementById(billIds[idx]);
    if (el) el.textContent = `R ${bill.toFixed(2)}`;
  });
}

function checkWarnings(structure, utilityType) {
  const warnings = [];
  const warningsDiv = document.getElementById("reviewWarnings");
  const warningsList = document.getElementById("reviewWarningsList");

  if (Object.keys(structure).length === 0) {
    warnings.push("No pricing model is configured. This rate table won't calculate any charges.");
  }

  if (!document.getElementById("rtFrom")?.value) {
    warnings.push("No effective-from date set. This rate table may not apply correctly.");
  }

  if (!document.getElementById("rtName")?.value?.trim()) {
    warnings.push("Rate table has no name.");
  }

  // Check for tier gaps/overlaps
  if (structure.tiers && structure.tiers.length > 1) {
    for (let i = 1; i < structure.tiers.length; i++) {
      const prevTo = structure.tiers[i - 1].to;
      const currFrom = structure.tiers[i].from;
      if (prevTo !== null && currFrom !== undefined && prevTo !== currFrom) {
        warnings.push(`Tier gap/overlap detected between tier ${i} (to: ${prevTo}) and tier ${i + 1} (from: ${currFrom}).`);
      }
    }
  }

  if (warnings.length > 0) {
    warningsList.innerHTML = warnings.map(w => `<li>${escapeHtml(w)}</li>`).join("");
    warningsDiv.classList.remove("hidden");
  } else {
    warningsDiv.classList.add("hidden");
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.appendChild(document.createTextNode(str));
  return div.innerHTML;
}

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("step2Content").classList.add("hidden");
  document.getElementById("step3Content").classList.add("hidden");
  loadDetails();
  document.getElementById("saveBtn").addEventListener("click", saveChanges);
});
