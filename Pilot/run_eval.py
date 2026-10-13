"""Pilot ölçümü: eval/questions.json -> eval/sonuc.md (doğru kaynak, değer, reddetme, süre)."""
import json
import logging
import time
import warnings
from pathlib import Path

from pilot.pipeline import soru_cevapla

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING)
HERE = Path(__file__).parent / "eval"


def judge(item: dict, res) -> dict:
    ans = res.answer
    pages = {(h.chunk["doc_id"], p) for h in res.hits for p in h.chunk["pages"]}
    docs = {h.chunk["doc_id"] for h in res.hits}
    out = {"refused": bool(ans.get("bulunamadi")), "status": res.verification.status}
    if item.get("expect_not_found"):
        out["correct"] = out["refused"]
        return out
    if item.get("expect_clarify") or res.verification.status == "clarify":
        # Netleştirme: beklenmişse seçenekler beklenen kaynakları kapsamalı; beklenmemişse yanlış (gereksiz soru)
        offered = {o.get("doc_id") for o in ans.get("secenekler", [])}
        out["clarify_ok"] = res.verification.status == "clarify" and set(item["expect_docs"]) <= offered
        out["correct"] = bool(item.get("expect_clarify")) and out["clarify_ok"]
        return out
    out["source_hit"] = any((d, p) in pages for d in item["expect_docs"] for p in item["expect_pages"])
    out["wrong_doc_in_sources"] = bool(set(item.get("forbid_docs", [])) & docs)
    text = ans.get("cevap", "") + " " + res.speech_text
    out["value_ok"] = all(s in text for s in item["expect_in_answer"]) if item["expect_in_answer"] else None
    out["correct"] = (out["source_hit"] and not out["refused"] and out["value_ok"] is not False
                      and not out["wrong_doc_in_sources"] and out["status"] != "failed")
    return out


if __name__ == "__main__":
    items = json.loads((HERE / "questions.json").read_text(encoding="utf-8"))
    rows, raw = [], []
    for it in items:
        t = time.time()
        res = soru_cevapla(it["q"])
        j = judge(it, res)
        rows.append((it, res, j, time.time() - t))
        raw.append({"id": it["id"], "judge": j, "answer": res.answer, "speech": res.speech_text,
                    "problems": res.verification.problems, "timings": res.timings,
                    "sources": [(h.chunk["doc_id"], h.chunk["pages"], round(h.rerank_score or 0, 2)) for h in res.hits]})
        print(it["id"], "✔" if j["correct"] else "✖", f"{rows[-1][3]:.1f} sn", flush=True)
    (HERE / "sonuc.json").write_text(json.dumps(raw, ensure_ascii=False, indent=1), encoding="utf-8")

    n = len(rows)
    lines = ["# Pilot ölçüm sonucu", "",
             f"Soru sayısı: {n} · Model: kurulumdaki `PILOT_LLM_MODEL` · Arama: hibrit + reranker (CPU)", "",
             "| # | Tür | Soru | Doğru | Doğrulama | Süre | Not |", "|---|-----|------|-------|-----------|------|-----|"]
    for it, res, j, dt in rows:
        note = "; ".join(res.verification.problems)[:110].replace("|", "/")
        lines.append(f"| {it['id']} | {it['kind']} | {it['q']} | {'✔' if j['correct'] else '✖'} | "
                     f"{res.verification.badge} | {dt:.0f} sn | {note} |")
    ok = sum(1 for _, _, j, _ in rows if j["correct"])
    lines += ["", f"**Doğru: {ok}/{n}** · Ortalama süre: {sum(r[3] for r in rows) / n:.1f} sn", ""]
    (HERE / "sonuc.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Doğru: {ok}/{n}")
