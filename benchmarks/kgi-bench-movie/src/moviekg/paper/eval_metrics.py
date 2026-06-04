"""Build paper tables from per-stage ``eval_results.json`` files."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from moviekg.paper.legacy.config import METRIC_NAME_MAP, SEM_METRIC_LONG_NAMES, SEM_METRIC_SHORT_NAMES

# Pretty pipeline labels (aligned with legacy ``test_figtab.py``).
PIPELINE_NAME_PRETTY: dict[str, str] = {
    "json_rdf_text": "JRT",
    "json_text_rdf": "JTR",
    "rdf_json_text": "RJT",
    "rdf_text_json": "RTJ",
    "text_json_rdf": "TJR",
    "text_rdf_json": "TRJ",
    "json_a": "JSON_base",
    "json_b": "JSON_alt",
    "json_c": "JSON_llm",

    "rdf_a": "RDF_base",
    "rdf_b": "RDF_alt",
    "rdf_c": "RDF_llm",

    "text_a": "TEXT_base",
    "text_b": "TEXT_alt",
    "text_c": "TEXT_llm",

    # "rdf_base": "R_A",
    # "rdf_alt": "R_B",
    # "rdf_llm": "R_C",
    # "text_base": "T_A",
    # "text_alt": "T_B",
    # "text_llm": "T_C",
    # "json_base": "J_A",
    # "json_alt": "J_B",
    # "json_llm": "J_C",
    # "json_baseA": "J_baseA",
}

# Count/statistic columns for the stage-3 summary table (legacy ``test_table_with_statistic_metrics``).
STATISTIC_COUNT_MEASUREMENTS = (
    "entity_count",
    "relation_count",
    "triple_count",
    "class_count",
    "property_count",
    "loose_entity_count",
    "shallow_entity_count",
)

# ``property_count`` replaces legacy ``relation_count`` in the new eval API.
_MEASUREMENT_PRETTY = {**METRIC_NAME_MAP, "property_count": "RC"}

STATISTIC_TABLE_COLUMNS = ("pipeline", "FC", "EC", "RC", "TC", "SEC", "Time")

# New-eval metric class -> legacy semantic metric name (``test_tab_3_ssp_semantic_eval.csv``).
SEMANTIC_EVAL_METRICS: dict[str, str] = {
    "DisjointDomainMetric": "disjoint_domain",
    "DomainMetric": "incorrect_relation_domain",
    "RangeMetric": "incorrect_relation_range",
    "RelationDirectionMetric": "incorrect_relation_direction",
    "DatatypeMetric": "incorrect_datatype",
    "DatatypeFormatMetric": "incorrect_datatype_format",
}

GROWTH_METRICS = ("entity_count", "triple_count")


def _eval_result_paths(output_root: Path) -> list[Path]:
    return sorted(output_root.glob("*/*/eval_results.json"))


def _scalar_measurements(eval_path: Path) -> list[dict]:
    """Extract numeric count measurements from one ``eval_results.json``."""
    stage_dir = eval_path.parent
    pipeline_dir = stage_dir.parent
    rows: list[dict] = []

    for entry in json.loads(eval_path.read_text()):
        for measurement in entry.get("measurements") or []:
            name = measurement.get("name")
            value = measurement.get("value")
            if name not in STATISTIC_COUNT_MEASUREMENTS:
                continue
            if not isinstance(value, (int, float)):
                continue
            rows.append(
                {
                    "pipeline": pipeline_dir.name,
                    "stage": stage_dir.name,
                    "metric": name,
                    "value": float(value),
                }
            )
    return rows


def _pipeline_runtime_seconds(pipeline_dir: Path) -> float:
    total = 0.0
    for stage_dir in sorted(pipeline_dir.glob("stage_*")):
        report_path = stage_dir / "exec-report.json"
        if not report_path.exists():
            continue
        report = json.loads(report_path.read_text())
        total += float(report.get("duration", 0.0))
    return total


def eval_results_to_long_df(output_root: Path) -> pd.DataFrame:
    """Long-format table: pipeline, stage, metric, value."""
    rows: list[dict] = []
    for eval_path in _eval_result_paths(output_root):
        rows.extend(_scalar_measurements(eval_path))

    if not rows:
        raise FileNotFoundError(
            f"No count measurements found under {output_root}. "
            "Run evaluation first (e.g. `make evaluation`)."
        )
    return pd.DataFrame(rows)


def duration_rows(output_root: Path, *, stage: str = "stage_3") -> pd.DataFrame:
    pipelines = {p.parent.parent.name for p in _eval_result_paths(output_root)}
    rows = [
        {
            "pipeline": pipeline,
            "stage": stage,
            "metric": "duration",
            "value": _pipeline_runtime_seconds(output_root / pipeline),
        }
        for pipeline in sorted(pipelines)
    ]
    return pd.DataFrame(rows)


def create_statistic_counts_table(
    output_root: Path,
    *,
    stage: str = "stage_3",
) -> pd.DataFrame:
    """
    Wide stage-3 count table (legacy ``test_tab_2_statistic_metrics.csv`` layout).

    Values are read from ``<pipeline>/stage_<n>/eval_results.json``; runtime is the sum
    of ``exec-report.json`` stage durations per pipeline.
    """
    metric_df = eval_results_to_long_df(output_root)
    metric_df = pd.concat([metric_df, duration_rows(output_root, stage=stage)], ignore_index=True)

    metric_df["metric"] = metric_df["metric"].map(_MEASUREMENT_PRETTY)
    metric_df["pipeline"] = metric_df["pipeline"].map(
        lambda name: PIPELINE_NAME_PRETTY.get(name, name)
    )
    metric_df = metric_df[metric_df["stage"] == stage]

    pivot_df = metric_df.pivot_table(
        index=["pipeline", "stage"],
        columns="metric",
        values="value",
        aggfunc="first",
    ).reset_index()
    pivot_df.columns.name = None

    columns = [c for c in STATISTIC_TABLE_COLUMNS if c in pivot_df.columns]
    return pivot_df[columns]


def _parse_eval_path(eval_path: Path) -> tuple[str, str]:
    stage_dir = eval_path.parent
    pipeline_dir = stage_dir.parent
    return pipeline_dir.name, stage_dir.name


def _legacy_rows_from_eval_path(eval_path: Path) -> list[dict]:
    """Convert one ``eval_results.json`` into legacy long-table rows."""
    pipeline, stage = _parse_eval_path(eval_path)
    rows: list[dict] = []

    for entry in json.loads(eval_path.read_text()):
        metric_key = entry.get("metric")
        for measurement in entry.get("measurements") or []:
            name = measurement.get("name")
            value = measurement.get("value")
            if name is None:
                continue

            legacy_metric = SEMANTIC_EVAL_METRICS.get(metric_key)
            if legacy_metric and name == "normalized_score" and isinstance(value, (int, float)):
                rows.append(
                    {
                        "pipeline": pipeline,
                        "stage": stage,
                        "aspect": "semantic",
                        "metric": legacy_metric,
                        "value": float(value),
                        "normalized": float(value),
                        "duration": 0,
                        "details": json.dumps({}, ensure_ascii=False),
                    }
                )
                continue

            value_out = value
            normalized_out = value
            details: dict = {}

            if isinstance(value, (dict, list)):
                value_out = 0
                normalized_out = 0
                if name == "class_occurrence" and isinstance(value, dict):
                    details = {"classes": value}
                elif name == "property_occurrence" and isinstance(value, dict):
                    details = {"properties": value}
                else:
                    details = {"value": value}
            elif not isinstance(value, (int, float)):
                continue

            rows.append(
                {
                    "pipeline": pipeline,
                    "stage": stage,
                    "aspect": "eval_new",
                    "metric": str(name),
                    "value": float(value_out),
                    "normalized": float(normalized_out),
                    "duration": 0,
                    "details": json.dumps(details, ensure_ascii=False, default=str),
                }
            )
    return rows


def eval_results_to_legacy_long_df(output_root: Path) -> pd.DataFrame:
    """
    Long table compatible with legacy plotting helpers
    (columns: pipeline, stage, aspect, metric, value, normalized, duration, details).
    """
    rows: list[dict] = []
    for eval_path in _eval_result_paths(output_root):
        rows.extend(_legacy_rows_from_eval_path(eval_path))

    if not rows:
        raise FileNotFoundError(
            f"No eval_results.json found under {output_root}. "
            "Run evaluation first (e.g. `make evaluation`)."
        )
    return pd.DataFrame(rows)


def create_semantic_metrics_table(
    output_root: Path,
    *,
    stage: str = "stage_3",
) -> pd.DataFrame:
    """Wide semantic table (legacy ``test_tab_3_ssp_semantic_eval.csv`` layout)."""
    df = eval_results_to_legacy_long_df(output_root)
    df = df[(df["stage"] == stage) & (df["aspect"] == "semantic")]
    if df.empty:
        raise ValueError(
            "No semantic/consistency metrics in eval_results.json. "
            "Re-run evaluation with consistency metrics enabled."
        )

    df = df[df["metric"].isin(SEM_METRIC_SHORT_NAMES)]
    df = df.copy()
    df["metric"] = df["metric"].map(SEM_METRIC_SHORT_NAMES)
    df["pipeline"] = df["pipeline"].map(lambda n: PIPELINE_NAME_PRETTY.get(n, n))
    df["normalized"] = df["normalized"].round(3)

    pivot_df = df.pivot(index="metric", columns="pipeline", values="normalized").T
    long_name_row = {col: SEM_METRIC_LONG_NAMES.get(col, col) for col in pivot_df.columns}
    return pd.concat([pd.DataFrame([long_name_row], index=["metric_long_name"]), pivot_df])


def reference_growth_rows_from_dataset(dataset) -> list[dict]:
    """Reference KG counts per stage (pipeline ``reference``) for growth-plot baselines."""
    from kgpipe.common.model.data import DataFormat
    from kgpipe.common.model.kg import KG
    from kgpipe_eval.metrics.statistics import count_measures
    from kgpipe_eval.utils.kg_utils import KgManager

    rows: list[dict] = []
    for i in range(1, 4):
        stage = f"stage_{i}"
        split = dataset.splits.get(f"split_{i}")
        if split is None or split.kg_reference is None:
            continue

        ref_root = split.kg_reference.root
        ref_path = ref_root / "data_agg.nt"
        if not ref_path.exists():
            ref_path = ref_root / "data.nt"
        if not ref_path.exists():
            continue

        tg = KgManager.load_kg(
            KG(
                id="reference",
                name="reference",
                path=ref_path,
                format=DataFormat.RDF_NTRIPLES,
            )
        )
        counts = count_measures(tg)
        for metric in GROWTH_METRICS:
            rows.append(
                {
                    "pipeline": "reference",
                    "stage": stage,
                    "aspect": "reference",
                    "metric": metric,
                    "value": float(getattr(counts, metric)),
                    "normalized": float(getattr(counts, metric)),
                    "duration": 0,
                    "details": json.dumps({}, ensure_ascii=False),
                }
            )
    return rows


def _append_reference_growth_rows(df: pd.DataFrame, dataset) -> pd.DataFrame:
    ref_rows = reference_growth_rows_from_dataset(dataset)
    if not ref_rows:
        return df
    return pd.concat([df, pd.DataFrame(ref_rows)], ignore_index=True)


def _reference_class_counts_from_long_df(df: pd.DataFrame) -> dict[str, dict[str, int]]:
    from collections import defaultdict

    reference: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    ref_df = df[(df["pipeline"] == "reference") & (df["metric"] == "class_occurrence")]
    for stage in ref_df["stage"].unique():
        stage_df = ref_df[ref_df["stage"] == stage]
        if stage_df.empty:
            continue
        details = json.loads(stage_df["details"].values[0])
        for class_name, count in details.get("classes", {}).items():
            reference[stage][class_name.split("/")[-1]] += int(count)
    return reference


def save_growth_figure(
    output_root: Path,
    output_path: Path,
    *,
    metrics: tuple[str, ...] = GROWTH_METRICS,
    dataset=None,
) -> None:
    """Grouped bar chart of KG growth per stage (legacy ``test_fig_both_growth.png``)."""
    from moviekg.paper.legacy.helpers.helpers import plot_growth

    df = eval_results_to_legacy_long_df(output_root)
    if dataset is not None:
        df = _append_reference_growth_rows(df, dataset)
    df = df[df["stage"] != "stage_0"]
    df = df.copy()
    df["pipeline"] = df["pipeline"].replace("json_b2", "json_b")
    df = df.sort_values(by=["stage", "pipeline"])

    g = plot_growth(df, metrics=list(metrics), kind="bar")
    g.fig.subplots_adjust(wspace=0.1)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.savefig(output_path)


def save_class_evolution_figure(output_root: Path, output_path: Path) -> None:
    """Class-occurrence facet chart (legacy ``test_fig_msp_type_reference.png``)."""
    from moviekg.paper.legacy.config import main_classes
    from moviekg.paper.legacy.helpers.helpers import plot_class_occurence_new

    df = eval_results_to_legacy_long_df(output_root)
    for pipeline in ("seed", "json_b", "rdf_b", "text_b", "reference"):
        df = df[df["pipeline"] != pipeline]

    if df[df["metric"] == "class_occurrence"].empty:
        raise ValueError(
            "No class_occurrence measurements in eval_results.json "
            "(expected from CountMetric)."
        )

    reference = _reference_class_counts_from_long_df(df)
    g = plot_class_occurence_new(df, reference, main_classes)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    g.savefig(output_path)
