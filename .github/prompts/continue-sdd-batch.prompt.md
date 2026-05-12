---
name: continue-sdd-batch
description: Retoma trabalho no batch atual do Conn2Flow Nexus sem perder o contexto dos specs e artefatos incrementais.
agent: nexus-sdd-coordinator
argument-hint: 'Opcionalmente descreva o que mudou ou passe um .md em specs/human-requests/.'
---

Retome o trabalho considerando:

- specs numerados relevantes
- batch atual
- decisions e validation ligadas ao slice
- arquivos alterados manualmente desde a ultima rodada

Se o usuario mudou arquivos ou premissas, releia primeiro esse material antes de continuar.
Se a atualizacao vier como caminho em `specs/human-requests/`, releia primeiro esse intake humano. Se vier apenas a pasta, use `CURRENT.md`, depois `README.md`, depois o `.md` mais recente.

Atualizacao:

${input:update:Sem atualizacao adicional}