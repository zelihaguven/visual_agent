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
EDGE_BAND = 0.12              # üst/alt bilgi tespiti için sayfa kenar oranı
FURNITURE_MIN_RATIO = 0.5     # üst/alt bilgi: sayfaların en az bu oranında tekrar eder
SENTENCE_END = (".", "!", "?", ":", ";", '"', ")")

EMBED_MODEL = "BAAI/bge-m3"
RERANK_MODEL = "BAAI/bge-reranker-v2-m3"
EMBED_DEVICE = "cpu"          # MPS'te bge-m3 ve reranker yanlış sonuç veriyor (KURULUM-LOGU.md #1)
EMBED_MAX_LENGTH = 512
EMBED_BATCH = 16
COLLECTION = "manuals"

# Küçük model: 24 GB RAM'li makinede GPU belleğini zorlamaz. Değiştirmek için PILOT_LLM_MODEL ortam değişkeni.
LLM_MODEL = os.environ.get("PILOT_LLM_MODEL", "qwen2.5:7b")
LLM_NUM_CTX = 4096
LLM_NUM_PREDICT = 700
TOP_K_SOURCES = 5             # LLM'e verilen kaynak sayısı
MIN_RERANK_SCORE: float | None = None   # None: eşik kapalı. Test setiyle kalibre edilecek
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
