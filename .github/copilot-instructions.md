# Nexus MDD Guidelines

- Este repositorio usa desenvolvimento orientado por especificacoes. A fonte normativa e [memory/README.md](../memory/README.md) junto dos arquivos numerados em [sdd](../memory).
- Antes de editar codigo ou sdd, leia [memory/README.md](../memory/README.md), [process/00-START-HERE.md](../memory/process/00-START-HERE.md), [process/01-WORKFLOW.md](../memory/process/01-WORKFLOW.md), [implementation/BATCH-INDEX.md](../memory/implementation/BATCH-INDEX.md), o batch atual, [validation/VALIDATION-CHECKLIST.md](../memory/validation/VALIDATION-CHECKLIST.md) e [decisions/DECISION-LOG.md](../memory/decisions/DECISION-LOG.md).
- Use [memory/human-requests/](../memory/human-requests/README.md) apenas como intake humano nao normativo. Se a demanda vier como arquivo Markdown ou como a propria pasta, leia esse material primeiro e depois classifique a demanda no artefato MDD correto.
- Classifique a demanda cedo: mudanca de requisito, implementacao de batch, review de entrega, ou validacao.
- Nao reescreva os sdd numerados para comentarios de review ou pequenos ajustes de implementacao; use `memory/change-requests/`, `memory/reviews/`, `memory/implementation/`, `memory/validation/` e `memory/decisions/`.
- Edite os sdd numerados apenas quando requisito, contrato, criterio de aceite ou decisao aprovada realmente mudar.
- Mantenha o trabalho em batches pequenos, com alvo de validacao explicito.
- Este repo nao usa a logica de `conn2flow-site` versus `conn2flow`, nem heuristicas de `gestor`/PHP. Nao importe esse contexto aqui.
- Para decidir como registrar trabalho dentro do modelo MDD, use a skill [sdd-workflow](./skills/sdd-workflow/SKILL.md).
- Para validacao local de pytest e Docker Compose, use a skill [nexus-validation](./skills/nexus-validation/SKILL.md).
- O hook [nexus-sdd-session-start.json](./hooks/nexus-sdd-session-start.json) injeta um lembrete curto de MDD no inicio da sessao; mantenha esse hook pequeno e previsivel.