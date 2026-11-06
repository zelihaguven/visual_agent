# Yerel OCR karşılaştırması, CPU: OCRmyPDF ve Docling + Tesseract (2026-11-06)

Plan: [docs/PLAN-OCR.md §8](../../../../docs/PLAN-OCR.md). Araç: `bench/ocr_karsilastir.py`. Ham sonuç: `ham/ocr_karsilastirma.json`.
- Kurulum: Tesseract 5.4 (`tur`, `eng`); OCRmyPDF 17.13, Ghostscript'siz (`--rasterizer pypdfium --output-type pdf`).
- Model ve bulut çağrısı yok. CPU, geliştirme dizüstü bilgisayarı.
- İki adayın yapısı (tablo, kutu) Docling'den okunur: OCRmyPDF çıktısı Docling ile (OCR kapalı, bugünkü ayrıştırma), Docling + Tesseract kendi içinde (tam sayfa OCR).

## (i) Bilinen OCR hataları: pantolon şartnamesi, 9 sayfa (`-l tur+eng`)

Her hücre: kalan hatalı yazım / doğru yazım sayısı.

| Hata (doğrusu) | Bugünkü katman | **OCRmyPDF `--redo-ocr`** | Docling + Tesseract |
|---|---|---|---|
| "112 inch" (1/2 inch) | 19 / 0 | **0 / 19** | 5 / 14 |
| "114 inch" (1/4 inch) | 11 / 4 | **0 / 15** | 8 / 7 |
| "7-114" (7-1/4) | 1 / 0 | **0 / 1** | 0 / 1 |
| "3116" (3/16) | 3 / 4 | **0 / 7** | 3 / 4 |
| "IS min" (15 min) | 1 / 0 | **0 / 1** | 0 / 1 |
| Süre (sn/sayfa) | – | **1,1** | 5,3 |

OCRmyPDF bilinen hataların hepsini düzeltti. Docling + Tesseract kesirlerin yarısını düzeltemedi.

## (ii) Metin katmanı silinmiş sentetik sayfalar (300 dpi, eğiklik 1,2°, bulanıklık, JPEG 70, gri ton)

Doğru cevap: orijinal dijital katman (Docling, OCR kapalı).

| Belge (sayfa) | Aday | sayı duyarlılık | sayı kesinlik | metin benzerliği | tablo hücresi | kutu IoU (eşleşen) | sn/sayfa |
|---|---|---|---|---|---|---|---|
| Ceket (5) | OCRmyPDF | 0,97 | 0,99 | 0,85 | 257/257 | 0,69 (23) | 1,4 OCR + 4,8 ayrıştırma |
| | Docling + Tess. | 0,98 | 1,00 | 0,74 | 257/257 | 0,73 (21) | 6,8 |
| S-7300A (2) | OCRmyPDF | 0,88 | 0,95 | 0,57 | 40/49 | 0,52 (23) | 2,0 + 4,6 |
| | Docling + Tess. | 0,95 | 0,98 | 0,57 | 43/49 | 0,56 (23) | 5,5 |
| JUKI (1) | OCRmyPDF | 0,93 | 0,99 | 0,91 | 44/43 | 0,52 (5) | 14,1 + 5,7 |
| | Docling + Tess. | 0,92 | 0,97 | 0,89 | 43/43 | 0,58 (5) | 8,3 |

- Sayısal değer doğruluğu iki adayda benzer: %88–98 duyarlılık, %95–100 kesinlik. Kaçan sayıların çoğu küçük yazılı tablo dipnotları ve şekil üzerindeki etiketler.
- Tablo hücreleri büyük ölçüde korunuyor.
- **Kutu örtüşmesi orta düzeyde** (IoU 0,5–0,7). Sayfa vurgusu doğru bölgeyi gösterir ama dijital kadar sıkı değil. Eğiklik 1,2° ve bulanıklık bunun önemli kısmı.

## (iii) Türkçe karakter: dil ayarı belirleyici

| Ayar (Tesseract) | Temiz görüntü: benzerlik / Türkçe harf | Bozulmuş görüntü |
|---|---|---|
| **`-l tur`** | **0,99 / 70/70** | **0,95 / 64/70** |
| `-l tur+eng` | 0,78 / 40/70 | 0,30 / 41/70 |
| `-l eng+tur` | 0,52 / 8/70 | 0,49 / 25/70 |

Karşılaştırma koşusunda iki aday da `tur+eng` ile 39–43/70 aldı. **İki dili birlikte vermek zarar veriyor.** OCR dili belgenin (ya da sayfanın) diline göre seçilmeli: kayıttaki `default_lang` / `lang_ranges` alanı. Türkçe belge `tur`, İngilizce belge `eng`. Sayılar her ayarda 6/6.

## Strickland'ın metin katmanı olmayan 28 sayfası

- Bunlar çizim, levha ve boş sayfalar; metin sayfası değil.
- OCRmyPDF 7 sayfada anlamsız karakter dizisi üretti ("ııuııuııı…", "VPCAOLLEAELDAP0…"). Docling + Tesseract hiçbir şey çıkarmadı.
- **Sonuç:** OCR'dan sonra metin katmanı kalite kontrolü (`text_layer.quality`) şart. Düşük kaliteli OCR metni indekse alınmamalı; sayfa şekil sayfası olarak kalır.

## Granovsky: bozuk (harf aralıklı) katman, 6 sayfa

| | kalite skoru (sayfa başına) | sn/sayfa |
|---|---|---|
| Bugünkü katman | 0,28–0,36 | – |
| OCRmyPDF `--redo-ocr` | 0,28–0,34 (1 sayfada 0,80) | 3,1 |
| **OCRmyPDF `--force-ocr`** | **0,92–1,00** | 3,2 |
| Docling + Tesseract | 0,99–1,00 | 4,3 |

`--redo-ocr` bu katmanı "OCR katmanı" olarak tanımıyor ve dokunmuyor; **`--force-ocr` gerekiyor.** Metin katmanı kontrolü "zayıf" dediği sayfada `--force-ocr`, "taranmış" dediği sayfada `--redo-ocr` kullanılmalı.

## Ölçüt: 16 OCR etiketli soruda cevaplanabilirlik (model çağrısı yok)

Araç: `bench/ocr_soru_olcumu.py`, ham sonuç `ham/ocr_soru_olcumu.json`. Yöntem:
- belgeler OCRmyPDF ile yeniden OCR'landı (pantolon `--redo-ocr`, Granovsky `--force-ocr`; dil `eng`, belge dili);
- uygulamanın ayrıştırma + parçalama + bge-m3/BM25 kodu, geçici bellek indeksiyle (gerçek indekse ve önbelleğe dokunulmadı);
- iki sürüm aynı sayfa alt kümesinde (beklenen sayfa ± 3);
- arama uygulamanın hibrit araması; BM25 sorgusu hat kaydındaki çeviri.

**"Cevaplanabilir"** = beklenen sayfa ilk 8 kaynakta **ve** beklenen değer bu parçalarda birebir geçiyor. Cevapsız kalma oranının modelsiz vekili.

| | beklenen sayfa ilk 8'de | beklenen değer parçada | **cevaplanabilir** |
|---|---|---|---|
| Bugünkü OCR katmanı | 16/16 | 5/12 | **9/16** |
| **OCRmyPDF ile yeniden OCR** | 16/16 | **12/12** | **16/16** |

- **Pantolon (11 soru): 4/11 → 11/11.** Arama doğru sayfayı iki durumda da buluyor; fark değerde.
  - Bugünkü katmanda "6–7-1/4", "3/16–1/4", "1/8–3/16", "3/8–1/2", "15" bozuk yazılı ("7-114", "3116", "112", "IS"). Doğrulayıcı geçirmediği için bu 7 soru bugün cevapsız kalıyor: A022, A025, A026, A027, A030, A148, A154.
  - A154'te beklenen sayfa 7. sıradan 1. sıraya çıktı.
- **Granovsky (5 soru): 5/5 → 5/5.** Uygulamanın harf aralıklı katmanı birleştirme yedeği aramayı zaten kurtarıyordu.
- Model çağrısı gerekmedi.
