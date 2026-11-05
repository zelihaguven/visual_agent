"""Aday soru seti otomatik tutarlılık kontrolü (model çağrısı yok; 2026-11-05 onayında kullanıldı).

Kontroller: beklenen değer beklenen parçada/sayfada geçiyor mu; OCR bozukluğu kalıbı; "bulunamadı" sorusunda bir model
doğrulanmış (✓/⚠) cevap üretti mi; arama ve Adım 2 ilk turunun dört modelinin beklenenle çelişmesi (kayıtlardan).
Uyarı: son ölçüt model çıktısı kullanır; bununla onaylanan küme o modellerin kalite ölçümü için yanlıdır.

Kullanım (Pilot klasöründe): python -m bench.aday_kontrol [şüpheliler.json]
"""
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from pilot.config import CHUNKS_PATH
from pilot.verify import normalize, numbers_in, word_numbers

ROOT = Path(".")
items = json.loads((ROOT / "eval/aday_sorular.json").read_text(encoding="utf-8"))
chunks = [json.loads(l) for l in CHUNKS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
by_id = {c["chunk_id"]: c for c in chunks}
by_page = defaultdict(list)
for c in chunks:
    for p in c.get("pages") or []:
        by_page[(c["doc_id"], p)].append(c)

OCR = [(r"\b\d*1(?:12|14|18|16|34|38|58|78)\s*-?\s*inch", "kesir OCR (112 = ½)"),
       (r"\b\d{1,2}-1(?:12|14|18|16|34)\b", "kesir OCR (7-114)"), (r"\bIS\s+min\b", "IS = 15"),
       (r"\bfi'om\b|\bpattem\b|\bconstmction\b|\bconfonn\b|\bTlu·ead", "harf OCR"), (r"\b\d[lI]\d", "1/l karışması")]

rows = {}
for f in sorted((ROOT / "eval/bench/adim2/ham").glob("ana_*.json")):
    rows[f.stem.split("_", 1)[1]] = json.loads(f.read_text(encoding="utf-8"))["rows"]

sus = {}
for it in items:
    qid = f"aday_sorular:{it['id']}"
    why = []
    ids = it.get("expect_chunk_ids") or [k["chunk_id"] for k in it.get("kabul") or [] if k.get("chunk_id")]
    exp = [by_id[i] for i in ids if i in by_id]
    if not exp:
        exp = [c for d in it.get("expect_docs") or [] for p in it.get("expect_pages") or [] for c in by_page[(d, p)]]
    text = " ".join(c["text"] for c in exp)
    if it.get("expect_in_answer") and not it.get("expect_not_found"):
        if not exp:
            why.append("beklenen parça bulunamadı")
        for v in it["expect_in_answer"]:
            ok = normalize(v) in normalize(text)
            if not ok and numbers_in(v):
                ok = numbers_in(v) <= (numbers_in(text) | word_numbers(text))
            if not ok:
                why.append(f"beklenen değer parçada yok: {v!r}" + (" (ocr_bicimi notlu)" if it.get("ocr_bicimi") else ""))
    for pat, label in OCR:
        m = re.search(pat, text)
        if m and not it.get("expect_not_found"):
            why.append(f"OCR şüphesi: {label} «{m.group(0)}»" + (" (ocr_bicimi notlu)" if it.get("ocr_bicimi") else ""))
            break
    if it.get("expect_not_found"):
        made = [k for k, R in rows.items() if R.get(qid, {}).get("cikis") == "cevap"
                and R[qid].get("durum") in ("verified", "partial")]
        if made:
            why.append(f"bulunamadı sorusu ama doğrulanmış cevap üreten model: {', '.join(made)}")
    elif not it.get("expect_clarify"):
        rs = [R.get(qid) for R in rows.values() if R.get(qid)]
        if rs:
            searched_miss = all(r.get("sira") is None or r["sira"] > 5 for r in rs)
            bad = lambda r: (r.get("cikis") == "bulunamadi" or r.get("deger_dogru") is False
                             or ("deger_dogru" not in r and r.get("atif_dogru_biri") is False))
            all_bad = len(rs) == 4 and all(bad(r) for r in rs)
            if searched_miss and all_bad:
                why.append("arama ilk 5'te beklenen kaynağı getirmedi ve 4 model de beklenenle çelişti")
            elif all_bad:
                why.append("4 model de beklenenle çelişti (arama getirdi)")
    if why:
        sus[it["id"]] = {"q": it["q"], "kind": it["kind"], "neden": why}

out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
print(len(items), "soru,", len(sus), "şüpheli")
for k, v in sus.items():
    print(f"| {k} | {v['kind']} | {v['q'][:70]} | {'; '.join(v['neden'])[:260]} |")
if out:
    out.write_text(json.dumps(sus, ensure_ascii=False, indent=1), encoding="utf-8")
