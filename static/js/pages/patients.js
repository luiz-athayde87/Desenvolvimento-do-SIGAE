import { request } from "../api.js";
import { autoRefresh, closeModal, debounce, emptyTable, formatDateTime, formatDuration, openModal, patientCell, priorityBadge, renderIcons, statusBadge, toast } from "../ui.js";

let page = 1;
let pages = 1;

async function load() {
  const query = document.getElementById("patient-search").value.trim();
  const status = document.getElementById("patient-status").value;
  const priority = document.getElementById("patient-priority").value;
  const params = new URLSearchParams({ page, per_page: 15 });
  if (query) params.set("q", query);
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  const [result, state] = await Promise.all([
    request(`/api/v1/patients?${params}`),
    request("/api/v1/state"),
  ]);
  pages = result.pagination.pages;
  document.getElementById("patients-total").textContent = state.patients.length;
  document.getElementById("patients-waiting").textContent = state.metrics.waiting;
  document.getElementById("patients-active").textContent = state.metrics.active;
  document.getElementById("patients-completed").textContent = state.metrics.completed;
  document.getElementById("patients-table").innerHTML = result.items.length ? result.items.map((patient) => {
    const canCancel = ["Aguardando", "Em atendimento"].includes(patient.situacao);
    return `<tr><td>${patientCell(patient)}</td><td>${priorityBadge(patient.prioridade)}</td><td>${formatDateTime(patient.horario_chegada_iso)}</td><td>${formatDuration(patient.tempo_total_minutos)}</td><td>${statusBadge(patient.situacao)}</td><td class="align-right">${canCancel ? `<button class="button small ghost cancel-patient" data-id="${patient.id}" type="button">Cancelar</button>` : "—"}</td></tr>`;
  }).join("") : emptyTable(6, "Nenhum paciente corresponde aos filtros.");
  document.getElementById("patients-page").textContent = `Página ${page} de ${pages} · ${result.pagination.total} registros`;
  document.getElementById("patients-prev").disabled = page <= 1;
  document.getElementById("patients-next").disabled = page >= pages;
  renderIcons();
}

async function cancelPatient(identifier) {
  if (!window.confirm(`Cancelar o registro ${identifier}?`)) return;
  try {
    await request(`/api/v1/patients/${encodeURIComponent(identifier)}/cancel`, { method: "POST" });
    toast("Paciente cancelado e recursos liberados.");
    await load();
  } catch (error) { toast(error.message, "error", "Não foi possível cancelar"); }
}

export async function init() {
  const params = new URLSearchParams(window.location.search);
  document.getElementById("patient-search").value = params.get("q") || "";
  document.getElementById("new-patient").addEventListener("click", () => openModal("patient-modal"));
  if (params.get("new") === "1") openModal("patient-modal");
  document.getElementById("patient-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const patient = await request("/api/v1/patients", {
        method: "POST",
        body: JSON.stringify({ nome: document.getElementById("patient-name").value.trim(), queixa: document.getElementById("patient-complaint").value.trim(), prioridade: Number(document.getElementById("patient-priority-input").value) }),
      });
      event.target.reset();
      closeModal("patient-modal");
      toast(`${patient.id} · ${patient.nome} cadastrado no horário real atual.`);
      page = 1;
      await load();
    } catch (error) { toast(error.message, "error", "Cadastro não concluído"); }
  });
  document.getElementById("patients-table").addEventListener("click", (event) => {
    const button = event.target.closest(".cancel-patient");
    if (button) cancelPatient(button.dataset.id);
  });
  const filter = debounce(() => { page = 1; load(); }, 280);
  document.getElementById("patient-search").addEventListener("input", filter);
  document.getElementById("patient-status").addEventListener("change", filter);
  document.getElementById("patient-priority").addEventListener("change", filter);
  document.getElementById("patients-prev").addEventListener("click", () => { if (page > 1) { page -= 1; load(); } });
  document.getElementById("patients-next").addEventListener("click", () => { if (page < pages) { page += 1; load(); } });
  await load();
  autoRefresh(load, 15000);
}
