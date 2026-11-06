"""Gri akış C ölçümü (API planı §10 adım 6; karar 2026-11-06). Uygulamanın c yolu: pipeline.soru_cevapla(on_event=...),
gerçek arama ve bulut. Olaylar geldikçe zaman damgası alınır (sorunun başından).

Ölçüler: ilk görünen kelime (gizlenmeyen ilk tam kelimenin göründüğü oge_akis), ilk doğrulanmış cümle (ilk
oge_dogrulandi), ✖ kartları (oge_dogrulanamadi), "cevap tamamlanamadı", akışta sızan rakam (0 olmalı: oge_akis'te rakam
görünmez). Soru seti duman testinin tabakalı seçimi (en az 3 "bulunamadı", 3 netleştirme), N = 25.

Kullanım (Pilot klasöründe; arayüz kapalı):  $env:PILOT_ANSWER_MODE = "c"; python -m bench.gri_akis_olcumu
Çıktı: eval/bench/adim2/gri_akis_<tarih>.md ve ham/gri_akis.json
"""
from __future__ import annotations

import json
import re
import time
from collections import Counter
from datetime import date, datetime
from typing import Any

from bench.common import PILOT_DIR, percentile

N = 25
OUT = PILOT_DIR / "eval" / "bench" / "adim2"


def main() -> None:
    from bench import require_mode
    require_mode("c")
    import bench.duman_testi as D
    from pilot import pipeline
    D.N = N
    qs = D.pick()
    pipeline.soru_cevapla("Isınma: dikiş adımı nasıl ayarlanır?")      # ölçülmez
    rows = []
    for i, q in enumerate(qs, 1):
        t0 = time.perf_counter()
        ev: list[dict[str, Any]] = []

        def on_event(e: dict, ev=ev, t0=t0) -> None:
            ev.append({**e, "t": time.perf_counter() - t0})
        r = pipeline.soru_cevapla(q["q"], on_event=on_event)
        akis = [e for e in ev if e["olay"] == "oge_akis"]
        first_word = next((e["t"] for e in akis if re.search(r"[^\W\d_]{2,}", e["metin"])), None)
        first_ok = next((e["t"] for e in ev if e["olay"] == "oge_dogrulandi"), None)
        row = {"qid": q["qid"], "q": q["q"], "durum": r.verification.status, "model": r.llm_called,
               "saglayici": r.answer.get("saglayici"), "ilk_gorunen_kelime": first_word, "ilk_dogrulanmis": first_ok,
               "dogrulanamadi_karti": sum(e["olay"] == "oge_dogrulanamadi" for e in ev),
               "dogrulandi": sum(e["olay"] == "oge_dogrulandi" for e in ev),
               "tamamlanamadi": any(e["olay"] == "cevap_tamamlanamadi" for e in ev),
               "sifirla": sum(e["olay"] == "oge_sifirla" for e in ev),
               "sizan_rakam": sum(bool(re.search(r"\d", e["metin"])) for e in akis),
               "olay_sayisi": len(ev), "maliyet": r.answer.get("maliyet", 0.0), "toplam": r.timings.get("total")}
        rows.append(row)
        print(f"{time.strftime('%H:%M:%S')} {i}/{len(qs)} {q['qid']} {row['durum']} kelime={first_word or float('nan'):.2f} "
              f"doğr={first_ok or float('nan'):.2f} ✖kart={row['dogrulanamadi_karti']}", flush=True)
    out = {"tarih": datetime.now().isoformat(timespec="seconds"), "satirlar": rows,
           "ceviri_maliyet": (pipeline._CLIENTS.get("translate").stats["cost_usd"] if pipeline._CLIENTS.get("translate") else 0.0)}
    (OUT / "ham" / "gri_akis.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    p = OUT / f"gri_akis_{date.today().isoformat()}.md"
    p.write_text(report(out), encoding="utf-8")
    print(p)
    print(p.read_text(encoding="utf-8"))


def report(out: dict[str, Any]) -> str:
    rows = out["satirlar"]
    s_ = lambda x: "–" if x is None or x != x else f"{x:.2f} sn".replace(".", ",")
    fw = [r["ilk_gorunen_kelime"] for r in rows if r["ilk_gorunen_kelime"] is not None]
    fv = [r["ilk_dogrulanmis"] for r in rows if r["ilk_dogrulanmis"] is not None]
    st = Counter(r["durum"] for r in rows)
    cost = sum(r["maliyet"] or 0 for r in rows) + (out.get("ceviri_maliyet") or 0)
    L = ["# Gri akış C ölçümü (c kipi, c150b-J, uygulama yolu)", "",
         f"{out['tarih']}. `pipeline.soru_cevapla(on_event=...)`; süreler sorunun başından, olay geldiği anda. "
         "API planı §10 adım 6.", "",
         "| Ölçü | Değer |", "|---|---|",
         f"| Soru | {len(rows)} ({dict(st)}) |",
         f"| **İlk görünen kelime** p50 / p95 | {s_(percentile(fw, .5))} / {s_(percentile(fw, .95))} (n={len(fw)}) |",
         f"| **İlk doğrulanmış cümle** p50 / p95 | {s_(percentile(fv, .5))} / {s_(percentile(fv, .95))} (n={len(fv)}) |",
         f"| ≤ 3 sn (ilk doğrulanmış cümle) | {sum(x <= 3 for x in fv)}/{len(fv)} |",
         f"| ✖ kartı (\"Değer doğrulanamadı\") | {sum(r['dogrulanamadi_karti'] for r in rows)} öğe, "
         f"{sum(r['dogrulanamadi_karti'] > 0 for r in rows)} soruda |",
         f"| \"Cevap tamamlanamadı\" | {sum(r['tamamlanamadi'] for r in rows)} |",
         f"| Yedeğe geçişte sıfırlama | {sum(r['sifirla'] for r in rows)} |",
         f"| **Akışta sızan rakam** (0 olmalı) | {sum(r['sizan_rakam'] for r in rows)} |",
         f"| Sağlayıcı | {dict(Counter(r['saglayici'] for r in rows if r['saglayici']))} |",
         f"| Maliyet | {cost:.4f} USD |", "",
         "| Soru | Durum | ilk görünen kelime | ilk doğrulanmış | ✓ öğe | ✖ kart |", "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['qid']} | {r['durum']} | {s_(r['ilk_gorunen_kelime'])} | {s_(r['ilk_dogrulanmis'])} | "
                 f"{r['dogrulandi']} | {r['dogrulanamadi_karti']} |")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    main()
