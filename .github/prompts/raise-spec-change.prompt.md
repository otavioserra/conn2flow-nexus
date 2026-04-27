---
name: raise-spec-change
description: Abre ou atualiza uma mudanca de requisito no fluxo SDD do Conn2Flow Nexus antes de partir para implementacao.
agent: nexus-sdd-coordinator
argument-hint: 'Descreva a mudanca de requisito, contrato ou criterio de aceite.'
---

Para a mudanca abaixo:

1. Identifique quais specs numerados seriam impactados.
2. Avalie se a mudanca deve entrar em `specs/change-requests/`, `specs/decisions/` e `specs/implementation/`.
3. Proponha o menor change request coerente com o fluxo atual.
4. Nao implemente codigo ate a mudanca normativa ficar explicita.

Mudanca proposta:

${input:change:Descreva a mudanca}