# Política de segurança

## Versões suportadas

Enquanto o projeto estiver em desenvolvimento, apenas a versão mais recente da branch `main` recebe correções de segurança.

## Relatar uma vulnerabilidade

Não publique detalhes exploráveis em uma issue aberta. Use o recurso **Security > Report a vulnerability** do repositório GitHub. Inclua impacto, passos mínimos para reprodução e uma sugestão de correção, se disponível.

Evite dados pessoais, credenciais reais ou informações clínicas no relatório. Uma confirmação deve ser enviada depois da triagem; prazos de correção dependem da gravidade e da disponibilidade dos mantenedores.

## Operação segura

- substitua `SIGAE_SECRET_KEY` e `SIGAE_DEMO_PASSWORD`;
- defina `SIGAE_ENV=production` e `SIGAE_AUTH_REQUIRED=true`;
- use HTTPS por meio de um proxy reverso;
- restrinja permissões do volume SQLite e dos backups;
- não utilize dados reais: este projeto é somente um simulador educacional.
