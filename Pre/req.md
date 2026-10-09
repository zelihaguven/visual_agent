# Visual Agent: Pre Req 

> **Son güncelleme:** 2026-10-09

---

## 0. Amaç ve Kapsam

Kullanıcı bir **visual board** üzerinden soru sorar (örn. *"Nike için dikiş standartları nelerdir?"*). Sistem:

1. Soruyu analiz eder, marka/müşteri bilgisini çıkarır.
2. İlgili marka/manual ile filtreler.
3. RAG ile manual içinden ilgili bölümleri getirir.
4. LLM ile **kaynağa dayalı** yanıt üretir (kaynak: dosya adı + sayfa no).
5. Bulunan manual sayfasını ekranda gösterir (mümkünse ilgili alanı vurgular).
6. Yanıtı TTS ile sesli okur.

**Bu doküman sadece araştırma aşamasını kapsar.** 

### Hedef akış (ilk taslak)

```
[Kullanıcı sorusu (metin / ses?)]
        │
        ▼
[Sorgu analizi: marka, konu, dil]  ──►  metadata filtresi (brand = "Nike")
        │
        ▼
[Retrieval: hybrid search (BM25 + vektör) → reranking]
        │
        ▼
[LLM: kaynağa dayalı yanıt + citation (dosya, sayfa, bbox)]
        │
        ├──►  [Sayfa görüntüleyici: PDF sayfası + highlight]
        │
        └──►  [TTS: okunabilir metne dönüştür → sesli oku]
```

---

## Çalışma Sırası (Önceliklendirme)

| Faz | Konular | Neden bu sırada |
|-----|---------|-----------------|
| **Faz 1** | 1. RAG Temelleri · 2. Manual/PDF İşleme · 3. Kaynak Gösterme | Sistemin çekirdeği. Diğer her şey bunların kararlarına bağlı. |
| **Faz 2** | 5. TTS · 6. Arayüz ve Orkestrasyon | Kullanıcı deneyimi katmanı. Çekirdek netleşince seçilir. |
| **Faz 3** | 4. LLM Seçimi ve Yanıt Kalitesi | Retrieval hattı belli olunca model ve değerlendirme anlamlı olur. |
| **Faz 4** | 7. Veri Güvenliği ve Erişim | Tüm seçimleri (bulut/on-prem) son kez filtreler. |
| **Faz 5** | Sentez: mimari, araç seçimi, risk listesi | Beklenen çıktıları üretir. |
| **Faz 6** | Uygulama planı + pilot önerisi | Bir sonraki task'lara geçiş. |



---

## Adım 0: Hazırlık (araştırmaya başlamadan önce)

- [ ] **0.1** Paydaşlara kritik soruyu sor: *Müşteri manualleri bulut API'ye (OpenAI, Anthropic, Google vb.) gönderilebilir mi, yoksa on-prem zorunlu mu?*
- [ ] **0.2** Örnek manuallerden bir set topla. **Karar (2026-10-08):** Geliştirme ve testler internetten bulunan **açık erişimli (public) manuellerle** yapılacak. Sistem bu set üzerinde iyi sonuç verdiği kanıtlanınca **son adımda kendi (müşteri) verimize** geçilecek. Aday liste: [notes/manual-envanteri.md](notes/manual-envanteri.md).
- [ ] **0.3** Manuallerin dilini belirle (Türkçe / İngilizce / karışık). Kullanıcı soruları hangi dilde olacak?
- [ ] **0.4** 10–20 adet gerçekçi örnek soru yaz (cevabı ve geçtiği sayfayı bilerek). Bu, ileride **test soru seti** olacak.
- [ ] **0.5** Donanım durumunu öğren: GPU var mı? (Lokal model, OCR ve TTS seçimlerini belirler.)
- [ ] **0.6** Geliştirme ortamı: Python kurulumu (şu an yok). PDF araç denemesi (2.3) için gerekli.

**Çıktı:** `Pre/notes/00-hazirlik.md` (cevaplar, örnek doküman listesi, soru seti taslağı)

---

## Faz 1: Çekirdek (RAG + PDF + Kaynak)

### Adım 1: RAG Temelleri

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 1.1 | RAG mimarisini öğren | Ingestion → chunking → embedding → vector DB → retrieval → generation adımları nedir, her biri ne iş yapar? | [x] |
| 1.2 | Chunking stratejileri | Sabit boyut vs. semantic vs. sayfa/başlık bazlı: hangisi **sayfa numarasını kaybetmeden** çalışır? Chunk sayfa sınırını aşarsa ne olur? | [x] |
| 1.3 | Embedding modelleri | Çok dilli (TR + EN) hangi modeller var? (örn. `bge-m3`, `multilingual-e5`, OpenAI `text-embedding-3`, Cohere `embed-multilingual`). Boyut, hız, lisans, Türkçe kalitesi. | [x] |
| 1.4 | Vector DB karşılaştırma | Chroma, Qdrant, FAISS, pgvector, (Weaviate, Milvus). Metadata filtreleme, hybrid search desteği, kurulum kolaylığı, ölçek. | [x] |
| 1.5 | Hybrid search | BM25 + vektör aramayı birleştirmek neden önemli? (Teknik terimler, ürün kodları, standart numaraları için.) | [x] |
| 1.6 | Reranking | Cross-encoder reranker nedir? (örn. `bge-reranker`, Cohere Rerank). Kazanç / gecikme maliyeti. | [x] |
| 1.7 | Metadata filtreleme | "Nike" sorusunda sadece Nike manuallerinde aramak için filtre nasıl uygulanır? Marka sorudan nasıl çıkarılır? | [x] |

**Çıktı:** [notes/rag-temelleri.md](notes/rag-temelleri.md) (özet, seçenekler tablosu, artı/eksi, ilk öneri)

### Adım 2: Manual / PDF İşleme

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 2.1 | Manual envanteri | **Önce public test seti**, gerçek müşteri manuelleri en sonda. Manuellerin listesi: marka, doküman adı, versiyon, sayfa sayısı, dil, tür (dijital / taranmış), içerik ağırlığı (metin / tablo / şekil). | [x] |
| 2.2 | PDF parsing araçları | PyMuPDF, pdfplumber, Unstructured, Docling, Marker, LlamaParse, Azure Document Intelligence vb. Tablolar ve çok kolonlu sayfaları nasıl ayrıştırıyorlar? | [x] |
| 2.3 | Araç denemesi | Seçilen 2–3 aracı aynı 3 zor sayfada (tablo, şekil, çok kolon) dene ve sonuçları karşılaştır. | 🟡 Docling denendi (Faz 1 kontrol noktası, [faz1_output/report.md](../faz1_output/report.md)). Diğer araçlarla karşılaştırma yapılmadı |
| 2.4 | OCR ihtiyacı | Taranmış manual var mı? Varsa: Tesseract, PaddleOCR, EasyOCR, bulut OCR. Türkçe karakter başarısı. | [x] |
| 2.5 | Metadata şeması | Her chunk için tutulacak alanlar: `brand`, `doc_name`, `version`, `page`, `section/heading`, `bbox`, `lang`, `chunk_type` (metin/tablo/şekil). | 🟡 Taslak hazır |
| 2.6 | Bounding box | Hangi araç metin bloklarının koordinatlarını (bbox) veriyor? Highlight için gerekli (bkz. Adım 3). | [x] |

**Çıktı:** [notes/pdf-isleme.md](notes/pdf-isleme.md) + `Pre/notes/manual-envanteri.md` (tablo)

### Adım 3: Kaynak Gösterme ve Sayfa Görüntüleme

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 3.1 | Citation / grounding | Yanıttaki her iddia hangi chunk'tan geldi? LLM'e kaynak ID'si nasıl verdirilir ve doğrulanır? | [ ] |
| 3.2 | Sayfayı görsele çevirme | PDF sayfası → PNG (PyMuPDF `get_pixmap`, pdf2image) vs. tarayıcıda PDF.js ile doğrudan render. Artı/eksi. | [ ] |
| 3.3 | Highlight | Chunk'ın bbox'ı sayfa üzerinde nasıl çizilir? (Görsele dikdörtgen çizme / PDF.js annotation / metin arama ile bulma.) | [ ] |
| 3.4 | Multimodal retrieval | ColPali / ColQwen gibi sayfa-görseli tabanlı retrieval nedir? Tablo/şekil ağırlıklı manuallerde metin tabanlı RAG'e göre avantajı ne? **Bizim için gerekli mi?** | [ ] |

**Çıktı:** [notes/kaynak-gosterme.md](notes/kaynak-gosterme.md)

**Faz 1 sonu kontrol noktası:** Bir manualden bir chunk'ı sayfa no + bbox ile çıkarıp, o sayfayı görsel olarak highlight'lı gösterebiliyor muyuz? (Küçük bir deneme scripti ile doğrulanabilir.)

> ✅ **Sonuç (2026-10-09): Evet.** [faz1-test.py](../faz1-test.py) ile dijital şartname, taranmış şartname (OCR) ve Brother makine kılavuzunda denendi. 27/27 test geçti. Sayfa geçişinde bölünen paragraf birleştirildi, tablo satırı seviyesinde vurgu ve basılı sayfa numarası ("s.90 (PDF s.101)") çalışıyor. Rapor: [faz1_output/report.md](../faz1_output/report.md).
>
> Denemede çıkan açık maddeler **araştırma aşamasında çözülmeyecek**, uygulama aşamasına devredildi (bkz. 6.2, "Faz 1 denemesinden devredilenler").

---

## Faz 2: Kullanıcı Deneyimi (TTS + Arayüz)

### Adım 5: TTS (Text-to-Speech)

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 5.1 | Seçenek listesi | **Bulut:** Azure TTS, Google Cloud TTS, ElevenLabs, OpenAI TTS, Amazon Polly. **Açık kaynak:** Piper, Coqui XTTS, Kokoro, F5-TTS vb. | [x] Chatterbox Multilingual eklendi. Fiyat/lisanslar kesin seçimden önce resmi sayfadan doğrulanacak |
| 5.2 | Türkçe / İngilizce kalite | Aynı 3 cümleyi (biri teknik terim ve sayı içeren) her adayla seslendirip dinleyerek karşılaştır. | [x] Araştırma seviyesinde (kaynaklardan dil desteği, normalizasyon davranışı). Test planı ve 4 test cümlesi hazır. Dinleme denemesi **pilota (6.1) devredildi** (tasks.md deneme istemiyor) |
| 5.3 | Gecikme ve streaming | İlk sesin gelme süresi. Streaming destekliyor mu? LLM cümle cümle üretirken TTS de cümle cümle okuyabilir mi? | [x] Öneri: önce tam cevap + doğrulama, sonra streaming TTS (bkz. R5). Ölçüm pilotta |
| 5.4 | Maliyet ve lisans | Karakter başı ücret, ticari kullanım lisansı (özellikle açık kaynak modellerde). | [x] Maliyet karar verdirici değil. Lisans: bkz. R6 |
| 5.5 | Metin normalizasyonu | Uzun/teknik yanıtı okunur hale getirme: kısaltmalar, sayılar, birimler ("12 mm", "SPI 8-10"), madde işaretleri. Sesli okumak için ayrı kısa özet mi üretilmeli? | [x] Ayrı kısa sesli metin + sayı kontrolü + kural tablosu. Okunuş alışkanlıkları kullanıcılara sorulacak (Q10) |

**Çıktı:** [notes/tts.md](notes/tts.md) (kalite/gecikme/maliyet karşılaştırma tablosu). Ses örnekleri (`Pre/notes/tts-samples/`) pilotta üretilecek.

### Adım 6: Visual Board / Arayüz ve Orkestrasyon

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 6.1 | Arayüz seçenekleri | Streamlit, Gradio, Open WebUI, özel web (React/Next.js + FastAPI). Hız vs. esneklik. | [x] Pilot Streamlit, üretim muhtemelen özel web (pilottan sonra karar). Open WebUI / Chainlit / Gradio elendi |
| 6.2 | Tek ekran düzeni | Soru girişi + yanıt metni + sayfa görüntüleyici (highlight) + ses oynatıcı aynı ekranda nasıl birleşir? Kaba bir wireframe çiz. | [x] ASCII wireframe (geniş + dar ekran) ve tasarım kararları hazır. Cihaz bilgisi bekleniyor (Q11) |
| 6.3 | Orkestrasyon çatıları | LangChain vs. LlamaIndex vs. Haystack vs. çatısız (düz Python). Öğrenme eğrisi, esneklik, citation desteği. | [x] Çatısız, modüler Python + denetim izi |
| 6.4 | STT (sesli soru) | Sesli soru gerekli mi? (Fabrika/atölye ortamı, eller meşgul vb.) Gerekirse: Whisper, faster-whisper, bulut STT. | [x] Mimariyi değiştirmiyor, sonradan eklenebilir. Gerekirse bas-konuş + tanınan metni onaylama + terim listesi. Gereklilik Q4'e bağlı |

**Çıktı:** [notes/arayuz-orkestrasyon.md](notes/arayuz-orkestrasyon.md) (wireframe dosyanın içinde ASCII olarak. Pilot arayüzü yapılınca ekran görüntüsüyle güncellenecek)

---

## Faz 3: LLM Seçimi ve Yanıt Kalitesi

### Adım 4: LLM ve Değerlendirme

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 4.1 | Model seçenekleri | **Bulut:** Claude, GPT, Gemini. **Lokal/açık:** Qwen, Llama, Gemma, Mistral. Türkçe performansı, bağlam uzunluğu, maliyet, donanım ihtiyacı. | [x] Sağlayıcı önceden seçilmiyor, pilotta 3 bulut + 1 lokal aday aynı test setiyle ölçülecek. Lokal hedef ~27–32B (24 GB GPU). Maliyet karar verdirici değil |
| 4.2 | Prompt tasarımı | Sadece verilen kaynaklara dayanarak cevap ver, kaynak göster, bilgi yoksa *"Bu bilgi manuallerde bulunamadı"* de. Taslak sistem promptu yaz. | [x] Taslak sistem talimatı + JSON çıktı şeması hazır ([prompt-taslak.md](notes/prompt-taslak.md)). Pilotta iyileştirilecek |
| 4.3 | Hallucination azaltma **🔴 (kritik, bkz. R4)** | Kaynak zorunluluğu, alıntı (quote) isteme, yanıt sonrası doğrulama (alıntı + sayı kontrolü), düşük skorlu retrieval'da cevap vermeme eşiği. Taslak plan: [rag-temelleri.md, S11](notes/rag-temelleri.md). | [x] 6 katman ayrıntılandırıldı: kalibre eşik, birebir alıntı, iki yönlü sayı-tolerans kontrolü, başarısızlık davranışları |
| 4.4 | Değerlendirme yöntemi | Test soru seti (Adım 0.4), retrieval metrikleri (Recall@k, MRR), yanıt metrikleri (faithfulness, answer relevance). Araçlar: RAGAS, DeepEval, TruLens. | [x] Test seti yapısı (8 soru türü), metrikler ve taslak hedefler, araçlar (kendi script + RAGAS). Test setini kimin hazırlayacağı açık (0.4) |

**Çıktı:** [notes/llm-degerlendirme.md](notes/llm-degerlendirme.md) + [notes/prompt-taslak.md](notes/prompt-taslak.md)

---

## Faz 4: Veri Güvenliği ve Erişim

### Adım 7: Güvenlik

| # | Alt görev | Cevaplanacak soru | Durum |
|---|-----------|-------------------|-------|
| 7.1 | Gizlilik gereksinimleri | Müşteri (marka) manuallerinde NDA / gizlilik maddesi var mı? Üçüncü taraf servise gönderilebilir mi? | 🟡 Araştırma tamam: NDA (ticari sır) ve KVKK (kişisel veri) ayrımı, hukuka bakılacak 8 madde, KVKK 2024 yurt dışı aktarım değişikliği. **Cevap paydaşlardan bekleniyor** |
| 7.2 | Bulut vs. on-prem | Her bileşen (embedding, LLM, TTS, OCR) için: bulut kullanılırsa risk ne, on-prem olursa maliyet/donanım ne? Veri saklama (zero data retention) politikaları. | 🟡 Bileşen tablosu, 3 senaryo (A bulut / **B hibrit** / C lokal), sağlayıcı politikaları. Ön öneri: adaptörlü mimari, gerçek veride B. Karar Q1'e bağlı |
| 7.3 | Marka bazlı yetkilendirme | Kullanıcı A sadece Nike'ı mı görebilmeli? Retrieval filtresine kullanıcı yetkisi nasıl eklenir? | 🟡 SSO + rol → marka, sunucuda zorunlu pre-filter, yan kapılar (PDF, önbellek, loglar), yetki testleri. İş kuralı paydaşlardan bekleniyor |

**Çıktı:** [notes/guvenlik.md](notes/guvenlik.md)

---

## Faz 5: Sentez (Beklenen Çıktılar)

**Çıktı:** [sentez.md](sentez.md) (sunulabilir özet doküman) + şekiller: [sentez-sekiller/](sentez-sekiller/) (SVG + PNG)

- [x] **5.1** Her konu için araştırma notu (özet, seçenekler, artı/eksi). Faz 1–4 notlarının tamamlanmış hali. → sentez.md Ek A
- [x] **5.2** Önerilen mimari taslağı (akış diyagramı). → sentez.md Bölüm 3, Şekil 1
- [x] **5.3** Araç/model seçim önerileri. → sentez.md Bölüm 4 (durum sütunuyla: netleşti / pilotta ölçülecek / paydaş kararına bağlı)
- [ ] **5.4** Manual envanteri ve format değerlendirmesi (Adım 2.1'in final hali). 🟡 Test seti envanteri hazır ([manual-envanteri.md](notes/manual-envanteri.md)). Gerçek dokümanlar için Q2, Q3, Q7 cevapları bekleniyor
- [x] **5.5** Açık sorular ve riskler listesi. → sentez.md Bölüm 8–9, [sorulacaklar.md](notes/sorulacaklar.md)

---

## Faz 6: Uygulama Planı ve Pilot

- [ ] **6.1** Pilot tanımı: **tek marka, 3–5 manual**, uçtan uca prototip (soru → retrieval → yanıt + kaynak → sayfa highlight → TTS).
  - Pilotta yapılacak doğrulamalar (Adım 1'den ertelendi, bkz. [rag-temelleri.md → Doğrulanacaklar](notes/rag-temelleri.md)): `bge-m3` TR↔EN eşleşmesi, hybrid vs. sadece dense (A–D deneyi), BM25 vs. BGE-M3 sparse, Türkçe kök bulucu seçimi, reranker gecikmesi, query translation gerekliliği (Q6).
  - Adım 5'ten ertelenen: TTS adaylarının 4 test cümlesiyle karşılaştırılması (ham + normalize, kritik değer doğruluğu, round-trip STT, atölye gürültüsünde dinleme), Chatterbox Multilingual Türkçe kalitesi (R6), ilk ses gecikmesi ölçümü (bkz. [tts.md 2.2](notes/tts.md)).
- [ ] **6.2** Uygulama aşaması task listesi. İlk öneri:
  1. Ingestion pipeline (parse + chunk + metadata + indeksleme)
  2. Retrieval (hybrid + filtre + rerank) ve test seti ile ölçüm
  3. Yanıt üretimi + citation
  4. Sayfa görüntüleyici + highlight
  5. TTS entegrasyonu
  6. Arayüz birleştirme
  7. Değerlendirme ve iyileştirme turu
  8. Güvenlik / yetkilendirme

  **Faz 1 denemesinden devredilenler** (ayrıntı: [faz1_output/report.md → Yaşanan problemler](../faz1_output/report.md)):
  | Madde | İlgili task | Not |
  |-------|-------------|-----|
  | OCR satır kaybı (sessiz hata) | 1. Ingestion | İki OCR farklı yerlerde hata yapıyor (Docling OCR satırı kaybetti, PDF'in kendi OCR katmanı doğru okudu ama "confOlm" gibi küçük hatalar yaptı). Birleştirme / farklı OCR motoru denenecek. Kesirli ölçülerde de OCR hatası var ("½" → "V2", Strickland) |
  | Tablo satırı metninde başlık tekrarı ve çizim kodları ("Problem: 1 \| Problem: …0573M") | 1. Ingestion (chunking) | Vurgu doğru, metin temizliği gerekiyor |
  | Basılı → fiziksel sayfa eşleme tablosu | 1. Ingestion | Kılavuz içi atıflar ("Page 67") basılı numarayla. Kitapçık düzeni (Mr. Coffee: bir PDF sayfasında iki basılı sayfa) ve üstte basılı numara (Strickland) ayrıca ele alınmalı |
  | Tarayıcıda vurgunun (streamlit-pdf-viewer) gözle doğrulanması | 4. Sayfa görüntüleyici | Otomatik testte görüntüleyici hatasız açılıyor, vurgu henüz gözle kontrol edilmedi |
  | Docling dışındaki parser'larla karşılaştırma (Adım 2.3) | 1. Ingestion | Marker, PyMuPDF4LLM vb. aynı sayfalarda |
- [ ] **6.3** Pilot başarı kriterleri (örn. test setinde doğru sayfa ilk 3'te %80+, yanıt gecikmesi < X sn).

---

## Açık Sorular ve Riskler (yaşayan liste)

> Kime ne sorulacağı (cevap satırlarıyla): **[notes/sorulacaklar.md](notes/sorulacaklar.md)**

| # | Soru / Risk | Etki | Durum |
|---|-------------|------|-------|
| Q1 | Manualler bulut API'ye gönderilebilir mi? | Tüm model seçimlerini belirler. Veri kurum dışına çıkabilecek tüm noktaların listesi: [pdf-isleme.md → "VLM ile şekil açıklaması veri güvenliğini etkiler mi?"](notes/pdf-isleme.md) | Açık |
| Q2 | Manuallerin dili ve kullanıcı sorularının dili ne? | Embedding, LLM, TTS seçimi | Kısmen cevaplandı: TR + EN destek bekleniyor. Şu an EN manualler TR'ye çevriliyor, hedef çevirmeden kullanmak (çok dilli embedding ile). |
| Q6 | Diller arası aramada BM25 için soru doküman diline çevrilmeli mi (*query translation*)? | Hybrid search kalitesi | Açık (bkz. [rag-temelleri.md](notes/rag-temelleri.md) 1.3) |
| Q7 | Doküman metadata'sı (marka, versiyon, ürün kategorisi, yürürlük tarihi) nasıl elde edilecek? | Filtreleme doğruluğu, ingestion akışı | Yön belirlendi: **elle değil, otomatik çıkarım** (klasör/dosya adı kuralı + kapak regex'i + LLM ile çıkarım), sadece emin olunamayanlar için insan onayı. Açık kalan: gerçek manuellerin klasör/adlandırma düzeni ne? (bkz. [pdf-isleme.md 2.5](notes/pdf-isleme.md)) |
| Q8 | Sistem hangi doküman türlerini kapsayacak (ürün standartları, makine kılavuzları, başka?) ve soru türü arayüzde seçilecek mi yoksa otomatik mi anlaşılacak? | Metadata şeması (`doc_type`), sorgu yönlendirme, arayüz tasarımı | Açık (bkz. [rag-temelleri.md 1.7 → "Birden fazla doküman türü"](notes/rag-temelleri.md)) |
| Q9 | Kullanıcı ekranda sadece ilgili sayfayı mı görmeli, yoksa dokümanın tamamında gezinebilmeli mi (ve indirebilmeli mi)? | Sayfa görüntüleme yöntemi (resim vs. tarayıcıda PDF.js), gizlilik, yetkilendirme | Açık. Eğilim: gezinme + yakınlaştırma gerekli → PDF.js (bkz. [kaynak-gosterme.md 3. bölüm](notes/kaynak-gosterme.md)) |
| Q3 | Gerçek dokümanlarda taranmış PDF oranı ne? Hangi **görsel türleri** var (dikiş tipi çizimleri, ölçülü teknik çizimler, fotoğraflar, makine parça çizimleri) ve ne sıklıkta? | OCR ihtiyacı, görsel anlama yöntemi (VLM açıklaması / ColPali) | Kısmen: Gerçek spec ve manuellerde dikiş, ölçü ve makine görselleri olduğu biliniyor → görsel anlama **gerekli** (bkz. [kaynak-gosterme.md 5. bölüm](notes/kaynak-gosterme.md)). Türler ve oranlar açık |
| Q4 | Sesli soru (STT) gerekli mi? | Arayüz kapsamı | Açık. Mimariyi değiştirmiyor, pilotta isteğe bağlı mikrofon butonuyla kullanıcı tepkisi ölçülebilir ([arayuz-orkestrasyon.md 6.4](notes/arayuz-orkestrasyon.md)) |
| Q11 | Sistem hangi cihazda kullanılacak (PC, tablet, duvar ekranı / kiosk)? Ekran nerede duracak, kaç kişi kullanacak, kullanıcı girişi nasıl olacak? | Ekran düzeni, arayüz teknolojisi, yetkilendirme | Açık (bkz. [arayuz-orkestrasyon.md 6.2](notes/arayuz-orkestrasyon.md)) |
| Q5 | Donanım (GPU) var mı? | Lokal model uygulanabilirliği | Açık |
| R1 | Tablo/şekil ağırlıklı sayfalarda metin tabanlı RAG zayıf kalabilir | Yanıt kalitesi | İzlenecek |
| Q10 | Atölyede kodlar ve terimler nasıl söyleniyor? (Dikiş tipi 301: "üç yüz bir" mi "üç sıfır bir" mi, model kodu S-7300A, "SPI" mi "inç başına dikiş" mi?) Hoparlör mü kulaklık mı? | TTS normalizasyon kuralları, sesli metin dili, donanım | Açık (bkz. [tts.md 2.5](notes/tts.md)) |
| R2 | Türkçe TTS'de teknik terim/birim okunuşu bozuk olabilir | Kullanıcı deneyimi, **yanlış değer duyulması (R4 ile bağlantılı)** | İzlenecek. Önlem: ayrı kısa sesli metin + sayı kontrolü + kendi normalizasyon kural tablomuz, uzun kodlar okunmaz → ekrana yönlendirilir ([tts.md 2.5](notes/tts.md)) |
| R5 | LLM → TTS cümle cümle seslendirme, "cevap kullanıcıya gitmeden doğrulama" (S11 Katman 5) ile çatışıyor: doğrulanmamış değer duyulabilir | Yanlış değer, R4 | Öneri: önce tam cevap + doğrulama, sonra streaming TTS ([tts.md 2.3](notes/tts.md)) |
| R6 | Türkçe + ticari lisanslı + kaliteli açık (lokal) TTS modeli çok az (şu an sadece Chatterbox Multilingual görünüyor). Q1 "bulut yok" çıkarsa seçenek daralır | TTS seçimi, lokal kurulum | İzlenecek. Chatterbox'ın Türkçe kalitesi 5.2'de denenecek, Azure container yolu araştırılacak |
| R3 | Aynı konunun farklı manual versiyonlarında çelişen bilgi | Yanlış yanıt | İzlenecek |
| **R4** | **🔴 KRİTİK: Uydurulmuş (halüsinasyon) bilgi yanlış dikime yol açar** | Ürün hatası, müşteri kaybı | **En yüksek öncelik.** Katmanlı önlem planı: [rag-temelleri.md, S11](notes/rag-temelleri.md), ayrıntısı [llm-degerlendirme.md 4.3](notes/llm-degerlendirme.md) (6 katman, iki yönlü sayı-tolerans kontrolü). |
| R7 | OCR'ın bir satırı sessizce kaybetmesi (Faz 1 denemesinde görüldü) | Bilgi aranamaz hale gelir | Uygulama aşamasına devredildi (6.2). Önlem: bozuk OCR uyarısı, iki OCR'ın birleştirilmesi, orijinal sayfanın her zaman gösterilmesi |
| R8 | Yetki filtresinin bir erişim noktasında (PDF, önbellek, loglar) unutulması | Gizli bilginin yetkisiz kişiye gösterilmesi | Merkezi zorunlu filtre, tüm erişim noktaları, yetki testleri ([guvenlik.md 7.3](notes/guvenlik.md)) |
| R9 | Sesli soruda model kodunun yanlış tanınması (S-7300A → S-7300B) | Yanlış makinenin kılavuzundan cevap | Tanınan metnin kullanıcı onayı, terim listesi ([arayuz-orkestrasyon.md 6.4](notes/arayuz-orkestrasyon.md)) |
| R10 | Test setinin gerçek dokümanları temsil etmemesi | Pilot sonuçları gerçek veriye taşınmaz | Gerçek veriye geçişte test seti yeniden kurulur, yeniden ölçülür |

---

## Öğrenme Notları / Günlük

> Araştırma ilerledikçe buraya kısa notlar, faydalı linkler ve alınan kararlar eklenecek.

| Tarih | Konu | Not / Karar | Link |
|-------|------|-------------|------|
| 2026-10-08 | Planlama | Araştırma planı oluşturuldu | |
| 2026-10-08 | Adım 1: RAG | İlk tur tamamlandı. Ön öneri: başlık bazlı chunking + `bge-m3` + Qdrant + hybrid search + `bge-reranker-v2-m3`. Test setiyle doğrulanacak. | [rag-temelleri.md](notes/rag-temelleri.md) |
| 2026-10-09 | Faz 1 kontrol noktası | ✅ Docling ile parse + bbox + sayfa vurgusu üç doküman türünde çalışıyor (27/27 test). Açık maddeler uygulama aşamasına devredildi (6.2). | [faz1_output/report.md](../faz1_output/report.md) |
| 2026-10-09 | Test seti | Strickland terzilik kitabı (iki kolon, taranmış), Mr. Coffee ve Bosch makine kılavuzları (alan dışı, çok dilli) eklendi. Toplam 8 doküman. | [manual-envanteri.md](notes/manual-envanteri.md) |
| 2026-10-09 | Adım 5: TTS | İlk tur: kavramlar + seçenekler + kontrol soruları. Ön öneri: test için Azure, lokal gerekirse Chatterbox Multilingual. Ayrı kısa sesli metin + kural tabanlı normalizasyon, önce doğrula sonra oku. Yeni: Q10, R5, R6. | [tts.md](notes/tts.md) |
| 2026-10-09 | Adım 5: kapsam | Kontrol soruları değerlendirildi. 5.2 sistematik ses denemesi pilota (6.1) devredildi: araştırma task'ı (tasks.md) deneme değil not istiyor. İsteğe bağlı web demosu dinlemesi notta. | [tts.md 2.2](notes/tts.md) |
| 2026-10-09 | Adım 5 kapandı | Üç ana madde (seçenek + kalite, gecikme/maliyet/lisans, normalizasyon) araştırma seviyesinde tamam. Dinleme denemesi pilotta. | [tts.md](notes/tts.md) |
| 2026-10-09 | Adım 6: Arayüz | İlk tur. Ön öneri: pilot Streamlit (+ streamlit-pdf-viewer), RAG hattı arayüzden bağımsız `soru_cevapla()`, çatısız modüler Python + denetim izi, cevap doğrulandıktan sonra gösterilir, STT isteğe bağlı (bas-konuş + onay). Yeni: Q11. | [arayuz-orkestrasyon.md](notes/arayuz-orkestrasyon.md) |
| 2026-10-09 | Adım 6: kontrol soruları | K1–K5 değerlendirildi (1 ✅, 4 🟡). Streamlit rerun modeli ara sorusu eklendi. | [arayuz-orkestrasyon.md](notes/arayuz-orkestrasyon.md) |
| 2026-10-09 | Adım 6 kapandı | Araştırma seviyesinde tamam. Açık kalanlar (Q4, Q11) sorulacaklar listesinde. | [arayuz-orkestrasyon.md](notes/arayuz-orkestrasyon.md) |
| 2026-10-09 | Sorulacaklar | Tüm adımlardaki açık sorular kişi grubuna göre (yönetim/hukuk, BT, doküman sahipleri, kullanıcılar, kalite) tek dosyada toplandı, cevap satırlarıyla. Bizim tarafımızdaki işler ayrı bölümde. | [sorulacaklar.md](notes/sorulacaklar.md) |
| 2026-10-09 | Adım 4: LLM | İlk tur. Sağlayıcı önceden seçilmiyor, pilotta aynı test setiyle ölçülecek. 7–8B açık modeller Türkçe doküman QA'da yetersiz (bir 2026 çalışması: %49–75). Prompt taslağı + JSON şema, 6 katmanlı halüsinasyon planı, 8 türlü test seti ve metrikler. Yeni sorular: sorulacaklar.md A5. | [llm-degerlendirme.md](notes/llm-degerlendirme.md) |
| 2026-10-09 | Adım 4: kontrol soruları | K1–K5 değerlendirildi (3 🟡, 2 boş → doğru cevaplar yazıldı: K2 lokal model kararı, K3 iki yönlü sayı-tolerans kontrolü). | [llm-degerlendirme.md](notes/llm-degerlendirme.md) |
| 2026-10-09 | Adım 4 kapandı | Araştırma seviyesinde tamam. Model ölçümü pilotta. | [llm-degerlendirme.md](notes/llm-degerlendirme.md) |
| 2026-10-09 | Adım 7: Güvenlik | İlk tur. Ana bulgu: Ingestion'da bulut = dokümanın tamamı dışarı, sorguda bulut LLM = 3–5 parça → **hibrit senaryo** (ingestion/embedding/vektör DB lokal, LLM+TTS kurumsal bulut + ZDR). Yetki kararı LLM'de değil kodda, retrieval öncesi. Kararlar Q1/NDA/7.3 cevaplarına bağlı. Yeni sorular sorulacaklar.md A1'e eklendi. | [guvenlik.md](notes/guvenlik.md) |
| 2026-10-09 | Adım 7: kontrol soruları | K1–K5 değerlendirildi (4 🟡, 1 boş → K4 yan kapılar tablosu yazıldı). | [guvenlik.md](notes/guvenlik.md) |
| 2026-10-09 | Faz 5: Sentez | Sunulabilir sentez dokümanı: özet, mimari (Şekil 1), araç seçimleri, doğruluk güvencesi (Şekil 2), dağıtım senaryoları (Şekil 3), riskler (R1–R10), bekleyen kararlar, pilot önerisi. Yeni riskler sentezde: R7 OCR satır kaybı, R8 yetki filtresi sızıntısı, R9 STT kod tanıma, R10 test setinin temsiliyeti. | [sentez.md](sentez.md) |
