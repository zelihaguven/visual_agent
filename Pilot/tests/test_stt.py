"""Sesli soru (STT): ses çözme, terim ipucu, güven. Whisper modeli taklit edilir (model gerekmez)."""
import io
from types import SimpleNamespace

import numpy as np
import pytest
from scipy.io import wavfile

from pilot import stt


def wav_bytes(audio: np.ndarray, rate: int) -> bytes:
    buf = io.BytesIO()
    wavfile.write(buf, rate, audio)
    return buf.getvalue()


@pytest.mark.parametrize("dtype,rate,channels", [
    (np.int16, 48_000, 1),       # tarayıcı kaydı (st.audio_input)
    (np.int16, 44_100, 2),       # stereo
    (np.float32, 24_000, 1),     # Chatterbox çıktısı (float WAV, eski hata: "unknown format 3")
    (np.int32, 16_000, 1),
])
def test_decode_wav_gives_16k_mono_float(dtype, rate, channels):
    t = np.linspace(0, 1, rate, endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * 440 * t)
    if np.issubdtype(dtype, np.integer):
        wave = (wave * np.iinfo(dtype).max).astype(dtype)
    else:
        wave = wave.astype(dtype)
    if channels == 2:
        wave = np.stack([wave, wave], axis=1)
    out = stt.decode_wav(wav_bytes(wave, rate))
    assert out.dtype == np.float32 and out.ndim == 1
    assert abs(len(out) - stt.SAMPLE_RATE) <= 1             # 1 saniye
    assert 0.4 < np.abs(out).max() <= 1.0                    # ölçek korunur


def test_hint_terms_come_from_registry_and_glossary():
    hint = stt.hint_terms()
    for term in ("Brother S-7300A", "Brother S-7300B", "ceket", "pantolon", "US Army", "çağanoz", "masura", "SPI"):
        assert term in hint


class FakeModel:
    def __init__(self, segments):
        self.segments = segments
        self.kwargs = {}

    def transcribe(self, audio, **kw):
        self.kwargs = kw
        return iter(self.segments), None


def seg(text, logprob):
    return SimpleNamespace(text=text, avg_logprob=logprob)


@pytest.fixture
def silence():
    return wav_bytes(np.zeros(16_000, dtype=np.int16), 16_000)


def test_transcribe_joins_segments_and_passes_hints(monkeypatch, silence):
    fake = FakeModel([seg(" S-7300A makinesinde", -0.2), seg(" üst iplik gergin değil. ", -0.3)])
    monkeypatch.setattr(stt, "_model", lambda: fake)
    tr = stt.transcribe(silence)
    assert tr.text == "S-7300A makinesinde üst iplik gergin değil."
    assert tr.audio_seconds == pytest.approx(1.0)
    assert not tr.low_confidence
    assert fake.kwargs["language"] == "tr" and "S-7300A" in fake.kwargs["initial_prompt"]


def test_spoken_codes_are_written_in_transcript(monkeypatch, silence):
    monkeypatch.setattr(stt, "_model", lambda: FakeModel([seg(" Es yetmiş üç yüz A'da E sıfır elli hatası ne demek?", -0.3)]))
    assert stt.transcribe(silence).text == "S-7300A'da E050 hatası ne demek?"


def test_low_logprob_is_flagged(monkeypatch, silence):
    monkeypatch.setattr(stt, "_model", lambda: FakeModel([seg("es yetmiş üç", -1.4)]))
    assert stt.transcribe(silence).low_confidence


def test_empty_recognition_is_low_confidence(monkeypatch, silence):
    monkeypatch.setattr(stt, "_model", lambda: FakeModel([]))
    tr = stt.transcribe(silence)
    assert tr.text == "" and tr.low_confidence


def test_echoed_hint_list_is_dropped(monkeypatch, silence):
    # Whisper sessiz kayıtta ipucu listesini aynen yazabiliyor: soru sanılmamalı
    monkeypatch.setattr(stt, "_model", lambda: FakeModel([seg(stt.hint_terms()[:60], -0.1)]))
    assert stt.transcribe(silence).text == ""
