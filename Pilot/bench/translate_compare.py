"""BM25 sorgu çevirisi: model etkisi ve sağlayıcı etkisi ayrı (Adım 2 planı §14, onay 2026-11-05).

Üç kol, her soruda iç içe ve sırası dönerek (aynı dakikada, aynı ağ koşulunda):
    g3_deepinfra   google/gemma-3-12b-it, DeepInfra (bugünkü çeviri modeli ve sağlayıcısı)
    g3_nextbit     google/gemma-3-12b-it, NextBit
    g4_nextbit     google/gemma-4-26b-a4b-it, NextBit, düşünme kapalı
Her kol tek sağlayıcıya sabit (allow_fallbacks false; ZDR kısıtı cloud.py'den). İstem ve ayrıştırma uygulamanınki
(pilot.translate.translate_query); yalnız istemci ölçüm aracında: sağlayıcı sabitleme, düşünme kapatma, çağrı kaydı.
Yeniden deneme yok: süre tek çağrının tamamı (istek → cevabın sonu; çeviri bitmeden BM25 aranamaz). Hata sayılır,
BM25 o soruda çevirisiz aranır (uygulamadaki gibi).

Çıktı:
    data/bench_cache/ceviri_cmp_<kol>_<tur>.json   bench.translate_bm25 biçimi (triple_fusion --bm25-translations)
    data/bench_cache/ceviri_cmp_cagrilar_<tur>.json çağrı kayıtları (süre, token, sağlayıcı, hata)
Kalite (BM25 isabeti) ayrıca triple_fusion + candidate_report ile (bench/run_ceviri_karsilastirma.ps1).

Kullanım (Pilot klasöründe):
    python -m bench.translate_compare --pass t1
    python -m bench.translate_compare --report t1 t2      # eval/bench/b4/asama4_ceviri_karsilastirma_<tarih>.md
"""
import argparse
import json
import logging
import time
from collections import Counter
from typing import Any

from bench.common import KNOWN_SETS, OUT_DIR, load_questions, percentile, prepare

log = logging.getLogger("bench")
ARMS: dict[str, dict[str, Any]] = {
    "g3_deepinfra": {"model": "google/gemma-3-12b-it", "provider": "deepinfra"},
    "g3_nextbit": {"model": "google/gemma-3-12b-it", "provider": "nextbit"},
    "g4_nextbit": {"model": "google/gemma-4-26b-a4b-it", "provider": "nextbit", "reasoning": {"enabled": False}},
}
SETS = [*KNOWN_SETS, "aday_sorular"]
LIMIT = 1.2               # §9.3: çeviri sınırı (aşınca BM25 çevirisiz)


class PinnedChat:
    """CloudChat.complete ile aynı arayüz; tek sağlayıcı, düşünme ayarı, yeniden denemesiz, her çağrı kaydedilir."""

    def __init__(self, arm: str) -> None:
        import requests

        from pilot.cloud import api_key, require_zdr, zdr_index
        self.arm, self.spec = arm, ARMS[arm]
        require_zdr(self.spec["model"])
        strict = zdr_index()[self.spec["model"]]["strict"]
        if self.spec["provider"] not in strict:
            raise ValueError(f"{self.spec['model']}: {self.spec['provider']} ZDR sağlayıcısı değil ({sorted(strict)})")
        self.session = requests.Session()
        self.session.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
        self.calls: list[dict[str, Any]] = []
        self.cost = 0.0

    def complete(self, messages: list[dict[str, str]], max_tokens: int = 300, temperature: float = 0.0,
                 json_mode: bool = False) -> str:
        from pilot.cloud import openrouter_body
        from pilot.config import OPENROUTER_URL
        body: dict[str, Any] = {"model": self.spec["model"], "messages": messages, "max_tokens": max_tokens,
                                "temperature": temperature, "usage": {"include": True},
                                "provider": {"order": [self.spec["provider"]], "allow_fallbacks": False}}
        if json_mode:
            body["response_format"] = {"type": "json_object"}
        if self.spec.get("reasoning"):
            body["reasoning"] = self.spec["reasoning"]
        rec: dict[str, Any] = {"err": ""}
        t0 = time.perf_counter()
        try:
            r = self.session.post(f"{OPENROUTER_URL}/chat/completions", json=openrouter_body(body), timeout=30)
            rec["sn"] = time.perf_counter() - t0
            if r.status_code != 200:
                rec["err"] = f"{r.status_code}: {r.text[:120]}"
                return ""
            d = r.json()
            u = d.get("usage") or {}
            rec.update(provider=d.get("provider"), giris=u.get("prompt_tokens"), cikis=u.get("completion_tokens"),
                       dusunce=((u.get("completion_tokens_details") or {}).get("reasoning_tokens")),
                       maliyet=float(u.get("cost") or 0.0))
            self.cost += rec["maliyet"]
            return d["choices"][0]["message"]["content"] or ""
        except Exception as e:  # noqa: BLE001 — zaman aşımı/bağlantı: kayda geçer
            rec["sn"] = time.perf_counter() - t0
            rec["err"] = repr(e)[:120]
            return ""
        finally:
            self.calls.append(rec)


def run_pass(tag: str, max_usd: float) -> None:
    from bench.providers import CACHE_DIR
    from pilot.query import question_lang
    from pilot.translate import bm25_text, target_languages, translate_query
    chats = {a: PinnedChat(a) for a in ARMS}
    items = [(it, prepare(it["q"])) for it in load_questions(SETS, include_unapproved=True)]
    items = [(it, p) for it, p in items if not p["skip"] and not it.get("expect_clarify")]
    outs = {a: {"questions": {}} for a in ARMS}
    calls: list[dict[str, Any]] = []
    order = list(ARMS)
    for n, (it, p) in enumerate(items, 1):
        src = question_lang(it["q"])
        targets = {"filtered": target_languages(p["doc_ids"]), "unfiltered": target_languages(None)}
        rot = order[n % len(order):] + order[:n % len(order)]          # sıra her soruda döner
        for mode, tg in targets.items():
            for arm in rot:
                c = chats[arm]
                before = len(c.calls)
                try:
                    tr = translate_query(p["search_q"], src, tg, c)
                except (ValueError, json.JSONDecodeError):      # bozuk JSON: çeviri yok (uygulamadaki gibi)
                    tr = {src: p["search_q"]} if src in tg else {}
                    if len(c.calls) > before:
                        c.calls[-1]["err"] = c.calls[-1]["err"] or "json"
                called = len(c.calls) > before
                rec = outs[arm]["questions"].setdefault(it["qid"], {"src": src, "search_q": p["search_q"]})
                rec[mode] = {"targets": tg, "translations": tr, "bm25": bm25_text(tr, p["search_q"]), "called": called,
                             "seconds": c.calls[-1]["sn"] if called else 0.0}
                if called:
                    calls.append({"kol": arm, "qid": it["qid"], "mod": mode, "hedef": tg, **c.calls[-1]})
        spent = sum(c.cost for c in chats.values())
        if spent > max_usd:
            raise SystemExit(f"harcama sınırı aşıldı: {spent:.4f} USD")
        if n % 20 == 0:
            log.info("%d/%d · %.4f USD", n, len(items), spent)
    for arm, o in outs.items():
        o["params"] = {"model": ARMS[arm]["model"], "provider": ARMS[arm]["provider"], "sets": SETS,
                       "include_unapproved": True, "tur": tag, "stats": {"cost_usd": chats[arm].cost}}
        (CACHE_DIR / f"ceviri_cmp_{arm}_{tag}.json").write_text(json.dumps(o, ensure_ascii=False, indent=1),
                                                               encoding="utf-8")
    (CACHE_DIR / f"ceviri_cmp_cagrilar_{tag}.json").write_text(json.dumps(
        {"tur": tag, "bitis": time.strftime("%Y-%m-%d %H:%M:%S"), "cagrilar": calls}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    log.info("yazıldı: tur %s, %d çağrı, %.4f USD", tag, len(calls), sum(c.cost for c in chats.values()))


def report(tags: list[str]) -> str:
    from bench.providers import CACHE_DIR
    f = lambda x: "–" if x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    L = ["# BM25 sorgu çevirisi: model ve sağlayıcı etkisi (yalnız ölçüm aracı)", "",
         "Üç kol her soruda iç içe, sırası dönerek; tek sağlayıcıya sabit, yeniden denemesiz. Süre: çağrının tamamı "
         "(istek → cevabın sonu). Başarı ölçütü p95 ve 1,2 sn sınırını aşma oranı; p50 de veriliyor. "
         "`filtreli` çağrı uygulamanın yolu (hedef diller kapsamdan); `filtresiz` bütün korpus dilleri. "
         "Kalite (BM25 isabeti) aynı çevirilerle ayrı raporda. Plan: [Adım 2 planı §14]"
         "(../adim2/plan_cevap_modeli_2026-11-05.md).", ""]
    runs = {t: json.loads((CACHE_DIR / f"ceviri_cmp_cagrilar_{t}.json").read_text(encoding="utf-8")) for t in tags}
    L += ["## Süre ve çıktı tokeni (filtreli: uygulamanın yolu)", "",
          "| Tur | Kol | çağrı | süre p50 | p95 | > 1,2 sn | çıktı tokeni p50 | p95 | düşünce tokeni | hata | sağlayıcı | maliyet |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t, r in runs.items():
        for arm in ARMS:
            cs = [c for c in r["cagrilar"] if c["kol"] == arm and c["mod"] == "filtered"]
            ok = [c for c in cs if not c["err"]]
            s = [c["sn"] for c in ok]
            o = [c["cikis"] for c in ok if c.get("cikis") is not None]
            over = sum(c["sn"] > LIMIT or bool(c["err"]) for c in cs)
            L.append(f"| {t} ({r['bitis'][11:16]}) | {arm} | {len(cs)} | {f(percentile(s, .5))} | {f(percentile(s, .95))} | "
                     f"{over}/{len(cs)} ({over / max(len(cs), 1):.0%}) | {percentile(o, .5):.0f} | {percentile(o, .95):.0f} | "
                     f"{sum(c.get('dusunce') or 0 for c in ok)} | {len(cs) - len(ok)} | "
                     f"{dict(Counter(c.get('provider') for c in ok))} | {sum(c.get('maliyet') or 0 for c in cs):.4f} |")
    L += ["", "Sınırı aşan: süre > 1,2 sn ya da hata (uygulamada ikisi de çevirisiz BM25 demek).", "",
          "## Bütün çağrılar (filtreli + filtresiz)", "", "| Tur | Kol | çağrı | süre p50 | p95 | > 1,2 sn | hata |",
          "|---|---|---|---|---|---|---|"]
    for t, r in runs.items():
        for arm in ARMS:
            cs = [c for c in r["cagrilar"] if c["kol"] == arm]
            s = [c["sn"] for c in cs if not c["err"]]
            over = sum(c["sn"] > LIMIT or bool(c["err"]) for c in cs)
            L.append(f"| {t} | {arm} | {len(cs)} | {f(percentile(s, .5))} | {f(percentile(s, .95))} | "
                     f"{over / max(len(cs), 1):.0%} | {sum(bool(c['err']) for c in cs)} |")
    t0 = tags[0]
    tr = {a: json.loads((CACHE_DIR / f"ceviri_cmp_{a}_{t0}.json").read_text(encoding="utf-8"))["questions"] for a in ARMS}
    ref = tr["g3_deepinfra"]
    L += ["", f"## Çeviri farkı (tur {t0}, filtreli, g3_deepinfra'ya göre)", "", "| Kol | soru | birebir aynı BM25 sorgusu |",
          "|---|---|---|"]
    for arm in ARMS:
        same = sum(tr[arm][q]["filtered"]["bm25"] == ref[q]["filtered"]["bm25"] for q in ref if q in tr[arm])
        L.append(f"| {arm} | {len(ref)} | {same} |")
    L += ["", "Farklı çeviriler (ilk 12, g3_deepinfra → g4_nextbit):", ""]
    diff = [q for q in ref if tr["g4_nextbit"][q]["filtered"]["bm25"] != ref[q]["filtered"]["bm25"]]
    for q in diff[:12]:
        L.append(f"- `{q}`: {ref[q]['filtered']['bm25'][:110]} → {tr['g4_nextbit'][q]['filtered']['bm25'][:110]}")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pass", dest="tag")
    ap.add_argument("--report", nargs="*")
    ap.add_argument("--max-usd", type=float, default=0.1)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    if a.tag:
        run_pass(a.tag, a.max_usd)
    if a.report:
        from datetime import date
        p = OUT_DIR / "b4" / f"asama4_ceviri_karsilastirma_{date.today().isoformat()}.md"
        p.write_text(report(a.report), encoding="utf-8")
        print(p)


if __name__ == "__main__":
    main()
