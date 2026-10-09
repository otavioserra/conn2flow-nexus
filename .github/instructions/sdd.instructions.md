---
name: 'Nexus MDD'
description: 'Use ao editar sdd, reviews, batches, change requests, decisions ou validacao no Conn2Flow Nexus.'
applyTo: 'memory/**/*.md'
---

- Os arquivos numerados em `memory/00-*.md` a `memory/10-*.md` sao a fonte normativa.
- Trate `memory/human-requests/` apenas como intake humano nao normativo; qualquer consolidacao deve ir para `memory/change-requests/`, `memory/reviews/`, `memory/implementation/`, `memory/validation/`, `memory/decisions/` ou para os sdd numerados quando aprovado.
- Use `memory/change-requests/` para mudanca de requisito, `memory/reviews/` para feedback de round, `memory/implementation/` para batches, `memory/validation/` para evidencias e `memory/decisions/` para racional.
- Nao mova comentario de review para os sdd numerados se o requisito nao mudou.
- Quando atualizar batches, validacao ou decisoes, mantenha consistencia entre escopo, status e evidencia.