// Reports page JavaScript

// Auto-refresh functionality for real-time reports
function autoRefresh() {
  if (window.location.search.includes("auto_refresh=true")) {
    setTimeout(() => {
      window.location.reload();
    }, 30000); // Refresh every 30 seconds
  }
}

// Export functionality
function exportReport(reportType, format) {
  const url = new URL(window.location);
  url.pathname = "/api/v1/reports/export/" + reportType;
  url.searchParams.set("format", format);
  url.searchParams.set("category", window.REPORT_CONFIG.category);
  url.searchParams.set("date_range", window.REPORT_CONFIG.dateRange);
  if (window.REPORT_CONFIG.estateId) {
    url.searchParams.set("estate_id", window.REPORT_CONFIG.estateId);
  }
  if (window.REPORT_CONFIG.meterType) {
    url.searchParams.set("meter_type", window.REPORT_CONFIG.meterType);
  }

  window.open(url.toString(), "_blank");
}

// Tab switching functionality for top consumers
function showTopConsumersTab(utilityType) {
  // Hide all content
  const contents = document.querySelectorAll(".top-consumers-content");
  contents.forEach((content) => content.classList.add("hidden"));

  // Remove active state from all tabs
  const tabs = document.querySelectorAll('[id$="-tab"]');
  tabs.forEach((tab) => {
    tab.classList.remove("bg-primary", "text-white");
    tab.classList.add(
      "bg-gray-200",
      "dark:bg-gray-700",
      "text-gray-700",
      "dark:text-gray-300"
    );
  });

  // Show selected content
  const selectedContent = document.getElementById(utilityType + "-content");
  if (selectedContent) {
    selectedContent.classList.remove("hidden");
  }

  // Activate selected tab
  const selectedTab = document.getElementById(utilityType + "-tab");
  if (selectedTab) {
    selectedTab.classList.remove(
      "bg-gray-200",
      "dark:bg-gray-700",
      "text-gray-700",
      "dark:text-gray-300"
    );
    selectedTab.classList.add("bg-primary", "text-white");
  }
}

// Helper function to detect dark mode
function isDarkMode() {
  return document.documentElement.classList.contains("dark");
}

// Helper function to get chart colors based on theme
function getChartColors() {
  return {
    text: isDarkMode() ? "#ffffff" : "#000000",
    grid: isDarkMode() ? "#374151" : "#e5e7eb",
    background: isDarkMode()
      ? "rgba(31, 41, 55, 0.1)"
      : "rgba(255, 255, 255, 0.1)",
  };
}

// Initialize charts when DOM is ready
document.addEventListener("DOMContentLoaded", function () {
  autoRefresh();
  initializeCharts();
});

// Initialize all charts
function initializeCharts() {
  const colors = getChartColors();

  // Daily Consumption Trend Chart
  if (
    window.REPORT_CONFIG.dailyConsumptionTrend &&
    document.getElementById("dailyConsumptionChart")
  ) {
    initDailyConsumptionChart(colors);
  }

  // Estate Comparison Chart
  if (
    window.REPORT_CONFIG.bulkSubComparison &&
    document.getElementById("estateComparisonChart")
  ) {
    initEstateComparisonChart(colors);
  }

  // Revenue Chart
  if (
    window.REPORT_CONFIG.creditPurchases &&
    document.getElementById("revenueChart")
  ) {
    initRevenueChart(colors);
  }

  // Occupancy Chart
  if (
    window.REPORT_CONFIG.estateUtilitySummary &&
    document.getElementById("occupancyChart")
  ) {
    initOccupancyChart(colors);
  }

  // Utility Chart
  if (
    window.REPORT_CONFIG.estateUtilitySummary &&
    document.getElementById("utilityChart")
  ) {
    initUtilityChart(colors);
  }

  // Set up dark mode observer
  setupDarkModeObserver();
}

// Daily Consumption Trend Chart
function initDailyConsumptionChart(colors) {
  const trendData = window.REPORT_CONFIG.dailyConsumptionTrend;
  const days = [];
  const electricityData = [];
  const waterData = [];
  const hotWaterData = [];
  const solarData = [];

  trendData.forEach((day) => {
    const date = new Date(day.date);
    days.push(date.toLocaleDateString("en-US", { month: "short", day: "numeric" }));
    electricityData.push(parseFloat(day.electricity) || 0);
    waterData.push(parseFloat(day.water) || 0);
    hotWaterData.push(parseFloat(day.hot_water) || 0);
    solarData.push(parseFloat(day.solar) || 0);
  });

  const ctx = document
    .getElementById("dailyConsumptionChart")
    .getContext("2d");

  window.dailyConsumptionChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: days,
      datasets: [
        {
          label: "Electricity (kWh)",
          data: electricityData,
          borderColor: "#F59E0B",
          backgroundColor: "rgba(245, 158, 11, 0.1)",
          borderWidth: 2,
          fill: false,
          tension: 0.4,
        },
        {
          label: "Water (kL)",
          data: waterData,
          borderColor: "#3B82F6",
          backgroundColor: "rgba(59, 130, 246, 0.1)",
          borderWidth: 2,
          fill: false,
          tension: 0.4,
        },
        {
          label: "Hot Water (kL)",
          data: hotWaterData,
          borderColor: "#F97316",
          backgroundColor: "rgba(249, 115, 22, 0.1)",
          borderWidth: 2,
          fill: false,
          tension: 0.4,
        },
        {
          label: "Solar (kWh)",
          data: solarData,
          borderColor: "#10B981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          borderWidth: 2,
          fill: false,
          tension: 0.4,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: colors.text, font: { size: 12 } },
          grid: { color: colors.grid },
          title: {
            display: true,
            text: "Consumption",
            color: colors.text,
            font: { size: 14, weight: "bold" },
          },
        },
        x: {
          ticks: { color: colors.text, font: { size: 12 } },
          grid: { color: colors.grid },
          title: {
            display: true,
            text: "Date",
            color: colors.text,
            font: { size: 14, weight: "bold" },
          },
        },
      },
      plugins: {
        legend: {
          labels: {
            color: colors.text,
            font: { size: 12, weight: "bold" },
            usePointStyle: true,
            pointStyle: "circle",
          },
        },
      },
    },
  });
}

// Estate Comparison Chart
function initEstateComparisonChart(colors) {
  const data = window.REPORT_CONFIG.bulkSubComparison;
  const labels = data.map((row) => row.estate_name);
  const bulkData = data.map(
    (row) => (row.bulk_electricity || 0) + (row.bulk_water || 0)
  );
  const subData = data.map(
    (row) => (row.sub_electricity || 0) + (row.sub_water || 0)
  );

  const ctx = document
    .getElementById("estateComparisonChart")
    .getContext("2d");

  window.estateComparisonChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Bulk Consumption",
          data: bulkData,
          backgroundColor: "#3B82F6",
          borderWidth: 1,
          borderColor: isDarkMode() ? "#1f2937" : "#ffffff",
        },
        {
          label: "Sub-meter Consumption",
          data: subData,
          backgroundColor: "#10B981",
          borderWidth: 1,
          borderColor: isDarkMode() ? "#1f2937" : "#ffffff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: { color: colors.text, font: { size: 12 } },
          grid: { color: colors.grid },
          title: {
            display: true,
            text: "Consumption",
            color: colors.text,
            font: { size: 14, weight: "bold" },
          },
        },
        x: {
          ticks: { color: colors.text, font: { size: 12 } },
          grid: { color: colors.grid },
          title: {
            display: true,
            text: "Estate",
            color: colors.text,
            font: { size: 14, weight: "bold" },
          },
        },
      },
      plugins: {
        legend: {
          labels: {
            color: colors.text,
            font: { size: 12, weight: "bold" },
            usePointStyle: true,
            pointStyle: "rect",
          },
        },
      },
    },
  });
}

// Revenue Chart
function initRevenueChart(colors) {
  const data = window.REPORT_CONFIG.creditPurchases.slice(0, 10);
  const labels = data.map((row) =>
    row.completed_at
      ? new Date(row.completed_at).toLocaleDateString("en-US", {
          month: "2-digit",
          day: "2-digit",
        })
      : "N/A"
  );
  const amounts = data.map((row) => row.amount || 0);

  const ctx = document.getElementById("revenueChart").getContext("2d");

  window.revenueChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Revenue (R)",
          data: amounts,
          borderColor: "#10B981",
          backgroundColor: "rgba(16, 185, 129, 0.1)",
          tension: 0.4,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              return "R " + value.toFixed(2);
            },
          },
        },
      },
    },
  });
}

// Occupancy Chart
function initOccupancyChart(colors) {
  const data = window.REPORT_CONFIG.estateUtilitySummary;
  const labels = data.map((row) => row.estate_name);
  const occupiedData = data.map((row) => row.occupied_units || 0);
  const vacantData = data.map(
    (row) => (row.total_units || 0) - (row.occupied_units || 0)
  );

  const ctx = document.getElementById("occupancyChart").getContext("2d");

  window.occupancyChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Occupied Units",
          data: occupiedData,
          backgroundColor: "rgba(16, 185, 129, 0.8)",
          borderColor: "#10B981",
          borderWidth: 1,
        },
        {
          label: "Vacant Units",
          data: vacantData,
          backgroundColor: "rgba(156, 163, 175, 0.8)",
          borderColor: "#9CA3AF",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
      },
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

// Utility Chart
function initUtilityChart(colors) {
  const data = window.REPORT_CONFIG.estateUtilitySummary;
  const labels = data.map((row) => row.estate_name);

  const ctx = document.getElementById("utilityChart").getContext("2d");

  window.utilityChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Electricity (kWh)",
          data: data.map((row) => row.total_electricity || 0),
          backgroundColor: "rgba(251, 188, 4, 0.8)",
          borderColor: "#FBBC04",
          borderWidth: 1,
        },
        {
          label: "Water (kL)",
          data: data.map((row) => row.total_water || 0),
          backgroundColor: "rgba(26, 115, 232, 0.8)",
          borderColor: "#1A73E8",
          borderWidth: 1,
        },
        {
          label: "Hot Water (kL)",
          data: data.map((row) => row.total_hot_water || 0),
          backgroundColor: "rgba(249, 115, 22, 0.8)",
          borderColor: "#F97316",
          borderWidth: 1,
        },
        {
          label: "Solar (kWh)",
          data: data.map((row) => row.total_solar || 0),
          backgroundColor: "rgba(52, 168, 83, 0.8)",
          borderColor: "#34A853",
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "bottom" },
      },
      scales: {
        y: { beginAtZero: true },
      },
    },
  });
}

// Set up dark mode observer
function setupDarkModeObserver() {
  const observer = new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      if (
        mutation.type === "attributes" &&
        mutation.attributeName === "class"
      ) {
        const colors = getChartColors();
        updateChartColors(colors);
      }
    });
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ["class"],
  });
}

// Update chart colors on theme change
function updateChartColors(colors) {
  const charts = [
    window.dailyConsumptionChart,
    window.estateComparisonChart,
    window.revenueChart,
    window.occupancyChart,
    window.utilityChart,
  ];

  charts.forEach((chart) => {
    if (chart) {
      if (chart.options.scales && chart.options.scales.y) {
        chart.options.scales.y.ticks.color = colors.text;
        chart.options.scales.y.grid.color = colors.grid;
        if (chart.options.scales.y.title) {
          chart.options.scales.y.title.color = colors.text;
        }
      }
      if (chart.options.scales && chart.options.scales.x) {
        chart.options.scales.x.ticks.color = colors.text;
        chart.options.scales.x.grid.color = colors.grid;
        if (chart.options.scales.x.title) {
          chart.options.scales.x.title.color = colors.text;
        }
      }
      if (chart.options.plugins && chart.options.plugins.legend) {
        chart.options.plugins.legend.labels.color = colors.text;
      }
      chart.update();
    }
  });
}
