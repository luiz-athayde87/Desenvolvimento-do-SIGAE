# API HTTP

Base URL: `/api/v1`. Respostas de sucesso usam `{ "data": ... }`; erros usam `error.code`, `error.message` e, quando aplicável, `error.fields`.

## Estado e saúde

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | verifica aplicação e banco |
| `GET` | `/state` | retorna pacientes, médicos, fila, atendimentos, auditoria e estruturas |
| `GET` | `/search?q=termo` | pesquisa pacientes e médicos; mínimo de 2 caracteres |

## Pacientes e médicos

| Método | Rota | Papel quando autenticado |
|---|---|---|
| `POST` | `/patients` | recepção, enfermagem ou administrador |
| `GET` | `/patients/{id}` | leitura pública no modo atual |
| `PATCH` | `/patients/{id}/priority` | enfermagem ou administrador |
| `POST` | `/patients/{id}/complete` | médico, enfermagem ou administrador |
| `POST` | `/patients/{id}/cancel` | recepção, enfermagem ou administrador |
| `POST` | `/doctors` | administrador |

Exemplo de cadastro:

```json
{
  "id": "P90",
  "nome": "Paciente Exemplo",
  "prioridade": 2
}
```

O ID é opcional. IDs de pacientes começam por `P` ou `PAC-`; IDs de médicos começam por `M` ou `MED-`.

## Atendimentos e relatórios

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/attendances/call-next` | associa o próximo paciente ao médico elegível |
| `GET` | `/reports/shift.csv` | exporta o estado do plantão em UTF-8 |
| `POST` | `/reset` | restaura os dados de demonstração; administrador |

## Autenticação

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/login` | inicia sessão e retorna token CSRF |
| `GET` | `/auth/me` | informa a sessão atual |
| `POST` | `/auth/logout` | encerra a sessão |

Quando a autenticação está ativa, inclua `X-CSRF-Token` em `POST`, `PATCH`, `PUT` e `DELETE`. Cookies devem ser enviados pelo cliente HTTP.

O contrato completo e importável por ferramentas como Swagger Editor e Postman está em `docs/openapi.yaml`.
