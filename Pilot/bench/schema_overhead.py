"""Şemaya zorlamanın (response_format json_schema) ilk istekteki ek süresi, sağlayıcı bazında (Adım 2 planı §15.0, §20).

Her yapılandırmada aynı sorular, şemalı ve şemasız istek iç içe ve sırası dönerek; aynı istem (şema C), aynı sağlayıcı,
düşünme kapalı. Yalnız ilk token ölçülür; çıktı 60 tokenle sınırlı (maliyet düşük). Kullanıcı mesajı uygulamanınki
(pipeline'dan; arama önbellekten).

Kullanım (Pilot klasöründe): python -m bench.schema_overhead --tag s1 [--n 10] [--models gemma4 ...]
    → eval/bench/adim2/sema_ek_suresi_<tarih>.md (bütün turlar)
"""
import argparse
import json
import random
import time
from datetime import date
from typing import Any

from bench.common import OUT_DIR, PILOT_DIR, percentile, sse_events

DIR = PILOT_DIR / "data" / "bench_cache" / "sema_ek_suresi"
CONFIGS = ["gemma4", "qwen36", "gpt54mini", "mistral2603", "gemma4_nextbit", "gemma4_parasail", "gemma4_venice", "gemma4_31b"]


class _Got(Exception):
    pass


def user_messages(n: int) -> list[tuple[str, str]]:
    from bench import answer_models as am
    from pilot import pipeline
    am.install_search_cache(frozen=True)
    got: dict[str, str] = {}

    def capture(user: str) -> Any:
        got["u"] = user
        raise _Got

    pipeline.chat_json = capture
    pool = [q for q in am.questions() if not q.get("expect_not_found")]
    out = []
    for q in random.Random(20261105).sample(pool, len(pool)):
        try:
            pipeline.soru_cevapla(q["q"])
        except _Got:
            out.append((q["qid"], got["u"]))
        if len(out) == n:
            break
    return out


def first_token(m: Any, messages: list[dict[str, str]], schema: bool) -> dict[str, Any]:
    from pilot.config import OPENROUTER_URL
    body = m.body(messages)
    body["max_tokens"] = 60
    if not schema:
        body.pop("response_format", None)
    t0, first, err, cost, prov = time.perf_counter(), None, "", 0.0, None
    try:
        with m.session.post(f"{OPENROUTER_URL}/chat/completions", json=body, stream=True, timeout=(10, 60)) as r:
            if r.status_code != 200:
                err = f"{r.status_code}: {r.text[:100]}"
            else:
                for d in sse_events(r):
                    prov = d.get("provider") or prov
                    if d.get("usage"):
                        cost = float(d["usage"].get("cost") or 0.0)
                    if first is None and ((d.get("choices") or [{}])[0].get("delta") or {}).get("content"):
                        first = time.perf_counter() - t0
    except Exception as e:  # noqa: BLE001
        err = repr(e)[:100]
    return {"ilk_token": first, "err": err, "maliyet": cost, "provider": prov}


def report() -> str:
    f = lambda x: "–" if x is None or x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    L = ["# Şemaya zorlamanın ilk istekteki ek süresi (sağlayıcı bazında)", "",
         "Aynı sorular, şemalı (json_schema, şema C) ve şemasız istek iç içe; ilk token. Adım 2 planı §15.0/§20.", "",
         "| Tur | Yapılandırma | Sağlayıcı | n | şemalı p50 | p95 | şemasız p50 | p95 | fark p50 (eşli) | hata |",
         "|---|---|---|---|---|---|---|---|---|---|"]
    for p in sorted(DIR.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        for k in CONFIGS:
            rs = [r for r in d["rows"] if r["model"] == k]
            if not rs:
                continue
            a = [r["semali"]["ilk_token"] for r in rs if r["semali"]["ilk_token"]]
            b = [r["semasiz"]["ilk_token"] for r in rs if r["semasiz"]["ilk_token"]]
            diff = [r["semali"]["ilk_token"] - r["semasiz"]["ilk_token"] for r in rs
                    if r["semali"]["ilk_token"] and r["semasiz"]["ilk_token"]]
            errs = sum(bool(r["semali"]["err"]) + bool(r["semasiz"]["err"]) for r in rs)
            L.append(f"| {d['tag']} ({d['start'][11:16]}) | {k} | {rs[0]['saglayici']} | {len(rs)} | {f(percentile(a, .5))} | "
                     f"{f(percentile(a, .95))} | {f(percentile(b, .5))} | {f(percentile(b, .95))} | "
                     f"{f(percentile(diff, .5)) if diff else '–'} | {errs} |")
    return "\n".join(L) + "\n"


def main() -> None:
    from bench import require_mode
    require_mode("bugun")
    from bench import answer_models as am
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--models", nargs="*", default=CONFIGS)
    a = ap.parse_args()
    am.SCHEMA = "c"
    prompt = am.schema_and_prompt()[1]
    users = user_messages(a.n)
    out: dict[str, Any] = {"tag": a.tag, "start": time.strftime("%Y-%m-%d %H:%M:%S"), "rows": []}
    models = {k: am.CloudModel(k) for k in a.models}
    for i, (qid, user) in enumerate(users):
        msgs = [{"role": "system", "content": prompt}, {"role": "user", "content": user}]
        for k, m in models.items():
            order = [True, False] if i % 2 == 0 else [False, True]
            res = {s: first_token(m, msgs, s) for s in order}
            out["rows"].append({"model": k, "saglayici": am.MODELS[k]["provider"], "qid": qid,
                                "semali": res[True], "semasiz": res[False]})
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / f"{a.tag}.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    path = OUT_DIR / "adim2" / f"sema_ek_suresi_{date.today().isoformat()}.md"
    path.write_text(report(), encoding="utf-8")
    print(path, f"{sum(r['semali']['maliyet'] + r['semasiz']['maliyet'] for r in out['rows']):.4f} USD")


if __name__ == "__main__":
    main()
