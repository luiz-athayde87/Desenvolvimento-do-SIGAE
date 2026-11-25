import { request } from "../api.js";
import { autoRefresh, escapeHTML, formatDateTime, initials, priorityBadge, priorityMeta, renderIcons, toast } from "../ui.js";

async function load() {
  const state = await request("/api/v1/state");
  const queue = state.waiting_queue;
  document.getElementById("triage-count").textContent = `${queue.length} paciente${queue.length === 1 ? "" : "s"}`;
  document.getElementById("triage-list").innerHTML = queue.length ? queue.map((patient) => `<article class="triage-patient"><div class="patient-cell"><span class="avatar">${initials(patient.nome)}</span><span><strong>${escapeHTML(patient.nome)}</strong><small>${escapeHTML(patient.id)} · ${escapeHTML(patient.queixa || "Sem queixa informada")} · Chegada ${formatDateTime(patient.horario_chegada_iso)} · ${patient.tempo_espera_minutos} min de espera</small></span></div>${priorityBadge(patient.prioridade)}<div class="priority-actions" aria-label="Reclassificar ${escapeHTML(patient.nome)}">${Object.keys(priorityMeta).map((priority) => `<button class="priority-button ${Number(priority) === patient.prioridade ? "is-active" : ""}" data-id="${patient.id}" data-priority="${priority}" type="button" title="${priorityMeta[priority].label}">${priority}</button>`).join("")}</div></article>`).join("") : `<div class="empty-state"><i data-lucide="clipboard-check"></i><p>Nenhum paciente aguardando reclassificação.</p></div>`;
  renderIcons();
}

async function reclassify(identifier, priority) {
  try {
    await request(`/api/v1/patients/${encodeURIComponent(identifier)}/priority`, { method: "PATCH", body: JSON.stringify({ prioridade: Number(priority) }) });
    toast(`${identifier} reclassificado para P${priority}.`);
    await load();
  } catch (error) { toast(error.message, "error", "Reclassificação não concluída"); }
}

export async function init() {
  document.getElementById("triage-list").addEventListener("click", (event) => {
    const button = event.target.closest(".priority-button");
    if (button) reclassify(button.dataset.id, button.dataset.priority);
  });
  await load();
  autoRefresh(load, 10000);
}
