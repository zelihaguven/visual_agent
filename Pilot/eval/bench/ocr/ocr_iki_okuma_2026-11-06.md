# İki okuma ölçümü: Tesseract + RapidOCR (metin katmanı olmayan sayfa)

2026-11-06 17:34. PLAN-OCR §11. Model ve ağ yok. Tesseract: OCRmyPDF `--skip-text`, sayfa başına tek dil; RapidOCR: varsayılan model (ONNX, CPU), 300 dpi.

## A. Okuma kalitesi (sentetik: metin katmanı silinmiş, bozulmuş sayfalar; doğru cevap orijinal katman)

| Belge | Sayfa | Okuyucu | değer duyarlılık | değer kesinlik | kesir | ± | Türkçe harf |
|---|---|---|---|---|---|---|---|
| gl-pd-14-04a | 21 | tesseract | 0.75 | 1.0 | 2/2 | 0/0 | – |
| gl-pd-14-04a | 21 | rapidocr | 1.0 | 1.0 | 2/2 | 0/0 | – |
| gl-pd-14-04a | 22 | tesseract | 0.809 | 0.95 | 1/1 | 0/5 | – |
| gl-pd-14-04a | 22 | rapidocr | 1.0 | 1.0 | 1/1 | 5/5 | – |
| gl-pd-14-04a | 23 | tesseract | 0.983 | 0.983 | 16/16 | 0/0 | – |
| gl-pd-14-04a | 23 | rapidocr | 1.0 | 1.0 | 16/16 | 0/0 | – |
| gl-pd-14-04a | 24 | tesseract | 1.0 | 0.987 | 29/29 | 0/0 | – |
| gl-pd-14-04a | 24 | rapidocr | 1.0 | 1.0 | 29/29 | 0/0 | – |
| gl-pd-14-04a | 25 | tesseract | 1.0 | 1.0 | 21/21 | 0/0 | – |
| gl-pd-14-04a | 25 | rapidocr | 1.0 | 1.0 | 21/21 | 0/0 | – |
| brother-s7300a | 12 | tesseract | 0.952 | 1.0 | 2/2 | 0/0 | – |
| brother-s7300a | 12 | rapidocr | 1.0 | 0.977 | 2/2 | 0/0 | – |
| brother-s7300a | 13 | tesseract | 0.952 | 1.0 | 0/0 | 0/0 | – |
| brother-s7300a | 13 | rapidocr | 1.0 | 0.5 | 0/0 | 0/0 | – |
| juki-mo6800s | 3 | tesseract | 0.941 | 0.985 | 0/0 | 0/0 | – |
| juki-mo6800s | 3 | rapidocr | 0.956 | 1.0 | 0/0 | 0/0 | – |
| turkce | 1 | tesseract | 0.833 | 0.833 | 0/0 | 0/2 | 64/70 |
| turkce | 1 | rapidocr | 1.0 | 1.0 | 0/0 | 2/2 | 48/70 |

Sayfa başına süre (sn): {'tesseract': 3.6, 'rapidocr': 5.2}

## B. İki okuma kuralı (Tesseract dizisi RapidOCR'da eşi yoksa belirsiz)

| Belge | Sayfa | sayı dizisi | belirsiz | belirsiz doğru / yanlış | **kabul edilen yanlış** |
|---|---|---|---|---|---|
| gl-pd-14-04a | 21 | 18 | 0 | 0 / 0 | 0 |
| gl-pd-14-04a | 22 | 34 | 2 | 0 / 2 | 0 |
| gl-pd-14-04a | 23 | 37 | 1 | 0 / 1 | 0 |
| gl-pd-14-04a | 24 | 49 | 1 | 0 / 1 | 0 |
| gl-pd-14-04a | 25 | 38 | 0 | 0 / 0 | 0 |
| brother-s7300a | 12 | 39 | 1 | 1 / 0 | 0 |
| brother-s7300a | 13 | 22 | 0 | 0 / 0 | 0 |
| juki-mo6800s | 3 | 61 | 3 | 2 / 1 | 0 |
| turkce | 1 | 5 | 1 | 0 / 1 | 0 |
| **Toplam** | | 303 | 9 | 3 / 6 | **0** |

## C. Strickland: OCR'la metin alan metinsiz sayfalar (doğru cevap yok)

| Sayfa | sayı dizisi | belirsiz | belirsiz diziler | Tesseract (ilk 120) | RapidOCR (ilk 120) |
|---|---|---|---|---|---|
| 1 | 0 | 0 | – | A Tailoring  Manual | 華 Tailoring A Manual |
| 3 | 0 | 0 | – | A Tailoring Manual | A Tailoring Manual |
| 13 | 0 | 0 | – | A Tailoring Manual | A Tailoring Manual |
| 26 | 1 | 0 | – | 12 | 1 g. h. k. 一 Figure 2 (Continued) 12 |
| 61 | 8 | 3 | 1, 2S, 8 | !  \  J  iN  l  Q  Nn  47  1]  Figure 21 (Problems 10, 11)  > ee  aN => >>> =  %  KN  XY  _ mr he Mee tienes  ‘  IN  ee  | a. b. Figure 21 (Problem 9) 10 11 Figure 21 (Problems 10, 11) 47 |
| 66 | 1 | 0 | – | 52 | b. a. C. g. h. FiFurr23 52 |
| 157 | 1 | 0 | – | 1. Right side | Slacks 143 b. At top front edge stitch pocket and slacks the width of 2 inches across the top to finish for buttonhole o |
