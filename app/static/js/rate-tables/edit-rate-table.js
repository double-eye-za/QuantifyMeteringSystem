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

function collectStructure() {
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

document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("step2Content").classList.add("hidden");
  document.getElementById("step3Content").classList.add("hidden");
  loadDetails();
  document.getElementById("saveBtn").addEventListener("click", saveChanges);
});
