""""Hangi ürün/model?" koruması (pipeline.post_search_ambiguity): yanlış pozitif ve yanlış negatif sayısı.

Koruma yalnız kaynak belirtmeyen (filtresiz) sorularda çalışır: ilk 3 sonuç farklı ürün şartnamelerinden ya da aynı ailenin
modellerinden geliyorsa model çağrılmadan sorulur; sonuçlar alakasızsa (ilk skor < CLARIFY_MIN_SCORE) sorulmaz. Eşik
reranker skoruna bağlı; rerank kapalıyken (varsayılan) koruma çalışmaz. Açık kalan: eşik onaylı soru setiyle hibrit/RRF
skoruna göre yeniden ayarlanacak. Bu betik bugünkü durumu sayar ve o ayar için skor dağılımını kaydeder.

Kullanım (Pilot klasöründe; yol ortam değişkenleriyle seçilir, her yol ayrı süreçte):
    python -m bench.clarify_guard run --label yeni_varsayilan
    $env:PILOT_RERANK_PROVIDER="local"; $env:PILOT_SPARSE="bge-m3"; $env:PILOT_RERANK_PASSAGE="text"; `
      $env:PILOT_RERANK_FUSION="none"; python -m bench.clarify_guard run --label eski_rerank
    python -m bench.clarify_guard summary          # eval/bench/netlestirme_korumasi_<tarih>.md
Onaylı setler sayılır; --unverified ile eval/aday_sorular.json (onaysız) ayrıca, yalnız bilgi amaçlı.
"""
import argparse
import json
import warnings
from typing import Any

from bench.common import KNOWN_SETS, OUT_DIR, load_questions, meta, prepare, write_result

warnings.filterwarnings("ignore")
CACHE = OUT_DIR.parent.parent / "data" / "bench_cache"


def outcome(expected: bool, triggered: bool, not_found: bool) -> str:
    if expected and triggered:
        return "dogru_netlestirme"
    if expected:
        return "yanlis_negatif"
    if triggered:
        return "yanlis_pozitif_alakasiz" if not_found else "yanlis_pozitif"
    return "dogru_gecis"


def run(label: str, unverified: bool) -> None:
    from pilot import config, retrieve
    from pilot.config import TOP_K_SOURCES
    from pilot.pipeline import code_lookup, post_search_ambiguity
    from pilot.retrieve import Hit

    sets: list[tuple[str, list[dict[str, Any]]]] = [("onayli", load_questions(KNOWN_SETS))]
    if unverified:
        items = json.loads((OUT_DIR.parent / "aday_sorular.json").read_text(encoding="utf-8"))
        sets.append(("aday_onaysiz", [{**it, "set": "aday", "qid": f"aday:{it['id']}"} for it in items]))
    rows = []
    for group, items in sets:
        for it in items:
            p = prepare(it["q"])
            if p["skip"] or p["doc_ids"]:
                continue                     # netleştirme aramadan önce (varlık) ya da kaynak belli: koruma çalışmaz
            hits = retrieve.search(p["search_q"], top_k=TOP_K_SOURCES)
            found, _, _ = code_lookup(it["q"], None, None)
            if found:
                have = {h.chunk["chunk_id"] for h in hits}
                hits = ([Hit(c, -1, None) for c in found if c["chunk_id"] not in have] + hits)[:TOP_K_SOURCES]
            amb = post_search_ambiguity(hits) if hits else None
            rows.append({"group": group, "qid": it["qid"], "q": it["q"], "expected": bool(it.get("expect_clarify")),
                         "not_found": bool(it.get("expect_not_found")), "triggered": bool(amb),
                         "offered": amb[1] if amb else [], "top_docs": [h.chunk["doc_id"] for h in hits[:3]],
                         "top_score": hits[0].rerank_score if hits else None,
                         "outcome": outcome(bool(it.get("expect_clarify")), bool(amb), bool(it.get("expect_not_found")))})
            print(group, it["qid"], rows[-1]["outcome"], rows[-1]["top_docs"], rows[-1]["top_score"], flush=True)
    from pilot.index import close_shared
    close_shared()
    params = {"label": label, "rerank": config.RERANK_PROVIDER, "sparse": config.SPARSE_KIND,
              "passage": config.RERANK_PASSAGE, "fusion": config.RERANK_FUSION, "clarify_min_score": config.CLARIFY_MIN_SCORE}
    CACHE.mkdir(parents=True, exist_ok=True)
    (CACHE / f"clarify_guard_{label}.json").write_text(json.dumps({"params": params, "rows": rows}, ensure_ascii=False,
                                                                  indent=1, default=float), encoding="utf-8")


def counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    out = {k: 0 for k in ("dogru_netlestirme", "yanlis_negatif", "yanlis_pozitif", "yanlis_pozitif_alakasiz", "dogru_gecis")}
    for r in rows:
        out[r["outcome"]] += 1
    return out


def summary() -> None:
    runs = [json.loads(f.read_text(encoding="utf-8")) for f in sorted(CACHE.glob("clarify_guard_*.json"))]
    lines = ['# "Hangi ürün/model?" koruması: yanlış pozitif ve negatif', "",
             "Yalnız kaynak belirtmeyen sorular (koruma yalnız bunlarda çalışır). Yanlış pozitif: netleştirme beklenmiyordu ama "
             "soruldu ('alakasız': cevabı olmayan soruda soruldu; koruma tam bunu önlemek içindi, Q10). Yanlış negatif: "
             "netleştirme bekleniyordu ama sorulmadı. Açık kalan: eşik onaylı soru setiyle hibrit/RRF skoruna göre "
             "yeniden ayarlanacak.", ""]
    for group, title in (("onayli", "Onaylı setler (bilinen 36 + bulunamadı soruları)"),
                         ("aday_onaysiz", "Aday taslak (onaysız; yalnız bilgi amaçlı, karar için kullanılmaz)")):
        lines += [f"## {title}", "", "| Yol | soru | doğru netleştirme | yanlış negatif | yanlış pozitif | yanlış pozitif (alakasız) | doğru geçiş |",
                  "|---|---|---|---|---|---|---|"]
        for r in runs:
            rows = [x for x in r["rows"] if x["group"] == group]
            if not rows:
                continue
            c = counts(rows)
            p = r["params"]
            lines.append(f"| {p['label']} (rerank {p['rerank']}, sparse {p['sparse']}) | {len(rows)} | {c['dogru_netlestirme']} | "
                         f"{c['yanlis_negatif']} | {c['yanlis_pozitif']} | {c['yanlis_pozitif_alakasiz']} | {c['dogru_gecis']} |")
        lines.append("")
        for r in runs:
            bad = [x for x in r["rows"] if x["group"] == group and x["outcome"] not in ("dogru_netlestirme", "dogru_gecis")]
            if bad:
                lines += [f"{r['params']['label']}: " + "; ".join(
                    f"{x['qid']} {x['outcome']} (ilk 3: {', '.join(x['top_docs'])}; skor {x['top_score'] if x['top_score'] is None else round(x['top_score'], 2)})"
                    for x in bad), ""]
    print(write_result("netlestirme_korumasi", {"meta": meta({}), "runs": runs}, "\n".join(lines) + "\n"))
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--label", required=True)
    r.add_argument("--unverified", action="store_true")
    sub.add_parser("summary")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.label, a.unverified)
    else:
        summary()


if __name__ == "__main__":
    main()
