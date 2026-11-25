# Arquitetura do SIGAE

## Objetivos

O projeto separa apresentação, contrato HTTP, regras de domínio, persistência e índices em memória. Essa divisão impede que o navegador mantenha uma versão concorrente do estado e torna os fluxos testáveis sem interface gráfica.

## Componentes

| Camada | Responsabilidade |
|---|---|
| `templates/base.html` | shell compartilhado, navegação, busca global e autenticação |
| `templates/pages/*.html` | página focada para cada área operacional |
| `static/css/app.css` | design system responsivo e acessível |
| `static/js/core.js` | relógio real, sessão, busca e inicialização do módulo da página |
| `static/js/pages/*.js` | comportamento isolado de cada área, sem estado concorrente |
| `sigae/api.py` | contrato REST, serialização, CSV e erros estruturados |
| `sigae/service.py` | invariantes do fluxo de atendimento e sincronização das estruturas |
| `sigae/database.py` | esquema, transações SQLite, índices e auditoria |
| `sigae/auth.py` | login, sessão, papéis e proteção CSRF |
| estruturas na raiz | filas, busca e histórico implementados sem bibliotecas prontas |

## Fonte única de verdade

O SQLite é o registro durável e possui migrações versionadas. Depois de cada alteração, o serviço reconstrói os índices em memória a partir de uma transação confirmada. Essa estratégia privilegia clareza e consistência no simulador; em escala real, a reconstrução completa seria substituída por atualizações incrementais e um banco cliente-servidor.

## Tempo e atualização

O sistema não avança mais um relógio artificial. Cadastros, filas, atendimentos, relatórios e auditoria usam Unix epoch/UTC reais no servidor; a interface exibe o relógio local do dispositivo a cada segundo. As áreas operacionais consultam novamente a API em intervalos de 8 a 15 segundos e imediatamente depois de cada mutação.

## Regras centrais

1. Pacientes aguardando são ordenados por prioridade, chegada e ID.
2. Apenas médicos disponíveis participam do heap de distribuição.
3. A distribuição escolhe a menor carga concluída, o maior tempo ocioso e o ID.
4. Um paciente só pode ser concluído quando está em atendimento.
5. Cancelar um atendimento libera o médico associado.
6. Toda mudança relevante gera um evento de auditoria.

## Segurança

Quando `SIGAE_AUTH_REQUIRED=true`, as mutações exigem sessão, papel compatível e token CSRF. A aplicação usa sessões com expiração, limitação de tentativas de login, cookies `HttpOnly`, `SameSite=Lax`, `Secure` em produção, CSP, bloqueio de enquadramento, política de permissões e respostas de API sem cache.

As rotas antigas em `/api/*` existem apenas para migração e obedecem às mesmas regras de autorização. Novos consumidores devem usar exclusivamente `/api/v1/*`.

## Observabilidade

Cada resposta inclui `X-Request-ID`; a aplicação registra método, rota, status e duração. `Server-Timing` permite inspecionar latência no navegador. O healthcheck consulta o banco, e não apenas o processo HTTP.

## Decisões e limites

- SQLite atende demonstração e implantação de uma única instância. Múltiplas réplicas exigiriam PostgreSQL ou equivalente.
- A interface permanece sem framework para manter o foco acadêmico nas estruturas de dados.
- Os horários são reais, mas os dados clínicos continuam demonstrativos e não implementam protocolos, interoperabilidade ou requisitos regulatórios de um sistema hospitalar real.
