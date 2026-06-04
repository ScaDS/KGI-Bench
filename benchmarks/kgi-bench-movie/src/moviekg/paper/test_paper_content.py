import json
from pathlib import Path

import pytest

try:
    from moviekg import config as moviekg_config
except Exception as e:
    pytest.skip(
        f"MovieKG config not available for eval integration test: {e}",
        allow_module_level=True,
    )

from moviekg.paper.eval_metrics import (
    create_semantic_metrics_table,
    create_statistic_counts_table,
    save_class_evolution_figure,
    save_growth_figure,
)


def _eval_result_paths():
    return sorted(moviekg_config.OUTPUT_ROOT.glob("*/*/eval_results.json"))


def _paper_output_dir() -> Path:
    out = moviekg_config.OUTPUT_ROOT / "paper"
    out.mkdir(parents=True, exist_ok=True)
    return out


# @pytest.mark.parametrize(
#     "eval_path",
#     _eval_result_paths(),
#     ids=lambda p: str(p.relative_to(moviekg_config.OUTPUT_ROOT)),
# )
def test_eval_results_readable():
    for eval_path in _eval_result_paths():
        print(eval_path)


def test_create_counts_table():
    pivot_df = create_statistic_counts_table(moviekg_config.OUTPUT_ROOT)

    assert not pivot_df.empty
    assert list(pivot_df.columns[:1]) == ["pipeline"]
    for col in ("FC", "EC", "RC", "TC", "Time"):
        assert col in pivot_df.columns, f"missing column {col}"

    output_path = _paper_output_dir() / "new_test_tab_2_statistic_metrics.csv"
    pivot_df.to_csv(output_path, sep="\t", index=False)

    written = output_path.read_text()
    assert "pipeline" in written
    assert "FC" in written


def test_create_growth_figure():
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")

    output_path = _paper_output_dir() / "new_test_fig_both_growth.png"
    save_growth_figure(
        moviekg_config.OUTPUT_ROOT,
        output_path,
        dataset=moviekg_config.dataset,
    )
    assert output_path.exists()
    assert output_path.stat().st_size > 0


def test_create_semantic_table():
    try:
        pivot_df = create_semantic_metrics_table(moviekg_config.OUTPUT_ROOT)
    except ValueError as exc:
        pytest.skip(str(exc))

    assert not pivot_df.empty

    output_path = _paper_output_dir() / "new_test_tab_3_ssp_semantic_eval.csv"
    pivot_df.to_csv(output_path, sep="\t")
    assert "metric_long_name" in output_path.read_text()


def test_create_class_evolution_figure():
    pytest.importorskip("matplotlib")
    pytest.importorskip("seaborn")

    output_path = _paper_output_dir() / "new_test_fig_msp_type_reference.png"
    save_class_evolution_figure(moviekg_config.OUTPUT_ROOT, output_path)
    assert output_path.exists()
    assert output_path.stat().st_size > 0
