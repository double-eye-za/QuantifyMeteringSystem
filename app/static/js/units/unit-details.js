// Unit Details Page JavaScript
const UNIT_ID = window.UNIT_ID;

// =====================
// Owner Management
// =====================
function showAddOwnerModal() {
  document.getElementById('addOwnerModal').classList.remove('hidden');
}

function closeAddOwnerModal() {
  document.getElementById('addOwnerModal').classList.add('hidden');
  document.getElementById('addOwnerForm').reset();
}

async function submitAddOwner() {
  const personId = parseInt(document.getElementById('ownerPersonId').value);
  const percentage = parseFloat(document.getElementById('ownerPercentage').value);

  if (!personId) {
    showFlashMessage('Please select a person', 'error', true);
    return;
  }

  try {
    const response = await fetch(`/api/v1/api/units/${UNIT_ID}/owners`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        person_id: personId,
        ownership_percentage: percentage
      })
    });

    const data = await response.json();

    if (response.ok) {
      showFlashMessage('Owner added successfully', 'success', false);
      closeAddOwnerModal();
      window.location.reload();
    } else {
      showFlashMessage(data.message || 'Failed to add owner', 'error', true);
    }
  } catch (error) {
    console.error('Error:', error);
    showFlashMessage('Failed to add owner', 'error', true);
  }
}

async function removeOwner(personId) {
  if (!confirm('Are you sure you want to remove this owner?')) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/api/units/${UNIT_ID}/owners/${personId}`, {
      method: 'DELETE'
    });

    const data = await response.json();

    if (response.ok) {
      showFlashMessage('Owner removed successfully', 'success', false);
      window.location.reload();
    } else {
      showFlashMessage(data.message || 'Failed to remove owner', 'error', true);
    }
  } catch (error) {
    console.error('Error:', error);
    showFlashMessage('Failed to remove owner', 'error', true);
  }
}

// =====================
// Tenant Management
// =====================
function showAddTenantModal() {
  document.getElementById('addTenantModal').classList.remove('hidden');
}

function closeAddTenantModal() {
  document.getElementById('addTenantModal').classList.add('hidden');
  document.getElementById('addTenantForm').reset();
  // Reset payer container visibility (if payment_roles feature enabled)
  var payerContainer = document.getElementById('payerSelectContainer');
  if (payerContainer) payerContainer.classList.add('hidden');
}

function togglePayerSelect() {
  var roleSelect = document.getElementById('tenantPaymentRole');
  var payerContainer = document.getElementById('payerSelectContainer');
  if (roleSelect && payerContainer) {
    if (roleSelect.value === 'sponsored') {
      payerContainer.classList.remove('hidden');
    } else {
      payerContainer.classList.add('hidden');
    }
  }
}

async function submitAddTenant() {
  const personId = parseInt(document.getElementById('tenantPersonId').value);

  if (!personId) {
    showFlashMessage('Please select a person', 'error', true);
    return;
  }

  // Build payload
  var payload = {
    person_id: personId,
    status: 'active'
  };

  // Include payment_role if the fields exist (feature flag enabled)
  var roleSelect = document.getElementById('tenantPaymentRole');
  if (roleSelect) {
    payload.payment_role = roleSelect.value;

    if (roleSelect.value === 'sponsored') {
      var payerSelect = document.getElementById('tenantDelegatedPayerId');
      var payerId = payerSelect ? parseInt(payerSelect.value) : null;
      if (!payerId) {
        showFlashMessage('Please select a delegated payer for the sponsored tenant', 'error', true);
        return;
      }
      payload.delegated_payer_id = payerId;
    }
  }

  try {
    const response = await fetch(`/api/v1/api/units/${UNIT_ID}/tenants`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok) {
      showFlashMessage('Tenant added successfully', 'success', false);
      closeAddTenantModal();
      window.location.reload();
    } else {
      showFlashMessage(data.message || data.error || 'Failed to add tenant', 'error', true);
    }
  } catch (error) {
    console.error('Error:', error);
    showFlashMessage('Failed to add tenant', 'error', true);
  }
}

async function removeTenant(personId) {
  if (!confirm('Are you sure you want to remove this tenant?')) {
    return;
  }

  try {
    const response = await fetch(`/api/v1/api/units/${UNIT_ID}/tenants/${personId}`, {
      method: 'DELETE'
    });

    const data = await response.json();

    if (response.ok) {
      showFlashMessage('Tenant removed successfully', 'success', false);
      window.location.reload();
    } else {
      showFlashMessage(data.message || 'Failed to remove tenant', 'error', true);
    }
  } catch (error) {
    console.error('Error:', error);
    showFlashMessage('Failed to remove tenant', 'error', true);
  }
}

// =====================
// Edit Payment Role
// =====================
function showEditPaymentRoleModal(personId, personName, currentRole, currentPayerId) {
  document.getElementById('editRolePersonId').value = personId;
  document.getElementById('editRolePersonName').textContent = personName;

  var roleSelect = document.getElementById('editPaymentRole');
  roleSelect.value = currentRole;

  var payerSelect = document.getElementById('editDelegatedPayerId');
  if (currentPayerId && payerSelect) {
    payerSelect.value = currentPayerId;
  }

  toggleEditPayerSelect();
  document.getElementById('editPaymentRoleModal').classList.remove('hidden');
}

function closeEditPaymentRoleModal() {
  document.getElementById('editPaymentRoleModal').classList.add('hidden');
  document.getElementById('editPaymentRoleForm').reset();
  var container = document.getElementById('editPayerSelectContainer');
  if (container) container.classList.add('hidden');
}

function toggleEditPayerSelect() {
  var roleSelect = document.getElementById('editPaymentRole');
  var payerContainer = document.getElementById('editPayerSelectContainer');
  if (roleSelect && payerContainer) {
    if (roleSelect.value === 'sponsored') {
      payerContainer.classList.remove('hidden');
    } else {
      payerContainer.classList.add('hidden');
    }
  }
}

async function submitEditPaymentRole() {
  var personId = parseInt(document.getElementById('editRolePersonId').value);
  var roleSelect = document.getElementById('editPaymentRole');
  var paymentRole = roleSelect.value;

  var payload = { payment_role: paymentRole };

  if (paymentRole === 'sponsored') {
    var payerSelect = document.getElementById('editDelegatedPayerId');
    var payerId = payerSelect ? parseInt(payerSelect.value) : null;
    if (!payerId) {
      showFlashMessage('Please select a delegated payer for the sponsored tenant', 'error', true);
      return;
    }
    payload.delegated_payer_id = payerId;
  }

  try {
    const response = await fetch(`/api/v1/api/units/${UNIT_ID}/tenants/${personId}/payment-role`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (response.ok) {
      showFlashMessage('Payment role updated successfully', 'success', false);
      closeEditPaymentRoleModal();
      window.location.reload();
    } else {
      showFlashMessage(data.error || 'Failed to update payment role', 'error', true);
    }
  } catch (error) {
    console.error('Error:', error);
    showFlashMessage('Failed to update payment role', 'error', true);
  }
}

// =====================
// Top Up Modal Functions
// =====================
function openTopUpModal() {
  const modal = document.getElementById("topUpModal");
  if (modal) {
    modal.classList.remove("hidden");
  }
}

function closeTopUpModal() {
  const modal = document.getElementById("topUpModal");
  if (modal) {
    modal.classList.add("hidden");
    // Reset form
    document.getElementById("topUpForm").reset();
  }
}

async function handleTopUpSubmit(event) {
  event.preventDefault();

  const walletId = document.getElementById("walletId").value;
  const amount = parseFloat(document.getElementById("topUpAmount").value);
  const reference = document.getElementById("topUpReference").value;

  if (!walletId) {
    showFlashMessage("Error: Wallet ID not found", "error", true);
    return;
  }

  if (!amount || amount <= 0) {
    showFlashMessage("Please enter a valid amount", "error", true);
    return;
  }

  const submitBtn = document.getElementById("submitTopUpBtn");
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Processing...';

  try {
    const response = await fetch(`/api/v1/wallets/${walletId}/topup`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        amount: amount,
        payment_method: "manual_admin",
        reference: reference || "Admin wallet top-up",
        metadata: {
          added_by: "admin",
          source: "unit_details_page"
        }
      }),
    });

    const result = await response.json();

    if (response.ok && result.data) {
      showFlashMessage(`Top-up completed. Transaction: ${result.data.transaction_number}`, "success", false);
      closeTopUpModal();
      // Reload page to show updated balance
      window.location.reload();
    } else {
      showFlashMessage(result.error || "Failed to process top-up", "error", true);
    }
  } catch (error) {
    console.error("Top-up error:", error);
    showFlashMessage("Error: Failed to process top-up. Please try again.", "error", true);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

// =====================
// Initialize on page load
// =====================
document.addEventListener("DOMContentLoaded", function () {
  // Top Up Modal Event Listeners
  const topUpBtn = document.getElementById("topUpBtn");
  const topUpBtnWarning = document.getElementById("topUpBtnWarning");
  const closeTopUpModalBtn = document.getElementById("closeTopUpModal");
  const cancelTopUpBtn = document.getElementById("cancelTopUpBtn");
  const topUpForm = document.getElementById("topUpForm");

  if (topUpBtn) {
    topUpBtn.addEventListener("click", openTopUpModal);
  }

  if (topUpBtnWarning) {
    topUpBtnWarning.addEventListener("click", openTopUpModal);
  }

  if (closeTopUpModalBtn) {
    closeTopUpModalBtn.addEventListener("click", closeTopUpModal);
  }

  if (cancelTopUpBtn) {
    cancelTopUpBtn.addEventListener("click", closeTopUpModal);
  }

  if (topUpForm) {
    topUpForm.addEventListener("submit", handleTopUpSubmit);
  }

  // Close modal when clicking outside
  const modal = document.getElementById("topUpModal");
  if (modal) {
    modal.addEventListener("click", function (event) {
      if (event.target === modal) {
        closeTopUpModal();
      }
    });
  }
});
