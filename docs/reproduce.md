# Reproducing KGI-Bench-Movie experiments

Guidelines for running the movie-domain benchmark in [benchmarks/kgi-bench-movie](../benchmarks/kgi-bench-movie/).

See also:

- [benchmarks/kgi-bench-movie/README.md](../benchmarks/kgi-bench-movie/README.md) — dataset layout and output structure
- [README.md](../README.md) — KGI-Bench overview and metrics
- [kgi-bench.pdf](../kgi-bench.pdf) — paper (12-pipeline evaluation)

## Overview

1. [Prerequisites](#prerequisites)
2. [Repository setup](#repository-setup)
3. [Configuration](#configuration)
4. [Download datasets](#download-datasets)
5. [Docker workflow](#docker-workflow-recommended) (full orchestration)
6. [Local workflow](#local-workflow) (pytest-driven pipelines & evaluation)

All commands below assume the working directory:

```bash
cd benchmarks/kgi-bench-movie
```

## Prerequisites

| Resource | Notes |
|----------|--------|
| **Hardware** | 32–64 GB RAM, ~50 GB disk; optional NVIDIA GPU (≥2 GB) for embedding / LLM tasks |
| **Software** | git, make, tar, gzip, Docker (Docker workflow), [uv](https://docs.astral.sh/uv/) or pip |
| **Python** | 3.12+ (see [.python-version](../.python-version)) |
| **LLM pipelines** | OpenAI API token (or compatible endpoint) when running `*-llm` pipelines |

Install Python dependencies from the repository root:

```bash
cd ../..   # KGI-Bench root
uv sync
# optional: uv sync --extra ml --extra cpu
```

## Repository setup

```bash
git clone https://github.com/ScaDS/KGI-Bench.git
cd KGI-Bench/benchmarks/kgi-bench-movie
```

Pipeline definitions: [pipeline.conf](../benchmarks/kgi-bench-movie/pipeline.conf)  
Ontology: [movie-ontology.ttl](../benchmarks/kgi-bench-movie/movie-ontology.ttl)

## Configuration

Experiments are configured via environment variables (loaded by `moviekg.config` through `python-dotenv`).

### Local runs

Copy the provided template and adjust paths / tokens:

```bash
cp env .env
```

Example [env](../benchmarks/kgi-bench-movie/env):

```ini
PIPELINE_CONFIG=pipeline.conf
DATASET_SELECT=small          # small | medium | large

ONTOLOGY_PATH=movie-ontology.ttl
OUTPUT_DIR=./data/results/

DATASET_SMALL=./data/datasets/film_100
DATASET_MEDIUM=./data/datasets/film_1k
DATASET_LARGE=./data/datasets/film_10k

EMBEDDER=sentence-transformer
DBPEDIA_ANNOTATE_URL=http://localhost:2222/rest/annotate
DEFAULT_LLM_MODEL_NAME=gpt-5-mini
OPENAI_TOKEN=                 # required for LLM pipelines
```

| Variable | Description |
|----------|-------------|
| `PIPELINE_CONFIG` | Path to KGpipe pipeline catalog (`pipeline.conf`) |
| `DATASET_SELECT` | Active size: `small` (100 films), `medium` (1k), `large` (10k) |
| `DATASET_SMALL` / `MEDIUM` / `LARGE` | Directories of extracted Zenodo archives |
| `ONTOLOGY_PATH` | Target ontology TTL (relative to benchmark dir for local runs) |
| `OUTPUT_DIR` | Root for pipeline outputs; results go to `$OUTPUT_DIR/$DATASET_SELECT/` |

### Docker runs

Copy the Docker template:

```bash
cp docker_env docker.env
```

Edit `docker.env` (set `OPENAI_TOKEN` for LLM runs). Paths marked as set by the script are filled in by `scripts/moviekg_docker.sh` when using `make run_docker_small`:

```ini
PIPELINE_CONFIG=pipeline.conf
DATASET_SELECT=small

# inside the container (after mount)
ONTOLOGY_PATH=/app/benchmarks/kgi-bench-movie/movie-ontology.ttl

EMBEDDER=sentence-transformer
EMBED_CACHE=redis://cache:6379
DBPEDIA_ANNOTATE_URL=http://dbpedia-spotlight:80/rest/annotate
OPENAI_TOKEN=INSERT_YOUR_OPENAI_TOKEN_HERE
DEFAULT_LLM_MODEL_NAME=gpt-5-mini
```

> **Note:** `make setup_docker` / `make run_docker_small` expect a repository-root `docker-compose.yml`, `Makefile` target `docker_build`, and `scripts/moviekg_docker.sh`. If these are missing in your checkout, use the [local workflow](#local-workflow) or obtain the orchestration files from the [KGpipe](https://github.com/ScaDS/KGpipe) companion setup.

## Download datasets

Datasets are published on Zenodo: https://doi.org/10.5281/zenodo.17246357

From `benchmarks/kgi-bench-movie`:

```bash
make download-datasets
```

This downloads and extracts archives under `data/datasets/` (`film_100`, `film_1k`, `film_10k`).

Optional dataset statistics:

```bash
make datasets-eval
```

## Docker workflow (recommended)

In this mode, KGpipe runs inside Docker; tasks that need external tools (Paris, Valentine, CoreNLP, DBpedia Spotlight, etc.) are invoked on the host via the mounted Docker socket.

1. Configure `docker.env` (see above).
2. Prepare images, tool containers, and supporting services:

```bash
make setup_docker
```

3. Run the full small-dataset experiment (dataset stats, pipelines, evaluation, paper artifacts):

```bash
make run_docker_small
```

To include LLM pipelines in the Docker run, add `make pipelines-llm` to the task list in `scripts/moviekg_docker.sh` (once that script is available in your tree).

## Local workflow

Use this path when running pytest directly on the host (no root Docker orchestration).

### 1. Pipelines

Run all non-LLM integration pipelines (SSP + MSP tests):

```bash
make pipelines
```

LLM variants:

```bash
make pipelines-llm
```

**Per-pipeline targets** (examples):

```bash
make test-rdf-a      # run pipeline
make eval-rdf-a      # evaluate pipeline
make test-ssp-all    # all single-source-type pipelines
make test-msp-all    # all multi-source-type pipelines
```

Outputs under `$OUTPUT_DIR/$DATASET_SELECT/<pipeline_name>/stage_<n>/`:

- `result.nt` — integrated KG after stage *n*
- `exec-plan.json`, `exec-report.json` — KGpipe execution metadata
- `tmp/` — intermediate artifacts

### 2. Evaluation

Compute metrics for all non-LLM pipelines:

```bash
make evaluation
```

Per-pipeline evaluation uses the same naming as above (`make eval-json-a`, etc.).

Aggregated long-format metrics:

```bash
make concatenate-metrics
```

Produces `all_metrics.csv` under the output root (see benchmark README for layout).

**Single-result evaluation via KGpipe CLI** (example):

```bash
kgpipe eval -c metric_config.yaml \
  -m ReferenceTripleAlignmentMetricSoftEV \
  -m entity_count \
  -m incorrect_relation_direction \
  -m incorrect_relation_cardinality \
  -m incorrect_relation_range \
  -m incorrect_relation_domain \
  -m incorrect_datatype \
  -m incorrect_datatype_format \
  data/results/small/rdf_a/stage_3/result.nt
```

(See [eval.sh](../benchmarks/kgi-bench-movie/eval.sh).)

### 3. Paper content

Generate figures and tables used in the paper (PNG outputs, not LaTeX):

```bash
make paper
```

Or individually:

```bash
make concatenate-metrics
make paper-figtab
```

Outputs: `$OUTPUT_DIR/$DATASET_SELECT/paper/`

For LaTeX table editing, [latex-tables.com](https://www.latex-tables.com/) is helpful.

## Output layout

For `DATASET_SELECT=small` and `OUTPUT_DIR=./data/results/`:

```
data/results/small/
├── all_metrics.csv
├── rdf_a/
│   ├── stage_1/ … stage_3/
│   │   ├── result.nt
│   │   ├── exec-plan.json
│   │   └── exec-report.json
├── json_a/ …
├── rdf_json_text/ … text_json_rdf/         # MSP pipelines (e.g. RDF→JSON→Text)
└── paper/
    ├── test_fig*.png
    └── test_tab*.png
```

## Integration settings (paper)

| Setting | Description | Pipelines in paper |
|---------|-------------|-------------------|
| **SSP** | Three steps, same source format each time | `rdf_a`, `json_a`, `text_a` (+ alternates in repo) |
| **MSP** | Three steps, one format per step | Six combinations of base SSP pipelines (e.g. RJT = RDF→JSON→Text) |

The repository defines additional variants in `pipeline.conf` (`*_b`, `*_llm_*`) beyond the 12 pipelines reported in the paper.

## Cleanup

```bash
make clean   # removes data/ under the benchmark directory
```
