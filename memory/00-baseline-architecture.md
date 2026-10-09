# System Master Index — conn2flow-nexus

Projeto: conn2flow-nexus. Raiz: C:/Users/otavi/OneDrive/Documentos/GIT/conn2flow-nexus.
Papel: Hub de Conexões e Integrações do ecossistema Conn2Flow (FastAPI/Python, roteamento de LLM e workers).
Fundação MDD adotada pela REQ-068 / BATCH-070 (matriz conn2flow-ai-workspace), 2026-10-09. Histórico SDD preservado por git mv.

## Entrada econômica

1. Leia este router, [mecânica](01-general-memory.md) e [política](02-policy.md).
2. Leia [CURRENT](human-requests/CURRENT.md) quando existir e a requisição apontada; confirme aprovação, lote e autonomia.
3. Use o index.md da área antes de carregar documentos extensos. Consulte somente as fontes necessárias ao slice.
4. Confira [README](README.md) e o [índice geral](index.md).

## Mapa do repositório

| Área | Responsabilidade |
| --- | --- |
| memory/ | Governança persistente (MDD): requisições, lotes, decisões, validação, relatórios e índices |
| CLAUDE.md | Arquivo do projeto |
| docker-compose.yml | Arquivo do projeto |
| Dockerfile | Arquivo do projeto |
| docs/ | Diretório do projeto |
| LICENSE | Arquivo do projeto |
| pyproject.toml | Arquivo do projeto |
| README.md | Arquivo do projeto |
| requirements.txt | Arquivo do projeto |
| src/ | Diretório do projeto |
| tests/ | Diretório do projeto |

## Autoridade e preservação

Código, schemas e configuração vigentes prevalecem sobre memórias históricas. Decisões e contratos aprovados governam requisitos; intake não substitui contrato normativo. A governança canônica vive na matriz conn2flow-ai-workspace; skills canônicas são propagadas por scripts/skills/sync-skills.cjs e skills locais deste repositório são preservadas.
