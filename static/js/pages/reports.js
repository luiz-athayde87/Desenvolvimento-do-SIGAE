import { request } from "../api.js";
import { autoRefresh, formatDateTime, priorityMeta } from "../ui.js";

async function load() {
  const report = await request("/api/v1/reports/summary");
  const metrics = report.metrics;
  document.getElementById("report-patients").textContent = report.total_patients;
  document.getElementById("report-doctors").textContent = report.total_doctors;
  document.getElementById("report-completed").textContent = metrics.completed;
  document.getElementById("report-wait").textContent = `${metrics.average_wait_minutes} min`;
  const distribution = metrics.priority_distribution;
  const maximum = Math.max(...Object.values(distribution).map(Number), 1);
  document.getElementById("report-priority-chart").innerHTML = Object.entries(distribution).map(([priority, value]) => {
    const meta = priorityMeta[priority];
    return `<div class="bar-row"><span>${meta.code} · ${meta.label}</span><div class="bar-track"><div class="bar-fill" style="width:${(Number(value) / maximum) * 100}%;background:${meta.color}"></div></div><strong>${value}</strong></div>`;
  }).join("");
  const summary = [
    ["Pacientes aguardando", metrics.waiting], ["Casos críticos", metrics.critical],
    ["Atendimentos ativos", metrics.active], ["Médicos disponíveis", metrics.available_doctors],
    ["Eventos auditados", report.audit_events], ["Gerado em", formatDateTime(report.generated_at)],
  ];
  document.getElementById("report-summary").innerHTML = summary.map(([label, value]) => `<div class="summary-row"><span>${label}</span><strong>${value}</strong></div>`).join("");
}

export async function init() {
  await load();
  autoRefresh(load, 15000);
}
