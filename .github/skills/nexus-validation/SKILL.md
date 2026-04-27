---
name: nexus-validation
description: Use quando validar mudancas no Conn2Flow Nexus com pytest, Docker Compose, healthcheck e smoke flow orientado pelos batches e pela validation checklist.
---

# Nexus validation

Use esta skill para validar mudancas no Nexus respeitando o fluxo SDD.

## Ordem recomendada

1. Leia [validation checklist](../../../specs/validation/VALIDATION-CHECKLIST.md) e [batch index](../../../specs/implementation/BATCH-INDEX.md).
2. Rode primeiro o menor pytest coerente com o batch ativo.
3. Amplie para `pytest -q` quando o slice local estiver estavel.
4. So depois parta para validacao de stack com Docker Compose quando o batch realmente pedir isso.

## Comandos uteis atuais

- Batch 001 focado: `pytest tests/test_security.py tests/test_delivery_worker.py -q`
- Regressao local: `pytest -q`
- Stack local: `docker compose up -d`
- Saude dos servicos: `docker compose ps`
- Health endpoint: `curl http://localhost:8000/api/v1/health`

## Regras

- Use o ambiente Python configurado do repo antes de rodar `pytest`.
- Se o batch atual nao exigir stack real, nao pule direto para Docker Compose.
- Quando uma validacao relevante for concluida, atualize a evidencia em `specs/validation/VALIDATION-CHECKLIST.md` se a tarefa pedir consolidacao documental.