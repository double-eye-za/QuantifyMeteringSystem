const BASE_URL = "/api/v1/settings";

document.addEventListener("DOMContentLoaded", function () {
  loadSettings();
});

// Load settings from db
async function loadSettings() {
  try {
    const response = await fetch("/api/v1/api/settings");
    const result = await response.json();

    if (response.ok) {
      const settings = result.settings;

      // General settings
      document.getElementById("org_name").value = settings.org_name || "";
      document.getElementById("contact_email").value =
        settings.contact_email || "";
      document.getElementById("default_language").value =
        settings.default_language || "English";
      document.getElementById("timezone").value =
        settings.timezone || "Africa/Johannesburg (GMT+2)";
      document.getElementById("date_format").value =
        settings.date_format || "YYYY-MM-DD";
      document.getElementById("session_timeout").value =
        settings.session_timeout || 15;

      // Security settings
      document.getElementById("min_password_length").value =
        settings.min_password_length || 8;
      document.getElementById("require_uppercase").checked =
        settings.require_uppercase || false;
      document.getElementById("require_numbers").checked =
        settings.require_numbers || false;
      document.getElementById("require_special_chars").checked =
        settings.require_special_chars || false;
      document.getElementById("enable_2fa").checked =
        settings.enable_2fa || false;
      document.getElementById("account_lockout").checked =
        settings.account_lockout || false;
      document.getElementById("allowed_ips").value = settings.allowed_ips || "";

      // Notification settings
      document.getElementById("sms_provider").value =
        settings.sms_provider || "twilio";
      document.getElementById("emergency_contact").value =
        settings.emergency_contact || "";
      document.getElementById("system_alerts").checked =
        settings.system_alerts || false;
      document.getElementById("security_alerts").checked =
        settings.security_alerts || false;
      document.getElementById("system_updates").checked =
        settings.system_updates || false;
    } else {
      console.error("Failed to load settings:", result.error);
    }
  } catch (error) {
    console.error("Error loading settings:", error);
  }
}

async function saveGeneralSettings() {
  try {
    const payload = {
      org_name: document.getElementById("org_name").value,
      contact_email: document.getElementById("contact_email").value,
      default_language: document.getElementById("default_language").value,
      timezone: document.getElementById("timezone").value,
      date_format: document.getElementById("date_format").value,
      session_timeout: parseInt(
        document.getElementById("session_timeout").value
      ),
    };

    const response = await fetch(`${BASE_URL}/general`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (response.ok) {
      showFlashMessage("General settings saved successfully", "success");
    } else {
      showFlashMessage(result.error || "Failed to save settings", "error");
    }
  } catch (error) {
    showFlashMessage("Network error while saving settings", "error");
  }
}

async function saveSecuritySettings() {
  try {
    const payload = {
      min_password_length: parseInt(
        document.getElementById("min_password_length").value
      ),
      require_uppercase: document.getElementById("require_uppercase").checked,
      require_numbers: document.getElementById("require_numbers").checked,
      require_special_chars: document.getElementById("require_special_chars")
        .checked,
      enable_2fa: document.getElementById("enable_2fa").checked,
      account_lockout: document.getElementById("account_lockout").checked,
      allowed_ips: document.getElementById("allowed_ips").value,
    };

    const response = await fetch(`${BASE_URL}/security`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (response.ok) {
      showFlashMessage("Security settings saved successfully", "success");
    } else {
      showFlashMessage(result.error || "Failed to save settings", "error");
    }
  } catch (error) {
    showFlashMessage("Network error while saving settings", "error");
  }
}

async function saveNotificationSettings() {
  try {
    const payload = {
      sms_provider: document.getElementById("sms_provider").value,
      emergency_contact: document.getElementById("emergency_contact").value,
      system_alerts: document.getElementById("system_alerts").checked,
      security_alerts: document.getElementById("security_alerts").checked,
      system_updates: document.getElementById("system_updates").checked,
    };

    const response = await fetch(`${BASE_URL}/notifications`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (response.ok) {
      showFlashMessage("Notification settings saved successfully", "success");
    } else {
      showFlashMessage(result.error || "Failed to save settings", "error");
    }
  } catch (error) {
    showFlashMessage("Network error while saving settings", "error");
  }
}

function showSettingSection(sectionName) {
  // Hide all sections
  document.querySelectorAll(".setting-section").forEach((section) => {
    section.classList.add("hidden");
  });

  // Remove active state from all buttons
  document.querySelectorAll(".setting-btn").forEach((btn) => {
    btn.classList.remove("bg-primary", "text-white");
    btn.classList.add(
      "bg-gray-100",
      "dark:bg-gray-700",
      "text-gray-700",
      "dark:text-gray-300"
    );
  });

  // Show selected section
  document.getElementById(`${sectionName}-section`).classList.remove("hidden");

  // Add active state to selected button
  const activeBtn = document.querySelector(`[data-section="${sectionName}"]`);
  activeBtn.classList.add("bg-primary", "text-white");
  activeBtn.classList.remove(
    "bg-gray-100",
    "dark:bg-gray-700",
    "text-gray-700",
    "dark:text-gray-300"
  );

  // Load data for dynamic tabs
  if (sectionName === "feature-flags") {
    loadFeatureFlags();
  } else if (sectionName === "credit-control") {
    loadCreditControlStatus();
  }
}

// ── Feature Flags ───────────────────────────────────────────────────────

async function loadFeatureFlags() {
  try {
    const response = await fetch("/api/v1/api/feature-flags");
    const result = await response.json();

    if (!response.ok) {
      console.error("Failed to load feature flags:", result.error);
      return;
    }

    const container = document.getElementById("feature-flags-container");
    if (result.flags.length === 0) {
      container.innerHTML =
        '<p class="text-sm text-gray-500 dark:text-gray-400">No feature flags registered.</p>';
      return;
    }

    let html = '<div class="space-y-4">';
    for (const flag of result.flags) {
      const displayName = flag.name
        .replace(/_/g, " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());

      html += `
        <div class="flex items-center justify-between">
          <div>
            <p class="text-sm font-medium text-gray-900 dark:text-white">
              ${displayName}
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-400">
              ${flag.description}
            </p>
            <p class="text-xs mt-1 ${
              flag.enabled
                ? "text-green-600 dark:text-green-400"
                : "text-gray-400 dark:text-gray-500"
            }">
              ${flag.enabled ? "Currently: Enabled" : "Currently: Disabled"}
            </p>
          </div>
          <label class="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              id="flag_${flag.name}"
              class="sr-only peer"
              ${flag.enabled ? "checked" : ""}
            />
            <div
              class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-primary"
            ></div>
          </label>
        </div>`;
    }
    html += "</div>";

    // Warning banner
    html += `
      <div class="mt-6 rounded-lg bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 p-4">
        <div class="flex">
          <i class="fas fa-exclamation-triangle text-yellow-500 mt-0.5 mr-3"></i>
          <div>
            <p class="text-sm font-medium text-yellow-800 dark:text-yellow-300">Important</p>
            <p class="text-xs text-yellow-700 dark:text-yellow-400 mt-1">
              Feature flags take effect immediately. The automated credit control tasks are
              currently disabled in the scheduler. Enabling the credit control flag here only
              affects manual task execution, not automatic scheduling.
            </p>
          </div>
        </div>
      </div>`;

    container.innerHTML = html;
  } catch (error) {
    console.error("Error loading feature flags:", error);
  }
}

async function saveFeatureFlags() {
  try {
    // Collect all flag states from checkboxes
    const flags = {};
    document
      .querySelectorAll('[id^="flag_"]')
      .forEach((cb) => {
        const name = cb.id.replace("flag_", "");
        flags[name] = cb.checked;
      });

    const response = await fetch(`${BASE_URL}/feature-flags`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ flags }),
    });

    const result = await response.json();
    if (response.ok) {
      showFlashMessage("Feature flags saved successfully", "success");
      loadFeatureFlags(); // Refresh to show updated status text
    } else {
      showFlashMessage(result.error || "Failed to save feature flags", "error");
    }
  } catch (error) {
    showFlashMessage("Network error while saving feature flags", "error");
  }
}

// ── Credit Control Status ───────────────────────────────────────────────

async function loadCreditControlStatus() {
  try {
    const response = await fetch("/api/v1/api/credit-control/status");
    const result = await response.json();

    if (!response.ok) {
      console.error("Failed to load credit control status:", result.error);
      return;
    }

    // Status banner
    const banner = document.getElementById("cc-status-banner");
    if (result.credit_control_active) {
      banner.className =
        "rounded-lg p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800";
      banner.innerHTML = `
        <div class="flex items-center">
          <i class="fas fa-check-circle text-green-500 text-lg mr-3"></i>
          <div>
            <p class="text-sm font-medium text-green-800 dark:text-green-300">Credit Control is Enabled</p>
            <p class="text-xs text-green-700 dark:text-green-400 mt-1">
              Automated disconnect/reconnect tasks will execute when scheduled.
              Note: The beat schedule entries must also be uncommented in celery_app.py.
            </p>
          </div>
        </div>`;
    } else {
      banner.className =
        "rounded-lg p-4 bg-gray-50 dark:bg-gray-700 border border-gray-200 dark:border-gray-600";
      banner.innerHTML = `
        <div class="flex items-center">
          <i class="fas fa-info-circle text-gray-400 text-lg mr-3"></i>
          <div>
            <p class="text-sm font-medium text-gray-700 dark:text-gray-300">Credit Control is Disabled</p>
            <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">
              Tasks run in dry-run mode. No relay commands will be sent.
              Enable via Feature Flags tab when ready.
            </p>
          </div>
        </div>`;
    }

    // Summary cards
    document.getElementById("cc-zero-balance").textContent =
      result.total_zero_balance;
    document.getElementById("cc-suspended").textContent =
      result.total_suspended;
    document.getElementById("cc-eligible").textContent =
      result.total_eligible_reconnect;

    // Meter table
    const tbody = document.getElementById("cc-meter-table");
    if (result.meters.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" class="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
            <i class="fas fa-check-circle text-green-500 mr-2"></i>
            No meters with zero or negative balance
          </td>
        </tr>`;
      return;
    }

    let rows = "";
    for (const m of result.meters) {
      // Unified wallet: color based on main balance
      const balanceClass =
        m.balance < 0
          ? "text-red-600 dark:text-red-400"
          : "text-orange-600 dark:text-orange-400";

      const statusBadge = m.is_suspended
        ? '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">Suspended</span>'
        : '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">Active</span>';

      rows += `
        <tr class="hover:bg-gray-50 dark:hover:bg-gray-700/50">
          <td class="px-4 py-3 text-sm text-gray-900 dark:text-white">${m.unit_number}</td>
          <td class="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">${m.meter_serial}</td>
          <td class="px-4 py-3 text-xs font-mono text-gray-500 dark:text-gray-400">${m.device_eui}</td>
          <td class="px-4 py-3 text-sm text-right ${balanceClass}">R${m.balance.toFixed(2)}</td>
          <td class="px-4 py-3 text-sm text-right text-gray-600 dark:text-gray-300">R${m.electricity_spent.toFixed(2)}</td>
          <td class="px-4 py-3 text-center">${statusBadge}</td>
        </tr>`;
    }
    tbody.innerHTML = rows;
  } catch (error) {
    console.error("Error loading credit control status:", error);
  }
}
