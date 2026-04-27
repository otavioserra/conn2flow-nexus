---
name: continue-sdd-batch
description: Retoma trabalho no batch atual do Conn2Flow Nexus sem perder o contexto dos specs e artefatos incrementais.
agent: nexus-sdd-coordinator
argument-hint: 'Opcionalmente descreva o que mudou desde a ultima rodada.'
---

Retome o trabalho considerando:

- specs numerados relevantes
- batch atual
- decisions e validation ligadas ao slice
- arquivos alterados manualmente desde a ultima rodada

Se o usuario mudou arquivos ou premissas, releia primeiro esse material antes de continuar.

Atualizacao:

${input:update:Sem atualizacao adicional}