"""İki okuma ölçümü (karar 2026-11-06, PLAN-OCR §11): metin katmanı olmayan sayfada ikinci okuma RapidOCR. Model ve ağ yok.

A. RapidOCR ile Tesseract (OCRmyPDF, sayfa başına tek dil) okuma kalitesi, metin katmanı silinmiş sentetik sayfalarda
   (ocr_karsilastir.SYNTH: ceket 21–25, S-7300A 12–13, JUKI 3; Türkçe sentetik sayfa). Doğru cevap orijinal metin
   katmanı. Ölçüler: sayısal değer duyarlılığı/kesinliği (verify'ın kanonik sayıları, çoklu küme), kesir ve ±,
   Türkçe harf, sayfa başına süre.
B. İki okuma kuralı (pilot.ocr.unconfirmed): Tesseract'ın sayı içeren dizileri RapidOCR'da eşi yoksa "belirsiz".
   Ölçüler: belirsiz oranı; kabul edilen ama yanlış dizi (kaçan yanlış; 0 olmalı); belirsiz kalan doğru dizi.
   Dizi "doğru": içindeki değerlerin hepsi o sayfanın gerçek değerlerinde var.
C. Strickland'ın OCR'la metin alan 7 metinsiz sayfası (doğru cevap yok): belirsiz oranı ve dizilerin listesi (elle).

Kullanım (Pilot klasöründe):  $env:PILOT_ANSWER_MODE = "bugun"; python -m bench.ocr_iki_okuma
Çıktı: eval/bench/ocr/ocr_iki_okuma_<tarih>.md, ham/ocr_iki_okuma.json
"""
from __future__ import annotations

import json
import time
from collections import Counter
from datetime import date
from typing import Any

from bench.common import PILOT_DIR

OUT = PILOT_DIR / "eval" / "bench" / "ocr"
WORK = PILOT_DIR / "data" / "ocr_test"
TR_CHARS = "çğıöşüÇĞİÖŞÜ"


def _vals(text: str) -> Counter:
    from bench.ocr_regresyon import numbers
    return Counter(v for v, _ in numbers(text))


def _tok_ok(tok: str, truth_vals: set[str]) -> bool:
    from pilot.verify import numbers_in
    vs = numbers_in(tok)
    return bool(vs) and vs <= truth_vals


def reading_scores(truth: str, got: str) -> dict[str, Any]:
    import re
    t, g = _vals(truth), _vals(got)
    hit = sum((t & g).values())
    fr = lambda s: Counter(re.findall(r"\d+/\d+", s))
    tf, gf = fr(truth), fr(got)
    out = {"deger_duyarlilik": round(hit / max(1, sum(t.values())), 3),
           "deger_kesinlik": round(hit / max(1, sum(g.values())), 3),
           "kesir": f"{sum((tf & gf).values())}/{sum(tf.values())}",
           "artı_eksi": f"{min(truth.count('±'), got.count('±'))}/{truth.count('±')}"}
    if any(c in truth for c in TR_CHARS):
        out["turkce_harf"] = f"{sum(min(truth.count(c), got.count(c)) for c in TR_CHARS)}/{sum(truth.count(c) for c in TR_CHARS)}"
    return out


def two_reading(primary: str, second: str, truth: str | None) -> dict[str, Any]:
    from pilot.ocr import numeric_tokens, unconfirmed
    from pilot.verify import numbers_in
    toks = [t for t in numeric_tokens(primary) if numbers_in(t)]
    unc = Counter(t for t in unconfirmed(primary, second) if numbers_in(t))
    acc = Counter(toks) - unc
    row: dict[str, Any] = {"dizi": len(toks), "belirsiz": sum(unc.values()), "belirsiz_diziler": sorted(unc.elements())}
    if truth is not None:
        tv = set(_vals(truth))
        row["kabul_yanlis"] = sorted(t for t in acc.elements() if not _tok_ok(t, tv))
        row["belirsiz_dogru"] = sum(_tok_ok(t, tv) for t in unc.elements())
        row["belirsiz_yanlis"] = sum(not _tok_ok(t, tv) for t in unc.elements())
    return row


def main() -> None:
    from bench import require_mode
    require_mode("bugun")
    import pymupdf

    from bench.ocr_karsilastir import SYNTH, TR_TEXT
    from pilot import ocr as O
    from pilot.registry import BY_ID
    cases = [(did, WORK / f"{did}_goruntu.pdf", BY_ID[did].source_path, pgs, "eng") for did, pgs in SYNTH.items()]
    cases.append(("turkce", WORK / "turkce_goruntu.pdf", None, [1], "tur"))
    rows, times = [], {"tesseract": [], "rapidocr": []}
    for name, img, src, pgs, lang in cases:
        tess_pdf = WORK / f"{name}_iki_okuma_tess.pdf"
        n = len(pgs)
        times["tesseract"].append(O.run_ocrmypdf(img, tess_pdf, "--skip-text", lang, list(range(1, n + 1))) / n)
        with pymupdf.open(str(tess_pdf)) as td:
            for i in range(n):
                truth = TR_TEXT if src is None else pymupdf.open(str(src))[pgs[i] - 1].get_text()
                tess = td[i].get_text()
                t = time.perf_counter()
                rap = O.rapid_page_text(img, i + 1)
                times["rapidocr"].append(time.perf_counter() - t)
                rows.append({"belge": name, "sayfa": pgs[i], "tesseract": reading_scores(truth, tess),
                             "rapidocr": reading_scores(truth, rap), "iki_okuma": two_reading(tess, rap, truth)})
                print(rows[-1]["belge"], rows[-1]["sayfa"], rows[-1]["iki_okuma"]["belirsiz"], "/",
                      rows[-1]["iki_okuma"]["dizi"], "kaçan:", rows[-1]["iki_okuma"]["kabul_yanlis"], flush=True)
    # C: Strickland'ın metinsiz sayfaları (OCR'la metin alanlar)
    rec = json.loads((WORK / "entegrasyon" / "strickland-1956.json").read_text(encoding="utf-8"))
    pages = [d["page"] for d in rec["sayfalar"] if d["kind"] == "yok" and d["chosen"] == "yeni"]
    srows = []
    with pymupdf.open(str(WORK / "entegrasyon" / "strickland-1956.pdf")) as sd:
        for p in pages:
            tess = sd[p - 1].get_text()
            rap = O.rapid_page_text(BY_ID["strickland-1956"].source_path, p)
            srows.append({"sayfa": p, "tesseract": tess.strip()[:200], "rapidocr": rap[:200], **two_reading(tess, rap, None)})
    agg = lambda k: {"dizi": sum(r["iki_okuma"]["dizi"] for r in rows), "belirsiz": sum(r["iki_okuma"]["belirsiz"] for r in rows),
                     "kabul_yanlis": sum(len(r["iki_okuma"]["kabul_yanlis"]) for r in rows),
                     "belirsiz_dogru": sum(r["iki_okuma"]["belirsiz_dogru"] for r in rows),
                     "belirsiz_yanlis": sum(r["iki_okuma"]["belirsiz_yanlis"] for r in rows)}
    summ = {"iki_okuma_sentetik": agg(None),
            "sn_sayfa": {k: round(sum(v) / max(1, len(v)), 2) for k, v in times.items()},
            "strickland": {"sayfa": len(srows), "dizi": sum(r["dizi"] for r in srows), "belirsiz": sum(r["belirsiz"] for r in srows)}}
    out = {"tarih": time.strftime("%Y-%m-%d %H:%M"), "ozet": summ, "sentetik": rows, "strickland": srows}
    (OUT / "ham").mkdir(parents=True, exist_ok=True)
    (OUT / "ham" / "ocr_iki_okuma.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    L = ["# İki okuma ölçümü: Tesseract + RapidOCR (metin katmanı olmayan sayfa)", "",
         f"{out['tarih']}. PLAN-OCR §11. Model ve ağ yok. Tesseract: OCRmyPDF `--skip-text`, sayfa başına tek dil; "
         "RapidOCR: varsayılan model (ONNX, CPU), 300 dpi.", "",
         "## A. Okuma kalitesi (sentetik: metin katmanı silinmiş, bozulmuş sayfalar; doğru cevap orijinal katman)", "",
         "| Belge | Sayfa | Okuyucu | değer duyarlılık | değer kesinlik | kesir | ± | Türkçe harf |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        for k in ("tesseract", "rapidocr"):
            s = r[k]
            L.append(f"| {r['belge']} | {r['sayfa']} | {k} | {s['deger_duyarlilik']} | {s['deger_kesinlik']} | {s['kesir']} | "
                     f"{s['artı_eksi']} | {s.get('turkce_harf', '–')} |")
    L += ["", f"Sayfa başına süre (sn): {summ['sn_sayfa']}", "",
          "## B. İki okuma kuralı (Tesseract dizisi RapidOCR'da eşi yoksa belirsiz)", "",
          "| Belge | Sayfa | sayı dizisi | belirsiz | belirsiz doğru / yanlış | **kabul edilen yanlış** |", "|---|---|---|---|---|---|"]
    for r in rows:
        b = r["iki_okuma"]
        L.append(f"| {r['belge']} | {r['sayfa']} | {b['dizi']} | {b['belirsiz']} | {b['belirsiz_dogru']} / {b['belirsiz_yanlis']} | "
                 f"{', '.join(b['kabul_yanlis']) or '0'} |")
    a = summ["iki_okuma_sentetik"]
    L += [f"| **Toplam** | | {a['dizi']} | {a['belirsiz']} | {a['belirsiz_dogru']} / {a['belirsiz_yanlis']} | **{a['kabul_yanlis']}** |", "",
          "## C. Strickland: OCR'la metin alan metinsiz sayfalar (doğru cevap yok)", "",
          "| Sayfa | sayı dizisi | belirsiz | belirsiz diziler | Tesseract (ilk 120) | RapidOCR (ilk 120) |", "|---|---|---|---|---|---|"]
    for r in srows:
        cl = lambda s: s.replace("|", "/").replace("\n", " ")[:120]
        L.append(f"| {r['sayfa']} | {r['dizi']} | {r['belirsiz']} | {', '.join(r['belirsiz_diziler']) or '–'} | {cl(r['tesseract'])} | {cl(r['rapidocr'])} |")
    p = OUT / f"ocr_iki_okuma_{date.today().isoformat()}.md"
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False))
    print(p)


if __name__ == "__main__":
    main()
