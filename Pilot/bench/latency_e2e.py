"""Uçtan uca gecikme dökümü, dondurulan aday yapılandırma (üçlü füzyon + BM25'e çevrilmiş sorgu, reranker'sız).

Adımlar ve paralellik (her soru için):
  1. paralel: Qwen3-8B sorgu embed'i (bulut, önbelleksiz) ‖ bge-m3 sorgu embed'i (CPU) ‖ çeviri (bulut LLM)
  2. paralel: Qdrant — Qwen dense kolu ‖ bge-m3 dense kolu ‖ BM25 kolu (çevrilmiş sorgu)
  3. füzyon (RRF, istemcide)
  4. cevap üretimi (bulut LLM, akışlı; ilk token ve toplam), pipeline'ın sistem talimatı ve kaynak biçimiyle
Her adımın kendi süresi ve paralel grubun duvar saati ayrı kaydedilir. Isınma (model yükleme, bağlantı) hariç.

Kullanım (Pilot klasöründe, Qdrant sunucusu açık):
    python -m bench.latency_e2e --n 20 --answer-model mistralai/mistral-small-24b-instruct-2501
Çıktı: eval/bench/b4/asama4_gecikme_e2e_<tarih>
"""
import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from statistics import median
from typing import Any

from bench.common import KNOWN_SETS, load_questions, meta, prepare, write_result

STAGES = ("qwen_embed", "bge_embed", "ceviri", "grup1_duvar", "qdrant_qwen", "qdrant_bge", "qdrant_bm25",
          "grup2_duvar", "fuzyon", "cevap_ilk_token", "cevap_toplam", "toplam_ilk_token", "toplam")


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    k = (len(xs) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def timed(f: Any) -> Any:
    """İş parçacığında çalışacak sarmal: (sonuç, süre)."""
    def run() -> tuple[Any, float]:
        t0 = time.perf_counter()
        out = f()
        return out, time.perf_counter() - t0
    return run


def stream_answer(session: Any, model: str, messages: list[dict[str, str]], max_tokens: int) -> tuple[float, float, dict]:
    """(ilk token süresi, toplam süre, usage). ZDR zorunlu (openrouter_body)."""
    from pilot.cloud import openrouter_body
    from pilot.config import OPENROUTER_URL
    body = openrouter_body({"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": 0,
                            "stream": True, "usage": {"include": True}, "response_format": {"type": "json_object"}})
    t0 = time.perf_counter()
    first, usage = None, {}
    with session.post(f"{OPENROUTER_URL}/chat/completions", json=body, stream=True, timeout=120) as r:
        if r.status_code != 200:
            raise RuntimeError(f"{model} {r.status_code}: {r.text[:300]}")
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: ") or line == "data: [DONE]":
                continue
            d = json.loads(line[6:])
            if d.get("usage"):
                usage = d["usage"]
            delta = (d.get("choices") or [{}])[0].get("delta", {}).get("content")
            if delta and first is None:
                first = time.perf_counter() - t0
    return first or float("nan"), time.perf_counter() - t0, usage


def main() -> None:
    import requests

    from bench.providers import QueryEncoder, specs
    from bench.server import server_client
    from bench.triple_fusion import fuse
    from pilot import retrieve
    from pilot.cloud import CloudChat, api_key, require_zdr
    from pilot.config import TOP_K_SOURCES
    from pilot.pipeline import format_sources
    from pilot.prompts import SYSTEM_PROMPT
    from pilot.query import question_lang
    from pilot.sparse import bm25_query
    from pilot.translate import bm25_text, target_languages, translate_query

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261103)
    ap.add_argument("--sets", nargs="+", default=[*KNOWN_SETS, "aday_sorular"])
    ap.add_argument("--qwen-collection", default="scale_qwen3_8b_10000")
    ap.add_argument("--bge-collection", default="scale_bge_m3_10000")
    ap.add_argument("--translate-model", default="google/gemma-3-12b-it")
    ap.add_argument("--answer-model", default="mistralai/mistral-small-24b-instruct-2501")
    ap.add_argument("--max-tokens", type=int, default=600)
    ap.add_argument("--max-usd", type=float, default=0.5)
    ap.add_argument("--name", default="asama4_gecikme_e2e")
    a = ap.parse_args()

    items = [(it, prepare(it["q"])) for it in load_questions(a.sets, include_unapproved=True)]
    pool = [(it, p) for it, p in items if not p["skip"] and p["doc_ids"] and not it.get("expect_clarify")
            and not it.get("expect_not_found")]
    sample = random.Random(a.seed).sample(pool, a.n)

    qwen, bge = QueryEncoder(specs()["qwen3-8b"], 256), QueryEncoder(specs()["bge-m3-local-bm25"], 256)
    chat = CloudChat(a.translate_model)
    require_zdr(a.answer_model)
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    clients = [server_client() for _ in range(3)]
    k = retrieve.PREFETCH_K

    # ısınma: bge-m3 modeli, bağlantılar
    w = sample[0][1]["search_q"]
    bge(w, True), qwen(w, False), translate_query(w, "tr", ["en"], chat)
    stream_answer(session, a.answer_model, [{"role": "user", "content": "OK?"}], 5)
    chat.stats.update({k_: 0 if isinstance(v, int) else 0.0 for k_, v in chat.stats.items()})
    qwen.cloud.cache = None      # gerçek çağrı süresi; SQLite önbelleği iş parçacıkları arasında kullanılamaz

    rows, cost = [], {"ceviri": 0.0, "cevap": 0.0, "qwen": 0.0}
    with ThreadPoolExecutor(max_workers=3) as ex:
        for it, p in sample:
            q, scope = p["search_q"], p["doc_ids"]
            flt = retrieve._filter(None, scope)
            src, targets = question_lang(it["q"]), target_languages(scope)
            t1 = time.perf_counter()
            fq = ex.submit(timed(lambda: qwen(q, False)))
            fb = ex.submit(timed(lambda: bge(q, True)))
            ft = ex.submit(timed(lambda: translate_query(q, src, targets, chat)))
            (qv, s_q), (bv, s_b), (tr, s_t) = fq.result(), fb.result(), ft.result()
            g1 = time.perf_counter() - t1
            sq = {**qv, "sparse": bm25_query(bm25_text(tr, q))}
            t2 = time.perf_counter()
            fa = ex.submit(timed(lambda: retrieve.candidates(clients[0], qv, flt, "dense", collection=a.qwen_collection,
                                                             dense_mode="short_rescore", short_dim=256, fused_k=k)))
            fbg = ex.submit(timed(lambda: retrieve.candidates(clients[1], bv, flt, "dense", collection=a.bge_collection,
                                                              dense_mode="full", fused_k=k)))
            fs = ex.submit(timed(lambda: retrieve.candidates(clients[2], sq, flt, "sparse", collection=a.qwen_collection,
                                                             sparse_name="bm25", fused_k=k)))
            (arm_q, s_aq), (arm_b, s_ab), (arm_s, s_as) = fa.result(), fbg.result(), fs.result()
            g2 = time.perf_counter() - t2
            t3 = time.perf_counter()
            top = fuse([arm_q, arm_b, arm_s], TOP_K_SOURCES, retrieve.RRF_K)
            s_f = time.perf_counter() - t3
            hits = [retrieve.Hit(x.payload, i, None, x.score) for i, x in enumerate(top)]
            user = f"{format_sources(hits)}\n\n<cevap_dili>{src.upper()}</cevap_dili>\n\n<soru>\n{q}\n</soru>"
            ttft, s_ans, usage = stream_answer(session, a.answer_model, [{"role": "system", "content": SYSTEM_PROMPT},
                                                                         {"role": "user", "content": user}],
                                               a.max_tokens)
            cost["cevap"] += float(usage.get("cost") or 0.0)
            pre = g1 + g2 + s_f
            rows.append({"qid": it["qid"], "qwen_embed": s_q, "bge_embed": s_b, "ceviri": s_t, "grup1_duvar": g1,
                         "qdrant_qwen": s_aq, "qdrant_bge": s_ab, "qdrant_bm25": s_as, "grup2_duvar": g2,
                         "fuzyon": s_f, "cevap_ilk_token": ttft, "cevap_toplam": s_ans,
                         "toplam_ilk_token": pre + ttft, "toplam": pre + s_ans, "ceviri_cagri": bool(set(targets) - {src}),
                         "prompt_tokens": usage.get("prompt_tokens"), "completion_tokens": usage.get("completion_tokens")})
            cost["ceviri"], cost["qwen"] = chat.stats["cost_usd"], qwen.cloud.stats["cost_usd"]
            if sum(cost.values()) > a.max_usd:
                raise SystemExit(f"harcama sınırı aşıldı: {cost}")
    for c in clients:
        c.close()

    summ = {s: {"p50": median([r[s] for r in rows]), "p95": pct([r[s] for r in rows], 95)} for s in STAGES}
    data = {"meta": meta({"n": a.n, "seed": a.seed, "translate_model": a.translate_model,
                          "answer_model": a.answer_model, "max_tokens": a.max_tokens}),
            "summary": summ, "rows": rows, "cost_usd": cost}
    f = lambda x: f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ",")
    names = {"qwen_embed": "Qwen3-8B sorgu embed'i (bulut)", "bge_embed": "bge-m3 sorgu embed'i (CPU)",
             "ceviri": f"Çeviri ({a.translate_model})", "grup1_duvar": "**Grup 1 duvar saati** (üçü paralel)",
             "qdrant_qwen": "Qdrant: Qwen dense kolu", "qdrant_bge": "Qdrant: bge-m3 dense kolu",
             "qdrant_bm25": "Qdrant: BM25 kolu (çevrilmiş)", "grup2_duvar": "**Grup 2 duvar saati** (üçü paralel)",
             "fuzyon": "Füzyon (RRF)", "cevap_ilk_token": f"Cevap ilk token ({a.answer_model})",
             "cevap_toplam": "Cevap toplam (akış bitişi)", "toplam_ilk_token": "**Uçtan uca, ilk token**",
             "toplam": "**Uçtan uca, cevap bitişi**"}
    lines = [f"# Uçtan uca gecikme: üçlü füzyon + çevirili BM25, reranker'sız ({a.n} soru, 10k, filtreli)", "",
             "Geliştirme dizüstü (i5-1335U, GPU yok), bulut çağrıları bu makinenin bağlantısından: **üretimi temsil "
             "etmez**. Isınma hariç; Qwen sorgu embed'i önbelleksiz (gerçek çağrı). Cevap modeli henüz seçilmedi "
             f"(PRD A1): `{a.answer_model}` yalnız gösterge.", "",
             "| Adım | Paralel grubu | p50 | p95 |", "|---|---|---|---|"]
    group = {"qwen_embed": "1", "bge_embed": "1", "ceviri": "1", "qdrant_qwen": "2", "qdrant_bge": "2",
             "qdrant_bm25": "2"}
    for s in STAGES:
        lines.append(f"| {names[s]} | {group.get(s, '–')} | {f(summ[s]['p50'])} | {f(summ[s]['p95'])} |")
    lines += ["", f"Çeviri çağrısı yapılan soru: {sum(r['ceviri_cagri'] for r in rows)}/{a.n}. "
              f"Harcama: çeviri {cost['ceviri']:.4f} USD, Qwen embed {cost['qwen']:.5f} USD, cevap {cost['cevap']:.4f} USD.", ""]
    print(write_result(a.name, data, "\n".join(lines) + "\n"))


if __name__ == "__main__":
    main()
