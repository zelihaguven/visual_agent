"""Bulut çağrılarında gecikme kuyruğu: Qwen3-8B sorgu embed'i, çeviri (gemma-3-12b-it), cevap modeli (mistral-small).

Her servis için 30 çağrı; her girdide provider.sort = latency ile ve onsuz çağrı art arda (iki koşul aynı zaman dilimini
görür). Cevap modeli akışlı: ilk token ve toplam süre. Girdiler sabit (data/bench_cache/kuyruk/girdiler.json; Qdrant
gerekmez). Önbellek yok. Gün içinde farklı saatlerde çalıştırılır (bench/run_kuyruk.ps1, Görev Zamanlayıcı).
Harcama, önceki koşular dahil --max-usd'yi geçerse durur.

Kullanım (Pilot klasöründe): python -m bench.tail_probe --label t1
Çıktı: data/bench_cache/kuyruk/<tarih>_<label>.json; özet: python -m bench.tail_probe --summary
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

DIR = Path(__file__).resolve().parent.parent / "data" / "bench_cache" / "kuyruk"
EMBED_MODEL = "qwen/qwen3-embedding-8b"
TRANSLATE_MODEL = "google/gemma-3-12b-it"
ANSWER_MODEL = "mistralai/mistral-small-24b-instruct-2501"


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def spent() -> float:
    return sum(json.loads(f.read_text(encoding="utf-8")).get("cost_usd", 0.0) for f in DIR.glob("2*_*.json"))


def call(session: Any, path: str, body: dict[str, Any], stream: bool = False) -> tuple[float, float | None, float, str]:
    """(süre, ilk token, maliyet, hata). ZDR zorunlu (openrouter_body); sort yalnız provider'a eklenir."""
    from pilot.cloud import openrouter_body
    from pilot.config import OPENROUTER_URL
    t0 = time.perf_counter()
    first, cost = None, 0.0
    try:
        with session.post(f"{OPENROUTER_URL}/{path}", json=openrouter_body(body), stream=stream, timeout=120) as r:
            if r.status_code != 200:
                return time.perf_counter() - t0, None, 0.0, f"{r.status_code}: {r.text[:120]}"
            if not stream:
                cost = float((r.json().get("usage") or {}).get("cost") or 0.0)
            else:
                for line in r.iter_lines(decode_unicode=True):
                    if not line or not line.startswith("data: ") or line == "data: [DONE]":
                        continue
                    d = json.loads(line[6:])
                    cost = float((d.get("usage") or {}).get("cost") or cost)
                    if first is None and (d.get("choices") or [{}])[0].get("delta", {}).get("content"):
                        first = time.perf_counter() - t0
    except Exception as e:                       # zaman aşımı, bağlantı: kayda geçer, ölçüm sürer
        return time.perf_counter() - t0, None, 0.0, repr(e)[:120]
    return time.perf_counter() - t0, first, cost, ""


def run(label: str, n: int, max_usd: float) -> Path:
    import requests

    from pilot.cloud import api_key, require_zdr
    from pilot.prompts import SYSTEM_PROMPT
    from pilot.translate import PROMPT
    for m in (EMBED_MODEL, TRANSLATE_MODEL, ANSWER_MODEL):
        require_zdr(m)
    inputs = json.loads((DIR / "girdiler.json").read_text(encoding="utf-8"))[:n]
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    tmsg = PROMPT.format(src="Turkish", targets="English", codes="en")
    out: dict[str, Any] = {"label": label, "start": datetime.now().isoformat(timespec="seconds"), "rows": [],
                           "cost_usd": 0.0}
    services = {
        "qwen_embed": lambda x: ("embeddings", {"model": EMBED_MODEL, "input": [x["search_q"]], "encoding_format": "float"}, False),
        "ceviri": lambda x: ("chat/completions", {"model": TRANSLATE_MODEL, "max_tokens": 200, "temperature": 0,
                                                  "response_format": {"type": "json_object"}, "usage": {"include": True},
                                                  "messages": [{"role": "system", "content": tmsg},
                                                               {"role": "user", "content": x["search_q"]}]}, False),
        "cevap": lambda x: ("chat/completions", {"model": ANSWER_MODEL, "max_tokens": 300, "temperature": 0, "stream": True,
                                                 "response_format": {"type": "json_object"}, "usage": {"include": True},
                                                 "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                                                              {"role": "user", "content": x["answer_user"]}]}, True),
    }
    prior = spent()
    for name, make in services.items():
        path, body, stream = make(inputs[0])
        call(s, path, body, stream)                       # ısınma (bağlantı)
        for x in inputs:
            for sort in (None, "latency"):
                path, body, stream = make(x)
                if sort:
                    body = {**body, "provider": {"sort": sort}}
                sec, first, cost, err = call(s, path, body, stream)
                out["rows"].append({"servis": name, "sort": sort or "yok", "qid": x["qid"], "sn": sec,
                                    "ilk_token": first, "hata": err})
                out["cost_usd"] += cost
                if prior + out["cost_usd"] > max_usd:
                    out["durdu"] = f"harcama sınırı {max_usd} USD"
                    break
            if out.get("durdu"):
                break
        if out.get("durdu"):
            break
    out["end"] = datetime.now().isoformat(timespec="seconds")
    path = DIR / f"{datetime.now():%Y-%m-%d_%H%M}_{label}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def summary() -> str:
    lines = ["| Koşu | Servis | sort | n | hata | p50 | p90 | p95 | en uzun | ilk token p50 / p95 |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for f in sorted(DIR.glob("2*_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for svc in ("qwen_embed", "ceviri", "cevap"):
            for sort in ("yok", "latency"):
                rs = [r for r in d["rows"] if r["servis"] == svc and r["sort"] == sort]
                ok = [r["sn"] for r in rs if not r["hata"]]
                if not ok:
                    continue
                ft = [r["ilk_token"] for r in rs if r.get("ilk_token")]
                tt = f"{pct(ft, 50):.2f} / {pct(ft, 95):.2f}" if ft else "–"
                lines.append(f"| {d['start'][11:16]} {d['label']} | {svc} | {sort} | {len(rs)} | {len(rs) - len(ok)} | "
                             f"{pct(ok, 50):.2f} | {pct(ok, 90):.2f} | {pct(ok, 95):.2f} | {max(ok):.2f} | {tt} |")
    return "\n".join(lines) + f"\n\nToplam harcama: {spent():.4f} USD\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="t")
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--max-usd", type=float, default=0.3)
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    print(summary() if a.summary else run(a.label, a.n, a.max_usd))


if __name__ == "__main__":
    main()
