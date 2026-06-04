# KGI-Bench Movie (evaluation)

This benchmark package contains the **dataset definition** and the **evaluation workflow** for the Movie-domain
incremental KG integration benchmark.

Pipeline **execution** (building the KGs) is handled in the [KGpipe repository](https://github.com/ScaDS/KGpipe/tree/cleanup-eval/experiments/moviekg):
- KGpipe MovieKG pipelines: `experiments/moviekg/` (pipeline catalog + execution helpers)

## Dataset overview

- Dataset release: `https://doi.org/10.5281/zenodo.17246357`
- Sizes:
  - `small` (100 films) — development
  - `medium` (1,000 films) — testing
  - `large` (10,000 films) — benchmarking
- Formats per split: RDF, JSON, TEXT (+ reference metadata for evaluation)

## Evaluation workflow

### 1) Configure environment

Copy the template:

```bash
cp env .env
```

Set at least:
- `OUTPUT_DIR` and `DATASET_SELECT`
- `DATASET_SMALL` / `DATASET_MEDIUM` / `DATASET_LARGE` paths

### 2) Download datasets

```bash
# benchmark data
make download-datasets
# pipeline results
make download-results
```

### 3) Evaluate pipeline outputs (recommended)

Evaluation is run via the KGI-Bench CLI (Movie preset). It expects KGpipe outputs under:

`$OUTPUT_DIR/$DATASET_SELECT/<pipeline_name>/stage_<n>/`

Run evaluation for all pipeline output directories under the selected output root:

```bash
make eval-all
```

Or evaluate a single pipeline:

```bash
make eval-rdf-base
```

You can also call the CLI directly:

```bash
kgibench evaluate -m CountMetric benchmarks/kgi-bench-movie/data/results_curr/large/rdf_a/stage_3/result.nt
```

## Directory structure

### Input structure (example)

```
├── film_100
│   ├── entities
│   │   └── master_entities.csv
│   ├── ontology.ttl -> ../movie-ontology.ttl
│   ├── split_0
│   │   ├── index
│   │   │   └── entities.csv
│   │   ├── kg
│   │   │   ├── reference
│   │   │   │   ├── data/
│   │   │   │   ├── data_agg.nt
│   │   │   │   ├── data.nt
│   │   │   │   └── meta/
│   │   │   └── seed
│   │   │       ├── data/
│   │   │       ├── data.nt
│   │   │       └── meta/
│   │   └── sources
│   │       ├── json
│   │       │   ├── data/
│   │       │   └── meta/
│   │       ├── rdf
│   │       │   ├── data/
│   │       │   ├── data.nt
│   │       │   └── meta/
│   │       └── text
│   │           ├── data/
│   │           └── meta/
│   ├── split_1[... trunc]
├── film_1k[... trunc]
```

### Output structure (example)

KGpipe produces incremental stage outputs; KGI-Bench writes evaluation results alongside them:
- `result.nt` / `result_eval.nt` — integrated KG
- `exec-plan.json`, `exec-report.json` — KGpipe metadata
- `eval_results.json` — metric results written by `kgibench evaluate`

```
├── small
│   ├── json_base
│   │   ├── stage_1
│   │   │   ├── exec-plan.json
│   │   │   ├── exec-report.json
│   │   │   ├── result.nt
│   │   │   ├── eval_results.json
│   │   │   └── tmp/
│   │   ├── stage_2
│   │   │   ├── exec-plan.json
│   │   │   ├── exec-report.json
│   │   │   ├── result.nt
│   │   │   ├── eval_results.json
│   │   │   └── tmp/
│   │   └── stage_3
│   │       ├── exec-plan.json
│   │       ├── exec-report.json
│   │       ├── result.nt
│   │       ├── eval_results.json
│   │       └── tmp/
│   ├── json_alt[... trunc]
└── medium[... trunc]
```