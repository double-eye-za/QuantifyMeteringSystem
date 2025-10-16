console.log("Hello from flash.js");
function showFlashMessage(message, type = "success", persist = false) {
  console.log("Showing flash message:");
  if (persist) {
    const flashData = {
      message: message,
      type: type,
      timestamp: Date.now(),
    };
    sessionStorage.setItem("flashMessage", JSON.stringify(flashData));
    return;
  }

  const existingFlash = document.querySelector(".flash-message");
  if (existingFlash) {
    existingFlash.remove();
  }

  const flashDiv = document.createElement("div");
  flashDiv.className = `flash-message fixed top-4 right-4 z-50 px-6 py-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;

  const bgColor = type === "success" ? "bg-green-500" : "bg-red-500";
  const icon = type === "success" ? "fa-check-circle" : "fa-exclamation-circle";

  flashDiv.innerHTML = `
        <div class="flex items-center space-x-3 text-white">
            <i class="fa-solid ${icon}"></i>
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4 hover:text-gray-200">
                <i class="fa-solid fa-times"></i>
            </button>
        </div>
    `;

  flashDiv.classList.add(bgColor);
  document.body.appendChild(flashDiv);

  setTimeout(() => {
    flashDiv.classList.remove("translate-x-full");
  }, 100);

  setTimeout(() => {
    if (flashDiv.parentElement) {
      flashDiv.classList.add("translate-x-full");
      setTimeout(() => {
        if (flashDiv.parentElement) {
          flashDiv.remove();
        }
      }, 300);
    }
  }, 5000);
}

function checkStoredFlashMessage() {
  const storedFlash = sessionStorage.getItem("flashMessage");
  if (storedFlash) {
    try {
      const flashData = JSON.parse(storedFlash);

      if (Date.now() - flashData.timestamp < 15000) {
        showFlashMessage(flashData.message, flashData.type);
      }

      sessionStorage.removeItem("flashMessage");
    } catch (e) {
      sessionStorage.removeItem("flashMessage");
    }
  }
}

document.addEventListener("DOMContentLoaded", function () {
  checkStoredFlashMessage();
});
