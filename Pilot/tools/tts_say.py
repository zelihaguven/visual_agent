"""Chatterbox Multilingual ile Türkçe seslendirme (ayrı ortamda çalışır: .venv-tts, CPU).

Kullanım: .venv-tts/bin/python tools/tts_say.py "metin" cikti.wav
"""
import sys
import warnings

import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS

warnings.filterwarnings("ignore")

if __name__ == "__main__":
    text, out = sys.argv[1], sys.argv[2]
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")   # MPS'te bozuk çıktı veriyor
    with torch.no_grad():
        wav = model.generate(text, language_id="tr")
    ta.save(out, wav.cpu(), model.sr)
