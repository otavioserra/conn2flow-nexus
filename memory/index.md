# Index — memory

Navegação hierárquica; leia o resumo antes do documento integral.

| ID | Título | Resumo Executivo | Link Relativo | Status |
| --- | --- | --- | --- | --- |
| 00-baseline-architecture.md | System Master Index — conn2flow-nexus | Projeto: conn2flow-nexus. Raiz: C:/Users/otavi/OneDrive/Documentos/GIT/conn2flow-nexus. | [00-baseline-architecture.md](00-baseline-architecture.md) | indexed |
| 00-system-overview.md | SPEC-00: System Overview | The Conn2Flow platform needs to consume AI models from different providers, but: | [00-system-overview.md](00-system-overview.md) | indexed |
| 01-architecture.md | SPEC-01: Architecture | The system follows **Event-Driven Architecture (EDA)** with the **Async Request-Reply** pattern: | [01-architecture.md](01-architecture.md) | indexed |
| 01-general-memory.md | Memory Mechanics & Lifecycle | MDD (Memory Driven Development) organiza memória persistente em quatro camadas. Uma especificação continua normativa; o contexto verificável permite aplicar o contrato vigente sem  | [01-general-memory.md](01-general-memory.md) | indexed |
| 02-api-contract.md | SPEC-02: API Contract | {protocol}://{host}:{port}/api/v1 | [02-api-contract.md](02-api-contract.md) | indexed |
| 02-policy.md | MDD Policy — Governance, Folders & Agent SLAs | Vigência: 2026-10-09, REQ-067 / BATCH-069; adotada em conn2flow-nexus pela REQ-068 / BATCH-070. Nomes novos de pastas e arquivos estruturais em inglês; conteúdo pode ser multilíngu | [02-policy.md](02-policy.md) | indexed |
| 03-event-schemas.md | SPEC-03: Event Schemas (Kafka) | Published by the API when a new task is submitted. | [03-event-schemas.md](03-event-schemas.md) | indexed |
| 04-data-models.md | SPEC-04: Data Models | class TaskRequest(BaseModel): | [04-data-models.md](04-data-models.md) | indexed |
| 05-llm-routing.md | SPEC-05: LLM Routing | The LLM Router is the layer that abstracts communication with multiple AI providers. It uses **LiteLLM** as the abstraction library, providing: | [05-llm-routing.md](05-llm-routing.md) | indexed |
| 06-worker-pipeline.md | SPEC-06: Worker Pipeline | The processing pipeline is composed of two independent workers that communicate via Kafka: | [06-worker-pipeline.md](06-worker-pipeline.md) | indexed |
| 07-infrastructure.md | SPEC-07: Infrastructure | The system is composed of **5 Docker services**: | [07-infrastructure.md](07-infrastructure.md) | indexed |
| 08-security.md | SPEC-08: Security |                     ┌─────────────────────┐ | [08-security.md](08-security.md) | indexed |
| 09-configuration.md | SPEC-09: Configuration | The system uses **`pydantic-settings`** for centralized and type-safe configuration. | [09-configuration.md](09-configuration.md) | indexed |
| 10-testing.md | SPEC-10: Testing | tests/ | [10-testing.md](10-testing.md) | indexed |
| change-requests | change-requests | Nó de navegação | [change-requests](change-requests/index.md) | indexed |
| decisions | decisions | Nó de navegação | [decisions](decisions/index.md) | indexed |
| human-requests | human-requests | Nó de navegação | [human-requests](human-requests/index.md) | indexed |
| implementation | implementation | Nó de navegação | [implementation](implementation/index.md) | indexed |
| 03-memory-engineering-chief.md | Memória de Engenharia — Chefia | Documento preservado; consultar fonte | [03-memory-engineering-chief.md](03-memory-engineering-chief.md) | indexed |
| 04-memory-engineering-execution.md | Memória de Engenharia — Execução | Documento preservado; consultar fonte | [04-memory-engineering-execution.md](04-memory-engineering-execution.md) | indexed |
| process | process | Nó de navegação | [process](process/index.md) | indexed |
| raw | raw | Nó de navegação | [raw](raw/index.md) | indexed |
| README.md | 📋 Conn2Flow Nexus AI — Specifications (SDD) | This project adopts **SDD Spec-Anchored**: | [README.md](README.md) | indexed |
| reports | reports | Nó de navegação | [reports](reports/index.md) | indexed |
| reviews | reviews | Nó de navegação | [reviews](reviews/index.md) | indexed |
| scripts | scripts | Nó de navegação | [scripts](scripts/index.md) | indexed |
| validation | validation | Nó de navegação | [validation](validation/index.md) | indexed |
