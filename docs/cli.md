# magma.cli

> **Status** | v0.1.0 | Experimental  
> **Depends on** | `typer >= 0.12`, `rich`, `cookiecutter`, `baml-cli`, `magma.registry`  

---

## 1 · Purpose & Mental Model
`magma.cli` is a **minimal command‑line interface** that glues together the
other magma modules for day‑zero productivity.  
Version 0.1.0 ships three core sub‑commands:

| Command | One‑liner | Primary audience |
|---------|-----------|------------------|
| `magma init` | Scaffold a fresh project | New users |
| `magma generate` | Re‑generate BAML client & refresh tool checksums | Everyday dev loop |
| `magma explain` | Human‑readable introspection of a prompt / agent | Debugging & demos |

Each command is implemented with **Typer**, giving you automatic `--help`, rich
terminal output via **rich**, and shell completion for free.

---

## 2 · Quick‑start

```bash
# 1) create new repo structure
$ magma init my-cool-agent
✔ Created project 'my-cool-agent'
   ├─ baml_src/
   ├─ src/
   ├─ .env.example
   └─ README.md

# 2) work … edit tools & BAML …

# 3) regenerate clients & check schemas
$ magma generate
✔ BAML client generated (4 functions)
✔ 2 tools synced, 0 checksum drifts

# 4) inspect a prompt
$ magma explain prompt Visualize --args path=data/iris.csv
== Prompt: Visualize ==
curl  -X POST https://api.openai.com/v1/chat/completions \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  […]

== JSON body ==
{ "model": "gpt-4o-mini", "messages": […], "tools": […] }
````

---

## 3 · Public API (CLI surface)

### 3.1 Sub‑command table

| Sub‑command | Flags / options                                                     | Description                                |
| ----------- | ------------------------------------------------------------------- | ------------------------------------------ |
| `init`      | `--template` (cookiecutter URL)<br>`--yes` (non‑interactive)        | Generate project skeleton                  |
| `generate`  | `--quiet`<br>`--skip-baml`                                          | Run `baml generate`, update tool checksums |
| `explain`   | `prompt <name>`<br>`agent <name>`<br>`--args key=val …`<br>`--json` | Show fully rendered cURL / JSON            |

### 3.2 Typer entry‑point

```python
app = typer.Typer(help="Magma command‑line utility")

@app.command()
def init(
    project_name: str,
    template: str = typer.Option(None, help="Cookiecutter template URL"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Non‑interactive"),
): ...

@app.command()
def generate(
    quiet: bool = typer.Option(False, "--quiet", "-q"),
    skip_baml: bool = typer.Option(False, "--skip-baml"),
): ...

@app.command()
def explain(
    kind: str = typer.Argument(..., help="prompt | agent"),
    name: str = typer.Argument(...),
    args: list[str] = typer.Option([], "--args", "-a"),
    json: bool = typer.Option(False, "--json"),
): ...
```

---

## 4 · Design Notes

* **Zero external state** – working directory is inferred; `init` refuses to run
  if path exists unless `--yes`.
* **Registry powered** – `generate` and `explain` rely on
  `magma.registry.*`; no brittle path math.
* **Cookiecutter templates** – `init` defaults to an internal template shipped
  in `magma.assets`, but users may supply their own via `--template`.
* **Rich tables** – command outputs use `rich.table.Table` for readability when
  terminal supports ANSI; falls back to plain text in non‑TTY.

---

## 5 · Extensibility Hooks

| Hook                      | Usage                                                                  | Scenario                |
| ------------------------- | ---------------------------------------------------------------------- | ----------------------- |
| **Custom templates**      | `magma init --template=https://github.com/org/cookiecutter-magma`      | Company‑standard layout |
| **Plugin commands**       | Install package exposing Typer app via entry‑point `magma_cli_plugins` | `magma yourcmd …`       |
| **Environment overrides** | `export MAGMA_GENERATE_OPTS="--quiet"`                                 | CI pipelines            |

Planned **v0.2+**: `magma doctor`, `magma docs build`, `magma graph`.

---

## 6 · Integration Points

| External           | Interaction                              | Notes                                              |
| ------------------ | ---------------------------------------- | -------------------------------------------------- |
| **baml-cli**       | `generate` shell‑outs to `baml generate` | Ensures Python client in sync                      |
| **magma.registry** | Listing tools / agents for `explain`     | Single lookup source                               |
| **rich**           | Pretty console rendering                 | Auto‑detect “dumb” terminals to degrade gracefully |

---

## 7 · Reference Implementation Roadmap

| Phase           | Scope                                          | Tests                                       |
| --------------- | ---------------------------------------------- | ------------------------------------------- |
| **P1**          | Typer skeleton + `init` (local template)       | Run in temp dir, assert files exist         |
| **P2**          | `generate` (wrap baml, checksum refresh)       | Mock baml CLI, diff tool files              |
| **P3**          | `explain` (prompt & agent)                     | Use sample registry objects, compare output |
| **P4** *(v0.2)* | Plugin command loading, `doctor`, `docs build` | Integration test with dummy plugin          |

---

## 8 · Changelog Snippet


### Added
- Typer-based `magma` CLI with sub‑commands: `init`, `generate`, `explain`.
- Rich terminal output; cookiecutter project scaffolding.
