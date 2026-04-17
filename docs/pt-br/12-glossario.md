# 12. Glossário

Termos técnicos utilizados no projeto Conn2Flow Nexus AI.

---

### A

**ABC (Abstract Base Class)** — Classe Python que define métodos abstratos que subclasses devem implementar. Usada em `BaseKafkaConsumer`.

**ASGI (Asynchronous Server Gateway Interface)** — Interface padrão para servidores web assíncronos em Python. FastAPI é ASGI.

**async/await** — Sintaxe Python para programação assíncrona. `async def` define uma coroutine; `await` pausa a execução sem bloquear o thread.

**API Gateway** — Serviço que centraliza o acesso a múltiplas APIs backend, gerenciando autenticação, roteamento e rate limiting.

### B

**Backoff Exponencial** — Estratégia de retry onde o tempo de espera dobra a cada tentativa (2s, 4s, 8s...).

**Bind Mount** — Mapeia um diretório do host para dentro do container Docker. Usado em dev para hot-reload.

**Broker** — No Kafka, o servidor que recebe e armazena mensagens.

### C

**Consumer** — Processo que lê mensagens de um tópico Kafka.

**Consumer Group** — Grupo de consumers que dividem o trabalho de um tópico. Cada partição é atribuída a um consumer.

**CORS** — Mecanismo que permite que um servidor especifique quais origens podem acessar seus recursos via browser.

**Coroutine** — Função `async def` que pode ser pausada e retomada. Base da programação assíncrona em Python.

### D

**Dependency Injection (DI)** — Padrão onde dependências são passadas para uma função em vez de serem criadas internamente. FastAPI usa `Depends()`.

**Docker Compose** — Ferramenta para definir e rodar aplicações multi-container Docker.

### E

**Event-Driven Architecture (EDA)** — Padrão arquitetural onde componentes se comunicam via eventos publicados em um message broker.

**Event Loop** — Mecanismo que gerencia execução de coroutines assíncronas. Em Python, implementado pelo `asyncio`.

### F

**Factory Pattern** — Padrão de criação de objetos onde uma função encapsula a lógica de instanciação. `create_app()` no main.py.

**Fallback** — Alternativa automática quando o recurso principal falha. No LiteLLM, se gpt-4o falhar, tenta claude-3-5-sonnet.

**FastAPI** — Framework web Python de alta performance baseado em Starlette e Pydantic.

### H

**Health Check** — Endpoint que indica se o serviço está funcionando. Usado por Docker, load balancers e monitoramento.

**HMAC (Hash-based Message Authentication Code)** — Método criptográfico para verificar integridade e autenticidade de dados.

### I

**Idempotência** — Propriedade onde executar a mesma operação múltiplas vezes produz o mesmo resultado. No Kafka producer, evita duplicação.

### K

**Kafka** — Plataforma de streaming de eventos distribuída. Armazena mensagens em tópicos particionados.

**KRaft** — Modo do Kafka que usa protocolo Raft para consenso, eliminando dependência do Zookeeper.

**Key (Kafka)** — Chave de uma mensagem que determina em qual partição ela será armazenada.

### L

**LangGraph** — Biblioteca para construir aplicações LLM como grafos de estado com nodes e edges.

**Lifespan** — Gerenciamento do ciclo de vida de uma aplicação FastAPI (startup/shutdown).

**LiteLLM** — Biblioteca que fornece API unificada para chamar múltiplos provedores de LLM.

**LLM (Large Language Model)** — Modelo de linguagem de grande escala (GPT-4, Claude, Gemini, etc.).

**LRU Cache** — Cache que descarta itens menos recentemente usados quando atinge o limite.

### M

**Middleware** — Código que roda antes/depois de cada request HTTP, podendo modificar request/response.

**Mock** — Objeto falso usado em testes para substituir dependências reais.

**Monkeypatch** — Fixture do pytest para modificar temporariamente objetos/variáveis durante testes.

**Multi-Stage Build** — Técnica Docker que usa múltiplos stages para criar imagens menores.

### N

**Node (LangGraph)** — Função que recebe o state, executa lógica e retorna campos modificados.

### O

**Offset (Kafka)** — Posição de uma mensagem dentro de uma partição. Usado para rastrear progresso do consumer.

**orjson** — Biblioteca de serialização JSON ultra-rápida para Python (3-10x mais rápida que json padrão).

### P

**Partition (Kafka)** — Subdivisão de um tópico que permite paralelismo. Cada partição é uma fila ordenada.

**Producer** — Processo que publica mensagens em um tópico Kafka.

**Pydantic** — Biblioteca de validação de dados que usa type hints para definir schemas.

**pydantic-settings** — Extensão do Pydantic para carregar configurações de variáveis de ambiente e arquivos .env.

### R

**Redis** — Banco de dados in-memory de alta performance. Key-value store, cache, contador.

**Retry** — Tentativa de repetir uma operação que falhou.

### S

**SDD (Spec Driven Development)** — Metodologia onde especificações formais guiam o desenvolvimento do software.

**Singleton** — Padrão onde apenas uma instância de um objeto existe na aplicação.

**State (LangGraph)** — Dicionário tipado compartilhado entre todos os nodes de um grafo.

**StateGraph** — Tipo de grafo do LangGraph onde nodes leem/modificam um estado compartilhado.

### T

**TTL (Time To Live)** — Tempo de expiração de uma chave no Redis. Após o TTL, a chave é removida.

**Topic (Kafka)** — Canal nomeado onde mensagens são publicadas e consumidas.

**TypedDict** — Tipo Python que define um dicionário com chaves e tipos de valores fixos.

### U

**Uvicorn** — Servidor ASGI de alta performance para aplicações Python assíncronas.

### W

**Webhook** — Callback HTTP — um servidor envia um POST para uma URL pré-configurada quando um evento acontece.

**Worker** — Processo independente que executa tarefas em background, geralmente consumindo de uma fila.

---

## Anterior: [← Segurança](11-seguranca.md) | [Voltar ao Índice →](README.md)
