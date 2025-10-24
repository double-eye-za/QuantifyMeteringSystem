const BASE_URL = "/api/v1/profile";

let passwordRequirements = {};

// Load password requirements on page load
document.addEventListener("DOMContentLoaded", function () {
  loadPasswordRequirements();
});

async function loadPasswordRequirements() {
  try {
    const response = await fetch(`${BASE_URL}/password-requirements`);
    const data = await response.json();
    passwordRequirements = data.requirements;
    displayPasswordRequirements();
  } catch (error) {
    console.error("Failed to load password requirements:", error);
    document.getElementById("passwordRequirements").innerHTML =
      '<span class="text-red-600">Failed to load password requirements</span>';
  }
}

function displayPasswordRequirements() {
  const requirementsDiv = document.getElementById("passwordRequirements");
  let requirementsHtml = '<ul class="list-disc list-inside space-y-1">';

  requirementsHtml += `<li>At least ${passwordRequirements.min_length} characters</li>`;

  if (passwordRequirements.require_uppercase) {
    requirementsHtml += "<li>At least one uppercase letter (A-Z)</li>";
  }

  if (passwordRequirements.require_numbers) {
    requirementsHtml += "<li>At least one number (0-9)</li>";
  }

  if (passwordRequirements.require_special_chars) {
    requirementsHtml += "<li>At least one special character (!@#$%^&*...)</li>";
  }

  requirementsHtml += "</ul>";
  requirementsDiv.innerHTML = requirementsHtml;
}

function validatePassword() {
  const password = document.getElementById("newPassword").value;
  const validationDiv = document.getElementById("passwordValidation");
  let isValid = true;
  let messages = [];

  // Check minimum length
  if (password.length < passwordRequirements.min_length) {
    isValid = false;
    messages.push(`At least ${passwordRequirements.min_length} characters`);
  }

  // Check uppercase
  if (passwordRequirements.require_uppercase && !/[A-Z]/.test(password)) {
    isValid = false;
    messages.push("At least one uppercase letter");
  }

  // Check numbers
  if (passwordRequirements.require_numbers && !/[0-9]/.test(password)) {
    isValid = false;
    messages.push("At least one number");
  }

  // Check special characters
  if (
    passwordRequirements.require_special_chars &&
    !/[!@#$%^&*(),.?":{}|<>]/.test(password)
  ) {
    isValid = false;
    messages.push("At least one special character");
  }

  if (password.length === 0) {
    validationDiv.innerHTML = "";
    updateSubmitButton();
    return;
  }

  if (isValid) {
    validationDiv.innerHTML =
      '<span class="text-green-600"><i class="fas fa-check mr-1"></i>Password meets all requirements</span>';
  } else {
    validationDiv.innerHTML =
      '<span class="text-red-600"><i class="fas fa-times mr-1"></i>' +
      messages.join(", ") +
      "</span>";
  }

  updateSubmitButton();
}

function validatePasswordMatch() {
  const password = document.getElementById("newPassword").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const validationDiv = document.getElementById("passwordMatchValidation");

  if (confirmPassword.length === 0) {
    validationDiv.innerHTML = "";
    updateSubmitButton();
    return;
  }

  if (password === confirmPassword) {
    validationDiv.innerHTML =
      '<span class="text-green-600"><i class="fas fa-check mr-1"></i>Passwords match</span>';
  } else {
    validationDiv.innerHTML =
      '<span class="text-red-600"><i class="fas fa-times mr-1"></i>Passwords do not match</span>';
  }

  updateSubmitButton();
}

function updateSubmitButton() {
  const password = document.getElementById("newPassword").value;
  const confirmPassword = document.getElementById("confirmPassword").value;
  const submitBtn = document.getElementById("submitPasswordBtn");

  // Check if password meets all requirements
  let passwordValid = true;
  if (password.length < passwordRequirements.min_length) passwordValid = false;
  if (passwordRequirements.require_uppercase && !/[A-Z]/.test(password))
    passwordValid = false;
  if (passwordRequirements.require_numbers && !/[0-9]/.test(password))
    passwordValid = false;
  if (
    passwordRequirements.require_special_chars &&
    !/[!@#$%^&*(),.?":{}|<>]/.test(password)
  )
    passwordValid = false;

  const passwordsMatch = password === confirmPassword && password.length > 0;

  submitBtn.disabled = !(passwordValid && passwordsMatch);
}

function showTab(tabName) {
  // Hide all tab contents
  document.querySelectorAll(".tab-content").forEach((tab) => {
    tab.classList.add("hidden");
  });

  // Remove active state from all tab buttons
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.classList.remove("border-primary", "text-primary");
    btn.classList.add(
      "border-transparent",
      "text-gray-500",
      "dark:text-gray-400"
    );
  });

  document.getElementById(`${tabName}-tab`).classList.remove("hidden");

  // Add active state to selected tab button
  const activeBtn = document.querySelector(`[data-tab="${tabName}"]`);
  activeBtn.classList.add("border-primary", "text-primary");
  activeBtn.classList.remove(
    "border-transparent",
    "text-gray-500",
    "dark:text-gray-400"
  );
}

async function submitProfile(event) {
  event.preventDefault();
  const payload = {
    first_name: document.getElementById("first_name")?.value || "",
    last_name: document.getElementById("last_name")?.value || "",
    email: document.getElementById("email")?.value || "",
    phone: document.getElementById("phone")?.value || "",
  };
  try {
    const resp = await fetch(`${BASE_URL}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!resp.ok) showFlashMessage("Failed to update profile", "error", true);
    await resp.json();
    window.location.reload();
    showFlashMessage("Profile updated successfully", "success", true);
  } catch (e) {
    console.error("Error updating profile:", e);
    showFlashMessage("Failed to update profile", "error", true);
  }
  return false;
}

async function submitChangePassword(event) {
  event.preventDefault();
  const form = event.target;
  const payload = Object.fromEntries(new FormData(form));

  const password = payload.new_password;
  let passwordValid = true;
  let messages = [];

  if (password.length < passwordRequirements.min_length) {
    passwordValid = false;
    messages.push(`At least ${passwordRequirements.min_length} characters`);
  }
  if (passwordRequirements.require_uppercase && !/[A-Z]/.test(password)) {
    passwordValid = false;
    messages.push("At least one uppercase letter");
  }
  if (passwordRequirements.require_numbers && !/[0-9]/.test(password)) {
    passwordValid = false;
    messages.push("At least one number");
  }
  if (
    passwordRequirements.require_special_chars &&
    !/[!@#$%^&*(),.?":{}|<>]/.test(password)
  ) {
    passwordValid = false;
    messages.push("At least one special character");
  }

  if (!passwordValid) {
    showFlashMessage(
      "Password does not meet requirements: " + messages.join(", "),
      "error",
      true
    );
    return false;
  }

  if (payload.new_password !== payload.confirm_password) {
    showFlashMessage("Passwords do not match", "error", true);
    return false;
  }

  try {
    const resp = await fetch(`${BASE_URL}/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await resp.json();
    if (!resp.ok) {
      window.location.reload();
      showFlashMessage(
        data.error || "Failed to update password",
        "error",
        true
      );
      return false;
    }

    showFlashMessage("Password updated successfully", "success", false);

    form.reset();
    document.getElementById("passwordValidation").innerHTML = "";
    document.getElementById("passwordMatchValidation").innerHTML = "";
    document.getElementById("submitPasswordBtn").disabled = true;
  } catch (e) {
    console.error("Error updating password:", e);
    showFlashMessage("Failed to update password", "error", false);
  }
  return false;
}
