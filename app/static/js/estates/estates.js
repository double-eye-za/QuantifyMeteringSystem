const BASE_URL = "/api/v1";

function showAddEstateModal() {
  document.getElementById("addEstateModal").classList.remove("hidden");
}

function closeAddEstateModal() {
  document.getElementById("addEstateModal").classList.add("hidden");
}

function confirmDeleteEstate(buttonEl) {
  const card = buttonEl.closest("[data-estate]");
  const estate = JSON.parse(card.getAttribute("data-estate"));
  const modal = document.getElementById("deleteEstateModal");
  modal.setAttribute("data-estate-id", estate.id);
  modal.classList.remove("hidden");
  modal.classList.add("flex");
}

function hideDeleteEstate() {
  const modal = document.getElementById("deleteEstateModal");
  modal.classList.add("hidden");
  modal.classList.remove("flex");
}

async function performDeleteEstate() {
  const modal = document.getElementById("deleteEstateModal");
  const estateId = modal.getAttribute("data-estate-id");
  if (!estateId) return;

  try {
    const res = await fetch(`${BASE_URL}/estates/${estateId}`, {
      method: "DELETE",
    });

    const result = await res.json();

    if (res.ok) {
      // Success - hide modal and reload with success message
      hideDeleteEstate();
      showFlashMessage("Estate deleted successfully", "success", true);
      window.location.reload();
    } else {
      // Error - show message immediately WITHOUT reload
      hideDeleteEstate();
      const errorMessage = result.error || result.message || "Failed to delete estate. It may be associated with units or other data.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (e) {
    // Network or parsing error
    hideDeleteEstate();
    console.error("Error deleting estate:", e);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

async function saveNewEstate(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const d = Object.fromEntries(formData);

  try {
    const res = await fetch(`${BASE_URL}/estates`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: d.estate_name,
        code: d.estate_code,
        address: d.address,
        city: d.city,
        postal_code: d.postal_code,
        contact_name: d.manager_name,
        contact_phone: d.contact_number,
        contact_email: d.manager_email,
        total_units: Number(d.total_units || 0),
        electricity_markup_percentage: Number(d.electricity_markup || 0),
        water_markup_percentage: Number(d.water_markup || 0),
        solar_free_allocation_kwh: Number(d.solar_free_kwh || 0),
        electricity_rate_table_id: d.electricity_rate_table || null,
        water_rate_table_id: d.water_rate_table || null,
      }),
    });

    const result = await res.json();

    if (res.ok && (result.success || result.data)) {
      // Success - close modal and reload with success message
      closeAddEstateModal();
      showFlashMessage("Estate created successfully", "success", true);
      window.location.reload();
    } else {
      // Error - show message immediately WITHOUT reload
      const errorMessage = result.error || result.message || "Failed to create estate. Please check the form and try again.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (e) {
    // Network or parsing error
    console.error("Error creating estate:", e);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

function viewEstateDetails(buttonEl) {
  const card = buttonEl.closest("[data-estate]");
  if (!card) return;
  const estate = JSON.parse(card.getAttribute("data-estate"));
  window.location.href = `${BASE_URL}/estates/${estate.id}/details`;
}

function editEstate(buttonEl) {
  const card = buttonEl.closest("[data-estate]");
  if (!card) {
    showEditEstateModal();
    return;
  }
  const estate = JSON.parse(card.getAttribute("data-estate"));
  // Populate edit form
  document.getElementById("edit_estate_name").value = estate.name || "";
  document.getElementById("edit_address").value = estate.address || "";
  document.getElementById("edit_city").value = estate.city || "";
  document.getElementById("edit_postal_code").value = estate.postal_code || "";
  document.getElementById("edit_total_units").value = estate.total_units || 0;
  document.getElementById("edit_estate_code").value = estate.code || "";
  document.getElementById("edit_manager_name").value =
    estate.contact_name || "";
  document.getElementById("edit_contact_number").value =
    estate.contact_phone || "";
  document.getElementById("edit_manager_email").value =
    estate.contact_email || "";
  // Billing/rates
  const electricityMarkUp = document.getElementById("edit_electricity_markup_field");
  if (electricityMarkUp)
    electricityMarkUp.value = estate.electricity_markup_percentage ?? 0;
  const waterMarkUp = document.getElementById("edit_water_markup_field");
  if (waterMarkUp) waterMarkUp.value = estate.water_markup_percentage ?? 0;
  const solarFree = document.getElementById("edit_solar_free_kwh_field");
  if (solarFree) solarFree.value = estate.solar_free_allocation_kwh ?? 0;
  const electricityRateTable = document.getElementById(
    "edit_electricity_rate_table"
  );
  if (electricityRateTable && estate.electricity_rate_table_id)
    electricityRateTable.value = estate.electricity_rate_table_id;
  const waterRateTable = document.getElementById("edit_water_rate_table");
  if (waterRateTable && estate.water_rate_table_id)
    waterRateTable.value = estate.water_rate_table_id;
  // Store id on form for submit
  document
    .getElementById("editEstateModal")
    .setAttribute("data-estate-id", estate.id);
  showEditEstateModal();
}

function showEditEstateModal() {
  document.getElementById("editEstateModal").classList.remove("hidden");
}

function closeEditEstateModal() {
  document.getElementById("editEstateModal").classList.add("hidden");
}

async function saveEditedEstate(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const updatedData = Object.fromEntries(formData);
  const estateId = document
    .getElementById("editEstateModal")
    .getAttribute("data-estate-id");

  try {
    const res = await fetch(`${BASE_URL}/estates/${estateId}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: updatedData.estate_name,
        code: updatedData.estate_code,
        address: updatedData.address,
        city: updatedData.city,
        postal_code: updatedData.postal_code,
        contact_name: updatedData.manager_name,
        contact_phone: updatedData.contact_number,
        contact_email: updatedData.manager_email,
        total_units: Number(updatedData.total_units || 0),
        electricity_markup_percentage: Number(
          updatedData.electricity_markup || 0
        ),
        water_markup_percentage: Number(updatedData.water_markup || 0),
        solar_free_allocation_kwh: Number(updatedData.solar_free_kwh || 0),
        electricity_rate_table_id: updatedData.electricity_rate_table || null,
        water_rate_table_id: updatedData.water_rate_table || null,
      }),
    });

    const result = await res.json();

    if (res.ok && (result.success || result.data)) {
      // Success - close modal and reload with success message
      closeEditEstateModal();
      showFlashMessage("Estate updated successfully", "success", true);
      window.location.reload();
    } else {
      // Error - show message immediately WITHOUT reload
      const errorMessage = result.error || result.message || "Failed to update estate. Please try again.";
      showFlashMessage(errorMessage, "error", false);
    }
  } catch (e) {
    // Network or parsing error
    console.error("Error updating estate:", e);
    showFlashMessage("An unexpected error occurred. Please try again.", "error", false);
  }
}

// Close modal on escape key
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    closeAddEstateModal();
    closeEditEstateModal();
  }
});
