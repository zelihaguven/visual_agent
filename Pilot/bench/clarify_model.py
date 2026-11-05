"""Netleştirme, MODELLE (Gemma 4): ürün belli olmayan sorularda netleştirme soruluyor mu, seçenekler doğru mu
(Adım 2 planı §11, onay 2026-11-05). Önceki ölçüm (bench/doc_rules_diff.py) modeli çağırmadan yapılmıştı.

Durumlar (arama uygulamanın varsayılan yolu, canlı; cevap modeli Gemma 4, DeepInfra, düşünme kapalı, aynı istem):
    a  ilke dışı kurallardan BRAND_ALIASES açık (taban)
    b  kurallar kapalı (varsayılan)
    c  b + clarify_options seçenekleri bulunan kaynakların doküman/ürün adıyla da eşleştirir (yalnız ölçüm aracında)
    d  c, netleştirme beklenMEYEN sorularda (cevaplı + "bulunamadı"): gereksiz netleştirme
Metrikler: netleştirme soruldu mu; seçenekler doğru mu (expect_docs; doc_rules_diff.options_verdict); model sordu ama
gösterilmedi (atlanan_netlestirme); gereksiz netleştirme (d). Metin seçenekleri doküman/ürün adına harf-rakam eşleşmesiyle
dokümana bağlanır.

Kullanım (Pilot klasöründe, Qdrant sunucusu açık): python -m bench.clarify_model [--max-usd 0.15]
    → eval/bench/adim2/netlestirme_modelle_<tarih>.md (+ .json)
"""
import argparse
import json
import re
import time
from collections import Counter
from datetime import date
from typing import Any

from bench.common import KNOWN_SETS, load_questions

STATES = {"a": "BRAND_ALIASES açık (taban)", "b": "kurallar kapalı", "c": "kapalı + seçenek ürün/doküman adıyla",
          "d": "c, netleştirme beklenmeyen sorular"}


def _key(s: str) -> str:
    return re.sub(r"[^0-9a-zçğıöşü]", "", s.casefold())


def option_docs(res: Any, hits: list[Any]) -> list[str]:
    """Netleştirmedeki seçeneklerin dokümanları: doküman düğmeleri + ürün/doküman adına eşlenen metin seçenekleri."""
    docs = [o["doc_id"] for o in res.answer.get("secenekler") or [] if "doc_id" in o]
    names = {h.chunk["doc_id"]: (h.chunk["doc_id"], h.chunk.get("product") or "") for h in hits}
    for o in res.answer.get("secenekler") or []:
        k = _key(o.get("ek") or o.get("etiket") or "") if "doc_id" not in o else ""
        if len(k) < 2:
            continue
        for d, (doc, prod) in names.items():
            if k in _key(doc) or k in _key(prod) or (len(_key(prod)) > 2 and _key(prod) in k):
                docs.append(d)
    return list(dict.fromkeys(docs))


def main() -> None:
    from bench.answer_models import CloudModel, parse_answer, questions
    from bench.doc_rules_diff import VERDICTS, options_verdict
    from pilot import config, pipeline
    from pilot.prompts import SYSTEM_PROMPT

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-usd", type=float, default=0.15)
    a = ap.parse_args()
    m = CloudModel("gemma4")
    st: dict[str, Any] = {"cost": 0.0}
    orig_search, orig_co = pipeline.search, pipeline.clarify_options

    def search(*args: Any, **kw: Any) -> list[Any]:
        st["hits"] = orig_search(*args, **kw)
        return st["hits"]

    def co_names(options: list, sources: dict[int, str]) -> list[str]:
        names = " ".join(f'{h.chunk["doc_id"]} {h.chunk.get("product") or ""}' for h in st.get("hits") or [])
        return orig_co(options, {**sources, 0: names})

    def chat(user: str) -> tuple[dict[str, Any], dict[str, float]]:
        if st["cost"] > a.max_usd:
            raise SystemExit(f"bütçe sınırı {a.max_usd} USD")
        rec = m.stream([{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}])
        st["cost"] += m.cost(rec)
        st["calls"] = st.get("calls", 0) + 1
        ans, status, _ = parse_answer(rec.get("content", ""), rec.get("finish"))
        if ans is None:
            raise json.JSONDecodeError(status, rec.get("content", "")[:50], 0)
        return ans, {"llm_seconds": rec.get("total") or 0.0}

    pipeline.search, pipeline.chat_json = search, chat
    clar = [q for q in load_questions([*KNOWN_SETS, "aday_sorular"], include_unapproved=True) if q.get("expect_clarify")]
    plan = [(s, q) for s in "abc" for q in clar] + [("d", q) for q in questions()]
    rows: list[dict[str, Any]] = []
    for i, (s, q) in enumerate(plan, 1):
        config.DOC_SPECIFIC_RULES = frozenset({"brand_aliases"} if s == "a" else ())
        pipeline.clarify_options = co_names if s in "cd" else orig_co
        st["hits"] = []
        res = pipeline.soru_cevapla(q["q"])
        asked = res.verification.status == "clarify"
        opts = option_docs(res, st["hits"]) if asked else []
        rows.append({"durum": s, "qid": q["qid"], "beklenen_netlestirme": bool(q.get("expect_clarify")),
                     "soruldu": asked, "model_cagrildi": res.llm_called, "secenekler": opts,
                     "secenek_etiketleri": [o.get("etiket") for o in res.answer.get("secenekler") or []],
                     "degerlendirme": options_verdict(opts, q.get("expect_docs") or []) if asked else None,
                     "atlanan": res.answer.get("atlanan_netlestirme"), "soru": res.answer.get("netlestirme_sorusu"),
                     "beklenen_dokumanlar": q.get("expect_docs") or []})
        if i % 25 == 0:
            print(f"{time.strftime('%H:%M:%S')} {i}/{len(plan)} · {st['cost']:.4f} USD", flush=True)
    pipeline.search, pipeline.clarify_options = orig_search, orig_co

    L = [f"# Netleştirme, modelle (Gemma 4, DeepInfra) — {date.today().isoformat()}", "",
         "Adım 2 planı §11. Arama uygulamanın varsayılan yolu (canlı); aynı istem; model çağrısı yalnız kural katmanından "
         f"geçen sorularda. {st.get('calls', 0)} model çağrısı, {st['cost']:.4f} USD. Araç: `python -m bench.clarify_model`.", "",
         "## Netleştirme beklenen 18 soru", "",
         "| Durum | soruldu | " + " | ".join(VERDICTS.values()) + " | model sordu ama gösterilmedi |",
         "|---|---|" + "---|" * len(VERDICTS) + "---|"]
    for s in "abc":
        R = [r for r in rows if r["durum"] == s]
        v = Counter(r["degerlendirme"] for r in R if r["soruldu"])
        L.append(f"| ({s}) {STATES[s]} | {sum(r['soruldu'] for r in R)}/{len(R)} | "
                 + " | ".join(str(v[k]) for k in VERDICTS) + f" | {sum(bool(r['atlanan']) for r in R)} |")
    D = [r for r in rows if r["durum"] == "d"]
    L += ["", "## (d) Netleştirme beklenmeyen sorular", "",
          f"Gereksiz netleştirme: **{sum(r['soruldu'] for r in D)}/{len(D)}**; model sordu ama gösterilmedi: "
          f"{sum(bool(r['atlanan']) for r in D)}.", "", "| Soru | netleştirme sorusu | seçenekler |", "|---|---|---|"]
    L += [f"| {r['qid']} | {(r['soru'] or '')[:90]} | {', '.join(x for x in r['secenek_etiketleri'] if x)[:90]} |"
          for r in D if r["soruldu"]]
    L += ["", "## Soru başına (18 soru × a/b/c)", "", "| Soru | beklenen | Durum | soruldu | seçenekler | değerlendirme | atlanan |",
          "|---|---|---|---|---|---|---|"]
    for r in rows:
        if r["durum"] != "d":
            L.append(f"| {r['qid']} | {', '.join(r['beklenen_dokumanlar'])} | {r['durum']} | {'evet' if r['soruldu'] else 'hayır'} | "
                     f"{', '.join(r['secenekler']) or '–'} | {VERDICTS.get(r['degerlendirme'], '–')} | {(r['atlanan'] or '')[:60]} |")
    from bench.common import OUT_DIR
    base = OUT_DIR / "adim2" / f"netlestirme_modelle_{date.today().isoformat()}"
    base.with_suffix(".md").write_text("\n".join(L) + "\n", encoding="utf-8")
    base.with_suffix(".json").write_text(json.dumps({"rows": rows, "cost_usd": st["cost"], "calls": st.get("calls", 0)},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    print(base.with_suffix(".md"), f"{st['cost']:.4f} USD")


if __name__ == "__main__":
    main()
