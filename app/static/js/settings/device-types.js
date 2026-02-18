// Device Type Management JavaScript

function showCreateDeviceType() {
  document.getElementById("modalTitle").textContent = "Add Device Type";
  document.getElementById("deviceTypeForm").reset();
  document.getElementById("deviceTypeId").value = "";
  document.getElementById("deviceTypeModal").classList.remove("hidden");
}

function hideDeviceTypeModal() {
  document.getElementById("deviceTypeModal").classList.add("hidden");
}

async function editDeviceType(id) {
  try {
    const response = await fetch(`/api/v1/api/device-types/${id}`);
    if (!response.ok) throw new Error("Failed to fetch device type");

    const deviceType = await response.json();

    document.getElementById("modalTitle").textContent = "Edit Device Type";
    document.getElementById("deviceTypeId").value = deviceType.id;
    document.getElementById("code").value = deviceType.code;
    document.getElementById("name").value = deviceType.name;
    document.getElementById("manufacturer").value = deviceType.manufacturer || "";
    document.getElementById("default_model").value = deviceType.default_model || "";
    document.getElementById("description").value = deviceType.description || "";
    document.getElementById("supports_temperature").checked = deviceType.supports_temperature;
    document.getElementById("supports_pulse").checked = deviceType.supports_pulse;
    document.getElementById("supports_modbus").checked = deviceType.supports_modbus;
    document.getElementById("is_active").checked = deviceType.is_active;

    document.getElementById("deviceTypeModal").classList.remove("hidden");
  } catch (error) {
    alert("Error loading device type: " + error.message);
  }
}

async function deactivateDeviceType(id, name) {
  if (!confirm(`Are you sure you want to deactivate "${name}"?`)) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/api/device-types/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) throw new Error("Failed to deactivate device type");

    location.reload();
  } catch (error) {
    alert("Error deactivating device type: " + error.message);
  }
}

// Form submission
document.getElementById("deviceTypeForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(e.target);
  const id = formData.get("id");

  const payload = {
    code: formData.get("code"),
    name: formData.get("name"),
    manufacturer: formData.get("manufacturer") || null,
    default_model: formData.get("default_model") || null,
    description: formData.get("description") || null,
    supports_temperature: formData.get("supports_temperature") === "on",
    supports_pulse: formData.get("supports_pulse") === "on",
    supports_modbus: formData.get("supports_modbus") === "on",
    is_active: formData.get("is_active") === "on",
  };

  try {
    let response;
    if (id) {
      // Update existing
      response = await fetch(`/api/v1/api/device-types/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } else {
      // Create new
      response = await fetch("/api/v1/api/device-types", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Failed to save device type");
    }

    location.reload();
  } catch (error) {
    alert("Error saving device type: " + error.message);
  }
});

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    hideDeviceTypeModal();
  }
});
