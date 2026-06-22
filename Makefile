LLM_MODEL ?= iKhalid/ALLaM:7b

.PHONY: up up-ollama down build logs pull-model pipeline pipeline-all eval offline-demo ps seed-data

up:		## Build + start app + postgres + dashboard (Ollama on host)
	docker compose up -d --build

up-ollama:	## Also start a containerised Ollama (Linux / GPU-in-Docker hosts)
	docker compose --profile with-ollama up -d --build

down:		## Stop services
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

pull-model:	## Pull ALLaM (only for the containerised --profile with-ollama)
	docker compose exec ollama ollama pull $(LLM_MODEL)

seed-data:	## Load datasets into Postgres (raw_* + answer-key tables)
	docker compose exec app python ingestion/seed_postgres.py

pipeline:	## Run pipeline on 300 rows/file (quick)
	docker compose exec app python pipeline.py --max-per-file 300

pipeline-all:	## Run pipeline on the full dataset
	docker compose exec app python pipeline.py

eval:		## Score the last run against the answer keys
	docker compose exec app python evaluate.py

offline-demo:	## Run the pipeline WITHOUT the LLM (rules + keyword fallback)
	docker compose exec -e LLM_MODE=offline app python pipeline.py --max-per-file 500
