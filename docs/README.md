# Docs (MkDocs)

The `KGI-Bench/` subproject has its own documentation site built with **MkDocs + Material**.

## Local preview

From the repo root:

```bash
cd KGI-Bench
python -m pip install -e ".[docs]"
mkdocs serve
```

## Build

```bash
cd KGI-Bench
mkdocs build --strict
```

The static site is written to `KGI-Bench/site/`.

