#!/usr/bin/env bash
# Pull the local model into the running Ollama container.
set -euo pipefail
MODEL="${1:-iKhalid/ALLaM:7b}"
echo "Pulling $MODEL into Ollama (first time can take several minutes)…"
docker compose exec ollama ollama pull "$MODEL"
echo "Done. Verify with: docker compose exec ollama ollama list"
