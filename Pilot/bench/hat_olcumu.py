"""Bağlanacak hattın uçtan uca ölçümü (Adım 2 planı §26 / §28; onay 2026-11-06). Uygulamaya bağlı değil.

Hat, soru başına:
  1. paralel: sorgu çevirisi (Gemma 4 NextBit, düşünme kapalı, 1,2 sn sınırı; aşarsa BM25 çevirisiz) ‖ bge-m3 dense
  2. Qdrant (uygulamanın `manuals` koleksiyonu, gömülü mod): bge-m3 dense ‖ BM25 (çevrilmiş sorgu), RRF; rerank yok
  3. uygulamanın kural katmanı olduğu gibi (pipeline.soru_cevapla; `search` yerine bu ikili yol)
  4. cevap: Gemma 4, şema c150b-J, max_tokens 1200, DeepInfra'ya sabit, akışlı
  5. doğrulama verify_c (alan etiketi kuralı dahil); ilk doğrulanmış cümle gerçek akış zaman çizelgesinden
Varyant: modele 5 / 8 kaynak. Arama soru başına bir kez (ilk varyantın çağrısında; ikinci varyant aynı adayları
kullanır). İki varyantın sırası her soruda rastgele (tohum sabit).
Uçtan uca ilk doğrulanmış cümle = cevap isteğine kadar geçen süre (arama dahil; ikinci varyantta ilk varyantın ölçülen
arama süresi eklenir) + başarısız deneme süreleri + akıştaki ilk doğrulanmış cümle anı.

Kayıt: eval/bench/adim2/ham/nihai_hat_k5_gemma4.json, nihai_hat_k8_gemma4.json (answer_models biçimi; report_c okur),
arama ve çeviri ayrıntısı satırda "hat". Rapor: eval/bench/adim2/hat_rapor_<tarih>.md

Kullanım (Pilot klasöründe; uygulama arayüzü kapalı, gömülü Qdrant):
    python -m bench.hat_olcumu --max-usd 3.0                 # 245 soru (onaylı 199 + yeni 46)
    python -m bench.hat_olcumu --ids Q07 C004 --tag deneme    # birkaç soru
    python -m bench.hat_olcumu --report
"""
from __future__ import annotations

import argparse
import json
import random
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutTimeout
from datetime import date, datetime
from typing import Any

import bench.answer_models as AM
from bench.common import percentile

KS = (5, 8)
TR_LIMIT = 1.2
SEED = 20261106
SETS = [*AM.SETS, "aday_sorular_ek"]
MODEL = "gemma4"            # DeepInfra'ya sabit (answer_models.MODELS)
WATCH = ["questions:Q05", "sekil_sorular:G7"]     # c150b-J'de yeni gereksiz netleştirme (izlenecek)


class IkiliYol:
    """pipeline.search yerine: çeviri ‖ bge-m3, sonra Qdrant hibrit (dense + çevirili BM25). Soru başına önbellekli."""

    def __init__(self) -> None:
        from bench.translate_compare import PinnedChat
        self.chat = PinnedChat("g4_nextbit")
        self.pool = ThreadPoolExecutor(4)
        self.memo: dict[str, dict[str, Any]] = {}
        self.last: dict[str, Any] = {}

    def __call__(self, query: str, *, brands: list[str] | None = None, doc_ids: list[str] | None = None,
                 mode: str = "hybrid", top_k: int = 5, query_en: str | None = None, access: list[str] | None = None,
                 **_: Any) -> list[Any]:
        from pilot import retrieve
        key = json.dumps([query, brands, doc_ids, access], ensure_ascii=False)
        t0 = time.perf_counter()
        if key not in self.memo:
            self.memo[key] = self._search(query, brands, doc_ids, access)
        info = self.memo[key]
        self.last = {"bu_cagri_sn": time.perf_counter() - t0, **{k: v for k, v in info.items() if k != "hits"}}
        return [retrieve.Hit(**h) for h in info["hits"][:top_k]]

    def _search(self, query: str, brands: Any, doc_ids: Any, access: Any) -> dict[str, Any]:
        from pilot import retrieve
        from pilot.embed import embed
        from pilot.query import question_lang
        from pilot.sparse import bm25_query
        from pilot.translate import bm25_text, target_languages, translate_query
        t0 = time.perf_counter()
        src, targets = question_lang(query), target_languages(doc_ids)

        def tr() -> tuple[dict[str, str], float]:
            t = time.perf_counter()
            try:
                out = translate_query(query, src, targets, self.chat)
            except (ValueError, json.JSONDecodeError):
                out = {}
            return out, time.perf_counter() - t

        f_tr = self.pool.submit(tr)
        te = time.perf_counter()
        dense = embed([query])[0]["dense"]
        t_embed = time.perf_counter() - te
        try:
            trans, t_tr = f_tr.result(timeout=max(0.0, TR_LIMIT - (time.perf_counter() - t0)))
            late = False
        except FutTimeout:
            trans, t_tr, late = {}, None, True       # çeviri sınırı aşıldı: BM25 çevirisiz (çağrı arka planda biter)
        sparse_text = bm25_text(trans, query) if trans else query
        q = {"dense": dense, "sparse": bm25_query(sparse_text)}
        if retrieve.DENSE_MODE != "full":
            from pilot.embed import short_vector
            q["short"] = short_vector(dense, retrieve.DENSE_SHORT_DIM)
        tq = time.perf_counter()
        qc = retrieve.search_client()
        try:
            points = retrieve.candidates(qc, q, retrieve._filter(brands, doc_ids, access), "hybrid",
                                         dparams=retrieve.dense_params())
        finally:
            retrieve.release(qc)
        t_q = time.perf_counter() - tq
        hits = [AM._hit_to_json(retrieve.Hit(p.payload, i, None, p.score)) for i, p in enumerate(points)]
        return {"hits": hits, "arama_sn": time.perf_counter() - t0, "ceviri_sn": t_tr, "ceviri_sinir_asildi": late,
                "ceviri_bos": not trans and not late, "embed_sn": t_embed, "qdrant_sn": t_q, "bm25_metni": sparse_text,
                "hedef_diller": targets}


def run(tag: str, max_usd: float, ids: list[str]) -> list[str]:
    from pilot import pipeline
    AM.SCHEMA, AM.MAX_TOKENS, AM.SETS = "c150bJ", 1200, SETS
    search = IkiliYol()
    pipeline.search = search
    m = AM.CloudModel(MODEL)
    system_prompt = AM.schema_and_prompt()[1]
    qs = AM.questions(include_clarify=True)
    if ids:
        qs = [q for q in qs if q["id"] in ids or q["qid"] in ids]
    rng = random.Random(SEED)
    outs = {k: {"model": MODEL, "spec": AM.MODELS[MODEL], "tag": f"{tag}_k{k}", "zdr_providers": m.zdr_providers,
                "verify": AM.VERIFY_TAG, "deger": AM.VALUE_TAG, "sema": AM.SCHEMA, "netlestirme_sorulari": "dahil",
                "max_tokens": AM.MAX_TOKENS, "kaynak_sayisi": k, "hat": "ikili yol (manuals, gömülü) + c150b-J DeepInfra",
                "start": datetime.now().isoformat(timespec="seconds"), "rows": {}, "cost_usd": 0.0} for k in KS}
    paths = {k: AM.RAW_DIR / f"{tag}_k{k}_{MODEL}.json" for k in KS}

    def save() -> None:
        for k in KS:
            outs[k]["end"] = datetime.now().isoformat(timespec="seconds")
            outs[k]["ceviri_maliyet"] = search.chat.cost
            paths[k].write_text(json.dumps(outs[k], ensure_ascii=False, indent=1), encoding="utf-8")

    chk = AM.thinking_check(m)
    outs[KS[0]]["dusunme_kontrolu"], outs[KS[0]]["cost_usd"] = chk, chk["cost"]
    print(f"düşünme kontrolü {chk}", flush=True)
    if not chk["ok"]:
        save()
        raise SystemExit("düşünme kapanmadı")
    others = AM.spent_all(prefix="nihai") - sum(
        json.loads(p.read_text(encoding="utf-8")).get("cost_usd", 0.0) for p in paths.values() if p.exists())
    current: dict[str, Any] = {}

    def chat(user: str) -> tuple[dict[str, Any], dict[str, float]]:
        if others + sum(o["cost_usd"] for o in outs.values()) + search.chat.cost > max_usd:
            raise AM.Budget
        current["llm_start"] = time.perf_counter()
        rec = m.stream([{"role": "system", "content": system_prompt}, {"role": "user", "content": user}])
        outs[current["k"]]["cost_usd"] += m.cost(rec)
        current["rec"] = rec
        if rec.get("unanswered"):
            raise AM.Unanswered(rec["unanswered"])
        from bench.schema_c import parse_c, to_legacy
        ans_c, status = parse_c(rec["content"], rec.get("finish"))
        current.update(json=status, thought=False, c=ans_c)
        if status in ("bos", "kesik", "gecersiz") or ans_c is None:
            from pilot.jsonparse import ModelJSONError, error_detail
            raise ModelJSONError(status == "kesik", error_detail(rec["content"] or "") or status)
        return to_legacy(ans_c), {"llm_seconds": rec["total"]}

    pipeline.chat_json = chat
    # Isınma (ölçülmez): bge-m3 yükleme, Qdrant açma, parça dosyası, çeviri bağlantısı; ilk soruda ~1 dk sürüyordu
    pipeline._chunks()
    for w in ("Isınma: dikiş adımı nasıl ayarlanır?", "Warm-up: how to adjust the stitch length?"):
        search._search(w, None, None, None)
    stopped = False
    for i, q in enumerate(qs, 1):
        order = list(KS)
        rng.shuffle(order)
        for j, k in enumerate(order):
            pipeline.TOP_K_SOURCES = k
            current.clear()
            current["k"] = k
            t0 = time.perf_counter()
            try:
                res = pipeline.soru_cevapla(q["q"])
                row = AM.judge_c(q, res, current) if current.get("c") is not None else AM.judge(q, res)
            except AM.Unanswered as e:
                row = {"cikis": "cevapsiz", "hata": str(e)}
            except AM.Budget:
                print(f"BÜTÇE SINIRI {max_usd} USD, durdu ({i}/{len(qs)})", flush=True)
                stopped = True
                break
            rec = current.get("rec") or {}
            usage = rec.get("usage") or {}
            s = dict(search.last)
            row.update(json=current.get("json"), provider=rec.get("provider"), ilk_token=rec.get("first_token"),
                       toplam=rec.get("total"), finish=rec.get("finish"), denemeler=rec.get("attempts"),
                       giris=usage.get("prompt_tokens"), cikis_token=usage.get("completion_tokens"),
                       maliyet=m.cost(rec) if rec else 0.0, ham=rec.get("content", "") if rec else "",
                       sira_varyant=j, hat=s)
            if rec.get("zaman"):
                row["akis_zaman"] = rec["zaman"]
            if "llm_start" in current:
                # cevap isteğine kadar: bu çağrının ölçülen süresi, aramanın bu çağrıdaki payı yerine ölçülen arama süresi
                pre = (current["llm_start"] - t0) - s.get("bu_cagri_sn", 0.0) + s.get("arama_sn", 0.0)
                failed = sum(a.get("sn") or 0.0 for a in (rec.get("attempts") or [])[:-1])
                row["istek_oncesi_sn"] = pre
                if row.get("ilk_dogrulanmis_cumle") is not None:
                    row["uctan_uca_ilk_dogrulanmis"] = pre + failed + row["ilk_dogrulanmis_cumle"]
                if rec.get("first_token") is not None:
                    row["uctan_uca_ilk_token"] = pre + failed + rec["first_token"]
            outs[k]["rows"][q["qid"]] = row
            print(f"{time.strftime('%H:%M:%S')} {i}/{len(qs)} k{k} {q['qid']} {row.get('cikis')} {row.get('durum')} "
                  f"u2u={row.get('uctan_uca_ilk_dogrulanmis') or float('nan'):.2f} çeviri="
                  f"{'sınır' if s.get('ceviri_sinir_asildi') else round(s.get('ceviri_sn') or 0, 2)} · "
                  f"{sum(o['cost_usd'] for o in outs.values()) + search.chat.cost:.4f} USD", flush=True)
        if stopped:
            for k in KS:
                outs[k]["durdu"] = f"bütçe sınırı {max_usd} USD"
            break
        if i % 10 == 0:
            save()
    for k in KS:
        outs[k]["tamam"] = not stopped
    save()
    search.pool.shutdown(wait=True)
    return [str(p) for p in paths.values()]


def report(tag: str) -> str:
    AM.SETS = SETS
    s_ = lambda x: "–" if x is None or x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))
    runs = {k: json.loads((AM.RAW_DIR / f"{tag}_k{k}_{MODEL}.json").read_text(encoding="utf-8")) for k in KS}
    L = [f"# Bağlanacak hattın uçtan uca ölçümü: `{tag}`", "",
         "Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, "
         "gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). "
         "Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.", "",
         "**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle "
         "(b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.", ""]
    for k, d in runs.items():
        # kalite tablosu answer_models.report_c'den (aynı ölçütler)
        pass
    for n, k in enumerate(KS):
        rows = AM.report_c(f"{tag}_k{k}").splitlines()
        L += (rows[4:6] if n == 0 else []) + [rows[6].replace("| gemma4 |", f"| {k} kaynak |", 1)]
    L += ["", "## Süre (gerçek akış; uçtan uca arama dahil)", "",
          "| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | "
          "≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |", "|---|---|---|---|---|---|---|"]
    for k, d in runs.items():
        R = d["rows"]
        fv = [r["ilk_dogrulanmis_cumle"] for r in R.values() if r.get("ilk_dogrulanmis_cumle") is not None]
        u2u = [r["uctan_uca_ilk_dogrulanmis"] for r in R.values() if r.get("uctan_uca_ilk_dogrulanmis") is not None]
        ft = [r["uctan_uca_ilk_token"] for r in R.values() if r.get("uctan_uca_ilk_token") is not None]
        pre = [r["istek_oncesi_sn"] for r in R.values() if r.get("istek_oncesi_sn") is not None]
        ok3 = sum(x <= 3.0 for x in u2u)
        L.append(f"| {k} kaynak | {len(u2u)} | {s_(percentile(fv, .5))} / {s_(percentile(fv, .95))} | "
                 f"**{s_(percentile(u2u, .5))} / {s_(percentile(u2u, .95))}** | {ok3}/{len(u2u)} ({ok3 / max(len(u2u), 1):.0%}) | "
                 f"{s_(percentile(ft, .5))} / {s_(percentile(ft, .95))} | {s_(percentile(pre, .5))} / {s_(percentile(pre, .95))} |")
    first = runs[KS[0]]["rows"]
    srch = {}
    for d in runs.values():
        for q, r in d["rows"].items():
            if r.get("hat") and r["hat"].get("arama_sn") is not None:
                srch[q] = r["hat"]
    a = [h["arama_sn"] for h in srch.values()]
    tr = [h["ceviri_sn"] for h in srch.values() if h.get("ceviri_sn") is not None]
    late = sum(bool(h.get("ceviri_sinir_asildi")) for h in srch.values())
    L += ["", "## Arama adımı (soru başına bir kez)", "",
          "| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |",
          "|---|---|---|---|---|---|---|",
          f"| {len(srch)} | {s_(percentile(a, .5))} / {s_(percentile(a, .95))} | {s_(percentile(tr, .5))} / {s_(percentile(tr, .95))} | "
          f"{late}/{len(srch)} ({late / max(len(srch), 1):.0%}) | {sum(bool(h.get('ceviri_bos')) for h in srch.values())} | "
          f"{s_(percentile([h['embed_sn'] for h in srch.values()], .5))} | {s_(percentile([h['qdrant_sn'] for h in srch.values()], .5))} |"]
    L += ["", "## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)", "", "| Soru | 5 kaynak | 8 kaynak |", "|---|---|---|"]
    for q in WATCH:
        L.append(f"| {q} | " + " | ".join(f"{runs[k]['rows'].get(q, {}).get('cikis')} / {runs[k]['rows'].get(q, {}).get('durum')}"
                                         for k in KS) + " |")
    L += ["", f"Çeviri maliyeti: {runs[KS[0]].get('ceviri_maliyet', 0):.4f} USD · cevap: "
          + " · ".join(f"{k} kaynak {d.get('cost_usd', 0):.4f} USD" for k, d in runs.items()), ""]
    del first
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="nihai_hat")
    ap.add_argument("--max-usd", type=float, default=3.0)
    ap.add_argument("--ids", nargs="+", default=[])
    ap.add_argument("--report", action="store_true")
    ap.add_argument("--setler", nargs="+", help="soru setleri (varsayılan: onaylı + yeni 46)")
    ap.add_argument("--ks", nargs="+", type=int, help="kaynak sayıları (varsayılan 5 8)")
    a = ap.parse_args()
    global KS, SETS
    if a.setler:
        SETS = list(a.setler)
    if a.ks:
        KS = tuple(a.ks)
    if not a.report:
        for p in run(a.tag, a.max_usd, a.ids):
            print(p, flush=True)
    md = report(a.tag)
    out = AM.RAW_DIR.parent / f"hat_rapor_{date.today().isoformat()}.md" if a.tag == "nihai_hat" else \
        AM.RAW_DIR.parent / f"{a.tag}_rapor_{date.today().isoformat()}.md"
    out.write_text(md, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
