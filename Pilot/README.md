# Visual Agent: Pilot (kod)

Araştırma aşamasının **tamamen lokal** pilotu:

```
yazılı / sesli soru → netleştirme → hibrit arama + reranker → kaynaklı cevap → otomatik doğrulama → vurgulu kaynak sayfa → sesli okuma
```

- **Ne yapıldı, ne ölçüldü:** [../PILOT-RAPORU.md](../PILOT-RAPORU.md)
- **Kod nasıl çalışıyor, her aşamada ne kullanılıyor, neden:** [../MIMARI.md](../MIMARI.md)

## Gereksinimler

| | |
|---|---|
| Makine | 16 GB+ RAM. GPU şart değil: Apple M4 Pro (24 GB) ve GPU'suz Windows dizüstünde (i5, 32 GB) denendi |
| Yazılım | Python 3.12, [Ollama](https://ollama.com/download). macOS'ta [uv](https://docs.astral.sh/uv/) |
| Disk | ~12 GB: model 4,7 + embedding/reranker 4,6 + ortam 1,5. İsteğe bağlı ses +4 GB, sesli soru +0,5 GB |
| Ağ | Yalnız kurulumda (model indirme). Çalışırken veri dışarı gitmez. Modeller önbellekteyse sistem kendiliğinden çevrimdışı çalışır |

## Kurulum ve çalıştırma

**macOS / Linux:**

```bash
cd pilot
./setup.sh                                  # ortam + model + indeks (~15-25 dk)
.venv/bin/streamlit run app.py              # arayüz
.venv/bin/python -m pytest                  # 271 birim test
.venv/bin/python run_eval.py                # 18 soruluk ölçüm → eval/sonuc.md
```

**Windows** (GPU'suz dizüstünde denendi; `setup.sh` yerine elle kurulum):

```powershell
cd pilot
python -m venv ..\.venv; ..\.venv\Scripts\pip install -r requirements-pilot.txt
winget install Ollama.Ollama; ollama pull qwen2.5:7b
..\.venv\Scripts\python run_index.py                    # CPU'da ~1 saat
..\.venv\Scripts\streamlit run app.py        # ya da çift tıkla: baslat.bat
..\.venv\Scripts\python -m pytest -q
```

Kod dosyaları açıkça UTF-8 ile okuyup yazıyor. Pilotta bütün çalıştırmalar `$env:PYTHONUTF8="1"` ile yapıldı; aynısı önerilir.

**Sesli okuma (isteğe bağlı):** Ayrı ortam gerekir, çünkü Chatterbox kendi torch sürümünü sabitliyor.

```bash
uv venv --python 3.12 .venv-tts && uv pip install --python .venv-tts/bin/python -r requirements-tts.txt   # macOS / Linux
```
```powershell
python -m venv .venv-tts; .venv-tts\Scripts\pip install -r requirements-tts.txt                            # Windows
```

Arayüz ortamı kendiliğinden bulur. Üretilen sesler `data/audio/` altına kaydedilir ve kenar çubuğunda dinlenebilir.

**Sesli soru (isteğe bağlı):** Ana ortamdaki faster-whisper ile çalışır. Model bir kez indirilir: varsayılan `small` (~0,5 GB); GPU varsa `large-v3-turbo` (~1,6 GB).

```powershell
$env:HF_HUB_OFFLINE="0"; ..\.venv\Scripts\python -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')"
```

Kullanım:
- Arayüzde 🎤 ile kaydı başlatıp durdurun.
- Tanınan metin soru kutusuna yazılır; kontrol edip "Sor"a basın.
- Ses diske yazılmaz.

**Ayarlar (ortam değişkenleri):**
- `PILOT_LLM_MODEL`: başka LLM. 24 GB RAM'de 14B'den büyüğü önerilmez, bkz. [KURULUM-LOGU.md](KURULUM-LOGU.md).
- `PILOT_STT_MODEL`: başka STT modeli.

**Şekil açıklaması (isteğe bağlı, VLM):** Çizimlerin aranabilmesi için her şekle bir kez metin açıklaması yazılır.

```powershell
ollama pull qwen2.5vl:3b                                           # ~3,2 GB
..\.venv\Scripts\python run_figures.py gl-pd-14-04a --limit 5      # deneme; argümansız: tüm dokümanlar
..\.venv\Scripts\python run_reindex_docs.py gl-pd-14-04a           # şekil parçalarını indekse ekle
```

Sonuç `data/figures/<doc_id>.json` (repoda gelir). Kaldığı yerden sürer; aynı görsel bir kez açıklanır. Başka VLM için `PILOT_VLM_MODEL`.

**Hazır veri:** Ayrıştırılmış dokümanlar (`data/parsed/`, `data/chunks.jsonl`) repoda gelir, yalnız indeks üretilir. Sıfırdan ayrıştırmak için `run_parse.py`. Bir dokümanın ayrıştırması değişirse yalnız onu yeniden indekslemek için `run_reindex_docs.py <doc_id>`.

## Kalınan yer (2026-10-16)

JUKI MO-6800S'in şekil açıklamaları (VLM) üretildi (`data/figures/juki-mo6800s.json`), ama **JUKI henüz yeniden indekslenmedi**. Bu yüzden JUKI şekilleri aramada görünmüyor ve `data/chunks.jsonl` JUKI'nin şekil parçalarını içermiyor. Arayüz (Streamlit) kapalıyken, `pilot` klasöründe (~4 dk):

```powershell
$env:PYTHONUTF8="1"; ..\..\visual_agent_repo\.venv\Scripts\python.exe run_reindex_docs.py juki-mo6800s
```

Ortam şimdilik eski kopyadan (`Desktop\visual_agent_repo\.venv`) kullanılıyor; kendi `..\.venv` kurulunca komutta `..\.venv\Scripts\python.exe` yazılır. İndeksleme bitince `chunks.jsonl` değişir, commit'lenmeli.

Ayrıca bekleyenler: birleşik hücre düzeltmesi için diğer dokümanların yeniden ayrıştırılıp indekslenmesi (birkaç saat, gece), JUKI şekil soruları, yeni soru setlerinin otomatik ölçümü. Ayrıntı: [../PILOT-RAPORU.md §7](../PILOT-RAPORU.md).

## Yapı

```
pilot/
├── pilot/                kütüphane (her dosyanın görevi: ../MIMARI.md §A8)
│   ├── registry.py       doküman kaydı
│   ├── parse.py          Docling + PyMuPDF yedekleri
│   ├── figures.py        şekil açıklaması (VLM)
│   ├── tables.py         tablo satırı biçimi, tablo varyant kontrolü (K9)
│   ├── chunk.py          parçalama
│   ├── embed.py          bge-m3, reranker
│   ├── index.py          Qdrant
│   ├── retrieve.py       hibrit arama
│   ├── query.py          karar kuralları: varlıklar, uyum, netleştirme, söylenmiş kodlar, dil
│   ├── terms.py          atölye terim sözlüğü (taslak)
│   ├── pipeline.py       soru_cevapla(): uçtan uca
│   ├── prompts.py, llm.py   talimat, şema, Ollama
│   ├── verify.py         doğrulama
│   ├── speech.py         sesli metin kuralları
│   ├── stt.py            sesli soru
│   └── render.py         vurgulu sayfa görseli
├── app.py                Streamlit arayüzü
├── run_parse.py, run_figures.py, run_index.py, run_reindex_docs.py, run_eval.py
├── eval/                 test soruları (18 + 5 sesli), ölçüm sonuçları
├── tests/                271 birim test
├── tools/                seslendirme, ölçüm ve duman testi betikleri
├── data/                 parsed/, figures/, chunks.jsonl (repoda) · qdrant/, audio/ (yerel, repoda değil)
└── KURULUM-LOGU.md       Mac kurulumunun boyut/süre/sorun kaydı
```

Test dokümanları: [../test-dokumanlari/](../test-dokumanlari/). Kaynakları ve lisans notu: [manual-envanteri.md](../calisma-notlari/notlar/manual-envanteri.md).
