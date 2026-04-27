---
name: 'Nexus Source Python'
description: 'Use ao editar codigo Python em src/ no Conn2Flow Nexus.'
applyTo: 'src/**/*.py'
---

- Antes de mudar comportamento, releia o spec numerado e o batch que controlam esse slice.
- Preserve os padroes async de FastAPI, httpx, Redis, Kafka, LangGraph e Pydantic v2 ja usados no repositorio.
- Prefira mudancas locais no modulo que decide o comportamento em vez de refatoracoes amplas.
- Se a demanda implicar contrato novo ou requisito diferente, registre a mudanca no fluxo SDD antes de ampliar o codigo.
- Depois da primeira edicao substantiva, rode o menor pytest capaz de falsificar a mudanca antes do suite completo.