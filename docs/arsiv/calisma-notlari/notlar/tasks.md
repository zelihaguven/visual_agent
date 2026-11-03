Manual tabanlı RAG + Sesli Yanıt Visual Board – Temel Konu Araştırması

Amaç

Kullanıcının bir visual board üzerinden soru sorduğu (örn. "Nike için dikiş standartları nelerdir?"), modelin RAG ile indekslenmiş manuallerden ilgili bilgiyi bulduğu, bilginin geçtiği manual sayfasını ekranda gösterdiği ve yanıtı TTS modeliyle sesli okuduğu bir sistemin kurulması.

Bu task, projeye başlamadan önce öğrenilmesi gereken temel konuların araştırılmasını kapsar (araştırma aşaması). Uygulama aşaması araştırma çıktılarına göre ayrı task'lara bölünecektir.

Hedef Akış

Kullanıcı soru sorar (marka/müşteri bilgisi içerebilir: Nike vb.)

Sistem sorguyu analiz eder, ilgili marka/manual ile filtreler

RAG ile manual içinden ilgili bölümler getirilir

LLM, kaynağa dayalı yanıt üretir (kaynak: dosya adı + sayfa no)

Bulunan manual sayfası görsel olarak ekranda gösterilir (mümkünse ilgili alan vurgulanır)

Yanıt TTS ile sesli okunur

Araştırılacak Temel Konular

1. RAG Temelleri

RAG mimarisi ve bileşenleri (ingestion, chunking, embedding, vector DB, retrieval, generation)

Chunking stratejileri (sabit boyut, semantic, sayfa/başlık bazlı) ve sayfa bazlı izlenebilirlik

Embedding model seçenekleri (çok dilli, Türkçe/İngilizce destekli)

Vector DB seçenekleri (Chroma, Qdrant, FAISS, pgvector vb.) ve karşılaştırma

Hybrid search (BM25 + vektör), reranking, metadata filtreleme

2. Manual / PDF İşleme

Manual formatlarının envanteri (dijital PDF, taranmış PDF, tablo/şekil ağırlıklı içerik)

PDF parsing ve layout-aware ayrıştırma araçları (tablolar, şekiller, çok kolonlu sayfalar)

OCR ihtiyacı ve seçenekleri (taranmış manuallerde)

Her chunk için metadata tutma: marka, doküman adı, versiyon, sayfa numarası, (varsa) bounding box

3. Kaynak Gösterme ve Sayfa Görüntüleme

Cevaptan kaynağa geri izlenebilirlik (citation / source grounding)

PDF sayfasını görsele çevirme ve ekranda gösterme yöntemleri

İlgili metnin sayfa üzerinde vurgulanması (highlight / bbox)

Multimodal / görsel tabanlı retrieval yaklaşımları (örn. ColPali benzeri) ve gerekliliği

4. LLM Seçimi ve Yanıt Kalitesi

Model seçenekleri (bulut API vs. lokal/açık kaynak) ve Türkçe performansı

Prompt tasarımı: yalnızca kaynağa dayalı yanıt, "bilgi bulunamadı" davranışı

Hallucination azaltma yöntemleri

RAG değerlendirme yöntemleri (test soru seti, retrieval doğruluğu, yanıt doğruluğu; örn. RAGAS)

5. TTS (Text-to-Speech)

TTS model/servis seçenekleri (bulut ve açık kaynak) ve Türkçe/İngilizce kalite karşılaştırması

Gecikme (latency), streaming ses, maliyet ve lisans konuları

Uzun/teknik yanıtların sesli okunmaya uygun hale getirilmesi (kısaltma, sayı ve birim okunuşu)

6. Visual Board / Arayüz ve Orkestrasyon

Arayüz seçenekleri (Streamlit, Gradio, Open WebUI, web tabanlı özel arayüz vb.)

Soru girişi + sayfa görüntüleyici + ses oynatıcı bileşenlerinin tek ekranda birleştirilmesi

Orkestrasyon çatıları (LangChain, LlamaIndex vb.) ve karşılaştırma

Sesli soru girişi (STT) ihtiyacı olup olmadığının değerlendirilmesi

7. Veri Güvenliği ve Erişim

Müşteri (marka) manuallerinin gizlilik gereksinimleri

Bulut API kullanımı vs. şirket içi (on-prem) çalıştırma

Marka bazlı erişim yetkilendirme ihtiyacı

Beklenen Çıktılar

Her konu başlığı için kısa araştırma notu (özet, seçenekler, artı/eksi)

Önerilen mimari taslağı (akış diyagramı)

Araç/model seçim önerileri (embedding, vector DB, LLM, TTS, arayüz)

Kullanılacak manuallerin envanteri ve format değerlendirmesi

Açık sorular ve riskler listesi

Uygulama aşaması için önerilen task/aşama planı

Notlar

Önceliklendirme önerisi: 1, 2, 3 → 5, 6 → 4 → 7

Küçük bir pilot (tek marka, birkaç manual) ile uçtan uca prototip denemesi araştırmanın sonunda önerilebilir.