"""Qwen3-8B embed: sağlayıcı sabitleme bir seçenek mi? (Adım 2 planı §19, onay 2026-11-05)

Aynı sorgular DeepInfra / Nebius / SiliconFlow'a (ZDR'li) iç içe ve sırası dönerek gönderilir; her çağrı tek sağlayıcıya
sabit (allow_fallbacks false), yeniden deneme yok. Süre çağrının tamamı. Sorgular cevaplı sorulardan sabit örneklem.
Bir sağlayıcı iki ayrı saatte de p95 ≤ 1,5 sn tutarsa sabitleme seçenek olur.

Kullanım (Pilot klasöründe): python -m bench.qwen_provider_probe --tag p1 [--n 30]
    → eval/bench/b4/qwen_saglayici_<tarih>.md (bütün turlar)
"""
import argparse
import json
import random
import time
from datetime import date
from typing import Any

from bench.common import KNOWN_SETS, OUT_DIR, PILOT_DIR, load_questions, percentile, prepare

MODEL = "qwen/qwen3-embedding-8b"
PROVIDERS = ["deepinfra", "nebius", "siliconflow"]
DIR = PILOT_DIR / "data" / "bench_cache" / "qwen_saglayici"


def call(session: Any, text: str, provider: str) -> dict[str, Any]:
    from pilot.cloud import openrouter_body
    from pilot.config import OPENROUTER_URL
    body = openrouter_body({"model": MODEL, "input": [text], "encoding_format": "float",
                            "provider": {"order": [provider], "allow_fallbacks": False}})
    t0 = time.perf_counter()
    try:
        r = session.post(f"{OPENROUTER_URL}/embeddings", json=body, timeout=30)
        sn = time.perf_counter() - t0
        if r.status_code != 200:
            return {"sn": sn, "err": f"{r.status_code}: {r.text[:100]}"}
        d = r.json()
        return {"sn": sn, "err": "", "provider": d.get("provider"), "cost": float((d.get("usage") or {}).get("cost") or 0)}
    except Exception as e:  # noqa: BLE001
        return {"sn": time.perf_counter() - t0, "err": repr(e)[:100]}


def report() -> str:
    f = lambda x: "–" if x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    L = ["# Qwen3-8B embed: sağlayıcıya göre süre (sabitlenmiş, iç içe)", "",
         "Adım 2 planı §19. Her çağrı tek sağlayıcıya sabit, yeniden denemesiz; süre çağrının tamamı. Ölçüt: bir sağlayıcı iki "
         "ayrı saatte de p95 ≤ 1,5 sn.", "", "| Tur | Sağlayıcı | çağrı | p50 | p95 | en uzun | > 1,5 sn | 429 | diğer hata |",
         "|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for prov in PROVIDERS:
            cs = [c for c in d["calls"] if c["saglayici"] == prov]
            s = [c["sn"] for c in cs if not c["err"]]
            L.append(f"| {d['tag']} ({d['start'][11:16]}) | {prov} | {len(cs)} | {f(percentile(s, .5))} | {f(percentile(s, .95))} | "
                     f"{f(max(s) if s else float('nan'))} | {sum(x > 1.5 for x in s)} | "
                     f"{sum(c['err'].startswith('429') for c in cs)} | {sum(bool(c['err']) and not c['err'].startswith('429') for c in cs)} |")
    return "\n".join(L) + "\n"


def main() -> None:
    import requests

    from pilot.cloud import api_key, require_zdr, zdr_index
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()
    require_zdr(MODEL)
    strict = zdr_index()[MODEL]["strict"]
    missing = [p for p in PROVIDERS if p not in strict]
    if missing:
        raise SystemExit(f"ZDR'li değil: {missing} ({sorted(strict)})")
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    qs = [it for it in load_questions([*KNOWN_SETS, "aday_sorular"]) if not it.get("expect_not_found")]
    sample = random.Random(20261105).sample(qs, a.n)
    out = {"tag": a.tag, "start": time.strftime("%Y-%m-%d %H:%M:%S"), "calls": []}
    for i, it in enumerate(sample):
        text = prepare(it["q"])["search_q"]
        for prov in PROVIDERS[i % 3:] + PROVIDERS[:i % 3]:
            out["calls"].append({"qid": it["qid"], "saglayici": prov, **call(s, text, prov)})
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{a.tag}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    path = OUT_DIR / "b4" / f"qwen_saglayici_{date.today().isoformat()}.md"
    path.write_text(report(), encoding="utf-8")
    print(path, f"{sum(c.get('cost') or 0 for c in out['calls']):.5f} USD")


if __name__ == "__main__":
    main()
