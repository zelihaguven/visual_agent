#!/usr/bin/env bash
# Aşama 3a (süre) ve 3c (yük) — şirket içi Linux sunucu. İnternet gerekmez: Python, Qdrant ve indeksler pakette.
#
# TEK KOMUT (paket klasöründe):   sudo bash asama3_sunucu.sh
#   Biter bitmez bu klasörde asama3_sonuc_<sunucu>_<tarih>.tar.gz oluşur; o dosyayı geri getirin.
#   Ardından temizlik:            sudo bash asama3_sunucu.sh temizle
#
# Adımlar tek tek de çalışır:  kontrol | kur | yukle | olcum | topla | temizle   (hepsi = varsayılan)
#   kontrol  donanım, disk, systemd/cgroup v2, kök yetkisi → kontrol.txt (yetmiyorsa durur ve nedenini yazar)
#   kur      paketteki Python 3.12 ve Qdrant v1.19.2 açılır, Python paketleri internetsiz kurulur
#   yukle    Qdrant sınırsız açılır, snapshot'lar geri yüklenir (sha256 kontrollü), küçük kademeler kopyalanır
#   olcum    Qdrant systemd ile sınırlanır (8 vCPU / 16 GB, sonra 4 vCPU / 16 GB; sayfa önbelleği dahil) → 3a süre,
#            3c yük (istemci Qdrant'ın çekirdekleri dışında)
#   topla    sonuçlar + sistem bilgisi + günlük → tar.gz
#   temizle  Qdrant'ı durdurur, açılmış indeksleri ve çalışma klasörünü siler (paket ve sonuç dosyası kalır)
#
# Gereken: Linux x86_64, bash, tar, en az 10 çekirdek ve 24 GB RAM (daha azında koşul uyarlanır, raporda yazar),
# boş disk ≈ 2,5 × snapshot boyutu, 6333/6334 portları boş, taskset (util-linux). Sınır için systemd + cgroup v2 ve kök yetkisi; yoksa kullanıcı birimi ya da
# taskset ile sürer ve sonuçlara "bellek sınırı yok" etiketi düşülür. Docker gerekmez. Ağ: yalnız 127.0.0.1.
# Süre kabaca: yükleme 20–40 dk, ölçüm iki koşul için ~2 saat. Ekran kapansa da sürsün: tmux/screen ya da nohup.
set -uo pipefail
PAKET=$(cd "$(dirname "$0")" && pwd)
W=$PAKET/calisma
PY=$W/python/bin/python3
QBIN=$W/qdrant/qdrant
QDATA=$W/qdrant_data
KOD=$PAKET/kod/Pilot
LOG=$W/asama3_sunucu.log
UNIT=asama3-qdrant
PORT=6333                                  # gRPC 6334 (qdrant-client'in varsayılanı); ikisi de boş olmalı
mkdir -p "$W"
log() { echo "$(date +%T) $*" | tee -a "$LOG"; }
die() { log "HATA: $*"; exit 1; }
cd "$KOD" || die "kod klasörü yok: $KOD"

export PYTHONUTF8=1 PYTHONUNBUFFERED=1 PILOT_QDRANT_URL=http://127.0.0.1:$PORT PILOT_QDRANT_GRPC=1
export PILOT_QDRANT_STORAGE=$QDATA/storage BENCH_GIT_COMMIT=$(cat "$PAKET/COMMIT" 2>/dev/null || echo "?")
export BENCH_NETWORK="yalnız yerel (127.0.0.1), sunucuda internet yok"

ncpu=$(nproc); ram_gb=$(awk '/MemTotal/ {printf "%d", $2/1048576}' /proc/meminfo)
is_root() { [ "$(id -u)" = 0 ]; }
runner() {
  if [ -d /run/systemd/system ] && [ "$(stat -fc %T /sys/fs/cgroup 2>/dev/null)" = cgroup2fs ]; then
    if is_root; then echo systemd; return; fi
    systemd-run --user --scope -q true 2>/dev/null && { echo systemd-user; return; }
  fi
  echo yok
}
RUNNER=$(runner)
SCTL=(systemctl); [ "$RUNNER" = systemd-user ] && SCTL=(systemctl --user)

kontrol() {
  local need_gb snap_gb free_gb
  snap_gb=$(du -s --block-size=1G "$PAKET/snapshots" 2>/dev/null | cut -f1); snap_gb=${snap_gb:-0}
  need_gb=$(( snap_gb * 5 / 2 + 5 ))
  free_gb=$(df --output=avail -BG "$PAKET" | tail -1 | tr -dc 0-9)
  {
    echo "sunucu: $(hostname -s) · $(uname -srm)"
    grep -m1 "model name" /proc/cpuinfo | sed 's/.*: /cpu: /'
    echo "çekirdek: $ncpu · RAM: ${ram_gb} GB · boş disk: ${free_gb} GB (gereken ~${need_gb} GB, snapshot ${snap_gb} GB)"
    echo "kök: $(is_root && echo evet || echo hayır) · sınırlayıcı: $RUNNER · cgroup: $(stat -fc %T /sys/fs/cgroup 2>/dev/null)"
    . /etc/os-release 2>/dev/null && echo "işletim sistemi: $PRETTY_NAME"
    ldd --version 2>/dev/null | head -1
  } | tee "$W/kontrol.txt" | tee -a "$LOG"
  [ "$(uname -m)" = x86_64 ] || die "yalnız x86_64 destekleniyor"
  [ "$free_gb" -ge "$need_gb" ] || die "disk yetmiyor: ${free_gb} GB boş, ~${need_gb} GB gerekli"
  [ "$ncpu" -ge 6 ] || die "en az 6 çekirdek gerekli (Qdrant 4 + istemci 2)"
  command -v taskset >/dev/null || die "taskset yok (util-linux paketi)"
  if ! { [ -f "$W/qdrant.pid" ] || "${SCTL[@]}" is-active -q "$UNIT" 2>/dev/null; }; then
    for p in "$PORT" $((PORT + 1)); do
      (exec 3<>/dev/tcp/127.0.0.1/$p) 2>/dev/null && die "port $p kullanımda (başka bir Qdrant?); önce onu durdurun"
    done
  fi
  [ "$RUNNER" = yok ] && log "UYARI: systemd/cgroup v2 ile sınır konamıyor; taskset ile çekirdek sınırı, bellek sınırı yok (sonuçlarda yazar)"
  return 0
}

kur() {
  [ -x "$PY" ] || { mkdir -p "$W" && tar -xzf "$PAKET"/python/cpython-*.tar.gz -C "$W" || die "Python açılamadı"; }
  "$PY" -m pip install -q --no-index --find-links "$PAKET/wheels" -r "$PAKET/wheels/pins.txt" || die "paket kurulumu"
  [ -x "$QBIN" ] || { mkdir -p "$W/qdrant" && tar -xzf "$PAKET"/bin/qdrant-*.tar.gz -C "$W/qdrant" || die "Qdrant açılamadı"; }
  "$QBIN" --version | tee -a "$LOG"
  "$PY" -c "import qdrant_client, numpy, bench.scale_bench, bench.load_test; print('python hazır')" | tee -a "$LOG" || die "içe aktarma"
}

qdrant_stop() {
  case $RUNNER in
    systemd|systemd-user) "${SCTL[@]}" stop "$UNIT" 2>/dev/null; "${SCTL[@]}" reset-failed "$UNIT" 2>/dev/null ;;
    *) [ -f "$W/qdrant.pid" ] && kill "$(cat "$W/qdrant.pid")" 2>/dev/null; rm -f "$W/qdrant.pid" ;;
  esac
  sleep 3
}

# qdrant_start [çekirdek] [bellek, ör. 16G] — boşsa sınırsız
qdrant_start() {
  local cpus=${1:-} mem=${2:-} props=() pin=()
  qdrant_stop
  if is_root; then sync; echo 3 > /proc/sys/vm/drop_caches; fi        # soğuk başlangıç
  mkdir -p "$QDATA/storage" "$QDATA/snapshots"
  local envs=(QDRANT__STORAGE__STORAGE_PATH="$QDATA/storage" QDRANT__STORAGE__SNAPSHOTS_PATH="$QDATA/snapshots"
              QDRANT__SERVICE__HOST=127.0.0.1 QDRANT__SERVICE__HTTP_PORT="$PORT" QDRANT__SERVICE__GRPC_PORT=$((PORT + 1))
              QDRANT__TELEMETRY_DISABLED=true QDRANT__LOG_LEVEL=WARN)
  [ -n "$cpus" ] && pin=("$(command -v taskset)" -c "0-$((cpus - 1))")
  case $RUNNER in
    systemd|systemd-user)
      if [ -n "$cpus" ]; then
        props=(-p "CPUQuota=$((cpus * 100))%" -p "MemoryMax=$mem" -p MemorySwapMax=0)
        [ "$RUNNER" = systemd ] && props+=(-p "AllowedCPUs=0-$((cpus - 1))")
      fi
      local setenv=(); for e in "${envs[@]}"; do setenv+=(--setenv="$e"); done
      systemd-run $([ "$RUNNER" = systemd-user ] && echo --user) -q --unit="$UNIT" --collect \
        --working-directory="$QDATA" ${props[@]+"${props[@]}"} "${setenv[@]}" ${pin[@]+"${pin[@]}"} "$QBIN" || die "systemd-run"
      export PILOT_QDRANT_UNIT=$UNIT PILOT_QDRANT_UNIT_USER=$([ "$RUNNER" = systemd-user ] && echo 1 || echo 0) ;;
    *)
      (cd "$QDATA" && env "${envs[@]}" nohup ${pin[@]+"${pin[@]}"} "$QBIN" >> "$W/qdrant.out" 2>&1 & echo $! > "$W/qdrant.pid")
      unset PILOT_QDRANT_UNIT ;;
  esac
  "$PY" -m bench.scale_bench wait --url "http://127.0.0.1:$PORT" --timeout 900 || die "Qdrant açılmadı (günlük: journalctl -u $UNIT)"
  log "Qdrant açık · sınır: ${cpus:-yok} çekirdek, ${mem:-yok} bellek · $RUNNER"
}

exists() { "$PY" -c "from bench.server import server_client as s; import sys; sys.exit(0 if s().collection_exists('$1') else 1)"; }
max_kademe() { "$PY" -c "
from bench.server import server_client as s; from qdrant_client import models as m
c = s(); n = c.count('$1', count_filter=m.Filter(must=[m.FieldCondition(key='kademe', range=m.Range(gt=$2))])).count
print(n)"; }

yukle() {
  qdrant_start
  "$PY" -m bench.onprem.snapshot restore --dir "$PAKET/snapshots" --snapshots-path "$QDATA/snapshots" \
    --progress-dir "$KOD/data/scale/progress" 2>&1 | tee -a "$LOG"
  [ "${PIPESTATUS[0]}" = 0 ] || die "snapshot geri yükleme"
  cp -n "$PAKET"/queries/*.json "$KOD/data/scale/" 2>/dev/null
  copy() { exists "$2" || "$PY" -m bench.scale_index copy --source "$1" --target "$2" --max-kademe "$3" 2>&1 | tee -a "$LOG"; }
  if exists synth_1m; then copy synth_1m synth_10k 10000; copy synth_1m synth_100k 100000; fi
  if exists scale_qwen3_8b; then
    copy scale_qwen3_8b scale_qwen3_8b_gercek 0
    for k in 10000 30000 100000; do copy scale_qwen3_8b "scale_qwen3_8b_$k" "$k"; done
  fi
  if exists scale_bge_m3; then
    copy scale_bge_m3 scale_bge_m3_gercek 0
    [ "$(max_kademe scale_bge_m3 10000)" -gt 0 ] && copy scale_bge_m3 scale_bge_m3_10000 10000
  fi
  log "yükleme bitti"
}

olcum_kosul() {   # $1 çekirdek, $2 bellek (ör. 16G)
  local c=$1 m=$2 label client
  label="${c}cpu-$(echo "$m" | tr 'G' 'g')"
  [ "$RUNNER" = yok ] && label="${label}-bellek-sinirsiz"
  client="$c-$((ncpu - 1))"
  export BENCH_HW_LABEL="şirket içi sunucu $(hostname -s), Qdrant ${c} vCPU / ${m} sınırlı ($RUNNER; sayfa önbelleği dahil), istemci çekirdek $client"
  qdrant_start "$c" "$m"
  for col in synth_10k synth_100k synth_1m scale_qwen3_8b_gercek scale_qwen3_8b_10000 scale_qwen3_8b_100000 \
             scale_qwen3_8b scale_bge_m3_gercek scale_bge_m3_10000 scale_bge_m3; do
    exists "$col" || continue
    log "== süre $col $label"
    taskset -c "$client" "$PY" -m bench.scale_bench latency --collection "$col" --label "$label" 2>&1 | tee -a "$LOG"
  done
  local procs=$(( ncpu - c )); [ "$procs" -gt 8 ] && procs=8
  local L=(--client-cpus "$client" --procs "$procs" --label "$label" --duration 60)
  for col in scale_qwen3_8b synth_1m; do
    exists "$col" || continue
    log "== yük $col qdrant think0 $label"
    "$PY" -m bench.load_test --collection "$col" --mode qdrant --think 0 "${L[@]}" 2>&1 | tee -a "$LOG"
  done
  if [ "$c" = 8 ] && exists scale_qwen3_8b; then
    log "== yük scale_qwen3_8b qdrant think5 $label"
    "$PY" -m bench.load_test --collection scale_qwen3_8b --mode qdrant --think 5 "${L[@]}" 2>&1 | tee -a "$LOG"
  fi
}

olcum() {
  local m=16G
  [ "$ram_gb" -lt 20 ] && { m="$((ram_gb - 4))G"; log "UYARI: RAM ${ram_gb} GB; bellek sınırı $m (16 GB yerine)"; }
  if [ "$ncpu" -ge 10 ]; then olcum_kosul 8 "$m"; else log "UYARI: $ncpu çekirdek; 8 vCPU koşulu atlandı (istemciye çekirdek kalmıyor)"; fi
  olcum_kosul 4 "$m"
  qdrant_stop
  log "ölçüm bitti"
}

topla() {
  local out="$PAKET/asama3_sonuc_$(hostname -s)_$(date +%Y%m%d_%H%M).tar.gz"
  {
    echo "== uname"; uname -a; echo "== os"; cat /etc/os-release 2>/dev/null
    echo "== lscpu"; lscpu 2>/dev/null; echo "== bellek"; free -g; echo "== disk"; df -h "$PAKET"
    echo "== systemd"; systemctl --version 2>/dev/null | head -1; echo "== commit"; cat "$PAKET/COMMIT" 2>/dev/null
  } > "$W/sistem.txt" 2>&1
  tar -czf "$out" -C "$KOD" $(cd "$KOD" && ls eval/bench/b3/asama3_sure_* eval/bench/b3/asama3_yuk_* 2>/dev/null) \
      -C "$W" kontrol.txt sistem.txt asama3_sunucu.log || die "tar"
  log "SONUÇ: $out ($(du -h "$out" | cut -f1)) — bu dosyayı geri getirin"
}

temizle() {
  qdrant_stop
  rm -rf "$QDATA" "$W/python" "$W/qdrant"
  log "temizlendi: Qdrant durduruldu, indeksler ve çalışma dosyaları silindi (paket ve sonuç tar.gz duruyor)"
}

case "${1:-hepsi}" in
  kontrol) kontrol ;;
  kur) kur ;;
  yukle) yukle ;;
  olcum) olcum ;;
  topla) topla ;;
  temizle) temizle ;;
  hepsi) kontrol && kur && yukle && olcum && topla
         log "BİTTİ. Sonucu getirin; temizlik için: sudo bash $0 temizle" ;;
  *) sed -n 2,22p "$0"; exit 1 ;;
esac
