"""Pilot arayüzü (Streamlit): soru -> cevap + doğrulama rozeti + vurgulu kaynak sayfa + isteğe bağlı ses.

Çalıştır: .venv/bin/streamlit run app.py
"""
import subprocess
import tempfile
from pathlib import Path

import streamlit as st

from pilot.pipeline import Result, soru_cevapla
from pilot.registry import BY_ID, DOCS
from pilot.render import page_image

ROOT = Path(__file__).parent
TTS_PY = ROOT / ".venv-tts" / "bin" / "python"

st.set_page_config(page_title="Visual Agent Pilot", layout="wide")
st.title("Visual Agent: Pilot")
st.caption("Lokal çalışır. Küçük model ile araştırma pilotu, üretim kalitesi değildir.")

brands = sorted({d.brand for d in DOCS})
chosen = st.multiselect("Marka / kaynak filtresi (boşsa tümü)", brands)
question = st.text_input("Soru", placeholder="Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı?")

if st.button("Sor", type="primary") and question.strip():
    with st.spinner("Aranıyor ve cevaplanıyor..."):
        st.session_state["result"] = soru_cevapla(question.strip(), brands=chosen or None)
        st.session_state.pop("audio", None)

res: Result | None = st.session_state.get("result")
if res:
    left, right = st.columns([1, 1])
    with left:
        st.subheader(res.verification.badge)
        if res.context.matched:
            st.caption("Sorudan okunan filtre: " + ", ".join(res.context.matched))
        ans = res.answer
        if ans.get("bulunamadi"):
            st.info("Bu bilgi manuellerde bulunamadı.")
        else:
            st.markdown(ans.get("cevap") or "_(cevap üretilemedi)_")
            if ans.get("netlestirme_sorusu"):
                st.warning(ans["netlestirme_sorusu"])
            for q in ans.get("alintilar", []):
                st.markdown(f"> {q.get('metin', '')}  \n> *(kaynak {q.get('kaynak_no')})*")
        for p in res.verification.problems:
            st.error(p)
        t = res.timings
        st.caption(f"Süre: arama {t.get('search', 0):.1f} sn · model {t.get('llm', 0):.1f} sn · toplam {t.get('total', 0):.1f} sn")
        if res.speech_text:
            st.markdown(f"**Sesli metin:** {res.speech_text}")
            if TTS_PY.exists() and st.button("🔊 Sesli oku"):
                with st.spinner("Seslendiriliyor (CPU, ~15 sn)..."):
                    out = Path(tempfile.mkdtemp()) / "cevap.wav"
                    subprocess.run([str(TTS_PY), str(ROOT / "tools" / "tts_say.py"), res.speech_text, str(out)],
                                   check=True)
                    st.session_state["audio"] = out.read_bytes()
            if "audio" in st.session_state:
                st.audio(st.session_state["audio"], format="audio/wav")
    with right:
        if res.hits:
            labels = [f"[{i}] {h.chunk['doc_id']} · s.{h.chunk['page']}" for i, h in enumerate(res.hits, 1)]
            pick = st.selectbox("Kaynak", range(len(labels)), format_func=lambda i: labels[i])
            chunk = res.hits[pick].chunk
            page = st.selectbox("Sayfa", chunk["pages"], index=0)
            printed = chunk["page_labels"].get(str(page))
            if printed and printed != str(page):
                st.caption(f"Basılı sayfa {printed} (PDF s.{page})")
            st.image(page_image(BY_ID[chunk["doc_id"]].path, page, chunk["boxes"]), width="stretch")
