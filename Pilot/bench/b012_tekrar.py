"""B012 (niteleyici uyuşmazlığı) tekrar ölçümü (karar 2026-11-06, §23): aynı soru N kez, uygulama c yolu (yeni hat,
8 kaynak, DeepInfra), şema c150b-JS ve c150b-JSN (niteleyici kuralı). Doğrulanmış görünen yanlış = ✓/⚠ cevap.
Kullanım:  $env:PILOT_ANSWER_MODE = "c"; python -m bench.b012_tekrar [şema ...]   (varsayılan c150bJS c150bJSN)"""
import json
import sys
import time

from bench.common import PILOT_DIR, load_questions

N = 10
OUT = PILOT_DIR / "eval" / "bench" / "adim2"


def main() -> None:
    from collections import Counter

    from bench import require_mode
    require_mode("c")
    from pilot import config, pipeline
    q = next(x for x in load_questions(["aday_sorular_ek"], include_unapproved=True) if x["id"] == "B012")
    out = {"soru": q["q"], "tekrar": N, "sonuc": {}}
    variants = sys.argv[1:] or ["c150bJS", "c150bJSN"]
    for variant in variants:
        config.ANSWER_SCHEMA_VARIANT = variant
        pipeline._CLIENTS.pop("answer", None)
        pipeline._CLIENTS.pop("prompt", None)
        rows = []
        for i in range(N):
            r = pipeline.soru_cevapla(q["q"])
            rows.append({"durum": r.verification.status, "cevap": (r.answer.get("cevap") or "")[:160],
                         "maliyet": r.answer.get("maliyet", 0.0)})
            print(f"{time.strftime('%H:%M:%S')} {variant} {i + 1}/{N} {r.verification.status}", flush=True)
        c = Counter(x["durum"] for x in rows)
        out["sonuc"][variant] = {"dagilim": dict(c), "dogrulanmis_gorunen_yanlis": c["verified"] + c["partial"],
                                 "satirlar": rows, "maliyet": sum(x["maliyet"] or 0 for x in rows)}
        print(variant, dict(c), flush=True)
    (OUT / "ham" / ("b012_tekrar.json" if not sys.argv[1:] else f"b012_tekrar_{'_'.join(variants)}.json")).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
