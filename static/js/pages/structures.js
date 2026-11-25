import { request } from "../api.js";
import { autoRefresh, escapeHTML, renderIcons } from "../ui.js";

let structures = {};
let selected = "patient_heap";

const NODE_WIDTH = 168;
const LEVEL_GAP = 150;
const metadata = {
  patient_heap: {
    label: "Heap de pacientes",
    kind: "Árvore binária completa",
    description: "Min-heap ordenado por risco, horário de chegada e ID. O nó raiz representa o próximo paciente da fila.",
    legend: [["Raiz", "Próximo paciente"], ["E / D", "Filho esquerdo / direito"], ["#", "Índice no vetor"]],
  },
  doctor_heap: {
    label: "Heap de médicos",
    kind: "Árvore binária completa",
    description: "Min-heap de carga assistencial. O médico disponível com menor carga permanece na raiz.",
    legend: [["Raiz", "Menor carga"], ["E / D", "Filho esquerdo / direito"], ["#", "Índice no vetor"]],
  },
  hash: {
    label: "Tabela Hash",
    kind: "Buckets com encadeamento",
    description: "Representação canônica da tabela: a função hash seleciona o bucket e colisões são mantidas em uma cadeia.",
    legend: [["Bucket", "Posição calculada"], ["→", "Encadeamento"], ["∅", "Bucket vazio"]],
  },
  avl: {
    label: "Árvore AVL",
    kind: "Árvore binária balanceada",
    description: "Árvore de busca binária autobalanceada. Cada nó expõe altura e fator de balanceamento reais.",
    legend: [["h", "Altura do nó"], ["FB", "Fator de balanceamento"], ["E / D", "Filho esquerdo / direito"]],
  },
  red_black: {
    label: "Árvore Rubro-Negra",
    kind: "Árvore binária balanceada",
    description: "Árvore de busca com a coloração real usada para preservar o balanceamento após inserções.",
    legend: [["●", "Nó preto"], ["●", "Nó vermelho"], ["E / D", "Filho esquerdo / direito"]],
  },
};

function valueLabel(value = {}) {
  return value.nome || value.paciente_nome || value.paciente_id || value.doctor_name || value.medico_id || value.id || "Registro";
}

function formatKey(key) {
  if (Array.isArray(key)) return key.map((part) => String(part)).join(" · ");
  if (key && typeof key === "object") return JSON.stringify(key);
  return String(key ?? "—");
}

function renderLegend() {
  document.getElementById("structure-legend").innerHTML = metadata[selected].legend.map(([symbol, label], index) => {
    const colorClass = selected === "red_black" ? ` rb-legend-${index}` : "";
    return `<span class="legend-key${colorClass}"><b>${escapeHTML(symbol)}</b>${escapeHTML(label)}</span>`;
  }).join("");
}

function edgeMarkup(edge) {
  const startY = edge.parent.y + 49;
  const endY = edge.child.y - 49;
  const midX = (edge.parent.x + edge.child.x) / 2;
  const midY = (startY + endY) / 2;
  return `<g class="tree-edge"><line x1="${edge.parent.x}" y1="${startY}" x2="${edge.child.x}" y2="${endY}"></line><circle cx="${edge.child.x}" cy="${endY}" r="3"></circle><text x="${midX}" y="${midY - 5}">${edge.direction}</text></g>`;
}

function heapNodeMarkup(item, index, position) {
  const isPatient = selected === "patient_heap";
  const detail = isPatient
    ? `<span class="tree-node-priority p${Number(item.prioridade) || 5}">P${escapeHTML(item.prioridade)}</span><span>${escapeHTML(item.situacao || "Aguardando")}</span>`
    : `<span>${escapeHTML(item.atendimentos_concluidos || 0)} concluídos</span><span>${escapeHTML(item.situacao || "Disponível")}</span>`;
  return `<article class="tree-node heap-node${index === 0 ? " is-root" : ""}" style="left:${position.x}px;top:${position.y}px">
    <span class="node-index">#${index}${index === 0 ? " · raiz" : ""}</span>
    <strong>${escapeHTML(item.id)}</strong><span class="tree-node-label">${escapeHTML(item.nome)}</span>
    <div class="tree-node-meta">${detail}</div>
  </article>`;
}

function renderHeap(items) {
  const maxDepth = Math.floor(Math.log2(items.length));
  const bottomSlots = 2 ** maxDepth;
  const width = Math.max(780, bottomSlots * (NODE_WIDTH + 32));
  const height = Math.max(310, 145 + maxDepth * LEVEL_GAP);
  const positions = items.map((_, index) => {
    const depth = Math.floor(Math.log2(index + 1));
    const firstAtLevel = (2 ** depth) - 1;
    const slot = index - firstAtLevel;
    return { x: ((slot + 0.5) / (2 ** depth)) * width, y: 72 + depth * LEVEL_GAP };
  });
  const edges = positions.slice(1).map((child, index) => {
    const childIndex = index + 1;
    return { parent: positions[Math.floor((childIndex - 1) / 2)], child, direction: childIndex % 2 ? "E" : "D" };
  });
  return `<div class="tree-stage" style="width:${width}px;height:${height}px"><svg class="tree-edges" width="${width}" height="${height}" aria-hidden="true">${edges.map(edgeMarkup).join("")}</svg>${items.map((item, index) => heapNodeMarkup(item, index, positions[index])).join("")}</div>`;
}

function flattenTree(root) {
  const nodes = [];
  const edges = [];
  let order = 0;
  let maxDepth = 0;
  function visit(node, depth = 0, parent = null, direction = "") {
    if (!node) return;
    visit(node.esq, depth + 1, node, "E");
    const entry = { node, depth, order: order++, parent, direction };
    nodes.push(entry);
    maxDepth = Math.max(maxDepth, depth);
    visit(node.dir, depth + 1, node, "D");
  }
  visit(root);
  const byNode = new Map(nodes.map((entry) => [entry.node, entry]));
  nodes.forEach((entry) => {
    if (entry.parent) edges.push({ parent: byNode.get(entry.parent), child: entry, direction: entry.direction });
  });
  return { nodes, edges, maxDepth };
}

function balancedNodeMarkup(entry) {
  const { node, position } = entry;
  const isRedBlack = selected === "red_black";
  const color = String(node.cor || "PRETO").toLowerCase();
  const meta = isRedBlack
    ? `<span>${color === "vermelho" ? "Vermelho" : "Preto"}</span>`
    : `<span>h ${escapeHTML(node.altura)}</span><span>FB ${escapeHTML(node.fator_balanco)}</span>`;
  const className = isRedBlack ? ` rb-node rb-${color}` : " avl-node";
  return `<article class="tree-node${className}${entry.depth === 0 ? " is-root" : ""}" style="left:${position.x}px;top:${position.y}px">
    <span class="node-index">${entry.depth === 0 ? "raiz" : `nível ${entry.depth}`}</span>
    <strong>${escapeHTML(formatKey(node.chave))}</strong><span class="tree-node-label">${escapeHTML(valueLabel(node.valor))}</span>
    <div class="tree-node-meta">${meta}</div>
  </article>`;
}

function renderBalancedTree(root) {
  const tree = flattenTree(root);
  const width = Math.max(780, tree.nodes.length * (NODE_WIDTH + 30));
  const height = Math.max(310, 145 + tree.maxDepth * LEVEL_GAP);
  tree.nodes.forEach((entry) => {
    entry.position = { x: 99 + entry.order * (NODE_WIDTH + 30), y: 72 + entry.depth * LEVEL_GAP };
  });
  const edges = tree.edges.map((edge) => ({ parent: edge.parent.position, child: edge.child.position, direction: edge.direction }));
  return `<div class="tree-stage" style="width:${width}px;height:${height}px"><svg class="tree-edges" width="${width}" height="${height}" aria-hidden="true">${edges.map(edgeMarkup).join("")}</svg>${tree.nodes.map(balancedNodeMarkup).join("")}</div>`;
}

function renderHash(buckets) {
  return `<div class="hash-table-view">${buckets.map((bucket) => {
    const items = bucket.itens || [];
    const chain = items.length
      ? items.map((item, index) => `${index ? '<span class="chain-arrow">→</span>' : ""}<article class="hash-entry"><strong>${escapeHTML(item.chave)}</strong><span>${escapeHTML(valueLabel(item.valor))}</span></article>`).join("")
      : '<span class="hash-empty">∅ vazio</span>';
    return `<div class="hash-bucket-row"><div class="bucket-index"><small>bucket</small><strong>${escapeHTML(bucket.bucket_id)}</strong></div><div class="bucket-port"></div><div class="bucket-chain">${chain}</div></div>`;
  }).join("")}</div>`;
}

function countTree(node) {
  return node ? 1 + countTree(node.esq) + countTree(node.dir) : 0;
}

function render() {
  const data = structures[selected];
  const canvas = document.getElementById("structure-canvas");
  const info = metadata[selected];
  const isEmpty = !data || (Array.isArray(data) && !data.length);
  let size = 0;
  if (selected === "hash") size = (data || []).reduce((total, bucket) => total + (bucket.itens?.length || 0), 0);
  else if (["patient_heap", "doctor_heap"].includes(selected)) size = data?.length || 0;
  else size = countTree(data);

  document.getElementById("structure-title").textContent = info.label;
  document.getElementById("structure-kind").textContent = info.kind;
  document.getElementById("structure-description").textContent = info.description;
  const unit = selected === "hash" ? (size === 1 ? "registro" : "registros") : (size === 1 ? "nó" : "nós");
  document.getElementById("structure-size").textContent = `${size} ${unit}`;
  renderLegend();

  if (isEmpty && selected !== "hash") {
    canvas.innerHTML = `<div class="empty-state"><i data-lucide="network"></i><strong>Estrutura aguardando dados</strong><p>Quando houver registros associados, a topologia real aparecerá aqui.</p></div>`;
  } else if (["patient_heap", "doctor_heap"].includes(selected)) {
    canvas.innerHTML = renderHeap(data);
  } else if (selected === "hash") {
    canvas.innerHTML = renderHash(data || []);
  } else {
    canvas.innerHTML = renderBalancedTree(data);
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
    button.classList.add("is-active");
    selected = button.dataset.structure;
    render();
  }));
  await load();
  autoRefresh(load, 15000);
}
