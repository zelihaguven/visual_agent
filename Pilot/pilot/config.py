"""Yollar ve sabitler. Tek yerden değişir."""
import os
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parent.parent
MANUALS_DIR = PILOT_DIR.parent / "Pre" / "manuals" / "public"
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

DOCLING_DEVICE = os.environ.get("PILOT_DOCLING_DEVICE", "cpu")   # "mps" Apple GPU belleğini zorlar
