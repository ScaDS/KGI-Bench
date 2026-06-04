.PHONY:

DATASET_URL := https://zenodo.org/record/17246358/files/inc_movie_kg_datasets.tar.gz?download=1
RESULTS_URL := https://zenodo.org/record/17246358/files/inc_movie_kg_results.tar.gz?download=1
BASE_DIR := ./data

# === Main ===

download-all: download-datasets download-results

eval-all: eval-rdf-base eval-rdf-alt eval-rdf-llm eval-json-base eval-json-alt eval-json-llm eval-text-base eval-text-alt eval-msp-all

# === Python Install ===

python-setup:
	cd ../.. && uv pip install -e .

# === Dataset ===

$(BASE_DIR)/datasets.tar.gz:
	@mkdir -p $(BASE_DIR)
	@cd $(BASE_DIR) && wget $(DATASET_URL) -O datasets.tar.gz

$(BASE_DIR)/datasets/.extracted: $(BASE_DIR)/datasets.tar.gz
	@mkdir -p $(BASE_DIR)/datasets
	@cd $(BASE_DIR) && tar -xzf datasets.tar.gz
	@touch $(BASE_DIR)/datasets/.extracted

download-datasets: $(BASE_DIR)/datasets/.extracted

$(BASE_DIR)/results.tar.gz:
	@mkdir -p $(BASE_DIR)
	@cd $(BASE_DIR) && wget $(RESULTS_URL) -O results.tar.gz

$(BASE_DIR)/results/.extracted: $(BASE_DIR)/results.tar.gz
	@mkdir -p $(BASE_DIR)/results
	@cd $(BASE_DIR) && tar -xzf results.tar.gz
	@touch $(BASE_DIR)/results/.extracted

download-results: $(BASE_DIR)/results/.extracted

# === SEED and REF stats ===

datasets-eval:
	pytest -v src/moviekg/datasets/test_evaluate_film_data.py

# === RDF ===

eval-rdf-base:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "rdf_a" \

eval-rdf-alt:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "rdf_b" \

eval-rdf-llm:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "rdf_c" \

# === JSON ===

eval-json-base:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "json_a"

eval-json-alt:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "json_b"

eval-json-llm:
	DATASET_SELECT=medium pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "json_c"

# === TEXT ===

eval-text-base:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "text_a"

eval-text-alt:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "text_b"

eval-text-llm:
	DATASET_SELECT=medium pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "text_c"

# === MSPs ===

eval-msp-all:
	DATASET_SELECT=large pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "test_evaluate_new_multisource_pipeline"

# === Paper (legacy)
#
# Paper artifacts are currently driven by the legacy CSV aggregation workflow.
# Keep these targets only if you still rely on `all_metrics.csv`.

# === Paper (new)

paper-content:
	DATASET_SELECT=large pytest -v -s src/moviekg/paper/test_paper_content.py
