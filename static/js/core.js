import { loadSession, login, logout, request, session } from "./api.js";
import { debounce, escapeHTML, openModal, closeModal, renderIcons, statusBadge, toast } from "./ui.js";

function updateRealClock() {
  const now = new Date();
  const clock = document.getElementById("real-clock");
  const date = document.getElementById("real-date");
  if (clock) clock.textContent = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(now);
  if (date) date.textContent = new Intl.DateTimeFormat("pt-BR", { weekday: "short", day: "2-digit", month: "short" }).format(now);
}

function updateProfile() {
  const name = session.user?.username || "Operador";
  const role = session.authenticated ? session.user?.role : session.authRequired ? "Entrar no SIGAE" : "Modo demonstração";
  document.getElementById("profile-name").textContent = name;
  document.getElementById("profile-role").textContent = role;
  document.getElementById("profile-avatar").textContent = name.slice(0, 2).toUpperCase();
  const logoutButton = document.getElementById("logout-button");
  if (logoutButton) logoutButton.hidden = !session.authenticated;
  window.dispatchEvent(new CustomEvent("sigae:session-changed", { detail: session }));
}

async function updateGlobalState() {
  try {
    const state = await request("/api/v1/state");
    const queueCount = document.getElementById("nav-queue-count");
    const sync = document.getElementById("sidebar-sync");
    if (queueCount) queueCount.textContent = state.metrics.waiting;
    if (sync) sync.textContent = `Dados atualizados às ${new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" }).format(new Date(state.server_time))}`;
    document.documentElement.dataset.connection = "online";
  } catch {
    document.documentElement.dataset.connection = "offline";
    const sync = document.getElementById("sidebar-sync");
    if (sync) sync.textContent = "Conexão indisponível";
  }
}

function setupNavigation() {
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.getElementById("sidebar-backdrop");
  const close = () => { sidebar?.classList.remove("is-open"); backdrop?.classList.remove("is-visible"); };
  document.getElementById("mobile-menu")?.addEventListener("click", () => {
    sidebar?.classList.add("is-open"); backdrop?.classList.add("is-visible");
  });
  backdrop?.addEventListener("click", close);
  document.getElementById("notifications-button")?.addEventListener("click", () => {
    toast("Não há alertas operacionais pendentes.", "success", "Central de notificações");
  });
}

function setupModals() {
  document.querySelectorAll("[data-close-modal]").forEach((button) => {
    button.addEventListener("click", () => closeModal(button.dataset.closeModal));
  });
  document.querySelectorAll("dialog").forEach((dialog) => {
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  });
  const openAuth = () => openModal("auth-modal");
  document.getElementById("profile-button")?.addEventListener("click", openAuth);
  window.addEventListener("sigae:auth-required", openAuth);
  document.getElementById("auth-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    const username = document.getElementById("auth-username").value.trim();
    const password = document.getElementById("auth-password").value;
    try {
      await login(username, password);
      document.getElementById("auth-password").value = "";
      closeModal("auth-modal");
      updateProfile();
      toast("Sessão iniciada com sucesso.");
    } catch (error) { toast(error.message, "error", "Não foi possível entrar"); }
  });
  document.getElementById("logout-button")?.addEventListener("click", async () => {
    try { await logout(); } catch { /* session is cleared locally below */ }
    closeModal("auth-modal");
    updateProfile();
    toast("Sessão encerrada.", "success");
  });
}

function setupSearch() {
  const modal = document.getElementById("search-modal");
  const input = document.getElementById("global-search");
  const results = document.getElementById("global-results");
  const open = () => { openModal("search-modal"); setTimeout(() => input?.focus(), 20); };
  document.getElementById("search-trigger")?.addEventListener("click", open);
  document.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") { event.preventDefault(); open(); }
  });
  input?.addEventListener("input", debounce(async () => {
    const query = input.value.trim();
    if (query.length < 2) {
      results.innerHTML = `<div class="empty-state compact"><i data-lucide="search"></i><p>Digite pelo menos dois caracteres.</p></div>`;
      renderIcons();
      return;
    }
    try {
      const items = await request(`/api/v1/search?q=${encodeURIComponent(query)}`);
      results.innerHTML = items.length ? items.map((item) => {
        const isPatient = item.type === "patient";
        return `<a class="command-result" href="/${isPatient ? "patients" : "doctors"}?q=${encodeURIComponent(item.id)}"><span class="avatar">${isPatient ? "PA" : "MD"}</span><div><strong>${escapeHTML(item.name)}</strong><small>${escapeHTML(item.id)} · ${isPatient ? "Paciente" : escapeHTML(item.crm)}</small></div>${statusBadge(item.status)}</a>`;
      }).join("") : `<div class="empty-state compact"><i data-lucide="search-x"></i><p>Nenhum registro encontrado.</p></div>`;
      renderIcons();
    } catch (error) { results.innerHTML = `<div class="empty-state compact"><p>${escapeHTML(error.message)}</p></div>`; }
  }, 280));
  modal?.addEventListener("close", () => { input.value = ""; });
}

async function initPage() {
  const page = document.body.dataset.page;
  if (!page) return;
  try {
    const module = await import(`./pages/${page}.js`);
    await module.init?.();
  } catch (error) {
    console.error(error);
    toast("A página não pôde ser inicializada.", "error", "Erro de interface");
  }
}

async function init() {
  updateRealClock();
  setInterval(updateRealClock, 1000);
  setupNavigation();
  setupModals();
  setupSearch();
  renderIcons();
  try { await loadSession(); } catch { /* demo mode remains available */ }
  updateProfile();
  await Promise.all([updateGlobalState(), initPage()]);
  setInterval(updateGlobalState, 15000);
}

init();
