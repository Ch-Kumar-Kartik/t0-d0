import { apiRequest } from "./auth.js";
import { getErrorMessage } from "./utils.js";

const feedback = document.getElementById("form-feedback");
const forgotPasswordForm = document.getElementById("forgot-password-form");
const resetPasswordForm = document.getElementById("reset-password-form");

function setFeedback(message = "", isError = false) {
  feedback.textContent = message;
  feedback.classList.toggle("is-success", !isError && Boolean(message));
}

async function submitForgotPassword(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const submitButton = form.querySelector("button[type=submit]");
  submitButton.disabled = true;

  try {
    const response = await apiRequest("/api/users/forgot-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: form.email.value }),
    });
    form.reset();
    setFeedback(response.detail);
  } catch (error) {
    setFeedback(getErrorMessage(error.body || error.message), true);
  } finally {
    submitButton.disabled = false;
  }
}

async function submitResetPassword(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const token = new URLSearchParams(window.location.search).get("token");
  const submitButton = form.querySelector("button[type=submit]");

  if (!token) {
    setFeedback("This reset link is missing its token.", true);
    return;
  }
  if (form.new_password.value !== form.confirm_password.value) {
    setFeedback("New passwords do not match.", true);
    return;
  }

  submitButton.disabled = true;
  try {
    await apiRequest("/api/users/reset-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password: form.new_password.value }),
    });
    form.reset();
    setFeedback("Password updated. Redirecting you to log in...");
    window.setTimeout(() => window.location.assign("/login"), 1500);
  } catch (error) {
    setFeedback(getErrorMessage(error.body || error.message), true);
    submitButton.disabled = false;
  }
}

if (forgotPasswordForm) {
  forgotPasswordForm.addEventListener("submit", submitForgotPassword);
}

if (resetPasswordForm) {
  resetPasswordForm.addEventListener("submit", submitResetPassword);
}
