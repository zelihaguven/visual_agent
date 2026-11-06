# Plan: taranmış belgeler için yerel OCR (pilot öncesi zorunlu iş)

> Karar 2026-11-06: OCR pilot öncesi zorunlu. Öncelik listesinde gri akışın hemen arkasında. **Bu belge plandır; kod yok.**
> İlgili: [PRD "Taranmış belgeler ve OCR"](PRD.md), [kurulum listesi](KURULUM-KENDI-BELGELER.md), A9 kararı (sayfa görüntüsü buluta gitmez).

## 1. Bugünkü durum

- Ayrıştırma Docling ile **OCR kapalı** yapılıyor (`pilot/parse.py`, `do_ocr = False`). PDF'in **kendi metin katmanı** kullanılıyor.
- Taranmış PDF'te bu katmanı tarayıcı yazılımı (ör. FineReader) eklemişse çalışıyor. Yedekler:
  - PyMuPDF metin katmanı (Docling bir sayfanın metnini büyük oranda kaçırırsa);
  - harf aralıklı katmanın birleştirilmesi ("C a r d" → "Card").
- **Metin katmanı olmayan tarama (yalnız görüntü) hiç aranamıyor:** o sayfalardan parça çıkmıyor, kapsam raporunda da uyarı yok.
- **Mevcut OCR katmanlarında görülen hatalar** (test belgeleri: GL-PD-07-14A pantolon, Granovsky):
  - kesir ve rakam: "112 inch" = ½, "7-114" = 7-1/4, "3/8 - 112";
  - harf/rakam: "IS min" = 15, "GLlPD" = GL-PD, "Apri12007" = April 2007;
  - tablo satırı kaybı.
- Doğrulayıcı bu hatalardan **yanlış değer üretmiyor**: model "112"yi ½ diye yorumlarsa alıntıda ½ olmadığı için ✖ olur. Ama soru **cevapsız kalıyor**.

## 2. Yüklemede metin katmanı kontrolü

Her sayfa için, yükleme sırasında ve kapsam raporunda (G13):
1. **Metin katmanı var mı:** PyMuPDF ile sayfa metni. Sayfanın büyük kısmını bir görüntü kaplıyor ve metin < 50 karakterse "taranmış, metin katmanı yok" → **OCR yolu**.
2. **Metin katmanının kalitesi:** sözlükte olmayan kelime oranı, harf aralıklı dizi, rakam/harf karışık kelimeler ("GLlPD", "Apri12007"). Eşiği aşan sayfa "OCR katmanı zayıf" diye işaretlenir; yeniden OCR seçeneği sunulur.
3. Kapsam raporu: sayfa sayısı, metin katmanı olmayan / zayıf sayfa listesi, OCR uygulanan sayfalar ve sayfa başına OCR güveni. Yetkili onaylamadan belge sorgulanabilir olmaz.

## 3. Yerel OCR seçenekleri

Sayfa görüntüsü sunucudan çıkmaz (A9). Dil: Türkçe + İngilizce. Kritik olan tablo ve ölçü değerleri: kesir, ±, aralık, birim.

| Seçenek | Lisans | Tablo | Sayılar / kesir | Kutu (vurgu için) | CPU süresi (300 dpi, sayfa) | GPU | Not |
|---|---|---|---|---|---|---|---|
| **Docling + OCR** (EasyOCR / Tesseract / RapidOCR arka ucu, TableFormer) | MIT | iyi (TableFormer) | arka uca bağlı | var | 3–10 sn | hızlanır | Bugünkü ayrıştırma hattının aynısı; bbox, tablo satırı, parça yapısı korunur. **Entegrasyon en kolay** |
| Tesseract 5 (tur + eng) | Apache-2.0 | zayıf (yapı yok) | iyi; "½" gibi kesir karakterleri sık hatalı | var | 1–3 sn | yok | Hafif, olgun; Docling arka ucu olarak da kullanılabilir |
| PaddleOCR (PP-OCRv4/v5, PP-Structure) | Apache-2.0 | iyi (tablo yapısı) | iyi | var | 2–5 sn | 0,2–0,5 sn (T4) | Çok dilli Latin modeli Türkçeyi kapsar |
| EasyOCR | Apache-2.0 | yok | orta | var | 5–15 sn | hızlanır | Docling'in varsayılan OCR arka ucu |
| docTR | Apache-2.0 | yok | iyi | var | 3–8 sn | hızlanır | Latin dilleri |
| **Yerel görsel model ile sayfa okuma** (Qwen2.5-VL 7B, olmOCR 7B, GOT-OCR2) | Apache-2.0 (model kartına göre) | **en iyi** (tabloyu Markdown/HTML verir) | en iyi (½, ± bağlamdan) | **yok / güvenilmez** | pratik değil (dakikalar) | 5–20 sn; 7B için 16–24 GB VRAM (4-bit ~8 GB) | **Uydurma riski:** model değeri "düzeltebilir". Tek başına kaynak sayılmaz |

**Önerilen tasarım (ölçümle doğrulanacak):**
1. **Birincil: Docling + OCR** (arka uç: ölçümde en iyi çıkan Tesseract ya da PaddleOCR/RapidOCR). Metin, kutular ve tablo satırları bugünkü parça yapısına girer; sayfa vurgusu çalışmaya devam eder.
2. **Değer ikinci okuması (isteğe bağlı, GPU varsa):** sayısal değer içeren tablo hücreleri ve satırlar yerel görsel modelle de okunur.
   - İki okuma **uyuşursa** değer kabul edilir.
   - Uyuşmazsa parça "OCR değeri belirsiz" diye işaretlenir. O değer doğrulanmış gösterilmez (sıfır tolerans); cevapsız kalır ve kaynak sayfa gösterilir.
3. OCR'lı parçalar `ocr: true` ve sayfa güveniyle saklanır. Doğrulama değişmez: alıntı OCR metninde birebir olmalı.

## 4. Sunucu kaynak ihtiyacı (bir kerelik, yüklemede; soru anında değil)

| Kurulum | 1.000 taranmış sayfa | Not |
|---|---|---|
| Docling + Tesseract, 8 çekirdek CPU | ~0,5–1,5 saat | GPU gerekmez |
| Docling + PaddleOCR, CPU | ~1–2 saat | |
| Docling + PaddleOCR, GPU (T4 / 16 GB) | ~5–15 dk | |
| + Görsel model ikinci okuma (yalnız sayısal tablo sayfaları, ~%20), GPU 24 GB | +~0,5–1 saat | 7B model; 4-bit ile 12–16 GB yeter |

Süreler yaklaşık (yayımlanmış ölçümler ve benzer donanım); karar §5'teki ölçümle verilir.

## 5. Test planı

**Ölçütler:**
- **sayısal değer doğruluğu:** sayı, kesir (½ ¼ 3/8), ±, aralık, birimli değer; kelime değil değer düzeyinde birebir;
- karakter hata oranı (CER);
- tablo satırı kurtarma oranı;
- sayfa başına süre;
- `ocr` etiketli sorularda **cevapsız kalma oranı** ve doğrulanmış görünen yanlış (**0 olmalı**).

| Set | İçerik | Doğru cevap | Amaç |
|---|---|---|---|
| A: sentetik | Metin katmanı temiz dijital sayfalar (GL-PD-14-04A ceket şartnamesinin tablo sayfaları, S-7300A ayar tabloları). 200 ve 300 dpi görüntüye çevrilir, tarama bozulması eklenir (eğiklik ±2°, bulanıklık, JPEG, gri ton) | Metin katmanı | Seçenekleri değer doğruluğu ve tablo kurtarmada karşılaştırmak |
| B: bilinen hatalar | GL-PD-07-14A pantolon ve Granovsky'nin taranmış sayfaları | Elle okunan değerler | "112" = ½, "IS" = 15, "7-114" vakalarının yeni OCR'da düzelip düzelmediği; bugünkü katmanla yan yana |
| C: soru düzeyi | Mevcut setteki 14 `ocr` etiketli soru | Onaylı beklenen değerler | Cevapsız kalma oranı: bugünkü katman ile yeni OCR. Doğrulanmış görünen yanlış 0. Model çağrısı ~0,01 USD |
| D: gerçek | Pilot birimimizin gerçek taranmış belgesi (Adım 6) | Kullanımda not edilen sorular | Pilot öncesi son kontrol |

**Kabul:**
- Set A'da sayısal değer doğruluğu, bugünkü OCR katmanlarının hatalı vakalarını (Set B) düzeltir;
- Set C'de cevapsız kalma düşer ve doğrulanmış görünen yanlış 0 kalır;
- 1.000 sayfa, hedef sunucuda bir gecede (≤ 8 saat) işlenir.

## 6. Sıra

1. Yüklemede metin katmanı kontrolü ve kapsam raporu uyarısı (küçük iş; OCR'sız bile değerli: aranamayan sayfa görünür olur).
2. Set A ve B ölçümü: Docling + Tesseract / PaddleOCR / RapidOCR. Görsel model GPU'lu sunucuda ayrıca.
3. Seçilen OCR'ın ayrıştırma hattına bağlanması (`do_ocr` sayfa bazında: yalnız metin katmanı olmayan ya da zayıf sayfalar).
4. Set C ve D.

## 7. Karar: iki aşama (2026-11-06)

### a) Pilot öncesi, CPU'da (gri akıştan sonra kodlanacak)

**Seçim: Docling + Tesseract arka ucu** (Docling'in OCR seçeneği, `TesseractOcrOptions`, dil `tur+eng` *(§9 ile değişti: tek dil, kayıttaki dile ya da dil aralığına göre, sayfa başına)*).
- **Neden Docling:** OCR çıktısı bugünkü ayrıştırma hattına aynen girer: öğe kutuları (sayfa vurgusu), TableFormer ile tablo yapısı ve satır parçaları, başlık sınırlı parçalama. Ayrı bir Tesseract hattı tablo satırlarını ve kutu-öğe eşlemesini yeniden yazmayı gerektirirdi.
- **Neden Tesseract arka ucu** (Docling'in varsayılanı EasyOCR yerine):
  - CPU'da 2–5 kat hızlı;
  - Türkçe dil verisi resmi;
  - rakamda olgun; yaygın, Apache-2.0.
  - EasyOCR CPU'da sayfa başına 5–15 sn.
- **Sayfa bazında:** `do_ocr` yalnız metin katmanı olmayan ya da zayıf sayfalarda. Metin katmanı iyi sayfalar bugünkü gibi; süre ve risk yalnız gereken sayfada.
- **Kurulum gereği:** sunucuda Tesseract ikilisi ve `tur`, `eng` dil verileri *(§9 ile değişti: tek dil, kayıttaki dile ya da dil aralığına göre, sayfa başına)* (Windows: UB Mannheim kurulumu; Linux: paket). Kurulum listesine madde olarak girer.
- **Yedek seçenek:** RapidOCR (ONNX, sistem ikilisi gerektirmez). Türkçe karakterlerde (ç ğ ı ö ş ü) Latin modeli ölçülür; Tesseract Set A'da kesir/± değerlerinde geride kalırsa denenir.

**Test** (§5'in Set A, B, C'si):
- sentetik bozulmuş sayfalar;
- bilinen hata türleri: "112" = ½, "IS" = 15, "7-114" = 7-1/4;
- 14 OCR etiketli soruda cevapsız kalma oranı (bugünkü katman ile yeni OCR);
- doğrulanmış görünen yanlış 0.

**Süre tahmini (iş):**

| İş | Tahmin |
|---|---|
| Yüklemede sayfa başına metin katmanı ve kalite kontrolü + kapsam raporu uyarısı | 0,5 gün |
| Docling OCR'ın sayfa bazında açılması (Tesseract arka ucu), parça işaretleri (`ocr`, güven) | 1 gün |
| Set A üreticisi (sayfa → görüntü, bozulma) ve değer düzeyi karşılaştırma aracı | 1 gün |
| Ölçüm: Set A (~100 sayfa × 2 arka uç, CPU ~3–10 sn/sayfa ≈ 15–35 dk), Set B, Set C (~0,01 USD) ve rapor | 0,5–1 gün |
| **Toplam** | **~3–3,5 iş günü** |

İşleme süresi (CPU, 8 çekirdek): taranmış 1.000 sayfa ~0,5–1,5 saat, yüklemede bir kez.

### b) Sunucu gelince (yalnız plan)

- Görsel modelle (yerel, GPU) ikinci okuma: sayısal değer içeren tablo hücreleri ve satırlar.
- **"İki okuma uyuşursa kabul."** Uyuşmazsa değer doğrulanmış gösterilmez (sıfır tolerans), parça "OCR değeri belirsiz" diye işaretlenir.
- Ölçüm Set A, B ve D ile; GPU belleği ve süre §4'teki gibi.

## 8. Karar (2026-11-06, ikinci): GPU gerektirmeyen yol; OCRmyPDF birincil aday

(b) aşaması (görsel model) yalnız planda kalıyor.

**Adaylar (CPU):**
1. **OCRmyPDF** (birincil aday): `ocrmypdf -l tur+eng --skip-text` *(§9 ile değişti: tek dil, kayıttaki dile ya da dil aralığına göre, sayfa başına)* (metin katmanı olan sayfaları atlar). Bozuk katmanlı belgelerde `--redo-ocr` (eski OCR katmanını atıp yeniden okur, dijital metne dokunmaz). Çıktı aranabilir PDF: bugünkü ayrıştırma hattı (Docling, OCR kapalı) olduğu gibi okur; kutular ve sayfa vurgusu aynı yoldan gelir. Tesseract + Ghostscript kullanır.
2. **Docling + Tesseract arka ucu:** OCR ayrıştırma sırasında, sayfa bazında.

**Ön koşul:** bu makinede Tesseract, Ghostscript ve OCRmyPDF kurulu değil (Docling ve RapidOCR var). Kurulum kullanıcı onayıyla (kurulum listesi §8).

**Karşılaştırma testleri:**

| # | Test | Nasıl | Ölçü |
|---|---|---|---|
| i | Bilinen OCR hataları | Pantolon şartnamesinin (taranmış, 48/48 sayfa OCR katmanlı) hatalı sayfaları: "112 inch" = ½, "IS min" = 15, "7-114" = 7-1/4, "3116" = 3/16 (parçalarda 30 yerde) | Yeniden OCR'da değer doğru mu (değer düzeyinde, `verify.numbers_in` ile) |
| ii | Metin katmanı silinmiş sentetik sayfalar | Ceket (dijital) ve pantolondan 8–10 tablo/ölçü sayfası 300 dpi görüntüye çevrilir; bozulma: eğiklik ±2°, bulanıklık, JPEG, gri ton | Doğru cevap orijinal katman: sayısal değer doğruluğu, karakter hata oranı |
| iii | Tablo satırları ve Türkçe karakter | (ii)'nin tablo sayfalarında Docling tablo satırı sayısı (orijinal ile OCR'lı); Türkçe metin içeren sentetik sayfa (ç ğ ı ö ş ü İ) | Satır kurtarma oranı; Türkçe karakter doğruluğu |
| iv | Sayfa başına süre (CPU) | (i)–(iii) sayfalarında | sn/sayfa; 1.000 sayfa tahmini |
| v | Sayfa vurgusu kutuları | (ii)'de OCR'lı sayfanın Docling kutuları ile orijinal kutuların örtüşmesi (IoU) | Vurgunun yerinde kalması |

**Ölçüt:**
- değer düzeyinde doğruluk ((i), (ii));
- **16 OCR etiketli soruda cevapsız kalma oranı** (pantolon 11, Granovsky 5, ceket 2). Yeniden OCR'lı belgeler geçici koleksiyona indekslenir. Kayıttaki ikili yol aramasıyla (kayıtlı BM25 metni) karşılaştırılır: beklenen sayfa ilk 8'de mi, beklenen değer parçada birebir mi.
- Model çağrısı yalnız gerekirse: 16 soru × 2 aday ≈ 32 çağrı, **~0,01 USD** (sorulacak).

**Sonuç:** kazanan gerekçesiyle önerilir; entegrasyondan önce kullanıcıya sorulur.

## 9. Karşılaştırma sonucu ve öneri (2026-11-06; entegrasyon onaylandı, ekler §10)

Rapor: [ocr_karsilastirma_2026-11-06.md](../Pilot/eval/bench/ocr/ocr_karsilastirma_2026-11-06.md).

**Kazanan: OCRmyPDF** (CPU, Ghostscript'siz).

Gerekçe:
1. **Bilinen sayısal hataların hepsini düzeltti** ("112" = ½, "114" = ¼, "3116" = 3/16, "7-114", "IS" = 15). Docling + Tesseract kesirlerin yarısını düzeltemedi.
2. **16 OCR sorusunda cevaplanabilir 9 → 16.** Pantolonun 7 sorusu bugün bozuk değer yüzünden cevapsız kalıyor.
3. **4–5 kat hızlı:** 1,1 sn/sayfa (yeniden OCR) / ~1,4 sn (görüntü sayfası); Docling + Tesseract 5–7 sn.
4. **Bugünkü ayrıştırma hattı değişmez:** OCRmyPDF aranabilir PDF üretir, Docling (OCR kapalı) okur. Tablo hücreleri sentetik sayfalarda korunuyor.
5. Ghostscript gerekmiyor (`--rasterizer pypdfium`), AGPL konusu yok.

**Önerilen entegrasyon** (kod yazılmadı):
- Yükleme sırasında `text_layer.check_pdf`'in sayfa sınıfına göre OCRmyPDF çağrısı:
  - **yok** → `--skip-text` (yalnız metinsiz sayfalar OCR'lanır);
  - **taranmış** → `--redo-ocr` (eski OCR katmanı yenilenir; dijital metne dokunulmaz);
  - **zayıf** (harf aralıklı vb.) → `--force-ocr`;
  - **dijital** → OCR yok.
- **Dil:** belgenin kayıttaki diline göre tek dil (`tur` ya da `eng`; `lang_ranges` varsa sayfa aralığına göre). `tur+eng` birlikte Türkçe harfleri bozuyor (70 harfte 40).
- **OCR sonrası kalite kontrolü:** OCR'lanan sayfanın metni `text_layer.quality` ile ölçülür. Düşükse (Strickland'ın çizim ve levha sayfaları gibi anlamsız dizi) o sayfanın OCR metni indekse alınmaz, sayfa şekil sayfası kalır.
- OCR'lı PDF kaynağın yanında saklanır (sayfa görüntüsü ve vurgu aynı sayfadan). Parçalar `ocr: true` işareti taşır; kapsam raporunda OCR'lanan sayfa sayısı.

**Bilinen sınırlar:**
- Kutu örtüşmesi orta (IoU 0,5–0,7): vurgu doğru bölgede ama dijital kadar sıkı değil.
- Küçük dipnot ve şekil üzerindeki sayıların bir kısmı kaçıyor (sayı duyarlılığı %88–98).
- Sayfa başına süre karmaşık tablo sayfasında 14 sn'ye çıkabiliyor (JUKI).

**Tahmini iş:** ~1,5–2 gün (yükleme akışına bağlama, sayfa sınıfına göre bayrak, dil seçimi, OCR sonrası kalite süzgeci, testler, pantolonun yeniden indekslenmesi ve 16 soruyla doğrulama).

## 10. Entegrasyon onayı, ekler ve regresyon kontrolü (2026-11-06)

**Karar:** OCRmyPDF entegrasyonu §9 tasarımıyla onaylandı, şu eklerle:
- **(a) Regresyon kontrolü:** pantolonda eski ve yeni OCR katmanı değer değer karşılaştırılır. Eskide doğru olup yenide bozulan sayı varsa soru soru gösterilir; **entegrasyondan önce kullanıcıya sorulur**.
- **(b) Dil sayfa başına:** kayıttaki dil aralıklarından (`DocMeta.lang_of`; ör. Bosch üç dilli). Belgeye tek dil verilmez.
- **(c) OCR sonrası kalite süzgeci:** ölçütü genel (anlamsız dizi oranı). Belgeye ya da sayfaya özel eşik yok.
- **Ek 1, sayfa sayfa seçim:** `--redo-ocr` / `--force-ocr` sonrası eski ve yeni katmanın skoru karşılaştırılır; yeni katman daha kötüyse eski katman kalır. Böylece tarayıcı yazılımının iyi OCR'ı (ör. FineReader) kaybolmaz. Pantolondaki değer değer regresyon kontrolü bu kuralın testidir.
- **Ek 2:** §7 ve §8'deki `tur+eng` satırları işaretlendi (§9 ile değişti).
- **Ek 3:** entegrasyondan sonra 16 OCR sorusu **modelle** koşulur (~0,01 USD). Ölçüler: doğrulanmış görünen yanlış 0, cevapsız kalma oranı, bugünkü katmanla karşılaştırma.

### Yazılan kod (ayrıştırma ve indekslemeye henüz bağlanmadı; onay bekliyor)

- **`pilot/ocr.py`:**
  - sayfa sınıfı → bayrak: yok → `--skip-text`, taranmış → `--redo-ocr`, zayıf → `--force-ocr`;
  - sayfa başına tek dil;
  - aynı (bayrak, dil) sayfaları tek çağrıda (`--pages`);
  - `--rotate-pages` (ters ya da yan dönmüş taranmış sayfa).
- **Sayfa sayfa seçim (ek 1):** yeni katmanın skoru eskiden 0,02'den fazla düşükse eski katman kalır.
- **Süzgeç (c):** metinsiz sayfanın OCR metni skoru < 0,85 ise alınmaz; sayfa görüntü sayfası kalır.
- **Sonuç:** OCR'lı PDF `test-dokumanlari/ocr/<doc_id>.pdf` (sayfa sırası özgünle aynı, içindekiler korunur) ve sayfa kararları `<doc_id>.json`.
- **`text_layer.junk_score`:** anlamsız dizi skoru, genel ölçüt. Sayılanlar:
  - yalnız çizgi/gölge karakterli dizi ("|", "AWK}");
  - tek harf;
  - aynı harfin üç kez tekrarı ("NNN"; Roma rakamı hariç);
  - 4+ harfli sesli harfsiz dizi;
  - sesli harf oranı dil dışı uzun büyük harf dizisi;
  - iç harfleri büyük/küçük karışık dizi ("JopurpAo": ters dönmüş sayfa).

  Sınıflandırmadaki `quality` değişmedi: sıkı ölçüt dijital sayfadaki harf listesini (JUKI s.31) düşürüyor; yalnız OCR katmanlarını karşılaştırmak ve OCR metnini kabul etmek için kullanılıyor.
- **Diğer:**
  - `DocMeta.path` OCR'lı PDF varsa onu gösterir; `source_path` özgün dosya;
  - `PILOT_OCR=0` ile kapanır;
  - eksik Tesseract dil verisi açık hata verir;
  - testler `tests/test_ocr.py`.

### Regresyon kontrolü (`bench/ocr_regresyon.py`; model yok)

| Belge | Sayfa | Seçim | OCR süresi |
|---|---|---|---|
| Pantolon (48 taranmış) | 48 | yeni 44, eski kaldı 4 (s.4, 20, 44, 48) | 78 sn |
| Strickland (136 taranmış, 28 metinsiz) | 164 | yeni 134 (127 taranmış + 7 metinsiz), eski kaldı 9, **görüntü kaldı 21** (süzgeç: levha ve çizim) | 444 sn |
| Granovsky (269 zayıf, 2 metinsiz) | 271 | yeni 269, görüntü kaldı 2 | 594 sn |

**Pantolon, değer değer** (kelime hizalaması; `ocr_regresyon_gl-pd-07-14a.md`):
- 127 değişim **düzeltme**: "112" → 1/2, "114" → 1/4, "118" → 1/8, "3116" → 3/16, "50150" → 50/50, "IS" → 15, "ISO" → 150, "lOOoC" → 100°C.
- 25 değişim **tablo okuma sırası**: değer yeni sayfada başka yerde var.
- **Eskide doğru, yenide bozulan** (sayfa görüntüsüyle doğrulandı):

| Sayfa | Görüntüde | Eski katman | Yeni katman | Etki |
|---|---|---|---|---|
| 30 | ≥99.999% | ~99.999% | **299.999%** | **yanlış değer** (doğrulayıcı geçirir) |
| 23 | 43-3/8 (beden tablosu) | 43-3/8 | **43.3/8** | **yanlış değer** (43.3) |
| 37, 40, 45 | GL/PD 07-14A | GLIPD 07-14A | 07-**144** | belge kodu bozuk (üst bilgi) |
| 9 | 40 lbs (düğme dayanımı) | 40 | AQ | değer kayıp (cevapsız) |
| 19 | (5-thread) | 5-thread | S-thread | değer kayıp |
| 22 | 48 (tablo hücresi) | 48 | AS | değer kayıp |
| 1 | Class 1 | Class 1 | Classl | değer kayıp |
| 41 | sayfa no 41 | 41 | 4] | sayfa etiketi |

- **Seçim kuralının testi:** eski katmanın kaldığı 4 sayfada değer kaybı yok. Ama bozulan değerlerin hiçbirini kural yakalamadı: sayfa skoru (anlamsız dizi) tek bir sayının yanlış okunmasını görmez.

**Strickland:**
- Süzgeç 28 metinsiz sayfanın 21'ini (levha, çizim: anlamsız dizi) dışarıda bıraktı; 7 sayfa (başlık, şekil yazısı, s.61 tablo) alındı.
- Taranmış sayfalarda iki katmanın da kesirleri bozuk: kitap ½ ¼ ¾ dizgi kesri kullanıyor.
  - eski katman: "Vi" (75 yerde), "3A", "lA";
  - yeni katman: "%" (159), "'4", "!2".
- Hiçbiri doğrulanabilir değer vermiyor. İçindekiler sayfasında (s.9) yeni katman sayfa numaralarını kaybetti.

**Granovsky:**
- `--rotate-pages` ters taranmış tablo sayfalarını (s.147–191) düzeltti: skor 0,69–0,84'ten ortalama 0,98'e çıktı.
- Değer değer karşılaştırma anlamlı değil: eski katman harf aralıklı, her rakam ayrı sayılıyor. Soru düzeyinde 5/5 (§9).

### Öneri: iki okuma uyuşması (genel kural; onay bekliyor)

Taranmış sayfada eski OCR katmanı varsa **iki bağımsız okuma** var (§7b'deki "iki okuma uyuşursa kabul" ilkesi, görsel modelsiz):
- Yeni katmandaki sayı içeren bir dizi, **OCR-karışık karakter eşlemesiyle** aynı sayfanın eski katmanında geçiyorsa kabul edilir. Eşlenen karakterler: / l I i | ! ] → 1, S → 5, O o → 0; ayırıcılar ("-", ".") eşlenmez.
- Geçmiyorsa dizi **"OCR değeri belirsiz"** işaretlenir. Doğrulayıcı o değeri doğrulanmış göstermez; öğe ✖ olur ve sayfa gösterilir.
- Metinsiz sayfada tek okuma var; değer kabul edilir (§9).

**Pantolonda ölçüm:**
- Yeni katmandaki 1.577 sayısal dizinin **61'i** belirsiz oluyor.
- Bulunan bütün yanlışlar bu 61'in içinde: 299.999, 43.3/8, 07-144, 4].
- Doğru olup belirsiz kalanlar da var: 140°, 160°, 100°C, 200ng/uL. Bunlar cevapsız kalır, yanlış gösterilmez.
- 11 pantolon sorusunun beklenen değerlerinin **hiçbiri** belirsize düşmüyor.
- Kayıp değerler (40, 5, 48) yalnız cevapsızlık: yanlış değer üretmiyor.

**İş:** belirsiz dizilerin sayfa kararlarına yazılması, parçaya taşınması, doğrulayıcıda kontrol ve testler (~0,5 gün).

**Sıra (onaydan sonra):**
1. Ayrıştırmaya bağlama (`run_parse.py` → `ocr_document`) ve parçalarda `ocr` işareti;
2. iki okuma kuralı;
3. pantolonun yeniden indekslenmesi ve 16 soruyla doğrulama (arama düzeyi);
4. 16 soru modelle (~0,01 USD).
