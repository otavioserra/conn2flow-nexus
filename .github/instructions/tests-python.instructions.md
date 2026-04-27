---
name: 'Nexus Tests Python'
description: 'Use ao editar testes Python em tests/ no Conn2Flow Nexus.'
applyTo: 'tests/**/*.py'
---

- Ancore cada teste novo ao spec numerado e ao batch ativo.
- Prefira testes deterministas e mock-only, salvo quando o batch pedir validacao de stack real.
- Expanda cobertura no menor slice que prove o contrato em revisao.
- Quando o batch tiver validacao focada, rode primeiro o subconjunto do batch e depois `pytest -q`.