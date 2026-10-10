"""Parse edilmiş dokümanlardan parça üret (data/chunks.jsonl) ve Qdrant'a indeksle."""
import logging
import time
import warnings

from pilot.chunk import build_chunks, read_chunks, write_chunks
from pilot.index import build_index
from pilot.parse import load_or_parse
from pilot.registry import DOCS

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("index")

if __name__ == "__main__":
    all_chunks = []
    for meta in DOCS:
        chunks = build_chunks(meta, load_or_parse(meta)["elements"])
        log.info("%s: %d parça", meta.doc_id, len(chunks))
        all_chunks += chunks
    write_chunks(all_chunks)
    t = time.time()
    n = build_index(read_chunks())
    log.info("== %d parça indekslendi, %.0f sn", n, time.time() - t)
