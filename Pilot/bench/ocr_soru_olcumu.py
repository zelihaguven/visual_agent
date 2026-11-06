"""OCR etiketli sorularda cevapsız kalma ölçümü (docs/PLAN-OCR.md §8 ölçütü; model ve bulut çağrısı yok).

Bugünkü OCR katmanının parçaları ile yeniden OCR'lı belgenin parçaları aynı düzenekte karşılaştırılır:
  - yeniden OCR: OCRmyPDF (Ghostscript'siz), dil belge dilinden (kayıt: default_lang → eng/tur). Pantolon
    --redo-ocr; Granovsky --force-ocr (harf aralıklı katmanda --redo-ocr işe yaramadı)
  - ayrıştırma ve parçalama uygulamanın kodu (pilot.parse, pilot.chunk), geçici klasörde (gerçek önbelleğe dokunmaz)
  - yalnız sorulara ait sayfa alt kümesi (beklenen sayfa ± 3) bellekteki geçici Qdrant'a (bge-m3 + BM25) indekslenir;
    iki sürüm aynı sayfalarla
  - arama uygulamanın hibrit araması (retrieve.candidates); BM25 sorgusu hat kaydındaki çeviri (bm25_metni)
Ölçüler (ilk 8 kaynak): beklenen sayfa ilk 8'de mi; beklenen değerler (expect_in_answer) bu parçalarda birebir geçiyor
mu (bench.common.value_in). "Cevaplanabilir" = ikisi birden. Cevapsız kalma oranının modelsiz vekili.

Kullanım (Pilot klasöründe):  $env:PILOT_ANSWER_MODE = "bugun"; python -m bench.ocr_soru_olcumu
"""
from __future__ import annotations

import dataclasses
import json
import time
from pathlib import Path
from typing import Any

from bench.common import PILOT_DIR, load_questions, prepare, value_in
from bench.ocr_karsilastir import WORK, run_ocrmypdf

SETS = ["questions", "questions_ek", "sekil_sorular", "aday_sorular", "aday_sorular_ek"]
MODES = {"gl-pd-07-14a": "redo", "granovsky-1986": "force"}
TOP_K = 8
OUT = PILOT_DIR / "eval" / "bench" / "ocr"


def ocr_doc(meta, mode: str, lang: str) -> Path:
    import subprocess

    from bench.ocr_karsilastir import OCRMYPDF, _env
    out = WORK / f"{meta.doc_id}_tam_{mode}.pdf"
    if not out.exists():
        flag = {"redo": "--redo-ocr", "force": "--force-ocr"}[mode]
        t = time.perf_counter()
        r = subprocess.run([str(OCRMYPDF), "-l", lang, flag, "--rasterizer", "pypdfium", "--output-type", "pdf",
                            "--pdfa-backend", "internal", "-q", "-j", "4", str(meta.path), str(out)], env=_env(),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-400:])
        print(f"{meta.doc_id}: OCR {time.perf_counter() - t:.0f} sn", flush=True)
    return out


def chunks_for(meta) -> list[dict[str, Any]]:
    """Uygulamanın ayrıştırma + parçalaması, geçici önbellekle (gerçek data/parsed'e yazmaz)."""
    from pilot import parse
    from pilot.chunk import build_chunks
    old = parse.PARSED_DIR
    parse.PARSED_DIR = WORK / "parsed"
    parse.PARSED_DIR.mkdir(parents=True, exist_ok=True)
    try:
        res = parse.load_or_parse(meta)
    finally:
        parse.PARSED_DIR = old
    return [dataclasses.asdict(c) if dataclasses.is_dataclass(c) else dict(c) for c in build_chunks(meta, res["elements"], None)]


def index(chunks: list[dict[str, Any]], name: str):
    from qdrant_client import QdrantClient, models

    from pilot.embed import encode_docs
    from pilot.index import collection_schema, point_vectors
    qc = QdrantClient(":memory:")
    schema = collection_schema()
    qc.create_collection(name, **schema)
    vecs = encode_docs([c.get("embed_text") or c["text"] for c in chunks])
    qc.upsert(name, [models.PointStruct(id=i, vector=point_vectors(v), payload=c) for i, (c, v) in enumerate(zip(chunks, vecs))])
    return qc


def search(qc, name: str, query: str, bm25_text: str | None) -> list[dict[str, Any]]:
    from pilot import retrieve
    from pilot.embed import encode_query
    from pilot.sparse import bm25_query
    q = encode_query(query)
    if bm25_text:
        q["sparse"] = bm25_query(bm25_text)
    pts = retrieve.candidates(qc, q, None, "hybrid", collection=name, dparams=retrieve.dense_params())
    return [p.payload for p in pts[:TOP_K]]


def main() -> None:
    from bench import require_mode
    require_mode("bugun")
    from pilot.chunk import read_chunks
    from pilot.registry import BY_ID
    qs = [q for q in load_questions(SETS, include_unapproved=True) if "ocr" in (q.get("zorluk") or []) or q.get("ocr")]
    hat = {}
    for f in ("nihai_hat_k8_gemma4.json",):
        hat.update(json.loads((PILOT_DIR / "eval" / "bench" / "adim2" / "ham" / f).read_text(encoding="utf-8"))["rows"])
    old_all = read_chunks()
    rows = []
    for did, mode in MODES.items():
        meta = BY_ID[did]
        dq = [q for q in qs if did in (q.get("expect_docs") or [])]
        pages = sorted({p + d for q in dq for p in q.get("expect_pages", []) for d in range(-3, 4) if p + d >= 1})
        lang = {"en": "eng", "tr": "tur"}.get(meta.default_lang, "eng")
        new_pdf = ocr_doc(meta, mode, lang)
        new_meta = dataclasses.replace(meta, file=str(new_pdf))
        new_chunks = [c for c in chunks_for(new_meta) if set(c["pages"]) & set(pages)]
        old_chunks = [c for c in old_all if c["doc_id"] == did and set(c["pages"]) & set(pages)]
        print(f"{did}: sayfa {len(pages)}, parça eski {len(old_chunks)} yeni {len(new_chunks)}", flush=True)
        idx = {"bugunku_katman": index(old_chunks, "eski"), "yeni_ocr": index(new_chunks, "yeni")}
        for q in dq:
            p = prepare(q["q"])
            bm = ((hat.get(q["qid"]) or {}).get("hat") or {}).get("bm25_metni")
            row = {"qid": q["qid"], "q": q["q"], "belge": did, "beklenen_sayfa": q.get("expect_pages"),
                   "beklenen": q.get("expect_in_answer")}
            for name, qc in idx.items():
                hits = search(qc, "eski" if name == "bugunku_katman" else "yeni", p.get("search_q") or q["q"], bm)
                rank = next((i + 1 for i, h in enumerate(hits) if set(h["pages"]) & set(q.get("expect_pages") or [])), None)
                text = " ".join(h["text"] for h in hits)
                vals = [v for v in (q.get("expect_in_answer") or [])]
                found = all(value_in(v, text) for v in vals) if vals else None
                row[name] = {"sayfa_sirasi": rank, "deger_parcada": found,
                             "cevaplanabilir": bool(rank) and (found is not False)}
            rows.append(row)
            print(row, flush=True)
    summ = {k: {"sayfa_ilk8": sum(bool(r[k]["sayfa_sirasi"]) for r in rows),
                "deger_parcada": sum(r[k]["deger_parcada"] is True for r in rows),
                "deger_sorusu": sum(r[k]["deger_parcada"] is not None for r in rows),
                "cevaplanabilir": sum(r[k]["cevaplanabilir"] for r in rows), "soru": len(rows)}
            for k in ("bugunku_katman", "yeni_ocr")}
    out = {"tarih": time.strftime("%Y-%m-%d %H:%M"), "ozet": summ, "satirlar": rows}
    (OUT / "ham").mkdir(parents=True, exist_ok=True)
    (OUT / "ham" / "ocr_soru_olcumu.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
