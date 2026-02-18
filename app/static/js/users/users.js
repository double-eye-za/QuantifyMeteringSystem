const BASE_URL = "/api/v1";

// Global table filter instance
let usersTableFilter = null;

// Render a single user row for the table
function renderUserRow(user) {
  const permissions = window.USER_PERMISSIONS || {};
  const userJson = JSON.stringify(user).replace(/'/g, "&#39;").replace(/"/g, "&quot;");

  let actionsHtml = '<div class="flex gap-2">';

  // Edit button
  if (permissions.canEdit) {
    actionsHtml += `
      <button data-user="${userJson}" class="inline-flex items-center px-2 py-1 border border-gray-300 dark:border-gray-600 rounded text-xs hover:bg-gray-100 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 transition-colors duration-200" title="Edit user">
        <i class="fa-solid fa-pen-to-square mr-1"></i>
        Edit
      </button>
    `;
  }

  // Enable/Disable button
  if (user.is_active && permissions.canDisable) {
    actionsHtml += `
      <button data-user-id="${user.id}" data-user-data="${userJson}" class="inline-flex items-center px-2 py-1 border border-red-300 dark:border-red-600 rounded text-xs hover:bg-red-50 dark:hover:bg-red-900/20 text-red-700 dark:text-red-400 transition-colors duration-200" title="Disable user">
        <i class="fa-solid fa-ban mr-1"></i>
        Disable
      </button>
    `;
  } else if (!user.is_active && permissions.canEnable) {
    actionsHtml += `
      <button data-user-id="${user.id}" data-user-data="${userJson}" class="inline-flex items-center px-2 py-1 border border-green-300 dark:border-green-600 rounded text-xs hover:bg-green-50 dark:hover:bg-green-900/20 text-green-700 dark:text-green-400 transition-colors duration-200" title="Enable user">
        <i class="fa-solid fa-check mr-1"></i>
        Enable
      </button>
    `;
  }

  // Delete button
  if (permissions.canDelete) {
    actionsHtml += `
      <button data-delete-user-id="${user.id}" data-delete-user-data="${userJson}" class="inline-flex items-center px-2 py-1 border border-red-300 dark:border-red-600 rounded text-xs hover:bg-red-100 dark:hover:bg-red-900/30 text-red-700 dark:text-red-400 transition-colors duration-200" title="Delete user permanently">
        <i class="fa-solid fa-trash mr-1"></i>
        Delete
      </button>
    `;
  }

  actionsHtml += '</div>';

  const statusClass = user.is_active ? 'bg-green-600' : 'bg-gray-500';
  const statusText = user.is_active ? 'Active' : 'Disabled';

  return `
    <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors">
      <td class="px-4 py-3 text-gray-900 dark:text-gray-100">${user.full_name || ''}</td>
      <td class="px-4 py-3 text-gray-900 dark:text-gray-100">${user.email || ''}</td>
      <td class="px-4 py-3 text-gray-900 dark:text-gray-100">${user.phone || '-'}</td>
      <td class="px-4 py-3 text-gray-900 dark:text-gray-100">${user.role_name || '-'}</td>
      <td class="px-4 py-3">
        <span class="px-2 py-1 rounded text-white text-xs ${statusClass}">
          ${statusText}
        </span>
      </td>
      <td class="px-4 py-3 text-gray-900 dark:text-gray-100">${user.created_at || ''}</td>
      <td class="px-4 py-3">${actionsHtml}</td>
    </tr>
  `;
}

// Attach event listeners to dynamically rendered action buttons
function attachUserRowEventListeners() {
  // Edit buttons
  document.querySelectorAll("[data-user]").forEach((button) => {
    button.addEventListener("click", function () {
      const user = JSON.parse(this.dataset.user);
      populateEditForm(user);
      showEditModal();
    });
  });

  // Enable/Disable buttons
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

  // Delete buttons
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
}

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
  // Initialize TableFilter for AJAX-based filtering
  usersTableFilter = new TableFilter({
    tableBodyId: 'usersTableBody',
    apiEndpoint: `${BASE_URL}/api/users`,
    filters: {
      search: { element: '#searchInput', param: 'search', debounce: true },
      status: { element: '#statusFilter', param: 'status' },
      role: { element: '#roleFilter', param: 'role_id' }
    },
    renderRow: renderUserRow,
    colSpan: 7,
    onError: (error) => showFlashMessage(error, 'error', false),
    onAfterFetch: () => {
      // Re-attach event listeners after table is re-rendered
      attachUserRowEventListeners();
    }
  });

  // Override attachRowEventListeners in the filter instance
  usersTableFilter.attachRowEventListeners = attachUserRowEventListeners;

  // Clear filters button
  const clearFiltersBtn = document.getElementById("clearFiltersBtn");
  if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener("click", function () {
      usersTableFilter.clearFilters();
    });
  }

  // Modal buttons
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

  // Attach initial event listeners for server-rendered rows
  attachUserRowEventListeners();

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
      // Success - hide modal and refresh table
      hideCreateModal();
      showFlashMessage("User created successfully", "success", false);
      refreshUsersTable();
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
      showFlashMessage("User updated successfully", "success", false);
      refreshUsersTable();
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
      showFlashMessage("User enabled successfully", "success", false);
      refreshUsersTable();
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
      showFlashMessage("User disabled successfully", "success", false);
      refreshUsersTable();
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
      showFlashMessage("User deleted successfully", "success", false);
      refreshUsersTable();
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

// Refresh the table after CRUD operations (use AJAX refresh instead of full page reload)
function refreshUsersTable() {
  if (usersTableFilter) {
    usersTableFilter.refresh();
  } else {
    window.location.reload();
  }
}
