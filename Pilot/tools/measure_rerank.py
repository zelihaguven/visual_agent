"""Eşik kalibrasyonu için ön ölçüm: her test sorusunda (model çağırmadan) en iyi rerank skoru.

Cevaplı ve cevapsız soruların skorları ayrışıyorsa MIN_RERANK_SCORE için geçici bir değer seçilebilir.
Kullanım: python tools/measure_rerank.py  -> eval/rerank_skorlari.json
"""
import json
import sys
import time
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
warnings.filterwarnings("ignore")

from pilot.query import analyze_query  # noqa: E402
from pilot.retrieve import search  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    questions = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))
    rows = []
    for it in questions:
        t = time.time()
        ctx = analyze_query(it["q"])
        hits = search(it["q"], doc_ids=list(ctx.doc_ids) or None, top_k=5)
        top = hits[0] if hits else None
        row = {"id": it["id"], "kind": it["kind"], "answerable": not it.get("expect_not_found", False),
               "top_score": round(top.rerank_score, 3) if top and top.rerank_score is not None else None,
               "top_doc": top.chunk["doc_id"] if top else None, "top_page": top.chunk["page"] if top else None,
               "scores": [round(h.rerank_score, 2) for h in hits], "seconds": round(time.time() - t, 1)}
        rows.append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    (ROOT / "eval" / "rerank_skorlari.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
