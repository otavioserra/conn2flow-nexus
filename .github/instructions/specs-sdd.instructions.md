---
name: 'Nexus SDD Specs'
description: 'Use ao editar specs, reviews, batches, change requests, decisions ou validacao no Conn2Flow Nexus.'
applyTo: 'specs/**/*.md'
---

- Os arquivos numerados em `specs/00-*.md` a `specs/10-*.md` sao a fonte normativa.
- Trate `specs/human-requests/` apenas como intake humano nao normativo; qualquer consolidacao deve ir para `specs/change-requests/`, `specs/reviews/`, `specs/implementation/`, `specs/validation/`, `specs/decisions/` ou para os specs numerados quando aprovado.
- Use `specs/change-requests/` para mudanca de requisito, `specs/reviews/` para feedback de round, `specs/implementation/` para batches, `specs/validation/` para evidencias e `specs/decisions/` para racional.
- Nao mova comentario de review para os specs numerados se o requisito nao mudou.
- Quando atualizar batches, validacao ou decisoes, mantenha consistencia entre escopo, status e evidencia.