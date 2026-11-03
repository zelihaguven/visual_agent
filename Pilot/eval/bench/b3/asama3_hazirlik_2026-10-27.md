# Aşama 3 hazırlığı: VM seçenekleri, korpus, kalabalık testi, kuru çalıştırma

Durum: **Aşama 3 bölündü (kullanıcı kararları, 2026-10-27).**

- **3b, dizüstünde:** `bench/run_asama3_yerel.ps1`. Süreleri "dizüstü, üretimi temsil etmez" diye işaretli, karar için kullanılmayacak.
- **3a süre ve 3c yük, şirket içi Linux sunucuda:** Hetzner açılmayacak; sunucuyu BT'den istiyoruz.
- **Paket:** `bench/onprem/`, internet gerekmez.
  - İndeksler dizüstünde snapshot olarak hazırlanıyor (sha256 kontrollü).
  - Pakette Python 3.12 (standalone), Qdrant v1.19.2 (statik musl ikili), Linux tekerlekleri ve hazır sorgu vektörleri var.
- **Kaynak sınırı:** Docker gerekmez; sınırı systemd veriyor: `systemd-run -p AllowedCPUs -p CPUQuota -p MemoryMax -p MemorySwapMax=0`, cgroup v2'de sayfa önbelleği dahil. systemd yoksa çekirdek sınırı taskset ile konuyor; bellek sınırı olmuyor ve bu sonuçlara yazılıyor.
- **SSH izni çıkmazsa:** tek komut `sudo bash asama3_sunucu.sh`. Sonuç tek bir `asama3_sonuc_<sunucu>_<tarih>.tar.gz`.
- **Yerelde denenenler:** Windows'ta snapshot alma, sha256 ve dosyadan geri yükleme, Linux tekerleklerinin çözümlenmesi, LF satır sonları.
- **Denenmeyen:** Linux'ta systemd sınırı ve betiğin kendisi; burada Linux, WSL ve Docker yok. Sunucuda önce `sudo bash asama3_sunucu.sh kontrol` çalıştırılmalı.

Hetzner bölümü (§1, `bench/vm/`) VM seçeneği olarak duruyor, kullanılmayacak.

## 0. Onay koşulları ve nasıl uygulanıyor

| Koşul | Uygulama |
|---|---|
| Süre ölçümleri görev dosyasındaki hedef donanımla (4–8 vCPU / 16 GB) | İndeksleme ve kurulum bütün makinede. 3a/3b süre ölçümleri ve 3c, Qdrant konteyneri `--cpuset-cpus 0-7 --cpus 8 --memory 16g --memory-swap 16g` ile sınırlıyken (`bench.scale_bench limits`). cgroup v2'de dosya sayfa önbelleği de bu 16 GB'a sayılıyor. Her koşuldan önce konteyner yeniden başlatılıyor ve önbellek boşaltılıyor. Aynı ölçümler 4 vCPU / 16 GB ile de yapılıyor. Raporda iki koşul ayrı gösterilecek; sınırsız 64 GB sonuçları üretim süresi diye sunulmayacak |
| 3c yük testi | Bu VM'de yapılabiliyor: Qdrant 0–7 (ya da 0–3) numaralı çekirdeklerde, yük üreten istemci kalan çekirdeklerde (`os.sched_setaffinity`), Qdrant'ın cgroup'u dışında, 8 süreç (`bench.load_test`) |
| Dikkat dağıtıcı korpus başlamadan bildirilecek | §2 (tek satırı başlamadan önce yazılacak) |
| İlk 10k kademesinden sonra hız ve maliyet | `run_asama3.sh qwen10k` ayrı adım. 1M tahmini 3 saati ya da 3 $ OpenRouter'ı aşarsa durulup sorulacak |
| Kapanış | Sonuçlar ve gerekli dosyalar (`eval/bench/asama3*`, `data/scale/progress/*.stats.json`, günlük) `scp` ile indirilecek. Sunucuyu kullanıcı Console'dan silecek (API belirteci yok); SSH bağlantısının artık kurulamadığı doğrulanacak. Gerçek toplam: açık kalınan saat × 0,4431 € ve OpenRouter kullanımı (betik istatistiklerindeki `usage.cost` toplamı). `bench/vm/hetzner.py` yalnız belirteç olursa kullanılır |
| Anahtar | Mevcut OpenRouter anahtarı, yalnız SSH oturumunun ortamında; diske ve günlüğe yazılmaz. Harcama sınırı betikte (`--max-usd 3`) |
 Betikler hazır ve yerelde 300 parçayla kuru çalıştırıldı (aşağıda). Yerelde 10k–30k kademesi koşulmadı; uçtan uca test sürerken CPU'yu yormamak için.

## 1. VM seçenekleri

VM'de yapılacak iş:
- Korpusu kurmak.
- Qwen3-8B ile 1M parçayı bulutta embed edip indekslemek (MRL 256 + diskte tam vektör + BM25).
- Küçük kademeleri kopyalamak.
- Local yolu (bge-m3 + BM25) indekslemek.
- 3a sentetik ölçeklenme testi, 3b doğruluk ölçümü ve kalabalık testi.

Embedding bulutta olduğu için GPU yalnız local yolu 30k'nın üstüne taşımak için gerekir. Görev dosyası local yol için 20–30k sınırı koyuyor.

| | A. Hetzner CCX43 (önerilen) | B. AWS m7i.4xlarge | C. AWS g6.4xlarge (GPU) |
|---|---|---|---|
| Donanım | 16 ayrılmış vCPU, 64 GB RAM, 360 GB NVMe | 16 vCPU, 64 GiB RAM, + 150 GB gp3 disk | 16 vCPU, 64 GiB RAM, 1× NVIDIA L4 24 GB, + 150 GB gp3 disk |
| Saatlik | ~0,44 € (~0,51 $), KDV ve IPv4 hariç | ~0,81 $ + disk ~0,02 $ | ~1,32 $ + disk ~0,02 $ |
| Local yol (bge-m3) | 30k'ya kadar (CPU, ~1 saat) | 30k'ya kadar (CPU, ~1 saat) | 1M'e kadar (GPU, tahmini 0,5–1 saat) |
| Tahmini süre | 6–8 saat | 6–8 saat | 7–9 saat |
| VM toplamı | ~3–4 $ | ~5–7 $ | ~9–12 $ |
| OpenRouter (Qwen3-8B, 1M parça) | ~1,6–2,1 $ | ~1,6–2,1 $ | ~1,6–2,1 $ |
| **Toplam** | **~5–6 $** | **~7–9 $** | **~11–14 $** |

Fiyatlar üçüncü taraf fiyat listelerinden (Ekim 2026), us-east-1 / Almanya; açmadan önce sağlayıcının sayfasından doğrulanmalı. Hetzner'in fiyatı Haziran 2026 zammından sonraki değer. Üç seçenek de 5 USD'yi aştığı için kural gereği onayınız gerekir.

Süre dökümü (A/B):

| Adım | Süre |
|---|---|
| Kurulum | 0,5 sa |
| Korpus (~2 GB parquet indirme + bölme) | 0,5 sa |
| Qwen3-8B 1M embed + yükleme | 1–3 sa (16 paralel istek; aşağıdaki hız notuna bakın) |
| HNSW kurulumu ve kademe kopyaları | ~0,5 sa |
| bge-m3 30k (CPU) | ~1 sa |
| 3a sentetik, 3b ölçüm, kalabalık testi | ~2 sa |

**Hız notu:** Aşama 4'te tek iş parçacığıyla 19 parça/sn ölçüldü (64'lük istek ~3,2 sn). 16 paralel istek doğrusal ölçeklenirse ~300 parça/sn olur, 1M parça ~1 saat sürer. OpenRouter'ın hız sınırı bilinmiyor. 429 hatalarında betik bekleyip yeniden dener, bu yüzden üst sınır 3 saat varsayıldı. İlk 10k kademesi gerçek hızı gösterecek; sürmesi gerekenden uzun sürerse durdurup size sorarım.

**Kaynak gereksinimi (1M, ölçülmedi, hesap):**

| Koleksiyon | Disk / RAM |
|---|---|
| Qwen3-8B tam vektör | 4096 × 4 B × 1M = 16,4 GB, diskte; 64 GB RAM'de sayfa önbelleğine sığar |
| Qwen3-8B 256'lık kısa vektör | ~1 GB, RAM'de, HNSW ile |
| Qwen3-8B BM25 | ~1 GB |
| Qwen3-8B payload | ~1,5 GB |
| bge-m3 (30k) | ihmal edilebilir |
| bge-m3 (GPU'da 1M) | ~7 GB |
| 3a sentetik (1M × 1024) | ~6 GB |
| Ham parquet | ~2 GB |

Toplam disk ~40 GB, bu yüzden 100 GB+ disk yeterli.

Ağ: embedding yanıtı JSON float olarak geliyor. 4096 boyutlu bir vektör ~45 KB, 1M vektör ~45 GB indirme eder; bulut VM'de sorun değil.

**Öneri:** A. Aynı iş, en ucuz seçenek. AWS hesabınız varsa ve onu kullanmak isterseniz B. C yalnız local yolu da 1M'de görmek isterseniz.

## 2. Korpus: 1M parça nereden geliyor (3b)

Gerçek 4.232 parça her kademede var. Geri kalanı Hugging Face'teki açık veri setlerinden konuya yakın dikkat dağıtıcılar ([scale_sources.json](../../bench/scale_sources.json)):

| Kaynak | Pay | Neden | Lisans |
|---|---|---|---|
| `NortheasternUniversity/big_patent`, CPC D (tekstil, kâğıt; dikiş makineleri D05B) | %40 | Konuya en yakın: makine ve tekstil teknik dili | CC BY 4.0 |
| `big_patent`, CPC F (makine mühendisliği: motor, pompa) | %30 | Teknik cihaz tarifi; başka kaynak eksik kalırsa açığı bu kapatır | CC BY 4.0 |
| `wikimedia/wikipedia` 20231101.en, makine/tekstil/giyim/cihaz kelimeli maddeler | %18 | Genel ansiklopedik teknik metin | CC BY-SA 3.0 + GFDL |
| `wikimedia/wikipedia` 20231101.tr, aynı süzgeç (Türkçe kelimeler) | %12 | Türkçe dikkat dağıtıcı | CC BY-SA 3.0 + GFDL |

Kurallar:
- **Parça boyu:** gerçek parçalara yakın (hedef 450 karakter; gerçeklerin ortancası 409).
- **Belge başına üst sınır:** tek bir patentten en fazla 40 parça alınıyor, uzun belgeler korpusu domine etmesin diye.
- **Kademeler:** 10k, 30k, 100k ve 1M; iç içe. Sabit tohumla karıştırılıyor; her kademede kaynak payları aynı.
- **Marka:** dikkat dağıtıcının markası gerçek marka dağılımından atanıyor. Böylece marka filtreli aramada da kalabalık oluşuyor (1M'de Brother filtresinde ~250k parça). `doc_type` alanı "dikkat".

Bilinen sınırlar:
- Açık lisanslı ve büyük bir "kullanım kılavuzu" veri seti bulamadım; HF aramasında yalnız küçük ya da lisanssız setler çıktı. En yakın kaynak patentler.
- Vikipedi kelime süzgeci gevşek. Kuru çalıştırmada "Linux çekirdeği" maddesi "cihaz" kelimesi yüzünden geçti. Bu, dikkat dağıtıcı olarak zararsız ama "konuya yakın" iddiasını zayıflatıyor; ölçümde kaynak bazında da raporlanacak.

**3a (sentetik vektör)** görev dosyasındaki gibi kurulacak: gerçek bge-m3 vektörüne küçük Gauss gürültüsü eklenip yeniden normalize ediliyor; sparse ağırlıklar rastgele ölçekleniyor ve rastgele token düşürülüyor. Bu 10k/100k/1M koleksiyonu embed maliyeti olmadan kurar. Betiği VM'i açmadan önce yazıp kuru çalıştıracağım (test bitince, CPU boşken).

## 3. Kalabalık testi (eşzamanlı kullanıcı) planı

Ölçülen katman arama katmanı: sorgu embed'i (bulut) + Qdrant hibrit arama (`short_rescore` + BM25). LLM kapsam dışı.

- **Araç:** `bench/load_test.py`, yeni bağımlılık yok. Kapalı döngü sanal kullanıcı modeli: her kullanıcı bir sorgu gönderir, cevabı bekler, sonra bekleme süresinin ardından yeni sorgu gönderir.
- **Kullanıcı kademeleri:** 1, 5, 10, 25, 50, 100. Her kademe 3 dakika.
- **Bekleme süresi:** iki ayar. 0 sn, kapasite sınırını bulmak için. 5 sn, gerçekçi tablet kullanımı için.
- **Sorgular:** onaylı setlerden ve onların yeniden yazımlarından en az 200 farklı sorgu. Önbellek kapalı, aynı sorgu art arda gelmez. Karışım: %50 marka filtreli, %25 erişim filtreli (yapay departman grupları, Aşama 2'deki gibi), %25 filtresiz.
- **Üç ayrı ölçüm:**
  1. Yalnız Qdrant (önceden hesaplanmış sorgu vektörleri): veritabanının kapasitesi.
  2. Yalnız bulut embed: OpenRouter gecikmesi ve hız sınırı (429).
  3. İkisi birlikte: uçtan uca arama.
- **Koleksiyonlar:** 1M ve 100k.
- **Ölçülenler:**
  - p50/p95/p99 toplam süre ve aşama bazında süre.
  - Saniyede sorgu.
  - Hata oranı (429, zaman aşımı).
  - Qdrant CPU/RAM (`docker stats`).
  - Doyma noktası: p95'in 1 saniyenin altında kaldığı en yüksek kullanıcı sayısı.
- **İstemci konumu:** istemci aynı VM'de çalışırsa CPU paylaşır. İstemci `taskset` ile 4 çekirdeğe sınırlanacak; sonuçlara donanım ve ağ etiketi yazılacak.

**3b doğruluk ölçümü:**
- **Ölçüm:** her kademede (gerçek parçalar, 10k, 30k, 100k, 1M) ve her yolda (Qwen3-8B, bge-m3 + BM25) filtreli ve filtresiz hit@1/@5/MRR. Kullanılan araç mevcut `bench.measure`; koleksiyon ortam değişkenleri `bench.scale_index search_env` ile veriliyor.
- **JUKI:** ayarlamada kullanılmıyor; ayrı satırda raporlanıyor.

## 3c. Kalabalık testi kurulumu (VM)

`bench/load_test.py`:
- **Kullanıcı modeli:** kapalı döngü; her kademe 60 sn.
- **Biçimler ve kademeler:**

  | Biçim | Düşünme süresi | Kullanıcı | Koleksiyon |
  |---|---|---|---|
  | `qdrant` | 0 sn | 1, 5, 10, 25, 50, 100 | 1M Qwen ve 1M sentetik (bge-m3) |
  | `qdrant` | 5 sn | 1, 5, 10, 25, 50, 100 | 1M Qwen |
  | `embed` | 0 sn | 1–25 | (bulut) |
  | `e2e` | 5 sn | 1, 5, 10, 25, 50, 100 | 1M Qwen |

- **4 vCPU koşulu:** yalnız `qdrant`, düşünme süresi 0.
- **Ölçülenler:** p50/p95/p99, saniyede sorgu, hata türleri ve doyma noktası.

## 4. Betikler

| Dosya | Ne yapar |
|---|---|
| [bench/vm/setup.sh](../../bench/vm/setup.sh) | Ubuntu 24.04 kurulumu: paketler, kod (GitHub ya da git bundle), `.venv-vm`, Qdrant (docker, yalnız 127.0.0.1), kontrol. `--gpu` ile torch CUDA. Anahtar dosyaya yazılmaz (`read -rs`). |
| [bench/vm/run_asama3.sh](../../bench/vm/run_asama3.sh) | Sırayla: korpus → Qwen3-8B 1M → kademe kopyaları → local yol → durum. Her adım kaldığı yerden sürer; tmux içinde çalışır. |
| [bench/scale_corpus.py](../../bench/scale_corpus.py) | Korpus: parquet (tam) ya da rows API (küçük örnek). İndirmeler önbellekte; deterministik. |
| [bench/scale_index.py](../../bench/scale_index.py) | Paralel embed (iş parçacığı başına istemci), BM25, Qdrant'a yükleme. Toplu iş bazında ilerleme dosyası; Ctrl+C güvenli. Maliyet tahmini 5 USD'yi aşarsa `--yes` ister. Alt komutlar: `copy` (kademe), `status`, `probe`. |
| [bench/vm/requirements-vm.txt](../../bench/vm/requirements-vm.txt), [requirements-vm-local.txt](../../bench/vm/requirements-vm-local.txt) | VM paketleri (sürümler lock dosyasından); local yol için torch CPU + bge-m3 |
| [bench/scale_synth.py](../../bench/scale_synth.py) | 3a: gerçek bge-m3 vektörleri (yerelde dışa aktarılır) + Gauss gürültüsü; BM25 ağırlıkları ölçeklenir, token düşürülür; 1M, gRPC ile yükleme |
| [bench/scale_bench.py](../../bench/scale_bench.py) | Qdrant konteyner sınırı, sorgu vektörleri (bir kez), yalnız Qdrant gecikmesi (filtresiz / marka / yetki / dense), ANN recall, RAM/disk |
| [bench/load_test.py](../../bench/load_test.py) | 3c yük testi |
| [bench/vm/hetzner.py](../../bench/vm/hetzner.py) | Hetzner API: fiyat, aç, durum, sil (doğrulamalı), gerçek maliyet |
| `bench.measure --scale-collection` | 3b doğruluk + uçtan uca arama süresi (bulut embed dahil) |

VM kodu GitHub'dan çeker. Commit'ler push edilmediyse yerelde `git bundle create visual_agent.bundle main` ile bir bundle oluşturulup VM'e kopyalanır, kurulum `BUNDLE=...` ile yapılır.

**Koleksiyon şeması (Qwen3-8B):**
- `dense`: 4096 boyutlu tam vektör, diskte, HNSW'siz (`m=0`). Yalnız kısa vektörün adaylarını yeniden skorluyor; 1M × 4096 için graf kurmak saatler ve GB'lar alır.
- `dense_s256`: kısa vektör, RAM'de, HNSW'li.
- `bm25`: IDF modifier'lı sparse.
- **Payload indeksleri:** brand, doc_id, access, nav, kademe.
- **Yükleme sırasında** HNSW kurulumu kapalı (`indexing_threshold=0`); bütün toplu işler bitince açılıyor.

## 5. Kuru çalıştırma (yerel, 2026-10-27)

Geliştirme dizüstü (GPU'suz Windows), yerel Qdrant sunucusu v1.19.2. Ağ: ofis bağlantısı. **Aynı anda uçtan uca "bulunamadı" testi CPU'da LLM çalıştırıyordu.**

| Adım | Sonuç |
|---|---|
| Korpus (rows API, indirme yok) | 300 parça: 150 gerçek (dokümanlara eşit aralıklı) + 150 dikkat dağıtıcı (patent-d 60, patent-f 45, wiki-en 27, wiki-tr 18). Kademeler 100 / 300. 12 sn |
| İndeks, 2 toplu işte dur | 64 parça yazıldı, ilerleme dosyasında 2 iş |
| Kaldığı yerden | Kalan 8 iş (236 parça) yazıldı, toplam 300 nokta, `tamam=True` |
| Tekrar | "0 kalan", yalnız HNSW açıldı; çift kayıt yok (300 nokta) |
| Kademe kopyası ≤100 | 150 nokta (gerçek parçalar), yeniden embed yok |
| Deneme sorgusu | `short_rescore` + BM25 yolu çalışıyor; ilk 5'te gerçek parçalar ve bir Türkçe Vikipedi dikkat dağıtıcısı |
| Maliyet | 44.178 token, **0,0006 USD** (API'nin `usage.cost` alanından) |
| Hız | 4 paralel istekle 8,9 parça/sn; 32 parçalık istek ~6,6 sn. **Temsil edici değil:** CPU testle meşguldü ve sağlayıcı Aşama 4'tekinden yavaştı (64 parça ~3,2 sn idi). VM'de ilk kademede yeniden ölçülecek |

Parça başına token 147 (API'nin saydığı). 1M parça için ~147M token × 0,011–0,014 $/Mtok ≈ **1,6–2,1 USD**.

**Henüz test edilmeyen:**
- Local yol (`--embed bge-m3-local`). Yerelde embed çalıştırmamak için kuru çalıştırmaya alınmadı. VM'de ilk adımda `--max-kademe 10000` ile denenecek.
- Parquet indirme yolu. Kuru çalıştırma rows API'yi kullandı; parquet listesi ve dosya boyutları API'den doğrulandı: patent-d 105 MB, patent-f 836 MB, wiki-tr 527 MB.
