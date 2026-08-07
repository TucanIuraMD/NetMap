# NetMap Coding Standards
**Version:** 1.0
**Status:** Approved
**Document:** 04_CODING_STANDARDS.md

---

# 1. Purpose

This document defines the coding standards for the NetMap project.

Every contributor (human or AI) must follow these rules.

Goals

- Readable code
- Consistent architecture
- Easy maintenance
- Predictable project structure
- Long-term scalability

---

# 2. General Rules

Write simple code.

Avoid clever code.

Readability is more important than brevity.

Prefer explicit over implicit.

Every class has one responsibility.

Every function has one responsibility.

Never duplicate business logic.

Always follow SOLID principles when practical.

---

# 3. Python Version

Python 3.12+

---

# 4. Code Style

PEP8

Use

Black

Ruff

isort

Pytest

---

# 5. Naming

Packages

snake_case

Modules

snake_case.py

Variables

snake_case

Functions

snake_case()

Classes

PascalCase

Constants

UPPER_CASE

Private methods

_prefix()

---

# 6. File Size

Maximum

500 lines

Recommended

300 lines

If a file grows too large

Split it.

---

# 7. Function Size

Maximum

50 lines

Ideal

20–30 lines

---

# 8. Class Size

Maximum

300 lines

If larger

Refactor.

---

# 9. Imports

Standard Library

↓

Third Party

↓

Local Project

Use absolute imports.

Never use wildcard imports.

---

# 10. Type Hints

Every public function must use type hints.

Example

```python
def discover(network: Network) -> list[DiscoveryResult]:
```

---

# 11. Docstrings

Public classes

Public methods

Complex functions

must contain docstrings.

Google Style preferred.

---

# 12. Logging

Never use print().

Use logging.

Levels

DEBUG

INFO

WARNING

ERROR

CRITICAL

---

# 13. Exceptions

Never ignore exceptions.

Never use

except:

Always catch specific exceptions.

---

# 14. Configuration

Never hardcode

IP addresses

Passwords

Paths

Tokens

Use configuration files.

---

# 15. Flask

Routes

must contain

NO business logic.

Only

Validate request

Call Service

Return Response

---

# 16. Services

Business logic belongs here.

Services never know about Flask.

---

# 17. Repositories

Repositories work only with database objects.

Repositories never know about HTTP.

Repositories never contain business logic.

---

# 18. Models

Models contain

Data

Relationships

Validation

No business logic.

---

# 19. Discovery Drivers

Every driver implements

DiscoveryDriver

Required methods

discover()

supports()

name()

weight()

Drivers never

Write database

Call Flask

Send notifications

---

# 20. Merge Engine

Only Merge Engine

creates

updates

merges

Device objects.

Drivers never modify infrastructure directly.

---

# 21. Event Bus

Every important change generates an event.

Examples

DeviceCreated

DeviceUpdated

DeviceOffline

DeviceOnline

ServiceChanged

IPChanged

---

# 22. REST API

All endpoints

JSON only.

Never return HTML.

API Version

/api/v1/

---

# 23. Database

Always use SQLAlchemy ORM.

Never write raw SQL unless absolutely necessary.

Keep SQLite and PostgreSQL compatible.

---

# 24. Frontend

Bootstrap 5

HTMX

Vanilla JavaScript

Avoid heavy JavaScript frameworks.

---

# 25. Templates

Templates display data only.

No business logic.

---

# 26. Testing

Every Service

should have tests.

Use

Pytest

---

# 27. Git

Branch naming

feature/...

bugfix/...

hotfix/...

release/...

Never commit directly to main.

---

# 28. Commits

Format

type(scope): description

Examples

feat(discovery): add ICMP driver

fix(api): correct pagination

docs(database): update relationships

refactor(repository): simplify queries

---

# 29. Documentation

Every new module

must update

Documentation

CHANGELOG

TODO

if applicable.

---

# 30. AI Development Rules

AI assistants must

Follow approved architecture.

Never redesign the project.

Never rename approved modules.

Never change database structure without approval.

Never introduce new dependencies without approval.

If improvement is suggested

Explain

Wait for approval

Then implement.

---

# 31. Performance

Avoid unnecessary database queries.

Prefer bulk operations.

Use pagination.

Lazy load where appropriate.

---

# 32. Security

Never trust user input.

Always validate.

Escape output where necessary.

Do not store plaintext passwords.

Use environment variables for secrets.

---

# 33. Code Review Checklist

Before every commit verify

✔ PEP8

✔ Type hints

✔ Logging

✔ Tests

✔ No duplicated code

✔ Documentation updated

✔ No business logic in routes

✔ No raw SQL

✔ Compatible with SQLite and PostgreSQL

---

# 34. Project Philosophy

Clean.

Simple.

Modular.

Predictable.

Every developer and every AI should produce code that looks like it was written by one team.

---

End of Document