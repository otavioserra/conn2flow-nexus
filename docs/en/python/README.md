# Python Course — For Senior LAMP Developers

Welcome to the **Conn2Flow Nexus AI Python Course** — a comprehensive, hands-on guide designed specifically for **senior PHP/LAMP developers** transitioning to Python.

This is not a beginner course. You already understand programming deeply — variables, functions, OOP, databases, HTTP, REST, testing. What you need is a **bridge** that maps your 20 years of PHP/MySQL/Apache knowledge to the Python ecosystem, highlighting where Python differs, where it shines, and where it will surprise you.

---

## Course Structure

| # | Module | Description |
|---|--------|-------------|
| 01 | [Python Fundamentals for PHP Developers](01-fundamentals.md) | Syntax, variables, types, f-strings, truthiness — PHP vs Python side-by-side |
| 02 | [Type Hints & The Type System](02-type-hints.md) | Python's type annotations, Union, Optional, generics, `str \| None` syntax |
| 03 | [Data Structures Deep Dive](03-data-structures.md) | list, dict, set, tuple — vs PHP arrays. Comprehensions, unpacking, slicing |
| 04 | [Functions, Closures & Decorators](04-functions-decorators.md) | `def`, `lambda`, `*args`, `**kwargs`, decorators, closures, functools |
| 05 | [OOP in Python](05-oop.md) | Classes, inheritance, ABC, protocols, `@property`, dataclasses, dunder methods |
| 06 | [Modules, Packages & Virtual Environments](06-modules-packages.md) | `import`, `__init__.py`, pip, venv, `pyproject.toml`, dependency management |
| 07 | [Async/Await & Concurrency](07-async-await.md) | asyncio, coroutines, event loop, `async for`, `async with`, tasks, gathering |
| 08 | [Context Managers & Resource Handling](08-context-managers.md) | `with`, `__enter__`/`__exit__`, `@contextmanager`, `@asynccontextmanager` |
| 09 | [Error Handling & Exceptions](09-error-handling.md) | `try`/`except`/`finally`, custom exceptions, exception chaining, best practices |
| 10 | [Pydantic & Data Validation](10-pydantic.md) | BaseModel, Field, validators, serialization, `model_dump()`, Settings |
| 11 | [FastAPI Deep Dive](11-fastapi.md) | Routing, dependency injection, middleware, lifespan, OpenAPI, TestClient |
| 12 | [Testing with Pytest](12-pytest.md) | Fixtures, mocking, parametrize, async tests, TestClient, coverage |
| 13 | [Design Patterns in Python](13-design-patterns.md) | Singleton, factory, state machine, DI — all from the Nexus codebase |
| 14 | [Python Ecosystem & Tooling](14-ecosystem-tooling.md) | pip, venv, pyproject.toml, linters, formatters, Docker, CI/CD |

---

## How to Use This Course

1. **Read sequentially** — each module builds on the previous one
2. **Compare with PHP** — every concept is compared side-by-side
3. **Study the codebase** — all examples come from the actual Nexus project
4. **Run the code** — use the virtual environment to test everything
5. **Refer back** — use this as a reference when working on the project

---

## Quick Setup

```bash
cd conn2flow-nexus
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

---

## Philosophy

> *"The best way to learn a new language is not to start from zero, but to map what you already know."*

Every chapter starts with what you know in PHP and builds the bridge to Python. Where Python does something fundamentally different, we explain **why** — not just how.
