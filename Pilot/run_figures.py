"""Şekillere VLM açıklaması yaz (data/figures/<doc_id>.json). Kaldığı yerden sürer; aynı görsel bir kez açıklanır.

Kullanım: python run_figures.py [doc_id ...] [--limit N] [--force]
Sonra parçaları ve indeksi yenileyin: python run_reindex_docs.py <doc_id ...>
Not: Ollama'da VLM modeli olmalı (ollama pull qwen2.5vl:3b, ~3,2 GB).
"""
import argparse
import logging
import time
import warnings

from pilot.figures import describe_document, is_candidate, is_described
from pilot.parse import load_or_parse
from pilot.registry import BY_ID, DOCS

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger("figures")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("docs", nargs="*")
    ap.add_argument("--limit", type=int, help="doküman başına en fazla bu kadar yeni VLM çağrısı")
    ap.add_argument("--force", action="store_true", help="eski açıklamaları yok say, yeniden üret")
    args = ap.parse_args()
    unknown = [d for d in args.docs if d not in BY_ID]
    if unknown:
        raise SystemExit(f"Bilinmeyen doküman: {unknown}")
    for meta in DOCS:
        if args.docs and meta.doc_id not in args.docs:
            continue
        elements = load_or_parse(meta)["elements"]
        t = time.time()
        res = describe_document(meta, elements, force=args.force, limit=args.limit)
        figs = res["figures"].values()
        n_pic = sum(e["label"] == "picture" for e in elements)
        log.info("== %s: %d resim, %d aday, %d açıklandı, %d süs/ikon, %.0f sn", meta.doc_id, n_pic,
                 sum(map(is_candidate, elements)), sum(map(is_described, figs)),
                 sum(f["desc"] == "DECORATIVE" for f in figs), time.time() - t)
