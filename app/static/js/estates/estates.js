const BASE_URL = "/api/v1";

function showAddEstateModal() {
  document.getElementById("addEstateModal").classList.remove("hidden");
}

function closeAddEstateModal() {
  document.getElementById("addEstateModal").classList.add("hidden");
}

function confirmDeleteEstate(buttonEl) {
  const card = buttonEl.closest("[data-estate]");
  const estate = JSON.parse(card.getAttribute("data-estate"));
  const modal = document.getElementById("deleteEstateModal");
  modal.setAttribute("data-estate-id", estate.id);
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hideDeleteEstate() {
  const modal = document.getElementById("deleteEstateModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

async function performDeleteEstate() {
  const modal = document.getElementById("deleteEstateModal");
  const estateId = modal.getAttribute("data-estate-id");
  if (!estateId) return;
  try {
    const res = await fetch(`${BASE_URL}/estates/${estateId}`, {
      method: "DELETE",
    });
    if (!res.ok) {
      showFlashMessage("Failed to delete estate", "error", true);
      return;
    }
    hideDeleteEstate();
    window.location.reload();
    showFlashMessage("Estate deleted successfully", "success", true);
  } catch (e) {
    console.error("Error deleting estate:", e);
    showFlashMessage("Failed to delete estate", "error", true);
  }
}

async function saveNewEstate(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const d = Object.fromEntries(formData);
  try {
    const res = await fetch(`${BASE_URL}/estates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: d.estate_name,
        code: d.estate_code,
        address: d.address,
        city: d.city,
        postal_code: d.postal_code,
        contact_name: d.manager_name,
        contact_phone: d.contact_number,
        contact_email: d.manager_email,
        total_units: Number(d.total_units || 0),
        electricity_markup_percentage: Number(d.electricity_markup || 0),
        water_markup_percentage: Number(d.water_markup || 0),
        solar_free_allocation_kwh: Number(d.solar_free_kwh || 0),
        electricity_rate_table_id: d.electricity_rate_table || null,
        water_rate_table_id: d.water_rate_table || null,
      }),
    });
    if (!res.ok) {
      showFlashMessage("Failed to create estate", "error", true);
      return;
    }
    await res.json();
    window.location.reload();
    showFlashMessage("Estate created successfully", "success", true);
  } catch (e) {
    console.error("Error creating estate:", e);
    showFlashMessage("Failed to create estate", "error", true);
  }
}

function viewEstateDetails(buttonEl) {
  const card = buttonEl.closest("[data-estate]");
  if (!card) return;
  const estate = JSON.parse(card.getAttribute("data-estate"));
  window.location.href = `${BASE_URL}/estates/${estate.id}/details`;
}

function editEstate(buttonEl) {
  const card = buttonEl.closest("[data-estate]");
  if (!card) {
    showEditEstateModal();
    return;
  }
  const estate = JSON.parse(card.getAttribute("data-estate"));
  // Populate edit form
  document.getElementById("edit_estate_name").value = estate.name || "";
  document.getElementById("edit_address").value = estate.address || "";
  document.getElementById("edit_city").value = estate.city || "";
  document.getElementById("edit_postal_code").value = estate.postal_code || "";
  document.getElementById("edit_total_units").value = estate.total_units || 0;
  document.getElementById("edit_estate_code").value = estate.code || "";
  document.getElementById("edit_manager_name").value =
    estate.contact_name || "";
  document.getElementById("edit_contact_number").value =
    estate.contact_phone || "";
  document.getElementById("edit_manager_email").value =
    estate.contact_email || "";
  // Billing/rates
  const electricityMarkUp = document.getElementById("edit_electricity_markup");
  if (electricityMarkUp)
    electricityMarkUp.value = estate.electricity_markup_percentage ?? 0;
  const waterMarkUp = document.getElementById("edit_water_markup");
  if (waterMarkUp) waterMarkUp.value = estate.water_markup_percentage ?? 0;
  const solarFree = document.getElementById("edit_solar_free_kwh");
  if (solarFree) solarFree.value = estate.solar_free_allocation_kwh ?? 50;
  const electricityRateTable = document.getElementById(
    "edit_electricity_rate_table"
  );
  if (electricityRateTable && estate.electricity_rate_table_id)
    electricityRateTable.value = estate.electricity_rate_table_id;
  const waterRateTable = document.getElementById("edit_water_rate_table");
  if (waterRateTable && estate.water_rate_table_id)
    waterRateTable.value = estate.water_rate_table_id;
  // Store id on form for submit
  document
    .getElementById("editEstateModal")
    .setAttribute("data-estate-id", estate.id);
  showEditEstateModal();
}

function showEditEstateModal() {
  document.getElementById("editEstateModal").classList.remove("hidden");
}

function closeEditEstateModal() {
  document.getElementById("editEstateModal").classList.add("hidden");
}

async function saveEditedEstate(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const updatedData = Object.fromEntries(formData);
  const estateId = document
    .getElementById("editEstateModal")
    .getAttribute("data-estate-id");

  try {
    const res = await fetch(`${BASE_URL}/estates/${estateId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: updatedData.estate_name,
        code: updatedData.estate_code,
        address: updatedData.address,
        city: updatedData.city,
        postal_code: updatedData.postal_code,
        contact_name: updatedData.manager_name,
        contact_phone: updatedData.contact_number,
        contact_email: updatedData.manager_email,
        total_units: Number(updatedData.total_units || 0),
        electricity_markup_percentage: Number(
          updatedData.electricity_markup || 0
        ),
        water_markup_percentage: Number(updatedData.water_markup || 0),
        solar_free_allocation_kwh: Number(updatedData.solar_free_kwh || 0),
        electricity_rate_table_id: updatedData.electricity_rate_table || null,
        water_rate_table_id: updatedData.water_rate_table || null,
      }),
    });
    if (!res.ok) {
      showFlashMessage("Failed to update estate", "error", true);
    }
    await res.json();
    window.location.reload();
    showFlashMessage("Estate updated successfully", "success", true);
  } catch (e) {
    console.error("Error updating estate:", e);
    showFlashMessage("Failed to update estate", "error", true);
  }
}

// Reconciliation View Functions
function updateReconciliation() {
  const viewType = document.getElementById("viewType").value;
  const estateSelect = document.getElementById("estateSelect").value;
  const mtdView = document.getElementById("mtdView");
  const monthlyView = document.getElementById("monthlyView");

  // Hide all views first
  mtdView.classList.add("hidden");
  monthlyView.classList.add("hidden");

  // Show selected view
  if (viewType === "mtd") {
    mtdView.classList.remove("hidden");
    updateMTDData(estateSelect);
  } else if (viewType === "monthly" || viewType === "yearly") {
    monthlyView.classList.remove("hidden");
    updateMonthlyData(estateSelect, viewType);
  }
}

function exportData() {
  alert("Export functionality would be implemented here");
}


  // Mock Data for Reconciliation
  const reconciliationData = {
    willow: {
      name: "Willow Creek Estate",
      mtd: {
        period: "October 2025 - Month to Date",
        daysElapsed: "9 of 31",
        totalBulk: 5625,
        solarOffset: -1350,
        unitsTotal: 4212,
        unaccounted: 63,
        unaccountedPercent: 1.5,
        estateBill: 157.5,
        dailyData: [
          {
            date: "Oct 1",
            bulk: 625,
            solar: 150,
            net: 475,
            units: 468,
            loss: 7,
            lossPercent: 1.5,
            bill: 17.5,
          },
          {
            date: "Oct 2",
            bulk: 642,
            solar: 148,
            net: 494,
            units: 485,
            loss: 9,
            lossPercent: 1.8,
            bill: 22.5,
          },
          {
            date: "Oct 3",
            bulk: 598,
            solar: 142,
            net: 456,
            units: 450,
            loss: 6,
            lossPercent: 1.3,
            bill: 15.0,
          },
          {
            date: "Oct 4",
            bulk: 634,
            solar: 155,
            net: 479,
            units: 472,
            loss: 7,
            lossPercent: 1.5,
            bill: 17.5,
          },
          {
            date: "Oct 5",
            bulk: 612,
            solar: 148,
            net: 464,
            units: 458,
            loss: 6,
            lossPercent: 1.3,
            bill: 15.0,
          },
          {
            date: "Oct 6",
            bulk: 648,
            solar: 156,
            net: 492,
            units: 486,
            loss: 6,
            lossPercent: 1.2,
            bill: 15.0,
          },
          {
            date: "Oct 7",
            bulk: 635,
            solar: 152,
            net: 483,
            units: 478,
            loss: 5,
            lossPercent: 1.0,
            bill: 12.5,
          },
          {
            date: "Oct 8",
            bulk: 621,
            solar: 149,
            net: 472,
            units: 467,
            loss: 5,
            lossPercent: 1.1,
            bill: 12.5,
          },
          {
            date: "Oct 9",
            bulk: 610,
            solar: 146,
            net: 464,
            units: 456,
            loss: 8,
            lossPercent: 1.7,
            bill: 20.0,
          },
        ],
      },
      monthly: {
        year: 2025,
        monthlyData: [
          {
            month: "January",
            bulk: 18750,
            solar: 4650,
            net: 14100,
            units: 13886,
            loss: 214,
            lossPercent: 1.5,
            efficiency: 98.5,
            bill: 535.0,
          },
          {
            month: "February",
            bulk: 16800,
            solar: 4200,
            net: 12600,
            units: 12411,
            loss: 189,
            lossPercent: 1.5,
            efficiency: 98.5,
            bill: 472.5,
          },
          {
            month: "March",
            bulk: 19200,
            solar: 4800,
            net: 14400,
            units: 14227,
            loss: 173,
            lossPercent: 1.2,
            efficiency: 98.8,
            bill: 432.5,
          },
          {
            month: "April",
            bulk: 17800,
            solar: 4450,
            net: 13350,
            units: 13184,
            loss: 166,
            lossPercent: 1.2,
            efficiency: 98.8,
            bill: 415.0,
          },
          {
            month: "May",
            bulk: 16500,
            solar: 4125,
            net: 12375,
            units: 12220,
            loss: 155,
            lossPercent: 1.3,
            efficiency: 98.7,
            bill: 387.5,
          },
          {
            month: "June",
            bulk: 15800,
            solar: 3950,
            net: 11850,
            units: 11703,
            loss: 147,
            lossPercent: 1.2,
            efficiency: 98.8,
            bill: 367.5,
          },
          {
            month: "July",
            bulk: 17200,
            solar: 4300,
            net: 12900,
            units: 12629,
            loss: 271,
            lossPercent: 2.1,
            efficiency: 97.9,
            bill: 677.5,
          },
          {
            month: "August",
            bulk: 18500,
            solar: 4625,
            net: 13875,
            units: 13689,
            loss: 186,
            lossPercent: 1.3,
            efficiency: 98.7,
            bill: 465.0,
          },
          {
            month: "September",
            bulk: 17900,
            solar: 4475,
            net: 13425,
            units: 13251,
            loss: 174,
            lossPercent: 1.3,
            efficiency: 98.7,
            bill: 435.0,
          },
          {
            month: "October (MTD)",
            bulk: 5625,
            solar: 1350,
            net: 4275,
            units: 4212,
            loss: 63,
            lossPercent: 1.5,
            efficiency: 98.5,
            bill: 157.5,
          },
        ],
        ytd: {
          bulk: 162375,
          solar: 39150,
          net: 123225,
          units: 121287,
          loss: 1938,
          lossPercent: 1.6,
          bill: 4845.0,
        },
        avgMonthlyLoss: 194,
        bestMonth: "March",
        worstMonth: "July",
      },
    },
    parkview: {
      name: "Parkview Gardens",
      mtd: {
        period: "October 2025 - Month to Date",
        daysElapsed: "9 of 31",
        totalBulk: 4280,
        solarOffset: -980,
        unitsTotal: 3298,
        unaccounted: 98,
        unaccountedPercent: 3.0,
        estateBill: 245.0,
        dailyData: [
          {
            date: "Oct 1",
            bulk: 475,
            solar: 115,
            net: 360,
            units: 345,
            loss: 15,
            lossPercent: 4.2,
            bill: 37.5,
          },
          {
            date: "Oct 2",
            bulk: 488,
            solar: 112,
            net: 376,
            units: 362,
            loss: 14,
            lossPercent: 3.7,
            bill: 35.0,
          },
          {
            date: "Oct 3",
            bulk: 455,
            solar: 108,
            net: 347,
            units: 338,
            loss: 9,
            lossPercent: 2.6,
            bill: 22.5,
          },
          {
            date: "Oct 4",
            bulk: 482,
            solar: 118,
            net: 364,
            units: 348,
            loss: 16,
            lossPercent: 4.4,
            bill: 40.0,
          },
          {
            date: "Oct 5",
            bulk: 465,
            solar: 112,
            net: 353,
            units: 342,
            loss: 11,
            lossPercent: 3.1,
            bill: 27.5,
          },
          {
            date: "Oct 6",
            bulk: 492,
            solar: 119,
            net: 373,
            units: 358,
            loss: 15,
            lossPercent: 4.0,
            bill: 37.5,
          },
          {
            date: "Oct 7",
            bulk: 483,
            solar: 116,
            net: 367,
            units: 352,
            loss: 15,
            lossPercent: 4.1,
            bill: 37.5,
          },
          {
            date: "Oct 8",
            bulk: 472,
            solar: 113,
            net: 359,
            units: 345,
            loss: 14,
            lossPercent: 3.9,
            bill: 35.0,
          },
          {
            date: "Oct 9",
            bulk: 488,
            solar: 111,
            net: 377,
            units: 358,
            loss: 19,
            lossPercent: 5.0,
            bill: 47.5,
          },
        ],
      },
      monthly: {
        year: 2025,
        monthlyData: [
          {
            month: "January",
            bulk: 14250,
            solar: 3530,
            net: 10720,
            units: 10398,
            loss: 322,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 805.0,
          },
          {
            month: "February",
            bulk: 12780,
            solar: 3195,
            net: 9585,
            units: 9298,
            loss: 287,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 717.5,
          },
          {
            month: "March",
            bulk: 14590,
            solar: 3648,
            net: 10942,
            units: 10612,
            loss: 330,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 825.0,
          },
          {
            month: "April",
            bulk: 13520,
            solar: 3380,
            net: 10140,
            units: 9836,
            loss: 304,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 760.0,
          },
          {
            month: "May",
            bulk: 12540,
            solar: 3135,
            net: 9405,
            units: 9123,
            loss: 282,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 705.0,
          },
          {
            month: "June",
            bulk: 12010,
            solar: 3003,
            net: 9007,
            units: 8737,
            loss: 270,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 675.0,
          },
          {
            month: "July",
            bulk: 13080,
            solar: 3270,
            net: 9810,
            units: 9516,
            loss: 294,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 735.0,
          },
          {
            month: "August",
            bulk: 14060,
            solar: 3515,
            net: 10545,
            units: 10229,
            loss: 316,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 790.0,
          },
          {
            month: "September",
            bulk: 13610,
            solar: 3403,
            net: 10207,
            units: 9901,
            loss: 306,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 765.0,
          },
          {
            month: "October (MTD)",
            bulk: 4280,
            solar: 980,
            net: 3300,
            units: 3298,
            loss: 98,
            lossPercent: 3.0,
            efficiency: 97.0,
            bill: 245.0,
          },
        ],
        ytd: {
          bulk: 123540,
          solar: 29780,
          net: 93760,
          units: 90949,
          loss: 2811,
          lossPercent: 3.0,
          bill: 7027.5,
        },
        avgMonthlyLoss: 281,
        bestMonth: "January",
        worstMonth: "July",
      },
    },
    sunset: {
      name: "Sunset Ridge Estate",
      mtd: {
        period: "October 2025 - Month to Date",
        daysElapsed: "9 of 31",
        totalBulk: 6890,
        solarOffset: -1650,
        unitsTotal: 5238,
        unaccounted: 2,
        unaccountedPercent: 0.0,
        estateBill: 5.0,
        dailyData: [
          {
            date: "Oct 1",
            bulk: 765,
            solar: 185,
            net: 580,
            units: 580,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 2",
            bulk: 789,
            solar: 190,
            net: 599,
            units: 599,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 3",
            bulk: 742,
            solar: 178,
            net: 564,
            units: 564,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 4",
            bulk: 798,
            solar: 192,
            net: 606,
            units: 606,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 5",
            bulk: 776,
            solar: 186,
            net: 590,
            units: 590,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 6",
            bulk: 812,
            solar: 195,
            net: 617,
            units: 617,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 7",
            bulk: 798,
            solar: 191,
            net: 607,
            units: 607,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 8",
            bulk: 781,
            solar: 187,
            net: 594,
            units: 594,
            loss: 0,
            lossPercent: 0.0,
            bill: 0.0,
          },
          {
            date: "Oct 9",
            bulk: 789,
            solar: 189,
            net: 600,
            units: 600,
            loss: 2,
            lossPercent: 0.3,
            bill: 5.0,
          },
        ],
      },
      monthly: {
        year: 2025,
        monthlyData: [
          {
            month: "January",
            bulk: 23400,
            solar: 5620,
            net: 17780,
            units: 17780,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "February",
            bulk: 21080,
            solar: 5060,
            net: 16020,
            units: 16020,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "March",
            bulk: 24120,
            solar: 5789,
            net: 18331,
            units: 18331,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "April",
            bulk: 22340,
            solar: 5362,
            net: 16978,
            units: 16978,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "May",
            bulk: 20760,
            solar: 4982,
            net: 15778,
            units: 15778,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "June",
            bulk: 19880,
            solar: 4771,
            net: 15109,
            units: 15109,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "July",
            bulk: 21640,
            solar: 5194,
            net: 16446,
            units: 16446,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "August",
            bulk: 23280,
            solar: 5587,
            net: 17693,
            units: 17693,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "September",
            bulk: 22540,
            solar: 5410,
            net: 17130,
            units: 17130,
            loss: 0,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 0.0,
          },
          {
            month: "October (MTD)",
            bulk: 6890,
            solar: 1650,
            net: 5240,
            units: 5238,
            loss: 2,
            lossPercent: 0.0,
            efficiency: 100.0,
            bill: 5.0,
          },
        ],
        ytd: {
          bulk: 209330,
          solar: 50225,
          net: 159105,
          units: 159103,
          loss: 2,
          lossPercent: 0.0,
          bill: 5.0,
        },
        avgMonthlyLoss: 0,
        bestMonth: "All Months",
        worstMonth: "October (MTD)",
      },
    },
  };

  function updateMTDData(estate) {
    const data = reconciliationData[estate].mtd;

    // Update period title
    document.querySelector("#mtdView h3").textContent = data.period;

    // Update summary card
    document.querySelector("#mtdView .space-y-2").innerHTML = `
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Days Elapsed</span>
                    <span class="text-sm font-semibold text-gray-900 dark:text-white">${
                      data.daysElapsed
                    }</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Total Bulk Reading</span>
                    <span class="text-sm font-semibold text-gray-900 dark:text-white">${data.totalBulk.toLocaleString()} kWh</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Solar Offset</span>
                    <span class="text-sm font-semibold text-yellow-600">${data.solarOffset.toLocaleString()} kWh</span>
                </div>
                <div class="flex justify-between items-center">
                    <span class="text-sm text-gray-600 dark:text-gray-400">Units Total</span>
                    <span class="text-sm font-semibold text-gray-900 dark:text-white">${data.unitsTotal.toLocaleString()} kWh</span>
                </div>
                <div class="flex justify-between items-center pt-2 border-t">
                    <span class="text-sm font-medium text-red-700 dark:text-red-300">Communal Usage</span>
                    <span class="text-sm font-bold text-red-600">${
                      data.unaccounted
                    } kWh (${data.unaccountedPercent}%)</span>
                </div>
                <div class="flex justify-between items-center bg-yellow-50 dark:bg-yellow-900/20 -mx-2 px-2 py-2 rounded">
                    <span class="text-sm font-medium text-yellow-700 dark:text-yellow-300">Estate Bill MTD</span>
                    <span class="text-sm font-bold text-yellow-600">R ${data.estateBill.toFixed(
                      2
                    )}</span>
                </div>
            `;

    // Update daily table
    const tbody = document.querySelector("#mtdView tbody");
    tbody.innerHTML = "";

    data.dailyData.forEach((day) => {
      const row = document.createElement("tr");
      row.className = "hover:bg-gray-50 dark:hover:bg-gray-700/50";
      row.innerHTML = `
                <td class="px-4 py-3 text-gray-900 dark:text-white">${
                  day.date
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  day.bulk
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  day.solar
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  day.net
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  day.units
                }</td>
                <td class="px-4 py-3 text-center text-red-600">${day.loss}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  day.lossPercent
                }%</td>
                <td class="px-4 py-3 text-right font-semibold text-gray-900 dark:text-white">R ${day.bill.toFixed(
                  2
                )}</td>
            `;
      tbody.appendChild(row);
    });

    // Add MTD total row
    const totalRow = document.createElement("tr");
    totalRow.className = "bg-gray-100 dark:bg-gray-700 font-semibold";
    totalRow.innerHTML = `
                <td class="px-4 py-3 text-gray-900 dark:text-white">MTD Total</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${data.totalBulk.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${Math.abs(
                  data.solarOffset
                ).toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${(
                  data.totalBulk + data.solarOffset
                ).toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${data.unitsTotal.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-red-600">${
                  data.unaccounted
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  data.unaccountedPercent
                }%</td>
                <td class="px-4 py-3 text-right text-lg text-gray-900 dark:text-white">R ${data.estateBill.toFixed(
                  2
                )}</td>
            `;
    tbody.appendChild(totalRow);

    // Update chart
    drawDailyTrendChart(data.dailyData);
  }

  function updateMonthlyData(estate, viewType) {
    const data = reconciliationData[estate].monthly;

    // Update title
    if (viewType === "yearly") {
      document.querySelector(
        "#monthlyView h3"
      ).textContent = `Year Overview - ${data.year}`;
    } else {
      document.querySelector(
        "#monthlyView h3"
      ).textContent = `Monthly Comparison - ${data.year}`;
    }

    // Update monthly table
    const tbody = document.querySelector("#monthlyView tbody");
    tbody.innerHTML = "";

    data.monthlyData.forEach((month) => {
      const row = document.createElement("tr");
      row.className = "hover:bg-gray-50 dark:hover:bg-gray-700/50";
      if (month.month === "October (MTD)") {
        row.className += " text-gray-500";
      }
      row.innerHTML = `
                <td class="px-4 py-3 font-medium text-gray-900 dark:text-white">${
                  month.month
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${month.bulk.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${month.solar.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${month.net.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${month.units.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-red-600">${
                  month.loss
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  month.lossPercent
                }%</td>
                <td class="px-4 py-3 text-center">
                    <span class="px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400 text-xs rounded">${
                      month.efficiency
                    }%</span>
                </td>
                <td class="px-4 py-3 text-right font-semibold text-gray-900 dark:text-white">R ${month.bill.toFixed(
                  2
                )}</td>
            `;
      tbody.appendChild(row);
    });

    // Add YTD total row
    const totalRow = document.createElement("tr");
    totalRow.className = "bg-gray-100 dark:bg-gray-700 font-bold";
    totalRow.innerHTML = `
                <td class="px-4 py-3 text-gray-900 dark:text-white">YTD Total</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${data.ytd.bulk.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${data.ytd.solar.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${data.ytd.net.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${data.ytd.units.toLocaleString()}</td>
                <td class="px-4 py-3 text-center text-red-600">${
                  data.ytd.loss
                }</td>
                <td class="px-4 py-3 text-center text-gray-900 dark:text-white">${
                  data.ytd.lossPercent
                }%</td>
                <td class="px-4 py-3 text-center">
                    <span class="px-2 py-1 bg-green-100 dark:bg-green-900/20 text-green-800 dark:text-green-400 text-xs rounded">${(
                      100 - data.ytd.lossPercent
                    ).toFixed(1)}%</span>
                </td>
                <td class="px-4 py-3 text-right text-lg text-gray-900 dark:text-white">R ${data.ytd.bill.toFixed(
                  2
                )}</td>
            `;
    tbody.appendChild(totalRow);

    // Update key metrics
    document.querySelector(
      "#monthlyView .bg-blue-50 .text-xl"
    ).textContent = `${data.avgMonthlyLoss} kWh`;
    document.querySelector("#monthlyView .bg-green-50 .text-xl").textContent =
      data.bestMonth;
    document.querySelector("#monthlyView .bg-red-50 .text-xl").textContent =
      data.worstMonth;
    document.querySelector(
      "#monthlyView .bg-yellow-50 .text-xl"
    ).textContent = `R ${data.ytd.bill.toLocaleString()}`;

    // Update chart
    drawMonthlyChart(data.monthlyData);
  }

  // Chart Drawing Functions
  function drawDailyTrendChart(dailyData = null) {
    const canvas = document.getElementById("dailyTrendChart");
    if (!canvas || !canvas.getContext) return;

    const ctx = canvas.getContext("2d");
    const container = canvas.parentElement;
    const rect = container.getBoundingClientRect();

    // Set canvas size to fill the container
    canvas.style.width = rect.width + "px";
    canvas.style.height = rect.height + "px";
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    const data = dailyData
      ? dailyData.map((day) => day.loss)
      : [7, 9, 6, 8, 5, 7, 8, 6, 7];
    const dates = dailyData
      ? dailyData.map((day) => day.date)
      : [
          "Oct 1",
          "Oct 2",
          "Oct 3",
          "Oct 4",
          "Oct 5",
          "Oct 6",
          "Oct 7",
          "Oct 8",
          "Oct 9",
        ];

    if (data.length === 0) return;

    // Chart dimensions - adjusted for better fit
    const padding = 30;
    const chartWidth = rect.width - padding * 2;
    const chartHeight = rect.height - padding * 2 - 20; // Extra space for title
    const maxValue = Math.max(...data) * 1.1; // Add 10% padding
    const minValue = Math.min(0, Math.min(...data) * 0.9);

    // Draw grid lines
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 2]);

    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(padding + chartWidth, y);
      ctx.stroke();
    }

    // Vertical grid lines
    for (let i = 0; i < data.length; i++) {
      const x = padding + (chartWidth / (data.length - 1)) * i;
      ctx.beginPath();
      ctx.moveTo(x, padding);
      ctx.lineTo(x, padding + chartHeight);
      ctx.stroke();
    }

    ctx.setLineDash([]);

    // Draw axis labels
    ctx.fillStyle = "#6b7280";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";

    // Y-axis labels
    for (let i = 0; i <= 5; i++) {
      const value = maxValue - (maxValue / 5) * i;
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(Math.round(value).toString(), padding - 8, y + 3);
    }

    // X-axis labels
    ctx.textAlign = "center";
    for (let i = 0; i < data.length; i++) {
      const x = padding + (chartWidth / (data.length - 1)) * i;
      ctx.fillText(dates[i], x, rect.height - 8);
    }

    // Draw the line chart
    ctx.beginPath();
    ctx.strokeStyle = "#ef4444";
    ctx.lineWidth = 3;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";

    data.forEach((value, index) => {
      const x = padding + (chartWidth / (data.length - 1)) * index;
      const y =
        padding +
        chartHeight -
        ((value - minValue) / (maxValue - minValue)) * chartHeight;

      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });

    ctx.stroke();

    // Draw data points
    ctx.fillStyle = "#ef4444";
    data.forEach((value, index) => {
      const x = padding + (chartWidth / (data.length - 1)) * index;
      const y =
        padding +
        chartHeight -
        ((value - minValue) / (maxValue - minValue)) * chartHeight;

      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();

      // Draw value labels above points
      ctx.fillStyle = "#374151";
      ctx.font = "8px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(value.toString(), x, y - 6);
      ctx.fillStyle = "#ef4444";
    });

    // Title is already provided in HTML, so we don't need to draw it
  }

  function drawMonthlyChart(monthlyData = null) {
    const canvas = document.getElementById("monthlyChart");
    if (!canvas || !canvas.getContext) return;

    const ctx = canvas.getContext("2d");
    const container = canvas.parentElement;
    const rect = container.getBoundingClientRect();

    // Set canvas size to fill the container
    canvas.style.width = rect.width + "px";
    canvas.style.height = rect.height + "px";
    canvas.width = rect.width;
    canvas.height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, rect.width, rect.height);

    const data = monthlyData || [
      { month: "January", loss: 214 },
      { month: "February", loss: 189 },
      { month: "March", loss: 156 },
      { month: "April", loss: 178 },
      { month: "May", loss: 195 },
      { month: "June", loss: 203 },
      { month: "July", loss: 245 },
      { month: "August", loss: 212 },
      { month: "September", loss: 198 },
      { month: "October (MTD)", loss: 63 },
    ];

    const months = data.map((item) => item.month.substring(0, 3));
    const losses = data.map((item) => item.loss);

    if (losses.length === 0) return;

    // Chart dimensions - adjusted for better fit
    const padding = 30;
    const chartWidth = rect.width - padding * 2;
    const chartHeight = rect.height - padding * 2 - 20; // Extra space for title
    const barWidth = chartWidth / (months.length * 1.5);
    const maxValue = Math.max(...losses) * 1.1;

    // Draw grid lines
    ctx.strokeStyle = "#e5e7eb";
    ctx.lineWidth = 1;
    ctx.setLineDash([2, 2]);

    // Horizontal grid lines
    for (let i = 0; i <= 5; i++) {
      const y = padding + (chartHeight / 5) * i;
      ctx.beginPath();
      ctx.moveTo(padding, y);
      ctx.lineTo(padding + chartWidth, y);
      ctx.stroke();
    }

    ctx.setLineDash([]);

    // Draw axis labels
    ctx.fillStyle = "#6b7280";
    ctx.font = "10px Inter, sans-serif";
    ctx.textAlign = "center";

    // Y-axis labels
    for (let i = 0; i <= 5; i++) {
      const value = maxValue - (maxValue / 5) * i;
      const y = padding + (chartHeight / 5) * i;
      ctx.fillText(Math.round(value).toString(), padding - 8, y + 3);
    }

    // X-axis labels
    for (let i = 0; i < months.length; i++) {
      const x = padding + (chartWidth / (months.length - 1)) * i;
      ctx.fillText(months[i], x, rect.height - 8);
    }

    // Draw bars
    losses.forEach((value, index) => {
      const x =
        padding + (chartWidth / (months.length - 1)) * index - barWidth / 2;
      const barHeight = (value / maxValue) * chartHeight;
      const y = padding + chartHeight - barHeight;

      // Bar color based on value
      ctx.fillStyle =
        value > 200 ? "#ef4444" : value > 100 ? "#f59e0b" : "#10b981";
      ctx.fillRect(x, y, barWidth, barHeight);

      // Value label above bar
      ctx.fillStyle = "#374151";
      ctx.font = "8px Inter, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(value.toString(), x + barWidth / 2, y - 3);
    });

    // Title is already provided in HTML, so we don't need to draw it
  }

  // Initialize on page load
  window.addEventListener("load", () => {
    // Small delay to ensure DOM is fully rendered
    setTimeout(() => {
      // Initialize reconciliation with default estate (Willow Creek)
      updateMTDData("willow");
    }, 100);
  });

  // Handle window resize to redraw charts
  window.addEventListener("resize", () => {
    const viewType = document.getElementById("viewType").value;
    const estate = document.getElementById("estateSelect").value;

    if (viewType === "mtd") {
      drawDailyTrendChart(reconciliationData[estate].mtd.dailyData);
    } else if (viewType === "monthly" || viewType === "yearly") {
      drawMonthlyChart(reconciliationData[estate].monthly.monthlyData);
    }
  });

  // Close modal on escape key
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeAddEstateModal();
      closeEditEstateModal();
    }
  });