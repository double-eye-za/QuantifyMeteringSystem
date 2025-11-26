const BASE_URL = "/api/v1";

function showCreateModal() {
  document.getElementById("invite-modal").classList.remove("hidden");
  document.getElementById("invite-modal").classList.add("flex");
}

function hideCreateModal() {
  document.getElementById("invite-modal").classList.add("hidden");
  document.getElementById("invite-modal").classList.remove("flex");
  document.getElementById("invite-form").reset();
}

function showEditModal() {
  document.getElementById("edit-modal").classList.remove("hidden");
  document.getElementById("edit-modal").classList.add("flex");
}

function hideEditModal() {
  document.getElementById("edit-modal").classList.add("hidden");
  document.getElementById("edit-modal").classList.remove("flex");
  document.getElementById("edit-form").reset();
}

function showConfirmModal(title, message, action) {
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-message").textContent = message;
  document.getElementById("user-confirm-modal").classList.remove("hidden");
  document.getElementById("user-confirm-modal").classList.add("flex");

  document.getElementById("user-confirm-action").onclick = action;
}

function hideConfirmModal() {
  document.getElementById("user-confirm-modal").classList.add("hidden");
  document.getElementById("user-confirm-modal").classList.remove("flex");
}

document.addEventListener("DOMContentLoaded", function () {
  document
    .getElementById("invite-open")
    .addEventListener("click", showCreateModal);
  document
    .getElementById("invite-close")
    .addEventListener("click", hideCreateModal);
  document
    .getElementById("invite-cancel")
    .addEventListener("click", hideCreateModal);

  document
    .getElementById("edit-close")
    .addEventListener("click", hideEditModal);
  document
    .getElementById("edit-cancel")
    .addEventListener("click", hideEditModal);

  document
    .getElementById("user-confirm-close")
    .addEventListener("click", hideConfirmModal);
  document
    .getElementById("user-confirm-cancel")
    .addEventListener("click", hideConfirmModal);

  document.querySelectorAll("[data-user]").forEach((button) => {
    button.addEventListener("click", function () {
      const user = JSON.parse(this.dataset.user);
      populateEditForm(user);
      showEditModal();
    });
  });

  document.querySelectorAll("[data-user-id]").forEach((button) => {
    button.addEventListener("click", function () {
      const userId = this.dataset.userId;
      const user = JSON.parse(this.dataset.userData);
      const isActive = user.is_active;

      if (isActive) {
        showConfirmModal(
          "Disable User",
          `Are you sure you want to disable ${user.full_name}?`,
          () => disableUser(userId)
        );
      } else {
        showConfirmModal(
          "Enable User",
          `Are you sure you want to enable ${user.full_name}?`,
          () => enableUser(userId)
        );
      }
    });
  });

  document.querySelectorAll("[data-delete-user-id]").forEach((button) => {
    button.addEventListener("click", function () {
      const userId = this.dataset.deleteUserId;
      const user = JSON.parse(this.dataset.deleteUserData);

      showConfirmModal(
        "Delete User",
        `Are you sure you want to permanently delete ${user.full_name}? This action cannot be undone.`,
        () => deleteUser(userId)
      );
    });
  });

  document
    .getElementById("invite-form")
    .addEventListener("submit", function (e) {
      e.preventDefault();
      createUser();
    });

  document.getElementById("edit-form").addEventListener("submit", function (e) {
    e.preventDefault();
    updateUser();
  });

  document
    .getElementById("generate-password")
    .addEventListener("click", function () {
      const password = generateSecurePassword();
      document.getElementById("temp-password").value = password;
    });

  document
    .getElementById("toggle-temp-password")
    .addEventListener("click", function () {
      const input = document.getElementById("temp-password");
      const icon = this.querySelector("i");

      if (input.type === "password") {
        input.type = "text";
        icon.classList.remove("fa-eye");
        icon.classList.add("fa-eye-slash");
      } else {
        input.type = "password";
        icon.classList.remove("fa-eye-slash");
        icon.classList.add("fa-eye");
      }
    });

  document
    .getElementById("copy-password")
    .addEventListener("click", function () {
      const password = document.getElementById("temp-password").value;
      navigator.clipboard.writeText(password).then(() => {
        this.innerHTML = '<i class="fa-solid fa-check mr-1"></i>Copied!';
        setTimeout(() => {
          this.innerHTML = '<i class="fa-solid fa-copy mr-1"></i>Copy';
        }, 2000);
      });
    });
});

function populateEditForm(user) {
  document.getElementById("edit-id").value = user.id;
  document.getElementById("edit-first-name").value = user.first_name;
  document.getElementById("edit-last-name").value = user.last_name;
  document.getElementById("edit-email").value = user.email;
  document.getElementById("edit-phone").value = user.phone || "";
  document.getElementById("edit-role").value = user.role_id || "";
}

async function createUser() {
  const payload = {
    username: document.getElementById("invite-username").value,
    email: document.getElementById("invite-email").value,
    first_name: document.getElementById("invite-first-name").value,
    last_name: document.getElementById("invite-last-name").value,
    phone: document.getElementById("invite-phone").value,
    role_id: document.getElementById("invite-role").value,
    password: document.getElementById("temp-password").value,
  };

  try {
    const response = await fetch(`${BASE_URL}/api/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    // Check response status first
    if (response.ok && result.success) {
      // Success - hide modal and reload with success message
      hideCreateModal();
      showFlashMessage("User created successfully", "success", true);
      window.location.reload();
    } else {
      // Error - show message immediately WITHOUT reload
      const errorMessage = result.error || result.message || "Failed to create user. Please check the form and try again.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    // Network or parsing error - show immediately
    console.error("Error creating user:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

async function updateUser() {
  const userId = document.getElementById("edit-id").value;
  const payload = {
    first_name: document.getElementById("edit-first-name").value,
    last_name: document.getElementById("edit-last-name").value,
    email: document.getElementById("edit-email").value,
    phone: document.getElementById("edit-phone").value,
    role_id: document.getElementById("edit-role").value,
  };

  try {
    const response = await fetch(`${BASE_URL}/api/users/${userId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();

    if (response.ok && result.success) {
      hideEditModal();
      showFlashMessage("User updated successfully", "success", true);
      window.location.reload();
    } else {
      const errorMessage = result.error || result.message || "Failed to update user. Please try again.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    console.error("Error updating user:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

async function enableUser(userId) {
  try {
    const response = await fetch(`${BASE_URL}/api/users/${userId}/enable`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();

    if (response.ok && result.success) {
      hideConfirmModal();
      showFlashMessage("User enabled successfully", "success", true);
      window.location.reload();
    } else {
      hideConfirmModal();
      const errorMessage = result.error || result.message || "Failed to enable user.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    hideConfirmModal();
    console.error("Error enabling user:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

async function disableUser(userId) {
  try {
    const response = await fetch(`${BASE_URL}/api/users/${userId}/disable`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();

    if (response.ok && result.success) {
      hideConfirmModal();
      showFlashMessage("User disabled successfully", "success", true);
      window.location.reload();
    } else {
      hideConfirmModal();
      const errorMessage = result.error || result.message || "Failed to disable user.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    hideConfirmModal();
    console.error("Error disabling user:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

async function deleteUser(userId) {
  try {
    const response = await fetch(`${BASE_URL}/api/users/${userId}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const result = await response.json();

    if (response.ok && result.success) {
      hideConfirmModal();
      showFlashMessage("User deleted successfully", "success", true);
      window.location.reload();
    } else {
      hideConfirmModal();
      const errorMessage = result.error || result.message || "Failed to delete user.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (error) {
    hideConfirmModal();
    console.error("Error deleting user:", error);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

function generateSecurePassword() {
  const chars =
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*";
  let password = "";
  for (let i = 0; i < 12; i++) {
    password += chars.charAt(Math.floor(Math.random() * chars.length));
  }
  return password;
}

function applyFilters() {
  const form = document.getElementById("filters");
  form.submit();
}

function clearFilters() {
  window.location.href = "/api/v1/users";
}

document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search");
  if (searchInput) {
    searchInput.addEventListener("keypress", function (e) {
      if (e.key === "Enter") {
        e.preventDefault();
        applyFilters();
      }
    });
  }
});
