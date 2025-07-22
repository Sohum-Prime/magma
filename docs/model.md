# magma.model

> **Status** | v0.1.0 | Experimental  
> **Depends on** | `litellm >= 0.42`, `pydantic >= 2`, `langfuse (optional)`  

---

## 1 · Purpose & Mental Model
`magma.model` provides a **uniform, declarative handle** for Large‑Language‑Models (LLMs) regardless of where they run – OpenAI, Anthropic, local vLLM, Ollama, etc.  
Think of it as a *typed connection string*:


```
   "anthropic/claude‑4‑opus‑20250514"
         ▲               ▲
       vendor          version
```



A `Model` instance encapsulates **(a)** provider identifier, **(b)** generation parameters (temperature, top‑p, …), and **(c)** provider‑specific extras (e.g. Anthropic “thinking” tokens).  
It does **not** know about prompts or tools – those are handled by `magma.prompt`.

---

## 2 · Quick‑start

```python
from magma.model import Model

# Two cloud models
gpt4o  = Model("openai/gpt-4o", temperature=0.7)
opus4  = Model(
    "anthropic/claude-4-opus-20250514",
    temperature=0.3,
    thinking={"type": "enabled", "budget_tokens": 10_000},
)

# A local GGUF model served via Ollama
mistral = Model("ollama/mistral:latest", max_tokens=512)

# Raw chat usage (rare – usually used via magma.prompt)
res = gpt4o([{"role": "user", "content": "Say hi!"}])
print(res.content)            # -> "Hello there!"
````

---

## 3 · Public API

### 3.1 Symbol overview

| Symbol       | Type                  | Description                                        |
| ------------ | --------------------- | -------------------------------------------------- |
| `Model`      | `@pydantic.dataclass` | Immutable configuration object + callable          |
| `ModelError` | `Exception`           | Raised on failed provider call                     |
| `Generation` | `TypedDict`           | Parsed LiteLLM‐style response (id, content, usage) |

### 3.2 Selected signatures & examples

```python
@dataclass(frozen=True, slots=True)
class Model:
    id: str                                  # "openai/gpt-4o" etc.
    temperature: float = 0.0
    top_p: float | None = None
    max_tokens: int | None = None
    # Provider‑specific free‑form kwargs
    extra: dict[str, Any] = field(default_factory=dict)

    # --- runtime helpers -------------------------------------------------
    def __call__(
        self,
        messages: list[dict],                # LiteLLM chat format
        *,
        stream: bool = False,
        **overrides,
    ) -> Generation | Iterable[Generation]: ...

    def with_(self, **kwargs) -> "Model": ...
    """Return a *new* Model with params overridden."""
```

> *Gotchas*
>
> • `top_p=None` means “leave provider default”.
>
> • `extra` keys are passed straight to LiteLLM → unknown keys may raise at provider side.

---

## 4 · Design Notes

* **Immutability**: dataclass is `frozen=True`; `.with_()` always returns a new instance – avoids hidden state mutation when a model is reused across prompts.
* **Single dispatch point**: all provider calls funnel through `litellm.completion()`; we *do not* re‑implement retries or streaming – we rely on LiteLLM’s built‑ins.
* **LangFuse hooks**: if `LANGFUSE_…` env vars exist, a callback wraps the call to capture timing, token usage, pricing. Zero overhead otherwise.
* **Async later**: v0.1.0 exposes only sync `__call__`; async wrapper arrives in v0.2.0 via `ModelAsync`.

---

## 5 · Extensibility Hooks

| Hook                         | How to use                                                                 | Typical need                                |
| ---------------------------- | -------------------------------------------------------------------------- | ------------------------------------------- |
| **Provider‑specific kwargs** | `Model("groq/llama3-70b", groq_api_key="…")`                               | Exotic params not yet first‑class in magma  |
| **Global defaults**          | `export MAGMA_MODEL_DEFAULT_TEMPERATURE=0.3`                               | Company‑wide baseline without touching code |
| **Pre‑call interceptor**     | `from magma.model import register_hook`<br>`@register_hook("before_call")` | Custom token‑budget enforcement             |

---

## 6 · Integration Points

| External         | Interaction                           | Notes                                              |
| ---------------- | ------------------------------------- | -------------------------------------------------- |
| **LiteLLM**      | `completion()` / `async_completion()` | Handles auth, router, retries                      |
| **LangFuse**     | `span = tracer.start_span()`          | Captures cost / latency if keys present            |
| **magma.prompt** | Accepts `Model` instance              | Prompt builder never touches provider IDs directly |

---

## 7 · Reference Implementation Roadmap

| Phase           | Scope                                                            | Tests                                            |
| --------------- | ---------------------------------------------------------------- | ------------------------------------------------ |
| **P1**          | Dataclass, sync `__call__`, `.with_()`, basic LiteLLM invocation | Doctest from §2, pytest for .with\_ immutability |
| **P2**          | LangFuse span integration, env‑var default overrides             | Mock LangFuse → assert span attributes           |
| **P3** *(v0.2)* | Async subclass, batching helper                                  | Trio/asyncio pytest                              |
| **P4** *(v0.2)* | Provider capability registry (max context window, rate‑limits)   | Contract tests per provider                      |

---

## 8 · Changelog Snippet


### Added
- Introduced `magma.model.Model`: immutable wrapper over LiteLLM with LangFuse tracing.