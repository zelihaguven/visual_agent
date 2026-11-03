"""Reranker neden zarar veriyor? Aşama 4 rerank sonuçlarından soru bazında teşhis (yeni çağrı yapmaz, model yüklemez
yalnız tokenizer).

Kullanım: python -m bench.rerank_diag qwen3-8b_full [bge-m3-local-bm25_full ...]
Her aday kümesi ve reranker için: rerank'ın hit@1'i bozduğu ve düzelttiği sorular (doğru parça önce/sonra kaçıncı, öne
alınan parça hangisi, aynı doküman mı), reranker'a giden metnin token uzunluğu ve kesilip kesilmediği (max_length),
metinde doküman/bölüm başlığı olup olmadığı. Çıktı: eval/bench/b4/rerank_teshis2_<tarih>.md
"""
import json
import sys
from pathlib import Path
from typing import Any

from bench.common import KNOWN_SETS, first_rank, load_questions, meta, stage_dir, write_result
from bench.rerank_bench import ranked_rank

CACHE = Path(__file__).resolve().parent.parent / "data" / "bench_cache"


def token_lengths(texts: list[str], query: str, model: str = "BAAI/bge-reranker-v2-m3") -> list[int]:
    from transformers import AutoTokenizer
    tok = _tok(model)
    return [len(tok(query, t, truncation=False)["input_ids"]) for t in texts]


_TOK: dict[str, Any] = {}


def _tok(model: str):
    if model not in _TOK:
        from transformers import AutoTokenizer
        _TOK[model] = AutoTokenizer.from_pretrained(model)
    return _TOK[model]


def analyze(key: str) -> tuple[list[str], dict[str, Any]]:
    from pilot.chunk import read_chunks
    chunks = {c["chunk_id"]: c for c in read_chunks()}
    cands = json.loads((CACHE / f"candidates_{key}.json").read_text(encoding="utf-8"))["questions"]
    res = json.loads(next(stage_dir("asama4_rerank").glob(f"asama4_rerank_{key}_*.json")).read_text(encoding="utf-8"))
    items = {it["qid"]: it for it in load_questions(KNOWN_SETS)}
    lines = [f"## {key}", ""]
    stats: dict[str, Any] = {}
    # metin uzunluğu ve kesilme (bge-v2-m3 tokenizer, soru + parça)
    all_len, cut512 = [], 0
    for q in cands.values():
        for mode in ("filtered", "unfiltered"):
            lens = token_lengths([x["text"] for x in q[mode]], q["search_q"])
            all_len += lens
            cut512 += sum(1 for n in lens if n > 512)
    has_header = sum(1 for q in cands.values() for x in q["unfiltered"]
                     if chunks.get(x["chunk_id"], {}).get("embed_text", "").startswith(x["text"][:20]))
    stats["tokens"] = {"n": len(all_len), "p50": sorted(all_len)[len(all_len) // 2], "max": max(all_len),
                       "over_512": cut512}
    lines += [f"Reranker'a giden metin (soru + parça, bge-v2-m3 tokenizer): {len(all_len)} çift, medyan "
              f"{stats['tokens']['p50']} token, en uzun {stats['tokens']['max']}; **512'yi aşan (kesilen): {cut512}** "
              f"(%{100 * cut512 / len(all_len):.0f}). Parça metninde doküman/bölüm başlığı yok (`text`); embedding "
              f"başlıklı metinle (`embed_text`) yapılıyor.", ""]
    for spec, by_mode in res["configs"].items():
        for mode in ("filtered", "unfiltered"):
            rows = by_mode[mode]["rows"]
            lost, gained = [], []
            for r in rows:
                if r["not_found"]:
                    continue
                q = cands[r["qid"]]
                before = first_rank(q[mode], items[r["qid"]])
                after = r["rank"]["20"]
                if before == 1 and after != 1:
                    order = sorted(range(len(r["scores"])), key=lambda i: -r["scores"][i])
                    top = q[mode][order[0]]
                    exp_doc = items[r["qid"]]["expect_docs"][0]
                    lost.append((r["qid"], before, after, top, top["doc_id"] == exp_doc))
                elif before != 1 and after == 1:
                    gained.append((r["qid"], before))
            name = spec.split(":")[1].split("/")[-1] + (" int8" if "int8" in spec else "")
            same_doc = sum(1 for x in lost if x[4])
            stats[f"{name}|{mode}"] = {"lost": len(lost), "gained": len(gained), "lost_same_doc": same_doc}
            lines += [f"### {name} · {'filtreli' if mode == 'filtered' else 'filtresiz'}: hit@1 kaybı {len(lost)}, "
                      f"kazancı {len(gained)} (kayıpların {same_doc}'i aynı dokümanın başka parçasını öne aldı, "
                      f"{len(lost) - same_doc}'i başka dokümanı)", ""]
            for qid, b, a, top, same in lost:
                ch = chunks.get(top["chunk_id"], {})
                lines.append(f"- {qid}: doğru parça 1. → {a or '>20'}. · öne alınan `{top['chunk_id']}` "
                             f"({'aynı doküman' if same else 'BAŞKA doküman'}, s.{top['pages']}, bölüm "
                             f"'{ch.get('section', '')[:40]}'): {' '.join(top['text'].split())[:110]}")
            if gained:
                lines.append("- düzelttikleri: " + ", ".join(f"{q} ({b or '>20'}. → 1.)" for q, b in gained))
            lines.append("")
    return lines, stats


def main(keys: list[str]) -> None:
    lines = ["# Reranker teşhisi: hit@1'i neden bozuyor?", "",
             "Aşama 4 rerank sonuçları üzerinden (yeni çağrı yok). 'Doğru parça': soru setindeki beklenen doküman+sayfa.", ""]
    stats = {}
    for k in keys:
        l, s = analyze(k)
        lines += l
        stats[k] = s
    print(write_result("rerank_teshis2", {"meta": meta({"keys": keys}), "stats": stats}, "\n".join(lines) + "\n"))
    print("\n".join(x for x in lines if x.startswith(("###", "Reranker'a"))))


if __name__ == "__main__":
    main(sys.argv[1:] or ["qwen3-8b_full", "bge-m3-local-bm25_full", "te3-large_full"])
