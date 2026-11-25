import { request } from "../api.js";
import { autoRefresh, emptyTable, escapeHTML, formatDateTime, initials, patientCell, priorityBadge, priorityMeta, renderIcons, statusBadge } from "../ui.js";

function renderMetrics(metrics) {
  document.querySelectorAll("[data-metric]").forEach((element) => {
    element.textContent = metrics[element.dataset.metric] ?? 0;
  });
}

function renderFlow(metrics) {
  const values = [metrics.waiting, metrics.critical, metrics.active, metrics.completed];
  const labels = ["Na fila", "Casos críticos", "Em atendimento", "Concluídos"];
  const icons = ["users", "siren", "activity", "circle-check-big"];
  const maximum = Math.max(...values, 1);
  document.getElementById("flow-chart").innerHTML = values.map((value, index) => `
    <div class="flow-stage"><div class="flow-bar-shell"><div class="flow-bar" style="height:${Math.max(5, (value / maximum) * 100)}%"></div></div><strong>${value}</strong><span><i data-lucide="${icons[index]}"></i> ${labels[index]}</span></div>
  `).join("");
}

function renderPriority(distribution) {
  const values = Object.values(distribution).map(Number);
  const total = values.reduce((sum, value) => sum + value, 0);
  document.getElementById("donut-total").textContent = total;
  let cursor = 0;
  const segments = [];
  Object.entries(distribution).forEach(([priority, raw]) => {
    const value = Number(raw);
    const percentage = total ? (value / total) * 100 : 0;
    segments.push(`${priorityMeta[priority].color} ${cursor}% ${cursor + percentage}%`);
    cursor += percentage;
  });
  if (segments.length && total) document.getElementById("priority-donut").style.background = `conic-gradient(${segments.join(",")})`;
  document.getElementById("priority-legend").innerHTML = Object.entries(distribution).map(([priority, value]) => {
    const item = priorityMeta[priority];
    return `<div class="legend-item"><i style="background:${item.color}"></i><b>${item.code} · ${item.label}</b><span>${value}</span></div>`;
  }).join("");
}

function renderQueue(queue) {
  document.getElementById("overview-queue").innerHTML = queue.length ? queue.slice(0, 5).map((patient, index) => `<tr><td><strong>${index + 1}</strong></td><td>${patientCell(patient)}</td><td>${priorityBadge(patient.prioridade)}</td><td>${formatDateTime(patient.horario_chegada_iso)}</td><td>${patient.tempo_espera_minutos} min</td></tr>`).join("") : emptyTable(5, "Nenhum paciente aguardando.");
}

function renderDoctors(doctors) {
  document.getElementById("overview-doctors").innerHTML = doctors.slice(0, 5).map((doctor) => `<div class="team-row"><span class="avatar">${initials(doctor.nome)}</span><div><strong>${escapeHTML(doctor.nome)}</strong><small>${escapeHTML(doctor.crm)} · ${doctor.atendimentos_concluidos} concluídos</small></div>${statusBadge(doctor.situacao)}</div>`).join("");
}

async function load() {
  const state = await request("/api/v1/state");
  renderMetrics(state.metrics);
  renderFlow(state.metrics);
  renderPriority(state.metrics.priority_distribution);
  renderQueue(state.waiting_queue);
  renderDoctors(state.doctors);
  document.getElementById("overview-last-sync").textContent = `Atualizado às ${formatDateTime(state.server_time)}`;
  renderIcons();
}

export async function init() {
  await load();
  autoRefresh(load, 10000);
}
