"""Süre sınırı ve yedek yol (özet rapor §9.3), yalnız ölçüm aracında; uygulamaya bağlı değil.

Aday yapılandırma (üçlü füzyon + çevirili BM25, rerank'sız, 10k, hattın kapsamıyla) her soruda iki kez değerlendirilir,
aynı bulut çağrılarıyla:
  - korumalı: Qwen3-8B sorgu embed'i 1 sn'de gelmezse aynı istek ikinci kez (hedge), 1,5 sn'de ikisi de yoksa o soru
    Qwen kolsuz (bge-m3 + çevirili BM25, "yedek yol"); devre kesici: son 5 denemenin 3'ü sınırı aştıysa 120 sn boyunca
    Qwen beklenmez. Çeviri 1,2 sn'de gelmezse BM25 çevirisiz. Cevap modeli: 1,2 sn'de ilk token yoksa ikinci akış
    (hedge), ilk token gelen kullanılır; toplam 20 sn sınırı.
  - korumasız (karşılaştırma): aynı çağrıların hepsi beklenseydi (Qwen'in ilk isteği, çevirinin kendisi, cevabın ilk
    akışı). Korumalı yolda bırakılan çağrılar arka planda bitene kadar beklenir ve süreleri kaydedilir.
İlk kelime süresi = soru başından cevabın ilk tokenine (grup 1: embed'ler ‖ çeviri; grup 2: Qdrant; füzyon; cevap).
Korumasız ilk kelime süresi aynı ölçümlerden bileşik: grup 1 en uzun çağrı + aynı grup 2/füzyon + ilk akışın ilk tokeni.
Her bulut yanıtında sağlayıcı kaydedilir. ZDR zorunlu (require_zdr + openrouter_body).

Kullanım (Pilot klasöründe, Qdrant sunucusu açık):
    python -m bench.latency_guard --answer-model mistralai/mistral-small-24b-instruct-2501 --max-usd 0.3
"""
import argparse
import json
import threading
import time
from collections import Counter, deque
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any

from bench.common import KNOWN_SETS, accuracy, first_rank, fmt_pct, load_questions, meta, prepare, write_result

QWEN_MODEL = "qwen/qwen3-embedding-8b"
_local = threading.local()


def pct(xs: list[float], p: float) -> float:
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p / 100
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def session() -> Any:
    """İş parçacığı başına bir requests oturumu (eşzamanlı istekler)."""
    import requests

    from pilot.cloud import api_key
    if not hasattr(_local, "s"):
        _local.s = requests.Session()
        _local.s.headers.update({"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    return _local.s


def qwen_call(text: str) -> dict[str, Any]:
    """Tek embed isteği: {vec, sn, provider, cost, err}."""
    from pilot.cloud import openrouter_body
    from pilot.config import OPENROUTER_URL
    t0 = time.perf_counter()
    try:
        r = session().post(f"{OPENROUTER_URL}/embeddings", timeout=60,
                           json=openrouter_body({"model": QWEN_MODEL, "input": [text], "encoding_format": "float"}))
        d = r.json() if r.status_code == 200 else {}
        return {"vec": d["data"][0]["embedding"] if d else None, "sn": time.perf_counter() - t0,
                "provider": d.get("provider"), "cost": float((d.get("usage") or {}).get("cost") or 0.0),
                "err": "" if d else f"{r.status_code}: {r.text[:120]}"}
    except Exception as e:  # noqa: BLE001 — zaman aşımı/bağlantı: kayda geçer
        return {"vec": None, "sn": time.perf_counter() - t0, "provider": None, "cost": 0.0, "err": repr(e)[:120]}


def stream_call(body: dict[str, Any], t_start: float, rec: dict[str, Any], first_ev: threading.Event,
                cap: float) -> None:
    """Akışlı cevap; rec'e ilk token (t_start'tan), toplam, sağlayıcı, maliyet yazar. rec['stop'] ilk tokenden sonra
    kesmek için (kaybeden akış); cap: soru başından toplam süre sınırı."""
    from pilot.cloud import openrouter_body
    from pilot.config import OPENROUTER_URL
    t0 = time.perf_counter()
    try:
        with session().post(f"{OPENROUTER_URL}/chat/completions", json=openrouter_body(body), stream=True,
                            timeout=60) as r:
            if r.status_code != 200:
                rec["err"] = f"{r.status_code}: {r.text[:120]}"
                return
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: ") or line == "data: [DONE]":
                    continue
                d = json.loads(line[6:])
                rec["provider"] = d.get("provider") or rec.get("provider")
                if d.get("usage"):
                    rec["cost"] = float(d["usage"].get("cost") or 0.0)
                if rec.get("first") is None and (d.get("choices") or [{}])[0].get("delta", {}).get("content"):
                    rec["first"], rec["first_own"] = time.perf_counter() - t_start, time.perf_counter() - t0
                    first_ev.set()
                if rec.get("first") is not None and rec.get("stop"):
                    rec["kesildi"] = "kaybeden"
                    break
                if time.perf_counter() - t_start > cap:
                    rec["kesildi"] = "sinir"
                    break
    except Exception as e:  # noqa: BLE001
        rec["err"] = repr(e)[:120]
    finally:
        rec["total"] = time.perf_counter() - t_start


def main() -> None:
    from bench.providers import QueryEncoder, specs
    from bench.server import server_client
    from bench.triple_fusion import K_OUT, fuse
    from pilot import retrieve
    from pilot.cloud import CloudChat, require_zdr
    from pilot.config import TOP_K_SOURCES
    from pilot.pipeline import format_sources
    from pilot.prompts import SYSTEM_PROMPT
    from pilot.query import question_lang
    from pilot.sparse import bm25_query
    from pilot.translate import bm25_text, target_languages, translate_query

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sets", nargs="+", default=[*KNOWN_SETS, "aday_sorular"])
    ap.add_argument("--n", type=int, default=0, help="0: bütün cevaplı sorular")
    ap.add_argument("--qwen-collection", default="scale_qwen3_8b_10000")
    ap.add_argument("--bge-collection", default="scale_bge_m3_10000")
    ap.add_argument("--translate-model", default="google/gemma-3-12b-it")
    ap.add_argument("--answer-model", default="mistralai/mistral-small-24b-instruct-2501")
    ap.add_argument("--max-tokens", type=int, default=600)
    ap.add_argument("--hedge", type=float, default=1.0, help="Qwen: ikinci istek (sn)")
    ap.add_argument("--qwen-limit", type=float, default=1.5, help="Qwen: yedek yola geçiş (sn)")
    ap.add_argument("--translate-limit", type=float, default=1.2)
    ap.add_argument("--answer-hedge", type=float, default=1.2)
    ap.add_argument("--answer-cap", type=float, default=20.0)
    ap.add_argument("--breaker", default="3/5/120", help="aşım/son N/kapalı kalma sn")
    ap.add_argument("--max-usd", type=float, default=0.3)
    ap.add_argument("--name", default="asama4_sure_siniri")
    ap.add_argument("--report-only", help="kayıtlı sonuç (.json) için yalnız raporu yeniden yaz; çağrı yok")
    a = ap.parse_args()
    if a.report_only:
        from pathlib import Path
        p = Path(a.report_only)
        d = json.loads(p.read_text(encoding="utf-8"))
        p.with_suffix(".md").write_text(report(d["rows"], d["cost_usd"], argparse.Namespace(**d["meta"]["params"])),
                                        encoding="utf-8")
        return
    b_hits, b_n, b_sec = (float(x) for x in a.breaker.split("/"))

    items = [(it, prepare(it["q"])) for it in load_questions(a.sets, include_unapproved=True)]
    pool = [(it, p) for it, p in items if not p["skip"] and not it.get("expect_clarify")
            and not it.get("expect_not_found") and (it.get("expect_docs") or it.get("kabul"))]
    pool = pool[:a.n] if a.n else pool

    require_zdr(QWEN_MODEL), require_zdr(a.answer_model)
    bge = QueryEncoder(specs()["bge-m3-local-bm25"], 256)
    clients = [server_client() for _ in range(3)]
    k = retrieve.PREFETCH_K
    ex = ThreadPoolExecutor(max_workers=12)

    def search(qv: dict | None, bv: dict, bm25: str, flt: Any) -> list[dict]:
        sq = {**bv, "sparse": bm25_query(bm25)}
        jobs = []
        if qv:
            jobs.append(ex.submit(retrieve.candidates, clients[0], qv, flt, "dense", collection=a.qwen_collection,
                                  dense_mode="short_rescore", short_dim=256, fused_k=k))
        jobs.append(ex.submit(retrieve.candidates, clients[1], bv, flt, "dense", collection=a.bge_collection,
                              dense_mode="full", fused_k=k))
        jobs.append(ex.submit(retrieve.candidates, clients[2], sq, flt, "sparse", collection=a.bge_collection,
                              sparse_name="bm25", fused_k=k))
        return [p.payload for p in fuse([j.result() for j in jobs], K_OUT, retrieve.RRF_K)]

    def qvec(vec: list[float]) -> dict[str, Any]:
        from pilot.embed import short_vector
        return {"dense": vec, "short": short_vector(vec, 256), "sparse": {}}

    # ısınma: bge-m3 modeli, bağlantılar
    # tek çeviri istemcisi (bağlantı açık kalır; çeviri bir sonraki soruya kadar her zaman biter, eşzamanlı değil)
    chat = CloudChat(a.translate_model)
    w = pool[0][1]["search_q"]
    bge(w, True), qwen_call(w), translate_query(w, "tr", ["en"], chat)
    stream_call({"model": a.answer_model, "messages": [{"role": "user", "content": "OK?"}], "max_tokens": 5},
                time.perf_counter(), {}, threading.Event(), 30)

    recent: deque[bool] = deque(maxlen=int(b_n))
    open_until = 0.0
    rows: list[dict[str, Any]] = []
    cost = {"qwen": 0.0, "ceviri": 0.0, "cevap": 0.0}
    for n, (it, p) in enumerate(pool, 1):
        q, scope = p["search_q"], p["doc_ids"]
        flt = retrieve._filter(None, scope)
        src, targets = question_lang(it["q"]), target_languages(scope)
        tr_cost0 = chat.stats["cost_usd"]
        row: dict[str, Any] = {"qid": it["qid"], "set": it["set"]}
        t0 = time.perf_counter()

        # --- grup 1: Qwen (hedge + sınır + devre kesici) ‖ bge-m3 ‖ çeviri (sınır)
        breaker_open = time.monotonic() < open_until
        fq = ex.submit(qwen_call, q)
        ft = ex.submit(lambda: (translate_query(q, src, targets, chat), time.perf_counter() - t0))
        bv = bge(q, True)
        s_bge = time.perf_counter() - t0
        fh = None
        qwen_got, qwen_how = None, "devre_kesici" if breaker_open else None
        if not breaker_open:
            done, _ = wait([fq], timeout=max(0.0, a.hedge - (time.perf_counter() - t0)))
            if not done:
                fh = ex.submit(qwen_call, q)
            while qwen_got is None and time.perf_counter() - t0 < a.qwen_limit:
                live = [f for f in (fq, fh) if f]
                done, _ = wait(live, timeout=a.qwen_limit - (time.perf_counter() - t0), return_when="FIRST_COMPLETED")
                for f in done:
                    if f.result()["vec"] is not None and qwen_got is None:
                        qwen_got, qwen_how = f.result(), "ilk" if f is fq else "hedge"
                if len(done) == len(live):
                    break
            if qwen_got is None:
                qwen_how = "yedek"
            recent.append(qwen_got is None)
            if sum(recent) >= b_hits:
                open_until, recent = time.monotonic() + b_sec, deque(maxlen=int(b_n))
        s_qwen = time.perf_counter() - t0 if qwen_got else None
        done, _ = wait([ft], timeout=max(0.0, a.translate_limit - (time.perf_counter() - t0)))
        tr_ok = bool(done) and ft.exception() is None
        bm25 = bm25_text(ft.result()[0], q) if tr_ok else q
        g1 = time.perf_counter() - t0

        # --- grup 2 + füzyon (korumalı yol)
        t2 = time.perf_counter()
        ranked = search(qvec(qwen_got["vec"]) if qwen_got else None, bv, bm25, flt)
        g2 = time.perf_counter() - t2

        # --- cevap: ilk akış, 1,2 sn'de ilk token yoksa ikinci akış; ilk token gelen kullanılır
        hits = [retrieve.Hit({"brand": "", "product": "", "lang": "en", "doc_type": "", "section": "", **c}, i)
                for i, c in enumerate(ranked[:TOP_K_SOURCES])]
        user = f"{format_sources(hits)}\n\n<cevap_dili>{src.upper()}</cevap_dili>\n\n<soru>\n{q}\n</soru>"
        body = {"model": a.answer_model, "max_tokens": a.max_tokens, "temperature": 0, "stream": True,
                "usage": {"include": True}, "response_format": {"type": "json_object"},
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": user}]}
        ev = threading.Event()
        ra, rb = {}, {}
        fa =ex.submit(stream_call, body, t0, ra, ev, a.answer_cap)
        fb = None
        if not ev.wait(a.answer_hedge):
            fb = ex.submit(stream_call, body, t0, rb, ev, a.answer_cap)
        ev.wait(a.answer_cap)
        firsts = [(r["first"], name, r) for name, r in (("ilk", ra), ("hedge", rb)) if r.get("first") is not None]
        win = min(firsts, key=lambda x: x[0]) if firsts else None
        for r in (ra, rb):                                # kaybeden akış ilk tokeninden sonra kesilir (süresi kayıtlı)
            if win and r is not win[2]:
                r["stop"] = True
        wait([f for f in (fa, fb) if f])
        first_word = win[0] if win else float("nan")

        # --- korumasız karşılaştırma: bırakılan çağrılar bitince
        orig_q = fq.result()
        orig_tr = ft.result() if ft.exception() is None else None
        s_tr = orig_tr[1] if orig_tr else float("nan")
        if orig_q["vec"] is not None and (qwen_how != "ilk" or not tr_ok):
            ranked_full = search(qvec(orig_q["vec"]), bv, bm25_text(orig_tr[0], q) if orig_tr else q, flt)
        else:
            ranked_full = ranked
        g1_full = max(s_bge, orig_q["sn"], s_tr if orig_tr else 0.0)
        first_full = g1_full + g2 + (ra.get("first_own", float("nan")) if ra else float("nan"))

        for r in (orig_q, fh.result() if fh else None):
            if r:
                cost["qwen"] += r["cost"]
        cost["ceviri"] += chat.stats["cost_usd"] - tr_cost0
        cost["cevap"] += ra.get("cost", 0.0) + rb.get("cost", 0.0)
        row.update({"qwen": qwen_how, "qwen_sn": s_qwen, "qwen_ilk_sn": orig_q["sn"],
                    "qwen_hedge_sn": fh.result()["sn"] if fh else None,
                    "qwen_provider": (qwen_got or orig_q).get("provider"),
                    "ceviri_ok": tr_ok, "ceviri_sn": s_tr, "ceviri_cagri": bool(set(targets) - {src}),
                    "bge_sn": s_bge, "grup1": g1, "grup2": g2,
                    "cevap": win[1] if win else "yok", "cevap_hedge_acildi": fb is not None,
                    "cevap_ilk_token": ra.get("first"),
                    "cevap_hedge_ilk_token": rb.get("first"), "cevap_provider": win[2].get("provider") if win else None,
                    "cevap_hedge_provider": rb.get("provider"), "cevap_hata": ra.get("err") or rb.get("err"),
                    "cevap_kesildi": (win[2].get("kesildi") if win else None),
                    "ilk_kelime": first_word, "ilk_kelime_korumasiz": first_full,
                    "rank": first_rank(ranked, it), "rank_korumasiz": first_rank(ranked_full, it)})
        rows.append(row)
        spent = sum(cost.values())
        print(f"{time.strftime('%H:%M:%S')} {n}/{len(pool)} {it['qid']} qwen={qwen_how} çeviri={'ok' if tr_ok else 'SINIR'}"
              f" cevap={row['cevap']} ilk_kelime={first_word:.2f} (korumasız {first_full:.2f}) sıra={row['rank']}"
              f"/{row['rank_korumasiz']} · {spent:.4f} USD", flush=True)
        if spent > a.max_usd:
            print(f"harcama sınırı aşıldı: {cost}", flush=True)
            break
    ex.shutdown(wait=True)
    for c in clients:
        c.close()
    print(write_result(a.name, {"meta": meta(vars(a)), "rows": rows, "cost_usd": cost}, report(rows, cost, a)))


def report(rows: list[dict[str, Any]], cost: dict[str, float], a: argparse.Namespace) -> str:
    n = len(rows)
    f = lambda x: "–" if x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    qh = Counter(r["qwen"] for r in rows)
    acc_g, acc_u = accuracy([r["rank"] for r in rows]), accuracy([r["rank_korumasiz"] for r in rows])
    fb = [r for r in rows if r["qwen"] in ("yedek", "devre_kesici")]
    acc_fb_g, acc_fb_u = accuracy([r["rank"] for r in fb]), accuracy([r["rank_korumasiz"] for r in fb])
    fw = [r["ilk_kelime"] for r in rows if r["ilk_kelime"] == r["ilk_kelime"]]
    fu = [r["ilk_kelime_korumasiz"] for r in rows if r["ilk_kelime_korumasiz"] == r["ilk_kelime_korumasiz"]]
    lines = [f"# Süre sınırı ve yedek yol: aday yapılandırma, {n} cevaplı soru (10k, hattın kapsamıyla, rerank'sız)", "",
             "Yalnız ölçüm aracında (`bench/latency_guard.py`); uygulamaya bağlı değil. Geliştirme dizüstü ve bu "
             "makinenin bağlantısı: **üretimi temsil etmez**. Onaysız set: geçici. Cevap modeli seçilmedi (PRD A1); "
             f"`{a.answer_model}` yalnız gösterge.", "",
             f"Ayarlar: Qwen hedge {a.hedge} sn, yedek yol {a.qwen_limit} sn, devre kesici {a.breaker} "
             f"(aşım/son N/sn); çeviri sınırı {a.translate_limit} sn (aşınca BM25 çevirisiz); cevap hedge "
             f"{a.answer_hedge} sn, toplam sınır {a.answer_cap} sn.", "",
             "## Yedek yola düşme", "",
             "| Qwen sonucu | soru | oran |", "|---|---|---|"]
    for key, label in (("ilk", "ilk istek zamanında"), ("hedge", "hedge kazandı"), ("yedek", "yedek yol (1,5 sn aşıldı)"),
                       ("devre_kesici", "devre kesici açık (Qwen beklenmedi)")):
        lines.append(f"| {label} | {qh[key]} | {qh[key] / n:.0%} |".replace(".", ","))
    tr_called = [r for r in rows if r["ceviri_cagri"]]
    lines += ["", f"Çeviri sınırı aşılan: {sum(not r['ceviri_ok'] for r in tr_called)}/{len(tr_called)} çeviri çağrısı. "
              f"Cevapta hedge açılan: {sum(r['cevap_hedge_acildi'] for r in rows)}, "
              f"hedge kazanan: {sum(r['cevap'] == 'hedge' for r in rows)}, ilk token gelmeyen: "
              f"{sum(r['cevap'] == 'yok' for r in rows)} (bunlardan sağlayıcı hız sınırı, 429: "
              f"{sum(r['cevap'] == 'yok' and '429' in (r['cevap_hata'] or '') for r in rows)}; "
              "ilk kelime yüzdeliklerine girmez).", "",
              "## Doğruluğa etkisi (filtreli, aynı sorular)", "",
              "| | n | hit@1 | hit@5 |", "|---|---|---|---|",
              f"| Korumasız (her çağrı beklenir) | {acc_u['n']} | {fmt_pct(acc_u['hit@1'])} | {fmt_pct(acc_u['hit@5'])} |",
              f"| **Korumalı** | {acc_g['n']} | {fmt_pct(acc_g['hit@1'])} | {fmt_pct(acc_g['hit@5'])} |",
              f"| Yalnız yedek yola düşen sorular, korumasız | {acc_fb_u['n']} | {fmt_pct(acc_fb_u['hit@1'])} | "
              f"{fmt_pct(acc_fb_u['hit@5'])} |",
              f"| Yalnız yedek yola düşen sorular, korumalı | {acc_fb_g['n']} | {fmt_pct(acc_fb_g['hit@1'])} | "
              f"{fmt_pct(acc_fb_g['hit@5'])} |", "",
              "## İlk kelime süresi (soru başından cevabın ilk tokenine)", "",
              "| | p50 | p90 | p95 | en uzun |", "|---|---|---|---|---|",
              f"| Korumasız (bileşik) | {f(pct(fu, 50))} | {f(pct(fu, 90))} | {f(pct(fu, 95))} | {f(max(fu) if fu else float('nan'))} |",
              f"| **Korumalı** | {f(pct(fw, 50))} | {f(pct(fw, 90))} | {f(pct(fw, 95))} | {f(max(fw) if fw else float('nan'))} |",
              "", "Adım süreleri (p50 / p95; Qwen ve çeviri: çağrının kendi süresi, beklensin beklenmesin): " + ", ".join(
                  f"{label} {f(pct([r[k] for r in rows if r[k] is not None], 50))} / "
                  f"{f(pct([r[k] for r in rows if r[k] is not None], 95))}"
                  for k, label in (("qwen_ilk_sn", "Qwen embed"), ("bge_sn", "bge-m3 embed"), ("ceviri_sn", "çeviri"),
                                   ("grup1", "grup 1 (korumalı)"), ("grup2", "grup 2 Qdrant"))), "",
              "Sağlayıcılar: Qwen " + json.dumps(Counter(r["qwen_provider"] for r in rows), ensure_ascii=False)
              + ", cevap " + json.dumps(Counter(r["cevap_provider"] for r in rows), ensure_ascii=False) + ".", "",
              f"Harcama: Qwen {cost['qwen']:.5f}, çeviri {cost['ceviri']:.4f}, cevap {cost['cevap']:.4f} USD "
              f"(toplam {sum(cost.values()):.4f}; sınır {a.max_usd}).", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
