# Curso Python — Para Desenvolvedores LAMP Seniores

Bem-vindo ao **Curso Python do Conn2Flow Nexus AI** — um guia completo e prático, projetado especificamente para **desenvolvedores seniores PHP/LAMP** em transição para Python.

Este não é um curso para iniciantes. Você já entende programação profundamente — variáveis, funções, OOP, bancos de dados, HTTP, REST, testes. O que você precisa é de uma **ponte** que mapeie seus 20 anos de conhecimento em PHP/MySQL/Apache para o ecossistema Python, destacando onde o Python difere, onde ele brilha e onde ele vai te surpreender.

---

## Estrutura do Curso

| # | Módulo | Descrição |
|---|--------|-----------|
| 01 | [Fundamentos Python para Devs PHP](01-fundamentos.md) | Sintaxe, variáveis, tipos, f-strings, truthiness — PHP vs Python lado a lado |
| 02 | [Type Hints & Sistema de Tipos](02-type-hints.md) | Anotações de tipo do Python, Union, Optional, generics, sintaxe `str \| None` |
| 03 | [Estruturas de Dados em Profundidade](03-estruturas-dados.md) | list, dict, set, tuple — vs arrays PHP. Comprehensions, unpacking, slicing |
| 04 | [Funções, Closures & Decorators](04-funcoes-decorators.md) | `def`, `lambda`, `*args`, `**kwargs`, decorators, closures, functools |
| 05 | [OOP em Python](05-oop.md) | Classes, herança, ABC, protocolos, `@property`, dataclasses, dunder methods |
| 06 | [Módulos, Pacotes & Ambientes Virtuais](06-modulos-pacotes.md) | `import`, `__init__.py`, pip, venv, `pyproject.toml`, gerenciamento de dependências |
| 07 | [Async/Await & Concorrência](07-async-await.md) | asyncio, coroutines, event loop, `async for`, `async with`, tasks, gathering |
| 08 | [Context Managers & Gerenciamento de Recursos](08-context-managers.md) | `with`, `__enter__`/`__exit__`, `@contextmanager`, `@asynccontextmanager` |
| 09 | [Tratamento de Erros & Exceções](09-tratamento-erros.md) | `try`/`except`/`finally`, exceções customizadas, encadeamento, boas práticas |
| 10 | [Pydantic & Validação de Dados](10-pydantic.md) | BaseModel, Field, validadores, serialização, `model_dump()`, Settings |
| 11 | [FastAPI em Profundidade](11-fastapi.md) | Roteamento, injeção de dependência, middleware, lifespan, OpenAPI, TestClient |
| 12 | [Testes com Pytest](12-pytest.md) | Fixtures, mocking, parametrize, testes async, TestClient, cobertura |
| 13 | [Design Patterns em Python](13-design-patterns.md) | Singleton, factory, state machine, DI — todos do código do Nexus |
| 14 | [Ecossistema Python & Ferramentas](14-ecossistema-ferramentas.md) | pip, venv, pyproject.toml, linters, formatters, Docker, CI/CD |

---

## Como Usar Este Curso

1. **Leia sequencialmente** — cada módulo se baseia no anterior
2. **Compare com PHP** — todo conceito é comparado lado a lado
3. **Estude o código-fonte** — todos os exemplos vêm do projeto Nexus real
4. **Execute o código** — use o ambiente virtual para testar tudo
5. **Consulte quando precisar** — use como referência ao trabalhar no projeto

---

## Setup Rápido

```bash
cd conn2flow-nexus
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

---

## Filosofia

> *"A melhor forma de aprender uma nova linguagem não é começar do zero, mas mapear o que você já sabe."*

Cada capítulo começa com o que você já conhece em PHP e constrói a ponte para Python. Onde o Python faz algo fundamentalmente diferente, explicamos **por quê** — não apenas como.
