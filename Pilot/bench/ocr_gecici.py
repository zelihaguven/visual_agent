"""OCR entegrasyonu: GEÇİCİ koleksiyonda doğrulama (karar 2026-11-06, PLAN-OCR §11 sırası). Ana indekse dokunmaz.

1. Hazırlık (--hazirla; model yok): hedef belgeler uygulamanın yükleme yolundan geçer (PILOT_OCR açık: metin katmanı
   kontrolü → OCRmyPDF → iki okuma → Docling ayrıştırma → parçalama, `ocr` ve `ocr_belirsiz` işaretleri). Çıktılar
   data/ocr_test/gecici/ altında (gerçek data/parsed ve test-dokumanlari/ocr'a yazılmaz). Hedefler:
     - gl-pd-07-14a (pantolon, taranmış; ikinci okuma eski katman)
     - granovsky-1986 (bozuk katman; ikinci okuma eski katman)
     - gl-pd-14-04a METİNSİZ ÖRNEK: ceketin bütün sayfaları sentetik taramaya çevrilir (300 dpi, eğiklik, bulanıklık,
       JPEG; metin katmanı yok) → ikinci okuma RapidOCR. Doğru cevap ceketin dijital metni.
   Şekil parçaları (görüntü açıklaması) eski parçalardan aynen taşınır.
2. Geçici koleksiyon: ana koleksiyonun diğer belgelerinin noktaları vektörleriyle kopyalanır (yeniden embed yok),
   hedeflerin yeni parçaları embed edilip eklenir; bellekte (":memory:"). Uygulamanın arama istemcisi
   (pilot.index._shared) bu koleksiyona çevrilir: arama ve cevap yolu uygulamanınki.
3. --arama: OCR etiketli 16 soru + ceketin cevaplı soruları, arama düzeyi (ilk 8: beklenen sayfa, beklenen değer
   parçada, beklenen değer belirsiz dizide mi), bugünkü indeks ile geçici koleksiyon.
4. --model (~0,01 USD): 16 soru uygulamanın c yolundan, bugünkü indeks ve geçici koleksiyon (32 çağrı).

Kullanım (Pilot klasöründe; arayüz kapalı):
  $env:PILOT_ANSWER_MODE = "c"; python -m bench.ocr_gecici --hazirla --arama [--model]
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import time
from collections import Counter
from datetime import date
from typing import Any

from bench.common import PILOT_DIR, load_questions, value_in

SETS = ["questions", "questions_ek", "sekil_sorular", "aday_sorular", "aday_sorular_ek"]
OUT = PILOT_DIR / "eval" / "bench" / "ocr"
GW = PILOT_DIR / "data" / "ocr_test" / "gecici"
TARGETS = ["gl-pd-07-14a", "granovsky-1986", "gl-pd-14-04a"]
TEXTLESS = "gl-pd-14-04a"


def log(m: str) -> None:
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)


def target_meta(did: str):
    from pilot.registry import BY_ID
    meta = BY_ID[did]
    if did != TEXTLESS:
        return meta
    import pymupdf

    from bench.ocr_karsilastir import image_only
    dst = GW / f"{did}_metinsiz.pdf"
    if not dst.exists():
        GW.mkdir(parents=True, exist_ok=True)
        n = len(pymupdf.open(str(meta.source_path)))
        image_only(meta.source_path, list(range(1, n + 1)), dst)
    return dataclasses.replace(meta, file=str(dst))          # MANUALS_DIR / mutlak yol = mutlak yol


def setup_dirs() -> None:
    from pilot import config, parse
    config.OCR_ENABLED = True
    config.OCR_DIR = GW / "ocr"
    parse.PARSED_DIR = GW / "parsed"
    parse.PARSED_DIR.mkdir(parents=True, exist_ok=True)


def prepare() -> None:
    from pilot import parse
    from pilot.chunk import build_chunks, read_chunks
    from pilot.ocr import summary
    setup_dirs()
    old = read_chunks()
    out = {}
    for did in TARGETS:
        meta = target_meta(did)
        t = time.perf_counter()
        res = parse.load_or_parse(meta, force=True)
        chunks = [dataclasses.asdict(c) for c in build_chunks(meta, res["elements"], None)]
        chunks += [c for c in old if c["doc_id"] == did and c.get("chunk_type") == "figure"]
        from pilot.ocr import load_record
        s = summary(load_record(meta) or {"sayfalar": []})
        out[did] = chunks
        log(f"{did}: {len(chunks)} parça ({sum(c.get('ocr', False) for c in chunks)} OCR'lı, "
            f"{sum(len(c.get('ocr_belirsiz') or []) for c in chunks)} belirsiz dizi parçada), OCR özeti {s}, "
            f"{time.perf_counter() - t:.0f} sn")
    (GW / "parcalar.json").write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")


def temp_collection():
    from qdrant_client import QdrantClient, models

    from pilot import index
    from pilot.config import COLLECTION
    from pilot.embed import encode_docs
    new = json.loads((GW / "parcalar.json").read_text(encoding="utf-8"))
    main = index.client()
    tmp = QdrantClient(":memory:")
    index.create_collection(tmp, COLLECTION, payload_indexes=False)
    off, nid, kept = None, 0, 0
    while True:
        pts, off = main.scroll(COLLECTION, limit=500, offset=off, with_payload=True, with_vectors=True)
        keep = [p for p in pts if p.payload.get("doc_id") not in new]
        if keep:
            tmp.upsert(COLLECTION, [models.PointStruct(id=nid + i, vector=p.vector, payload=p.payload) for i, p in enumerate(keep)])
            nid += len(keep)
            kept += len(keep)
        if off is None:
            break
    main.close()
    chunks = [c for cs in new.values() for c in cs]
    t = time.perf_counter()
    vecs = encode_docs([c.get("embed_text") or c["text"] for c in chunks])
    tmp.upsert(COLLECTION, [models.PointStruct(id=nid + i, vector=index.point_vectors(v), payload=index.with_access(c))
                            for i, (c, v) in enumerate(zip(chunks, vecs))])
    log(f"geçici koleksiyon: {kept} kopya + {len(chunks)} yeni parça ({time.perf_counter() - t:.0f} sn embed)")
    return tmp


def questions() -> list[dict[str, Any]]:
    qs = load_questions(SETS, include_unapproved=True)
    ocr = [q for q in qs if ("ocr" in (q.get("zorluk") or []) or q.get("ocr"))]
    ceket = [q for q in qs if TEXTLESS in (q.get("expect_docs") or []) and q.get("expect_in_answer")
             and not q.get("expect_not_found") and not q.get("expect_clarify") and q not in ocr]
    return [{**q, "grup": "ocr16"} for q in ocr] + [{**q, "grup": "metinsiz_ceket"} for q in ceket]


def _score(q: dict[str, Any], chunks: list[dict[str, Any]], label: str) -> dict[str, Any]:
    pages = set(q.get("expect_pages") or [])
    rank = next((i + 1 for i, c in enumerate(chunks) if set(c.get("pages") or []) & pages), None)
    text = " ".join(c["text"] for c in chunks)
    vals = q.get("expect_in_answer") or []
    found = all(value_in(v, text) for v in vals) if vals else None
    unc = [t for c in chunks for t in c.get("ocr_belirsiz") or []]
    in_unc = [v for v in vals if any(value_in(v, t) for t in unc)]
    return {"qid": q["qid"], "grup": q["grup"], "indeks": label, "sayfa_sirasi": rank, "deger_parcada": found,
            "cevaplanabilir": bool(rank) and found is not False, "beklenen_belirsizde": in_unc}


def retrieve_top8(q: dict[str, Any]) -> list[dict[str, Any]]:
    """Uygulamanın arama adımı (ikili yol dahil) ilk 8; model çağrısı yok."""
    from bench.common import prepare as prep
    from pilot import config, retrieve
    from pilot.pipeline import _translator
    p = prep(q["q"])
    sq, scope = p.get("search_q") or q["q"], p.get("doc_ids") or None
    tr = _translator(sq, scope)
    kw = {"translate": tr, "translate_limit_s": config.TRANSLATE_LIMIT_S} if tr is not None else {}
    hits = retrieve.search(sq, doc_ids=scope, top_k=config.ANSWER_TOP_K, **kw)
    return [h.chunk for h in hits]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hazirla", action="store_true")
    ap.add_argument("--arama", action="store_true")
    ap.add_argument("--model", action="store_true")
    a = ap.parse_args()
    from bench import require_mode
    require_mode("c")
    if a.hazirla:
        prepare()
    from pilot import index
    qs = questions()
    log(f"{len(qs)} soru: {Counter(q['grup'] for q in qs)}")
    res: dict[str, Any] = {"tarih": time.strftime("%Y-%m-%d %H:%M")}
    tmp = temp_collection()
    setup_dirs()                                                  # OCR açık: parçalar `ocr_belirsiz` taşır
    for label, qc in (("bugunku", index.client()), ("gecici", tmp)):
        index.close_shared()
        index._shared = qc
        if a.arama:
            res.setdefault("arama", [])
            for q in qs:
                res["arama"].append(_score(q, retrieve_top8(q), label))
            log(f"{label}: arama bitti")
        if a.model:
            from bench.duman_testi import judge
            from pilot import pipeline
            res.setdefault("model", [])
            for q in [q for q in qs if q["grup"] == "ocr16"]:
                r = pipeline.soru_cevapla(q["q"])
                row = {**judge(q, r), "indeks": label,
                       "ocr_belirsiz_sorun": [p for p in r.verification.problems if "OCR değeri belirsiz" in p]}
                # doğrulanmış görünen yanlış: beklenen değeri olan soruda ✓/⚠ ama beklenen değer yok
                row["dogrulanmis_gorunen_yanlis"] = row.get("deger") is False
                res["model"].append(row)
                log(f"{label} {q['qid']} {row['durum']} değer={row.get('deger')}")
        if label == "bugunku":
            index._shared = None
            qc.close()
    (OUT / "ham").mkdir(parents=True, exist_ok=True)
    (OUT / "ham" / "ocr_gecici.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    p = OUT / f"ocr_gecici_{date.today().isoformat()}.md"
    p.write_text(report(res), encoding="utf-8")
    print(p)


def report(res: dict[str, Any]) -> str:
    L = ["# OCR entegrasyonu: geçici koleksiyonda doğrulama", "",
         f"{res['tarih']}. PLAN-OCR §11. Ana indekse dokunulmadı. Pantolon ve Granovsky ikinci okuma eski katman; "
         "ceket metinsiz örnek (sentetik tarama, ikinci okuma RapidOCR).", ""]
    if res.get("arama"):
        L += ["## Arama düzeyi (ilk 8)", "", "| Grup | İndeks | soru | beklenen sayfa ilk 8'de | beklenen değer parçada | "
              "cevaplanabilir | beklenen değer belirsiz dizide |", "|---|---|---|---|---|---|---|"]
        for (g, ix), rs in sorted(_group(res["arama"]).items()):
            vq = [r for r in rs if r["deger_parcada"] is not None]
            L.append(f"| {g} | {ix} | {len(rs)} | {sum(bool(r['sayfa_sirasi']) for r in rs)} | "
                     f"{sum(r['deger_parcada'] is True for r in vq)}/{len(vq)} | {sum(r['cevaplanabilir'] for r in rs)} | "
                     f"{sum(bool(r['beklenen_belirsizde']) for r in rs)} |")
        L += ["", "| Soru | İndeks | sayfa sırası | değer parçada | belirsizde |", "|---|---|---|---|---|"]
        for r in res["arama"]:
            L.append(f"| {r['qid']} | {r['indeks']} | {r['sayfa_sirasi'] or '–'} | {r['deger_parcada']} | {r['beklenen_belirsizde'] or '–'} |")
    if res.get("model"):
        L += ["", "## Model (16 OCR sorusu, uygulamanın c yolu)", "",
              "| İndeks | soru | ✓ / ⚠ / ✖ | bulunamadı | beklenen değer | **doğrulanmış görünen yanlış** | OCR belirsiz nedeniyle ✖ öğe | maliyet |",
              "|---|---|---|---|---|---|---|---|"]
        for ix in ("bugunku", "gecici"):
            rs = [r for r in res["model"] if r["indeks"] == ix]
            c = Counter(r["durum"] for r in rs)
            dv = [r["deger"] for r in rs if r.get("deger") is not None]
            L.append(f"| {ix} | {len(rs)} | {c['verified']} / {c['partial']} / {c['failed']} | {c['not_found']} | "
                     f"{sum(dv)}/{len(dv)} | **{sum(r['dogrulanmis_gorunen_yanlis'] for r in rs)}** | "
                     f"{sum(bool(r['ocr_belirsiz_sorun']) for r in rs)} | {sum(r.get('maliyet') or 0 for r in rs):.4f} |")
        L += ["", "| Soru | İndeks | durum | değer | cevap (ilk 160) |", "|---|---|---|---|---|"]
        for r in res["model"]:
            L.append(f"| {r['qid']} | {r['indeks']} | {r['durum']} | {r.get('deger')} | {(r.get('cevap') or '')[:160].replace('|', '/')} |")
    return "\n".join(L) + "\n"


def _group(rows: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    g: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in rows:
        g.setdefault((r["grup"], r["indeks"]), []).append(r)
    return g


if __name__ == "__main__":
    main()
