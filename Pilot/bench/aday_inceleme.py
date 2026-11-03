"""Aday soru taslağı için inceleme tablosu (Excel): soru, beklenen doküman/sayfa, o sayfadan kısa alıntı, boş onay sütunu.

Sekmeler: "Nasıl" (talimat ve sayılar), "Sorular" (aranan sorular), "Bulunamadı + netleştirme".
Alıntı: taslaktaki kanıt cümlesi (kanit); yoksa beklenen parçanın metninin başı. "Alıntı parçada" sütunu, kanıt
cümlesinin beklenen sayfadaki parça metninde birebir geçip geçmediğini otomatik gösterir (boşluk farkı yok sayılır).

Kullanım (Pilot klasöründe): python -m bench.aday_inceleme [--out eval/aday_sorular_inceleme.xlsx]
"""
import argparse
import json
import re
from pathlib import Path
from typing import Any

from bench.common import EVAL_DIR

ONAY = '"evet,hayır,düzelt"'
EXCERPT = 300


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip().lower()


def page_chunks(chunks: list[dict[str, Any]], doc: str, pages: list[int]) -> list[dict[str, Any]]:
    return [c for c in chunks if c["doc_id"] == doc and (not pages or set(c["pages"]) & set(pages))]


def sources(it: dict[str, Any]) -> list[tuple[str, list[int], str | None]]:
    if it.get("kabul"):
        return [(k["doc"], k.get("pages") or [], k.get("chunk_id")) for k in it["kabul"]]
    return [(d, it.get("expect_pages") or [], None) for d in it.get("expect_docs") or []]


def excerpt_and_check(it: dict[str, Any], chunks: list[dict[str, Any]],
                      by_id: dict[str, dict[str, Any]]) -> tuple[str, str]:
    srcs = sources(it)
    texts = []
    for doc, pages, cid in srcs:
        texts += [by_id[cid]["text"]] if cid in by_id else [c["text"] for c in page_chunks(chunks, doc, pages)]
    if it.get("kanit"):
        found = any(norm(it["kanit"]) in norm(t) for t in texts)
        return it["kanit"], ("evet" if found else "HAYIR: kontrol et") if texts else "parça yok"
    if texts:
        t = re.sub(r"\s+", " ", texts[0]).strip()
        return (t[:EXCERPT] + ("…" if len(t) > EXCERPT else "")), "kanıt cümlesi yok (parçanın başı)"
    return "", "–"


def src_text(it: dict[str, Any]) -> tuple[str, str]:
    srcs = sources(it)
    return ("; ".join(d for d, _, _ in srcs),
            "; ".join(f"{d}: s. {', '.join(map(str, p))}" if len(srcs) > 1 else ", ".join(map(str, p))
                      for d, p, _ in srcs))


def build(out: Path) -> Path:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation

    from pilot.chunk import read_chunks
    from pilot.registry import BY_ID

    items = json.loads((EVAL_DIR / "aday_sorular.json").read_text(encoding="utf-8"))
    chunks = read_chunks()
    by_id = {c["chunk_id"]: c for c in chunks}
    special = [it for it in items if it.get("expect_not_found") or it.get("expect_clarify")]
    normal = [it for it in items if it not in special]

    wb = Workbook()
    head_font, head_fill = Font(bold=True, color="FFFFFF"), PatternFill("solid", fgColor="305496")
    onay_fill = PatternFill("solid", fgColor="FFF2CC")
    wrap = Alignment(wrap_text=True, vertical="top")

    def sheet(ws, headers: list[tuple[str, int]], rows: list[list[Any]], onay_col: int) -> None:
        ws.append([h for h, _ in headers])
        for i, (_, w) in enumerate(headers, 1):
            ws.column_dimensions[ws.cell(1, i).column_letter].width = w
            ws.cell(1, i).font, ws.cell(1, i).fill = head_font, head_fill
        for r in rows:
            ws.append(r)
        for row in ws.iter_rows(min_row=2):
            for c in row:
                c.alignment = wrap
            row[onay_col - 1].fill = onay_fill
        dv = DataValidation(type="list", formula1=ONAY, allow_blank=True, showErrorMessage=True,
                            errorTitle="Onay", error="evet, hayır ya da düzelt")
        ws.add_data_validation(dv)
        col = ws.cell(1, onay_col).column_letter
        dv.add(f"{col}2:{col}{len(rows) + 1}")
        ws.freeze_panes = "C2"
        ws.auto_filter.ref = ws.dimensions

    ws = wb.active
    ws.title = "Nasıl"
    for line in ["Aday soru taslağı: inceleme tablosu", "",
                 f"Toplam {len(items)} soru: {len(normal)} aranan soru ('Sorular' sekmesi), "
                 f"{sum(1 for i in special if i.get('expect_not_found'))} bulunamadı ve "
                 f"{sum(1 for i in special if i.get('expect_clarify'))} netleştirme ('Bulunamadı + netleştirme').",
                 "",
                 "Her satırda sarı 'Onay' hücresinden seçin: evet (soru ve beklenen kaynak doğru), hayır (soru setten "
                 "çıksın), düzelt (ne düzelecekse 'Not' sütununa yazın: doğru sayfa, doğru cevap, sorunun yeni hali).",
                 "Kontrol edilecek: soru anlaşılır mı; beklenen doküman ve sayfa doğru mu; alıntı soruyu gerçekten "
                 "cevaplıyor mu; beklenen cevap alıntıyla uyuşuyor mu.",
                 "'Alıntı parçada' sütunu otomatik: kanıt cümlesinin beklenen sayfanın metninde birebir geçip "
                 "geçmediği. 'HAYIR' olanlara önce bakın.",
                 "Bulunamadı soruları: dokümanlarda gerçekten cevabı yok mu ('Neden cevapsız' sütunu nasıl "
                 "arandığını yazar). Netleştirme soruları: soru gerçekten birden fazla ürüne uyuyor mu.",
                 "", "Onaylananlar eval/aday_sorular.json içinde dogrulandi: true yapılır; tablo geri okunarak "
                 "işlenebilir (ID sütunu)."]:
        ws.append([line])
    ws.column_dimensions["A"].width = 140
    ws["A1"].font = Font(bold=True, size=13)

    rows = []
    for n, it in enumerate(normal, 1):
        alinti, check = excerpt_and_check(it, chunks, by_id)
        docs, pages = src_text(it)
        titles = "; ".join(f"{BY_ID[d].product} ({BY_ID[d].file})" for d in docs.split("; ") if d in BY_ID)
        rows.append([n, it["id"], it["kind"], it["q"], docs, titles, pages, it.get("bolum", ""), alinti, check,
                     it.get("cevap", ""), ", ".join(it.get("zorluk") or []), "", ""])
    sheet(wb.create_sheet("Sorular"),
          [("No", 5), ("ID", 7), ("Tür", 11), ("Soru", 45), ("Beklenen doküman", 18), ("Doküman", 28),
           ("Sayfa", 9), ("Bölüm", 22), ("Alıntı (sayfadan)", 60), ("Alıntı parçada", 14), ("Beklenen cevap", 30),
           ("Etiketler", 16), ("Onay", 10), ("Not", 40)], rows, 13)

    rows = []
    for n, it in enumerate(special, 1):
        if it.get("expect_not_found"):
            rows.append([n, it["id"], "bulunamadı", it["q"], it.get("nf_kontrol", ""), "", "", "\"Bulunamadı\" demeli", ""])
        else:
            docs, pages = src_text(it)
            rows.append([n, it["id"], "netleştirme", it["q"], "", ", ".join(it.get("olasi_urunler") or []), pages,
                         it.get("cevap", ""), "", ""])
    rows = [r + [""] * (10 - len(r)) for r in rows]
    sheet(wb.create_sheet("Bulunamadı + netleştirme"),
          [("No", 5), ("ID", 7), ("Tür", 12), ("Soru", 45), ("Neden cevapsız (nasıl arandı)", 55),
           ("Olası ürünler", 30), ("Her üründe kaynak", 30), ("Beklenen davranış / cevap", 40), ("Onay", 10),
           ("Not", 40)], rows, 9)
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=EVAL_DIR / "aday_sorular_inceleme.xlsx")
    print(build(ap.parse_args().out))


if __name__ == "__main__":
    main()
