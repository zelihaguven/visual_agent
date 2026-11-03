"""256'lık ön elemenin (short_rescore) tam vektöre göre aday listesini nasıl değiştirdiği; aynı soru kümesinde.

Önce etikete bağlı olmayan ölçüler: her ön eleme ayarı (A) ile tam vektör (B) arasında ilk 20 aday örtüşmesi ve sıra
değişimleri. Sonra etiketli ölçüler (hit@k, ön elemenin düşürdüğü doğru parça); onaysız soru varsa "geçici" diye işaretli.

Kullanım (Pilot klasöründe): python -m bench.prefilter_diff --ref <B etiketi> --vs <A etiketleri...> [--extra <C etiketi>]
Girdi: data/bench_cache/candidates_<etiket>.json (bench.providers collect). Çıktı: eval/bench/b4/asama4_on_eleme_<tarih>.
"""
import argparse
import json
from statistics import mean
from typing import Any

from bench.common import accuracy, first_rank, fmt_pct, load_questions, meta, overlap_at_k, write_result
from bench.providers import CACHE_DIR

K = 20


def load(tag: str) -> dict[str, Any]:
    return json.loads((CACHE_DIR / f"candidates_{tag}.json").read_text(encoding="utf-8"))


def ids(chunks: list[dict[str, Any]]) -> list[str]:
    return [c["chunk_id"] for c in chunks[:K]]


def rank_shift(a: list[str], b: list[str]) -> float:
    """Ortak adayların sıra farkının ortalaması (0: ortak adaylar aynı sırada)."""
    common = set(a) & set(b)
    return mean(abs(a.index(c) - b.index(c)) for c in common) if common else 0.0


def label_free(ref: dict[str, Any], other: dict[str, Any], qids: list[str], mode: str) -> dict[str, Any]:
    rows = []
    for q in qids:
        a, b = ids(other["questions"][q][mode]), ids(ref["questions"][q][mode])
        rows.append({"qid": q, "overlap": overlap_at_k(a, b, K), "same_order": a == b, "top1_same": a[:1] == b[:1],
                     "top5_same_set": set(a[:5]) == set(b[:5]), "shift": rank_shift(a, b)})
    n = len(rows)
    return {"n": n, "overlap_mean": mean(r["overlap"] for r in rows) if n else float("nan"),
            "full_overlap": sum(r["overlap"] == 1.0 for r in rows), "same_order": sum(r["same_order"] for r in rows),
            "top1_same": sum(r["top1_same"] for r in rows), "top5_same_set": sum(r["top5_same_set"] for r in rows),
            "shift_mean": mean(r["shift"] for r in rows) if n else float("nan"),
            "changed": [r["qid"] for r in rows if not r["same_order"]]}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ref", required=True, help="tam vektör (B)")
    ap.add_argument("--vs", nargs="+", required=True, help="ön eleme ayarları (A)")
    ap.add_argument("--extra", nargs="*", default=[], help="yalnız etiketli ölçüye giren başka yollar (ör. bge-m3)")
    ap.add_argument("--name", default="asama4_on_eleme_10k")
    a = ap.parse_args()

    runs = {t: load(t) for t in [a.ref, *a.vs, *a.extra]}
    qids = sorted(set.intersection(*(set(r["questions"]) for r in runs.values())))
    sets = sorted({s for r in runs.values() for s in r["params"].get("sets", [])})
    unapproved = any(r["params"].get("include_unapproved") for r in runs.values())
    items = {it["qid"]: it for it in load_questions(sets, include_unapproved=unapproved)}
    answerable = [q for q in qids if not runs[a.ref]["questions"][q]["not_found"]]
    skipped = sorted({q for r in runs.values() for q in r.get("skipped_offline", [])})

    data: dict[str, Any] = {"meta": meta({"ref": a.ref, "vs": a.vs, "extra": a.extra, "sets": sets,
                                          "unapproved": unapproved, "params": {t: r["params"] for t, r in runs.items()}}),
                            "questions": qids, "skipped_offline": skipped, "label_free": {}, "accuracy": {},
                            "dropped": {}}
    for mode in ("filtered", "unfiltered"):
        for t in a.vs:
            data["label_free"][f"{t}|{mode}"] = label_free(runs[a.ref], runs[t], qids, mode)
        for t, r in runs.items():
            ranks = {q: first_rank(r["questions"][q][mode][:K], items[q]) for q in answerable}
            data["accuracy"][f"{t}|{mode}"] = {**accuracy(list(ranks.values())), "ranks": ranks}
        for t in a.vs:
            ref_r, oth_r = data["accuracy"][f"{a.ref}|{mode}"]["ranks"], data["accuracy"][f"{t}|{mode}"]["ranks"]
            data["dropped"][f"{t}|{mode}"] = [{"qid": q, "ref_rank": ref_r[q], "rank": oth_r[q]} for q in answerable
                                              if ref_r[q] is not None and oth_r[q] is None]

    tmp = " (**geçici, onaysız set**)" if unapproved else ""
    lines = [f"# 256'lık ön eleme ve tam vektör: aday listesi farkı ({a.name})", "",
             f"Koleksiyon: `{runs[a.ref]['params'].get('collection')}` · aday listesi: RRF ilk {K}, rerank'sız · "
             f"aynı {len(qids)} soru (cevabı olanlar: {len(answerable)}) · setler: {', '.join(sets)}"
             + (" · onaysız sorular dahil" if unapproved else ""), "",
             f"Önbellekte sorgu vektörü olmadığı için atlanan (bulut çağrısı yapılmadı): {len(skipped)} soru"
             + (f": {', '.join(skipped)}" if skipped else ""), "",
             "## 1. Etikete bağlı olmayan: ön eleme (A) ile tam vektör (B) arasındaki fark", "",
             f"B = `{a.ref}`. Ön elemeden geçen aday sayısı: (PREFETCH_K + 10) × SHORT_OVERSAMPLE.", ""]
    for mode, title in (("filtered", "Filtreli"), ("unfiltered", "Filtresiz")):
        lines += [f"### {title}", "",
                  "| A | ön elemeden geçen | ilk 20 örtüşme (ort.) | tam örtüşen soru | sırası aynı | ilk sıra aynı | "
                  "ilk 5 kümesi aynı | ortak adaylarda ort. sıra farkı |", "|---|---|---|---|---|---|---|---|"]
        for t in a.vs:
            s = data["label_free"][f"{t}|{mode}"]
            p = runs[t]["params"]
            n_pre = int((p.get("PREFETCH_K", 30) + 10) * p.get("SHORT_OVERSAMPLE", 4))
            lines.append(f"| `{t}` | {n_pre} | {fmt_pct(s['overlap_mean'])} | {s['full_overlap']}/{s['n']} | "
                         f"{s['same_order']}/{s['n']} | {s['top1_same']}/{s['n']} | {s['top5_same_set']}/{s['n']} | "
                         f"{fmt_pct(s['shift_mean'])} |")
        for t in a.vs:
            ch = data["label_free"][f"{t}|{mode}"]["changed"]
            lines.append(f"\n`{t}` sırası değişen sorular ({len(ch)}): {', '.join(ch) if ch else '–'}")
        lines.append("")
    lines += [f"## 2. Etiketli{tmp}", "",
              "Beklenen sayfa etiketleri" + (" onaysız taslaktan; sayılar karar için kullanılmaz." if unapproved
                                              else " onaylı setlerden."), ""]
    for mode, title in (("filtered", "Filtreli"), ("unfiltered", "Filtresiz")):
        lines += [f"### {title}", "", "| Yol | n | hit@1 | hit@5 | hit@20 | MRR |", "|---|---|---|---|---|---|"]
        for t in runs:
            s = data["accuracy"][f"{t}|{mode}"]
            lines.append(f"| `{t}` | {s['n']} | {fmt_pct(s['hit@1'])} | {fmt_pct(s['hit@5'])} | {fmt_pct(s['hit@20'])} | "
                         f"{fmt_pct(s['mrr'])} |")
        lines.append("")
        for t in a.vs:
            d = data["dropped"][f"{t}|{mode}"]
            lines.append(f"Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `{t}`: "
                         + (", ".join(f"{x['qid']} (B'de {x['ref_rank']}.)" for x in d) if d else "yok"))
        lines.append("")
    print(write_result(a.name, data, "\n".join(lines) + "\n"))


if __name__ == "__main__":
    main()
