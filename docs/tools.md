# magma.tool

> **Status** | v0.1.0 | Experimental  
> **Depends on** | `inspect`, `hashlib`, `baml-cli >= 0.79.0`, `pydantic`, `importlib.metadata`  

---

## 1 · Purpose & Mental Model
`magma.tool` turns **plain Python functions** into first‑class **LLM tools** – a common schema that can be:

1. Injected into *structured* function‑calling prompts  
2. Executed inside a CodeAgent sandbox  
3. Discovered at run‑time via `magma.registry.tools`

### Flow

```

@tool‑decorated function
│
├─➔ generates / updates    ─┐
│     baml\_src/foo.baml     │  (schema + prompt stub)
│                           ▼
checksum comment       // TOOL\_SIG\_SHA=5ad3b9f1
│                           │
└── registers with ➔  magma.registry.tools\["foo"]

````

If the Python signature later changes, the checksum mismatch raises `ToolSignatureChangedError` at import time → *fail‑fast*.

---

## 2 · Quick‑start

```python
from magma.tool import tool

@tool
def sentiment(text: str) -> str:
    """Return 'positive', 'neutral' or 'negative'."""
    return "positive"  # when run locally by CodeAgent

# auto‑generated file: baml_src/sentiment.baml
"""
// TOOL_SIG_SHA=49dfe8c2
class SentimentInput { text string }
function sentiment(input: SentimentInput) -> string { client "openai/gpt-4o" ... }
"""

# Use inside a prompt
from baml_client import b
from magma.model import Model
from magma.prompt import prompt

analyser = prompt(baml_fn=b.sentiment, model=Model("openai/gpt-4o"))
print(analyser("I love magma!"))   # → "positive"
````

---

## 3 · Public API

### 3.1 Symbol overview

| Symbol                      | Type                 | Description                                           |
| --------------------------- | -------------------- | ----------------------------------------------------- |
| `@tool`                     | decorator            | Converts a function to a tool & emits BAML            |
| `ToolInfo`                  | `pydantic.BaseModel` | Runtime metadata (name, schema, checksum, python\_fn) |
| `ToolSignatureChangedError` | `Exception`          | Raised when checksum ≠ recorded                       |

### 3.2 Key signatures

```python
def tool(
    fn: Callable = ...,
    *,
    name: str | None = None,
    allow_modules: list[str] | None = None,  # for sandbox
    description: str | None = None,
) -> Callable:
    """
    Decorator that:
    1. Calculates SHA‑256 of `inspect.signature(fn)`
    2. Writes / refreshes `baml_src/<name>.baml`
    3. Registers ToolInfo in magma.registry.tools
    """
```

```python
class ToolInfo(BaseModel):
    name: str
    checksum: str                # 8‑char hex
    schema_path: Path
    python_fn: Callable[..., Any]

    def schema_json(self) -> str: ...
    def run_locally(*args, **kw) -> Any: ...
```

---

## 4 · Design Notes

* **Schema generation** – primitives (`int`, `str`, `float`, `bool`) map 1‑to‑1 to BAML primitives; `pydantic.BaseModel` params become *nested objects*.
* **Idempotent file writes** – before overwriting `.baml`, compare existing checksum; only rewrite when the python signature changed → avoids noisy git diffs.
* **Checksum placement** – first line of the file → fast to read (`readline()`).
* **Sandbox allow‑list** – `allow_modules` arg is stored as metadata → CodeAgent can automatically configure `LocalPythonExecutor`.

---

## 5 · Extensibility Hooks

| Hook                         | Usage                                                 | Scenario                                     |
| ---------------------------- | ----------------------------------------------------- | -------------------------------------------- |
| **Manual BAML override**     | Add `custom_baml_path="..."` kwarg to decorator       | You wrote complex prompt manually            |
| **Rename tool**              | `@tool(name="summarise_text")`                        | Keep python snake‑case but expose kebab‑case |
| **Extra description**        | `@tool(description="Generates plotly scatter plot.")` | Better auto‑docs generation                  |
| **Disabling checksum guard** | `export MAGMA_TOOL_SKIP_CHECKSUM=1`                   | Rare: prototyping without BAML regeneration  |

---

## 6 · Integration Points

| External           | Interaction                                            | Notes                                             |
| ------------------ | ------------------------------------------------------ | ------------------------------------------------- |
| **BAML**           | Writes `.baml` file, later imported by `baml generate` | Ensures LLM sees matching input/output schema     |
| **magma.registry** | `registry.tools[name] = ToolInfo`                      | One‑stop lookup for CLI & prompt builder          |
| **magma.sandbox**  | `allow_modules` metadata                               | Configures secure import allow‑list for CodeAgent |
| **magma.prompt**   | Accepts list of `ToolInfo`                             | Injects JSON schema into function‑calling prompt  |

---

## 7 · Reference Implementation Roadmap

| Phase  | Scope                                       | Tests                                                |
| ------ | ------------------------------------------- | ---------------------------------------------------- |
| **P1** | Basic decorator, BAML emit, registry insert | pytest: file written & checksum match                |
| **P2** | Checksum drift detection                    | mutate function ➔ expect `ToolSignatureChangedError` |
| **P3** | Nested pydantic param → BAML nested object  | golden schema snapshot                               |
| **P4** | `allow_modules` pass‑through to sandbox     | integration test with `magma.sandbox.LocalPython`    |

---

## 8 · Changelog Snippet


### Added
- `magma.tool.@tool` decorator: auto‑generates BAML, checksum guard, registry entry.
- `ToolSignatureChangedError` for early failure on schema drift.