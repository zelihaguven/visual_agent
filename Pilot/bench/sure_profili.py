"""Gün içi süre profili (plan §33; onay 2026-11-06). Bir ölçüm = sabit 10 soru, uygulamanın c yolu
(pipeline.soru_cevapla(on_event=...), varsayılan şema, DeepInfra birincil). Her ölçüm ham/sure_profili.jsonl'e satır
satır eklenir; rapor bütün ölçümlerden saat dilimine göre üretilir.

Soru seti: duman testinin soru havuzundan, model çağıran cevaplı sorular (bulunamadı ve netleştirme beklenenler hariç),
sabit tohumla 10 soru. Her soruda: ölçüm saati, ilk görünen kelime ve ilk doğrulanmış cümle (uçtan uca, olay anında),
istek öncesi (arama ve kurallar), arama, çeviri, modelin ilk token süresi, sağlayıcı, maliyet.

Kullanım (Pilot klasöründe; arayüz kapalı, Qdrant gömülü modda tek süreç):
  $env:PILOT_ANSWER_MODE = "c"; python -m bench.sure_profili            # bir ölçüm
  $env:PILOT_ANSWER_MODE = "c"; python -m bench.sure_profili --rapor    # rapor (model çağrısı yok)
Döngü: bench/sure_profili.ps1 (elle başlatılır; zamanlanmış görev yok).
"""
from __future__ import annotations

import argparse
import json
import random
import re
import time
from collections import defaultdict
from datetime import datetime
from typing import Any

from bench.common import PILOT_DIR, load_questions, percentile

N = 10
SEED = 20261106
OUT = PILOT_DIR / "eval" / "bench" / "adim2"
RAW = OUT / "ham" / "sure_profili.jsonl"
SLOTS = [(9, 11), (11, 13), (13, 15), (15, 17), (17, 24)]


def pick() -> list[dict[str, Any]]:
    import bench.duman_testi as D
    qs = [q for q in load_questions(D.SETS, include_unapproved=True)
          if not q.get("expect_not_found") and not q.get("expect_clarify")]
    return random.Random(SEED).sample(qs, N)


def measure() -> list[dict[str, Any]]:
    from pilot import pipeline
    from pilot.retrieve import last_translation
    pipeline.soru_cevapla("Isınma: dikiş adımı nasıl ayarlanır?")      # ölçülmez
    stamp = datetime.now().isoformat(timespec="seconds")
    rows = []
    for q in pick():
        t0 = time.perf_counter()
        ev: list[dict[str, Any]] = []

        def on_event(e: dict, ev=ev, t0=t0) -> None:
            ev.append({"olay": e.get("olay"), "metin": e.get("metin", ""), "t": time.perf_counter() - t0})
        r = pipeline.soru_cevapla(q["q"], on_event=on_event)
        akis = [e for e in ev if e["olay"] == "oge_akis"]
        tm = r.timings
        row = {"olcum": stamp, "saat": datetime.now().isoformat(timespec="seconds"), "qid": q["qid"],
               "durum": r.verification.status, "model": r.llm_called, "saglayici": r.answer.get("saglayici"),
               "ilk_gorunen_kelime": next((e["t"] for e in akis if re.search(r"[^\W\d_]{2,}", e["metin"])), None),
               "ilk_dogrulanmis": next((e["t"] for e in ev if e["olay"] == "oge_dogrulandi"), None),
               "istek_oncesi": tm.get("istek_oncesi"), "arama": tm.get("search"),
               "ceviri": last_translation.get("sn"), "ceviri_sinir_asildi": last_translation.get("sinir_asildi"),
               "model_ilk_token": tm.get("llm_first_token"), "toplam": tm.get("total"),
               "maliyet": r.answer.get("maliyet", 0.0)}
        rows.append(row)
        print(f"{row['saat']} {q['qid']} {row['durum']} kelime={row['ilk_gorunen_kelime'] or float('nan'):.2f} "
              f"doğr={row['ilk_dogrulanmis'] or float('nan'):.2f} {row['saglayici']}", flush=True)
    tr = pipeline._CLIENTS.get("translate")
    RAW.parent.mkdir(parents=True, exist_ok=True)
    with RAW.open("a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.write(json.dumps({"olcum": stamp, "ceviri_maliyet": tr.stats["cost_usd"] if tr else 0.0}, ensure_ascii=False) + "\n")
    return rows


def slot(iso: str) -> str:
    h = datetime.fromisoformat(iso).hour
    a, b = next(((a, b) for a, b in SLOTS if a <= h < b), (0, 9))
    return f"{a:02d}–{b:02d}"


def report() -> str:
    lines = [json.loads(x) for x in RAW.read_text(encoding="utf-8").splitlines() if x.strip()] if RAW.exists() else []
    rows = [x for x in lines if "qid" in x]
    cost = sum(x.get("maliyet") or 0 for x in rows) + sum(x.get("ceviri_maliyet") or 0 for x in lines if "qid" not in x)
    s_ = lambda v: "–" if v is None or v != v else f"{v:.2f}".replace(".", ",")
    by: dict[str, list] = defaultdict(list)
    for x in rows:
        by[slot(x["olcum"])].append(x)
    L = ["# Gün içi süre profili (plan §33)", "",
         f"{len({x['olcum'] for x in rows})} ölçüm, {len({x['olcum'][:10] for x in rows})} gün, {len(rows)} soru. "
         f"Uygulamanın c yolu, sabit 10 soru. Süreler sn, sorunun başından. Toplam maliyet {cost:.4f} USD.", "",
         "| Saat dilimi | Ölçüm | Soru | ilk görünen kelime p50 / p95 | ilk doğrulanmış p50 / p95 | ≤ 3 sn | "
         "istek öncesi p50 | arama p50 | çeviri p50 / p95 | model ilk token p50 / p95 | sağlayıcı |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for k in sorted(by):
        R = by[k]
        g = lambda f: [x[f] for x in R if x.get(f) is not None]
        fv = g("ilk_dogrulanmis")
        prov: dict[str, int] = defaultdict(int)
        for x in R:
            if x.get("saglayici"):
                prov[x["saglayici"]] += 1
        L.append(f"| {k} | {len({x['olcum'] for x in R})} | {len(R)} | {s_(percentile(g('ilk_gorunen_kelime'), .5))} / "
                 f"{s_(percentile(g('ilk_gorunen_kelime'), .95))} | {s_(percentile(fv, .5))} / {s_(percentile(fv, .95))} | "
                 f"{sum(v <= 3 for v in fv)}/{len(fv)} | {s_(percentile(g('istek_oncesi'), .5))} | {s_(percentile(g('arama'), .5))} | "
                 f"{s_(percentile(g('ceviri'), .5))} / {s_(percentile(g('ceviri'), .95))} | "
                 f"{s_(percentile(g('model_ilk_token'), .5))} / {s_(percentile(g('model_ilk_token'), .95))} | {dict(prov)} |")
    L += ["", "| Ölçüm | Soru | ilk doğrulanmış p50 / p95 | model ilk token p95 | çeviri sınırı aşıldı |", "|---|---|---|---|---|"]
    per: dict[str, list] = defaultdict(list)
    for x in rows:
        per[x["olcum"]].append(x)
    for k in sorted(per):
        R = per[k]
        fv = [x["ilk_dogrulanmis"] for x in R if x.get("ilk_dogrulanmis") is not None]
        ft = [x["model_ilk_token"] for x in R if x.get("model_ilk_token") is not None]
        L.append(f"| {k} | {len(R)} | {s_(percentile(fv, .5))} / {s_(percentile(fv, .95))} | {s_(percentile(ft, .95))} | "
                 f"{sum(bool(x.get('ceviri_sinir_asildi')) for x in R)} |")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapor", action="store_true")
    a = ap.parse_args()
    from bench import require_mode
    require_mode("c")
    if not a.rapor:
        measure()
    p = OUT / "sure_profili.md"
    p.write_text(report(), encoding="utf-8")
    print(p)


if __name__ == "__main__":
    main()
