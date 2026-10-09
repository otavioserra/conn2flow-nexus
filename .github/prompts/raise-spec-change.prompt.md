---
name: raise-spec-change
description: Abre ou atualiza uma mudanca de requisito no fluxo MDD do Conn2Flow Nexus antes de partir para implementacao.
agent: nexus-sdd-coordinator
argument-hint: 'Descreva a mudanca de requisito ou passe um .md em memory/human-requests/.'
---

Para a mudanca abaixo:

1. Se a mudanca vier como caminho em `memory/human-requests/`, leia primeiro esse intake humano. Se vier apenas a pasta, use `CURRENT.md`, depois `README.md`, depois o `.md` mais recente.
2. Identifique quais sdd numerados seriam impactados.
3. Avalie se a mudanca deve entrar em `memory/change-requests/`, `memory/decisions/` e `memory/implementation/`.
4. Proponha o menor change request coerente com o fluxo atual.
5. Nao implemente codigo ate a mudanca normativa ficar explicita.

Mudanca proposta:

${input:change:Descreva a mudanca}