import { request, session } from "../api.js";
import { closeModal, escapeHTML, initials, openModal, renderIcons, statusBadge, toast } from "../ui.js";

function updateSessionCard() {
  const name = session.user?.username || "Operador";
  document.getElementById("settings-avatar").textContent = initials(name);
  document.getElementById("settings-user").textContent = name;
  document.getElementById("settings-role").textContent = session.authenticated ? session.user.role : session.authRequired ? "Sessão necessária" : "Modo demonstração";
  document.getElementById("session-action").textContent = session.authenticated ? "Gerenciar sessão" : "Entrar no sistema";
}

async function loadUsers() {
  const table = document.getElementById("users-table");
  const locked = document.getElementById("users-locked");
  try {
    const users = await request("/api/v1/auth/users");
    locked.hidden = true;
    table.closest(".table-wrap").hidden = false;
    table.innerHTML = users.map((user) => `<tr><td><div class="patient-cell"><span class="avatar">${initials(user.username)}</span><span><strong>${escapeHTML(user.username)}</strong><small>ID ${user.id}</small></span></div></td><td><span class="chip neutral">${escapeHTML(user.role)}</span></td><td>${statusBadge(user.active ? "Disponivel" : "Indisponivel")}</td><td class="align-right"><button class="button small ghost toggle-user" data-id="${user.id}" data-active="${!user.active}" type="button">${user.active ? "Desativar" : "Ativar"}</button></td></tr>`).join("");
    renderIcons();
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      table.closest(".table-wrap").hidden = true;
      locked.hidden = false;
    } else toast(error.message, "error", "Usuários indisponíveis");
  }
}

export async function init() {
  updateSessionCard();
  document.getElementById("settings-login").addEventListener("click", () => openModal("auth-modal"));
  document.getElementById("session-action").addEventListener("click", () => openModal("auth-modal"));
  document.getElementById("new-user").addEventListener("click", () => openModal("user-modal"));
  document.getElementById("user-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await request("/api/v1/auth/users", { method: "POST", body: JSON.stringify({ username: document.getElementById("user-name").value.trim(), password: document.getElementById("user-password").value, role: document.getElementById("user-role").value }) });
      event.target.reset(); closeModal("user-modal"); toast("Usuário criado com sucesso."); await loadUsers();
    } catch (error) { toast(error.message, "error", "Usuário não criado"); }
  });
  document.getElementById("users-table").addEventListener("click", async (event) => {
    const button = event.target.closest(".toggle-user");
    if (!button) return;
    try {
      await request(`/api/v1/auth/users/${button.dataset.id}/active`, { method: "PATCH", body: JSON.stringify({ active: button.dataset.active === "true" }) });
      toast("Situação do usuário atualizada."); await loadUsers();
    } catch (error) { toast(error.message, "error", "Acesso não alterado"); }
  });
  document.getElementById("reset-demo").addEventListener("click", async () => {
    if (!window.confirm("Reiniciar todos os dados operacionais da demonstração?")) return;
    try { await request("/api/v1/reset", { method: "POST" }); toast("Dados demonstrativos restaurados."); }
    catch (error) { toast(error.message, "error", "Reinício não concluído"); }
  });
  window.addEventListener("sigae:session-changed", () => { updateSessionCard(); loadUsers(); });
  await loadUsers();
}
