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
