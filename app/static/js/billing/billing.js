function applyFilters() {
  const form = document.getElementById("walletFilters");
  form.submit();
}

function clearFilters() {
  window.location.href = "/api/v1/billing";
}

document.addEventListener("DOMContentLoaded", function () {
  // Tab switching functionality
  const tabButtons = document.querySelectorAll(".tab-button");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach((button) => {
    button.addEventListener("click", function () {
      const targetTab = this.getAttribute("data-tab");

      // Remove active class from all buttons
      tabButtons.forEach((btn) => {
        btn.classList.remove("border-primary", "text-primary");
        btn.classList.add(
          "border-transparent",
          "text-gray-500",
          "hover:text-gray-700",
          "dark:hover:text-gray-300"
        );
      });

      // Add active class to clicked button
      this.classList.add("border-primary", "text-primary");
      this.classList.remove(
        "border-transparent",
        "text-gray-500",
        "hover:text-gray-700",
        "dark:hover:text-gray-300"
      );

      // Hide all tab contents
      tabContents.forEach((content) => {
        content.classList.add("hidden");
      });

      // Show target tab content
      const targetContent = document.getElementById(targetTab);
      if (targetContent) {
        targetContent.classList.remove("hidden");
      }
    });
  });
});
