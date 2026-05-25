---
name: sdd-workflow
description: Use quando o repositorio seguir Spec-Driven Development e a tarefa tocar sdd numerados, batches, reviews, validation, decisions ou change requests.
user-invocable: false
---

# SDD workflow

Use esta skill sempre que a tarefa depender do modelo SDD do Nexus.

## Leitura minima inicial

Comece por:

- [sdd index](../../../sdd/README.md)
- [start here](../../../sdd/process/00-START-HERE.md)
- [workflow](../../../sdd/process/01-WORKFLOW.md)
- [batch index](../../../sdd/implementation/BATCH-INDEX.md)
- [validation checklist](../../../sdd/validation/VALIDATION-CHECKLIST.md)
- [decision log](../../../sdd/decisions/DECISION-LOG.md)

Depois leia apenas os sdd numerados e arquivos de codigo que controlam o slice atual.

Se a tarefa apontar para `sdd/human-requests/*.md` ou para a pasta `sdd/human-requests/`, leia primeiro esse intake humano. Quando vier apenas a pasta, use a seguinte ordem deterministica:

1. `CURRENT.md`
2. `README.md`
3. o arquivo `.md` mais recente

## Classificacao da demanda

1. Mudanca de requisito ou contrato:
   - registre em `sdd/change-requests/`
   - avalie impacto nos sdd numerados, decisions, batches e validation
   - so depois parta para implementacao
2. Feedback de review sem mudanca normativa:
   - registre em `sdd/reviews/`
   - mantenha os sdd numerados estaveis
3. Implementacao incremental:
   - confira o batch atual em `sdd/implementation/`
   - implemente o menor slice aprovado
   - valide e atualize `sdd/validation/` quando necessario
4. Validacao ou spec drift check:
   - comece pela menor checagem automatizada
   - registre evidencia e pendencias nos artefatos certos

## Regras de ouro

- Os sdd numerados sao a fonte normativa.
- `sdd/human-requests/` nunca e fonte normativa; ele so alimenta change requests, reviews, batches, decisions ou validacao.
- Nao reescreva os sdd numerados para comentarios pequenos de review.
- Nao abra o proximo batch antes de o atual estar estavel e revisavel.
- Quando houver duvida entre mudar sdd ou nao, trate primeiro como change request ou review, nao como edicao direta do sdd numerado.