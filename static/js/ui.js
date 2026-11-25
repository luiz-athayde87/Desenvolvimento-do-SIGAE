export const priorityMeta = {
  1: { code: "P1", label: "Emergência", className: "p1", color: "#e6333d", sla: 0 },
  2: { code: "P2", label: "Muito urgente", className: "p2", color: "#f16d22", sla: 10 },
  3: { code: "P3", label: "Urgente", className: "p3", color: "#f2b720", sla: 60 },
  4: { code: "P4", label: "Pouco urgente", className: "p4", color: "#20a45a", sla: 120 },
  5: { code: "P5", label: "Não urgente", className: "p5", color: "#2a9c8c", sla: 240 },
};

export function escapeHTML(value = "") {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[character]);
}

export function initials(name = "") {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "--";
}

export function formatDateTime(value, options = {}) {
  if (!value) return "—";
  const date = typeof value === "number" ? new Date(value * 1000) : new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("pt-BR", {
    day: options.dateOnly ? "2-digit" : undefined,
    month: options.dateOnly ? "short" : undefined,
    hour: options.dateOnly ? undefined : "2-digit",
    minute: options.dateOnly ? undefined : "2-digit",
  }).format(date);
}

export function formatDuration(minutes) {
  const value = Number(minutes || 0);
  if (value < 60) return `${value} min`;
  return `${Math.floor(value / 60)}h ${value % 60}min`;
}

export function priorityBadge(priority) {
  const item = priorityMeta[Number(priority)] || priorityMeta[5];
  return `<span class="badge ${item.className}">${item.code} · ${item.label}</span>`;
}

export function statusBadge(status = "") {
  const normalized = String(status);
  const classes = {
    "Aguardando": "waiting", "Em atendimento": "active", "Concluido": "completed",
    "Cancelado": "cancelled", "Disponivel": "available", "Indisponivel": "offline",
  };
  const labels = { Concluido: "Concluído", Disponivel: "Disponível", Indisponivel: "Indisponível" };
  return `<span class="badge ${classes[normalized] || "offline"}">${labels[normalized] || escapeHTML(normalized)}</span>`;
}

export function patientCell(patient) {
  return `<div class="patient-cell"><span class="avatar">${initials(patient.nome || patient.patient_name)}</span><span><strong>${escapeHTML(patient.nome || patient.patient_name)}</strong><small>${escapeHTML(patient.id || patient.patient_id)}</small></span></div>`;
}

export function emptyTable(columns, message) {
  return `<tr><td colspan="${columns}"><div class="empty-state"><i data-lucide="inbox"></i><p>${escapeHTML(message)}</p></div></td></tr>`;
}

export function renderIcons() {
  if (window.lucide) window.lucide.createIcons({ attrs: { "aria-hidden": "true" } });
}

export function openModal(id) {
  const modal = document.getElementById(id);
  if (modal && !modal.open) modal.showModal();
}

export function closeModal(id) {
  document.getElementById(id)?.close();
}

export function toast(message, type = "success", title = "SIGAE") {
  const stack = document.getElementById("toast-stack");
  if (!stack) return;
  const item = document.createElement("div");
  item.className = `toast ${type}`;
  item.innerHTML = `<i data-lucide="${type === "error" ? "circle-alert" : "circle-check"}"></i><div><strong>${escapeHTML(title)}</strong><small>${escapeHTML(message)}</small></div><button type="button" aria-label="Fechar">×</button>`;
  item.querySelector("button").addEventListener("click", () => item.remove());
  stack.append(item);
  renderIcons();
  setTimeout(() => item.remove(), 5200);
}

export function debounce(callback, delay = 300) {
  let timer;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => callback(...args), delay);
  };
}

export function autoRefresh(callback, interval = 15000) {
  let running = true;
  const tick = async () => {
    if (!running || document.hidden) return;
    try { await callback(); } catch { /* feedback is handled by the page */ }
  };
  const timer = setInterval(tick, interval);
  document.addEventListener("visibilitychange", tick);
  return () => { running = false; clearInterval(timer); };
}
