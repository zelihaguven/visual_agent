"""Sesli soru (STT): WAV → 16 kHz mono → faster-whisper → metin. Akış: MIMARI.md §4.13.

Ses yalnız bellekte işlenir, diske yazılmaz (karar: ses saklanmaz).
Ses çözme scipy ile yapılır: faster-whisper'ın PyAV çözücüsü bu Windows makinesinde hata verdi
("metadata_errors"), tarayıcının gönderdiği WAV'ı scipy sorunsuz okuyor.
"""
import io
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from math import gcd

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

from .config import STT_COMPUTE, STT_DEVICE, STT_MODEL
from .query import spoken_codes
from .registry import DOCS
from .terms import GLOSSARY

SAMPLE_RATE = 16_000
LOW_CONFIDENCE = -0.8      # ortalama log olasılığın altı: "tanıma güveni düşük" uyarısı (pilot ayarı)


@dataclass(frozen=True)
class Transcript:
    text: str
    audio_seconds: float
    seconds: float             # yazıya çevirme süresi (model yükleme hariç)
    avg_logprob: float         # Whisper'ın kendi güveni, 0'a yakın = emin
    low_confidence: bool


def decode_wav(data: bytes) -> np.ndarray:
    """WAV baytları → 16 kHz mono float32 [-1, 1]. Tamsayı ve float WAV desteklenir."""
    rate, audio = wavfile.read(io.BytesIO(data))
    if audio.dtype.kind == "i":
        audio = audio.astype(np.float32) / np.iinfo(audio.dtype).max
    elif audio.dtype.kind == "u":      # 8 bit WAV işaretsizdir
        audio = (audio.astype(np.float32) - 128) / 128
    else:
        audio = audio.astype(np.float32)
    if audio.ndim == 2:
        audio = audio.mean(axis=1)
    if rate != SAMPLE_RATE:
        g = gcd(rate, SAMPLE_RATE)
        audio = resample_poly(audio, SAMPLE_RATE // g, rate // g).astype(np.float32)
    return np.clip(audio, -1.0, 1.0)


def hint_terms() -> str:
    """Whisper'a 'bu kelimeler geçebilir' ipucu: kayıttaki markalar, makine modelleri, ürünler ve atölye terimleri.

    Liste elle ayrıca tutulmaz, doküman kaydı ve terim sözlüğünden üretilir (gerçek sistemde ingestion metadata'sı).
    """
    words: list[str] = []
    for d in DOCS:
        if d.doc_type == "machine_manual":
            words.append(f"{d.brand} {d.product.split()[0]}")        # "Brother S-7300A", "Bosch RA1171"
        elif d.doc_type == "product_standard":
            words += [d.brand.split(" (")[0], d.product.lower()]      # "US Army", "ceket"
    words += list(GLOSSARY)
    words += ["SPI", "inç başına dikiş", "hata kodu"]
    return ", ".join(dict.fromkeys(words)) + "."


@lru_cache(maxsize=1)
def _model():
    from faster_whisper import WhisperModel
    return WhisperModel(STT_MODEL, device=STT_DEVICE, compute_type=STT_COMPUTE)


def _tidy(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    # Whisper ipucundaki listeyi aynen tekrarlayabiliyor (sessiz kayıtta bilinen davranış): metin ipucuyla başlıyorsa at
    if text and hint_terms().startswith(text[:40]):
        return ""
    # Kod söylendiği gibi yazılmışsa yazılı koda çevrilir: kullanıcı onay kutusunda "S-7300A'da E050" görür
    return spoken_codes(text)


def transcribe(data: bytes) -> Transcript:
    """Sesli soruyu yazıya çevirir. data: tarayıcının gönderdiği WAV."""
    audio = decode_wav(data)
    model = _model()
    t = time.time()
    segments, _info = model.transcribe(audio, language="tr", beam_size=5, vad_filter=True,
                                       initial_prompt=hint_terms(), condition_on_previous_text=False)
    segments = list(segments)          # üretici: çeviri burada çalışır
    text = _tidy(" ".join(s.text for s in segments))
    logprob = float(np.mean([s.avg_logprob for s in segments])) if segments else float("-inf")
    return Transcript(text, len(audio) / SAMPLE_RATE, time.time() - t, logprob,
                      low_confidence=not text or logprob < LOW_CONFIDENCE)
