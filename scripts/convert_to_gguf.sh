#!/usr/bin/env bash
# Convert the OFFICIAL ALLaM safetensors -> GGUF and quantize for an 8 GB GPU.
# Only needed if you want to run the exact downloaded weights instead of
# `ollama pull iKhalid/ALLaM:7b`. Requires llama.cpp:
#   git clone https://github.com/ggerganov/llama.cpp && cd llama.cpp && make
#
# Usage:  bash scripts/convert_to_gguf.sh  <safetensors-dir>  [out-prefix]
# Example (Windows path from WSL):
#   bash scripts/convert_to_gguf.sh /mnt/c/Users/fysl9/models/ALLaM-7B-Instruct-preview
set -euo pipefail

HF_DIR="${1:?path to the ALLaM safetensors directory}"
OUT="${2:-./allam-7b}"
LLAMA="${LLAMA_CPP:-./llama.cpp}"

echo "Converting $HF_DIR -> ${OUT}-f16.gguf"
python "$LLAMA/convert_hf_to_gguf.py" "$HF_DIR" --outfile "${OUT}-f16.gguf" --outtype f16

echo "Quantizing -> ${OUT}-q4_k_m.gguf (Q4_K_M, ~4.5 GB, fits 8 GB VRAM)"
"$LLAMA/llama-quantize" "${OUT}-f16.gguf" "${OUT}-q4_k_m.gguf" Q4_K_M

echo "Done. Next:"
echo "  cp ${OUT}-q4_k_m.gguf ollama/allam-7b-q4_k_m.gguf"
echo "  ollama create allam-7b -f ollama/Modelfile"
echo "  # then set LLM_MODEL=allam-7b in .env"
