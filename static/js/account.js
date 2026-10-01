import {
  apiRequest,
  clearUserCache,
  getCurrentUser,
  logout,
} from "./auth.js";
import { getErrorMessage } from "./utils.js";

const defaultAvatar = "/static/profile_picture/default.jpg";

function setFeedback(id, message = "", isError = false) {
  const element = document.getElementById(id);
  element.textContent = message;
  element.classList.toggle("is-error", isError);
}

function displayUser(user) {
  document.getElementById("account-username").textContent = user.username;
  document.getElementById("account-email").textContent = user.email;
  document.getElementById("username").value = user.username;
  document.getElementById("email").value = user.email;

  const avatar = document.getElementById("account-avatar");
  avatar.src = user.profile_image_url || defaultAvatar;
  avatar.alt = `${user.username}'s profile picture`;
}

async function updateProfile(field, form, feedbackId) {
  const formData = new FormData(form);
  const value = formData.get(field).trim();
  const payload = { [field]: value };
  if (field === "email") {
    payload.current_password = formData.get("current_password");
  }
  try {
    const user = await apiRequest("/api/users/me", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    clearUserCache();
    displayUser(user);
    if (field === "email") form.reset();
    setFeedback(feedbackId, "Saved.");
  } catch (error) {
    setFeedback(feedbackId, getErrorMessage(error.body || error.message), true);
  }
}

async function initialiseAccount() {
  const user = await getCurrentUser();
  if (!user) {
    window.location.replace("/login");
    return;
  }
  displayUser(user);
}

document.getElementById("username-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await updateProfile("username", event.currentTarget, "username-feedback");
});

document.getElementById("email-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await updateProfile("email", event.currentTarget, "email-feedback");
});

document.getElementById("password-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const currentPassword = form.current_password.value;
  const newPassword = form.new_password.value;

  if (newPassword !== form.confirm_password.value) {
    setFeedback("password-feedback", "New passwords do not match.", true);
    return;
  }

  try {
    await apiRequest("/api/users/me/password", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    });
    form.reset();
    setFeedback("password-feedback", "Password updated.");
  } catch (error) {
    setFeedback("password-feedback", getErrorMessage(error.body || error.message), true);
  }
});

document.getElementById("logout-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  await logout();
});

document.getElementById("delete-account-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!window.confirm("Delete your account and all of its todos?")) return;

  try {
    const currentPassword = new FormData(event.currentTarget).get("current_password");
    await apiRequest("/api/users/me", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: currentPassword }),
    });
    await logout();
  } catch (error) {
    setFeedback("delete-feedback", getErrorMessage(error.body || error.message), true);
  }
});

document.getElementById("avatar-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const pictureInput = form.elements.profile_picture;

  if (!pictureInput.files.length) {
    setFeedback("avatar-feedback", "Choose a JPG or PNG image first.", true);
    return;
  }

  const submitButton = form.querySelector("button[type=submit]");
  submitButton.disabled = true;
  submitButton.textContent = "Uploading...";

  try {
    const user = await apiRequest("/api/users/me/profile-picture", {
      method: "POST",
      body: new FormData(form),
    });
    clearUserCache();
    displayUser(user);
    form.reset();
    setFeedback("avatar-feedback", "Profile picture updated.");
  } catch (error) {
    setFeedback("avatar-feedback", getErrorMessage(error.body || error.message), true);
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = "Upload picture";
  }
});

initialiseAccount();
