"""Reranker koşularının (bench.rerank_bench compare) özeti: yol başına rerank'sız ve reranker sonrası hit@1/hit@5,
toplamda ve soru türüne göre; harcama.

Kullanım (Pilot klasöründe):
    python -m bench.rerank_report --name <ad> --runs "yol=<compare json>" ... [--config <yapılandırma>]
Reranker sonrası sıra: reranker sırası ile hibrit sıranın RRF birleşimi (B4 düzeltmesi), kayıtlı reranker skorlarından
bugünkü etiketlerle yeniden hesaplanır (etiket sonradan düzeltildiyse koşu anındaki rank_fused bayattır). Rerank'sız
sıra aynı aday dosyasından (RRF ilk 20). Onaysız soru içeren koşular "geçici, onaysız set" diye işaretlenir.
"""
import argparse
import json
from pathlib import Path
from typing import Any

from bench.candidate_report import KINDS, kind_of
from bench.common import accuracy, first_rank, fmt_pct, load_questions, meta, write_result
from pilot.retrieve import fused_order

K = 20


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--runs", nargs="+", required=True, help='"yol=compare_json"')
    ap.add_argument("--config", default=None, help="compare'deki yapılandırma (varsayılan: tek yapılandırma)")
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    runs = {r.split("=", 1)[0]: json.loads(Path(r.split("=", 1)[1]).read_text(encoding="utf-8")) for r in a.runs}
    cand_params = {k: v["meta"]["params"]["candidates"] for k, v in runs.items()}
    sets = sorted({s for p in cand_params.values() for s in p.get("sets", [])})
    unapproved = any(p.get("include_unapproved") for p in cand_params.values())
    items = {it["qid"]: it for it in load_questions(sets, include_unapproved=unapproved)}

    def config_of(r):
        return a.config or next(iter(r["configs"]))

    def candidates(path_key: str) -> dict[str, Any]:
        from bench.providers import CACHE_DIR      # providers içe aktarılırken global uyarı filtresini değiştirir
        tag = cand_params[path_key].get("tag") or ""
        return json.loads((CACHE_DIR / f"candidates_{tag}.json").read_text(encoding="utf-8"))["questions"]

    ranks: dict[str, dict[str, dict[str, dict[str, int | None]]]] = {}
    cost = {}
    for k, r in runs.items():
        cfg = r["configs"][config_of(r)]
        cands = candidates(k)
        ranks[k] = {}
        cost[k] = sum((x.get("cost_usd") or 0) for m in cfg.values() for x in m["rows"])
        for mode, v in cfg.items():
            rows = {x["qid"]: x for x in v["rows"] if not x["not_found"]}
            ranks[k][mode] = {"rerank'sız": {q: first_rank(cands[q][mode][:K], items[q]) for q in rows},
                              "reranker": {q: first_rank([cands[q][mode][j] for j in fused_order(x["scores"])],
                                                         items[q]) for q, x in rows.items()}}
    qids = sorted(set.intersection(*(set(ranks[k][m]["reranker"]) for k in ranks for m in ranks[k])))
    blocks = [("Toplam", qids)] + [(f"Tür: {t}", [q for q in qids if kind_of(items[q]) == t]) for t in KINDS]
    blocks = [(b, qs) for b, qs in blocks if qs]

    tmp = " — **geçici, onaysız set**" if unapproved else ""
    lines = [f"# {a.title or a.name}{tmp}", "",
             f"Aynı {len(qids)} cevaplı soru · aday listesi RRF ilk {K} · reranker: `{config_of(next(iter(runs.values())))}`, "
             "sıra = reranker sırası + hibrit sıra RRF birleşimi (B4 düzeltmesi)"
             + (" · onaysız sorular dahil, sayılar karar için kullanılmaz" if unapproved else ""), "",
             f"Harcama (reranker çağrıları, API'nin usage alanı): " +
             ", ".join(f"{k} {v:.3f} USD" for k, v in cost.items()) + f" · toplam {sum(cost.values()):.3f} USD", ""]
    data: dict[str, Any] = {"meta": meta({"runs": {k: str(v) for k, v in zip(runs, a.runs)}, "sets": sets,
                                          "unapproved": unapproved}), "questions": qids, "cost_usd": cost, "rows": {}}
    modes = [m for m in ("filtered", "unfiltered") if all(m in ranks[k] for k in ranks)]
    for mode in modes:
        heads = [f"{k}, {s}: hit@1 | hit@5" for k in ranks for s in ("rerank'sız", "reranker")]
        lines += [f"## {'Filtreli' if mode == 'filtered' else 'Filtresiz'}", "",
                  "| Küme | n | " + " | ".join(heads) + " |", "|---|---|" + "---|---|" * len(heads)]
        for b, qs in blocks:
            cells = []
            for k in ranks:
                for s in ("rerank'sız", "reranker"):
                    acc = accuracy([ranks[k][mode][s][q] for q in qs])
                    data["rows"][f"{mode}|{b}|{k}|{s}"] = acc
                    cells += [fmt_pct(acc["hit@1"]), fmt_pct(acc["hit@5"])]
            lines.append(f"| {b} | {len(qs)} | " + " | ".join(cells) + " |")
        lines.append("")
    print(write_result(a.name, data, "\n".join(lines) + "\n"))


if __name__ == "__main__":
    main()
