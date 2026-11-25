import { request } from "../api.js";
import { autoRefresh, closeModal, debounce, escapeHTML, formatDateTime, initials, openModal, renderIcons, statusBadge, toast } from "../ui.js";

async function load() {
  const query = document.getElementById("doctor-search").value.trim();
  const status = document.getElementById("doctor-status").value;
  const params = new URLSearchParams();
  if (query) params.set("q", query);
  if (status) params.set("status", status);
  const doctors = await request(`/api/v1/doctors?${params}`);
  document.getElementById("doctors-total").textContent = doctors.length;
  document.getElementById("doctors-available").textContent = doctors.filter((item) => item.situacao === "Disponivel").length;
  document.getElementById("doctors-active").textContent = doctors.filter((item) => item.situacao === "Em atendimento").length;
  document.getElementById("doctors-offline").textContent = doctors.filter((item) => item.situacao === "Indisponivel").length;
  document.getElementById("doctor-grid").innerHTML = doctors.length ? doctors.map((doctor) => {
    const toggleStatus = doctor.situacao === "Disponivel" ? "Indisponivel" : "Disponivel";
    const canToggle = doctor.situacao !== "Em atendimento";
    return `<article class="doctor-card"><div class="doctor-card-head"><span class="avatar">${initials(doctor.nome)}</span><div><h3>${escapeHTML(doctor.nome)}</h3><p>${escapeHTML(doctor.especialidade)} · ${escapeHTML(doctor.crm)} · ${escapeHTML(doctor.id)}</p></div></div><div class="doctor-stats"><div><span>Concluídos</span><strong>${doctor.atendimentos_concluidos}</strong></div><div><span>Última liberação</span><strong>${formatDateTime(doctor.ultimo_atendimento_iso)}</strong></div></div><div class="doctor-actions">${statusBadge(doctor.situacao)}${canToggle ? `<button class="button small ghost toggle-doctor" data-id="${doctor.id}" data-status="${toggleStatus}" type="button">${toggleStatus === "Disponivel" ? "Disponibilizar" : "Indisponibilizar"}</button>` : ""}</div></article>`;
  }).join("") : `<div class="empty-state"><i data-lucide="user-search"></i><p>Nenhum médico corresponde aos filtros.</p></div>`;
  renderIcons();
}

async function toggleDoctor(identifier, status) {
  try {
    await request(`/api/v1/doctors/${encodeURIComponent(identifier)}/status`, { method: "PATCH", body: JSON.stringify({ situacao: status }) });
    toast(`Disponibilidade de ${identifier} atualizada.`);
    await load();
  } catch (error) { toast(error.message, "error", "Disponibilidade não alterada"); }
}

export async function init() {
  const params = new URLSearchParams(window.location.search);
  document.getElementById("doctor-search").value = params.get("q") || "";
  document.getElementById("new-doctor").addEventListener("click", () => openModal("doctor-modal"));
  document.getElementById("doctor-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const doctor = await request("/api/v1/doctors", { method: "POST", body: JSON.stringify({ nome: document.getElementById("doctor-name").value.trim(), crm: document.getElementById("doctor-crm").value.trim(), especialidade: document.getElementById("doctor-specialty").value.trim() }) });
      event.target.reset(); closeModal("doctor-modal");
      toast(`${doctor.nome} adicionado ao corpo médico.`);
      await load();
    } catch (error) { toast(error.message, "error", "Cadastro não concluído"); }
  });
  document.getElementById("doctor-grid").addEventListener("click", (event) => {
    const button = event.target.closest(".toggle-doctor");
    if (button) toggleDoctor(button.dataset.id, button.dataset.status);
  });
  const filter = debounce(load, 280);
  document.getElementById("doctor-search").addEventListener("input", filter);
  document.getElementById("doctor-status").addEventListener("change", filter);
  await load();
  autoRefresh(load, 12000);
}
