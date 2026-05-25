---
name: 'Nexus SDD'
description: 'Use ao editar sdd, reviews, batches, change requests, decisions ou validacao no Conn2Flow Nexus.'
applyTo: 'sdd/**/*.md'
---

- Os arquivos numerados em `sdd/00-*.md` a `sdd/10-*.md` sao a fonte normativa.
- Trate `sdd/human-requests/` apenas como intake humano nao normativo; qualquer consolidacao deve ir para `sdd/change-requests/`, `sdd/reviews/`, `sdd/implementation/`, `sdd/validation/`, `sdd/decisions/` ou para os sdd numerados quando aprovado.
- Use `sdd/change-requests/` para mudanca de requisito, `sdd/reviews/` para feedback de round, `sdd/implementation/` para batches, `sdd/validation/` para evidencias e `sdd/decisions/` para racional.
- Nao mova comentario de review para os sdd numerados se o requisito nao mudou.
- Quando atualizar batches, validacao ou decisoes, mantenha consistencia entre escopo, status e evidencia.