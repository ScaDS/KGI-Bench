# CLI

KGI-Bench provides a CLI for dataset preparation and evaluation of KGpipe outputs.

## Help

```bash
kgibench --help
```

## List available metrics

```bash
kgibench list-metrics
kgibench list-metrics --group core
kgibench list-metrics --group aux
```

## Evaluate a KGpipe output (Movie preset)

The Movie preset expects either:
- a pipeline output directory containing `stage_*`, or
- a single `stage_<n>` directory.

It writes `eval_results.json` into each evaluated stage directory.

```bash
kgibench evaluate --benchmark movie \
  --bench-data /path/to/movie/dataset \
  /path/to/pipeline_output_dir
```

Evaluate only one stage:

```bash
kgibench evaluate --benchmark movie \
  --bench-data /path/to/movie/dataset \
  --stage 3 \
  /path/to/pipeline_output_dir
```

## Prepare: subtract graphs

Compute `GRAPH - SUBTRACT_GRAPH`.

```bash
kgibench prepare subtract graph.nt subtract.nt -o out.nt
```

Preserve labels and/or types for remaining resources:

```bash
kgibench prepare subtract graph.nt subtract.nt -o out.nt --keep-labels
kgibench prepare subtract graph.nt subtract.nt -o out.nt --keep-types
kgibench prepare subtract graph.nt subtract.nt -o out.nt --keep-labels --keep-types
```

