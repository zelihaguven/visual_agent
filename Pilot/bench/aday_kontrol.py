"""Aday soru seti onay kontrolü (model çağrısı yok; ölçüt 2026-11-05 akşam, kullanıcı kararı).

Onay ölçütü (model çıktısı KULLANILMAZ: sistemin zorlandığı soruları setten atmak döngüsel olur):
    cevaplı       kanıt cümlesi (kanit) beklenen parçada/sayfada geçiyor; beklenen değer kanıtta geçiyor (OCR hariç)
    netleştirme   kabul edilen parçalar var ve beklenen sayfalarda
    bulunamadı    27 Ekim korpus araması kaydı (nf_kontrol) var
    OCR           yukarıdakine ek olarak beklenen değer okunaklı (OCR biçimini kopyalamıyor); `ocr` etiketi eklenir
Bilgi (onayı etkilemez): Adım 2 ilk turunda arama ve dört modelin beklenenle çelişmesi (`model_celiskisi`).

Kullanım (Pilot klasöründe):
    python -m bench.aday_kontrol            # tablo
    python -m bench.aday_kontrol --yaz      # eval/aday_sorular.json: dogrulandi, onaylayan, onay_tarihi, kontrol alanları
"""
import argparse
import json
import re
from collections import defaultdict

from bench.common import EVAL_DIR, OUT_DIR, value_in
from pilot.config import CHUNKS_PATH
from pilot.verify import normalize

OCR_RE = re.compile(r"\b\d*1(?:12|14|18|16|34|38|58|78)\s*-?\s*inch|\b\d{1,2}-1(?:12|14|18|16|34)\b|\bIS\s+min\b|"
                    r"\bfi'om\b|\bpattem\b|\bconstmction\b|\bconfonn\b")
DATE, BY = "2026-11-05", "geliştirme ekibi"


def evidence_ok(kanit: str, text: str) -> bool:
    k, t = normalize(kanit), normalize(text)
    if k in t:
        return True
    words = [w for w in re.findall(r"\w+", k) if len(w) > 2]
    return bool(words) and sum(w in t for w in words) / len(words) >= 0.9


def model_conflict(qid: str, it: dict, rows: dict) -> str:
    rs = [R[qid] for R in rows.values() if qid in R]
    if it.get("expect_not_found"):
        made = [k for k, R in rows.items() if R.get(qid, {}).get("cikis") == "cevap"
                and R[qid].get("durum") in ("verified", "partial")]
        return f"doğrulanmış cevap üreten model: {', '.join(made)}" if made else ""
    if it.get("expect_clarify") or len(rs) < 4:
        return ""
    bad = lambda r: (r.get("cikis") == "bulunamadi" or r.get("deger_dogru") is False
                     or ("deger_dogru" not in r and r.get("atif_dogru_biri") is False))
    if all(bad(r) for r in rs):
        miss = all(r.get("sira") is None or r["sira"] > 5 for r in rs)
        return "arama ve 4 model beklenenle çelişti" if miss else "4 model beklenenle çelişti (arama getirdi)"
    return ""


def check(items: list[dict]) -> dict[str, dict]:
    chunks = [json.loads(l) for l in CHUNKS_PATH.read_text(encoding="utf-8").splitlines() if l.strip()]
    by_id = {c["chunk_id"]: c for c in chunks}
    by_page = defaultdict(list)
    for c in chunks:
        for p in c.get("pages") or []:
            by_page[(c["doc_id"], p)].append(c)
    rows = {f.stem.split("_", 1)[1]: json.loads(f.read_text(encoding="utf-8"))["rows"]
            for f in sorted((OUT_DIR / "adim2" / "ham").glob("ana_*.json"))}
    out = {}
    for it in items:
        qid, why, ocr = f"aday_sorular:{it['id']}", [], False
        kab = it.get("kabul") or []
        exp = [by_id[k["chunk_id"]] for k in kab if k.get("chunk_id") in by_id]
        page_text = " ".join(c["text"] for k in kab for p in k.get("pages") or [] for c in by_page[(k["doc"], p)])
        text = " ".join(c["text"] for c in exp) + " " + page_text
        if it.get("expect_not_found"):
            if not it.get("nf_kontrol"):
                why.append("27 Ekim korpus araması kaydı yok")
        elif it.get("expect_clarify"):
            for k in kab:
                c = by_id.get(k.get("chunk_id"))
                if not c or not set(k.get("pages") or []) & set(c.get("pages") or []):
                    why.append(f"kabul parçası yok ya da sayfası tutmuyor: {k.get('chunk_id')}")
            if not kab:
                why.append("kabul edilen parça yok")
        else:
            if not it.get("kanit"):
                why.append("kanıt cümlesi yok")
            elif not evidence_ok(it["kanit"], text):
                why.append(f"kanıt cümlesi beklenen parçada/sayfada geçmiyor: {it['kanit'][:80]!r}")
            ocr = bool(it.get("ocr_bicimi") or "ocr" in it.get("zorluk", []) or OCR_RE.search(it.get("kanit") or ""))
            if it.get("kanit") and not ocr:     # OCR'da kanıt bozuk biçimde; değer ondan okunamaz
                miss = [v for v in it.get("expect_in_answer") or [] if not value_in(v, it["kanit"])]
                if miss:
                    why.append(f"beklenen değer kanıt cümlesinde yok: {miss}")
            if ocr:
                form = it.get("ocr_bicimi") or ""
                if any(form and normalize(form) in normalize(v) for v in it.get("expect_in_answer") or []):
                    why.append(f"beklenen değer OCR biçimini kopyalıyor: {form!r}")
                if not (it.get("expect_in_answer") or it.get("cevap")):
                    why.append("OCR sorusu ama beklenen değer yazılmamış")
        out[it["id"]] = {"q": it["q"], "kind": it["kind"], "neden": why, "ocr": ocr,
                         "model_celiskisi": model_conflict(qid, it, rows)}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--yaz", action="store_true")
    a = ap.parse_args()
    path = EVAL_DIR / "aday_sorular.json"
    items = json.loads(path.read_text(encoding="utf-8"))
    res = check(items)
    bad = {k: v for k, v in res.items() if v["neden"]}
    print(f"{len(items)} soru: onaylanan {len(items) - len(bad)}, onaysız {len(bad)}, OCR {sum(v['ocr'] for v in res.values())}, "
          f"model çelişkisi (bilgi) {sum(bool(v['model_celiskisi']) for v in res.values())}")
    for k, v in bad.items():
        print(f"| {k} | {v['kind']} | {v['q']} | {'; '.join(v['neden'])} |")
    if a.yaz:
        for it in items:
            r = res[it["id"]]
            for f in ("kontrol_supheleri", "onaylayan", "onay_tarihi", "model_celiskisi"):
                it.pop(f, None)
            if r["model_celiskisi"]:
                it["model_celiskisi"] = r["model_celiskisi"]
            if r["ocr"] and "ocr" not in it["zorluk"]:
                it["zorluk"].append("ocr")
            if r["neden"]:
                it["dogrulandi"], it["kontrol_supheleri"] = False, r["neden"]
            else:
                it.update(dogrulandi=True, onaylayan=BY, onay_tarihi=DATE,
                          note=f"onaylandı {DATE} ({BY}): kanıt beklenen sayfada"
                               + ("; 27 Ekim korpus araması" if it.get("expect_not_found") else "")
                               + ("; OCR sorusu, beklenen değer okunaklı" if r["ocr"] else ""))
        path.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
        print("yazıldı:", path)


if __name__ == "__main__":
    main()
