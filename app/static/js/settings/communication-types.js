// Communication Type Management JavaScript

function showCreateCommunicationType() {
  document.getElementById("modalTitle").textContent = "Add Communication Type";
  document.getElementById("communicationTypeForm").reset();
  document.getElementById("communicationTypeId").value = "";
  document.getElementById("communicationTypeModal").classList.remove("hidden");
}

function hideCommunicationTypeModal() {
  document.getElementById("communicationTypeModal").classList.add("hidden");
}

async function editCommunicationType(id) {
  try {
    const response = await fetch(`/api/v1/api/communication-types/${id}`);
    if (!response.ok) throw new Error("Failed to fetch communication type");

    const commType = await response.json();

    document.getElementById("modalTitle").textContent = "Edit Communication Type";
    document.getElementById("communicationTypeId").value = commType.id;
    document.getElementById("code").value = commType.code;
    document.getElementById("name").value = commType.name;
    document.getElementById("description").value = commType.description || "";
    document.getElementById("requires_device_eui").checked = commType.requires_device_eui;
    document.getElementById("requires_gateway").checked = commType.requires_gateway;
    document.getElementById("supports_remote_control").checked = commType.supports_remote_control;
    document.getElementById("is_active").checked = commType.is_active;

    document.getElementById("communicationTypeModal").classList.remove("hidden");
  } catch (error) {
    alert("Error loading communication type: " + error.message);
  }
}

async function deactivateCommunicationType(id, name) {
  if (!confirm(`Are you sure you want to deactivate "${name}"?`)) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/api/communication-types/${id}`, {
      method: "DELETE",
    });

    if (!response.ok) throw new Error("Failed to deactivate communication type");

    location.reload();
  } catch (error) {
    alert("Error deactivating communication type: " + error.message);
  }
}

// Form submission
document.getElementById("communicationTypeForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const formData = new FormData(e.target);
  const id = formData.get("id");

  const payload = {
    code: formData.get("code"),
    name: formData.get("name"),
    description: formData.get("description") || null,
    requires_device_eui: formData.get("requires_device_eui") === "on",
    requires_gateway: formData.get("requires_gateway") === "on",
    supports_remote_control: formData.get("supports_remote_control") === "on",
    is_active: formData.get("is_active") === "on",
  };

  try {
    let response;
    if (id) {
      // Update existing
      response = await fetch(`/api/v1/api/communication-types/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    } else {
      // Create new
      response = await fetch("/api/v1/api/communication-types", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
    }

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || "Failed to save communication type");
    }

    location.reload();
  } catch (error) {
    alert("Error saving communication type: " + error.message);
  }
});

// Close modal on Escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    hideCommunicationTypeModal();
  }
});
