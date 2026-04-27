---
name: sdd-workflow
description: Use quando o repositorio seguir Spec-Driven Development e a tarefa tocar specs numerados, batches, reviews, validation, decisions ou change requests.
user-invocable: false
---

# SDD workflow

Use esta skill sempre que a tarefa depender do modelo SDD do Nexus.

## Leitura minima inicial

Comece por:

- [specs index](../../../specs/README.md)
- [start here](../../../specs/process/00-START-HERE.md)
- [workflow](../../../specs/process/01-WORKFLOW.md)
- [batch index](../../../specs/implementation/BATCH-INDEX.md)
- [validation checklist](../../../specs/validation/VALIDATION-CHECKLIST.md)
- [decision log](../../../specs/decisions/DECISION-LOG.md)

Depois leia apenas os specs numerados e arquivos de codigo que controlam o slice atual.

## Classificacao da demanda

1. Mudanca de requisito ou contrato:
   - registre em `specs/change-requests/`
   - avalie impacto nos specs numerados, decisions, batches e validation
   - so depois parta para implementacao
2. Feedback de review sem mudanca normativa:
   - registre em `specs/reviews/`
   - mantenha os specs numerados estaveis
3. Implementacao incremental:
   - confira o batch atual em `specs/implementation/`
   - implemente o menor slice aprovado
   - valide e atualize `specs/validation/` quando necessario
4. Validacao ou spec drift check:
   - comece pela menor checagem automatizada
   - registre evidencia e pendencias nos artefatos certos

## Regras de ouro

- Os specs numerados sao a fonte normativa.
- Nao reescreva os specs numerados para comentarios pequenos de review.
- Nao abra o proximo batch antes de o atual estar estavel e revisavel.
- Quando houver duvida entre mudar spec ou nao, trate primeiro como change request ou review, nao como edicao direta do spec numerado.