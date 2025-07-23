# Glacium Development Guidelines

> **Goal**: Create clean, maintainable, and **loosely coupled** code for software agents that is easy to test, extend, and render into scripts/configs.

---

## 1  Core Principles

| Principle                 | Short Description                                              | Practical Note                                                                        |
| ------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **Single Responsibility** | Each class/function has exactly *one* responsibility.          | Modules ≤ 400 lines, classes ≤ 200 lines, methods ≤ 40 lines.                         |
| **Loose Coupling**        | Components know only abstract interfaces, not implementations. | Pass dependencies via constructor/factory, never `import` in the middle of functions. |
| **Explicit Dependencies** | Dependencies are visible in constructor/function signatures.   | No global state outside clearly declared config objects.                              |
| **Fail Fast**             | Failures are raised immediately, not hidden.                   | Assertions for invariants, `pydantic` validation.                                     |
| **Immutable Data**        | Values are immutable after creation.                           | `@dataclass(frozen=True)` or `pydantic.BaseModel` with `frozen=True`.                 |

---

## 2  Architecture & Design Patterns

| Pattern                        | When to Use                                                             | Mini Example                                              |
| ------------------------------ | ----------------------------------------------------------------------- | --------------------------------------------------------- |
| **Dependency Injection (DI)**  | Each component gets its dependencies injected – replaceable & testable. | `Agent(db: Database, strategy: Strategy)`.                |
| **Strategy**                   | Swap behavior (e.g. selection algorithm) at runtime.                    | `class GreedySelection(Strategy): ...`                    |
| **Factory / Abstract Factory** | Encapsulate creation of complex objects.                                | `AgentFactory.create_from_cfg(cfg)`                       |
| **Observer / PubSub**          | Event-driven communication without tight coupling.                      | `event_bus.publish('task_finished', data)`                |
| **Facade**                     | Hide complex subsystems behind a simple API.                            | `StorageFacade.save_run(agent_run)`                       |
| **Builder**                    | Stepwise building of complex configurations/scripts.                    | `ScriptBuilder().with_env(env).with_tasks(tasks).build()` |
| **Template Method**            | Skeleton is fixed, details via hooks.                                   | Base class for agent lifecycle.                           |
| **Adapter**                    | Adapt foreign API to your own interface.                                | `class S3Adapter(Storage): ...`                           |

### Layered Model

1. **Interface** (REST, CLI, gRPC)
2. **Service** (Orchestration & Scheduling)
3. **Domain** (Core Logic & Strategies)
4. **Plugin** (Adapters for external programs)
5. **Infrastructure** (DB, FS, HTTP, MQ)

> Dependencies always point *downwards*; Domain remains framework-agnostic.

---

## 3  Configuration & Variable Management

- **pydantic Settings**: `Settings` class automatically reads from `.env`, environment variables, and YAML files.
  ```python
  from pydantic_settings import BaseSettings
  class AppSettings(BaseSettings):
      env: str = 'dev'
      run_dir: Path = Path('/tmp')
  settings = AppSettings(_env_file='.env')
  ```
- **Layered Context**: `defaults.yml` → `env/<stage>.yml` → CLI overrides (`--set key=value`).
- **Runtime State**: Use an immutable `Context` object that holds worker ID, timestamps, etc., injected into tasks.
- **Jinja Macros & Filters**: All custom filters in `glacium/templates/filters.py`; registered centrally in `glacium.templating`.
- **Secret Backends**: Support both `.env` and HashiCorp Vault via a unified `SecretProvider` interface.
- **Schema Versioning**: Each config carries `schema_version`; migrations executed via `glacium.config.migrate`.

---

## 4  Persistence Layer

- **SQLite (default)** for local runs without external dependencies.
- **PostgreSQL** optional via SQLAlchemy `async` engine, configured via `DATABASE_URL`.
- **Repository Pattern** keeps domain models free of ORMs: `RunRepository`, `TaskRepository`.
- **Event Sourcing**: Store state changes as events; snapshots after N events.
- **Filesystem Artifacts** (logs, plots) are stored deterministically under `~/.glacium/runs/<run_id>/`.
- **Cache**: In-memory (LRU) via `functools.cache` + optional Redis backend.

---

## 5  Test Strategy

| Level           | Tooling                                 | Goal                                  |
| --------------- | --------------------------------------- | ------------------------------------- |
| **Unit**        | `pytest`, `pytest-mocker`, `hypothesis` | 95% coverage in Domain.               |
| **Integration** | Docker-Compose services                 | Real-time connections & DB migrations |
| **Contract**    | `schemathesis` / `pact`                 | Don’t break external APIs.            |
| **End-to-End**  | CLI/REST via `pytest-xprocess`          | Black-box behavior.                   |

> Tests run in parallel on GitHub Actions; runtime < 10 min.

---

## 6  Documentation

- **Docstrings**: NumPy style; every public member.
- **API Docs**: Sphinx + `autodoc`, output to `docs/`.
- **ADRs**: Folder `docs/adr/`. Number by date `YYYY-MM-DD-topic.md`.
- **Diagrams**: Mermaid (`docs/diagrams/*.mmd`) or PlantUML.
- **How-To Guides** & **FAQs** in the wiki.

---

## 7  CI/CD & Code Quality

1. **Pre-Commit Hooks**: `black`, `ruff`, `isort`, `mypy`.
2. **Static Analysis**: `bandit`, `safety`.
3. **Build**: Poetry/PyPI package; SemVer tags.
4. **Release Artifacts**: Docker image & wheel.
5. **Deploy**: GitHub Actions → K8s / CloudRun.

---

## 8  Naming Conventions & Style

- **PEP 8** and `ruff --strict` as gatekeeper.
- **Type Hints** required (`from __future__ import annotations`).
- **Functional parameters** come first, **Optionals** last.
- No abbreviations except commonly known (`cfg`, `id`).

---

## 9  API Interface

- **Framework**: FastAPI for REST + AsyncIO; automatic OpenAPI docs.
- **Versioning**: Path-based (`/api/v1/`) + header `X-API-Version` for experimental endpoints.
- **Schema**: Pydantic models – domain objects are mapped via DTO ⇄ Domain mappers.
- **Error Handling**: Unified JSON errors (`{code, message, details}`) via global `exception_handler`.
- **Pagination & Filtering**: Cursor pagination (`next_cursor`) instead of offset.
- **Auth**: OAuth2 password + JWT refresh token or optional API key.
- **Rate Limit**: Middleware with `slowapi`.
- **Testing**: `pytest-asyncio` + `httpx.AsyncClient` mock; contract tests with `schemathesis`.

