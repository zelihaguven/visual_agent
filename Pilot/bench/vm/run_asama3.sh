#!/usr/bin/env bash
# Aşama 3 VM koşusu, adım adım. Her adım kaldığı yerden sürer (yarıda kalırsa aynı adımı yeniden çalıştırın).
# Kullanım (Pilot klasöründe, tmux içinde, kök kullanıcı):  bash bench/vm/run_asama3.sh <adım> [koşul]
#   korpus      dikkat dağıtıcı korpusu (1M; big_patent D/F + Vikipedi en/tr, bench/scale_sources.json)
#   qwen10k     Qwen3-8B indeksi, yalnız ilk 10k kademesi → gerçek hız ve maliyet (devam kararı için)
#   qwen        Qwen3-8B indeksinin geri kalanı (1M)
#   kademeler   Qwen3-8B kopyaları: gerçek (≤0), 10k, 30k, 100k
#   yerel       local yol: bge-m3 + BM25, 30k (CPU) ve 10k kopyası
#   sentetik    3a: 1M sentetik (bge-m3 vektörü + gürültü) ve 10k, 100k kopyaları
#   sorgular    sorgu vektörleri (Qwen3-8B: bulut, bir kez; bge-m3: yerel)
#   olcum <k>   3a/3b süre (Qdrant sınırlı: k = 8cpu-16g | 4cpu-16g) + 3b doğruluk (yalnız 8cpu-16g'de)
#   yuk <k>     3c yük testi (istemci Qdrant'ın çekirdekleri dışında)
#   sinirsiz    Qdrant sınırını kaldır (indeksleme adımlarından önce)
# Ortam: OPENROUTER_API_KEY (oturumda; dosyaya yazılmaz), WORKERS=16, YES=1 (5 USD üstü onaylı)
# İzleme:  tail -f data/logs/asama3_vm.log | grep -E "==|toplu iş|bitti|kullanıcı|HATA|Error|Traceback"
set -uo pipefail
cd "$(dirname "$0")/../.."
PY=.venv-vm/bin/python
export PILOT_QDRANT_URL=${PILOT_QDRANT_URL:-http://127.0.0.1:6333} PILOT_QDRANT_GRPC=1 PILOT_QDRANT_DOCKER=1 PYTHONUTF8=1 PYTHONUNBUFFERED=1
LOG=data/logs/asama3_vm.log; mkdir -p data/logs
WORKERS=${WORKERS:-16}; YESFLAG=$([ "${YES:-0}" = 1 ] && echo --yes)
NCPU=$(nproc)
step() { echo "$(date +%T) == $1" | tee -a "$LOG"; shift; "$@" 2>&1 | tee -a "$LOG"; return "${PIPESTATUS[0]}"; }
need_key() { [ -n "${OPENROUTER_API_KEY:-}" ] || { echo "OPENROUTER_API_KEY yok"; exit 1; }; }
QWEN="--collection scale_qwen3_8b --embed qwen3-8b --workers $WORKERS"

case "${1:-}" in
  sinirsiz) step "Qdrant sınırsız" $PY -m bench.scale_bench limits --none ;;
  korpus)   step "korpus (1M, parquet)" $PY -m bench.scale_corpus build ;;
  qwen10k)  need_key; step "Qwen3-8B ≤10k" $PY -m bench.scale_index index $QWEN --max-kademe 10000 $YESFLAG ;;
  qwen)     need_key; step "Qwen3-8B 1M" $PY -m bench.scale_index index $QWEN $YESFLAG ;;
  kademeler)
    for k in 0 10000 30000 100000; do
      n=$([ "$k" = 0 ] && echo gercek || echo "$k")
      step "kopya ≤$k" $PY -m bench.scale_index copy --source scale_qwen3_8b --target "scale_qwen3_8b_$n" --max-kademe "$k"
    done ;;
  yerel)
    step "bge-m3 + BM25 ≤30k (CPU)" $PY -m bench.scale_index index --collection scale_bge_m3_30000 --embed bge-m3-local \
      --device cpu --workers 1 --batch 32 --max-kademe 30000 --reuse-real data/scale/real_bge_m3.npz
    for k in 0 10000; do
      n=$([ "$k" = 0 ] && echo gercek || echo "$k")
      step "kopya ≤$k" $PY -m bench.scale_index copy --source scale_bge_m3_30000 --target "scale_bge_m3_$n" --max-kademe "$k"
    done ;;
  sentetik)
    [ -f data/scale/real_bge_m3.npz ] || { echo "data/scale/real_bge_m3.npz yok (yerelde: python -m bench.scale_synth export, scp)"; exit 1; }
    step "sentetik 1M" $PY -m bench.scale_synth build --n 1000000 --collection synth_1m --workers 4
    step "kopya ≤10k" $PY -m bench.scale_index copy --source synth_1m --target synth_10k --max-kademe 10000
    step "kopya ≤100k" $PY -m bench.scale_index copy --source synth_1m --target synth_100k --max-kademe 100000 ;;
  sorgular)
    need_key
    step "sorgular Qwen3-8B" $PY -m bench.scale_bench queries --collection scale_qwen3_8b
    step "sorgular bge-m3" $PY -m bench.scale_bench queries --collection synth_1m ;;
  olcum)
    k=${2:?koşul: 8cpu-16g | 4cpu-16g}; c=${k%%cpu*}; m=${k#*cpu-}
    step "Qdrant sınırı $k" $PY -m bench.scale_bench limits --cpus "$c" --memory "$m"
    for col in synth_10k synth_100k synth_1m scale_qwen3_8b_gercek scale_qwen3_8b_10000 scale_qwen3_8b_100000 \
               scale_qwen3_8b scale_bge_m3_gercek scale_bge_m3_10000 scale_bge_m3_30000; do
      step "süre $col $k" $PY -m bench.scale_bench latency --collection "$col" --label "$k"
    done
    if [ "$k" = 8cpu-16g ]; then
      need_key
      for col in scale_qwen3_8b_gercek scale_qwen3_8b_10000 scale_qwen3_8b_30000 scale_qwen3_8b_100000 scale_qwen3_8b \
                 scale_bge_m3_gercek scale_bge_m3_10000 scale_bge_m3_30000; do
        step "doğruluk $col" $PY -m bench.measure --scale-collection "$col" --name "asama3b_${col}" --no-rerank           --unfiltered --repeats 3 --recall-queries 300
      done
    fi ;;
  yuk)
    k=${2:?koşul: 8cpu-16g | 4cpu-16g}; c=${k%%cpu*}; m=${k#*cpu-}; CL="$c-$((NCPU - 1))"
    step "Qdrant sınırı $k" $PY -m bench.scale_bench limits --cpus "$c" --memory "$m"
    L="--client-cpus $CL --label $k --duration 60"
    step "yük qwen qdrant think0" $PY -m bench.load_test --collection scale_qwen3_8b --mode qdrant --think 0 $L
    step "yük sentetik qdrant think0" $PY -m bench.load_test --collection synth_1m --mode qdrant --think 0 $L
    if [ "$k" = 8cpu-16g ]; then
      need_key
      step "yük qwen qdrant think5" $PY -m bench.load_test --collection scale_qwen3_8b --mode qdrant --think 5 $L
      step "yük qwen embed think0" $PY -m bench.load_test --collection scale_qwen3_8b --mode embed --think 0 --users 1,5,10,25 $L
      step "yük qwen e2e think5" $PY -m bench.load_test --collection scale_qwen3_8b --mode e2e --think 5 $L
    fi ;;
  *) sed -n 2,16p "$0"; exit 1 ;;
esac
