import os
from pathlib import Path
from dotenv import load_dotenv

from kgpipe.common.discovery import discover_entry_points
from kgpipe.generation.loaders import load_pipeline_catalog
from kgpipe.datasets.multipart_multisource import load_dataset, Dataset

load_dotenv(override=False)
discover_entry_points()

PIPELINE_CONFIG=os.getenv("PIPELINE_CONFIG")
ONTOLOGY_PATH=os.getenv("ONTOLOGY_PATH")
OUTPUT_DIR=os.getenv("OUTPUT_DIR")

DATASET_SMALL_DIR=os.getenv("DATASET_SMALL")
DATASET_MEDIUM_DIR=os.getenv("DATASET_MEDIUM")
DATASET_LARGE_DIR=os.getenv("DATASET_LARGE")
DATASET_SELECT=os.getenv("DATASET_SELECT", "small")

if not ONTOLOGY_PATH:
    raise ValueError("MISSING ONTOLOGY PATH")

if not DATASET_SELECT:
    raise ValueError("MISSING DATASET SELECT")

DATASET_DIR = ""

if DATASET_SELECT == "small" and DATASET_SMALL_DIR:
    dataset = load_dataset(Path(DATASET_SMALL_DIR))
    DATASET_DIR = DATASET_SMALL_DIR
elif DATASET_SELECT == "medium" and DATASET_MEDIUM_DIR:
    dataset = load_dataset(Path(DATASET_MEDIUM_DIR))
    DATASET_DIR = DATASET_MEDIUM_DIR
elif DATASET_SELECT == "large" and DATASET_LARGE_DIR:
    dataset = load_dataset(Path(DATASET_LARGE_DIR))
    DATASET_DIR = DATASET_LARGE_DIR
else:
    raise ValueError("INVALID DATASET SELECT")

if not OUTPUT_DIR:
    raise ValueError("MISSING OUTPUT DIRECTORY")
OUTPUT_ROOT = Path(OUTPUT_DIR) / DATASET_SELECT


def idfn(param):
    # param is a tuple like ("text", "json", "rdf")
    if isinstance(param, tuple):
        return "-".join(param)
    return str(param)

pipeline_types_new = {
    "rdf_base": "rdf",
    "rdf_alt": "rdf",
    "text_base": "text",
    "text_alt": "text",
    "json_base": "json",
    "json_alt": "json",
}

pipeline_types = {
    "rdf_a": "rdf",
    "rdf_b": "rdf",
    "text_a": "text",
    "text_b": "text",
    "json_a": "json",
    "json_b": "json",
}

llm_pipeline_types_new = {
    "rdf_llm": "rdf",
    "json_llm": "json",
    "text_llm": "text",
}

llm_pipeline_types = {
    "rdf_llm_schema_align_v1": "rdf",
    "json_llm_mapping_v1": "json",
    "text_llm_triple_extract_v1": "text",
}

ssp = {
    "rdf": "rdf_base",
    "json": "json_alt",
    "text": "text_base",
}