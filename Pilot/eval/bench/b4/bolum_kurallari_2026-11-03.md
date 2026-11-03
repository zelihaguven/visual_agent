# Bölüm adı kuralları: kural bazında etki (2026-11-03)

Kod: `pilot/chunk.py` (Kural 1–4), testler `tests/test_parse_chunk.py`. Kuru çalıştırma: 4.232 parça önce ve sonra, kimlikler birebir aynı, `section` ve `embed_text` dışında değişen alan yok. Bölümü değişen parça: **606** (doküman bazında: gl-pd-14-04a 145, gl-pd-07-14a 108, brother-s7300a 14, brother-s7300b 15, granovsky-1986 273, juki-mo6800s 48, mrcoffee-2003 3).

Her kural tek başına açılarak sayıldı (Kural 3, Kural 2'nin üstüne); bir parça birden çok kurala girebilir. Örnekler farklı önce→sonra çiftlerinden; Kural 1'de her nedenden, Kural 2'de inceleme tablosundaki A005–A007 örneği dahil. Kural 4 bu korpusta yalnız 2 parçaya uygulandı.

## Kural 1 (OCR çöpü, uyarı etiketi, üst bilgi): 366 parça

Başlık etiketli öğe OCR çöpü (276), uyarı etiketi (79: NOTE, CAUTION, WARNING …) ya da sayfa üst bilgisinin OCR varyantıysa (11: "OLlPD 07-14A") bölüm adı olmaz; önceki bölüm sürer.

| Parça | Önce | Sonra |
|---|---|---|
| `gl-pd-14-04a-00147` | CAUTION: | USE AND CARE |
| `juki-mo6800s-00026` | WARNING : | 3. INSTALLATION |
| `granovsky-1986-00572` | c: o o | (boş) |
| `mrcoffee-2003-00014` | EE.UU. 1-800-MR COFFEE (1-800-672-6333) Canadá 1-800-667-8623 | Reparaciones |
| `gl-pd-07-14a-00160` | OLlPD 07-14A | 3.11.1.2 Fly seaming and stitching |

## Kural 2 (tablo adı): 248 parça

Tablo satırları tablonun adını taşır ("TABLE V. …"); ad tablonun hemen altında ya da üstünde, iki tablonun arasındakiler dokümanın çoğunluk düzenine göre bağlanır.

| Parça | Önce | Sonra |
|---|---|---|
| `gl-pd-07-14a-00071` | 3.5.5.1 Thread (Type II trouser) | 3.5.5.1 Thread (Type II trouser) > TABLE II. Thread requirements, Type II trouser only. |
| `gl-pd-07-14a-00097` | 3.8.1 Size label | 3.8.1 Size label > TABLE III. Size label. |
| `gl-pd-07-14a-00136` | 3.10 List of pattem parts | 3.10 List of pattem parts > TABLE IV. List ofpattem parts. |
| `gl-pd-07-14a-00215` | 4. VERIFICATION | 4. VERIFICATION > Table VIII. Trouser visual examination. |
| `gl-pd-14-04a-00182` | 3.11.1.1 Repair of stitch. | 3.11.1.1 Repair of stitch. > TABLE V. Seam and stitch types |

## Kural 3 (adı bilinen tabloda üst madde), Kural 2'nin üstüne: 186 parça

Adı bilinen tabloda en az üç düzeyli numaralı alt başlığın (3.11.1.1) kapsamı biter; satırlar en yakın üst maddeye bağlanır. Yan etkisi: doğru alt başlık da üste çıkar ("3.5.5 Thread …" → "3.5 Components."), bilgiyi tablo adı taşır.

| Parça | Önce | Sonra |
|---|---|---|
| `gl-pd-07-14a-00062` | 3.5.5 Thread (Type I trouser) > TABLE I. Thread requirements, Type I trouser only. | 3.5 Components. > TABLE I. Thread requirements, Type I trouser only. |
| `gl-pd-07-14a-00097` | 3.8.1 Size label > TABLE III. Size label. | 3.8 Labels > TABLE III. Size label. |
| `gl-pd-14-04a-00078` | 3.5.1.2 Upper sleeve pocket slide fastener > TABLE I. Thread requirements, Type I only. | 3.5.1 Slide fasteners. > TABLE I. Thread requirements, Type I only. |
| `gl-pd-14-04a-00084` | 3.5.6 Thread (Types II and III only, all styles and classes) > TABLE II. Thread requirements, Types II and III only. | 3.5 Components materials and shade (All types, styles and classes) > TABLE II. Thread requirements, Types II and III only. |
| `gl-pd-14-04a-00255` | 3.11.3 Bar-tacks and back-tacks > TABLE VIIB. Style B. Female finished measurements (inches) all types and classes | 3.11 Configuration > TABLE VIIB. Style B. Female finished measurements (inches) all types and classes |

## Kural 4 (PDF yer imi, boş bölüm): 2 parça

Bölümü boş kalan parça PDF yer iminden ad alır; yer imleri OCR'dan üretilmişse (Granovsky) kullanılmaz. Bu korpusta yalnız 2 kapak parçası.

| Parça | Önce | Sonra |
|---|---|---|
| `brother-s7300a-00000` | (boş) | Cover |

## Düzeltmeden sonra kalanlar

- OCR çöpü ve uyarı etiketi başlık: 0. Yanlış başlıklı tablo satırları tablo adına bağlandı.
- Genel kurala girmeyen etiket metni: 22 parça ("INSECT REPELLENT APPAREL", "DO NOT REMOVE THIS LABEL", Bosch "ASSUREZ-VOUS TOUJOURS"); dokümana özgü kural gerekir, dokunulmadı.
- Boş bölüm: 996 → 1.267 (Granovsky 958, Strickland 307): "c: o o" gibi yanlış başlık yerine boş; iki kitapta geçerli başlık ya da yer imi yok.
