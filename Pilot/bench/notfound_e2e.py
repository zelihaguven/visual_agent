""""Bulunamadı" davranışı uçtan uca: cevabı olmayan sorular ne alıyor? (model dahil, soru_cevapla)

Kullanım (Pilot klasöründe, Ollama açık; yol ortam değişkenleriyle, her yol ayrı süreçte):
    python -m bench.notfound_e2e run --label yeni_varsayilan
    $env:PILOT_RERANK_PROVIDER="local"; $env:PILOT_SPARSE="bge-m3"; $env:PILOT_RERANK_PASSAGE="text"; `
      $env:PILOT_RERANK_FUSION="none"; python -m bench.notfound_e2e run --label eski_rerank
    python -m bench.notfound_e2e summary         # eval/bench/bulunamadi_e2e_<tarih>.md
Sorular: onaylı setlerin expect_not_found soruları + aday taslağın (onaysız) bulunamadı soruları.
Çıkış noktası: yabanci_marka | kod_yok | kaynak_uyumsuz | skor_esigi | model_bulunamadi | model_cevap (cevap üretti:
yanlış) | netlestirme. Kaldığı yerden sürer (aynı etiketle yeniden çalıştırınca biten sorular atlanır).
"""
import argparse
import json
import time
import warnings
from typing import Any

from bench.common import KNOWN_SETS, OUT_DIR, load_questions, meta, write_result

warnings.filterwarnings("ignore")
CACHE = OUT_DIR.parent.parent / "data" / "bench_cache"


def exit_point(res) -> str:
    ans = res.answer
    reason = (ans.get("neden") or ans.get("reason") or "") + " " + " ".join(res.verification.problems or [])
    if res.verification.status == "clarify":
        return "netlestirme"
    if ans.get("bulunamadi"):
        if not res.llm_called:
            if "marka" in reason:
                return "yabanci_marka"
            if "kodu" in reason or "kod" in reason:
                return "kod_yok"
            if "Seçilen kaynak" in reason:
                return "kaynak_uyumsuz"
            return "skor_esigi"
        return "model_bulunamadi"
    return "model_cevap"


def questions() -> list[dict[str, Any]]:
    out = [it for it in load_questions(KNOWN_SETS) if it.get("expect_not_found")]
    aday = json.loads((OUT_DIR.parent / "aday_sorular.json").read_text(encoding="utf-8"))
    out += [{**it, "set": "aday", "qid": f"aday:{it['id']}"} for it in aday if it.get("expect_not_found")]
    return out


def run(label: str) -> None:
    from pilot import config
    from pilot.pipeline import soru_cevapla

    path = CACHE / f"notfound_e2e_{label}.json"
    done = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"rows": []}
    have = {r["qid"] for r in done["rows"]}
    done["params"] = {"label": label, "rerank": config.RERANK_PROVIDER, "sparse": config.SPARSE_KIND,
                      "passage": config.RERANK_PASSAGE, "fusion": config.RERANK_FUSION, "llm": config.LLM_MODEL,
                      "min_rerank_score": config.MIN_RERANK_SCORE}
    for it in questions():
        if it["qid"] in have:
            continue
        t = time.time()
        res = soru_cevapla(it["q"])
        row = {"qid": it["qid"], "set": it["set"], "q": it["q"], "exit": exit_point(res), "llm_called": res.llm_called,
               "bulunamadi": bool(res.answer.get("bulunamadi")), "cevap": (res.answer.get("cevap") or "")[:400],
               "neden": res.answer.get("neden") or res.answer.get("reason") or "", "badge": res.verification.badge,
               "top3": [{"doc": h.chunk["doc_id"], "pages": h.chunk["pages"], "rerank": h.rerank_score,
                         "fused": h.fused_score} for h in res.hits[:3]],
               "seconds": round(time.time() - t, 1)}
        done["rows"].append(row)
        path.write_text(json.dumps(done, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
        print(it["qid"], row["exit"], [x["doc"] for x in row["top3"]], f"{row['seconds']} sn", flush=True)
    from pilot.index import close_shared
    close_shared()


def summary() -> None:
    runs = {json.loads(f.read_text(encoding="utf-8"))["params"]["label"]: json.loads(f.read_text(encoding="utf-8"))
            for f in sorted(CACHE.glob("notfound_e2e_*.json"))}
    labels = list(runs)
    # Yalnız bugün hâlâ cevapsız etiketli sorular (ör. Q09 sonradan olumlu soruya çevrildi; satırı ham kayıtta kalır)
    current = {it["qid"] for it in questions()}
    dropped = sorted({r["qid"] for lb in labels for r in runs[lb]["rows"]} - current)
    for lb in labels:
        runs[lb] = {**runs[lb], "rows": [r for r in runs[lb]["rows"] if r["qid"] in current]}
    ok = {"yabanci_marka", "kod_yok", "kaynak_uyumsuz", "skor_esigi", "model_bulunamadi"}
    trusted = {"✔ Doğrulandı", "⚠ Kısmen doğrulandı"}       # yanlış cevap güvenilir görünüyor (K1: 0 olmalı)
    lines = ['# "Bulunamadı" davranışı uçtan uca', "",
             "Cevabı olmayan sorular tam hattan geçirildi (model dahil). Doğru: herhangi bir 'bulunamadı' çıkışı. Yanlış: model "
             "alakasız kaynaktan cevap üretti (`model_cevap`) ya da gereksiz netleştirme. Skor: rerank açıkken reranker, "
             "kapalıyken RRF (hibrit). Onaylı sorular ve aday taslak (onaysız) ayrı."
             + (f" Sonradan cevaplı sayılıp çıkarılan: {', '.join(dropped)}." if dropped else ""), "",
             "| Yol | soru | doğru 'bulunamadı' | oran | model cevap üretti | … doğrulanmış görünen | netleştirme | çıkışlar |",
             "|---|---|---|---|---|---|---|---|"]
    for lb in labels:
        rows = runs[lb]["rows"]
        ex: dict[str, int] = {}
        for r in rows:
            ex[r["exit"]] = ex.get(r["exit"], 0) + 1
        good = sum(v for k, v in ex.items() if k in ok)
        shown = sum(r["exit"] == "model_cevap" and r["badge"] in trusted for r in rows)
        lines.append(f"| {lb} | {len(rows)} | {good} | {good / max(len(rows), 1):.0%} | {ex.get('model_cevap', 0)} | "
                     f"{shown} | {ex.get('netlestirme', 0)} | " + ", ".join(f"{k} {v}" for k, v in sorted(ex.items())) + " |")
    lines += ["", "## Soru soru", "", "| Soru | " + " | ".join(labels) + " | ilk 3 kaynak (skor) — " + labels[0] + " |",
              "|---|" + "---|" * len(labels) + "---|"]
    by = {lb: {r["qid"]: r for r in runs[lb]["rows"]} for lb in labels}
    for qid in by[labels[0]]:
        r0 = by[labels[0]][qid]

        def sc(x):
            v = x["rerank"] if x["rerank"] is not None else x["fused"]
            return "–" if v is None else f"{v:.2f}"
        top = "; ".join(f"{x['doc']} s.{x['pages']} ({sc(x)})" for x in r0["top3"]) or "arama yok"
        cells = []
        for lb in labels:
            r = by[lb].get(qid)
            cells.append("–" if not r else r["exit"] + (f" ({r['badge']}): {r['cevap'][:90]}" if r["exit"] == "model_cevap"
                                                     else ""))
        lines.append(f"| {qid} {r0['q'][:60]} | " + " | ".join(c.replace("|", "/") for c in cells) + f" | {top} |")
    print(write_result("bulunamadi_e2e", {"meta": meta({}), "runs": runs}, "\n".join(lines) + "\n"))
    print("\n".join(lines[:12]))


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--label", required=True)
    sub.add_parser("summary")
    a = ap.parse_args()
    run(a.label) if a.cmd == "run" else summary()


if __name__ == "__main__":
    main()
