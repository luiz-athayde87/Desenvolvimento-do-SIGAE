<div align="center">

# 🏥 SIGAE — Sistema Inteligente de Gerenciamento de Atendimentos de Emergência

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-black?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.org/)
[![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)](https://developer.mozilla.org/pt-BR/docs/Web/HTML)
[![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=for-the-badge&logo=css3&logoColor=white)](https://developer.mozilla.org/pt-BR/docs/Web/CSS)
[![Status](https://img.shields.io/badge/Status-Conclu%C3%ADdo-brightgreen?style=for-the-badge)]()

*Uma aplicação web robusta para triagem hospitalar, alocação equitativa de médicos e auditoria cronológica baseada em Estruturas de Dados Avançadas nativas.*

[Visão Geral](#-visão-geral) • [Triagem de Risco](#-protocolo-de-triagem-de-risco) • [Estruturas de Dados](#%EF%B8%8F-arquitetura-e-estruturas-de-dados) • [Como Executar](#-como-executar) • [API REST](#-endpoints-da-api-rest) • [Inspetor Visual](#-inspetor-visual-de-memória)

</div>

---

## 📖 Visão Geral

O **SIGAE** foi desenvolvido para responder aos desafios operacionais de Unidades de Pronto Atendimento (UPAs) e hospitais. O sistema simula o fluxo completo de atendimento de emergência: desde o cadastro na recepção, passando pelo protocolo de triagem clínica de risco e distribuição justa da carga de trabalho médica, até o registro cronológico auditável das consultas.

> ⚡ **Diferencial Técnico:** O backend **não utiliza bibliotecas utilitárias pré-prontas de estruturas de dados** (como `heapq` ou dicionários nativos para prioridade). Todas as estruturas — **Min-Heap Binário**, **Tabela Hash com Encadeamento**, **Árvore AVL** e **Árvore Rubro-Negra** — foram implementadas de forma nativa e pura em Python.

---

## 🎨 Protocolo de Triagem de Risco

A classificação de risco segue o protocolo visual hospitalar de triagem:

| Nível | Classificação | Cor Visual | Código Hex | Descrição Operacional |
| :---: | :--- | :---: | :---: | :--- |
| **1** | **Emergência** | 🔴 Vermelho | `#dc2626` | Risco iminente de morte (Atendimento Imediato) |
| **2** | **Muito Urgente** | 🔴 Vermelho | `#dc2626` | Caso gravíssimo (Prioridade Máxima) |
| **3** | **Urgente** | 🟡 Amarelo | `#eab308` | Atendimento Rápido |
| **4** | **Pouco Urgente** | 🟢 Verde | `#16a34a` | Atendimento Ambulatorial Padrão |
| **5** | **Não Urgente** | 🟢 Verde | `#16a34a` | Consulta Eletiva / Sintomas Leves |

---

## 🏗️ Arquitetura e Estruturas de Dados

```text
                         [ PAINEL WEB FLASK ]
                                  │
      ┌───────────────────────────┼───────────────────────────┐
      ▼                           ▼                           ▼
[ TABELA HASH ]          [ MIN-HEAP CLÍNICO ]        [ MIN-HEAP MÉDICO ]
Busca O(1) por ID        Fila de Risco O(log n)      Equidade de Carga O(log n)
      │                           │                           │
      └───────────────────────────┼───────────────────────────┘
                                  ▼
                     [ ÁRVORE RUBRO-NEGRA / AVL ]
                      Histórico em O(log n)

---

### 🧠 Matriz de Decisão e Complexidade Computacional

| Estrutura de Dados | Papel no SIGAE | Complexidade (Médio) | Complexidade (Pior Caso) | Justificativa de Escolha Técnica |
| :--- | :--- | :---: | :---: | :--- |
| **Tabela Hash** | Cadastro e Busca por ID | `O(1)` | `O(n)` | Acesso instantâneo sem varredura linear. Trata colisões por encadeamento (*separate chaining*). |
| **Min-Heap (Pacientes)** | Fila de Prioridade Clínica | `O(1)` topo | `O(log n)` | Mantém o paciente com maior gravidade (menor valor 1–5) na raiz. Desempate por horário (FIFO) e ID. |
| **Min-Heap (Médicos)** | Balanceamento de Carga Médica | `O(1)` topo | `O(log n)` | Seleciona automaticamente o médico disponível com o **menor número de atendimentos concluídos**. |
| **Árvore Rubro-Negra** | Histórico Cronológico | `O(log n)` | `O(log n)` | Balanceamento relaxado por cores (Red/Black). Otimizada para inserções frequentes com poucas rotações. |
| **Árvore AVL** | Índice de Consulta de Alta Frequência | `O(log n)` | `O(log n)` | Balanceamento rígido por Fator de Balanço (`|FB| <= 1`). Garante altura mínima para buscas em tempo recorde. |

---

## 📁 Estrutura do Repositório

```text
sigae/
├── main.py                   # Servidor Flask, API REST e Orquestrador
├── tabela_hash.py            # Implementação da Tabela Hash O(1) com Encadeamento
├── heap_pacientes.py         # Min-Heap Binário para Fila de Triagem de Risco
├── heap_medicos.py           # Min-Heap Binário para Equidade de Carga Médica
├── arvore_rubro_negra.py     # Árvore Rubro-Negra para Histórico Cronológico
├── arvore_avl.py             # Árvore AVL para Consultas de Leitura Otimizada
├── templates/
│   └── index.html            # Interface Gráfica Responsiva + Inspetor Visual de Memória
├── sigae_flask_project.zip   # Pacote ZIP completo do projeto
└── README.md                 # Documentação do repositório
