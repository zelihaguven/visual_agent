#!/usr/bin/env bash
# Aşama 3 VM kurulumu (Ubuntu 24.04, Python 3.12). Bulut embed (OpenRouter, ZDR) + Qdrant sunucusu (docker).
# Kullanım (VM'de):
#   bash setup.sh            # CPU VM
#   bash setup.sh --gpu      # GPU'lu VM: local yol (bge-m3) için torch CUDA da kurulur
#   BUNDLE=~/visual_agent.bundle bash setup.sh    # GitHub yerine yerelden kopyalanan git bundle'dan (push edilmemiş commit'ler)
# Anahtar dosyaya yazılmaz: kurulumdan sonra oturumda  read -rs OPENROUTER_API_KEY && export OPENROUTER_API_KEY
set -euo pipefail
GPU=0; [[ "${1:-}" == "--gpu" ]] && GPU=1
REPO=${REPO:-https://github.com/zelihaguven/visual_agent.git}
DIR=${DIR:-$HOME/visual_agent}

echo "== 1/5 Sistem paketleri"
sudo apt-get update -q
sudo apt-get install -y -q git python3-venv python3-pip docker.io docker-compose-v2 tmux curl jq
sudo systemctl enable --now docker

echo "== 2/5 Kod"
if [ ! -d "$DIR" ]; then
  if [ -n "${BUNDLE:-}" ]; then git clone "$BUNDLE" "$DIR"; else git clone --depth 1 "$REPO" "$DIR"; fi
fi
cd "$DIR/Pilot"

echo "== 3/5 Python ortamı (.venv-vm)"
python3 -m venv .venv-vm
.venv-vm/bin/pip install -q -U pip
.venv-vm/bin/pip install -q -r bench/vm/requirements-vm.txt
if [ "$GPU" = 1 ]; then
  nvidia-smi || { echo "GPU sürücüsü yok (nvidia-smi çalışmadı)"; exit 1; }
  .venv-vm/bin/pip install -q torch==2.14.1 --index-url "${TORCH_INDEX:-https://download.pytorch.org/whl/cu128}"
  .venv-vm/bin/pip install -q -r bench/vm/requirements-vm-gpu.txt
  .venv-vm/bin/python -c "import torch; assert torch.cuda.is_available(); print('CUDA:', torch.cuda.get_device_name(0))"
fi

echo "== 4/5 Qdrant sunucusu (qdrant/docker-compose.yml, yalnız 127.0.0.1)"
sudo docker compose -f qdrant/docker-compose.yml up -d
for _ in $(seq 60); do curl -sf http://127.0.0.1:6333/readyz >/dev/null && break; sleep 2; done
curl -sf http://127.0.0.1:6333/readyz >/dev/null || { echo "Qdrant açılmadı: sudo docker logs visual-agent-qdrant"; exit 1; }
curl -s http://127.0.0.1:6333 | jq -c .

echo "== 5/5 Kontrol"
.venv-vm/bin/python -c "import bench.scale_corpus, bench.scale_index; print('betikler yüklendi')"
nproc; free -g | head -2; df -h . | tail -1
[ -n "${OPENROUTER_API_KEY:-}" ] || echo "UYARI: OPENROUTER_API_KEY yok. Oturumda: read -rs OPENROUTER_API_KEY && export OPENROUTER_API_KEY"
echo "Hazır. Koşu: tmux new -s asama3 'bash bench/vm/run_asama3.sh'   (GPU: GPU=1 bash bench/vm/run_asama3.sh)"
