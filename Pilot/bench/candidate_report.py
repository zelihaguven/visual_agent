"""Aday listelerinden (bench.providers collect) rerank'sız hit@1/hit@5: toplamda, soru türüne göre ve alt kümelerde.

Kullanım (Pilot klasöründe):
    python -m bench.candidate_report --name <ad> --runs "yol=önce:tag1,sonra:tag2" ... [--subset "ad=qids.json"] ...
Her --runs bir satır grubudur (ör. bir yolun önce/sonra hali); hepsi aynı soru kesişiminde ölçülür.
Onaysız soru içeren koşular "geçici, onaysız set" diye işaretlenir. Çıktı: write_result (adın önekine göre klasör).
"""
import argparse
import json
from pathlib import Path
from typing import Any

from bench.common import accuracy, first_rank, fmt_pct, load_questions, meta, write_result

K = 20
KINDS = ("değer", "prosedür", "kod", "arıza", "şekil", "diğer")


def kind_of(it: dict[str, Any]) -> str:
    """Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', gerisi 'diğer'."""
    k = (it.get("kind") or "").lower()
    if it.get("set") == "sekil_sorular" or "görsel" in k or k == "şekil":
        return "şekil"
    return k if k in KINDS else "diğer"


def load(tag: str) -> dict[str, Any]:
    from bench.providers import CACHE_DIR      # providers içe aktarılırken global uyarı filtresini değiştirir
    return json.loads((CACHE_DIR / f"candidates_{tag}.json").read_text(encoding="utf-8"))


def hits(run: dict[str, Any], items: dict[str, dict[str, Any]], qids: list[str], mode: str) -> dict[str, Any]:
    return accuracy([first_rank(run["questions"][q][mode][:K], items[q]) for q in qids])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--name", required=True)
    ap.add_argument("--runs", nargs="+", required=True, help='"yol=sütun:tag,..." (tag: candidates_<tag>.json)')
    ap.add_argument("--subset", nargs="*", default=[], help='"ad=dosya.json" (qid listesi)')
    ap.add_argument("--title", default="")
    a = ap.parse_args()

    groups = [(g.split("=", 1)[0], [tuple(x.split(":", 1)) for x in g.split("=", 1)[1].split(",")]) for g in a.runs]
    runs = {t: load(t) for _, cols in groups for _, t in cols}
    sets = sorted({s for r in runs.values() for s in r["params"].get("sets", [])})
    unapproved = any(r["params"].get("include_unapproved") for r in runs.values())
    items = {it["qid"]: it for it in load_questions(sets, include_unapproved=unapproved)}
    qids = sorted(set.intersection(*(set(r["questions"]) for r in runs.values())))
    qids = [q for q in qids if not items[q].get("expect_not_found")]
    subsets = {s.split("=", 1)[0]: [q for q in json.loads(Path(s.split("=", 1)[1]).read_text(encoding="utf-8"))
                                    if q in qids] for s in a.subset}
    by_kind = {k: [q for q in qids if kind_of(items[q]) == k] for k in KINDS}

    tmp = " — **geçici, onaysız set**" if unapproved else ""
    data: dict[str, Any] = {"meta": meta({"runs": {g: dict(c) for g, c in groups}, "sets": sets,
                                          "unapproved": unapproved}),
                            "questions": qids, "subsets": subsets, "rows": {}}
    lines = [f"# {a.title or a.name}{tmp}", "",
             f"Aday listesi: RRF ilk {K}, rerank'sız · aynı {len(qids)} cevaplı soru · setler: {', '.join(sets)}"
             + (" · onaysız sorular dahil, sayılar karar için kullanılmaz" if unapproved else ""), "",
             "Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', "
             "türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.", ""]
    blocks = [("Toplam", qids)] + [(f"Tür: {k}", v) for k, v in by_kind.items() if v] + \
             [(f"Alt küme: {n}", v) for n, v in subsets.items()]
    for mode, mtitle in (("filtered", "Filtreli"), ("unfiltered", "Filtresiz")):
        heads = [f"{g}, {col}: hit@1 | hit@5" for g, cols in groups for col, _ in cols]
        lines += [f"## {mtitle}", "", "| Küme | n | " + " | ".join(heads) + " |",
                  "|---|---|" + "---|---|" * len(heads)]
        for btitle, qs in blocks:
            cells = []
            for g, cols in groups:
                for _, t in cols:
                    s = hits(runs[t], items, qs, mode)
                    data["rows"][f"{mode}|{btitle}|{t}"] = s
                    cells += [fmt_pct(s["hit@1"]), fmt_pct(s["hit@5"])]
            lines.append(f"| {btitle} | {len(qs)} | " + " | ".join(cells) + " |")
        lines.append("")
    lines += ["Koşular: " + "; ".join(f"{g}: " + ", ".join(f"{c} `{t}`" for c, t in cols) for g, cols in groups), ""]
    print(write_result(a.name, data, "\n".join(lines) + "\n"))


if __name__ == "__main__":
    main()
