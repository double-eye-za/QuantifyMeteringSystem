function showFlashMessage(message, type = "success", persist = false) {
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

  let bgColor, icon;
  if (type === "success") {
    bgColor = "bg-green-500";
    icon = "fa-check-circle";
  } else if (type === "warning") {
    bgColor = "bg-yellow-500";
    icon = "fa-exclamation-triangle";
  } else {
    bgColor = "bg-red-500";
    icon = "fa-exclamation-circle";
  }

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
