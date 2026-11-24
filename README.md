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
