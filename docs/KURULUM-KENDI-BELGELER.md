# Kendi belgelerinle kurulum: kontrol listesi

> Pilot birimimizde, dikiş ölçüleri ve şartname türü belgelerle (karar 2026-11-06). Sistem konudan bağımsız: test belgeleri kaldırılır, kendi belgelerimiz indekslenir. Model, şema, arama ve doğrulama değişmez (PRD, [MIMARI A4.13](MIMARI.md#a413-cevap-hattı-c-kipi-varsayılan-adım-2-kararı-2026-11-06)).
>
> Komutlar Pilot klasöründe, `.venv` etkin, PowerShell. Bulut çağıran adımlarda `OPENROUTER_API_KEY` ortamda olmalı.

## 0. Önce

- [ ] **Yedek:** `data/` klasörünün bugünkü hali (parsed, figures, chunks.jsonl, qdrant, bench_cache) ayrı bir yere kopyalandı. Git dışı; geri dönüş için gerekli.
- [ ] Belgeler tek klasörde toplandı (PDF). Her belge için kayıt bilgisi hazır:
  - **ürün alanı:** ürün adı ve varsa model kodu, ör. "Ceket ACU", "S-7300A düz dikiş makinesi";
  - marka / müşteri;
  - belge türü: `product_standard` | `machine_manual` | `tailoring_guide` | `repair_guide`;
  - dil;
  - erişim grubu.
- [ ] **Taranmış belge kontrolü** (pilot öncesi zorunlu iş: [PLAN-OCR.md](PLAN-OCR.md)): her PDF'te metin seçilebiliyor mu? Sistem OCR'ı kendisi yapmıyor, PDF'in içindeki metin katmanını kullanıyor. Metin katmanı olmayan tarama aranamaz (PRD "Taranmış belgeler"). Böyle belgeler ya tarayıcı yazılımıyla OCR'lanır ya da Adım 6 OCR planı beklenir.

## 1. Test belgelerini ve indeksi temizleme

- [ ] `pilot/registry.py` → `DOCS` tablosundaki test belgeleri kaldırıldı.
- [ ] Elle yazılmış takma ad ve marka listeleri yok (2026-11-06'da silindi). Adlar yalnız kayıt alanlarından gelir.
- [ ] Silindi:
  - `data/parsed/*`, `data/figures/*`, `data/chunks.jsonl`;
  - `data/qdrant/` (gömülü indeks);
  - `data/bench_cache/adim2_arama.json` (eski arama önbelleği).
- [ ] Belge klasörü yolu: `config.MANUALS_DIR` bugün `../test-dokumanlari`. Yeni klasör buraya kopyalanır ya da yol değiştirilir (küçük kod değişikliği: `PILOT_MANUALS_DIR` ortam değişkeni önerisi).

## 2. Yeni belgeleri yükleme (kayıt)

- [ ] Her belge için `DocMeta(...)` satırı: `doc_id` (kısa, tekil), dosya adı, marka, **ürün**, tür, dil (`lang_ranges` gerekirse), `access`.
- [ ] Ürün alanı soruda geçecek adı içeriyor (ürün adı + model kodu). Takma ad listesi yazılmaz.
- [ ] **`title`**: belgenin kendi başlığı, ilk sayfadan (genelde İngilizce, ör. "TROUSERS, ARMY COMBAT UNIFORM"). **`author`**: varsa yazar. Yükleme formu ilk sayfadan önerir, yetkili onaylar (bugün kayıtta elle).

## 3. İşleme ve indeksleme

- [ ] `python run_parse.py`: ayrıştırma. Günlükte sayfa başına süre ve "metin katmanı yedeğine geçen sayfa" sayısı kontrol edilir.
- [ ] Kapsam kontrolü: her belgenin sayfa sayısı, boş ya da çok az metinli sayfa listesi (taranmış/metin katmanı yok), tablo sayısı.
- [ ] (İsteğe bağlı) `python run_figures.py`: şekil açıklaması (yerel VLM, uzun sürer). Dikiş ölçüsü belgelerinde şekil azsa atlanabilir.
- [ ] `python run_index.py`: parçalama + bge-m3 + BM25 indeksi. Günlükteki parça sayısı belge başına mantıklı.

## 4. Ağsız testler

- [ ] `$env:PILOT_ANSWER_MODE = "bugun"; python -m pytest -q tests`: hepsi geçmeli. Testler taklit veriyle çalışır, belgelerden bağımsızdır.

## 5. İlk duman testi (20–30 soru, bulut çağrılı)

- [ ] 20–30 soru elle yazıldı. Her biri için cevabın olduğu sayfa not edildi; en az 3'ünün cevabı belgede yok, en az 2'si ürün belirtmeyen (netleştirme) soru.
- [ ] Uygulama c kipinde (`PILOT_ANSWER_MODE=c`, varsayılan) açıldı: `streamlit run app.py`. Sorular arayüzden soruldu.
- [ ] Her soru için not:
  - rozet (✓ / ⚠ / ✖ / bulunamadı / netleştirme);
  - doğru sayfa ekranda mı;
  - değer doğru mu;
  - süre (alt satırdaki "ilk doğrulanmış cümle").
- [ ] **Kapılar:**
  - doğrulanmış görünen yanlış **0**: değer içeren cevapta tolerans sıfır;
  - "bulunamadı" soruları "bulunamadı" alıyor;
  - sağlayıcı DeepInfra.
- [ ] Sorunlar okuma notuna yazıldı (soru, beklenen sayfa, gelen cevap).

## 6. Gerçek soru seti (kullanım sırasında)

- [ ] Kullanım sırasında not edilen **30–50 soru**, her biri soru metni ve cevabın olduğu sayfa ile (değer varsa değer de) bir dosyada toplanır (`eval/kendi_sorular.json` biçimi: `id`, `q`, `expect_docs`, `expect_pages`, `expect_in_answer`, `expect_not_found`, `expect_clarify`).
- [ ] **Onay geliştirme ekibinde:** kanıt cümlesi beklenen sayfada ve beklenen değer kanıtta. Model çıktısı onay ölçütü olmaz.
- [ ] Taranmış belgeden gelen sorular `ocr` etiketiyle ayrıca izlenir (cevapsız kalma oranı, PRD).

## 7. Sunucu kurulumu (Adım 3; servis API'siyle)

API planı: [plan_cevap_modeli_2026-11-06_api.md](../Pilot/eval/bench/adim2/plan_cevap_modeli_2026-11-06_api.md).

- [ ] **Ters vekilde akış arabelleği kapalı:** yanıtta `X-Accel-Buffering: no` ve `Cache-Control: no-cache`; nginx'te `proxy_buffering off;`, uzun `proxy_read_timeout`, akış yanıtında gzip kapalı. Kontrol: bir soru sorulduğunda gri metin parça parça geliyor, toplu gelmiyor.
- [ ] Kimlik: istemci akışı `fetch` + `ReadableStream` ile `Authorization` başlığıyla okuyor (`EventSource` başlık göndermez).
- [ ] `OPENROUTER_API_KEY` yalnız sunucu ortamında. Anahtarda OpenRouter harcama sınırı tanımlı. Uygulamanın günlük maliyet bekçisi ve kullanıcı başına hız sınırı açık.
- [ ] Denetim kaydı yerelde, şifreli diskte. Okuma yetkisi ve saklama süresi kararı uygulanmış (A8).

## 8. OCR araçları (taranmış belgeler; docs/PLAN-OCR.md)

- [ ] **Tesseract OCR** (5.x) ve **Türkçe dil verisi** (`tur.traineddata`, `eng` ile birlikte).
  - Windows: UB Mannheim kurulumu (`winget install UB-Mannheim.TesseractOCR`), kurulumda Turkish seçilir. Linux: `apt install tesseract-ocr tesseract-ocr-tur`.
  - Kontrol: `tesseract --list-langs` içinde `tur` ve `eng`.
- [ ] **Ghostscript** (PDF işleme; OCRmyPDF gerektirir).
  - Windows: `winget install ArtifexSoftware.GhostScript`. Linux: `apt install ghostscript`.
- [ ] **OCRmyPDF** (Python paketi, uygulama ortamına): `pip install ocrmypdf`. Kontrol: `ocrmypdf --version`.
- [ ] **Lisans notu:**
  - Ghostscript **AGPL-3.0**. Şirket içi kullanımda (ağ üzerinden dışarıya hizmet verilmeden, değiştirilmeden) AGPL'in kaynak kodu paylaşma yükümlülüğü doğmaz. Hizmet dışarıya açılırsa ya da Ghostscript değiştirilirse hukuk görüşü gerekir. Ticari lisans seçeneği Artifex'ten alınabilir.
  - Tesseract Apache-2.0, OCRmyPDF MPL-2.0.
- [ ] Ayrıştırma günlüğünde metin katmanı raporu (`run_parse.py`): "yok" ve "zayıf" sayfalar uyarı olarak çıkar; "taranmış" sayfalar bilgi.
