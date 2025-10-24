// Consumption Chart
const ctx = document.getElementById("consumptionChart").getContext("2d");
new Chart(ctx, {
  type: "line",
  data: {
    labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "24:00"],
    datasets: [
      {
        label: "Consumption (kWh)",
        data: [0.8, 0.6, 1.2, 2.4, 2.8, 3.2, 2.1],
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
            return value + " kWh";
          },
        },
      },
    },
  },
});
