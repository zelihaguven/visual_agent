"""Tüm pilot dokümanlarını Docling ile ayrıştırır (sadece ayrıştırma, indeksleme yok).

Uzun sürer (CPU'da sayfa başına birkaç saniye). Yarıda kalırsa tekrar çalıştırın,
tamamlanan partiler atlanır.

    python pilot/scripts/parse_all.py [doc_id ...]
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from visual_agent.config import ensure_dirs, load_documents  # noqa: E402
from visual_agent.ingestion.parse import parse_document  # noqa: E402


def main(argv: list[str]) -> int:
    ensure_dirs()
    docs = load_documents()
    targets = argv or list(docs)
    for doc_id in targets:
        t0 = time.time()
        els = parse_document(docs[doc_id], log=lambda m: print(m, flush=True))
        print(f"[{doc_id}] TAMAM: {len(els)} öğe, {time.time() - t0:.0f} sn", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
