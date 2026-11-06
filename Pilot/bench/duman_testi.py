"""Bağlama sonrası duman testi (Adım 2 planı §29.5; karar 2026-11-06). Uygulamanın kendi yolu: pipeline.soru_cevapla,
PILOT_ANSWER_MODE=c (ikili yol + Gemma 4 c150b-J, DeepInfra birincil), gerçek arama (gömülü `manuals`) ve gerçek bulut.

1. 30 soru, onaylı setlerden tabakalı ve tohumlu: en az 3 "bulunamadı", 3 netleştirme (değer farklı), kalanı cevaplı
   (setlerin payına göre; şekil soruları dahil). Ölçüme girmeyen ısınma önce.
2. Yedeğe geçiş: birincil (DeepInfra) yapay olarak kesilir (istemcinin o sağlayıcıya denemesi bağlantı hatası verir;
   ağa çıkılmaz), 3 soru; cevap yedekten (Venice) gelmeli.
Kapılar: doğrulanmış görünen yanlış 0; ✓ / yanlış ret hat ölçümünden (nihai_hat_k8) belirgin sapmamalı (aynı sorular
yan yana); uçtan uca ilk doğrulanmış cümle p50 ≤ 3 sn (p95 de raporlanır); cevap veren her çağrıda sağlayıcı DeepInfra;
kural çıkışlarında bulut çağrısı yok.

Kullanım (Pilot klasöründe; arayüz kapalı):  python -m bench.duman_testi
Çıktı: eval/bench/adim2/duman_testi_<tarih>.md ve ham/duman_testi.json
"""
from __future__ import annotations

import json
import random
import time
from collections import Counter
from datetime import date, datetime
from typing import Any

from bench.common import PILOT_DIR, load_questions, percentile, value_in, variants_in

SEED = 20261106
SETS = ["questions", "questions_ek", "sekil_sorular", "aday_sorular"]
N, N_NF, N_CL = 30, 3, 3
OUT = PILOT_DIR / "eval" / "bench" / "adim2"
CLASSES = json.loads((PILOT_DIR / "eval" / "netlestirme_siniflari.json").read_text(encoding="utf-8"))


def pick() -> list[dict[str, Any]]:
    qs = [q for q in load_questions(SETS, include_unapproved=True)]
    rng = random.Random(SEED)
    nf = [q for q in qs if q.get("expect_not_found")]
    cl = [q for q in qs if q.get("expect_clarify") and CLASSES.get(q["qid"], {}).get("sinif") == "deger_farkli"]
    an = [q for q in qs if not q.get("expect_not_found") and not q.get("expect_clarify")]
    out = rng.sample(nf, N_NF) + rng.sample(cl, N_CL)
    by_set: dict[str, list] = {}
    for q in an:
        by_set.setdefault(q["set"], []).append(q)
    rest = N - len(out)
    quota = {s: max(1, round(rest * len(v) / len(an))) for s, v in by_set.items()}
    while sum(quota.values()) > rest:
        quota[max(quota, key=quota.get)] -= 1
    for s, v in by_set.items():
        out += rng.sample(v, quota[s])
    return out


def judge(q: dict[str, Any], r: Any) -> dict[str, Any]:
    a = r.answer
    st = r.verification.status
    text = " ".join(o.get("metin", "") for o in a.get("ogeler") or []) or (a.get("cevap") or "")
    row = {"qid": q["qid"], "q": q["q"], "beklenen": "bulunamadı" if q.get("expect_not_found") else
           ("netleştirme" if q.get("expect_clarify") else "cevap"), "durum": st, "model": r.llm_called,
           "saglayici": a.get("saglayici"), "denemeler": a.get("denemeler"), "maliyet": a.get("maliyet", 0.0),
           "u2u": r.timings.get("uctan_uca_ilk_dogrulanmis"), "ilk_dogr": r.timings.get("ilk_dogrulanmis_cumle"),
           "istek_oncesi": r.timings.get("istek_oncesi"), "toplam": r.timings.get("total"),
           "servis_yok": bool(a.get("servis_yok")), "sorunlar": r.verification.problems[:3], "cevap": text[:300]}
    if q.get("expect_not_found"):
        row["dogru"] = st == "not_found"
        row["dogrulanmis_gorunen_yanlis"] = st in ("verified", "partial")
    elif q.get("expect_clarify"):
        row["dogru"] = st == "clarify"
    else:
        row["yanlis_ret"] = st == "not_found"
        if q.get("varyantlar"):
            row["deger"] = variants_in(q["varyantlar"], [o.get("metin", "") for o in a.get("ogeler") or []]) if text else None
        elif q.get("expect_in_answer") and st in ("verified", "partial"):
            row["deger"] = all(value_in(v, text) for v in q["expect_in_answer"])
    return row


def main() -> None:
    from pilot import config, pipeline
    config.ANSWER_MODE = "c"
    qs = pick()
    log = lambda m: print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)
    log(f"{len(qs)} soru: {Counter('bulunamadı' if q.get('expect_not_found') else 'netleştirme' if q.get('expect_clarify') else q['set'] for q in qs)}")
    # ısınma (ölçülmez): bge-m3, Qdrant, parça dosyası, istemciler; tek soru gerçek yoldan
    pipeline.soru_cevapla("Isınma: dikiş adımı nasıl ayarlanır?")
    warm_cost = 0.0
    rows = []
    for i, q in enumerate(qs, 1):
        r = pipeline.soru_cevapla(q["q"])
        row = judge(q, r)
        rows.append(row)
        log(f"{i}/{len(qs)} {q['qid']} {row['durum']} model={row['model']} sağlayıcı={row['saglayici']} "
            f"u2u={row['u2u'] or float('nan'):.2f}")
    # yedeğe geçiş: birincil yapay olarak kesik (bağlantı hatası, ağa çıkmadan)
    client = pipeline._answer_client()
    real_one = client._one

    def cut(messages, provider):
        if provider == config.ANSWER_PROVIDERS[0]:
            return {"provider": provider, "content": "", "zaman": [], "err": "yapay kesinti (duman testi)",
                    "kacak": False, "sn": 0.0}
        return real_one(messages, provider)
    client._one = cut
    fb = []
    for q in [q for q in qs if not q.get("expect_not_found") and not q.get("expect_clarify")][:3]:
        r = pipeline.soru_cevapla(q["q"])
        row = judge(q, r)
        fb.append(row)
        log(f"yedek {q['qid']} {row['durum']} sağlayıcı={row['saglayici']} denemeler={row['denemeler']}")
    client._one = real_one
    out = {"tarih": datetime.now().isoformat(timespec="seconds"), "ayarlar": {
        "mod": config.ANSWER_MODE, "model": config.ANSWER_MODEL, "sema": config.ANSWER_SCHEMA_VARIANT,
        "saglayicilar": config.ANSWER_PROVIDERS, "max_tokens": config.ANSWER_MAX_TOKENS, "kaynak": config.ANSWER_TOP_K,
        "ilk_token_s": config.ANSWER_FIRST_TOKEN_S, "bekci": config.STREAM_GUARD_N,
        "ceviri": [config.TRANSLATE_MODEL, config.TRANSLATE_PROVIDERS, config.TRANSLATE_LIMIT_S]},
        "satirlar": rows, "yedek": fb,
        "ceviri_maliyet": ((pipeline._CLIENTS.get("translate") or None) and pipeline._CLIENTS["translate"].stats["cost_usd"]) or 0.0}
    (OUT / "ham").mkdir(parents=True, exist_ok=True)
    (OUT / "ham" / "duman_testi.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    md = report(out)
    p = OUT / f"duman_testi_{date.today().isoformat()}.md"
    p.write_text(md, encoding="utf-8")
    print(p)
    print(md)


def report(out: dict[str, Any]) -> str:
    rows, fb = out["satirlar"], out["yedek"]
    s_ = lambda x: "–" if x is None or x != x else f"{x:.2f} sn".replace(".", ",")
    hat = json.loads((OUT / "ham" / "nihai_hat_k8_gemma4.json").read_text(encoding="utf-8"))["rows"]
    an = [r for r in rows if r["beklenen"] == "cevap"]
    st = Counter(r["durum"] for r in an)
    nf = [r for r in rows if r["beklenen"] == "bulunamadı"]
    cl = [r for r in rows if r["beklenen"] == "netleştirme"]
    u2u = [r["u2u"] for r in rows if r["u2u"] is not None]
    dv = [r["deger"] for r in an if r.get("deger") is not None]
    model_rows = [r for r in rows if r["saglayici"]]
    provs = Counter(r["saglayici"] for r in model_rows)
    rule_cloud = [r for r in rows if not r["model"] and r["saglayici"]]
    bad = sum(bool(r.get("dogrulanmis_gorunen_yanlis")) for r in rows)
    hst = Counter((hat.get(r["qid"]) or {}).get("durum") for r in an)
    p50, p95 = percentile(u2u, .5), percentile(u2u, .95)
    cost = sum(r["maliyet"] or 0 for r in rows + fb) + (out.get("ceviri_maliyet") or 0)
    gate = lambda ok: "✅" if ok else "❌"
    L = ["# Bağlama sonrası duman testi (c kipi)", "",
         f"{out['tarih']}. Uygulamanın yolu (`pipeline.soru_cevapla`, PILOT_ANSWER_MODE=c), gerçek arama ve bulut. "
         f"Ayarlar: {out['ayarlar']}. Plan §29.5.", "",
         "## Kapılar", "", "| Kapı | Sonuç | |", "|---|---|---|",
         f"| Doğrulanmış görünen yanlış = 0 | {bad} | {gate(bad == 0)} |",
         f"| Uçtan uca ilk doğrulanmış cümle p50 ≤ 3 sn | p50 {s_(p50)} · p95 {s_(p95)} (n={len(u2u)}) | {gate(p50 == p50 and p50 <= 3)} |",
         f"| Cevap veren çağrılarda sağlayıcı DeepInfra | {dict(provs)} | {gate(set(provs) <= {'deepinfra'})} |",
         f"| Kural çıkışlarında bulut çağrısı yok | {len(rule_cloud)} | {gate(not rule_cloud)} |",
         f"| Yedeğe geçiş (birincil yapay kesik → Venice) | {[r['saglayici'] for r in fb]} | {gate(fb and all(r['saglayici'] == 'venice' for r in fb))} |",
         f"| ✓ / yanlış ret, hat ölçümüne göre (aynı {len(an)} soru) | duman ✓ {st['verified']} ⚠ {st['partial']} ✖ {st['failed']} "
         f"ret {st['not_found']} · hat k8 ✓ {hst['verified']} ⚠ {hst['partial']} ✖ {hst['failed']} ret {hst['not_found']} | bilgi |",
         "", f"Beklenen değer (cevaplı, doğrulanmış): {sum(dv)}/{len(dv)} · doğru \"bulunamadı\": "
         f"{sum(r['dogru'] for r in nf)}/{len(nf)} · netleştirme (değer farklı): {sum(r['dogru'] for r in cl)}/{len(cl)} · "
         f"servis yok: {sum(r['servis_yok'] for r in rows)} · maliyet: {cost:.4f} USD", "",
         "## Soru soru", "", "| Soru | Beklenen | Durum | hat k8 durumu | değer | sağlayıcı | u2u | sorun |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        h = (hat.get(r["qid"]) or {})
        L.append(f"| {r['qid']} | {r['beklenen']} | {r['durum']} | {h.get('durum', '–')} | "
                 f"{'' if r.get('deger') is None else ('✓' if r['deger'] else '✗')} | {r['saglayici'] or 'kural'} | {s_(r['u2u'])} | "
                 f"{'; '.join(r['sorunlar'])[:120]} |")
    L += ["", "## Yedeğe geçiş", "", "| Soru | Durum | Sağlayıcı | Denemeler |", "|---|---|---|---|"]
    for r in fb:
        L.append(f"| {r['qid']} | {r['durum']} | {r['saglayici']} | {[(d['provider'], d['err'][:40]) for d in r['denemeler'] or []]} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
