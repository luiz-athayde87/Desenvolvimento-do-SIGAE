import { request } from "../api.js";
import { autoRefresh, escapeHTML, renderIcons } from "../ui.js";

let structures = {};
let selected = "patient_heap";
const labels = {
  patient_heap: "Heap de pacientes", doctor_heap: "Heap de médicos", hash: "Tabela Hash",
  avl: "Árvore AVL", red_black: "Árvore Rubro-Negra",
};

function render() {
  const data = structures[selected];
  const canvas = document.getElementById("structure-canvas");
  const size = Array.isArray(data) ? data.length : data ? 1 : 0;
  document.getElementById("structure-title").textContent = labels[selected];
  document.getElementById("structure-size").textContent = `${size} ${size === 1 ? "nó" : "nós"}`;
  if (!data || (Array.isArray(data) && !data.length)) {
    canvas.innerHTML = `<div class="empty-state"><i data-lucide="network"></i><p>A estrutura ainda não possui nós.</p></div>`;
  } else if (["patient_heap", "doctor_heap"].includes(selected)) {
    canvas.innerHTML = `<div class="node-grid">${data.map((item, index) => `<article class="data-node"><strong>#${index} · ${escapeHTML(item.id)}</strong><span>${escapeHTML(item.nome)}</span><span>${selected === "patient_heap" ? `Prioridade P${item.prioridade}` : `${item.atendimentos_concluidos} atendimentos`}</span></article>`).join("")}</div>`;
  } else if (selected === "hash") {
    const buckets = data.filter((bucket) => bucket.itens?.length);
    canvas.innerHTML = `<div class="node-grid">${buckets.map((bucket) => `<article class="data-node"><strong>Bucket ${bucket.bucket_id}</strong>${bucket.itens.map((item) => `<span>${escapeHTML(item.chave)} → ${escapeHTML(item.valor?.nome || "registro")}</span>`).join("")}</article>`).join("")}</div>`;
  } else {
    canvas.innerHTML = `<pre class="json-view">${escapeHTML(JSON.stringify(data, null, 2))}</pre>`;
  }
  renderIcons();
}

async function load() {
  structures = await request("/api/v1/structures");
  render();
}

export async function init() {
  document.querySelectorAll(".structure-tab").forEach((button) => button.addEventListener("click", () => {
    document.querySelectorAll(".structure-tab").forEach((item) => item.classList.remove("is-active"));
    button.classList.add("is-active"); selected = button.dataset.structure; render();
  }));
  await load();
  autoRefresh(load, 15000);
}
