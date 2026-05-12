---
name: start-sdd-slice
description: Inicia uma demanda no Conn2Flow Nexus identificando specs relevantes, batch atual, artefato correto e validacao minima.
agent: nexus-sdd-coordinator
argument-hint: 'Descreva a demanda ou passe um .md em specs/human-requests/. Se passar a pasta, o fluxo usa CURRENT.md, depois README.md, depois o .md mais recente.'
---

Para a demanda abaixo:

1. Se a demanda for um caminho em `specs/human-requests/`, leia primeiro esse intake como material nao normativo. Se a demanda apontar so para a pasta, escolha `CURRENT.md`, depois `README.md`, depois o `.md` mais recente.
2. Leia `specs/README.md`, `specs/process/00-START-HERE.md`, `specs/process/01-WORKFLOW.md` e os artefatos SDD que governam o slice.
3. Identifique os specs numerados relevantes.
4. Classifique a demanda: change request, implementacao de batch, review ou validacao.
5. Determine o menor conjunto de arquivos a ler depois dos specs.
6. Declare uma hipotese local falsificavel e a menor validacao disponivel.
7. Se o contexto ja for suficiente, comece a execucao em vez de apenas planejar.

Demanda:

${input:task:Descreva a tarefa}