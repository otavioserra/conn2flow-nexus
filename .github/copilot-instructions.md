# Nexus SDD Guidelines

- Este repositorio usa desenvolvimento orientado por especificacoes. A fonte normativa e [specs/README.md](../specs/README.md) junto dos arquivos numerados em [specs](../specs).
- Antes de editar codigo ou specs, leia [specs/README.md](../specs/README.md), [process/00-START-HERE.md](../specs/process/00-START-HERE.md), [process/01-WORKFLOW.md](../specs/process/01-WORKFLOW.md), [implementation/BATCH-INDEX.md](../specs/implementation/BATCH-INDEX.md), o batch atual, [validation/VALIDATION-CHECKLIST.md](../specs/validation/VALIDATION-CHECKLIST.md) e [decisions/DECISION-LOG.md](../specs/decisions/DECISION-LOG.md).
- Classifique a demanda cedo: mudanca de requisito, implementacao de batch, review de entrega, ou validacao.
- Nao reescreva os specs numerados para comentarios de review ou pequenos ajustes de implementacao; use `specs/change-requests/`, `specs/reviews/`, `specs/implementation/`, `specs/validation/` e `specs/decisions/`.
- Edite os specs numerados apenas quando requisito, contrato, criterio de aceite ou decisao aprovada realmente mudar.
- Mantenha o trabalho em batches pequenos, com alvo de validacao explicito.
- Este repo nao usa a logica de `conn2flow-site` versus `conn2flow`, nem heuristicas de `gestor`/PHP. Nao importe esse contexto aqui.
- Para decidir como registrar trabalho dentro do modelo SDD, use a skill [sdd-workflow](./skills/sdd-workflow/SKILL.md).
- Para validacao local de pytest e Docker Compose, use a skill [nexus-validation](./skills/nexus-validation/SKILL.md).
- O hook [nexus-sdd-session-start.json](./hooks/nexus-sdd-session-start.json) injeta um lembrete curto de SDD no inicio da sessao; mantenha esse hook pequeno e previsivel.