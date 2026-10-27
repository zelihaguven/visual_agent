#!/usr/bin/env bash
# Aşama 3 VM koşusu: korpus → Qwen3-8B indeksi (1M) → küçük kademeler (kopya) → local yol (bge-m3 + BM25).
# Her adım kaldığı yerden sürer: yarıda kalırsa aynı komutu yeniden çalıştırın (bitmiş toplu işler atlanır).
# Kullanım (Pilot klasöründe, tmux içinde):  bash bench/vm/run_asama3.sh
#   WORKERS=16 (paralel bulut isteği) · GPU=1 (local yol 1M'e kadar; yoksa CPU'da 30k kademesine kadar) · YES=1 (5 USD üstü onaylı)
# İzleme:  tail -f data/logs/asama3_vm.log | grep -E "==|toplu iş|bitti|HATA|Error|Traceback"
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=.venv-vm/bin/python
export PILOT_QDRANT_URL=${PILOT_QDRANT_URL:-http://127.0.0.1:6333} PYTHONUTF8=1
LOG=data/logs/asama3_vm.log; mkdir -p data/logs
WORKERS=${WORKERS:-16}; GPU=${GPU:-0}; YESFLAG=$([ "${YES:-0}" = 1 ] && echo --yes)
[ -n "${OPENROUTER_API_KEY:-}" ] || { echo "OPENROUTER_API_KEY yok"; exit 1; }
step() { echo "$(date +%T) == $1" | tee -a "$LOG"; shift; "$@" 2>&1 | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }

step "korpus (1M, parquet)" $PY -m bench.scale_corpus build || exit 1
step "Qwen3-8B indeksi (MRL 256 + tam vektör diskte + BM25)" \
  $PY -m bench.scale_index index --collection scale_qwen3_8b --embed qwen3-8b --workers "$WORKERS" $YESFLAG || exit 1
for k in 10000 30000 100000; do
  step "kademe kopyası ≤$k" $PY -m bench.scale_index copy --source scale_qwen3_8b --target "scale_qwen3_8b_$k" --max-kademe "$k"
done
if [ "$GPU" = 1 ]; then
  step "local yol bge-m3 + BM25 (GPU, 1M)" \
    $PY -m bench.scale_index index --collection scale_bge_m3 --embed bge-m3-local --device cuda --workers 1 --batch 256
  for k in 10000 30000 100000; do
    step "kademe kopyası ≤$k" $PY -m bench.scale_index copy --source scale_bge_m3 --target "scale_bge_m3_$k" --max-kademe "$k"
  done
else
  step "local yol bge-m3 + BM25 (CPU, ≤30k)" \
    $PY -m bench.scale_index index --collection scale_bge_m3_30000 --embed bge-m3-local --device cpu --workers 1 \
    --batch 32 --max-kademe 30000
  step "kademe kopyası ≤10000" $PY -m bench.scale_index copy --source scale_bge_m3_30000 --target scale_bge_m3_10000 --max-kademe 10000
fi
for c in $(curl -s "$PILOT_QDRANT_URL/collections" | jq -r '.result.collections[].name' | grep '^scale_'); do
  step "durum $c" $PY -m bench.scale_index status --collection "$c"
done
step "disk (Qdrant birimi)" sudo du -sh /var/lib/docker/volumes/qdrant_qdrant_storage
step "deneme sorgusu" $PY -m bench.scale_index probe --collection scale_qwen3_8b --query "E050 hatası ne demek?"
echo "$(date +%T) == BİTTİ" | tee -a "$LOG"
