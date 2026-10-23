"""Bütün dokümanları yeni parçalama kurallarıyla yeniden parçala ve indeksi güncelle (yalnız gereken kadar embed).

Kullanım (Pilot klasöründe, arayüz kapalı): python run_rechunk.py [--dry-run]
- embed_text'i değişen dokümanlar yeniden embed edilir (index.replace_docs; CPU'da ~0,8 parça/sn)
- yalnız payload'ı değişenler (ör. nav işareti) vektörlere dokunmadan güncellenir (index.refresh_payloads)
- chunks.jsonl yeni parçalarla yazılır. Yarıda kalırsa yeniden çalıştırın: indeksteki embed_text zaten yeni olan
  dokümanlar atlanır. PILOT_QDRANT_URL tanımlıysa sunucudaki koleksiyon güncellenir.
"""
import json
import logging
import sys
import time
import warnings
from dataclasses import asdict

from qdrant_client import models

from pilot.chunk import build_chunks
from pilot.config import CHUNKS_PATH, COLLECTION
from pilot.figures import load_figures
from pilot.index import client, refresh_payloads, replace_docs
from pilot.parse import load_or_parse
from pilot.registry import DOCS

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("rechunk")


def indexed_embed_texts(doc_id: str) -> list[str]:
    qc = client()
    try:
        out, offset = [], None
        while True:
            pts, offset = qc.scroll(COLLECTION, limit=1000, offset=offset, with_payload=["chunk_id", "embed_text"],
                                    scroll_filter=models.Filter(must=[models.FieldCondition(
                                        key="doc_id", match=models.MatchValue(value=doc_id))]))
            out += [(p.payload["chunk_id"], p.payload["embed_text"]) for p in pts]
            if offset is None:
                return [t for _, t in sorted(out)]
    finally:
        qc.close()


if __name__ == "__main__":
    dry = "--dry-run" in sys.argv
    fresh = {m.doc_id: [asdict(c) for c in build_chunks(m, load_or_parse(m)["elements"], load_figures(m))]
             for m in DOCS}
    merged = [c for m in DOCS for c in fresh[m.doc_id]]
    embed_docs, payload_docs = [], []
    for m in DOCS:
        new = [c["embed_text"] for c in fresh[m.doc_id]]
        (payload_docs if indexed_embed_texts(m.doc_id) == new else embed_docs).append(m.doc_id)
    log.info("yeniden embed: %s", embed_docs or "–")
    log.info("yalnız payload: %s", payload_docs or "–")
    if dry:
        sys.exit(0)
    with CHUNKS_PATH.open("w", encoding="utf-8") as f:
        for c in merged:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    log.info("chunks.jsonl: %d parça", len(merged))
    t = time.time()
    n = refresh_payloads(merged, payload_docs) if payload_docs else 0
    log.info("payload güncellendi: %d nokta (%.0f sn)", n, time.time() - t)
    for d in embed_docs:          # doküman doküman: yarıda kalırsa biten dokümanlar bir sonraki çalıştırmada atlanır
        t = time.time()
        k = replace_docs(merged, [d])
        log.info("%s: %d parça yeniden embed edildi (%.0f sn)", d, k, time.time() - t)
    log.info("== bitti")
