import { request } from "../api.js";
import { autoRefresh, emptyTable, escapeHTML, formatDateTime, formatDuration, patientCell, priorityBadge, renderIcons, statusBadge } from "../ui.js";

let page = 1;
let pages = 1;

const eventLabels = {
  "patient.created": "Paciente cadastrado", "patient.reclassified": "Prioridade reclassificada",
  "patient.cancelled": "Paciente cancelado", "attendance.started": "Atendimento iniciado",
  "attendance.completed": "Atendimento concluído", "doctor.created": "Médico cadastrado",
  "doctor.status_changed": "Disponibilidade alterada", "shift.seeded": "Plantão inicializado",
  "user.created": "Usuário criado", "user.status_changed": "Acesso atualizado",
};

async function load() {
  const [history, state] = await Promise.all([
    request(`/api/v1/history?page=${page}&per_page=15`),
    request("/api/v1/state"),
  ]);
  pages = history.pagination.pages;
  document.getElementById("history-total").textContent = `${history.pagination.total} registros`;
  document.getElementById("history-table").innerHTML = history.items.length ? history.items.map((item) => `<tr><td>${patientCell({ id: item.patient_id, nome: item.patient_name })}</td><td>${escapeHTML(item.doctor_name)}</td><td>${priorityBadge(item.priority)}</td><td>${formatDateTime(item.started_at)}</td><td>${formatDuration(item.duration_minutes)}</td><td>${statusBadge(item.status)}</td></tr>`).join("") : emptyTable(6, "Ainda não há atendimentos no histórico.");
  document.getElementById("history-page").textContent = `Página ${page} de ${pages}`;
  document.getElementById("history-prev").disabled = page <= 1;
  document.getElementById("history-next").disabled = page >= pages;
  document.getElementById("audit-list").innerHTML = state.audit.length ? state.audit.map((event) => `<article class="audit-item"><strong>${escapeHTML(eventLabels[event.event] || event.event)}</strong><p>${escapeHTML(event.entity_type)}${event.entity_id ? ` · ${escapeHTML(event.entity_id)}` : ""}</p><small>${formatDateTime(`${event.created_at}Z`)}</small></article>`).join("") : `<div class="empty-state compact"><p>Nenhum evento registrado.</p></div>`;
  renderIcons();
}

export async function init() {
  document.getElementById("history-prev").addEventListener("click", () => { if (page > 1) { page -= 1; load(); } });
  document.getElementById("history-next").addEventListener("click", () => { if (page < pages) { page += 1; load(); } });
  await load();
  autoRefresh(load, 15000);
}
