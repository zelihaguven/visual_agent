"""BM25 kolu için sorgu çevirisi ölçümü, adım 1: soruları kapsamın diline çevir (bulut LLM, ZDR), süreyi ve maliyeti kaydet.

Her soru bir çağrı (gerekiyorsa; soru zaten hedef dildeyse çağrı yok). Çeviri dosyası bench.triple_fusion
--bm25-translations ile okunur. Harcama --max-usd'yi geçerse durur.

Kullanım (Pilot klasöründe): python -m bench.translate_bm25 --model google/gemma-3-12b-it --tag ceviri_gemma3_12b \\
    --sets questions questions_ek sekil_sorular aday_sorular --include-unapproved
Çıktı: data/bench_cache/<tag>.json
"""
import argparse
import json
import logging
import time
from typing import Any

from bench.common import KNOWN_SETS, load_questions, prepare

log = logging.getLogger("bench")


def main() -> None:
    from bench.providers import CACHE_DIR
    from pilot.cloud import CloudChat
    from pilot.query import question_lang
    from pilot.translate import bm25_text, target_languages, translate_query

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--sets", nargs="+", default=list(KNOWN_SETS))
    ap.add_argument("--include-unapproved", action="store_true")
    ap.add_argument("--max-usd", type=float, default=1.0)
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    chat = CloudChat(a.model)
    out: dict[str, Any] = {"questions": {}}
    items = [(it, prepare(it["q"])) for it in load_questions(a.sets, include_unapproved=a.include_unapproved)]
    items = [(it, p) for it, p in items if not p["skip"] and not it.get("expect_clarify")]
    for n, (it, p) in enumerate(items, 1):
        src = question_lang(it["q"])
        targets = target_languages(p["doc_ids"]), target_languages(None)
        rec: dict[str, Any] = {"src": src, "search_q": p["search_q"]}
        for mode, tg in zip(("filtered", "unfiltered"), targets):
            before = chat.stats["requests"]
            t0 = time.perf_counter()
            tr = translate_query(p["search_q"], src, tg, chat)
            rec[mode] = {"targets": tg, "translations": tr, "bm25": bm25_text(tr, p["search_q"]),
                         "called": chat.stats["requests"] > before,
                         "seconds": time.perf_counter() - t0 if chat.stats["requests"] > before else 0.0}
        out["questions"][it["qid"]] = rec
        if chat.stats["cost_usd"] > a.max_usd:
            raise SystemExit(f"harcama sınırı aşıldı: {chat.stats}")
        if n % 25 == 0:
            log.info("%d/%d · %.4f USD", n, len(items), chat.stats["cost_usd"])
    out["params"] = {"model": a.model, "sets": a.sets, "include_unapproved": a.include_unapproved,
                     "stats": chat.stats}
    path = CACHE_DIR / f"{a.tag}.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    log.info("yazıldı: %s · %s", path, chat.stats)


if __name__ == "__main__":
    main()
