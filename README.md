# KGI-Bench

**Knowledge Graph Integration Benchmark** — a framework for evaluating end-to-end pipelines that incrementally integrate heterogeneous data into an existing knowledge graph (KG).

KGI-Bench assesses pipeline outputs (the updated KG) using three complementary quality dimensions: **coverage**, **correctness**, and **consistency**. It also supports auxiliary metrics (structure, runtime, task-level diagnostics) and aggregated scores for ranking pipelines.

- **Paper:** [Arxiv](https://arxiv.org/pdf/2605.22304) — *Evaluation of Pipelines for Data Integration into Knowledge Graphs* (Marvin Hofer, Erhard Rahm, ScaDS.AI / Leipzig University)
- **Repository:** https://github.com/ScaDS/KGI-Bench
- **Datasets:** https://doi.org/10.5281/zenodo.17246357

## Motivation

Integrating new sources into a KG typically chains many tasks (extraction, mapping, entity resolution, fusion, cleaning, completion). Individual tools are often evaluated in isolation, but comparing **whole pipelines** — especially when updating an existing seed KG with overlapping, heterogeneous inputs — remains difficult.

KGI-Bench closes this gap by providing:

1. **Quality metrics** on the integrated KG (with optional reference-based, source-based, or labeling-based variants where applicable).
2. **Benchmark datasets** with a seed KG, input sources, and a reference KG as ground truth.
3. **Reproducible experiments** that compare multiple pipelines (e.g. via [KGpipe](https://github.com/ScaDS/KGpipe)).

## Evaluation metrics

Metrics are defined in the paper (Section 4). Implementations used in experiments currently live in [KGpipe](https://github.com/ScaDS/KGpipe); a mirrored interface is defined under `src/kgibench/metrics/`.

### Coverage

How completely information from the sources appears in the integrated KG.

| Metric | Description |
|--------|-------------|
| **Entity coverage** | Share of reference entities (with correct types) represented after alignment. |
| **Fact / triple coverage** | Share of reference triples matched in the integrated KG. |

**Alternatives without a reference KG:** source-based coverage checks whether extracted content from each input source is reflected in the KG.

### Correctness

Precision-oriented measures of whether newly added entities and triples are semantically correct relative to the reference (or labels / sources).

| Metric | Description |
|--------|-------------|
| **Entity correctness** | Fraction of produced entities that align to the right reference entity and types (duplicates penalized via reference-entity counting). |
| **Fact / triple correctness** | Fraction of produced triples that match reference triples (duplicate matches penalized similarly). |
| **Duplicate rate** | Diagnostic: multiple integrated entities aligned to the same reference entity. |

**Alternatives:** labeling-based evaluation (human or LLM judgments on samples) and source-supported fact checking for unstructured inputs.

### Consistency

Whether the integrated KG satisfies ontology constraints (independent of reference content). Examples include disjoint class violations, domain/range misuse, relation direction errors, cardinality violations, and literal datatype/format errors. These are reported as violation counts or normalized scores (higher is better when normalized).

### Auxiliary metrics

Useful for analysis and debugging, but **not** treated as end-to-end quality on their own:

- **Statistical:** fact/entity/relation/type counts, untyped entities, graph density.
- **Resource:** duration, peak memory, external API cost.
- **Task-level:** entity-matching precision/recall, ontology-matching precision/recall, entity/relation linking quality.

### Aggregation

Per-pipeline scores can be combined by normalizing metrics to \([0,1]\), averaging within quality groups, and taking a weighted average across groups (e.g. coverage, correctness, consistency). Entity and triple **F1** scores (harmonic mean of coverage and correctness) are also supported.

## Repository layout

```
KGI-Bench/
├── docs/                    # MkDocs site (CLI, movie benchmark pointer)
├── benchmarks/
│   └── kgi-bench-movie/     # Movie-domain benchmark (datasets, evaluation)
│       ├── ontology/movie-ontology.ttl
│       ├── Makefile         # Download data & run evaluation
│       └── src/moviekg/     # Evaluation helpers
└── src/kgibench/            # Evaluation framework interface
```

## KGI-Bench-Movie

The first benchmark instantiation covers the **movie domain** (entities `Film`, `Person`, `Company`; fixed ontology). It is derived from Wikipedia and DBpedia and supports incremental integration scenarios.

| Component | Description |
|-----------|-------------|
| **Seed KG** | Initial graph to be updated |
| **Input sources** | Overlapping data in **RDF**, **JSON**, and **text** (Wikipedia abstracts) |
| **Reference KG** | Ground truth integrating all inputs without duplicates |
| **Sizes** | `film_100` (development), `film_1k` (testing), `film_10k` (benchmarking) |

**Integration settings** (paper Section 3):

- **SSP (single-source type):** three steps, same format each time — six pipeline variants (two per format: base + alternate, plus optional LLM variants).
- **MSP (multi-source type):** three steps, one format per step (RDF → JSON → text or permutations) — six combined pipelines built from the SSP base variants.

The paper evaluates **12 pipelines** (6 SSP + 6 MSP, using the base variant per format) using [KGpipe](https://github.com/ScaDS/KGpipe). Pipeline definitions and execution live in [KGpipe `experiments/moviekg`](https://github.com/ScaDS/KGpipe/tree/main/experiments/moviekg).

### Quick start

See [benchmarks/kgi-bench-movie/README.md](benchmarks/kgi-bench-movie/README.md) for the full evaluation workflow.

Install the `kgi-bench` package from the repository root (Python 3.12+), e.g. with [uv](https://docs.astral.sh/uv/):

```bash
cd KGI-Bench
uv sync
source .venv/bin/activate
# optional (embedding / LLM metrics): uv sync --extra ml --extra cpu
```

**Evaluate pipeline outputs**

```bash
cd benchmarks/kgi-bench-movie
cp env .env
make download-datasets    # and/or
make download-results
make eval-all
```

Example CLI invocation:

```bash
kgibench evaluate -m CountMetric \
  benchmarks/kgi-bench-movie/data/results/large/rdf_base/stage_3/result.nt
```

## Installation

Python **3.12+** is required. Dependencies are declared in [pyproject.toml](pyproject.toml) (KGpipe / kgcore and optional ML extras for embeddings and LLM tasks).

```bash
# with uv (recommended)
uv sync

# or pip
pip install -e .
```

Optional extras: `dev`, `cpu` / `cuda` (PyTorch), `ml` (transformers, sentence-transformers).
