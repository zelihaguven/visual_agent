"""Yollar ve sabitler. Tek yerden değişir."""
import os
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parent.parent
MANUALS_DIR = PILOT_DIR.parent / "test-dokumanlari"
DATA_DIR = PILOT_DIR / "data"
PARSED_DIR = DATA_DIR / "parsed"
CHUNKS_PATH = DATA_DIR / "chunks.jsonl"
QDRANT_DIR = DATA_DIR / "qdrant"

PAGES_PER_BATCH = 10          # Docling'e verilen sayfa aralığı uzunluğu
CHUNK_MAX_CHARS = 900         # metin parçası üst sınırı (başlık sınırını aşmaz)
# Parça dili otomatik tespit edilir (chunk.py, lingua); aday diller kuruluma göre, dokümana göre değil
LANGS = tuple(os.environ.get("PILOT_LANGS", "en,tr,fr,es,de,it,pt").split(","))
# Dokümana özgü elle yazılmış kurallar (BRAND_ALIASES, "S-7300" aile grubu, ASPECTS/DETAIL_HINT) 2026-11-05'te silindi:
# netleştirme şema C'nin netleştirme moduyla ölçüldü, kurallar kapalıyken taban kadar iyi (Adım 2 planı §11, §20).
EDGE_BAND = 0.12             # üst/alt bilgi tespiti için sayfa kenar oranı
FURNITURE_MIN_RATIO = 0.5     # üst/alt bilgi: sayfaların en az bu oranında tekrar eder
SENTENCE_END = (".", "!", "?", ":", ";", '"', ")")

EMBED_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
EMBED_DEVICE = "cpu"          # MPS'te bge-m3 ve reranker yanlış sonuç veriyor (KURULUM-LOGU.md #1)
EMBED_MAX_LENGTH = 512
EMBED_BATCH = 16
COLLECTION = os.environ.get("PILOT_COLLECTION", "manuals")

# Arama katmanı seçenekleri (BENCHMARK-RAPORU.md). Varsayılanlar pilotun ölçülen yapısıdır; ortam değişkeniyle seçilir.
# none (varsayılan, Aşama 4 kararı): iyi adaylarla local reranker katkısız/zararlıydı; hibrit arama sonucu doğrudan
# kullanılır. local: bge-v2-m3 / jina / onnx (PILOT_RERANK_MODEL, PILOT_RERANK_BACKEND); openrouter: qwen3-reranker-8b
RERANK_PROVIDER = os.environ.get("PILOT_RERANK_PROVIDER", "none")           # none | local | openrouter
# Rerank açıkken (Aşama 4 teşhisi, rerank_duzeltme): reranker'a başlıklı metin gider (embed_text: marka, ürün, bölüm +
# metin; embedding de bununla yapılıyor) ve reranker sırası hibrit sırayla RRF ile birleştirilir (k=60, standart sabit).
# Başlıksız metinde reranker ceket ile pantolonun aynı adlı bölümlerini ayıramıyordu; tek başına sıra hibrit sırayı siliyordu.
RERANK_PASSAGE = os.environ.get("PILOT_RERANK_PASSAGE", "embed_text")       # embed_text | text (eski)
RERANK_FUSION = os.environ.get("PILOT_RERANK_FUSION", "rrf")               # rrf | none (yalnız reranker skoru, eski)
RERANK_FUSION_K = int(os.environ.get("PILOT_RERANK_FUSION_K", "60"))
RERANK_MODEL = os.environ.get("PILOT_RERANK_MODEL", RERANK_MODEL)
# local backend: torch (doğrudan transformers, varsayılan) | flag (FlagEmbedding, eski) | onnx | onnx-int8.
# torch, flag ile aynı skoru verir (fark <1e-5), 3,6 kat hızlı: FlagEmbedding her çağrıda ilk batch'i fazladan hesaplıyor
# ve 20 adayı tek batch'te en uzun parçaya dolduruyor (BENCHMARK-RAPORU Aşama 1)
RERANK_BACKEND = os.environ.get("PILOT_RERANK_BACKEND", "torch")
RERANK_MAX_LENGTH = int(os.environ.get("PILOT_RERANK_MAX_LENGTH", EMBED_MAX_LENGTH))
RERANK_BATCH = int(os.environ.get("PILOT_RERANK_BATCH", "4"))                # torch/onnx batch (4: 15,3 sn, 8: 17,1 sn)
TORCH_THREADS = int(os.environ["PILOT_TORCH_THREADS"]) if os.environ.get("PILOT_TORCH_THREADS") else None
OPENROUTER_URL = os.environ.get("PILOT_OPENROUTER_URL", "https://openrouter.ai/api/v1")
# OpenRouter istekleri her zaman ZDR + data_collection=deny ile gider; kapatılamaz (ürün kararı, cloud.py)
# Qdrant istemcisi süreç boyunca tek örnek (arama başına ~1,1 sn). Gömülü klasör o süreçte kilitli kalır: yeniden
# indeksleme arayüz kapalıyken yapılır. Eski davranış (her aramada aç/kapat): PILOT_QDRANT_REUSE=0
QDRANT_REUSE = os.environ.get("PILOT_QDRANT_REUSE", "1") == "1"

# Embedding sağlayıcısı (BENCHMARK-RAPORU Aşama 4). Varsayılan: local bge-m3 (dense + sparse), bugünkü yapı.
# openrouter: bulut dense (ZDR zorunlu) + BM25 sparse (pilot/sparse.py); koleksiyon o modelle kurulmuş olmalı.
EMBED_PROVIDER = os.environ.get("PILOT_EMBED_PROVIDER", "local")             # local | openrouter
EMBED_CLOUD_MODEL = os.environ.get("PILOT_EMBED_MODEL", "")                  # ör. qwen/qwen3-embedding-8b
EMBED_QUERY_PREFIX = os.environ.get("PILOT_EMBED_QUERY_PREFIX", "")          # modelin sorgu biçimi (bench/models.json)
EMBED_DOC_PREFIX = os.environ.get("PILOT_EMBED_DOC_PREFIX", "")
# Sparse kol: bm25 (varsayılan, Aşama 4: rerank'sız hit@1 0,44 → 0,72) | bge-m3 (bge-m3'ün kendi ağırlıkları, eski yol).
# Local indeksler ikisini birden taşır (INDEX_SPARSE); bulut dense indekslerde yalnız bm25.
SPARSE_KIND = os.environ.get("PILOT_SPARSE", "bm25")
INDEX_SPARSE: tuple[str, ...] = ("bge-m3", "bm25") if EMBED_PROVIDER == "local" else ("bm25",)
# Dense kol: full (tam vektör) | short (yalnız MRL kısa vektör) | short_rescore (kısa vektörle aday, tam vektörle sıra)
DENSE_MODE = os.environ.get("PILOT_DENSE_MODE", "full")
DENSE_SHORT_DIM = int(os.environ.get("PILOT_DENSE_SHORT_DIM", "256"))
SHORT_OVERSAMPLE = float(os.environ.get("PILOT_SHORT_OVERSAMPLE", "4"))

# Qdrant sunucu modu (Pilot/qdrant/README.md). PILOT_QDRANT_URL yoksa gömülü mod (QDRANT_DIR), bugünkü davranış.
QDRANT_URL = os.environ.get("PILOT_QDRANT_URL") or None
QDRANT_GRPC = os.environ.get("PILOT_QDRANT_GRPC", "0") == "1"
QDRANT_API_KEY = os.environ.get("PILOT_QDRANT_API_KEY") or None      # sunucuda anahtar varsa; hiçbir yere yazılmaz


def _int_env(name: str) -> int | None:
    return int(os.environ[name]) if os.environ.get(name) else None


# Koleksiyon ayarları (yalnız koleksiyon kurulurken uygulanır; gömülü mod HNSW/quantization kullanmaz, tam arar).
# Boş bırakılanlar Qdrant varsayılanı: m=16, ef_construct=100, full_scan_threshold=10000 KB.
HNSW_M = _int_env("PILOT_HNSW_M")
HNSW_EF_CONSTRUCT = _int_env("PILOT_HNSW_EF_CONSTRUCT")
HNSW_FULL_SCAN_THRESHOLD = _int_env("PILOT_HNSW_FULL_SCAN_THRESHOLD")
QUANTIZATION = os.environ.get("PILOT_QUANTIZATION", "none")          # none | int8 | binary
QUANT_ALWAYS_RAM = os.environ.get("PILOT_QUANT_ALWAYS_RAM", "1") == "1"
VECTORS_ON_DISK = os.environ.get("PILOT_VECTORS_ON_DISK", "0") == "1"
PAYLOAD_ON_DISK = os.environ.get("PILOT_PAYLOAD_ON_DISK", "0") == "1"
# Sorgu anı (dense kol). Boş: Qdrant varsayılanı (hnsw_ef = ef_construct; quantization varsa rescore açık)
HNSW_EF = _int_env("PILOT_HNSW_EF")
QUANT_RESCORE = os.environ.get("PILOT_QUANT_RESCORE")                  # "1" | "0" | boş
QUANT_OVERSAMPLING = float(os.environ["PILOT_QUANT_OVERSAMPLING"]) if os.environ.get("PILOT_QUANT_OVERSAMPLING") else None

# Küçük model: 24 GB RAM'li makinede GPU belleğini zorlamaz. Değiştirmek için PILOT_LLM_MODEL ortam değişkeni.
LLM_MODEL = os.environ.get("PILOT_LLM_MODEL", "qwen2.5:7b")
LLM_NUM_CTX = 4096
LLM_NUM_PREDICT = 700
TOP_K_SOURCES = 5             # LLM'e verilen kaynak sayısı
MIN_RERANK_SCORE: float | None = None   # None: eşik kapalı. Test setiyle kalibre edilecek

# Cevap hattı (Adım 2 planı §29, karar 2026-11-06). PILOT_ANSWER_MODE:
#   c     bulut: ikili yol araması (çevirili BM25) + Gemma 4, şema c150b-J, öğe başına doğrulama
#   bugun yerel Ollama (LLM_MODEL) + bugünkü şema ve doğrulama. YALNIZ ELLE açılan geri alma anahtarı; bir sürüm
#         tutulup silinecek. Bulut erişilemezse yerel modele otomatik düşüş YOK: kullanıcıya "servis kullanılamıyor".
ANSWER_MODE = os.environ.get("PILOT_ANSWER_MODE", "c")       # varsayılan c: duman testi geçti (2026-11-06)
ANSWER_MODEL = "google/gemma-4-26b-a4b-it"
ANSWER_SCHEMA_VARIANT = "c150bJ"
# Birincil sağlayıcı ve yedekler, sırayla (ZDR). Yedeğe yalnız kesintide geçilir: HTTP hatası/429, ilk token
# ANSWER_FIRST_TOKEN_S içinde gelmezse ya da akış bekçisi tetiklenirse (sıradakine bir kez). Sağlayıcı her cevapta kayıtlı.
ANSWER_PROVIDERS: tuple[str, ...] = tuple(os.environ.get("PILOT_ANSWER_PROVIDERS", "deepinfra,venice,parasail").split(","))
ANSWER_MAX_TOKENS = 1200
ANSWER_TOP_K = 8               # c kipinde modele verilen kaynak sayısı (TOP_K_SOURCES bugun kipinde)
ANSWER_FIRST_TOKEN_S = 2.5
STREAM_GUARD_N = 40            # akışta art arda bu kadardan fazla boşluk: kaçak, akış kesilir
# BM25 sorgu çevirisi (ikili yol): dense özgün soruyla, BM25 çevrilmiş sorguyla. Süre sınırını aşarsa BM25 çevirisiz.
TRANSLATE_MODEL = "google/gemma-4-26b-a4b-it"
TRANSLATE_PROVIDERS: tuple[str, ...] = ("nextbit", "venice")
TRANSLATE_LIMIT_S = 1.2
# Arama sonrası netleştirme yöntemi: top3 (varsayılan: ilk 3 sonucun dokümanları) | doc_score (ilk FUSED_K adayın RRF
# skorları dokümana göre toplanır; birbirinin yerine geçebilen en iyi iki dokümanın oranı ≥ CLARIFY_DOC_RATIO ise sorulur).
# Oran onaylı soru setiyle seçilecek (bench/clarify_guard.py); şimdilik yalnız seçenek.
CLARIFY_METHOD = os.environ.get("PILOT_CLARIFY_METHOD", "top3")
CLARIFY_DOC_RATIO = float(os.environ.get("PILOT_CLARIFY_DOC_RATIO", "0.6"))
CLARIFY_MIN_SCORE = -7.0      # arama sonrası "hangi ürün/model?" sorusu için en düşük ilk skor (Q10 −8, Q15 −6,2)

# Sesli soru (faster-whisper). Ölçüm (PILOT-RAPORU §16.4, GPU'suz i5): small ve large-v3-turbo varlık doğruluğunda
# eşit (4/5), small soru başına 4 sn, turbo 14 sn. CPU'da small; GPU'lu hedefte turbo. Değiştirmek için PILOT_STT_MODEL.
STT_MODEL = os.environ.get("PILOT_STT_MODEL", "small")
STT_DEVICE = "cpu"
STT_COMPUTE = "int8"          # CPU'da hızlı, doğruluk kaybı küçük

DOCLING_DEVICE =os.environ.get("PILOT_DOCLING_DEVICE", "cpu")   # "mps" Apple GPU belleğini zorlar

# Şekil anlama (VLM): Her şekle doküman işleme sırasında bir kez metin açıklaması yazılır (figures.py).
# Küçük model: GPU'suz dizüstünde şekil başına ~20-60 sn. Değiştirmek için PILOT_VLM_MODEL.
FIGURES_DIR = DATA_DIR / "figures"
VLM_MODEL = os.environ.get("PILOT_VLM_MODEL", "qwen2.5vl:3b")
FIGURE_MIN_AREA = 0.02        # sayfa alanına oranı: daha küçükler ikon/uyarı işareti/logo, açıklanmaz
FIGURE_MIN_SIDE = 50          # point: kısa kenarı bundan dar olanlar (çizgi, şerit) açıklanmaz
FIGURE_DPI = 150
FIGURE_MAX_PX = 896           # VLM'e giden görselin uzun kenarı (görsel token sayısı ve CPU süresi bununla büyür)


def _hf_models_cached() -> bool:
    """Embedding ve reranker modelleri yerel Hugging Face önbelleğinde var mı?"""
    hub = Path(os.environ.get("HF_HUB_CACHE") or Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub")
    return all((hub / f"models--{m.replace('/', '--')}").exists() for m in (EMBED_MODEL, RERANK_MODEL))


# Tam çevrimdışı çalışma: Modeller önbellekte varsa Hugging Face'e güncellik sorgusu yapılmaz (ağ kesilebilir kararı).
# İlk kurulumda (model yoksa) çevrimiçi kalır. Kullanıcı ayarladıysa ona dokunulmaz.
# Bu modül, Hugging Face kütüphanelerinden önce yüklendiği için ayar onlara ulaşır.
if "HF_HUB_OFFLINE" not in os.environ and _hf_models_cached():
    os.environ["HF_HUB_OFFLINE"] = "1"
