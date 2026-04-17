# 06. Módulos, Pacotes & Ambientes Virtuais

## PHP vs Python — Organização de Código

| PHP | Python |
|-----|--------|
| `require`/`include` | `import` |
| `use App\Models\User;` | `from src.models.user import User` |
| `namespace App\Models;` | Estrutura de diretórios = namespace |
| `composer.json` | `pyproject.toml` / `requirements.txt` |
| `vendor/` | `.venv/` |
| `composer install` | `pip install -r requirements.txt` |
| Autoload (PSR-4) | `import` automático por caminho |

---

## `import` — Importando Módulos

### Importar módulo inteiro
```python
import os
import json

os.path.exists("/tmp/file.txt")
json.dumps({"key": "value"})
```

### Importar nomes específicos
```python
from os.path import exists, join
from json import dumps, loads

exists("/tmp/file.txt")  # Sem prefixo os.path.
dumps({"key": "value"})
```

### Importar com alias
```python
import numpy as np
from datetime import datetime as dt
```

### Importação relativa (dentro do mesmo pacote)
```python
# src/api/endpoints/tasks.py
from src.core.kafka_producer import send_event       # Absoluta
from ..schemas.requests import TaskRequest             # Relativa (../ = pacote pai)
```

### No nosso código:
```python
# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config.settings import get_settings
from src.api.router import api_router
from src.core.kafka_producer import start_producer, stop_producer
from src.core.redis_client import start_redis, stop_redis
```

---

## `__init__.py` — O Que É?

```
src/
├── __init__.py          # Marca src/ como pacote Python
├── main.py
├── config/
│   ├── __init__.py      # Marca config/ como sub-pacote
│   └── settings.py
├── api/
│   ├── __init__.py
│   ├── router.py
│   ├── endpoints/
│   │   ├── __init__.py
│   │   ├── health.py
│   │   └── tasks.py
│   └── schemas/
│       ├── __init__.py
│       ├── requests.py
│       └── responses.py
```

### O que `__init__.py` faz:
1. Marca o diretório como um **pacote Python** (importável)
2. Pode ser **vazio** (apenas marcador)
3. Pode conter código de inicialização do pacote
4. Pode definir `__all__` para controlar `from pacote import *`

### Exemplo de `__init__.py` com re-exports:
```python
# src/api/schemas/__init__.py
from .requests import TaskRequest
from .responses import TaskAcceptedResponse, TaskStatusResponse

# Agora é possível:
from src.api.schemas import TaskRequest  # Ao invés de src.api.schemas.requests
```

### PHP comparado:
- PHP usa `namespace App\Models;` + PSR-4 autoload
- Python usa a estrutura de diretórios diretamente

---

## Ambientes Virtuais — `venv`

### PHP equivalente: `vendor/`
```bash
# PHP: composer cria vendor/ com dependências isoladas por projeto
composer install

# Python: venv cria uma cópia isolada do Python + pacotes
python -m venv .venv
```

### Criando e usando:
```bash
# 1. Criar
python -m venv .venv

# 2. Ativar
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 3. Verificar
which python    # Deve apontar para .venv/bin/python
python --version

# 4. Instalar dependências
pip install fastapi uvicorn pydantic

# 5. Desativar
deactivate
```

### Por que venv?
- **Isolamento**: cada projeto tem suas dependências
- **Reprodutibilidade**: `requirements.txt` garante mesmas versões
- **Sem conflitos**: projeto A pode usar FastAPI 0.100, projeto B FastAPI 0.136

### `.gitignore`:
```
.venv/
__pycache__/
*.pyc
.env
```

---

## pip — Gerenciador de Pacotes

### Comandos essenciais:
```bash
pip install fastapi              # Instalar pacote
pip install fastapi==0.136.0     # Versão específica
pip install "fastapi>=0.100"     # Versão mínima
pip install -r requirements.txt  # Instalar de arquivo
pip uninstall fastapi            # Desinstalar
pip list                         # Listar instalados
pip show fastapi                 # Info do pacote
pip freeze                       # Listar com versões (para requirements.txt)
pip install --upgrade pip        # Atualizar o pip
```

### `requirements.txt`:
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

# requirements-dev.txt (desenvolvimento)
-r requirements.txt
pytest==8.4.2
pytest-asyncio==0.26.0
```

### PHP comparado:
```json
// composer.json
{
    "require": {
        "laravel/framework": "^11.0"
    },
    "require-dev": {
        "phpunit/phpunit": "^10.0"
    }
}
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

[tool.mypy]
python_version = "3.11"
strict = true
```

`pyproject.toml` é o padrão moderno para configuração Python — substitui `setup.py`, `setup.cfg`, `.flake8`, etc. Um arquivo para tudo (similar ao `composer.json`).

---

## PYTHONPATH — Resolvendo Imports

Quando você executa `python -m pytest` ou `uvicorn src.main:app`, Python precisa encontrar seus módulos.

### Problema comum:
```
ModuleNotFoundError: No module named 'src'
```

### Soluções:
```bash
# 1. Executar da raiz do projeto (recomendado)
cd conn2flow-nexus
python -m pytest tests/

# 2. PYTHONPATH
export PYTHONPATH="${PWD}:$PYTHONPATH"
python -m pytest tests/

# 3. Instalar em modo editável
pip install -e .
```

### No Docker:
```dockerfile
WORKDIR /app
COPY . .
# WORKDIR garante que /app está no path
```

---

## Estrutura do Nosso Projeto

```
conn2flow-nexus/
├── .env                    # Variáveis de ambiente
├── .venv/                  # Ambiente virtual (não versionado)
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml          # Config do projeto e ferramentas
├── requirements.txt        # Dependências de produção
├── requirements-dev.txt    # Dependências de desenvolvimento
├── src/                    # Código-fonte
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── settings.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── router.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── health.py
│   │   │   └── tasks.py
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── requests.py
│   │       └── responses.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── kafka_producer.py
│   │   ├── kafka_consumer.py
│   │   ├── redis_client.py
│   │   └── llm_router.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── events.py
│   └── workers/
│       ├── __init__.py
│       ├── task_processor.py
│       └── delivery_worker.py
└── tests/
    ├── conftest.py
    ├── test_api.py
    ├── test_graph.py
    ├── test_llm_router.py
    ├── test_schemas.py
    └── test_settings.py
```

---

## Anterior: [← OOP](05-oop.md) | Próximo: [Async/Await →](07-async-await.md)
