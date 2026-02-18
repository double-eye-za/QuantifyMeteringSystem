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
}
