# KGI-Bench documentation

KGI-Bench is the benchmark suite accompanying KGpipe. It defines benchmark datasets and evaluation entrypoints
for comparing generated knowledge graphs.

## Getting started

- Movie benchmark: [movie-benchmark.md](movie-benchmark.md)
- CLI reference: [cli.md](cli.md)

## CLI

KGI-Bench provides a CLI intended to run evaluation on KGpipe pipeline outputs:

```bash
kgibench --help
kgibench evaluate --help
```

List available metrics:

```bash
kgibench list-metrics
```

Movie preset (evaluates `stage_*` directories and writes `eval_results.json` into each stage):

```bash
kgibench evaluate --benchmark movie --bench-data /path/to/movie/dataset /path/to/pipeline_output_dir
```
