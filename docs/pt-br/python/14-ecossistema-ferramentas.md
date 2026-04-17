# 14. Ecossistema Python & Ferramentas

Este módulo cobre as ferramentas, workflows e ecossistema ao redor do desenvolvimento Python — tudo que **não é** a linguagem em si, mas é essencial para trabalho profissional.

---

## Gerenciamento de Pacotes — pip & venv

### Equivalente PHP
| PHP | Python |
|-----|--------|
| Composer | pip |
| `composer.json` | `pyproject.toml` ou `requirements.txt` |
| `composer.lock` | `requirements.txt` (fixado) |
| `vendor/` | `.venv/lib/` |
| `composer require pkg` | `pip install pkg` |
| `composer install` | `pip install -r requirements.txt` |

### Ambientes Virtuais
```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar (Linux/macOS)
source .venv/bin/activate

# Ativar (Windows)
.venv\Scripts\activate

# Verificar
which python  # Deve apontar para .venv/bin/python

# Instalar dependências
pip install -r requirements.txt

# Desativar
deactivate
```

**Por que venv?** Cada projeto tem seu Python + pacotes isolados. Sem poluição global. Como o `vendor/` do PHP, mas para o interpretador inteiro.

### Arquivos de Requirements
```
# requirements.txt (produção)
fastapi==0.136.0
uvicorn[standard]==0.34.3
pydantic==2.12.5
pydantic-settings==2.13.1
aiokafka==0.13.0
redis[hiredis]==5.3.0
litellm==1.83.9
langgraph==1.1.7
httpx==0.28.1
orjson==3.11.0

# requirements-dev.txt
-r requirements.txt
pytest==8.4.2
pytest-asyncio==0.26.0
```

---

## `pyproject.toml` — Configuração Moderna

```toml
[project]
name = "conn2flow-nexus-ai"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "W", "F", "I", "N", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
```

`pyproject.toml` é o padrão moderno — substitui `setup.py`, `setup.cfg`, `.flake8`, etc. Um arquivo para tudo.

---

## Linters — Qualidade de Código

### Ruff (Recomendado — Rápido!)
```bash
pip install ruff

# Verificar problemas
ruff check .

# Auto-corrigir
ruff check --fix .

# Formatar código (como black)
ruff format .
```

Ruff substitui flake8, isort, pyflakes e mais. Escrito em Rust, extremamente rápido.

### Comparação PHP:
| PHP | Python |
|-----|--------|
| PHP_CodeSniffer | flake8 / ruff |
| PHPCS Fixer | black / ruff format |
| PHPStan / Psalm | mypy / pyright |

---

## Formatadores — Estilo Consistente

### Black (O Padrão)
```bash
pip install black

# Formatar um arquivo
black src/main.py

# Formatar projeto inteiro
black src/ tests/

# Apenas verificar (CI)
black --check src/ tests/
```

Black é **opinativo** — poucas opções de configuração. "Qualquer cor que quiser, desde que seja preto."

### Ruff Format (Alternativa)
```bash
ruff format src/ tests/
```

Compatível com Black, mas mais rápido.

---

## Type Checkers — Análise Estática

### Mypy
```bash
pip install mypy

# Verificar tipos
mypy src/

# Modo estrito
mypy src/ --strict
```

```python
# mypy detecta isso:
def greet(name: str) -> str:
    return 42  # ❌ error: Incompatible return value type (got "int", expected "str")
```

### Pyright (embutido no VS Code)
A extensão Pylance do VS Code usa Pyright. Verifica tipos enquanto você digita — sem comando necessário.

---

## Integração com Docker

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instala dependências primeiro (camada cacheada)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia código-fonte
COPY src/ ./src/

# Executa
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose
```yaml
services:
  nexus-ai:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      kafka:
        condition: service_healthy
      redis:
        condition: service_healthy

  kafka:
    image: apache/kafka:latest
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      # Modo KRaft — sem ZooKeeper!
    healthcheck:
      test: ["CMD", "/opt/kafka/bin/kafka-topics.sh", "--bootstrap-server", "localhost:9092", "--list"]

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
```

### Conceitos-chave Docker:
- **Cache de camadas:** `COPY requirements.txt` antes de `COPY src/` — dependências são cacheadas a menos que requirements mude
- **`depends_on` + healthcheck:** Garante que serviços estão prontos antes da app iniciar
- **`env_file`:** Carrega `.env` no container
- **Modo KRaft:** Kafka sem ZooKeeper (setup mais simples)

---

## Integração CI/CD

### GitHub Actions (Exemplo)
```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements-dev.txt
      - run: python -m pytest tests/ -v
      - run: ruff check src/
      - run: mypy src/
```

---

## Ferramentas CLI Úteis

```bash
# Gerenciamento de pacotes
pip list                    # Pacotes instalados
pip show fastapi            # Info do pacote
pip freeze                  # Todos os pacotes com versões
pip install --upgrade pkg   # Atualizar pacote

# Ambiente virtual
python -m venv .venv        # Criar
source .venv/bin/activate   # Ativar
deactivate                  # Desativar
which python                # Verificar Python ativo

# Execução
python -m pytest            # Executar testes
python -m uvicorn src.main:app  # Executar app
python -c "import sys; print(sys.version)"  # Comando rápido

# Debug
python -i script.py         # Executa e cai no REPL
python -m pdb script.py     # Debugger
```

---

## Convenção de Estrutura de Projeto

```
conn2flow-nexus/
├── .env                    # Variáveis de ambiente (não no git!)
├── .env.example            # Template para .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml          # Config do projeto + ferramentas
├── requirements.txt        # Dependências de produção
├── requirements-dev.txt    # Dependências de desenvolvimento
├── README.md
├── src/                    # Código-fonte
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   ├── api/
│   ├── core/
│   ├── models/
│   └── workers/
├── tests/
│   ├── conftest.py
│   └── test_*.py
└── docs/
    ├── en/
    └── pt-br/
```

### Convenção vs PHP:
| PHP | Python |
|-----|--------|
| `App\Http\Controllers\` | `src/api/endpoints/` |
| `App\Models\` | `src/models/` |
| `App\Services\` | `src/core/` |
| `config/` | `src/config/` |
| `tests/Feature/` | `tests/` |
| `routes/api.php` | `src/api/router.py` |

---

## Extensões VS Code Essenciais

- **Pylance** — IntelliSense, verificação de tipos, auto-imports
- **Python** — Debug, testes, gerenciamento de venv
- **Ruff** — Linting e formatação
- **Even Better TOML** — Suporte a `pyproject.toml`
- **Docker** — Suporte a Dockerfile e compose

---

## Anterior: [← Design Patterns](13-design-patterns.md) | Voltar para: [Índice do Curso](README.md)
