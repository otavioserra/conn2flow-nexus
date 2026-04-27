---
name: start-sdd-slice
description: Inicia uma demanda no Conn2Flow Nexus identificando specs relevantes, batch atual, artefato correto e validacao minima.
agent: nexus-sdd-coordinator
argument-hint: 'Descreva a demanda e, se souber, o batch ou spec relacionado.'
---

Para a demanda abaixo:

1. Leia `specs/README.md`, `specs/process/00-START-HERE.md`, `specs/process/01-WORKFLOW.md` e os artefatos SDD que governam o slice.
2. Identifique os specs numerados relevantes.
3. Classifique a demanda: change request, implementacao de batch, review ou validacao.
4. Determine o menor conjunto de arquivos a ler depois dos specs.
5. Declare uma hipotese local falsificavel e a menor validacao disponivel.
6. Se o contexto ja for suficiente, comece a execucao em vez de apenas planejar.

Demanda:

${input:task:Descreva a tarefa}