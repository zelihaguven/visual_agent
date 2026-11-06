"""Arayüz duman testi (Adım 2 planı §29.5 adım 4): app.py, Streamlit'in başsız test aracıyla (AppTest), c kipinde,
gerçek uygulama yolu. Beş senaryo: cevap, netleştirme, bulunamadı, sesli soru (STT sonucu oturuma yazılarak; mikrofon
yok), İngilizce soru. Ekrandaki rozet, öğe listesi, kaynak etiketi, sağlayıcı ve hata/uyarı metinleri okunur.

Kullanım (Pilot klasöründe):  $env:PILOT_ANSWER_MODE = "c"; python -m bench.arayuz_duman
"""
import os
import sys


from pathlib import Path

APP = Path(__file__).resolve().parents[1] / "app.py"
SCENARIOS = [
    ("cevap", "Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı?", False),
    ("netleştirme", "Dış görünür dikişlerde SPI kaç olmalı?", False),
    ("bulunamadı", "S-7300A'nın garanti süresi kaç yıl?", False),
    ("sesli soru", "masura kovanı nasıl takılır", True),
    ("İngilizce", "What should the stitches per inch be for the outside visible seams of the jacket?", False),
]


def main() -> int:
    from bench import require_mode
    require_mode("c")
    from streamlit.testing.v1 import AppTest
    rows = []
    for name, q, voice in SCENARIOS:
        at = AppTest.from_file(str(APP), default_timeout=180)
        at.run()
        at.text_input(key="question").input(q)
        if voice:
            at.session_state["stt"] = {"text": q, "low": False, "audio_s": 2.0, "secs": 1.0}
        next(b for b in at.button if b.label == "Sor").click()
        at.run()
        texts = lambda els: [e.value for e in els]
        row = {"senaryo": name, "soru": q, "rozet": texts(at.subheader)[:1], "uyari": texts(at.warning)[:2],
               "hata": texts(at.error)[:2], "bilgi": texts(at.info)[:2],
               "cevap": [m for m in texts(at.markdown) if m and ("[" in m or m[:2] in ("1.",))][:3],
               "alt": [c for c in texts(at.caption) if "sağlayıcı" in c or "Süre" in c][:1],
               "dugmeler": [b.label for b in at.button if b.label not in ("Sor",)][:5],
               "istisna": [str(e.value)[:200] for e in at.exception]}
        rows.append(row)
        print(row, flush=True)
    ok = all(not r["istisna"] for r in rows)
    print("ARAYÜZ DUMAN TESTİ:", "geçti (istisna yok)" if ok else "İSTİSNA VAR")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
