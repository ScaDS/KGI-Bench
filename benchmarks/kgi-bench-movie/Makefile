.PHONY:

DATASET_URL := https://zenodo.org/record/17246358/files/inc_movie_kg_datasets.tar.gz?download=1
RESULTS_URL := https://zenodo.org/record/17246358/files/inc_movie_kg_results.tar.gz?download=1
BASE_DIR := ./data

# === Helpers ===

# Load env vars from `.env` (preferred) or `env` (fallback).
# Usage:
#   $(LOAD_ENV) <command>
LOAD_ENV = bash -lc 'set -a; if [ -f .env ]; then . .env; elif [ -f env ]; then . ./env; fi; set +a; '

# Convenience variables inside recipes (after LOAD_ENV):
# - OUTPUT_ROOT = $${OUTPUT_DIR}/$${DATASET_SELECT}
# - BENCH_DATA  = dataset root for the selected size

# === Main ===

evaluation:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  echo "Evaluating all pipelines under $$OUTPUT_ROOT"; \
	  for d in "$$OUTPUT_ROOT"/*; do \
	    [ -d "$$d" ] || continue; \
	    echo "==> $$d"; \
	    kgibench evaluate --benchmark movie --bench-data "$$BENCH_DATA" "$$d"; \
	  done \
	'

# === Dataset ===

$(BASE_DIR)/datasets.tar.gz:
	@mkdir -p $(BASE_DIR)
	@cd $(BASE_DIR) && wget $(DATASET_URL) -O datasets.tar.gz

$(BASE_DIR)/datasets/.extracted: $(BASE_DIR)/datasets.tar.gz
	@mkdir -p $(BASE_DIR)/datasets
	@cd $(BASE_DIR) && tar -xzf datasets.tar.gz
	@touch $(BASE_DIR)/datasets/.extracted

download-datasets: $(BASE_DIR)/datasets/.extracted

datasets-eval:
	pytest -v src/moviekg/datasets/test_evaluate_film_data.py

# === RDF ===

eval-rdf-base:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "rdf_base"
	'

eval-rdf-alt:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "rdf_alt"
	'

eval-rdf-llm:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "rdf_llm"
	'

# === JSON ===

eval-json-base:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "json_base"
	'

eval-json-alt:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "json_alt"
	'

eval-json-llm:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "json_llm"
	'

# === TEXT ===

eval-text-base:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "text_a"
	'

eval-text-alt:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "text_b"
	'

eval-text-llm:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "text_c" \
	'

# === MSPs ===

eval-msp-all:
	@$(LOAD_ENV) ' \
	  OUTPUT_ROOT="$$OUTPUT_DIR/$$DATASET_SELECT"; \
	  if [ "$$DATASET_SELECT" = "small" ]; then BENCH_DATA="$$DATASET_SMALL"; \
	  elif [ "$$DATASET_SELECT" = "medium" ]; then BENCH_DATA="$$DATASET_MEDIUM"; \
	  elif [ "$$DATASET_SELECT" = "large" ]; then BENCH_DATA="$$DATASET_LARGE"; \
	  else echo "Invalid DATASET_SELECT=$$DATASET_SELECT"; exit 1; fi; \
	  echo "Evaluating all MSP pipelines under $$OUTPUT_ROOT (dirs with two underscores)"; \
	  pytest -v -s src/moviekg/evaluation/test_eval_refactor.py -k "test_evaluate_new_multisource_pipeline"; \
	'


# === Paper (legacy)
#
# Paper artifacts are currently driven by the legacy CSV aggregation workflow.
# Keep these targets only if you still rely on `all_metrics.csv`.

# === Paper (new)

eval-paper-new:
	pytest -v -s src/moviekg/paper/test_paper_content.py
