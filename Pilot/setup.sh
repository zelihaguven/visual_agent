#!/usr/bin/env bash
# Pilot kurulumu (macOS / Linux). Gereksinimler: Python 3.12, uv (https://docs.astral.sh/uv/), Ollama.
set -euo pipefail
cd "$(dirname "$0")"

command -v uv >/dev/null || { echo "uv kurulu değil: https://docs.astral.sh/uv/getting-started/installation/"; exit 1; }
command -v ollama >/dev/null || { echo "Ollama kurulu değil: https://ollama.com/download"; exit 1; }

echo "== 1/4 Ana ortam (.venv)"
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r requirements-pilot.txt

echo "== 2/4 Model: ${PILOT_LLM_MODEL:-qwen2.5:7b} (~4,7 GB)"
ollama pull "${PILOT_LLM_MODEL:-qwen2.5:7b}"

echo "== 3/4 Embedding ve reranker (~4,6 GB, ilk çalıştırmada kendiliğinden iner)"
echo "== 4/4 İndeks (data/qdrant) ~10 dk, CPU"
.venv/bin/python run_index.py

echo
echo "Hazır. Arayüz:   .venv/bin/streamlit run app.py"
echo "Ölçüm:           .venv/bin/python run_eval.py"
echo "Sesli okuma (isteğe bağlı, ~4 GB): uv venv --python 3.12 .venv-tts && uv pip install --python .venv-tts/bin/python -r requirements-tts.txt"
