# 1. Visão Geral da Arquitetura

## O Que É o Conn2Flow Nexus AI?

O **Conn2Flow Nexus AI** é um **microsserviço** que funciona como **AI Gateway** — um intermediário (Man-in-the-Middle) entre a plataforma Conn2Flow e múltiplos provedores de Inteligência Artificial (OpenAI, Anthropic, Google, Groq, etc.).

### Por que um Gateway de IA?

Sem um gateway, cada módulo do Conn2Flow precisaria:
- Implementar integração com cada provedor de IA separadamente
- Lidar com rate limiting, retries e fallbacks
- Gerenciar API keys em múltiplos locais
- Monitorar custos e uso de tokens

Com o Nexus AI, tudo isso fica **centralizado em um único ponto**.

---

## Padrão Arquitetural: Event-Driven Architecture (EDA)

O projeto usa o padrão **Event-Driven Architecture**, onde componentes se comunicam através de **eventos** em vez de chamadas diretas (REST síncronas).

### Como funciona:

```
┌─────────────┐        ┌──────────────┐        ┌─────────────────────┐
│  Conn2Flow   │──POST──►  FastAPI API  │──pub──►  Kafka               │
│  (Client)    │◄──202──│  (Gateway)    │        │  c2f_incoming_tasks  │
└─────────────┘        └──────────────┘        └──────────┬──────────┘
                                                          │ consume
                                                ┌─────────▼──────────┐
                                                │  Task Worker        │
                                                │  (LangGraph +       │
                                                │   LiteLLM)          │
                                                └─────────┬──────────┘
                                                          │ pub
                                               ┌──────────▼──────────┐
                                               │  Kafka               │
                                               │  c2f_completed_tasks │
                                               └──────────┬──────────┘
                                                          │ consume
                                               ┌──────────▼──────────┐
                                               │  Delivery Worker     │
                                               │  (Webhook POST)      │
                                               └──────────┬──────────┘
                                                          │
                                               ┌──────────▼──────────┐
                                               │  Conn2Flow           │
                                               │  (Webhook Receiver)  │
                                               └─────────────────────┘
```

### Vantagens do EDA:

| Vantagem | Explicação |
|----------|-----------|
| **Desacoplamento** | A API não precisa esperar o LLM terminar — retorna 202 imediatamente |
| **Resiliência** | Se o worker cair, as mensagens ficam no Kafka até serem processadas |
| **Escalabilidade** | Podemos adicionar N workers para processar em paralelo |
| **Auditoria** | Todos os eventos ficam registrados nos tópicos Kafka |

---

## Padrão: Request-Reply Assíncrono

O fluxo completo implementa o padrão **Async Request-Reply**:

1. **Request**: O Conn2Flow envia uma tarefa via `POST /api/v1/tasks/submit`
2. **Accept**: A API retorna `HTTP 202 Accepted` com um `task_id`
3. **Process**: O worker consome do Kafka, processa no LLM e publica o resultado
4. **Reply**: O delivery worker envia o resultado de volta via webhook

Isso é fundamentalmente diferente de um padrão síncrono onde o client ficaria esperando 30+ segundos pela resposta do LLM.

---

## Estrutura de Diretórios

```
conn2flow-nexus/
├── src/                          # Código-fonte principal
│   ├── main.py                   # Entry point — cria o app FastAPI
│   ├── config/
│   │   └── settings.py           # Configurações centralizadas (pydantic-settings)
│   ├── api/
│   │   ├── router.py             # Agrupa rotas da API
│   │   ├── endpoints/
│   │   │   ├── health.py         # GET /health — health check
│   │   │   └── tasks.py          # POST /submit + GET /status/{id}
│   │   └── schemas/
│   │       ├── requests.py       # Schema de entrada (TaskRequest)
│   │       └── responses.py      # Schemas de resposta
│   ├── core/                     # Infraestrutura compartilhada
│   │   ├── kafka_producer.py     # Publicar eventos no Kafka
│   │   ├── kafka_consumer.py     # Classe base para consumers
│   │   ├── redis_client.py       # Client Redis async (status + métricas)
│   │   └── llm_router.py         # Roteador LLM multi-provedor
│   ├── workers/                  # Processos independentes
│   │   ├── task_processor.py     # Consumer: processa tarefas com LLM
│   │   └── delivery_worker.py    # Consumer: entrega resultados via webhook
│   ├── graphs/
│   │   └── base_graph.py         # Pipeline LangGraph (validate → llm → format)
│   └── models/
│       └── events.py             # Modelos de eventos Kafka
├── tests/                        # Testes unitários
├── docs/                         # Documentação (esta pasta)
├── specs/                        # Especificações SDD
├── docker-compose.yml            # Orquestração Docker
├── Dockerfile                    # Build do container
├── requirements.txt              # Dependências Python
├── .env                          # Variáveis de ambiente (local)
└── .env.example                  # Template de .env
```

---

## Conceitos-Chave

### Singleton Pattern
Usado em `kafka_producer.py` e `redis_client.py` — uma única instância é compartilhada por toda a aplicação via variável global de módulo.

### Dependency Injection
O FastAPI usa DI nativo via `Depends()` — por exemplo, `verify_api_key` é injetado automaticamente nos endpoints.

### Abstract Base Class (ABC)
`BaseKafkaConsumer` é uma classe abstrata que define o contrato que todo consumer deve seguir, permitindo extensão fácil.

### Separation of Concerns
Cada camada tem responsabilidade única:
- `api/` → Recebe e valida HTTP
- `core/` → Infraestrutura (Kafka, Redis, LLM)
- `workers/` → Lógica de processamento
- `graphs/` → Orquestração de pipeline
- `models/` → Contratos de dados

---

## Próximo: [FastAPI — Web Framework →](02-fastapi.md)
