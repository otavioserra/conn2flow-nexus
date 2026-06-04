---
paths:
  - "sdd/**/*.md"
---

# Regras de artefatos SDD

- Os sdd numerados são a fonte normativa.
- Trate `sdd/human-requests/` apenas como intake humano não normativo; qualquer consolidação deve ir para `change-requests/`, `reviews/`, `implementation/`, `validation/`, `decisions/` ou sdd numerados quando aprovado.
- Use `sdd/change-requests/` para mudança de requisito, `sdd/reviews/` para feedback de round, `sdd/implementation/` para batches, `sdd/validation/` para evidências e `sdd/decisions/` para racional.
- Não reescreva os sdd numerados para comentários de review que não mudam o requisito.
- No início de cada sessão, leia `sdd/MEMORIA-ENGENHARIA-CHEFIA.md` e `sdd/MEMORIA-ENGENHARIA-EXECUCAO.md` para alinhar contexto.
- Ao término de cada tarefa, atualize `sdd/MEMORIA-ENGENHARIA-EXECUCAO.md` com aprendizados, bugs resolvidos e particularidades do ambiente. Nunca modifique `sdd/MEMORIA-ENGENHARIA-CHEFIA.md` sem instrução explícita do usuário humano.