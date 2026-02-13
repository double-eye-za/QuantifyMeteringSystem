const API_BASE_URL = "/api/v1";

document.addEventListener("DOMContentLoaded", function () {
  setupLoginForm();
  setupLogoutButtons();
  setupSessionHandling();
});

// Global session handling for AJAX requests
function setupSessionHandling() {
  const originalFetch = window.fetch;
  window.fetch = async function (...args) {
    const response = await originalFetch.apply(this, args);

    if (response.status === 401) {
      try {
        const errorData = await response.json();
        if (errorData.redirect) {
          showFlashMessage(
            "Your session has expired. Please log in again to continue.",
            "warning"
          );
          setTimeout(() => {
            window.location.href = errorData.redirect;
          }, 1000);
        } else {
          window.location.href = "/api/v1/login";
        }
      } catch (e) {
        window.location.href = "/api/v1/login";
      }
    }

    return response;
  };

  // Periodic session check (every 5 minutes)
  setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/auth/status`, {
        method: "GET",
        credentials: "include",
      });

      if (!response.ok) {
        // Session expired, redirect to login
        showFlashMessage(
          "Your session has expired. Please log in again to continue.",
          "warning"
        );
        setTimeout(() => {
          window.location.href = "/api/v1/login";
        }, 2000);
      }
    } catch (error) {
      console.log("Session check failed:", error);
    }
  }, 5 * 60 * 1000);
}

function setupLoginForm() {
  const loginForm = document.getElementById("loginForm");
  if (!loginForm) return;

  loginForm.addEventListener("submit", function (e) {
    e.preventDefault();
    handleLogin();
  });
}

function setupLogoutButtons() {
  // Setup logout buttons for both sidebar and header
  const logoutButtons = document.querySelectorAll(
    "#logoutButton, #logoutButtonHeader"
  );
  logoutButtons.forEach((button) => {
    button.addEventListener("click", function (e) {
      e.preventDefault();
      handleLogout();
    });
  });
}

// Global logout function that can be called from anywhere
function logout() {
  handleLogout();
}

async function handleLogin() {
  const credentialInput = document.getElementById("credential");
  const passwordInput = document.getElementById("password");
  const credentialError = document.getElementById("credentialError");
  const passwordError = document.getElementById("passwordError");
  const errorMessage = document.getElementById("errorMessage");
  const successMessage = document.getElementById("successMessage");
  const buttonText = document.getElementById("buttonText");
  const loadingIcon = document.getElementById("loadingIcon");
  const submitButton = document.querySelector('button[type="submit"]');

  hideElement(credentialError);
  hideElement(passwordError);
  hideElement(errorMessage);
  hideElement(successMessage);

  // Validate inputs
  let isValid = true;

  if (!credentialInput.value.trim()) {
    showElement(credentialError);
    credentialInput.classList.add("border-error");
    isValid = false;
  } else {
    credentialInput.classList.remove("border-error");
  }

  if (!passwordInput.value) {
    showElement(passwordError);
    passwordInput.classList.add("border-error");
    isValid = false;
  } else {
    passwordInput.classList.remove("border-error");
  }

  if (!isValid) return;

  // Show loading state
  buttonText.textContent = "Signing in...";
  showElement(loadingIcon);
  submitButton.disabled = true;

  try {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        credential: credentialInput.value.trim(),
        password: passwordInput.value,
      }),
    });

    if (response.ok) {
      const data = await response.json();
      showElement(successMessage);
      // Use redirect URL from server (admin → dashboard, portal → portal dashboard)
      const redirectUrl = data.redirect || "/api/v1/dashboard";
      setTimeout(function () {
        window.location.href = redirectUrl;
      }, 1500);
    } else {
      const errorData = await response.json();
      showElement(errorMessage);
      const errorText = document.getElementById("errorText");
      if (errorText) {
        errorText.textContent =
          errorData.error || "Invalid credentials. Please try again.";
      }
    }
  } catch (error) {
    console.error("Login error:", error);
    showElement(errorMessage);
    const errorText = document.getElementById("errorText");
    if (errorText) {
      errorText.textContent = "Network error. Please try again.";
    }
  } finally {
    // Reset button state
    buttonText.textContent = "Sign in";
    hideElement(loadingIcon);
    submitButton.disabled = false;
  }
}

async function handleLogout() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      // Redirect to login page
      window.location.href = "/api/v1/login";
    } else {
      console.error("Logout failed");
      // Still redirect to login page even if logout fails
      window.location.href = "/api/v1/login";
    }
  } catch (error) {
    console.error("Logout error:", error);
    // Still redirect to login page even if logout fails
    window.location.href = "/api/v1/login";
  }
}

function showElement(element) {
  if (element) {
    element.classList.remove("hidden");
  }
}

function hideElement(element) {
  if (element) {
    element.classList.add("hidden");
  }
}

async function checkAuthStatus() {
  try {
    const response = await fetch(`${API_BASE_URL}/auth/status`, {
      method: "GET",
      credentials: "include",
    });
    return response.ok;
  } catch (error) {
    console.error("Auth status check error:", error);
    return false;
  }
}
