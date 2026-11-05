"""İlke dışı kurallar bayrağı (PILOT_DOC_SPECIFIC_RULES: BRAND_ALIASES, "s7300" aile grubu, ASPECTS/DETAIL_HINT) açık/kapalı
farkı, iki arama yolunda: varsayılan (bge-m3 + BM25) ve dondurulan aday (Qwen3-8B + bge-m3 + çevirili BM25), 10k, rerank'sız.

Ölçülen: hattın karar katmanı (pipeline.soru_cevapla'nın kendisi; model çağrılmaz) ve arama isabeti. soru_cevapla'daki
search, seçilen yolun üçlü füzyon kodu (bench.triple_fusion.fuse, aynı koleksiyonlar ve ayarlar) ile değiştirilir; cevap
modeline gelindiğinde durulur ("model" çıkışı). Kural çıkışları (yabancı marka, netleştirme, konu belirsiz, kod yok,
arama sonrası netleştirme) model çıkışlarından ayrı sayılır. Bayrak her soru için açık ve kapalı iki kez.

Sorgu vektörü ve çeviri önbellekten; kapalı/açık durumda ilk kez aranan soru varsa bulut çağrısıyla tamamlanır (ZDR,
--max-usd). 10k koleksiyonundaki kayıt dışı (dikkat dağıtıcı) dokümanlar karar katmanında "kayıt dışı" tür sayılır.

Kullanım (Pilot klasöründe, Qdrant sunucusu açık):
    python -m bench.doc_rules_diff --translations data/bench_cache/ceviri_gemma3_12b_bayrak.json
"""
import argparse
import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any

from bench.common import KNOWN_SETS, accuracy, first_rank, fmt_pct, load_questions, meta, write_result

log = logging.getLogger("bench")

PATHS = {"varsayilan": "Varsayılan: bge-m3 + BM25", "aday": "Aday: Qwen3-8B + bge-m3 + çevirili BM25"}


class ModelReached(Exception):
    """Hat cevap modeline geldi (kural çıkışı yok)."""


class _Registry(dict):
    def __missing__(self, key: str) -> Any:            # 10k dikkat dağıtıcıları kayıtta yok
        from pilot.registry import DocMeta
        return DocMeta(key, "", "", "", "kayit_disi")


def outcome(res: Any) -> str:
    """soru_cevapla sonucu → kural çıkışı adı (model çağrılmadan dönen)."""
    a, why = res.answer, (res.answer.get("neden") or "")
    if res.verification.status == "clarify":
        if res.hits:
            return "netlestirme_sonra"                   # arama sonrası: ürünler / aynı ailenin modelleri
        doc_options = any("doc_id" in o for o in a.get("secenekler", []))
        return "netlestirme_once" if doc_options else "konu_belirsiz"
    if a.get("bulunamadi"):
        if "marka" in why and "doküman yok" in why:
            return "yabanci_marka"
        if "kodu" in why and "geçmiyor" in why:
            return "kod_yok"
        return "bulunamadi_diger"
    return "diger"


def main() -> None:
    from bench.providers import QueryEncoder, specs
    from bench.server import server_client
    from bench.triple_fusion import K_OUT, fuse
    from pilot import config, pipeline, retrieve
    from pilot.cloud import CloudChat
    from pilot.query import question_lang
    from pilot.retrieve import Hit
    from pilot.sparse import bm25_query
    from pilot.translate import bm25_text, target_languages, translate_query

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--translations", required=True)
    ap.add_argument("--qwen-collection", default="scale_qwen3_8b_10000")
    ap.add_argument("--bge-collection", default="scale_bge_m3_10000")
    ap.add_argument("--sets", nargs="+", default=list(KNOWN_SETS) + ["aday_sorular"])
    ap.add_argument("--max-usd", type=float, default=0.05)
    ap.add_argument("--name", default="asama4_ilke_bayragi_10k")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

    tr_path = Path(a.translations)
    tr = json.loads(tr_path.read_text(encoding="utf-8"))
    # Hattın kapsamıyla aranır: çevirinin "filtered" kaydı (hedef diller kapsamdan; kapsam yoksa bütün korpustan)
    by_text = {r["search_q"]: r["filtered"]["bm25"] for r in tr["questions"].values()}
    chat = None
    qwen, bge = QueryEncoder(specs()["qwen3-8b"], 256), QueryEncoder(specs()["bge-m3-local-bm25"], 256)
    qc = server_client()
    added: dict[str, str] = {}

    def bm25_for(search_q: str, doc_ids: list[str] | None) -> str:
        nonlocal chat
        if search_q not in by_text:                      # bu bayrak durumunda ilk kez aranan soru: çeviri (bulut)
            chat = chat or CloudChat(tr["params"]["model"])
            t = translate_query(search_q, question_lang(search_q), target_languages(doc_ids), chat)
            by_text[search_q] = added[search_q] = bm25_text(t, search_q)
        return by_text[search_q]

    state: dict[str, Any] = {}

    def search(query: str, *, brands=None, doc_ids=None, mode="hybrid", top_k=5, query_en=None, access=None):
        flt = retrieve._filter(brands, doc_ids, access)
        k = retrieve.PREFETCH_K
        bv = bge(query, True)
        if state["path"] == "aday":
            qv = qwen(query, True)
            sq = {**qv, "sparse": bm25_query(bm25_for(query, doc_ids))}
            arms = [retrieve.candidates(qc, qv, flt, "dense", collection=a.qwen_collection, dense_mode="short_rescore",
                                        short_dim=256, fused_k=k),
                    retrieve.candidates(qc, bv, flt, "dense", collection=a.bge_collection, dense_mode="full", fused_k=k),
                    retrieve.candidates(qc, sq, flt, "sparse", collection=a.qwen_collection, sparse_name="bm25",
                                        fused_k=k)]
        else:
            arms = [retrieve.candidates(qc, bv, flt, "dense", collection=a.bge_collection, dense_mode="full", fused_k=k),
                    retrieve.candidates(qc, bv, flt, "sparse", collection=a.bge_collection, sparse_name="bm25",
                                        fused_k=k)]
        pts = fuse(arms, K_OUT, retrieve.RRF_K)
        state["ranked"] = [p.payload for p in pts]
        return [Hit(p.payload, i) for i, p in enumerate(pts[:max(top_k, 1)])]

    def stop(_user: str) -> Any:
        raise ModelReached

    pipeline.search, pipeline.chat_json, pipeline.format_sources = search, stop, lambda hits: ""
    pipeline.BY_ID = _Registry(pipeline.BY_ID)

    qs = load_questions(a.sets, include_unapproved=True)
    rows: dict[str, dict[str, Any]] = {}
    for path in PATHS:
        state["path"] = path
        for flag in (False, True):
            config.DOC_SPECIFIC_RULES = flag
            for it in qs:
                state["ranked"] = None
                try:
                    out = outcome(pipeline.soru_cevapla(it["q"]))
                except ModelReached:
                    out = "model"
                ranked = state["ranked"]
                rows.setdefault(it["qid"], {"qid": it["qid"], "q": it["q"], "kind": it.get("kind", ""),
                                            "clarify": bool(it.get("expect_clarify")),
                                            "not_found": bool(it.get("expect_not_found")),
                                            "answered": bool(it.get("expect_docs") or it.get("kabul"))})
                rows[it["qid"]][f"{path}_{int(flag)}"] = {
                    "out": out, "rank": first_rank(ranked, it) if ranked is not None else None,
                    "searched": ranked is not None}
                cost = (chat.stats["cost_usd"] if chat else 0) + (qwen.cloud.stats["cost_usd"] if qwen.cloud else 0)
                if cost > a.max_usd:
                    raise SystemExit(f"harcama sınırı aşıldı: {cost}")
            log.info("%s bayrak=%d bitti", path, flag)
    qc.close()

    if added:                                            # yeni çeviriler sonraki koşular için kopyaya eklenir
        tr["params"].setdefault("bayrak_eklenen", {}).update(added)
        tr["questions"].update({f"metin:{q}": {"search_q": q, "filtered": {"bm25": b}} for q, b in added.items()})
        tr_path.write_text(json.dumps(tr, ensure_ascii=False, indent=1), encoding="utf-8")

    stats = {"chat": chat.stats if chat else None, "embed": qwen.cloud.stats if qwen.cloud else None,
             "eklenen_ceviri": list(added)}
    md = report(rows, stats, a)
    data = {"meta": meta({"translations": a.translations, "qwen": a.qwen_collection, "bge": a.bge_collection,
                          "sets": a.sets}), "stats": stats, "rows": rows}
    p = write_result(a.name, data, md)
    log.info("yazıldı: %s · %s", p, stats)


def report(rows: dict[str, dict[str, Any]], stats: dict[str, Any], a: argparse.Namespace) -> str:
    rs = list(rows.values())
    ans = [r for r in rs if r["answered"] and not r["clarify"] and not r["not_found"]]
    out = ["# İlke dışı kurallar bayrağı: açık / kapalı (10k, rerank'sız, geçici, onaysız set)", "",
           f"Bayrak: `PILOT_DOC_SPECIFIC_RULES` (varsayılan kapalı). Sorular: {len(rs)} (cevaplı {len(ans)}, "
           f"netleştirme beklenen {sum(r['clarify'] for r in rs)}, bulunamadı beklenen {sum(r['not_found'] for r in rs)}). "
           f"Hattın karar katmanı model çağrılmadan çalıştı; arama `{a.bge_collection}` / `{a.qwen_collection}`.", "",
           "## Arama isabeti (cevaplı sorular, hattın verdiği kapsamla)", "",
           "| Yol | Bayrak | aranan | hit@1 | hit@5 | modele ulaşan |", "|---|---|---|---|---|---|"]
    for path, title in PATHS.items():
        for flag in (0, 1):
            cells = [r[f"{path}_{flag}"] for r in ans]
            acc = accuracy([c["rank"] for c in cells if c["searched"]])
            out.append(f"| {title} | {'açık' if flag else 'kapalı'} | {acc['n']} | {fmt_pct(acc['hit@1'])} | "
                       f"{fmt_pct(acc['hit@5'])} | {sum(c['out'] == 'model' for c in cells)} |")
    out += ["", "Not: hit@k yalnız aranan sorular üzerinden (kural çıkışıyla aranmayan soru paydada yok).", "",
            "## Çıkışlar (bütün sorular)", ""]
    kinds = sorted({r[f"{p}_{f}"]["out"] for r in rs for p in PATHS for f in (0, 1)})
    out += ["| Yol | Bayrak | " + " | ".join(kinds) + " |", "|---|---|" + "---|" * len(kinds)]
    for path, title in PATHS.items():
        for flag in (0, 1):
            c = Counter(r[f"{path}_{flag}"]["out"] for r in rs)
            out.append(f"| {title} | {'açık' if flag else 'kapalı'} | " + " | ".join(str(c[k]) for k in kinds) + " |")
    out += ["", "## Beklenen davranış", "", "| Yol | Bayrak | netleştirme beklenen → netleştirme | "
            "bulunamadı beklenen → kural çıkışı |", "|---|---|---|---|"]
    for path, title in PATHS.items():
        for flag in (0, 1):
            cl = [r for r in rs if r["clarify"]]
            nf = [r for r in rs if r["not_found"]]
            okc = sum(r[f"{path}_{flag}"]["out"].startswith(("netlestirme", "konu")) for r in cl)
            okn = sum(r[f"{path}_{flag}"]["out"] not in ("model",) for r in nf)
            out.append(f"| {title} | {'açık' if flag else 'kapalı'} | {okc}/{len(cl)} | {okn}/{len(nf)} |")
    out += ["", "## Değişen sorular", "", "| Soru | Yol | kapalı | açık |", "|---|---|---|---|"]
    for r in rs:
        for path in PATHS:
            o, n = r[f"{path}_0"], r[f"{path}_1"]
            if o["out"] != n["out"] or o["rank"] != n["rank"]:
                out.append(f"| {r['qid']} — {r['q'][:60]} | {path} | {o['out']} (sıra {o['rank']}) | "
                           f"{n['out']} (sıra {n['rank']}) |")
    out += ["", f"Bulut: {json.dumps(stats, ensure_ascii=False)}", ""]
    return "\n".join(out)


if __name__ == "__main__":
    main()
