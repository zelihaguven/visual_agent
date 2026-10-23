# Qdrant sunucu modu

Pilot varsayılan olarak Qdrant'ı **gömülü** modda kullanır (`data/qdrant/`, tek süreç, kaba kuvvetle arama). Gömülü mod 1M parçayı taşımaz: HNSW, quantization ve payload indeksi yok, koleksiyonun tamamı RAM'de. Hedef ortamda (tablet + arka uç sunucu, çok kullanıcı) Qdrant ayrı bir **sunucu** olarak çalışır. Ölçümler: [../../BENCHMARK-RAPORU.md](../../BENCHMARK-RAPORU.md).

## Windows (geliştirme makinesi, Docker'sız)

```powershell
cd Pilot
# 1) İkili (bir kez, ~85 MB, git dışı)
New-Item -ItemType Directory -Force tools\qdrant\v1.19.2 | Out-Null
Invoke-WebRequest https://github.com/qdrant/qdrant/releases/download/v1.19.2/qdrant-x86_64-pc-windows-msvc.zip -OutFile tools\qdrant\q.zip
Expand-Archive tools\qdrant\q.zip tools\qdrant\v1.19.2; Remove-Item tools\qdrant\q.zip
# 2) Sunucu (ayrı pencerede açık kalır)
powershell -ExecutionPolicy Bypass -File qdrant\start_windows.ps1
# 3) Pilot sunucuya bağlanır
$env:PILOT_QDRANT_URL = "http://127.0.0.1:6333"
```

Sunucu yalnız `127.0.0.1`'i dinler, telemetri kapalıdır. Depo `data/qdrant_server/` (git dışı).

## Linux sunucu (hedef)

```bash
cd Pilot/qdrant && docker compose up -d
```

Aynı sürüm ve ayarlar (`docker-compose.yml`). Portlar varsayılan olarak yalnız sunucunun kendisine açıktır. Tabletler Qdrant'a doğrudan değil, arka uç uygulamasına bağlanır; Qdrant'ı ağa açmak gerekirse önce `QDRANT__SERVICE__API_KEY` (değer `.env`'den, repoya girmez) ve TLS. Pilot tarafında anahtar `PILOT_QDRANT_API_KEY` ortam değişkeninden okunur.

## Koleksiyon kurma

Yeni indeks (embed ile, CPU'da ~1 saat): `PILOT_QDRANT_URL` tanımlıyken `python run_index.py`.

Gömülü indeksteki vektörleri yeniden embed etmeden sunucuya kopyalamak (saniyeler): `python -m bench.server copy` (bkz. betiğin başı).

Koleksiyon ayarları ortam değişkenlerinden okunur (yalnız koleksiyon kurulurken): `PILOT_HNSW_M`, `PILOT_HNSW_EF_CONSTRUCT`, `PILOT_HNSW_FULL_SCAN_THRESHOLD`, `PILOT_QUANTIZATION` (`none` | `int8` | `binary`), `PILOT_QUANT_ALWAYS_RAM`, `PILOT_VECTORS_ON_DISK`, `PILOT_PAYLOAD_ON_DISK`. Sorgu anı: `PILOT_HNSW_EF`, `PILOT_QUANT_RESCORE`, `PILOT_QUANT_OVERSAMPLING`. Sunucu modunda `brand`, `doc_id`, `access` alanlarına keyword payload indeksi kurulur.

## Yetki alanı (`access`)

Her doküman kaydında (`pilot/registry.py`) `access` grupları vardır (varsayılan `("all",)`), indekslemede parçaların payload'ına yazılır. `search(access=[...])` ve `soru_cevapla(access=[...])` verilirse arama yalnız `all` ya da kullanıcının gruplarından birine açık parçalarda yapılır; koşul Qdrant filtresinin içindedir. Kayıtta grup değişirse yeniden embed gerekmez: `index.sync_access(client)`.
