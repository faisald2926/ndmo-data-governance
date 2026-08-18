LLM_MODEL ?= iKhalid/ALLaM:7b

.PHONY: up up-ollama down build logs pull-model pipeline pipeline-all eval offline-demo ps seed-data

up:            ## Build + start app + postgres + dashboard (Ollama on host)
	docker compose up -d --build

up-ollama:     ## Also start a containerised Ollama (Linux / GPU-in-Docker hosts)
	docker compose --profile with-ollama up -d --build

down:          ## Stop services
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

ps:
	docker compose ps

pull-model:    ## Pull ALLaM into Ollama (run once after `make up`)
	docker compose exec ollama ollama pull $(LLM_MODEL)

pipeline:      ## Run pipeline on 300 rows/file (quick)
	docker compose exec app python pipeline.py --max-per-file 300

pipeline-all:  ## Run pipeline on the full dataset
	docker compose exec app python pipeline.py

eval:          ## Score the last run against the answer keys
	docker compose exec app python evaluate.py

seed-data:     ## Load the datasets into Postgres as raw_* + answer-key tables
	docker compose exec app python -m ingestion.seed_postgres

offline-demo:  ## Run the whole pipeline WITHOUT the LLM (rules + keyword fallback)
	docker compose exec -e LLM_MODE=offline app python pipeline.py --max-per-file 500
