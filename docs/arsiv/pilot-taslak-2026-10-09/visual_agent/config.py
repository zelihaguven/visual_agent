"""Pilot ayarları. Ortam değişkenleriyle değiştirilebilir (VA_ öneki)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

PILOT_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = PILOT_DIR.parent
MANUALS_DIR = Path(os.environ.get("VA_MANUALS_DIR", PROJECT_DIR / "Pre" / "manuals" / "public"))
DATA_DIR = Path(os.environ.get("VA_DATA_DIR", PILOT_DIR / "data"))
CONFIG_DIR = PILOT_DIR / "config"

PARSED_DIR = DATA_DIR / "parsed"        # Docling çıktıları (parti parti, yeniden başlatılabilir)
CHUNKS_DIR = DATA_DIR / "chunks"        # doküman başına chunks.jsonl
QDRANT_DIR = DATA_DIR / "qdrant"        # gömülü Qdrant (Docker gerekmez)
AUDIT_DIR = DATA_DIR / "audit"          # denetim izi (JSONL)
AUDIO_DIR = DATA_DIR / "audio"          # üretilen ses dosyaları (geçici)
VIEW_DIR = DATA_DIR / "views"           # kullanıcıya gönderilen sayfa aralığı PDF'leri (geçici)


def _env(name: str, default):
    raw = os.environ.get(f"VA_{name}")
    if raw is None:
        return default
    if isinstance(default, bool):
        return raw.lower() in ("1", "true", "yes", "evet")
    if isinstance(default, int):
        return int(raw)
    if isinstance(default, float):
        return float(raw)
    return raw


@dataclass
class Settings:
    # Embedding ve rerank (kurum içi, CPU'da çalışır)
    embed_model: str = _env("EMBED_MODEL", "BAAI/bge-m3")
    embed_max_len: int = _env("EMBED_MAX_LEN", 512)
    rerank_model: str = _env("RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
    rerank_enabled: bool = _env("RERANK", True)
    rerank_max_len: int = _env("RERANK_MAX_LEN", 384)
    rerank_top_n: int = _env("RERANK_TOP_N", 12)        # rerank'e giren aday sayısı (CPU süresi)
    # Arama
    collection: str = _env("COLLECTION", "manuals")
    candidates: int = _env("CANDIDATES", 30)            # her kanaldan (dense / sparse) aday
    top_k: int = _env("TOP_K", 5)                       # LLM'e giden parça sayısı
    rrf_k: int = _env("RRF_K", 60)
    # Eşik: rerank skoru (0-1) bunun altındaysa "bulunamadı". Test setiyle kalibre edilir.
    threshold: float = _env("THRESHOLD", 0.20)
    # Rerank kapalıyken kullanılan eşik (RRF skoru)
    threshold_rrf: float = _env("THRESHOLD_RRF", 0.0)
    # Chunking
    chunk_words: int = _env("CHUNK_WORDS", 220)
    # LLM: extractive (anahtarsız, offline) | anthropic | openai | gemini | ollama
    llm_provider: str = _env("LLM_PROVIDER", "extractive")
    llm_model: str = _env("LLM_MODEL", "")
    llm_retry: int = _env("LLM_RETRY", 1)
    # TTS: windows (offline, Microsoft Tolga) | azure | edge | none
    tts_provider: str = _env("TTS_PROVIDER", "windows")
    tts_voice: str = _env("TTS_VOICE", "")
    # STT: faster-whisper modeli (CPU için 'small' önerilir; doğruluk için 'large-v3-turbo')
    stt_model: str = _env("STT_MODEL", "small")
    # Kaynak görüntüleme: varsayılan olarak cevap sayfasının en fazla 1 öncesi ve 1 sonrası
    page_window: int = _env("PAGE_WINDOW", 1)
    # Denetim izi saklama süresi (gün). KVKK sorumlusuyla kesinleştirilecek.
    audit_retention_days: int = _env("AUDIT_RETENTION_DAYS", 365)
    # Hedef yanıt süresi (cevaplar.md: 5 sn)
    target_latency_s: float = _env("TARGET_LATENCY_S", 5.0)


SETTINGS = Settings()


@dataclass
class DocMeta:
    doc_id: str
    file: str
    title: str
    brand: str
    doc_type: str
    product: str | None = None
    product_model: str | None = None
    version: str | None = None
    lang: str = "en"
    access: str = "brand"          # public | brand
    scanned: bool = False
    extra: dict = field(default_factory=dict)

    @property
    def path(self) -> Path:
        return MANUALS_DIR / self.file


def load_documents() -> dict[str, DocMeta]:
    raw = json.loads((CONFIG_DIR / "documents.json").read_text("utf-8"))
    out = {}
    for d in raw["documents"]:
        known = {k: v for k, v in d.items() if k in DocMeta.__dataclass_fields__ and not k.startswith("_")}
        extra = {k: v for k, v in d.items() if k not in known}
        out[d["doc_id"]] = DocMeta(**known, extra=extra)
    return out


def ensure_dirs() -> None:
    for d in (PARSED_DIR, CHUNKS_DIR, QDRANT_DIR, AUDIT_DIR, AUDIO_DIR, VIEW_DIR):
        d.mkdir(parents=True, exist_ok=True)
