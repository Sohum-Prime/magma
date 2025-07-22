# magma.registry

> **Status** | v0.1.0 | Experimental  
> **Depends on** | `importlib.metadata`, `functools`, `inspect`, `pydantic`, `types`, `magma.tool`, `magma.model`, `magma.prompt`, `magma.agent`  

---

## 1 · Purpose & Mental Model
`magma.registry` is the **single source of truth** for *discovering* every artefact created with magma:

* **Models** – `magma.model.Model` instances you defined in code  
* **Tools** – `@tool`‑decorated functions (`ToolInfo`)  
* **Prompts** – `PromptRunnable`s built via `magma.prompt`  
* **Agents** – compiled `Agent` runnables

Akin to Python’s *entry‑points*, the registry surfaces a **dict‑like interface** (`list()`, `get()`, `values()`) that powers:

* the CLI (`magma ls`, `magma explain <name>`)  
* auto‑docs generation (`magma docs build`)  
* dynamic loading in production (e.g., “run agent X by name”)

All lookups are **lazy** – import cost is paid only when you access an item.

---

## 2 · Quick‑start

```python
from magma.registry import models, tools, prompts, agents

# List available components
print(models.list())   # {'openai/gpt-4o', 'anthropic/claude-4-opus'}
print(tools.list())    # {'sentiment', 'create_scatter'}

# Fetch by name
plot_tool = tools.get("create_scatter")
plot_tool.run_locally("data.csv")

# Iterate over agents
for ag in agents.values():
    print("Agent:", ag.name, "nodes:", ag.mermaid()[:60], "…")
````

---

## 3 · Public API

### 3.1 Sub‑registries

| Symbol    | Returns                    | Description                           |
| --------- | -------------------------- | ------------------------------------- |
| `models`  | `Registry[Model]`          | Keys = `model.id`                     |
| `tools`   | `Registry[ToolInfo]`       | Keys = `tool.name`                    |
| `prompts` | `Registry[PromptRunnable]` | Keys = prompt `.name` or BAML fn name |
| `agents`  | `Registry[Agent]`          | Keys = agent `.name`                  |

### 3.2 Generic Registry interface

```python
class Registry(Generic[T]):
    def list(self) -> set[str]: ...
    def get(self, key: str) -> T | None: ...
    def values(self) -> Iterable[T]: ...
    def refresh(self) -> None: ...
```

> *Gotchas*
>
> • `refresh()` clears cache and re‑scans packages – rarely needed except in REPL after hot reload.
>
> • Lookups are **case‑sensitive**.

---

## 4 · Design Notes

* **Lazy loading** – first access triggers `_populate()` which:

  1. Scans `sys.modules` for already‑imported magma artefacts.
  2. Iterates entry‑points group `"magma_plugins"` so third‑party packages can ship tools / agents.
* **Checksum validation** – tooling registry calls `tool._validate_baml_sig()` (from `magma.tool`) to catch drift early.
* **Thread safety** – internal state protected by a `threading.Lock`; double‑checked locking avoids race on high concurrency servers.
* **Lightweight** – Registry objects contain *references*, not copies; no deep cloning.

---

## 5 · Extensibility Hooks

| Hook                       | Usage                                                                                    | Scenario                       |
| -------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------ |
| **Plugin entry‑points**    | `setup.cfg`:<br>`[options.entry_points]`<br>`magma_plugins =\n    mytools = mypkg.tools` | Ship custom toolset via PyPI   |
| **Manual registration**    | `models.register(my_model)`                                                              | Create models dynamically      |
| **Filter view**            | `tools.filter(lambda t: "plot" in t.name)` *(planned v0.2)*                              | Context‑aware CLI              |
| **Auto‑refresh on import** | `export MAGMA_REGISTRY_AUTO_REFRESH=1`                                                   | Jupyter hot‑reload convenience |

---

## 6 · Integration Points

| External         | Interaction                                   | Notes                                     |
| ---------------- | --------------------------------------------- | ----------------------------------------- |
| **magma.cli**    | `magma ls`, `magma explain` read registry     | Zero config discovery                     |
| **magma.prompt** | Registers each runnable (if `name` provided)  | Enables prompt reuse by string ID         |
| **magma.agent**  | Registers compiled agent under key `name`     | Run via `magma run agent <name>` (future) |
| **Docs builder** | Iterates `registry` to emit tables & diagrams | Keeps docs in sync with code              |

---

## 7 · Reference Implementation Roadmap

| Phase           | Scope                                        | Tests                                                   |
| --------------- | -------------------------------------------- | ------------------------------------------------------- |
| **P1**          | Core `Registry` class + sub‑instances        | Unit: register dummy obj, assert list/get               |
| **P2**          | Entry‑point loading                          | Install test‑wheel in CI, assert object visible         |
| **P3**          | Checksum validation for tools                | Modify tool signature → expect error on registry access |
| **P4** *(v0.2)* | Filter & search helpers, auto‑refresh toggle | REPL hot reload test                                    |

---

## 8 · Changelog Snippet


### Added
- Lazy-loading `Registry` with sub-registries: models, tools, prompts, agents.
- Entry‑point plugin support under group `magma_plugins`.
- Tool checksum validation at registry access.