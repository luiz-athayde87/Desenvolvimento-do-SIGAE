# Relatório de conformidade e roteiro de defesa

Este documento relaciona o enunciado acadêmico do SIGAE WEB à implementação executável e às evidências automatizadas do repositório.

## Matriz de conformidade

| Critério | Implementação | Evidência |
|---|---|---|
| Rubro-Negra | Índice de pacientes aguardando por `(chegada, ID)`, com busca, percurso, inserção e remoção balanceadas | `arvore_rubro_negra.py` e testes adversariais em `tests/test_structures.py` |
| Heap de pacientes | Min-Heap próprio por prioridade, chegada e ID | `heap_pacientes.py` e testes de prioridade, FIFO, desempate e reclassificação |
| Heap de médicos | Min-Heap próprio por carga, tempo ocioso e ID | `heap_medicos.py` e cenários de distribuição equilibrada |
| Tabela Hash | FNV-1a, encadeamento separado, consulta, remoção e redimensionamento | `tabela_hash.py` e testes de colisão deliberada |
| Integração | Cadastro, chamada, vínculo, conclusão, cancelamento e reconstrução consistente dos índices | `sigae/service.py` e `tests/test_evaluation_scenarios.py` |
| Interface web | Rotas independentes para visão geral, pacientes, triagem, fila, médicos, histórico e estruturas | `templates/pages`, `static/js/pages` e testes de rotas |
| Persistência | SQLite, transações, migrações e auditoria | `sigae/database.py` e `tests/test_persistence.py` |
| Qualidade | 31 testes, cobertura superior a 85%, Ruff, E2E e workflows de CI | `pyproject.toml`, `tests`, `e2e` e `.github/workflows` |

## Regras de ordenação

### Pacientes

1. Menor classificação de risco, de P1 a P5.
2. Horário de chegada mais antigo.
3. Menor ID.

### Médicos

1. Menor quantidade de atendimentos concluídos.
2. Maior tempo sem receber paciente, representado pelo menor instante de último atendimento.
3. Menor ID.

## Justificativa dos mecanismos auxiliares

As estruturas exigidas são implementadas do zero. Os dicionários armazenam somente os campos das entidades. O mapa `_indices` do heap de pacientes associa ID à posição no vetor para permitir reclassificação e remoção em `O(log n)`; ele não determina prioridade nem substitui o heap. Não são utilizados `heapq`, bibliotecas prontas de árvores ou mapas como implementação principal.

## Roteiro reproduzível para a defesa

1. Reinicie a demonstração em **Configurações > Restaurar dados**.
2. Abra **Estruturas** e mostre os dois heaps, a Tabela Hash e a Rubro-Negra de chegadas.
3. Cadastre um paciente e confirme a inserção no heap, na Hash e na Rubro-Negra.
4. Reclassifique o paciente e mostre sua nova posição no heap sem duplicidade.
5. Chame pacientes sucessivamente e confirme a escolha de M101, M102 e M103 enquanto os médicos anteriores permanecem ocupados.
6. Tente chamar outro paciente sem médico disponível e confirme que ele continua na fila.
7. Conclua um atendimento e demonstre o incremento da carga e o retorno do médico ao heap.
8. Cancele um atendimento e confirme que o médico é liberado sem incremento da contagem.
9. Mostre que a saída de um paciente remove sua chave da Rubro-Negra e mantém as propriedades de balanceamento.
10. Execute a suíte automatizada para reproduzir todos os cenários.

## Comandos de evidência

```bash
python -m ruff check .
python -m pytest
python -m pytest --cov --cov-report=term-missing
```

O sucesso esperado é: nenhuma violação de qualidade, 31 testes aprovados e cobertura total acima de 85%.
