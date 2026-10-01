import { apiRequest, getCurrentUser } from "./auth.js";
import { getErrorMessage } from "./utils.js";

const taskList = document.getElementById("task-list");
const todoCount = document.getElementById("todo-count");
const progressCopy = document.getElementById("progress-copy");
const progressMeter = document.getElementById("progress-meter");
const progressValue = document.getElementById("progress-value");
const feedback = document.getElementById("todo-feedback");
const createForm = document.getElementById("create-todo-form");
const showCreateFormButton = document.getElementById("show-create-form");
const cancelCreateButton = document.getElementById("cancel-create");
const clearCompletedButton = document.getElementById("clear-completed");

let todos = [];

function showFeedback(message = "") {
  feedback.textContent = message;
}

function setProgress() {
  const completed = todos.filter((todo) => todo.completed).length;
  const total = todos.length;
  const percentage = total ? Math.round((completed / total) * 100) : 0;

  todoCount.textContent = String(total);
  progressCopy.textContent = total
    ? `${completed} of ${total} tasks completed.`
    : "Add your first task to get started.";
  progressMeter.setAttribute("aria-label", `${percentage} percent complete`);
  progressMeter.firstElementChild.style.width = `${percentage}%`;
  progressValue.textContent = `${percentage}%`;
  clearCompletedButton.disabled = completed === 0;
}

function createActionButton(label, action, todoId) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "task-action";
  button.textContent = label;
  button.dataset.action = action;
  button.dataset.todoId = String(todoId);
  return button;
}

function renderTodos() {
  taskList.replaceChildren();
  setProgress();

  if (!todos.length) {
    const emptyTask = document.createElement("li");
    emptyTask.className = "empty-tasks";
    emptyTask.textContent = "You have no tasks yet.";
    taskList.append(emptyTask);
    return;
  }

  for (const todo of todos) {
    const item = document.createElement("li");
    item.className = `task${todo.completed ? " completed" : ""}`;

    const label = document.createElement("label");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.completed;
    checkbox.dataset.action = "toggle";
    checkbox.dataset.todoId = String(todo.id);

    const checkmark = document.createElement("span");
    checkmark.className = "checkmark";
    const copy = document.createElement("span");
    copy.className = "task-copy";
    const title = document.createElement("span");
    title.className = "task-title";
    title.textContent = todo.title;
    copy.append(title);
    if (todo.description) {
      const description = document.createElement("small");
      description.className = "task-description";
      description.textContent = todo.description;
      copy.append(description);
    }
    label.append(checkbox, checkmark, copy);

    const actions = document.createElement("div");
    actions.className = "task-actions";
    actions.append(
      createActionButton("Edit", "edit", todo.id),
      createActionButton("Delete", "delete", todo.id),
    );
    item.append(label, actions);
    taskList.append(item);
  }
}

async function loadTodos() {
  const response = await apiRequest("/api/todos?limit=100");
  todos = response.todos;
  renderTodos();
}

async function toggleTodo(todoId, completed) {
  await apiRequest(`/api/todos/${todoId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ completed }),
  });
  await loadTodos();
}

async function editTodo(todoId) {
  const todo = todos.find((item) => item.id === todoId);
  if (!todo) return;

  const title = window.prompt("Task title", todo.title);
  if (title === null) return;
  const trimmedTitle = title.trim();
  if (!trimmedTitle) {
    showFeedback("A task title is required.");
    return;
  }
  const description = window.prompt("Description (optional)", todo.description || "");
  if (description === null) return;

  await apiRequest(`/api/todos/${todoId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: trimmedTitle, description: description.trim() || null }),
  });
  await loadTodos();
}

async function deleteTodo(todoId) {
  if (!window.confirm("Delete this task?")) return;
  await apiRequest(`/api/todos/${todoId}`, { method: "DELETE" });
  await loadTodos();
}

function setCurrentDate() {
  document.getElementById("current-date").textContent = new Intl.DateTimeFormat(
    "en-US",
    { weekday: "long", month: "long", day: "numeric" },
  ).format(new Date());
}

async function initialiseDashboard() {
  setCurrentDate();
  const user = await getCurrentUser();
  if (!user) {
    window.location.replace("/login");
    return;
  }

  document.getElementById("profile-avatar").src =
    user.profile_image_url || "/static/profile_picture/default.jpg";
  document.getElementById("profile-avatar").alt = `${user.username}'s profile picture`;
  document.getElementById("login-link").hidden = true;
  document.getElementById("register-link").hidden = true;

  try {
    await loadTodos();
  } catch (error) {
    showFeedback(getErrorMessage(error.body || error.message));
  }
}

showCreateFormButton.addEventListener("click", () => {
  createForm.hidden = false;
  document.getElementById("todo-title").focus();
});

cancelCreateButton.addEventListener("click", () => {
  createForm.reset();
  createForm.hidden = true;
  showFeedback();
});

createForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(createForm);
  const title = formData.get("title").trim();
  const description = formData.get("description").trim();

  try {
    await apiRequest("/api/todos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, description: description || null }),
    });
    createForm.reset();
    createForm.hidden = true;
    showFeedback();
    await loadTodos();
  } catch (error) {
    showFeedback(getErrorMessage(error.body || error.message));
  }
});

taskList.addEventListener("change", async (event) => {
  const target = event.target;
  if (target.dataset.action !== "toggle") return;
  try {
    await toggleTodo(Number(target.dataset.todoId), target.checked);
  } catch (error) {
    showFeedback(getErrorMessage(error.body || error.message));
    await loadTodos();
  }
});

taskList.addEventListener("click", async (event) => {
  const target = event.target.closest("button[data-action]");
  if (!target) return;

  try {
    const todoId = Number(target.dataset.todoId);
    if (target.dataset.action === "edit") await editTodo(todoId);
    if (target.dataset.action === "delete") await deleteTodo(todoId);
  } catch (error) {
    showFeedback(getErrorMessage(error.body || error.message));
  }
});

clearCompletedButton.addEventListener("click", async () => {
  const completedTodos = todos.filter((todo) => todo.completed);
  if (!completedTodos.length || !window.confirm("Delete all completed tasks?")) return;

  try {
    await Promise.all(
      completedTodos.map((todo) => apiRequest(`/api/todos/${todo.id}`, { method: "DELETE" })),
    );
    await loadTodos();
  } catch (error) {
    showFeedback(getErrorMessage(error.body || error.message));
  }
});

initialiseDashboard();
