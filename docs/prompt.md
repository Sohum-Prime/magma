# magma.prompt

> **Status** | v0.1.0 | Experimental  
> **Depends on** | `baml-client >= 0.79.0`, `pydantic`, `litellm`, `magma.model`, `magma.tool`  

---

## 1 · Purpose & Mental Model
`magma.prompt` is the **invocation layer**: it marries a BAML function, a `Model`, and an optional toolbox into a single *callable* object → **PromptRunnable**.


```
      BAML fn           Model              Tools[]
         │                │                   │
         └──── prompt( … ) ──────▶  PromptRunnable  ──┐
                                                      ├─  __call__()  → parsed result
                                                      └─  .explain() → cURL / JSON
```


Responsibilities:

* Gather tool JSON‑schemas and inject them into the BAML request body.  
* Render the prompt *lazily* via BAML Modular API (`b.request.*`).  
* Delegate the actual chat to the chosen `Model`.  
* Return **type‑safe**, parsed output (thanks to BAML).

---

## 2 · Quick‑start

```python
from baml_client import b
from magma.model import Model
from magma.tool import tool
from magma.prompt import prompt

# --- define a tool ------------------------------------------------------
@tool
def create_scatter(df_path: str) -> str:
    """Return a Plotly HTML scatter plot."""
    ...

# --- build runnable -----------------------------------------------------
visualiser = prompt(
    baml_fn=b.Visualize,
    model=Model("openai/gpt-4o", temperature=0.2),
    tools=[create_scatter],
)

# --- invoke -------------------------------------------------------------
html = visualiser("data/iris.csv")
open("plot.html", "w").write(html)

# --- debug --------------------------------------------------------------
print(visualiser.ex())   # shows cURL & full JSON body sent to OpenAI
````

---

## 3 · Public API

### 3.1 Symbol overview

| Symbol           | Type        | Description                            |
| ---------------- | ----------- | -------------------------------------- |
| `prompt()`       | function    | Factory producing a `PromptRunnable`   |
| `PromptRunnable` | class       | Callable & debuggable wrapper          |
| `PromptError`    | `Exception` | Raised on validation / provider errors |

### 3.2 Key signatures

```python
def prompt(
    *,
    baml_fn,                             # Generated function from baml_client
    model: Model,
    tools: list[Callable] | None = None,
    name: str | None = None,             # optional human label
) -> "PromptRunnable": ...
```

```python
class PromptRunnable:
    def __call__(self, *fn_args, **fn_kwargs):
        """Executes the BAML function via the configured Model."""
        ...

    # --- developer ergonomics ------------------------------------------
    def explain(self, *fn_args, **fn_kwargs) -> dict[str, Any]: ...
    ex = explain                                 # alias

    # --- metadata -------------------------------------------------------
    @property
    def model(self) -> Model: ...
    @property
    def tools(self) -> list[ToolInfo]: ...
    def raw_request(self, *fn_args, **fn_kwargs) -> dict: ...
```

> *Gotchas*
>
> • `*fn_args/**fn_kwargs` are forwarded **first** to the BAML function, *then* merged into the request body.
>
> • Validation errors raised by BAML become `PromptError`.

---

## 4 · Design Notes

* **Lazy render**: request body is produced on every call, not at construction → allows per‑call dynamic args.
* **Tool schema injection**: when `tools` passed, their `.schema_json()` blobs are concatenated into `request.body["tools"]`; CodeAgent pattern instead appends their python signatures to the system prompt (future v0.2.0).
* **Streaming**: if caller supplies `stream=True` kwarg, prompt deduces provider streaming support from `Model.id` and yields incremental chunks.
* **Tracing**: internally wraps call in `magma.trace.observe(..)` span named `prompt:<baml_fn_name>`.

---

## 5 · Extensibility Hooks

| Hook                               | Usage                                                         | Scenario                                               |
| ---------------------------------- | ------------------------------------------------------------- | ------------------------------------------------------ |
| **Custom tool selection strategy** | `prompt(..., tools=tool_resolver(msg_context))`               | Pick tools dynamically per call                        |
| **Post‑parse filter**              | subclass `PromptRunnable` and override `_postprocess(result)` | E.g. convert markdown → HTML                           |
| **Request interceptor**            | `export MAGMA_PROMPT_PRE_HOOK=my.pkg.hook_fn`                 | Globally mutate request (e.g. add safety instructions) |

---

## 6 · Integration Points

| External                     | Interaction                       | Notes                           |
| ---------------------------- | --------------------------------- | ------------------------------- |
| **magma.model.Model**        | `. __call__()`                    | All network I/O delegated here  |
| **BAML Modular API**         | `b.request.<Fn>` / `b.parse.<Fn>` | Render + strict parse           |
| **magma.tool**               | consumes `ToolInfo.schema_json()` | Structured function calling     |
| **LangFuse via magma.trace** | Child span “prompt:<name>”        | Auto created if tracing enabled |

---

## 7 · Reference Implementation Roadmap

| Phase  | Scope                                                  | Tests                                  |
| ------ | ------------------------------------------------------ | -------------------------------------- |
| **P1** | Factory + runnable, happy‑path sync call, `.explain()` | doctest from §2 produces valid cURL    |
| **P2** | Tool schema injection & validation                     | feed invalid tool → expect PromptError |
| **P3** | Streaming support (`yield` chunks)                     | mock LiteLLM stream                    |
| **P4** | Pre/post hooks and trace spans                         | LangFuse mock span count = 1           |

---

## 8 · Changelog Snippet


### Added
- `prompt()` factory and `PromptRunnable` with `.explain()` for cURL/JSON debugging.
- Automatic tool‑schema injection for structured function calling.
