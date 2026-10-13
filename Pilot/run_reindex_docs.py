"""Yalnız verilen dokümanları yeniden parçala ve indeksle (parse düzeltmesinden sonra; tam indeks gerekmez).

Kullanım: python run_reindex_docs.py brother-s7300a brother-s7300b
Not: Qdrant gömülü modda klasörü tek süreç açabilir; arayüz ve değerlendirme çalışırken başlatmayın.
"""
import json
import logging
import sys
import time
import warnings
from dataclasses import asdict

from pilot.chunk import build_chunks, read_chunks
from pilot.config import CHUNKS_PATH
from pilot.index import replace_docs
from pilot.parse import load_or_parse
from pilot.registry import BY_ID, DOCS

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("reindex")

if __name__ == "__main__":
    targets = sys.argv[1:]
    unknown = [d for d in targets if d not in BY_ID]
    if not targets or unknown:
        sys.exit(f"Doküman kimliği verin. Bilinmeyen: {unknown}")
    old: dict[str, list[dict]] = {}
    for c in read_chunks():
        old.setdefault(c["doc_id"], []).append(c)
    fresh = {d: [asdict(c) for c in build_chunks(BY_ID[d], load_or_parse(BY_ID[d])["elements"])] for d in targets}
    for d, cs in fresh.items():
        log.info("%s: %d parça (önce %d)", d, len(cs), len(old.get(d, [])))
    # chunks.jsonl kayıt sırasını korur: hedef dokümanlar yenileriyle, diğerleri olduğu gibi
    merged = [c for meta in DOCS for c in fresh.get(meta.doc_id, old.get(meta.doc_id, []))]
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for c in merged:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    t = time.time()
    n = replace_docs(merged, targets)
    log.info("== %d parça yeniden indekslendi, %.0f sn", n, time.time() - t)
