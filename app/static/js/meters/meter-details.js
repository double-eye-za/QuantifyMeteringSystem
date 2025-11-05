// Meter Details - Real-time Data and Charts
let consumptionChart = null;
let currentPeriod = "day";

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
    lastReadingTime.textContent = `Last: ${timestamp.toLocaleString()}`;
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

// Initialize on page load
document.addEventListener("DOMContentLoaded", function () {
  // Initial data fetch
  fetchRealtimeStats();
  fetchChartData(currentPeriod);

  // Setup event listeners
  setupPeriodButtons();

  // Start auto-refresh
  startAutoRefresh();
});
