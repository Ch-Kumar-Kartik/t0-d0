export function getErrorMessage(error) {
  if (!error) {
    return "An error occurred. Please try again.";
  }

  if (typeof error === "string") {
    return error;
  }

  if (typeof error.detail === "string") {
    return error.detail;
  }

  if (Array.isArray(error.detail)) {
    return error.detail
      .map((item) => item.msg || "Invalid value")
      .join(". ");
  }

  return "An error occurred. Please try again.";
}

export function showModal(modalId) {
  if (!globalThis.bootstrap) {
    throw new Error("Bootstrap is required to show modals.");
  }

  const element = document.getElementById(modalId);
  if (!element) {
    throw new Error(`Modal not found: ${modalId}`);
  }

  const modal = bootstrap.Modal.getOrCreateInstance(element);
  modal.show();
  return modal;
}

export function hideModal(modalId) {
  if (!globalThis.bootstrap) {
    return;
  }

  const element = document.getElementById(modalId);
  const modal = element ? bootstrap.Modal.getInstance(element) : null;
  if (modal) {
    modal.hide();
  }
}

export function escapeHtml(value) {
  const div = document.createElement("div");
  div.textContent = String(value ?? "");
  return div.innerHTML;
}

export function formatDate(dateString) {
  const date = new Date(dateString);
  if (Number.isNaN(date.getTime())) {
    return "";
  }

  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "long",
    day: "2-digit",
  });
}
