# Contribuindo

## Preparação

Crie um ambiente virtual com Python 3.11 ou superior e instale `requirements-dev.txt`. Abra uma branch curta e focada a partir de `main`.

## Antes do commit

```bash
python -m ruff check .
python -m pytest --cov --cov-report=term-missing
```

O projeto exige cobertura global mínima de 85%. Novos fluxos precisam de testes de sucesso e de erro. Não versione `.env`, bancos, logs, dados pessoais ou credenciais.

## Commits e pull requests

Prefira commits pequenos no formato `tipo: descrição`, por exemplo `feat: adiciona filtro de prioridade` ou `fix: libera médico após cancelamento`. A pull request deve explicar o problema, a solução, a validação executada e qualquer decisão de UX ou segurança.

Mudanças no contrato HTTP devem atualizar `docs/api.md`, `docs/openapi.yaml` e os testes correspondentes.
