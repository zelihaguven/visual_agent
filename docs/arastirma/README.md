# Araştırma notları (Adım 1–7): dizin

> Manuel tabanlı, kaynak gösteren ve sesli cevap veren soru-cevap sistemi için araştırma notlarının temizlenmiş, numaralı hali (2026-10-08 / 09).
> Kontrol soruları ve cevap/değerlendirme alışverişi çıkarıldı; içlerindeki teknik bilgiler ilgili bölümlere işlendi. Kontrol sorularını da içeren ayrıntılı sürümler: [../calisma-notlari/notlar/](../calisma-notlari/notlar/).
> Bu notların özeti ve pilotla güncellenmiş hali: [../ARASTIRMA-SENTEZI.md](../ARASTIRMA-SENTEZI.md).

## Adım raporları (1–7)

| Adım | Konu | Rapor (bu set) | Ayrıntılı sürüm (kontrol soruları dahil) |
|------|------|----------------|-------------------------------------------|
| 1 | RAG temelleri | [07-rag-temelleri.md](07-rag-temelleri.md) | [../calisma-notlari/notlar/rag-temelleri.md](../calisma-notlari/notlar/rag-temelleri.md) |
| 2 | Manual / PDF işleme | [02-pdf-isleme.md](02-pdf-isleme.md), [01-manual-envanteri.md](01-manual-envanteri.md) | [pdf-isleme.md](../calisma-notlari/notlar/pdf-isleme.md), [manual-envanteri.md](../calisma-notlari/notlar/manual-envanteri.md) |
| 3 | Kaynak gösterme ve sayfa görüntüleme | [03-kaynak-gosterme.md](03-kaynak-gosterme.md) | [kaynak-gosterme.md](../calisma-notlari/notlar/kaynak-gosterme.md) |
| 4 | LLM seçimi ve yanıt kalitesi | [04-llm-secimi-ve-degerlendirme.md](04-llm-secimi-ve-degerlendirme.md), [09-prompt-taslagi.md](09-prompt-taslagi.md) | [llm-degerlendirme.md](../calisma-notlari/notlar/llm-degerlendirme.md), [prompt-taslak.md](../calisma-notlari/notlar/prompt-taslak.md) |
| 5 | TTS | [08-tts.md](08-tts.md) | [tts.md](../calisma-notlari/notlar/tts.md) |
| 6 | Arayüz ve orkestrasyon | [05-arayuz-ve-orkestrasyon.md](05-arayuz-ve-orkestrasyon.md) | [arayuz-orkestrasyon.md](../calisma-notlari/notlar/arayuz-orkestrasyon.md) |
| 7 | Veri güvenliği ve erişim | [06-veri-guvenligi-ve-erisim.md](06-veri-guvenligi-ve-erisim.md) | [guvenlik.md](../calisma-notlari/notlar/guvenlik.md) |

**Diğer teslimatlar:** Sentez → [ARASTIRMA-SENTEZI.md](../ARASTIRMA-SENTEZI.md) · Açık sorular ve riskler → [13-acik-sorular-ve-riskler.md](13-acik-sorular-ve-riskler.md) · **Uygulama aşaması planı → [UYGULAMA-PLANI.md](../UYGULAMA-PLANI.md)** (2026-10-13, akış şemalı) · Pilot raporu → [../PILOT-RAPORU.md](../PILOT-RAPORU.md)

## Notlar

| # | Dosya | Bir satırlık açıklama | Beslediği teslimatlar |
|---|-------|-----------------------|-----------------------|
| 01 | [01-manual-envanteri.md](01-manual-envanteri.md) | Public test seti stratejisi, seçim kriterleri, 7 dokümanın envanteri ve neyi test ettiği, eksikler | **Manual envanteri ve format değerlendirmesi** · Açık sorular & riskler · Faz planı (public → gerçek veri geçişi) |
| 02 | [02-pdf-isleme.md](02-pdf-isleme.md) | PDF türleri ve zorlukları, parsing yaklaşımları, parser/OCR araç karşılaştırması, şekiller, metadata çıkarımı, önerilen ingestion hattı, 2.3 araç denemesi | Araştırma notu · **Mimari (ingestion akışı)** · Araç seçimi (parser, OCR, VLM) · Format değerlendirmesi · Riskler · Görev planı |
| 03 | [03-kaynak-gosterme.md](03-kaynak-gosterme.md) | Citation ([n] → metadata), sayfa görüntüleme (PDF.js vs render), bbox vurgulama, ColPali ve A+B görsel anlama önerisi, Faz 1 kontrol noktası | Araştırma notu · Mimari (kaynak/vurgu akışı, görsel akış) · Araç seçimi (PDF görüntüleyici, VLM) · Riskler · Görev planı |
| 04 | [04-llm-secimi-ve-degerlendirme.md](04-llm-secimi-ve-degerlendirme.md) | LLM rolü ve kriterleri, bulut fiyatları ve açık modeller, donanım, maliyet, prompt ilkeleri, 6 katmanlı halüsinasyon önlemi, test seti ve metrikler | Araştırma notu · **Araç seçimi (LLM, değerlendirme araçları)** · Mimari (doğrulama katmanları) · Riskler · Görev planı (pilot karşılaştırma, test seti) |
| 05 | [05-arayuz-ve-orkestrasyon.md](05-arayuz-ve-orkestrasyon.md) | UI seçenekleri (Streamlit → özel web), wireframe, çatısız modüler orkestrasyon, `soru_cevapla()` mimarisi, STT seçenekleri | **Mimari taslağı (uçtan uca akış, modül yapısı)** · **Araç seçimi (UI, STT)** · Araştırma notu · Riskler · Görev planı (pilot arayüzü) |
| 06 | [06-veri-guvenligi-ve-erisim.md](06-veri-guvenligi-ve-erisim.md) | NDA vs KVKK, bulut/lokal bileşen analizi, A/B/C senaryoları (hibrit önerisi), sağlayıcı veri politikaları, marka bazlı yetki ve yan kapılar | **Açık sorular & riskler** (ana kaynak) · Mimari (veri akışı, dağıtım) · Araç seçimi (sağlayıcı, lokal bileşenler) · Araştırma notu |

## Task → not eşlemesi

| Teslimat | Notlar |
|----------|--------|
| Konu başına kısa araştırma notu (özet, seçenekler, artı/eksi) | 02, 03, 04, 05, 06 (her birinde Özet / Seçenekler / Öneri bölümleri) |
| Önerilen mimari taslağı (akış diyagramı) | 05 §3 (uçtan uca), 02 §7 (ingestion), 03 §3 ve §7.2 (kaynak/görsel), 04 §5 (doğrulama), 06 §3, §5.2, §6 (veri akışı, hibrit, yetki) |
| Araç/model seçim önerileri | Embedding → 06 §5.1 (yalnızca ad: `bge-m3`) · Vektör DB → 06 §5.1, §6 (Qdrant) · LLM → 04 · TTS → 06 §5.1 (yalnızca ad) · UI → 05, 03 · Parser/OCR → 02 · STT → 05 |
| Kullanılacak manuellerin envanteri ve format değerlendirmesi | 01 (+ 02 §2.2–3) |
| Açık sorular ve riskler listesi | Her notun son bölümü; en kapsamlı: 06 §9, 04 §8 |
| Uygulama için görev/faz planı | **[UYGULAMA-PLANI.md](../UYGULAMA-PLANI.md)** (birleşik plan: 8 aşama, karar kapıları, zaman çizelgesi, öneriler, geçiş kontrol listesi) |

## Araç/model önerileri — notlardan derlenmiş özet

| Bileşen | Öneri (notlardaki) | Alternatif | Not |
|---------|--------------------|-----------|-----|
| Parser | Docling | Marker, MinerU | 02 |
| OCR | Docling içi (EasyOCR/RapidOCR) | Azure DI, Surya | 02 |
| Sayfa render / vurgu | PyMuPDF (AGPL kontrolü) | pypdfium2, pdf2image | 02, 03 |
| Görsel anlama | A+B (ingestion'da VLM açıklaması + cevapta VLM) | ColPali/ColQwen ikinci kanal | 03 |
| Embedding | `bge-m3` (lokal) | — | 06'da referans; seçim gerekçesi rag-temelleri.md'de (sette yok) |
| Reranker | `bge-reranker-v2-m3` (lokal) | — | 06'da referans |
| Vektör DB | Qdrant (Docker, lokal), tek koleksiyon + zorunlu filtre | Marka başına koleksiyon | 06 |
| LLM | Pilotta 3 sağlayıcı orta seviye + 1 küçük + 1 lokal (~27–32B Apache-2.0) | 70B lokal | 04 |
| TTS | Chatterbox Multilingual (lokal) / Azure (bulut, STT ile tek sağlayıcı) | — | 05, 06'da referans; ayrıntı tts.md'de (sette yok) |
| STT | Bulut serbestse Azure STT, değilse faster-whisper (large-v3-turbo) | Whisper large-v3 | 05 |
| UI | Pilot: Streamlit + `streamlit-pdf-viewer`; üretim: React + FastAPI | NiceGUI | 05 |
| Orkestrasyon | Çatısız modüler Python + JSON denetim izi | LlamaIndex parçaları, Haystack | 05 |
| Değerlendirme | Custom script + RAGAS (TR) + insan | DeepEval, TruLens | 04 |
| Dağıtım | B. Hibrit (LLM/TTS kurumsal bulut + ZDR) | C. Tamamen lokal | 06 |

