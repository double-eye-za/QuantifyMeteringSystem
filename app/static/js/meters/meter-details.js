// Meter Details - Real-time Data and Charts
let consumptionChart = null;
let currentPeriod = "day";

// Helper: check if meter type is water-based
function isWaterType(meterType) {
  return meterType === "water" || meterType === "hot_water";
}

// Helper: get display unit for consumption values
function getConsumptionUnit() {
  return isWaterType(window.METER_TYPE) ? "kL" : "kWh";
}

// Helper: get display unit for readings
function getReadingUnit() {
  return isWaterType(window.METER_TYPE) ? "L" : "kWh";
}

// Transactions state
let txnCurrentPage = 1;
let txnTotalPages = 1;
let txnPerPage = 20;

// Readings state
let readingsCurrentPage = 1;
let readingsTotalPages = 1;
let readingsPerPage = 20;

// Fetch real-time stats and update cards
async function fetchRealtimeStats() {
  try {
    const response = await fetch(`/api/v1/meters/${window.METER_ID}/realtime-stats`);
    if (!response.ok) {
      console.error("Failed to fetch realtime stats");
      return;
    }

    const data = await response.json();
    updateRealtimeCards(data);
  } catch (error) {
    console.error("Error fetching realtime stats:", error);
  }
}

// Update the real-time stat cards
function updateRealtimeCards(data) {
  const unit = data.capabilities?.unit || "kWh";

  // Card 1: Today's Usage
  const todayUsage = document.getElementById("today-usage");
  const todayCost = document.getElementById("today-cost");
  if (todayUsage) {
    todayUsage.textContent = `${data.today.consumption} ${unit}`;
  }
  if (todayCost) {
    if (data.today.cost !== null) {
      todayCost.textContent = `Cost: R ${data.today.cost.toFixed(2)}`;
    } else {
      todayCost.textContent = data.today.cost_message || "Cost unavailable";
    }
  }

  // Card 2: Total Consumption
  const totalReading = document.getElementById("total-reading");
  const lastReadingTime = document.getElementById("last-reading-time");
  if (totalReading && data.latest_reading) {
    totalReading.textContent = `${data.latest_reading.value.toFixed(2)} ${unit}`;
  }
  if (lastReadingTime && data.latest_reading) {
    const timestamp = new Date(data.latest_reading.timestamp);
    // Format to local timezone (SAST for South Africa)
    const options = {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    };
    lastReadingTime.textContent = `Last: ${timestamp.toLocaleString('en-ZA', options)}`;
  }

  // Card 3: Device Status
  const batteryLevel = document.getElementById("battery-level");
  const temperature = document.getElementById("temperature");
  const signalStrength = document.getElementById("signal-strength");
  const batteryIcon = document.getElementById("battery-icon");

  if (batteryLevel && data.latest_reading?.battery_level !== null) {
    batteryLevel.textContent = `${data.latest_reading.battery_level}%`;

    // Update battery icon based on level
    if (batteryIcon) {
      const level = data.latest_reading.battery_level;
      batteryIcon.className = "fas ";
      if (level > 75) {
        batteryIcon.className += "fa-battery-full text-green-500";
      } else if (level > 50) {
        batteryIcon.className += "fa-battery-three-quarters text-green-500";
      } else if (level > 25) {
        batteryIcon.className += "fa-battery-half text-yellow-500";
      } else {
        batteryIcon.className += "fa-battery-quarter text-red-500";
      }
    }
  }

  if (temperature && data.latest_reading?.temperature !== null) {
    temperature.textContent = `${data.latest_reading.temperature.toFixed(1)}°C`;
  }

  if (signalStrength && data.latest_reading?.rssi !== null) {
    const rssi = data.latest_reading.rssi;
    let signalQuality = "Excellent";
    if (rssi < -90) signalQuality = "Poor";
    else if (rssi < -80) signalQuality = "Fair";
    else if (rssi < -70) signalQuality = "Good";

    signalStrength.textContent = `${signalQuality} (${rssi} dBm)`;
  }
}

// Fetch chart data and update chart
async function fetchChartData(period = "day") {
  try {
    const response = await fetch(`/api/v1/meters/${window.METER_ID}/chart-data?period=${period}`);
    if (!response.ok) {
      console.error("Failed to fetch chart data");
      return;
    }

    const data = await response.json();
    updateChart(data);
  } catch (error) {
    console.error("Error fetching chart data:", error);
  }
}

// Update or create the consumption chart
function updateChart(data) {
  const ctx = document.getElementById("consumptionChart")?.getContext("2d");
  if (!ctx) return;

  const unit = data.unit || "kWh";

  // Destroy existing chart if it exists
  if (consumptionChart) {
    consumptionChart.destroy();
  }

  // Create new chart
  consumptionChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: data.labels,
      datasets: [
        {
          label: `Consumption (${unit})`,
          data: data.data,
          borderColor: "#1A73E8",
          backgroundColor: "rgba(26, 115, 232, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return value + " " + unit;
            },
          },
        },
      },
    },
  });
}

// Handle period button clicks
function setupPeriodButtons() {
  const periodButtons = document.querySelectorAll(".period-btn");
  periodButtons.forEach((button) => {
    button.addEventListener("click", function () {
      // Remove active class from all buttons
      periodButtons.forEach((btn) => {
        btn.classList.remove("bg-primary", "text-white", "active");
        btn.classList.add("bg-white", "dark:bg-gray-600");
      });

      // Add active class to clicked button
      this.classList.remove("bg-white", "dark:bg-gray-600");
      this.classList.add("bg-primary", "text-white", "active");

      // Fetch data for the selected period
      const period = this.getAttribute("data-period");
      currentPeriod = period;
      fetchChartData(period);
    });
  });
}

// Auto-refresh data every 30 seconds
function startAutoRefresh() {
  setInterval(() => {
    fetchRealtimeStats();
    fetchChartData(currentPeriod);
  }, 30000); // 30 seconds
}

// Top Up Modal Functions
function openTopUpModal() {
  const modal = document.getElementById("topUpModal");
  if (modal) {
    modal.classList.remove("hidden");
  }
}

function closeTopUpModal() {
  const modal = document.getElementById("topUpModal");
  if (modal) {
    modal.classList.add("hidden");
    // Reset form
    document.getElementById("topUpForm").reset();
  }
}

async function handleTopUpSubmit(event) {
  event.preventDefault();

  const walletId = document.getElementById("walletId").value;
  const amount = parseFloat(document.getElementById("topUpAmount").value);
  const utilityType = document.getElementById("topUpUtilityType").value;
  const reference = document.getElementById("topUpReference").value;

  if (!walletId) {
    alert("Error: Wallet ID not found");
    return;
  }

  if (!amount || amount <= 0) {
    alert("Please enter a valid amount");
    return;
  }

  if (!utilityType) {
    alert("Please select a utility type");
    return;
  }

  const submitBtn = document.getElementById("submitTopUpBtn");
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';

  try {
    const response = await fetch(`/api/v1/wallets/${walletId}/topup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: amount,
        payment_method: "manual_admin",
        reference: reference || `Admin top-up for ${utilityType}`,
        metadata: {
          utility_type: utilityType,
          added_by: "admin",
          source: "meter_details_page"
        }
      }),
    });

    const result = await response.json();

    if (response.ok && result.data) {
      alert(`Success! Top-up completed.\nTransaction: ${result.data.transaction_number}\nStatus: ${result.data.status}`);
      closeTopUpModal();
      // Reload page to show updated balance
      window.location.reload();
    } else {
      alert(`Error: ${result.error || "Failed to process top-up"}`);
    }
  } catch (error) {
    console.error("Top-up error:", error);
    alert("Error: Failed to process top-up. Please try again.");
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

// ============================================
// Relay Control Functions (Disconnect/Reconnect)
// ============================================

let pendingRelayAction = null; // 'on' or 'off'

function openRelayModal(action) {
  pendingRelayAction = action;
  const modal = document.getElementById("relayModal");
  const title = document.getElementById("relayModalTitle");
  const actionText = document.getElementById("relayActionText");
  const confirmBtn = document.getElementById("confirmRelayBtn");

  if (action === "off") {
    title.innerHTML = '<i class="fas fa-power-off text-red-500 mr-2"></i>Confirm Disconnect';
    actionText.textContent = "disconnect";
    confirmBtn.innerHTML = '<i class="fas fa-power-off mr-2"></i>Disconnect';
    confirmBtn.className = "px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700";
  } else {
    title.innerHTML = '<i class="fas fa-plug text-green-500 mr-2"></i>Confirm Reconnect';
    actionText.textContent = "reconnect";
    confirmBtn.innerHTML = '<i class="fas fa-plug mr-2"></i>Reconnect';
    confirmBtn.className = "px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700";
  }

  if (modal) {
    modal.classList.remove("hidden");
  }
}

function closeRelayModal() {
  const modal = document.getElementById("relayModal");
  if (modal) {
    modal.classList.add("hidden");
  }
  pendingRelayAction = null;
}

async function sendRelayCommand() {
  if (!pendingRelayAction) {
    console.error("No pending relay action");
    return;
  }

  const confirmBtn = document.getElementById("confirmRelayBtn");
  const originalText = confirmBtn.innerHTML;
  confirmBtn.disabled = true;
  confirmBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Sending...';

  try {
    const response = await fetch(`/api/v1/meters/${window.METER_ID}/relay`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action: pendingRelayAction,
      }),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      const actionWord = pendingRelayAction === "off" ? "disconnect" : "reconnect";
      alert(
        `Success! ${actionWord.charAt(0).toUpperCase() + actionWord.slice(1)} command queued.\n\n` +
        `Note: ${result.note || "Command will be delivered on next device uplink."}`
      );
      closeRelayModal();
    } else {
      alert(`Error: ${result.error || "Failed to send command"}`);
    }
  } catch (error) {
    console.error("Relay command error:", error);
    alert("Error: Failed to send relay command. Please try again.");
  } finally {
    confirmBtn.disabled = false;
    confirmBtn.innerHTML = originalText;
  }
}

function setupRelayControls() {
  const disconnectBtn = document.getElementById("disconnectBtn");
  const reconnectBtn = document.getElementById("reconnectBtn");
  const closeRelayModalBtn = document.getElementById("closeRelayModal");
  const cancelRelayBtn = document.getElementById("cancelRelayBtn");
  const confirmRelayBtn = document.getElementById("confirmRelayBtn");
  const relayModal = document.getElementById("relayModal");

  if (disconnectBtn) {
    disconnectBtn.addEventListener("click", function () {
      openRelayModal("off");
    });
  }

  if (reconnectBtn) {
    reconnectBtn.addEventListener("click", function () {
      openRelayModal("on");
    });
  }

  if (closeRelayModalBtn) {
    closeRelayModalBtn.addEventListener("click", closeRelayModal);
  }

  if (cancelRelayBtn) {
    cancelRelayBtn.addEventListener("click", closeRelayModal);
  }

  if (confirmRelayBtn) {
    confirmRelayBtn.addEventListener("click", sendRelayCommand);
  }

  // Close modal when clicking outside
  if (relayModal) {
    relayModal.addEventListener("click", function (event) {
      if (event.target === relayModal) {
        closeRelayModal();
      }
    });
  }
}

// ============================================
// Readings Table Functions
// ============================================

function getTodayDateString() {
  const today = new Date();
  return today.toISOString().split('T')[0];
}

function initReadingsDateFilters() {
  const today = getTodayDateString();
  const startDateInput = document.getElementById("readingsStartDate");
  const endDateInput = document.getElementById("readingsEndDate");

  if (startDateInput) {
    startDateInput.value = today;
  }
  if (endDateInput) {
    endDateInput.value = today;
  }
}

async function fetchReadings(page = 1) {
  const startDate = document.getElementById("readingsStartDate")?.value || getTodayDateString();
  const endDate = document.getElementById("readingsEndDate")?.value || getTodayDateString();
  const minConsumption = document.getElementById("readingsMinConsumption")?.value;

  try {
    let url = `/api/v1/meters/${window.METER_ID}/readings-paginated?start_date=${startDate}&end_date=${endDate}&page=${page}&per_page=${readingsPerPage}`;
    if (minConsumption && parseFloat(minConsumption) > 0) {
      url += `&min_consumption=${minConsumption}`;
    }
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error("Failed to fetch readings");
    }

    const data = await response.json();
    updateReadingsTable(data);
    updateReadingsPagination(data.pagination);
  } catch (error) {
    console.error("Error fetching readings:", error);
    showReadingsError("Failed to load readings");
  }
}

function updateReadingsTable(data) {
  const tbody = document.getElementById("readingsTableBody");
  if (!tbody) return;

  if (!data.data || data.data.length === 0) {
    const colSpan = 6;
    tbody.innerHTML = `
      <tr>
        <td colspan="${colSpan}" class="px-6 py-8 text-center text-gray-500 dark:text-gray-400">
          <i class="fas fa-inbox mr-2"></i>No readings found for the selected date range
        </td>
      </tr>
    `;
    return;
  }

  const unit = getReadingUnit();
  const isElectricity = window.METER_TYPE === "electricity" || window.METER_TYPE === "solar";
  const isWater = isWaterType(window.METER_TYPE);

  tbody.innerHTML = data.data.map(r => {
    const dateTime = r.reading_date_sast || r.reading_date || "—";
    const readingValue = r.reading_value !== null ? parseFloat(r.reading_value).toFixed(3) : "—";
    const consumption = r.consumption_since_last !== null ? parseFloat(r.consumption_since_last).toFixed(4) : "—";
    const status = r.status || "—";

    let extraCols = "";
    if (isElectricity) {
      const power = r.power !== null ? r.power : "—";
      const voltage = r.voltage !== null ? r.voltage : "—";
      extraCols = `
        <td class="px-6 py-4">${power}</td>
        <td class="px-6 py-4">${voltage}</td>
      `;
    } else if (isWater) {
      const flowRate = r.flow_rate !== null ? r.flow_rate : "—";
      const temperature = r.temperature !== null ? r.temperature : "—";
      extraCols = `
        <td class="px-6 py-4">${flowRate}</td>
        <td class="px-6 py-4">${temperature}</td>
      `;
    }

    return `
      <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
        <td class="px-6 py-4 text-xs font-mono">${dateTime}</td>
        <td class="px-6 py-4 font-mono">${readingValue}</td>
        <td class="px-6 py-4">${consumption}</td>
        ${extraCols}
        <td class="px-6 py-4">${status}</td>
      </tr>
    `;
  }).join("");
}

function updateReadingsPagination(pagination) {
  readingsCurrentPage = pagination.page;
  readingsTotalPages = pagination.total_pages;

  const paginationInfo = document.getElementById("readingsPaginationInfo");
  const prevBtn = document.getElementById("readingsPrevBtn");
  const nextBtn = document.getElementById("readingsNextBtn");
  const pageNumbersContainer = document.getElementById("readingsPageNumbers");

  if (paginationInfo) {
    const start = pagination.total === 0 ? 0 : (pagination.page - 1) * pagination.per_page + 1;
    const end = Math.min(pagination.page * pagination.per_page, pagination.total);
    paginationInfo.textContent = `Showing ${start}-${end} of ${pagination.total} readings`;
  }

  if (prevBtn) {
    prevBtn.disabled = pagination.page <= 1;
  }
  if (nextBtn) {
    nextBtn.disabled = pagination.page >= pagination.total_pages;
  }

  // Generate page numbers
  if (pageNumbersContainer) {
    pageNumbersContainer.innerHTML = generatePageNumbers(
      pagination.page,
      pagination.total_pages,
      (page) => fetchReadings(page)
    );
  }
}

function generatePageNumbers(currentPage, totalPages, onClickFn) {
  if (totalPages <= 1) return "";

  const maxVisible = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  // Adjust start if we're near the end
  if (endPage - startPage + 1 < maxVisible) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  let html = "";

  // First page + ellipsis
  if (startPage > 1) {
    html += `<button onclick="(${onClickFn.toString()})(1)" class="px-2 py-1 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">1</button>`;
    if (startPage > 2) {
      html += `<span class="px-1 text-gray-400">...</span>`;
    }
  }

  // Page numbers
  for (let i = startPage; i <= endPage; i++) {
    const isActive = i === currentPage;
    const activeClass = isActive
      ? "bg-primary text-white"
      : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600";
    html += `<button data-page="${i}" class="page-num-btn px-2 py-1 text-sm rounded-lg ${activeClass}">${i}</button>`;
  }

  // Last page + ellipsis
  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      html += `<span class="px-1 text-gray-400">...</span>`;
    }
    html += `<button data-page="${totalPages}" class="page-num-btn px-2 py-1 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">${totalPages}</button>`;
  }

  return html;
}

function showReadingsError(message) {
  const tbody = document.getElementById("readingsTableBody");
  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-6 py-8 text-center text-red-500 dark:text-red-400">
          <i class="fas fa-exclamation-triangle mr-2"></i>${message}
        </td>
      </tr>
    `;
  }
}

function setupReadingsControls() {
  const filterBtn = document.getElementById("filterReadingsBtn");
  const prevBtn = document.getElementById("readingsPrevBtn");
  const nextBtn = document.getElementById("readingsNextBtn");
  const pageNumbersContainer = document.getElementById("readingsPageNumbers");

  if (filterBtn) {
    filterBtn.addEventListener("click", () => {
      readingsCurrentPage = 1;
      fetchReadings(1);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (readingsCurrentPage > 1) {
        fetchReadings(readingsCurrentPage - 1);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      if (readingsCurrentPage < readingsTotalPages) {
        fetchReadings(readingsCurrentPage + 1);
      }
    });
  }

  // Event delegation for page number buttons
  if (pageNumbersContainer) {
    pageNumbersContainer.addEventListener("click", (e) => {
      const btn = e.target.closest(".page-num-btn");
      if (btn) {
        const page = parseInt(btn.dataset.page, 10);
        if (page && page !== readingsCurrentPage) {
          fetchReadings(page);
        }
      }
    });
  }

  // Also allow Enter key on date inputs to trigger filter
  const startDateInput = document.getElementById("readingsStartDate");
  const endDateInput = document.getElementById("readingsEndDate");
  const minConsumptionInput = document.getElementById("readingsMinConsumption");

  if (startDateInput) {
    startDateInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        readingsCurrentPage = 1;
        fetchReadings(1);
      }
    });
  }

  if (endDateInput) {
    endDateInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        readingsCurrentPage = 1;
        fetchReadings(1);
      }
    });
  }

  if (minConsumptionInput) {
    minConsumptionInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        readingsCurrentPage = 1;
        fetchReadings(1);
      }
    });
  }
}

// ============================================
// Transactions Table Functions
// ============================================

function initTransactionDateFilters() {
  const today = getTodayDateString();
  const startDateInput = document.getElementById("txnStartDate");
  const endDateInput = document.getElementById("txnEndDate");

  if (startDateInput) {
    startDateInput.value = today;
  }
  if (endDateInput) {
    endDateInput.value = today;
  }
}

async function fetchTransactions(page = 1) {
  const startDate = document.getElementById("txnStartDate")?.value || getTodayDateString();
  const endDate = document.getElementById("txnEndDate")?.value || getTodayDateString();

  try {
    const url = `/api/v1/meters/${window.METER_ID}/transactions?start_date=${startDate}&end_date=${endDate}&page=${page}&per_page=${txnPerPage}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error("Failed to fetch transactions");
    }

    const data = await response.json();
    updateTransactionsTable(data);
    updateTransactionsSummary(data.summary);
    updateTransactionsPagination(data.pagination);
  } catch (error) {
    console.error("Error fetching transactions:", error);
    showTransactionsError("Failed to load transactions");
  }
}

function updateTransactionsTable(data) {
  const tbody = document.getElementById("txnTableBody");
  if (!tbody) return;

  if (!data.data || data.data.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-4 py-8 text-center text-gray-500 dark:text-gray-400">
          <i class="fas fa-inbox mr-2"></i>No transactions found for the selected date range
        </td>
      </tr>
    `;
    return;
  }

  const unit = getConsumptionUnit();

  tbody.innerHTML = data.data.map(txn => {
    const statusClass = txn.status === "completed"
      ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300"
      : "bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300";

    const consumption = txn.consumption_kwh !== null
      ? `${parseFloat(txn.consumption_kwh).toFixed(4)} ${unit}`
      : "—";

    const rate = txn.rate_applied !== null
      ? `R${parseFloat(txn.rate_applied).toFixed(4)}/${unit}`
      : "—";

    const amount = txn.amount !== null
      ? `R${parseFloat(txn.amount).toFixed(2)}`
      : "—";

    const balanceAfter = txn.balance_after !== null
      ? `R${parseFloat(txn.balance_after).toFixed(2)}`
      : "—";

    const dateTime = txn.created_at_sast || txn.created_at || "—";

    return `
      <tr class="bg-white border-b dark:bg-gray-800 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700">
        <td class="px-4 py-3 text-xs font-mono">${dateTime}</td>
        <td class="px-4 py-3">${consumption}</td>
        <td class="px-4 py-3">${rate}</td>
        <td class="px-4 py-3 font-medium">${amount}</td>
        <td class="px-4 py-3">${balanceAfter}</td>
        <td class="px-4 py-3">
          <span class="inline-flex items-center px-2 py-0.5 rounded text-xs ${statusClass}">
            ${txn.status || "—"}
          </span>
        </td>
      </tr>
    `;
  }).join("");
}

function updateTransactionsSummary(summary) {
  const totalConsumption = document.getElementById("txnTotalConsumption");
  const totalAmount = document.getElementById("txnTotalAmount");
  const txnCount = document.getElementById("txnCount");

  const unit = getConsumptionUnit();

  if (totalConsumption) {
    totalConsumption.textContent = `${(summary.total_consumption || 0).toFixed(4)} ${unit}`;
  }
  if (totalAmount) {
    totalAmount.textContent = `R${(summary.total_amount || 0).toFixed(2)}`;
  }
  if (txnCount) {
    txnCount.textContent = summary.transaction_count || 0;
  }
}

function updateTransactionsPagination(pagination) {
  txnCurrentPage = pagination.page;
  txnTotalPages = pagination.total_pages;

  const paginationInfo = document.getElementById("txnPaginationInfo");
  const prevBtn = document.getElementById("txnPrevBtn");
  const nextBtn = document.getElementById("txnNextBtn");
  const pageNumbersContainer = document.getElementById("txnPageNumbers");

  if (paginationInfo) {
    const start = pagination.total === 0 ? 0 : (pagination.page - 1) * pagination.per_page + 1;
    const end = Math.min(pagination.page * pagination.per_page, pagination.total);
    paginationInfo.textContent = `Showing ${start}-${end} of ${pagination.total} transactions`;
  }

  if (prevBtn) {
    prevBtn.disabled = pagination.page <= 1;
  }
  if (nextBtn) {
    nextBtn.disabled = pagination.page >= pagination.total_pages;
  }

  // Generate page numbers for transactions
  if (pageNumbersContainer) {
    pageNumbersContainer.innerHTML = generateTxnPageNumbers(
      pagination.page,
      pagination.total_pages
    );
  }
}

function generateTxnPageNumbers(currentPage, totalPages) {
  if (totalPages <= 1) return "";

  const maxVisible = 5;
  let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
  let endPage = Math.min(totalPages, startPage + maxVisible - 1);

  if (endPage - startPage + 1 < maxVisible) {
    startPage = Math.max(1, endPage - maxVisible + 1);
  }

  let html = "";

  if (startPage > 1) {
    html += `<button data-page="1" class="txn-page-num-btn px-2 py-1 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">1</button>`;
    if (startPage > 2) {
      html += `<span class="px-1 text-gray-400">...</span>`;
    }
  }

  for (let i = startPage; i <= endPage; i++) {
    const isActive = i === currentPage;
    const activeClass = isActive
      ? "bg-primary text-white"
      : "bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-300 dark:hover:bg-gray-600";
    html += `<button data-page="${i}" class="txn-page-num-btn px-2 py-1 text-sm rounded-lg ${activeClass}">${i}</button>`;
  }

  if (endPage < totalPages) {
    if (endPage < totalPages - 1) {
      html += `<span class="px-1 text-gray-400">...</span>`;
    }
    html += `<button data-page="${totalPages}" class="txn-page-num-btn px-2 py-1 text-sm rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 bg-gray-200 dark:bg-gray-700 text-gray-600 dark:text-gray-400">${totalPages}</button>`;
  }

  return html;
}

function showTransactionsError(message) {
  const tbody = document.getElementById("txnTableBody");
  if (tbody) {
    tbody.innerHTML = `
      <tr>
        <td colspan="6" class="px-4 py-8 text-center text-red-500 dark:text-red-400">
          <i class="fas fa-exclamation-triangle mr-2"></i>${message}
        </td>
      </tr>
    `;
  }
}

function setupTransactionsControls() {
  const filterBtn = document.getElementById("filterTxnBtn");
  const prevBtn = document.getElementById("txnPrevBtn");
  const nextBtn = document.getElementById("txnNextBtn");
  const pageNumbersContainer = document.getElementById("txnPageNumbers");

  if (filterBtn) {
    filterBtn.addEventListener("click", () => {
      txnCurrentPage = 1;
      fetchTransactions(1);
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (txnCurrentPage > 1) {
        fetchTransactions(txnCurrentPage - 1);
      }
    });
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      if (txnCurrentPage < txnTotalPages) {
        fetchTransactions(txnCurrentPage + 1);
      }
    });
  }

  // Event delegation for page number buttons
  if (pageNumbersContainer) {
    pageNumbersContainer.addEventListener("click", (e) => {
      const btn = e.target.closest(".txn-page-num-btn");
      if (btn) {
        const page = parseInt(btn.dataset.page, 10);
        if (page && page !== txnCurrentPage) {
          fetchTransactions(page);
        }
      }
    });
  }

  // Also allow Enter key on date inputs to trigger filter
  const startDateInput = document.getElementById("txnStartDate");
  const endDateInput = document.getElementById("txnEndDate");

  if (startDateInput) {
    startDateInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        txnCurrentPage = 1;
        fetchTransactions(1);
      }
    });
  }

  if (endDateInput) {
    endDateInput.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        txnCurrentPage = 1;
        fetchTransactions(1);
      }
    });
  }
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  // Initial data fetch
  fetchRealtimeStats();
  fetchChartData(currentPeriod);

  // Setup event listeners
  setupPeriodButtons();

  // Start auto-refresh
  startAutoRefresh();

  // Setup Relay Controls (Disconnect/Reconnect)
  setupRelayControls();

  // Initialize and fetch readings
  initReadingsDateFilters();
  setupReadingsControls();
  fetchReadings(1);

  // Initialize and fetch transactions
  initTransactionDateFilters();
  setupTransactionsControls();
  fetchTransactions(1);

  // Top Up Modal Event Listeners
  const topUpBtn = document.getElementById("topUpBtn");
  const closeTopUpModalBtn = document.getElementById("closeTopUpModal");
  const cancelTopUpBtn = document.getElementById("cancelTopUpBtn");
  const topUpForm = document.getElementById("topUpForm");

  if (topUpBtn) {
    topUpBtn.addEventListener("click", openTopUpModal);
  }

  if (closeTopUpModalBtn) {
    closeTopUpModalBtn.addEventListener("click", closeTopUpModal);
  }

  if (cancelTopUpBtn) {
    cancelTopUpBtn.addEventListener("click", closeTopUpModal);
  }

  if (topUpForm) {
    topUpForm.addEventListener("submit", handleTopUpSubmit);
  }

  // Close modal when clicking outside
  const modal = document.getElementById("topUpModal");
  if (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeTopUpModal();
      }
    });
  }
});
