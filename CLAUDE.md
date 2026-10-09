# Projeto Memory Driven Development (MDD)

- Trate `memory/README.md` e os sdd numerados como fonte normativa.
- Antes de editar código ou sdd, leia `memory/README.md`, `memory/process/00-START-HERE.md`, `memory/process/01-WORKFLOW.md`, `memory/implementation/BATCH-INDEX.md`, o batch atual, `memory/validation/VALIDATION-CHECKLIST.md` e `memory/decisions/DECISION-LOG.md`.
- Use `memory/human-requests/` apenas como intake humano não normativo. Se a demanda vier como caminho de arquivo Markdown ou como a própria pasta, leia esse material primeiro e depois classifique a demanda no artefato MDD correto.
- **Memórias de Engenharia**: No início de cada sessão, leia obrigatoriamente `memory/03-memory-engineering-chief.md` e `memory/04-memory-engineering-execution.md` para alinhar contexto antes de qualquer alteração.
- **Manutenção da Memória de Execução**: Ao término de cada tarefa, atualize `memory/04-memory-engineering-execution.md` com novos aprendizados, bugs resolvidos e particularidades do ambiente. Nunca modifique `memory/03-memory-engineering-chief.md` sem instrução explícita do usuário humano.
- Classifique a demanda cedo: change request, implementação de batch, review ou validação.
- Não reescreva os sdd numerados para comentários pequenos de review.
- Edite sdd numerados apenas quando requisito, contrato, critério de aceite ou decisão aprovada realmente mudar.
- Mantenha o trabalho em batches pequenos com alvo de validação explícito.

## Skills principais

- Use `/start-sdd-slice` para nova demanda ou entrada em `memory/human-requests/`.
- Use `/continue-sdd-batch` para retomar um batch em andamento.
- Use `/review-current-batch` para review findings-first do batch atual.
- Use `/raise-spec-change` para rodada de mudança normativa.

## Skills automáticas

- `sdd-workflow`: decidir o artefato certo e manter o batch alinhado ao fluxo.
- `project-validation`: escolher a menor validação executável para o slice atual.

## Otimização de Contexto e Arquivamento

- Mantenha `memory/decisions/DECISION-LOG.md`, `memory/implementation/BATCH-INDEX.md` e `memory/validation/VALIDATION-CHECKLIST.md` com no máximo 10 itens correntes ou ativos.
- Mantenha também `memory/human-requests/` enxuto, preservando no máximo 10 requisições correntes ou recentes fora de `archive/`.
- Mova históricos antigos para a subpasta `archive/` correspondente: `memory/decisions/archive/`, `memory/human-requests/archive/`, `memory/implementation/archive/` ou `memory/validation/archive/`.
- Nos arquivos principais, substitua o histórico arquivado por tabelas Markdown resumidas com 1 linha por item e link direto para o arquivo em `archive/`.
- Ao carregar contexto inicial, priorize os arquivos principais e abra itens em `archive/` apenas quando o batch, a requisição ativa ou um link de rastreabilidade exigir.
