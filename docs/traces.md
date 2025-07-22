# magma.trace

> **Status** | v0.1.0 | Experimental  
> **Depends on** | `langfuse >= 2.0`, `pydantic`, `contextvars`, `functools`  

---

## 1 · Purpose & Mental Model
`magma.trace` provides **end-to-end observability** by automatically capturing spans for:

1. **Model calls** (via `magma.model`)  
2. **Prompt executions** (via `magma.prompt`)  
3. **Custom developer-defined functions** (via `@observe`)  
4. **Agent flows** (via `magma.agent` / LangGraph callback hooks)

LangFuse serves as the **backend tracer**, collecting costs, tokens, latencies, and custom attributes. By default, tracing is enabled if `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` are set.

```

@observe
│
│─────> Span (data-cleaning-logic) ───────────┐
│                                             │
PromptRunnable ──> Span (prompt\:Visualize) ────────┼──> LangFuse trace tree
│                                             │
Model call ──────> Span (model\:openai/gpt-4o) ─────┘

````

---

## 2 · Quick-start

```python
import os

os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_..."   # if unset => no-op tracer
os.environ["LANGFUSE_SECRET_KEY"] = "sk_..."
os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

from magma.trace import observe
import time

@observe(name="data-cleaning-logic")
def clean_query(q: str) -> str:
    return q.strip().lower()

@observe  # name inferred from function name
def slow_op(n: int) -> int:
    time.sleep(n)
    return n * 2

if __name__ == "__main__":
    res = clean_query("  Hello World  ")
    print(res)   # -> "hello world"

    print(slow_op(1))  # triggers a trace named "slow_op"
````

When executed with `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` set, both calls produce visible spans in LangFuse UI.

---

## 3 · Public API

### 3.1 Symbol overview

| Symbol                      | Type            | Description                                                       |
| --------------------------- | --------------- | ----------------------------------------------------------------- |
| `observe`                   | decorator       | Creates a LangFuse span around a function call                    |
| `start_span(name, **attrs)` | context manager | Manually start a span for arbitrary code blocks                   |
| `get_current_trace()`       | function        | Returns the active trace context (if any)                         |
| `TraceError`                | `Exception`     | Raised if LangFuse is misconfigured or trace initialization fails |

### 3.2 Key signatures

```python
def observe(_fn=None, *, name: str | None = None):
    """
    Decorator that wraps the function in a LangFuse span.
    Usage:
        @observe
        def foo(...): ...
    or
        @observe(name="my-span")
        def bar(...): ...
    """
```

```python
@contextmanager
def start_span(name: str, **attrs) -> Generator[None, None, None]:
    """
    Context manager for ad-hoc span creation.
    Example:
        with start_span("data-transform", dataset="iris.csv"):
            run_transform()
    """
```

---

## 4 · Design Notes

* **Automatic span nesting**: `observe` checks if a trace context exists; nested calls create child spans.
* **No-op fallback**: If LangFuse keys are absent, the decorators become pass-through (zero overhead).
* **Metadata**: Input args and output (or exceptions) are serialized as LangFuse span attributes (truncated to safe size).
* **Performance**: Minimal overhead by caching LangFuse client and using lazy serialization for large data.

---

## 5 · Extensibility Hooks

| Hook                   | Usage                                            | Scenario                                 |
| ---------------------- | ------------------------------------------------ | ---------------------------------------- |
| **Custom tracer**      | `export MAGMA_TRACER=my.pkg.CustomTracer`        | Replace LangFuse with in-house telemetry |
| **Span tags**          | `@observe(name="logic", tags={"module": "ETL"})` | Add key-value tags for filtering         |
| **Dynamic attributes** | `with start_span("foo", user="alice"):`          | Add runtime metadata                     |

---

## 6 · Integration Points

| External         | Interaction                                                           | Notes                              |
| ---------------- | --------------------------------------------------------------------- | ---------------------------------- |
| **LangFuse**     | `client.trace(...)`                                                   | Core telemetry pipeline            |
| **magma.model**  | Each model call is automatically wrapped in a span named `model:<id>` | Injected via callback hooks        |
| **magma.prompt** | Wraps BAML invocations inside spans                                   | Helps correlate prompts with costs |
| **magma.agent**  | Each node in the LangGraph can create child spans                     | Useful for agent path debugging    |

---

## 7 · Reference Implementation Roadmap

| Phase           | Scope                                             | Tests                                         |
| --------------- | ------------------------------------------------- | --------------------------------------------- |
| **P1**          | `@observe` decorator with automatic span creation | Unit test verifying `observe` attaches span   |
| **P2**          | `start_span` context manager                      | Test nested spans and metadata propagation    |
| **P3**          | Integrate with `magma.model` and `magma.prompt`   | End-to-end trace tree test with mock LangFuse |
| **P4** *(v0.2)* | Add trace exporters (JSON file for offline debug) | Compare output snapshot                       |

---

## 8 · Changelog Snippet


### Added
- `magma.trace.observe` decorator for automatic LangFuse spans.
- `start_span` context manager for ad-hoc tracing.
- Integrated model and prompt calls with LangFuse trace context.
