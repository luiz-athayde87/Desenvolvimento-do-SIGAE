import { request } from "../api.js";
import { autoRefresh, emptyTable, escapeHTML, formatDateTime, formatDuration, patientCell, priorityBadge, priorityMeta, renderIcons, statusBadge, toast } from "../ui.js";

function slaStatus(patient) {
  const limit = priorityMeta[patient.prioridade].sla;
  if (limit === 0) return `<span class="badge p1">Imediato</span>`;
  const remaining = limit - patient.tempo_espera_minutos;
  return remaining < 0 ? `<span class="badge p1">SLA excedido</span>` : `<span class="badge available">${remaining} min restantes</span>`;
}

async function load() {
  const state = await request("/api/v1/state");
  document.getElementById("active-count").textContent = state.metrics.active;
  document.getElementById("average-wait").textContent = state.metrics.average_wait_minutes;
  document.getElementById("available-count").textContent = state.metrics.available_doctors;
  document.getElementById("queue-total").textContent = `${state.metrics.waiting} aguardando`;
  const patientMap = Object.fromEntries(state.patients.map((patient) => [patient.id, patient]));
  const doctorMap = Object.fromEntries(state.doctors.map((doctor) => [doctor.id, doctor]));
  document.getElementById("active-attendances").innerHTML = state.active_attendances.length ? state.active_attendances.map((attendance) => {
    const patient = patientMap[attendance.patient_id];
    const doctor = doctorMap[attendance.doctor_id];
    return `<article class="attendance-card"><h3>${escapeHTML(patient?.nome || attendance.patient_id)}</h3><p>${escapeHTML(doctor?.nome || attendance.doctor_id)} · Início ${formatDateTime(attendance.started_seconds)}</p><div class="attendance-card-footer">${priorityBadge(attendance.priority)}<button class="button small primary complete-attendance" data-id="${attendance.patient_id}" type="button"><i data-lucide="check"></i>Concluir</button></div></article>`;
  }).join("") : `<div class="empty-state"><i data-lucide="activity"></i><p>Nenhum atendimento ativo no momento.</p></div>`;
  document.getElementById("queue-table").innerHTML = state.waiting_queue.length ? state.waiting_queue.map((patient, index) => `<tr><td><strong>${index + 1}</strong></td><td>${patientCell(patient)}</td><td>${priorityBadge(patient.prioridade)}</td><td>${formatDateTime(patient.horario_chegada_iso)}</td><td>${formatDuration(patient.tempo_espera_minutos)}</td><td>${slaStatus(patient)}</td><td><button class="button small ghost cancel-waiting" data-id="${patient.id}" type="button">Cancelar</button></td></tr>`).join("") : emptyTable(7, "A fila está vazia.");
  renderIcons();
}

async function callNext() {
  const button = document.getElementById("call-next");
  button.disabled = true;
  try {
    const attendance = await request("/api/v1/attendances/call-next", { method: "POST" });
    toast(`${attendance.patient.nome} encaminhado para ${attendance.doctor.nome}.`);
    await load();
  } catch (error) { toast(error.message, "error", "Chamada não realizada"); }
  finally { button.disabled = false; }
}

async function mutatePatient(identifier, action) {
  try {
    await request(`/api/v1/patients/${encodeURIComponent(identifier)}/${action}`, { method: "POST" });
    toast(action === "complete" ? "Atendimento concluído com sucesso." : "Paciente removido da fila.");
    await load();
  } catch (error) { toast(error.message, "error", "Operação não concluída"); }
}

export async function init() {
  document.getElementById("call-next").addEventListener("click", callNext);
  document.getElementById("active-attendances").addEventListener("click", (event) => {
    const button = event.target.closest(".complete-attendance");
    if (button) mutatePatient(button.dataset.id, "complete");
  });
  document.getElementById("queue-table").addEventListener("click", (event) => {
    const button = event.target.closest(".cancel-waiting");
    if (button && window.confirm(`Remover ${button.dataset.id} da fila?`)) mutatePatient(button.dataset.id, "cancel");
  });
  await load();
  autoRefresh(load, 8000);
}
