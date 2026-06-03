from kgpipe_eval.metrics import CountMetric, DuplicateMetric
from typing import List
from kgpipe_eval.api import MetricConfig, MetricResult
from kgpipe_eval.metrics.statistics import CountMetric
from kgpipe_eval.metrics.duplicates import DuplicateConfig, DuplicateMetric
from kgpipe_eval.metrics.entity_alignment import EntityAlignmentMetric
from kgpipe_eval.metrics.triple_alignment import TripleAlignmentConfig, TripleAlignmentMetric
from kgpipe_eval.metrics.consistency_violations import ConsistencyViolationsConfig, DisjointDomainMetric, DomainMetric, RangeMetric, RelationDirectionMetric, DatatypeMetric, DatatypeFormatMetric
from kgpipe_eval.utils.alignment_utils import EntityAlignmentConfig
from kgpipe_eval.utils.kg_utils import KgLike, KgManager
from kgpipe_eval.evaluator import Evaluator
from pydantic import BaseModel, ConfigDict

from kgpipe.datasets.multipart_multisource import Dataset, load_dataset
from kgpipe_eval.test.utils import render_metric_result
from pathlib import Path
import pytest
from kgpipe.common.model.pipeline import KgPipePlan, KgPipeReport
from kgpipe.common.model.kg import KG
from kgpipe.common.model.data import DataFormat
import json
from dataclasses import asdict
from itertools import permutations
from typing import Set
from kgpipe_eval.utils.kg_utils import Term

import os
from dotenv import load_dotenv
load_dotenv()

from kgpipe.io.pipe_out import load_pipe_out, load_stage_out, StageOut

try:
    from moviekg import config as moviekg_config
    from moviekg.config import DATASET_DIR, ssp, idfn
except Exception as e:
    # These are integration-style tests that depend on local env/config files.
    import traceback
    traceback.print_exc()
    pytest.skip(f"MovieKG config not available for eval integration test: {e}", allow_module_level=True)


# TODO clearify
# substract seed from kg_1 and kg_1 from kg_2, or only seed from kg_1 and kg_2

EX_BENCH_DATA_PATH=Path(DATASET_DIR)


# TODO is a wrapper interface for now, Dataset needs refactor later
# TODO can be abstracted and implemented to have direct method per type, so dict is not needed for access
class KgBenchData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    dataset: Dataset
    
    @staticmethod
    def from_path(path: Path) -> 'KgBenchData':
        dataset = load_dataset(path)
        return KgBenchData(dataset=dataset)

    def get_verified_entities_path(self, i: int, source_type: str) -> Path:
        current_path = self.dataset.splits[f"split_{i}"].kg_reference.meta.entities.file
        current_new = current_path.with_name(f"{current_path.stem}_no_seed{current_path.suffix}")
        return current_new

    def get_ignored_entities(self, i: int, source_type: str) -> Set[Term]:
        seed_entities = self.dataset.splits[f"split_{0}"].kg_seed.meta.entities.read_csv()
        # source_seed_entities = self.dataset.splits[f"split_{i-1}"].sources[source_type].meta.entities.read_csv()
        return set([entity.entity_id for entity in seed_entities]) # + [entity.entity_id for entity in source_seed_entities])


class KgPipeData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    result_kg: KgLike  # name=rdf_a_1
    plan: KgPipePlan
    report: KgPipeReport
    tmp_dir: Path

def build_config_dict(i: int, pipe_data: KgPipeData, bench_data: KgBenchData) -> dict[str, MetricConfig]:
    dup_cfg = DuplicateConfig(
        entity_alignment_config=EntityAlignmentConfig(
            method="label_embedding",
            verified_entities_path=bench_data.get_verified_entities_path(i=i, source_type="rdf"), # TODO type needs to be derived from pipe_data
            verified_entities_delimiter="\t",
            entity_sim_threshold=0.95,
        )
    )

    tri_cfg = TripleAlignmentConfig(
        reference_kg=bench_data.dataset.splits[f"split_{i}"].kg_reference.root / "data_agg_eval_noo.nt",
        entity_alignment_config=EntityAlignmentConfig(
            method="label_embedding",
            reference_kg=bench_data.dataset.splits[f"split_{i}"].kg_reference.root / "data_agg_eval_noo.nt",
            # verified_entities_path=bench_data.get_verified_entities_path(i=i, source_type="rdf"), # TODO type needs to be derived from pipe_data
            # verified_entities_delimiter="\t",
            entity_sim_threshold=0.95,
        ),
        value_sim_threshold=0.5,
        cache_literal_embeddings=True,
        cache_ref_literal_embeddings=True,
    )

    ent_cfg = EntityAlignmentConfig(
        method="label_embedding_and_intersecting_type",
        verified_entities_path=bench_data.get_verified_entities_path(i=i, source_type="rdf"), # TODO type needs to be derived from pipe_data
        verified_entities_delimiter="\t",
        entity_sim_threshold=0.95,
        ignored_entities=bench_data.get_ignored_entities(i=i, source_type="rdf") # TODO type needs to be derived from pipe_data
    )

    consistency_cfg = ConsistencyViolationsConfig(
        # reference_kg=bench_data.dataset.splits[f"split_{i}"].kg_reference.root / "data_agg_eval_noo.nt",
        ontology_path=os.getenv("ONTOLOGY_PATH"),
    )

    return {
        "DuplicateMetric": dup_cfg,
        "EntityAlignmentMetric": ent_cfg,
        "TripleAlignmentMetric": tri_cfg,
        "DisjointDomainMetric": consistency_cfg,
        "DomainMetric": consistency_cfg,
        "RangeMetric": consistency_cfg,
        "RelationDirectionMetric": consistency_cfg,
        "DatatypeMetric": consistency_cfg,
        "DatatypeFormatMetric": consistency_cfg,
    }


def evaluate_stage(i: int, pipe_data: KgPipeData, bench_data: KgBenchData) -> List[MetricResult]:
    tg = KgManager.load_kg(pipe_data.result_kg)
    tg_no_seed = KgManager.load_kg(pipe_data.result_kg.path.absolute().parent / "result_eval.nt")

    metrics = [
        CountMetric(), 
        DisjointDomainMetric(),
        DomainMetric(),
        RangeMetric(),
        RelationDirectionMetric(),
        DatatypeMetric(),
        DatatypeFormatMetric(),
    ]

    no_seed_metrics = [
        EntityAlignmentMetric(),
        DuplicateMetric(),
        TripleAlignmentMetric(),
    ]
    config_dict = build_config_dict(i, pipe_data, bench_data)
    return Evaluator().run(tg, metrics, config_dict) + Evaluator().run(tg_no_seed, no_seed_metrics, config_dict)


def evaluate_stage_out(stage_out: StageOut, bench_data: KgBenchData) -> List[MetricResult]:
    """
    Canonical evaluation entrypoint using KGpipe's on-disk output wrappers.
    """
    i = int(stage_out.stage_name.split("_", 1)[1])
    pipe_data = KgPipeData(
        result_kg=KG(
            name=stage_out.root.name,
            id=stage_out.root.name,
            path=stage_out.resultKG,
            format=DataFormat.RDF_NTRIPLES,
        ),
        plan=stage_out.plan,
        report=KgPipeReport.from_path(stage_out.root / "exec-report.json"),
        tmp_dir=stage_out.root / "tmp",
    )
    return evaluate_stage(i=i, pipe_data=pipe_data, bench_data=bench_data)


def _metric_results_to_jsonable(results: list[MetricResult]) -> list[dict]:
    """
    Convert `MetricResult` dataclasses to JSON-serializable dicts.

    `MetricResult.metric` is an object instance, so we store its key/classname.
    """
    out: list[dict] = []
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

@pytest.mark.parametrize(
    "pipeline_name",
    list[str](moviekg_config.pipeline_types.keys()) + list[str](moviekg_config.llm_pipeline_types.keys()),
)
def test_evaluate_new(pipeline_name: str):
    """
    Boilerplate integration test that runs the new eval API for each pipeline
    output under `OUTPUT_ROOT/<pipeline_name>/stage_*`.
    """
    output_dir = moviekg_config.OUTPUT_ROOT / pipeline_name

    if not output_dir.exists():
        pytest.skip(f"Pipeline output directory {output_dir} not found")

    pipe_out = load_pipe_out(output_dir)
    if not pipe_out.stages:
        pytest.skip(f"No stage directories found under {output_dir}")

    # Uses the dataset selected/configured via `moviekg.config` env vars.
    bench_data = KgBenchData.from_path(EX_BENCH_DATA_PATH)

    for stage_out in pipe_out.stages:
        i = int(stage_out.stage_name.split("_", 1)[1])
        # if i != 3:
        #     continue # only run for stage 3
        results = evaluate_stage_out(stage_out=stage_out, bench_data=bench_data)

        eval_results = _metric_results_to_jsonable(results)
        with open(stage_out.root / "eval_results.json", "w") as f:
            json.dump(eval_results, f, indent=2)
            print(f"Wrote results to {stage_out.root / 'eval_results.json'}")

        # Smoke checks: we got metric results back for this stage.
        assert isinstance(results, list)
        assert results


@pytest.mark.parametrize(
    "source_1, source_2, source_3",
    permutations(list[str](ssp.keys()), 3),
    ids=idfn,
)
def test_evaluate_new_multisource_pipeline(source_1: str, source_2: str, source_3: str):
    """
    Integration test for the *multi-source* incremental pipelines where the selected
    source changes per iteration/stage (e.g. `a_b_c/stage_1`, `a_b_c/stage_2`, ...).
    """
    pipeline_name = f"{source_1}_{source_2}_{source_3}"
    output_dir = moviekg_config.OUTPUT_ROOT / pipeline_name

    if not output_dir.exists():
        pytest.skip(f"Pipeline output directory {output_dir} not found")

    pipe_out = load_pipe_out(output_dir)
    if not pipe_out.stages:
        pytest.skip(f"No stage directories found under {output_dir}")

    bench_data = KgBenchData.from_path(EX_BENCH_DATA_PATH)

    for stage_out in pipe_out.stages:
        i = int(stage_out.stage_name.split("_", 1)[1])
        # if i != 3:
        #     continue # only run for stage 3
        results = evaluate_stage_out(stage_out=stage_out, bench_data=bench_data)

        eval_results = _metric_results_to_jsonable(results)
        with open(stage_out.root / "eval_results.json", "w") as f:
            json.dump(eval_results, f, indent=2)

        assert isinstance(results, list)
        assert results
