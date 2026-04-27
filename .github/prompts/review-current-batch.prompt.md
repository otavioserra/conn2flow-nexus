---
name: review-current-batch
description: Revisa o batch atual do Conn2Flow Nexus com foco em spec drift, batch drift, bugs e validacao.
agent: nexus-sdd-reviewer
argument-hint: 'Opcionalmente cite arquivos, comportamento esperado ou risco suspeito.'
---

Revise a mudanca mais recente do batch atual.

Regras da resposta:

1. Liste findings primeiro, por severidade.
2. Verifique aderencia aos specs numerados e ao batch atual.
3. Aponte validacao ausente e drift entre testes, codigo e artefatos SDD.
4. Se nao houver findings, diga isso explicitamente e registre riscos residuais.

Contexto adicional:

${input:context:Sem contexto adicional}