# Changelog

Todas as mudanças relevantes do projeto são documentadas neste arquivo.

## [1.2.0] - 2026-11-25

### Adicionado

- visualização canônica das estruturas: heaps binários completos, topologias AVL e Rubro-Negra e buckets encadeados da Tabela Hash;
- identificação visual de raiz, níveis, filhos esquerdo/direito, índices, alturas, fatores de balanceamento e cores reais dos nós.

### Alterado

- README reorganizado como apresentação completa do produto, com rotas, arquitetura, execução, qualidade e segurança;
- exportação da Árvore Rubro-Negra passa a preservar a topologia real dos nós.

### Corrigido

- centralização dos ícones nos indicadores da fila de atendimento.

## [1.1.0] - 2026-11-25

### Adicionado

- nove páginas independentes e focadas para reduzir a carga cognitiva do painel;
- relógio local em tempo real, timestamps UTC reais e atualização automática;
- filtros, paginação, gestão do corpo médico, histórico e relatórios operacionais;
- gestão de usuários, expiração de sessão e limitação de tentativas de login;
- migrações versionadas de banco para especialidade e queixa principal;
- testes de jornada no Chromium, CodeQL e auditoria automática de dependências.

### Alterado

- frontend monolítico substituído por shell, design system e módulos JavaScript por página;
- experiência responsiva revisada para desktop, tablet e celular;
- imagem Docker passa a incluir os recursos estáticos do painel.

## [1.0.0] - 2026-11-25

### Adicionado

- dashboard profissional responsivo e integrado à API;
- persistência SQLite e trilha de auditoria;
- API REST versionada, busca e relatório CSV;
- autenticação por sessão, papéis e proteção CSRF opcionais;
- Docker, healthcheck, Waitress e observabilidade HTTP;
- testes automatizados, cobertura mínima e CI em múltiplas versões do Python;
- documentação de arquitetura, API, segurança e contribuição.

### Corrigido

- exportação recursiva da Árvore AVL;
- duplicidade e complexidade operacional dos Min-Heaps;
- hashing não determinístico e ausência de redimensionamento;
- divergência entre o estado do frontend e do backend.
