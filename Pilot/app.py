"""Pilot arayüzü (Streamlit): soru -> cevap + doğrulama rozeti + vurgulu kaynak sayfa + isteğe bağlı ses.

Çalıştır: .venv/bin/streamlit run app.py
"""
import os
import re
import subprocess
import time
from pathlib import Path

import streamlit as st

from pilot.pipeline import Result, soru_cevapla
from pilot.registry import BRAND_ALIASES, BY_ID, DOCS
from pilot.render import page_image

ROOT = Path(__file__).parent
# Sesli okuma ayrı ortamda çalışır (.venv-tts). macOS/Linux: bin/python, Windows: Scripts/python.exe
TTS_PY = next((p for p in (ROOT / ".venv-tts" / "bin" / "python", ROOT / ".venv-tts" / "Scripts" / "python.exe")
               if p.exists()), None)
AUDIO_DIR = ROOT / "data" / "audio"   # üretilen sesler kalıcı tutulur (pilot testlerinde dinlenebilsin diye)


def _slug(text: str, n: int = 40) -> str:
    return re.sub(r"[^\w]+", "-", text.lower()).strip("-")[:n] or "ses"


def synthesize(question: str, speech_text: str, lang: str = "tr") -> Path:
    """Sesli metni Chatterbox ile (cevabın dilinde) seslendirir, data/audio/ altına wav + açıklama dosyası olarak kaydeder."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    out = AUDIO_DIR / f"{time.strftime('%Y%m%d-%H%M%S')}_{_slug(question)}.wav"
    env = {**os.environ, "PYTHONUTF8": "1"}
    # Ses modeli önbellekteyse çevrimdışı; değilse (ilk kullanım) indirebilsin
    hub = Path(os.environ.get("HF_HOME") or Path.home() / ".cache" / "huggingface") / "hub"
    env["HF_HUB_OFFLINE"] = "1" if (hub / "models--ResembleAI--chatterbox").exists() else "0"
    proc = subprocess.run([str(TTS_PY), str(ROOT / "tools" / "tts_say.py"), speech_text, str(out), lang],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    if proc.returncode != 0 or not out.exists():
        raise RuntimeError(proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "TTS çıktı üretmedi")
    out.with_suffix(".txt").write_text(f"Soru: {question}\nSesli metin: {speech_text}\n", encoding="utf-8")
    return out

st.set_page_config(page_title="Visual Agent Pilot", layout="wide")
st.title("Visual Agent: Pilot")
st.caption("Lokal çalışır. Küçük model ile araştırma pilotu, üretim kalitesi değildir.")

with st.sidebar:
    st.subheader("Üretilen sesler")
    files = sorted(AUDIO_DIR.glob("*.wav"), reverse=True) if AUDIO_DIR.exists() else []
    if not files:
        st.caption("Henüz ses yok. Cevaptan sonra '🔊 Sesli oku' ile üretilir.")
    for f in files[:10]:
        info = f.with_suffix(".txt")
        st.caption(info.read_text(encoding="utf-8").splitlines()[0] if info.exists() else f.name)
        st.audio(str(f), format="audio/wav")

brands = sorted({d.brand for d in DOCS})
chosen = st.multiselect("Marka filtresi (boşsa tüm markalar)", brands)

# --- Sesli soru (STT): bas-konuş → yazıya çevir → soru kutusuna yaz → kullanıcı onaylar (MIMARI.md §4.13) ---
# Ses yalnız bellekte işlenir. Çeviriden sonra kayıt bileşeninin anahtarı değişir: bileşen sıfırlanır, ses düşer.
st.session_state.setdefault("mic_n", 0)
spoken = st.audio_input("🎤 Sesli soru: kaydı başlatın, sorunuzu söyleyin, durdurun", key=f"mic-{st.session_state['mic_n']}")
if spoken is not None:
    from pilot.stt import transcribe      # STT modeli yalnız sesli soru gelince yüklenir
    with st.spinner("Ses yazıya çevriliyor (ilk kullanımda model yükleniyor)..."):
        try:
            tr = transcribe(spoken.getvalue())
            st.session_state["question"] = tr.text
            st.session_state["stt"] = {"text": tr.text, "low": tr.low_confidence, "audio_s": tr.audio_seconds,
                                       "secs": tr.seconds}
        except Exception as exc:  # model indirilmemiş, ses bozuk: arayüz çökmesin
            st.session_state["stt"] = {"error": str(exc)}
    del spoken
    st.session_state["mic_n"] += 1
    st.rerun()

question = st.text_input("Soru", key="question",
                         placeholder="Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı?")
stt = st.session_state.get("stt")
if stt and "error" in stt:
    st.error(f"Ses yazıya çevrilemedi: {stt['error']}. STT modeli indirilmemişse: README.md → 'Sesli soru'.")
elif stt:
    # Onay: tanınan metin otomatik gönderilmez. Sistem ne anladı (hangi makine/ürün) da gösterilir (R9).
    from pilot.query import analyze_query
    seen = [BY_ID[d].product for d in analyze_query(question).doc_ids]
    st.info("🎤 Tanınan metin soru kutusuna yazıldı. **Kontrol edin, gerekirse düzeltin, sonra 'Sor'a basın.**  \n"
            + ("Sorudan okunan: **" + ", ".join(seen) + "**" if seen
               else "Soruda makine, ürün ya da marka okunmadı: Sor'a basınca hangi kaynak olduğu sorulacak.")
            + f"  \n_Kayıt {stt['audio_s']:.1f} sn · çeviri {stt['secs']:.1f} sn · ses saklanmadı_")
    if stt["low"]:
        st.warning("Tanıma güveni düşük. Metni dikkatle kontrol edin; model kodlarında harf ve rakam karışabilir.")


def start(q: str, brands: list[str] | None, doc_ids: list[str] | None = None, each: list[str] | None = None,
          switched_from: str | None = None, voice: bool = False) -> None:
    """Yeni bir çalıştırma başlatır. Eski cevap, sayfa ve ses hemen ekrandan kalkar.
    switched_from: kullanıcı 'bulunamadı' sonrası başka modelin kılavuzuna geçtiyse asıl sorduğu doküman.
    voice: soru sesle soruldu (sorudan kaynak çıkmıyorsa hat kaynak sorar)."""
    for key in [k for k in st.session_state if k.startswith(("results", "audio"))]:
        del st.session_state[key]
    st.session_state["pending"] = {"q": q, "brands": brands, "doc_ids": doc_ids, "each": each,
                                   "switched_from": switched_from, "voice": voice}
    st.rerun()


def siblings(doc_id: str) -> list[str]:
    """Aynı makine ailesindeki diğer modellerin dokümanları (S-7300A → S-7300B)."""
    for ids in BRAND_ALIASES.values():
        if doc_id in ids:
            return [d for d in ids if d != doc_id]
    return []


if st.button("Sor", type="primary") and question.strip():
    start(question.strip(), chosen or None, voice=st.session_state.pop("stt", None) is not None)

if "pending" in st.session_state:
    p = st.session_state["pending"]
    runs = [(BY_ID[d].product, [d]) for d in p["each"]] if p["each"] else [(None, p["doc_ids"])]
    results = []
    for i, (label, ids) in enumerate(runs, 1):
        extra = f" · {label} ({i}/{len(runs)})" if label else ""
        # Adım adım durum: aranıyor → cevap hazırlanıyor → kontrol ediliyor (her adım süresiyle)
        with st.status(f"\"{p['q']}\"{extra}", expanded=True) as box:
            t_step = {"t": time.time()}

            def step(msg: str, box=box, t_step=t_step) -> None:
                box.write(f"⏳ {msg}... (önceki adım {time.time() - t_step['t']:.0f} sn)")
                t_step["t"] = time.time()

            r = soru_cevapla(p["q"], brands=p["brands"], doc_ids=ids, on_step=step, voice=p.get("voice", False))
            box.update(label=f"Tamamlandı ({r.timings.get('total', 0):.0f} sn): \"{p['q']}\"{extra}",
                       state="complete", expanded=False)
        results.append((label, r))
    st.session_state["results"] = {"q": p["q"], "brands": p["brands"], "items": results, "doc_ids": p["doc_ids"],
                                   "switched_from": p.get("switched_from")}
    del st.session_state["pending"]
    st.rerun()


def cited_sources(r: Result) -> list[int]:
    """Cevabın dayandığı kaynak numaraları: alıntı yapılanlar + cevaptaki [n] atıfları (aramadaki sırayla)."""
    nos = {q.get("kaynak_no") for q in r.answer.get("alintilar", [])}
    nos |= {int(n) for n in re.findall(r"\[(\d+)\]", r.answer.get("cevap") or "")}
    return sorted(n for n in nos if isinstance(n, int) and 1 <= n <= len(r.hits))


def source_label(r: Result, n: int) -> str:
    """'[1] Brother · S-7300A düz dikiş makinesi · 1. MACHINE SPECIFICATIONS · s.1 (PDF s.12)'"""
    c = r.hits[n - 1].chunk
    meta = BY_ID[c["doc_id"]]
    printed = c["page_labels"].get(str(c["page"]))
    page = f"s.{printed} (PDF s.{c['page']})" if printed and printed != str(c["page"]) else f"s.{c['page']}"
    section = f" · {c['section'][:60]}" if c.get("section") else ""
    return f"[{n}] {meta.brand} · {meta.product}{section} · {page}"


def render_clarify(res: Result) -> None:
    """Netleştirme: kaynak seçimi (model/ürün belirsiz) ya da konu seçimi (soru neyi sorduğunu söylemiyor).
    Seçimden sonra soru yeniden çalıştırılır."""
    state_ = st.session_state["results"]
    st.subheader(res.verification.badge)
    st.warning(res.answer["netlestirme_sorusu"])
    opts = res.answer.get("secenekler", [])
    sources = [o for o in opts if "doc_id" in o]
    topics = [o for o in opts if "ek" in o]
    if sources:
        few = len(sources) <= 3            # "hepsi için ayrı ayrı" yalnız birkaç seçenekte anlamlı
        cols = st.columns(len(sources) + (1 if few else 0))
        for col, o in zip(cols, sources):
            if col.button(o["etiket"], key=f"opt-{o['doc_id']}"):
                start(res.question, state_["brands"], doc_ids=[o["doc_id"]])
        if few:
            if cols[-1].button("İkisi için ayrı ayrı" if len(sources) == 2 else "Hepsi için ayrı ayrı", key="opt-each"):
                start(res.question, state_["brands"], each=[o["doc_id"] for o in sources])
            st.caption("Her seçenek için model ayrı çalışır: 'ayrı ayrı' bu bilgisayarda süreyi katlar.")
    if topics:
        # Konu seçilince soruya eklenir; kaynak seçimi korunur
        cols = st.columns(len(topics))
        for i, (col, o) in enumerate(zip(cols, topics)):
            if col.button(o["etiket"], key=f"topic-{i}"):
                start(f"{res.question} ({o['ek']})", state_["brands"], doc_ids=state_.get("doc_ids"))
    if not sources:
        detail = st.text_input("Ya da sorunuza ayrıntı ekleyin", key="detail",
                               placeholder=res.answer.get("ipucu") or "")
        if st.button("Ayrıntıyla sor", key="detail-go") and detail.strip():
            start(f"{res.question} {detail.strip()}", state_["brands"], doc_ids=state_.get("doc_ids"))
        if res.answer.get("ipucu"):
            st.caption(res.answer["ipucu"])


def render_result(res: Result, key: str) -> None:
    left, right = st.columns([1, 1])
    with left:
        st.subheader(res.verification.badge)
        if res.context.doc_ids:
            st.caption("Sorudan okunan: " + ", ".join(BY_ID[d].product for d in res.context.doc_ids))
        ans = res.answer
        state_ = st.session_state.get("results", {})
        if state_.get("switched_from"):
            orig, now = BY_ID[state_["switched_from"]].product, BY_ID[state_["doc_ids"][0]].product
            st.warning(f"Dikkat: Bu cevap **{now}** kılavuzundan. Sorduğunuz **{orig}** için geçerli olmayabilir; "
                       f"değeri makinenizle karşılaştırmadan kullanmayın.")
        if res.expanded_terms:
            st.caption("Terim sözlüğü (taslak) aramaya ekledi: " + ", ".join(res.expanded_terms))
        if res.context_terms:
            st.caption("Seçilen kaynak bunlara göre değişmediği için aramada kullanılmadı: "
                       + ", ".join(res.context_terms))
        if ans.get("bulunamadi"):
            st.info("Bu bilgi manuellerde bulunamadı." + (f" {ans['neden']}" if ans.get("neden") else ""))
            # Sorudaki ürün başka bir kaynakta: o kaynağa geçiş (ör. "ceket" → Ceket şartnamesi)
            for d in ans.get("oneri", []):
                if st.button(f"🔎 {BY_ID[d].product} kaynağında ara", key=f"sug-{key}-{d}"):
                    start(res.question, state_.get("brands"), doc_ids=[d])
            # Makine ayarı soruluyorsa: ürün adı olmadan aynı kaynakta ("ceket dikerken iplik gerginliği")
            if ans.get("yalin_soru") and state_.get("doc_ids"):
                if st.button(f"🔎 Ürün adı olmadan bu kaynakta ara: \"{ans['yalin_soru']}\"", key=f"bare-{key}"):
                    start(ans["yalin_soru"], state_.get("brands"), doc_ids=state_["doc_ids"])
            # Tek bir model kılavuzunda bulunamadıysa aynı ailedeki diğer modelleri önerir ("şunu mu demek istediniz?")
            scope = state_.get("doc_ids") or list(res.context.doc_ids)
            if len(scope) == 1 and not state_.get("switched_from") and not ans.get("neden"):
                for other in siblings(scope[0]):
                    if st.button(f"🔎 {BY_ID[other].product} kılavuzunda ara", key=f"alt-{key}-{other}"):
                        start(res.question, state_.get("brands"), doc_ids=[other], switched_from=scope[0])
                if siblings(scope[0]):
                    st.caption("Bilgi aynı ailedeki başka bir modelin kılavuzunda olabilir. "
                               "Gelen cevap o model için geçerlidir, sizin makinenizle farklı olabilir.")
        else:
            if ans.get("cevap"):
                st.markdown(ans["cevap"])
            elif res.verification.status == "failed":
                st.warning("Güvenilir bir cevap üretilemedi. Bu bilgi kaynaklarda bulunmuyor olabilir.")
            if ans.get("netlestirme_sorusu"):
                st.warning(ans["netlestirme_sorusu"])
            for q in ans.get("alintilar", []):
                no = q.get("kaynak_no")
                where = source_label(res, no) if isinstance(no, int) and 1 <= no <= len(res.hits) else f"kaynak {no}"
                st.markdown(f"> {q.get('metin', '')}  \n> *{where}*")
        for p in res.verification.problems:
            # Seste düşen tolerans hata değil, bilgi: sesli metin doğrulanmış cevaptan yeniden üretildi (R15)
            (st.info if p.startswith("Sesli metinde tolerans") else st.error)(p)
        t = res.timings
        st.caption(f"Süre: arama {t.get('search', 0):.1f} sn · model {t.get('llm', 0):.1f} sn · toplam {t.get('total', 0):.1f} sn")
        if res.speech_text:
            st.markdown(f"**Sesli metin:** {res.speech_text}")
            if TTS_PY is None:
                st.info("Sesli okuma ortamı (.venv-tts) kurulu değil. Kurulum: README.md → 'Sesli okuma'.")
            elif st.button("🔊 Sesli oku", key=f"tts-{key}"):
                with st.spinner("Seslendiriliyor (CPU'da model yükleme dahil 1–3 dk sürebilir)..."):
                    try:
                        path = synthesize(res.question, res.speech_text, res.lang)
                        st.session_state[f"audio-{key}"] = str(path)
                    except Exception as exc:  # TTS hatası arayüzü çökertmesin
                        st.error(f"Seslendirme başarısız: {exc}")
            if f"audio-{key}" in st.session_state:
                path = Path(st.session_state[f"audio-{key}"])
                st.audio(path.read_bytes(), format="audio/wav")
                st.caption(f"Kaydedildi: {path.relative_to(ROOT)}")
    with right:
        # Sadece cevabın dayandığı kaynaklar gösterilir; aramanın getirip cevapta kullanılmayan parçalar gösterilmez.
        # Pilotta kullanıcı yetkisi yok. Gerçek sistemde arama yetki filtresiyle yapıldığı için bu liste zaten
        # yalnızca kullanıcının yetkili olduğu dokümanlardan oluşur (Aşama 4).
        nos = cited_sources(res) if not res.answer.get("bulunamadi") else []
        if not nos:
            st.caption("Gösterilecek kaynak sayfa yok: cevap bir kaynağa dayandırılamadı.")
            return
        # Doğrulanamayan cevapta bu sayfalar "cevabın kaynağı" değil, modelin dayandığını söylediği yerdir
        failed = res.verification.status == "failed"
        title = "Modelin gösterdiği kaynak (cevap doğrulanamadı)" if failed else "Cevabın kaynağı"
        n = nos[0] if len(nos) == 1 else st.radio(title, nos, key=f"src-{key}",
                                                  format_func=lambda i: source_label(res, i))
        chunk = res.hits[n - 1].chunk
        st.markdown(f"**{title}:** {source_label(res, n)}")
        if failed:
            st.caption("Cevap bu sayfayla doğrulanamadı. Değeri kullanmadan önce sayfayı kendiniz okuyun.")
        for page in chunk["pages"]:    # parça iki sayfaya yayılıyorsa ikisi de gösterilir
            st.image(page_image(BY_ID[chunk["doc_id"]].path, page, chunk["boxes"]), width="stretch")


state = st.session_state.get("results")
if state:
    items = state["items"]
    if len(items) == 1 and items[0][1].verification.status == "clarify":
        render_clarify(items[0][1])
    elif len(items) == 1:
        render_result(items[0][1], "r0")
    else:
        for tab, (i, (label, r)) in zip(st.tabs([lab for lab, _ in items]), enumerate(items)):
            with tab:
                render_result(r, f"r{i}")
