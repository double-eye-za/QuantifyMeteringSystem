/**
 * Meter Photos Management
 *
 * Handles photo upload (drag-and-drop + file picker), display, and deletion
 * inside the Edit Meter modal.  Photo CRUD is decoupled from the meter JSON
 * payload — photos use separate multipart/form-data API endpoints.
 */

const PHOTOS_BASE_URL = "/api/v1/meters";

// ─── Load existing photos when edit modal opens ───────────────────────

async function loadMeterPhotos(meterId) {
  const container = document.getElementById("editMeterPhotos");
  if (!container) return;
  container.innerHTML =
    '<p class="text-xs text-gray-400 col-span-4"><i class="fas fa-spinner fa-spin mr-1"></i>Loading photos…</p>';

  try {
    const resp = await fetch(`${PHOTOS_BASE_URL}/${meterId}/photos`);
    if (!resp.ok) throw new Error("Failed to load photos");
    const result = await resp.json();
    const photos = result.data || [];

    if (photos.length === 0) {
      container.innerHTML =
        '<p class="text-xs text-gray-400 col-span-4">No photos yet</p>';
      return;
    }

    container.innerHTML = photos
      .map(
        (photo) => `
      <div class="relative group rounded-lg overflow-hidden border border-gray-200 dark:border-gray-600"
           data-photo-id="${photo.id}">
        <img src="${photo.url}" alt="${photo.original_filename}"
             class="w-full h-20 object-cover" loading="lazy" />
        <button type="button"
                onclick="deleteMeterPhoto(${meterId}, ${photo.id}, this)"
                class="absolute top-1 right-1 bg-red-600 text-white rounded-full w-5 h-5 text-xs
                       flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                title="Delete photo">
          <i class="fas fa-times"></i>
        </button>
        <div class="absolute bottom-0 left-0 right-0 bg-black/50 px-1 py-0.5">
          <span class="text-white text-[10px] truncate block">${photo.original_filename}</span>
        </div>
      </div>
    `
      )
      .join("");
  } catch (e) {
    container.innerHTML =
      '<p class="text-xs text-red-400 col-span-4">Error loading photos</p>';
    console.error("Error loading meter photos:", e);
  }
}

// ─── Delete a photo ───────────────────────────────────────────────────

async function deleteMeterPhoto(meterId, photoId, btn) {
  if (!confirm("Delete this photo?")) return;
  try {
    const resp = await fetch(
      `${PHOTOS_BASE_URL}/${meterId}/photos/${photoId}`,
      { method: "DELETE" }
    );
    if (resp.ok) {
      const card = btn.closest("[data-photo-id]");
      if (card) card.remove();
      // Check if container is now empty
      const container = document.getElementById("editMeterPhotos");
      if (container && container.children.length === 0) {
        container.innerHTML =
          '<p class="text-xs text-gray-400 col-span-4">No photos yet</p>';
      }
      if (typeof showFlashMessage === "function") {
        showFlashMessage("Photo deleted", "success", false);
      }
    } else {
      const data = await resp.json();
      if (typeof showFlashMessage === "function") {
        showFlashMessage(
          data.error || "Failed to delete photo",
          "error",
          false
        );
      }
    }
  } catch (e) {
    console.error("Error deleting photo:", e);
    if (typeof showFlashMessage === "function") {
      showFlashMessage("Error deleting photo", "error", false);
    }
  }
}

// ─── Upload photos ────────────────────────────────────────────────────

async function uploadMeterPhotos(meterId, files) {
  if (!files || files.length === 0) return;

  const formData = new FormData();
  for (const file of files) {
    formData.append("photos", file);
  }

  const previewContainer = document.getElementById("photoUploadPreviews");
  if (previewContainer) {
    previewContainer.innerHTML =
      '<p class="text-xs text-blue-500 col-span-4"><i class="fas fa-spinner fa-spin mr-1"></i>Uploading…</p>';
  }

  try {
    const resp = await fetch(`${PHOTOS_BASE_URL}/${meterId}/photos`, {
      method: "POST",
      body: formData,
      // NOTE: Do NOT set Content-Type header — browser sets it with boundary
    });
    const result = await resp.json();

    if (result.data && result.data.length > 0) {
      if (typeof showFlashMessage === "function") {
        showFlashMessage(
          result.message || "Photos uploaded",
          "success",
          false
        );
      }
      // Reload photos in the modal
      loadMeterPhotos(meterId);
    }

    if (result.errors && result.errors.length > 0) {
      if (typeof showFlashMessage === "function") {
        showFlashMessage(result.errors.join("; "), "error", false);
      }
    }
  } catch (e) {
    console.error("Error uploading photos:", e);
    if (typeof showFlashMessage === "function") {
      showFlashMessage("Error uploading photos", "error", false);
    }
  } finally {
    if (previewContainer) previewContainer.innerHTML = "";
  }
}

// ─── Setup drag-and-drop and file input ───────────────────────────────

function setupPhotoUpload() {
  const dropZone = document.getElementById("photoDropZone");
  const fileInput = document.getElementById("photoFileInput");

  if (!dropZone || !fileInput) return;

  // Click to open file picker
  dropZone.addEventListener("click", () => fileInput.click());

  // File input change
  fileInput.addEventListener("change", () => {
    const meterId =
      document.getElementById("editMeterForm")?.elements.id?.value;
    if (meterId && fileInput.files.length > 0) {
      uploadMeterPhotos(meterId, fileInput.files);
      fileInput.value = ""; // reset for next upload
    }
  });

  // Drag events
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("border-primary", "bg-blue-50", "dark:bg-blue-900/20");
  });

  dropZone.addEventListener("dragleave", (e) => {
    e.preventDefault();
    dropZone.classList.remove(
      "border-primary",
      "bg-blue-50",
      "dark:bg-blue-900/20"
    );
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove(
      "border-primary",
      "bg-blue-50",
      "dark:bg-blue-900/20"
    );
    const meterId =
      document.getElementById("editMeterForm")?.elements.id?.value;
    if (meterId && e.dataTransfer.files.length > 0) {
      uploadMeterPhotos(meterId, e.dataTransfer.files);
    }
  });
}

// ─── Hook into the existing edit modal open functions ─────────────────

(function () {
  // Wrap openEditMeterFromData (used by dynamic table row buttons)
  const originalOpen = window.openEditMeterFromData;
  if (originalOpen) {
    window.openEditMeterFromData = function (data) {
      originalOpen(data);
      if (data.id) {
        loadMeterPhotos(data.id);
      }
    };
  }

  // Wrap openEditMeter (used by legacy row-click handler)
  const originalOpenBtn = window.openEditMeter;
  if (originalOpenBtn) {
    window.openEditMeter = function (btn) {
      originalOpenBtn(btn);
      const form = document.getElementById("editMeterForm");
      const meterId = form?.elements.id?.value;
      if (meterId) {
        loadMeterPhotos(meterId);
      }
    };
  }

  // Setup drag-and-drop on DOM ready
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setupPhotoUpload);
  } else {
    setupPhotoUpload();
  }
})();
