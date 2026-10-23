"""Kayıp analizi: Beklenen parça aday listesine (ilk 20) neden girmiyor? Yalnız bulgu üretir, hiçbir ayarı değiştirmez.

Kullanım: python -m bench.loss questions_ek:Q27 sekil_sorular:N1 sekil_sorular:N2
Her soru için: beklenen parçaların dense ve sparse kollardaki sırası (filtreli, ilk 500), RRF sırası, parça türü ve
embed_text'i, iki kolun ilk 3 rakibi. Çıktı: eval/bench/kayip_<tarih>.json ve .md
"""
import sys
import warnings
from typing import Any

from bench.common import is_match, load_questions, meta, prepare, write_result

warnings.filterwarnings("ignore")
DEEP = 500


def arm_ranks(qc, query_vec, using: str, flt, limit: int = DEEP) -> list[tuple[int, dict[str, Any], float]]:
    from pilot.config import COLLECTION
    res = qc.query_points(COLLECTION, query=query_vec, using=using, query_filter=flt, limit=limit, with_payload=True)
    return [(i + 1, p.payload, p.score) for i, p in enumerate(res.points)]


def analyze(qid: str) -> dict[str, Any]:
    from qdrant_client import models

    from pilot.chunk import read_chunks
    from pilot.embed import embed
    from pilot.index import release, search_client
    from pilot.retrieve import PREFETCH_K, _filter, is_toc

    item = next(it for it in load_questions(["questions", "questions_ek", "sekil_sorular"]) if it["qid"] == qid)
    p = prepare(item["q"])
    expected = [c for c in read_chunks() if is_match(c, item)]
    v = embed([p["search_q"]])[0]
    sparse = models.SparseVector(indices=list(v["sparse"].keys()), values=list(v["sparse"].values()))
    out: dict[str, Any] = {"qid": qid, "q": item["q"], "search_q": p["search_q"], "doc_ids": p["doc_ids"],
                           "expect_pages": item.get("expect_pages"), "arms": {}}
    qc = search_client()
    try:
        for scope_name, scope in (("filtreli", p["doc_ids"]), ("filtresiz", None)):
            flt = _filter(None, scope)
            arms = {"dense": arm_ranks(qc, v["dense"], "dense", flt), "sparse": arm_ranks(qc, sparse, "sparse", flt)}
            # Gerçek RRF sırası: pipeline'daki hibrit sorgunun aynısı, aday sınırı olmadan (iki kolun PREFETCH_K'sı)
            from pilot.config import COLLECTION
            hyb = qc.query_points(
                COLLECTION, prefetch=[models.Prefetch(query=v["dense"], using="dense", filter=flt, limit=PREFETCH_K),
                                      models.Prefetch(query=sparse, using="sparse", filter=flt, limit=PREFETCH_K)],
                query=models.FusionQuery(fusion=models.Fusion.RRF), limit=2 * PREFETCH_K, with_payload=True)
            fused_order = [pt.payload["chunk_id"] for pt in hyb.points if not is_toc(pt.payload["text"])]
            res = {}
            for name, lst in arms.items():
                pos = {pl["chunk_id"]: (r, s) for r, pl, s in lst}
                res[name] = {"expected": {c["chunk_id"]: pos.get(c["chunk_id"], (None, None)) for c in expected},
                             "n_returned": len(lst),
                             "top3": [{"rank": r, "chunk_id": pl["chunk_id"], "pages": pl["pages"],
                                       "type": pl.get("chunk_type"), "score": round(s, 4), "toc": is_toc(pl["text"]),
                                       "text": pl["text"][:160]} for r, pl, s in lst[:3]]}
            res["rrf_rank"] = {c["chunk_id"]: (fused_order.index(c["chunk_id"]) + 1
                                               if c["chunk_id"] in fused_order else None) for c in expected}
            out["arms"][scope_name] = res
    finally:
        release(qc)
    out["expected"] = [{"chunk_id": c["chunk_id"], "type": c.get("chunk_type"), "pages": c["pages"],
                        "section": c.get("section"), "generated": c.get("generated"), "toc": is_toc(c["text"]),
                        "chars": len(c["embed_text"]), "embed_text": c["embed_text"][:700]} for c in expected]
    return out


def to_md(rows: list[dict[str, Any]], m: dict[str, Any]) -> str:
    lines = ["# Kayıp analizi: ilk 20 adaya girmeyen sorular", "",
             f"{m['date']} · commit `{m['git_commit']}` · kollar ilk {DEEP} sonuca kadar izlendi", ""]
    for r in rows:
        lines += [f"## {r['qid']}", "", f"Soru: {r['q']}", "", f"Arama sorgusu: `{r['search_q']}` · filtre: "
                  f"{r['doc_ids']} · beklenen sayfalar: {r['expect_pages']}", "",
                  "| Parça | tür | sayfa | dense (filtreli) | sparse (filtreli) | RRF (filtreli) | dense (filtresiz) "
                  "| sparse (filtresiz) |", "|---|---|---|---|---|---|---|---|"]
        for e in r["expected"]:
            cid = e["chunk_id"]

            def rk(scope, arm):
                x = r["arms"][scope][arm]["expected"][cid][0]
                return str(x) if x else f">{r['arms'][scope][arm]['n_returned']}"
            rrf = r["arms"]["filtreli"]["rrf_rank"][cid]
            lines.append(f"| `{cid}` | {e['type']} | {e['pages']} | {rk('filtreli', 'dense')} | "
                         f"{rk('filtreli', 'sparse')} | {rrf or '–'} | {rk('filtresiz', 'dense')} | "
                         f"{rk('filtresiz', 'sparse')} |")
        lines += ["", "Beklenen parçaların embed_text'i (ilk 700 karakter):", ""]
        for e in r["expected"]:
            txt = e["embed_text"].replace("\n", " ")
            lines.append(f"- `{e['chunk_id']}` ({e['type']}, {e['chars']} karakter"
                         f"{', içindekiler satırı' if e['toc'] else ''}): {txt}")
        lines += ["", "Kolların ilk 3 sonucu (filtreli):", ""]
        for arm in ("dense", "sparse"):
            for t in r["arms"]["filtreli"][arm]["top3"]:
                lines.append(f"- {arm} {t['rank']}. `{t['chunk_id']}` s.{t['pages']} ({t['type']}"
                             f"{', içindekiler' if t['toc'] else ''}): {t['text']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    qids = sys.argv[1:] or ["questions_ek:Q27", "sekil_sorular:N1", "sekil_sorular:N2"]
    from pilot.index import close_shared
    rows = [analyze(q) for q in qids]
    close_shared()          # paylaşılan istemci kapanışta değil burada kapansın (aksi halde __del__ uyarısı)
    m = meta({"qids": qids, "deep": DEEP})
    print(write_result("kayip", {"meta": m, "rows": rows}, to_md(rows, m)))
