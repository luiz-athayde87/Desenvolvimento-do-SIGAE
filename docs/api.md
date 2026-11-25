# API HTTP

Base URL: `/api/v1`. Respostas de sucesso usam `{ "data": ... }`; erros usam `error.code`, `error.message` e, quando aplicável, `error.fields`.

## Estado e saúde

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | verifica aplicação e banco |
| `GET` | `/state` | retorna pacientes, médicos, fila, atendimentos, auditoria e estruturas |
| `GET` | `/search?q=termo` | pesquisa pacientes e médicos; mínimo de 2 caracteres |
| `GET` | `/structures` | retorna a inspeção atual das estruturas de dados |

## Pacientes e médicos

| Método | Rota | Papel quando autenticado |
|---|---|---|
| `GET` | `/patients?q=&status=&priority=&page=&per_page=` | lista e filtra pacientes com paginação |
| `POST` | `/patients` | recepção, enfermagem ou administrador |
| `GET` | `/patients/{id}` | leitura pública no modo atual |
| `PATCH` | `/patients/{id}/priority` | enfermagem ou administrador |
| `POST` | `/patients/{id}/complete` | médico, enfermagem ou administrador |
| `POST` | `/patients/{id}/cancel` | recepção, enfermagem ou administrador |
| `GET` | `/doctors?q=&status=` | lista e filtra o corpo médico |
| `POST` | `/doctors` | administrador |
| `PATCH` | `/doctors/{id}/status` | administrador |

Exemplo de cadastro:

```json
{
  "id": "P90",
  "nome": "Paciente Exemplo",
  "queixa": "Dor abdominal",
  "prioridade": 2
}
```

O ID é opcional. IDs de pacientes começam por `P` ou `PAC-`; IDs de médicos começam por `M` ou `MED-`.

## Atendimentos e relatórios

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/attendances/call-next` | associa o próximo paciente ao médico elegível |
| `GET` | `/history?page=&per_page=` | retorna o histórico paginado |
| `GET` | `/reports/summary` | retorna os indicadores operacionais atuais |
| `GET` | `/reports/shift.csv` | exporta o estado do plantão em UTF-8 |
| `POST` | `/reset` | restaura os dados de demonstração; administrador |

## Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/login` | inicia sessão e retorna token CSRF |
| `GET` | `/auth/me` | informa a sessão atual |
| `POST` | `/auth/logout` | encerra a sessão |
| `GET` | `/auth/users` | lista usuários; administrador |
| `POST` | `/auth/users` | cria usuário; administrador |
| `PATCH` | `/auth/users/{id}/active` | ativa ou desativa usuário; administrador |

Quando a autenticação está ativa, inclua `X-CSRF-Token` em `POST`, `PATCH`, `PUT` e `DELETE`. Cookies devem ser enviados pelo cliente HTTP. A sessão expira após oito horas de inatividade e o login limita tentativas repetidas por endereço de origem.

Todos os timestamps operacionais são instantes reais. Campos com sufixo `_iso` usam UTC no formato ISO 8601; tempos de espera e duração são calculados no momento da consulta.

O contrato completo e importável por ferramentas como Swagger Editor e Postman está em `docs/openapi.yaml`.
