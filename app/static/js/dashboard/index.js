// Auto-refresh every 5 minutes
setInterval(() => {
  location.reload();
}, 300000);

document.addEventListener("DOMContentLoaded", function () {
  // Add tooltip functionality to KPI cards
  const kpiCards = document.querySelectorAll(
    ".bg-white.dark\\:bg-gray-800.rounded-lg.shadow-sm.p-4"
  );
  kpiCards.forEach((card) => {
    card.addEventListener("mouseenter", function () {
      this.style.transform = "translateY(-2px)";
      this.style.transition = "transform 0.2s ease";
    });
    card.addEventListener("mouseleave", function () {
      this.style.transform = "translateY(0)";
    });
  });

  // Handle filter changes
  const estateFilter = document.getElementById("estateFilter");
  const dateRange = document.getElementById("dateRange");

  function updateDashboard() {
    const estateId = estateFilter.value;
    const timePeriod = dateRange.value;

    // Build URL with parameters
    const url = new URL(window.location);
    url.searchParams.set("estate", estateId);
    url.searchParams.set("period", timePeriod);

    window.location.href = url.toString();
  }

  estateFilter.addEventListener("change", updateDashboard);
  dateRange.addEventListener("change", updateDashboard);

  // Set initial values from URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const estateParam = urlParams.get("estate");
  const periodParam = urlParams.get("period");

  if (estateParam) {
    estateFilter.value = estateParam;
  }
  if (periodParam) {
    dateRange.value = periodParam;
  }
});
