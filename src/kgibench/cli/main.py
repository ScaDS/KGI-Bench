from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Set

import click
from rich.console import Console

from rdflib import Graph

from kgpipe_eval.evaluator import Evaluator as KgpipeEvaluator
from kgpipe_eval.api import MetricResult, Metric
from kgpipe_eval.utils.kg_utils import KgManager

from kgibench.metrics.core import CountMetric
from kgibench.metrics import core as core_metrics
from kgibench.metrics import auxiliary as auxiliary_metrics

from kgpipe.datasets.multipart_multisource import Dataset, load_dataset
from kgpipe_eval.metrics.duplicates import DuplicateConfig, DuplicateMetric
from kgpipe_eval.metrics.entity_alignment import EntityAlignmentMetric
from kgpipe_eval.metrics.triple_alignment import TripleAlignmentConfig, TripleAlignmentMetric
from kgpipe_eval.utils.alignment_utils import EntityAlignmentConfig
from kgpipe_eval.utils.kg_utils import Term


console = Console()

@click.group()
def cli() -> None:
    """
    KGI-Bench CLI
    """
    pass

@cli.group(name="prepare", invoke_without_command=True)
@click.pass_context
def prepare_cmd(ctx: click.Context) -> None:
    """
    Dataset / KG preparation utilities.
    """
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@prepare_cmd.command(name="subtract")
@click.argument("graph", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.argument("subtract_graph", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option(
    "--output",
    "-o",
    required=True,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output path for the subtracted graph (format inferred from extension).",
)
@click.option(
    "--keep-labels",
    is_flag=True,
    help="Preserve rdfs:label triples for remaining resources.",
)
@click.option(
    "--keep-types",
    is_flag=True,
    help="Preserve rdf:type triples for remaining resources.",
)
def prepare_subtract_cmd(
    graph: Path,
    subtract_graph: Path,
    output: Path,
    keep_labels: bool,
    keep_types: bool,
) -> None:
    """
    Subtract one RDF graph from another.

    Computes: GRAPH - SUBTRACT_GRAPH
    """
    from kgibench.utils.prepare import (
        substract_graph_from_graph,
        substract_graph_from_graph_keep_labels,
        substract_graph_from_graph_keep_types,
        substract_graph_from_graph_keep_labels_and_types,
    )

    g = Graph()
    g.parse(graph)
    sg = Graph()
    sg.parse(subtract_graph)

    if keep_labels and keep_types:
        out = substract_graph_from_graph_keep_labels_and_types(g, sg)
    elif keep_labels:
        out = substract_graph_from_graph_keep_labels(g, sg)
    elif keep_types:
        out = substract_graph_from_graph_keep_types(g, sg)
    else:
        out = substract_graph_from_graph(g, sg)

    output.parent.mkdir(parents=True, exist_ok=True)
    # rdflib infers serializer from extension poorly; default to nt if unknown.
    suffix = output.suffix.lower()
    fmt = "nt" if suffix in (".nt", ".ntriples") else None
    out.serialize(destination=str(output), format=fmt)
    console.print(f"[green]✓ Wrote[/green] {output} ({len(out)} triples)")


@cli.command(name="list-metrics")
@click.option(
    "--group",
    "group_name",
    type=click.Choice(["core", "aux", "all"], case_sensitive=False),
    default="all",
    show_default=True,
    help="Which metric group to list.",
)
def list_metrics_cmd(group_name: str) -> None:
    """
    List available metric keys/names.
    """
    group_name = group_name.lower()

    mods = {
        "core": (core_metrics,),
        "aux": (auxiliary_metrics,),
        "all": (core_metrics, auxiliary_metrics),
    }[group_name]

    metric_types: list[type[Metric]] = []
    for mod in mods:
        for name in getattr(mod, "__all__", []):
            obj = getattr(mod, name, None)
            if obj is not None:
                metric_types.append(obj)

    # De-duplicate by key (preferred) then by class name.
    seen: set[str] = set()
    rows: list[tuple[str, str]] = []
    for mt in metric_types:
        key = getattr(mt, "key", mt.__name__)
        if key in seen:
            continue
        seen.add(key)
        desc = getattr(mt, "description", "")
        rows.append((key, desc))

    if not rows:
        console.print("[yellow]No metrics found.[/yellow]")
        return

    console.print(f"[bold]Available metrics ({group_name})[/bold]")
    for key, desc in sorted(rows, key=lambda r: r[0].lower()):
        if desc:
            console.print(f"- [cyan]{key}[/cyan]: {desc}")
        else:
            console.print(f"- [cyan]{key}[/cyan]")


def _resolve_kg_input(input_path: Path) -> Path:
    """
    Accept either:
    - a KG file path (e.g. .nt/.ttl/.rdf)
    - a KGpipe stage output directory containing `result_eval.nt` (preferred) or `result.nt`
    """
    if input_path.is_file():
        return input_path

    if not input_path.is_dir():
        raise click.ClickException(f"Input path not found: {input_path}")

    candidates = [
        input_path / "result_eval.nt",
        input_path / "result.nt",
        input_path / "result.nt.gz",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c

    raise click.ClickException(
        "Could not find a KG file in the provided directory. "
        "Expected one of: result_eval.nt, result.nt, result.nt.gz"
    )


def _metric_registry() -> Dict[str, type[Metric]]:
    """
    Registry of available metrics by key/classname.

    KGI-Bench currently re-exports metrics from `kgpipe_eval`. We expose them here so the CLI can select them
    by name without requiring users to import Python code.
    """
    metric_types: list[type[Metric]] = []
    for mod in (core_metrics, auxiliary_metrics):
        for name in getattr(mod, "__all__", []):
            obj = getattr(mod, name, None)
            if obj is not None:
                metric_types.append(obj)

    out: Dict[str, type[Metric]] = {}
    for mt in metric_types:
        key = getattr(mt, "key", mt.__name__)
        out[key] = mt
        out[mt.__name__] = mt
    return out


def _results_to_jsonable(results: Sequence[MetricResult]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for r in results:
        metric_key = getattr(r.metric, "key", None) or r.metric.__class__.__name__
        out.append(
            {
                "metric": metric_key,
                "summary": r.summary,
                "measurements": [asdict(m) for m in r.measurements],
            }
        )
    return out


def _stage_dirs(output_dir: Path) -> list[Path]:
    stage_dirs = [p for p in output_dir.iterdir() if p.is_dir() and p.name.startswith("stage_")]
    stage_dirs.sort(key=lambda p: int(p.name.split("_", 1)[1]))
    return stage_dirs


def _stage_index(stage_dir: Path) -> int:
    try:
        return int(stage_dir.name.split("_", 1)[1])
    except Exception as e:
        raise click.ClickException(f"Invalid stage dir name (expected stage_<n>): {stage_dir.name}") from e


def _movie_bench_verified_entities_path(dataset: Dataset, i: int) -> Path:
    """
    Movie benchmark convention: use the reference entities file with the `_no_seed` suffix.
    """
    current_path = dataset.splits[f"split_{i}"].kg_reference.meta.entities.file
    return current_path.with_name(f"{current_path.stem}_no_seed{current_path.suffix}")


def _movie_bench_ignored_entities(dataset: Dataset) -> Set[Term]:
    """
    Ignore seed entities for incremental evaluation.
    """
    seed_entities = dataset.splits["split_0"].kg_seed.meta.entities.read_csv()
    return set([entity.entity_id for entity in seed_entities])


def _movie_confs(dataset: Dataset, stage_i: int) -> dict[str, Any]:
    verified_entities_path = _movie_bench_verified_entities_path(dataset, stage_i)
    if not verified_entities_path.exists():
        raise click.ClickException(
            f"Verified entities file not found for split_{stage_i}: {verified_entities_path}"
        )

    # NOTE: reference KG path is benchmark-specific.
    # In the current Movie benchmark layout it lives under the reference split as `data_agg_eval_noo.nt`.
    reference_kg = dataset.splits[f"split_{stage_i}"].kg_reference.root / "data_agg_eval_noo.nt"
    if not reference_kg.exists():
        raise click.ClickException(f"Reference KG not found for split_{stage_i}: {reference_kg}")

    dup_cfg = DuplicateConfig(
        entity_alignment_config=EntityAlignmentConfig(
            method="label_embedding",
            verified_entities_path=verified_entities_path,
            verified_entities_delimiter="\t",
            entity_sim_threshold=0.95,
        )
    )

    tri_cfg = TripleAlignmentConfig(
        reference_kg=reference_kg,
        entity_alignment_config=EntityAlignmentConfig(
            method="label_embedding",
            reference_kg=reference_kg,
            entity_sim_threshold=0.95,
        ),
        value_sim_threshold=0.5,
        cache_literal_embeddings=True,
        cache_ref_literal_embeddings=True,
    )

    ent_cfg = EntityAlignmentConfig(
        method="label_embedding_and_intersecting_type",
        verified_entities_path=verified_entities_path,
        verified_entities_delimiter="\t",
        entity_sim_threshold=0.95,
        ignored_entities=_movie_bench_ignored_entities(dataset),
    )

    return {
        "DuplicateMetric": dup_cfg,
        "EntityAlignmentMetric": ent_cfg,
        "TripleAlignmentMetric": tri_cfg,
    }


@cli.command(name="evaluate")
@click.argument("input", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--metrics",
    "-m",
    multiple=True,
    help=(
        "Metric key/name to run (repeatable). "
        "If omitted, runs CountMetric only. "
        "Examples: -m CountMetric -m DuplicateMetric"
    ),
)
@click.option(
    "--confs-json",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    default=None,
    help=(
        "Optional JSON file containing a dict of per-metric configs keyed by metric key. "
        "Note: only metrics whose config objects are JSON-constructible will work without additional glue."
    ),
)
@click.option(
    "--output",
    "-o",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Write JSON results to this path (default: <input_dir>/eval_results.json or ./eval_results.json).",
)
@click.option(
    "--benchmark",
    type=click.Choice(["movie"], case_sensitive=False),
    default=None,
    help="Use a benchmark preset (builds metric set + configs automatically).",
)
@click.option(
    "--bench-data",
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=None,
    help="Path to the benchmark dataset root (required for --benchmark movie).",
)
@click.option(
    "--stage",
    type=int,
    default=None,
    help="If INPUT is a pipeline output dir with stage_* subdirs, evaluate only this stage number.",
)
def evaluate_cmd(
    input: Path,
    metrics: tuple[str, ...],
    confs_json: Path | None,
    output: Path | None,
    benchmark: str | None,
    bench_data: Path | None,
    stage: int | None,
) -> None:
    """
    Evaluate a generated KG with selected metrics (new `kgpipe_eval` API).

    INPUT may be a KG file (e.g. .nt) or a KGpipe stage output directory containing `result_eval.nt`.
    """
    # Benchmark preset: evaluate an entire pipeline output directory (stage_*) with curated configs.
    if benchmark is not None:
        if benchmark.lower() != "movie":
            raise click.ClickException(f"Unknown benchmark preset: {benchmark}")
        if bench_data is None:
            raise click.ClickException("--bench-data is required when using --benchmark movie")

        dataset = load_dataset(bench_data)

        # INPUT is expected to be a pipeline output directory with stage_*.
        if input.is_dir() and any(p.is_dir() and p.name.startswith("stage_") for p in input.iterdir()):
            stage_dirs = _stage_dirs(input)
        elif input.is_dir() and input.name.startswith("stage_"):
            stage_dirs = [input]
        else:
            raise click.ClickException(
                "--benchmark movie expects INPUT to be a pipeline output dir containing stage_* "
                "or a single stage_<n> directory."
            )

        if stage is not None:
            stage_dirs = [sd for sd in stage_dirs if _stage_index(sd) == stage]
            if not stage_dirs:
                raise click.ClickException(f"No stage_{stage} found under {input}")

        for stage_dir in stage_dirs:
            i = _stage_index(stage_dir)
            kg_path = _resolve_kg_input(stage_dir)
            console.print(f"[bold]Loading KG[/bold] (stage {i}): {kg_path}")
            tg = KgManager.load_kg(kg_path)

            metric_objs: List[Metric] = [
                CountMetric(),
                EntityAlignmentMetric(),
                DuplicateMetric(),
                TripleAlignmentMetric(),
            ]
            confs = _movie_confs(dataset, i)

            console.print(
                f"[bold]Running metrics[/bold] (stage {i}): "
                f"{', '.join(getattr(m, 'key', m.__class__.__name__) for m in metric_objs)}"
            )
            results = KgpipeEvaluator().run(tg, metric_objs, confs)

            out_path = stage_dir / "eval_results.json"
            out_path.write_text(json.dumps(_results_to_jsonable(results), indent=2))
            console.print(f"[green]✓ Wrote[/green] {out_path}")
        return

    kg_path = _resolve_kg_input(input)
    console.print(f"[bold]Loading KG[/bold]: {kg_path}")

    tg = KgManager.load_kg(kg_path)

    reg = _metric_registry()
    if metrics:
        unknown = [m for m in metrics if m not in reg]
        if unknown:
            known = ", ".join(sorted(set(reg.keys())))
            raise click.ClickException(f"Unknown metric(s): {unknown}. Known: {known}")
        metric_objs: List[Metric] = [reg[m]() for m in metrics]
    else:
        metric_objs = [CountMetric()]

    confs: Mapping[str, Any] | None = None
    if confs_json is not None:
        confs = json.loads(confs_json.read_text())
        if not isinstance(confs, dict):
            raise click.ClickException("--confs-json must be a JSON object (dict)")

    console.print(f"[bold]Running metrics[/bold]: {', '.join(getattr(m, 'key', m.__class__.__name__) for m in metric_objs)}")
    results = KgpipeEvaluator().run(tg, metric_objs, confs)

    out_path: Path
    if output is not None:
        out_path = output
    else:
        out_path = (input / "eval_results.json") if input.is_dir() else Path("eval_results.json")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(_results_to_jsonable(results), indent=2))
    console.print(f"[green]✓ Wrote[/green] {out_path}")