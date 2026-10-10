"""Tüm pilot dokümanlarını parse eder (Docling, sonuç data/parsed/ altında önbelleklenir)."""
import logging
import sys
import warnings

from pilot.parse import load_or_parse
from pilot.registry import DOCS

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("parse")

if __name__ == "__main__":
    wanted = set(sys.argv[1:])
    for meta in DOCS:
        if wanted and meta.doc_id not in wanted:
            continue
        res = load_or_parse(meta)
        log.info("== %s: %d öğe, %.0f sn, başarısız sayfa: %s", meta.doc_id, res["n_elements"],
                 res["seconds"], res["failed_pages"] or "yok")
