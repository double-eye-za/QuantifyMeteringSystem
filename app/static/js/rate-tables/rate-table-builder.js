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
                <span class="text-sm font-medium w-20">Tier ${tierCount}:</span>
                <input type="number" placeholder="From" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <span>-</span>
                <input type="number" placeholder="To" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <span class="text-sm">kWh</span>
                <span class="text-sm">@</span>
                <span class="text-sm">R</span>
                <input type="number" step="0.01" placeholder="Rate" class="w-24 px-2 py-1 border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-white">
                <span class="text-sm text-gray-700 dark:text-gray-300">/kWh</span>
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

function collectStructure() {
  const out = {};
  const tiered = collectTieredStructure();
  if (tiered) Object.assign(out, tiered);
  const flat = collectFlatStructure();
  if (flat) Object.assign(out, flat);
  return out;
}

async function createRateTable() {
  try {
    const name = document.getElementById("rateName").value.trim();
    const utility = document.getElementById("resourceType").value;
    const effFrom = document.getElementById("effectiveDate").value;
    const effTo = document.getElementById("effectiveTo").value;
    const category = document.getElementById("category").value;
    const description = document.getElementById("description").value;
    if (!name || !utility || !effFrom) {
      showFlashMessage("Please complete the required fields", "error");
      return;
    }
    const structure = collectStructure();
    const payload = {
      name,
      utility_type: utility,
      effective_from: effFrom,
      effective_to: effTo || null,
      category: category,
      description: description,
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
