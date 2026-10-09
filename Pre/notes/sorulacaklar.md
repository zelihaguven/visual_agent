# Sorulacaklar ve Açık Kalanlar

> **Başlangıç:** 2026-10-09 · **Kaynak:** Tüm adımların notları + [req.md → Açık Sorular ve Riskler](../req.md)
> **Kullanım:** Soruları ilgili kişilere sorup cevabı `> **Cevap:**` satırına yaz. Cevaplanan sorular req.md'deki tabloya ve ilgili nota işlenecek.
> Yeni adımlarda çıkan sorular bu dosyaya eklenecek.

**Öncelik:** 🔴 Birçok kararı birden belirliyor, önce sorulmalı · 🟡 Bir bileşenin tasarımını etkiliyor · ⚪ Pilotta da öğrenilebilir

---

## A. Sorulacaklar

### A1. Yönetim / hukuk / müşteri sözleşmeleri

| # | Soru | Neden önemli (hangi kararı belirliyor) | Öncelik |
|---|------|----------------------------------------|---------|
| **Q1** (0.1) | Müşteri manuelleri (ve manuelden alıntı içeren cevaplar) **bulut servislere** (OpenAI, Anthropic, Google, Microsoft Azure, AWS) gönderilebilir mi, yoksa her şey **şirket içinde** mi çalışmalı? | LLM, embedding, OCR, VLM, TTS, STT seçiminin tamamı. Veri kurum dışına çıkabilecek noktalar: [pdf-isleme.md](pdf-isleme.md) "VLM ile şekil açıklaması veri güvenliğini etkiler mi?" | 🔴 |
| Q1-a | Bulut kabul edilirse şartlar ne? Veri saklamama (*zero data retention*) ve eğitimde kullanmama sözleşmesi yeterli mi? Verinin işlendiği bölge (AB / Türkiye) önemli mi? Şirketin zaten kurumsal bir Azure / AWS / Google hesabı var mı? | Hangi sağlayıcı, hangi sözleşme. Tek sağlayıcıda kalmak sözleşme sayısını azaltır (tts.md K5) | 🔴 |
| **7.1** | Müşteri (marka) manuellerinde **NDA / gizlilik maddesi** var mı? Üçüncü taraf bir servise gönderilmesi açıkça yasak mı? Hukuka bakılacak 8 madde listesi: [guvenlik.md 7.1](guvenlik.md) (üçüncü taraf, alt yüklenici izni, coğrafi kısıt, saklama/imha, güvenlik standardı, ihlal bildirimi, amaç sınırlaması, yapay zekâ maddesi) | Q1'in hukuki dayanağı | 🔴 |
| Müşteri izni | Sözleşme bulutu açıkça yasaklamıyor ama izin de vermiyorsa, **müşteriden yazılı izin** istenebilir mi? (Kurumsal bulut, AB bölgesi, veri saklamama, eğitimde kullanmama güvenceleriyle) | Hibrit senaryonun (guvenlik.md 7.2, B) mümkün olup olmadığı | 🟡 |
| Silme | Müşteri sözleşmesi bitince dokümanların ve **türevlerinin** (chunk, vektör, sayfa resmi, loglardaki alıntılar) silinmesi gerekiyor mu? | Veri modelinde doküman bazlı silme tasarımı | ⚪ |
| Loglar | Kullanıcı soruları ve kimlikleri (denetim izi) **ne kadar süre** saklanmalı? Kim görebilir? Çalışanlara aydınlatma metni gerekiyor mu? (KVKK sorumlusu) | Denetim izi tasarımı, KVKK | 🟡 |
| **Q9** | Kullanıcı ekranda sadece cevabın geçtiği sayfayı mı görmeli, yoksa **dokümanın tamamında gezinebilmeli / indirebilmeli** mi? | Sayfa görüntüleme yöntemi (kaynak-gosterme.md 3. bölüm), gizlilik | 🟡 |
| **7.3** | Her kullanıcı her markanın manuelini görebilir mi, yoksa **marka bazlı yetki** mi olmalı? (Örn. Nike hattındaki ekip sadece Nike'ı görür) | Retrieval filtresi, kullanıcı girişi | 🟡 |
| KVKK | Sesli soru (STT) eklenirse kullanıcının **ses kaydı** işlenebilir mi? Kaydedilmeli mi, hemen silinmeli mi? | STT kararı (arayuz-orkestrasyon.md 6.4) | ⚪ |
| Bütçe | Aylık bulut API bütçesi veya **donanım (GPU sunucu) yatırımı** için bir sınır var mı? | Bulut mu lokal mi (Q1 ile birlikte), LLM seçimi (Adım 4) | 🟡 |

> **Q1 Cevap:**
>
> **7.1 Cevap:**
>
> **Müşteri izni Cevap:**
>
> **Silme Cevap:**
>
> **Loglar Cevap:**
>
> **Q9 Cevap:**
>
> **7.3 Cevap:**
>
> **KVKK Cevap:**
>
> **Bütçe Cevap:**

### A2. BT / altyapı

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q5** (0.5) | Kullanılabilecek bir **GPU** var mı? (Model, bellek miktarı (VRAM)). Yoksa bir sunucu veya bulut GPU alınabilir mi? | Lokal LLM, lokal OCR/VLM, lokal TTS (Chatterbox) ve STT (Whisper) uygulanabilirliği | 🔴 |
| Ağ | Atölyede **internet / Wi-Fi** var mı? Sistemi kullanacak cihazlar şirket ağına bağlı mı? | Bulut servisler için internet şart. Yoksa her şey lokal olmalı | 🔴 |
| Giriş | Şirkette **kurumsal kullanıcı hesabı** (ör. Microsoft / Google hesabıyla tek giriş, SSO) var mı? | Kullanıcı girişi, marka bazlı yetki (7.3), arayüz teknolojisi | 🟡 |
| Sunucu | Sistem nerede çalışacak? Şirket içi bir sunucu mu, bulut sunucu mu? | Kurulum, bakım | 🟡 |

> **Q5 Cevap:**
>
> **Ağ Cevap:**
>
> **Giriş Cevap:**
>
> **Sunucu Cevap:**

### A3. Doküman sahipleri / kalite ekibi

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q2** (0.3) | Gerçek manuellerin dili ne (TR / EN / karışık / başka)? Kullanıcılar hangi dilde soru soracak? Şu an İngilizce manueller Türkçeye çevrilip mi kullanılıyor? | Embedding, LLM, TTS seçimi. Kısmen cevaplı: TR + EN | 🟡 |
| **Q8** | Sistem hangi **doküman türlerini** kapsayacak? (Marka şartnameleri, makine kılavuzları, terzilik/yöntem kitapları, iç talimatlar, başka?) | Metadata şeması (`doc_type`), sorgu yönlendirme (rag-temelleri.md 1.7) | 🟡 |
| **Q3** | Gerçek dokümanların ne kadarı **taranmış** PDF? Hangi **görsel türleri** var (dikiş tipi çizimleri, ölçülü teknik çizimler, fotoğraflar, makine parça çizimleri) ve ne sıklıkta? Mümkünse her türden 2–3 örnek sayfa | OCR ihtiyacı, görsel anlama yöntemi (kaynak-gosterme.md 5. bölüm) | 🟡 |
| **Q7** | Manueller şu an nerede ve nasıl saklanıyor? **Klasör ve dosya adlandırma düzeni** ne? Marka, versiyon, yürürlük tarihi dosyada veya kapakta yazıyor mu? | Metadata'nın otomatik çıkarımı (pdf-isleme.md 2.5) | 🟡 |
| **R3** | Aynı dokümanın **birden fazla versiyonu** var mı? Hangisinin geçerli olduğu nasıl biliniyor? Eski versiyonlar saklanıyor mu? | Çelişen bilgi riski, versiyon filtresi | 🟡 |
| Biçimler | Gerçek şartnamelerde **değerler hangi biçimde** yazılıyor? (Tolerans "11 ± 1" mi "10-12" mi, birimler, kesirler, kodlar, hata kodu ve parça no. biçimleri.) Örnek sayfalar yeterli | TTS normalizasyon kuralları (tts.md 2.2, 2.5), sayı doğrulaması (S11) | ⚪ |
| **0.4** | **Test soru seti:** Kullanıcıların gerçekte sorduğu 10–20 soru, **doğru cevabı ve geçtiği sayfayla** birlikte kim hazırlayabilir? (Kalite ekibi ideal) | Değerlendirme (Adım 4.4), pilot başarı kriterleri (6.3). Test seti olmadan sistem ölçülemez | 🔴 |

> **Q2 Cevap:**
>
> **Q8 Cevap:**
>
> **Q3 Cevap:**
>
> **Q7 Cevap:**
>
> **R3 Cevap:**
>
> **Biçimler Cevap:**
>
> **0.4 Cevap:**

### A4. Kullanıcılar (ustalar, kalite ekibi)

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q11** | Sistem hangi cihazda kullanılacak (PC, tablet, duvara asılı ekran / kiosk)? Ekran nerede duracak, aynı anda kaç kişi kullanacak? | Ekran düzeni, arayüz teknolojisi (arayuz-orkestrasyon.md 6.2) | 🟡 |
| **Q4** | Sesli soru sormak ister misiniz, yoksa yazmak yeterli mi? (Eller meşgul, eldiven, gürültü) | STT gerekli mi (6.4) | ⚪ |
| **Q10-a** | Atölyede kodlar nasıl söyleniyor? Dikiş tipi **301**: "üç yüz bir" mi "üç sıfır bir" mi? Model **S-7300A**: "S yetmiş üç yüz A" mı? **LSc-2**, hata kodu **E-07** nasıl okunuyor? | TTS normalizasyon kuralları (tts.md 2.5) | ⚪ |
| **Q10-b** | İngilizce terimler mi Türkçe karşılıkları mı kullanılıyor? ("SPI" mi "inç başına dikiş" mi, "lockstitch" mi "düz dikiş" mi, "overedge" mi "overlok" mu) | Sesli metin ve ekran cevabının dili | ⚪ |
| **Q10-c** | Sesli cevap **hoparlörden** mi dinlenmeli, **kulaklıkla** mı? (Gürültü, iş güvenliği) | Donanım, TTS ses seviyesi | ⚪ |
| Okuma | Cevap otomatik olarak sesli okunsun mu, butona basınca mı? Sesli cevap ne kadar uzun olmalı (kısa özet mi, tamamı mı)? | tts.md 2.5, arayuz-orkestrasyon.md 6.2 | ⚪ |
| Marka | Soruda marka yazılmazsa sistem "Hangi marka için?" diye sorsun mu, yoksa ekranda marka seçme kutusu mu olsun? | Metadata filtresi (rag-temelleri.md S8 / 1.7) | ⚪ |
| Süre | Bir cevap için **ne kadar beklemek** kabul edilebilir? (3 sn? 10 sn?) | Pilot başarı kriteri (req.md 6.3), doğrulamadan sonra gösterme kararı (tts.md R5) | 🟡 |

> **Q11 Cevap:**
>
> **Q4 Cevap:**
>
> **Q10-a Cevap:**
>
> **Q10-b Cevap:**
>
> **Q10-c Cevap:**
>
> **Okuma Cevap:**
>
> **Marka Cevap:**
>
> **Süre Cevap:**

### A5. Kalite yönetimi / süreç sahipleri (Adım 4'ten)

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| Hata toleransı | Sistemin **yanlış değer** vermesi için kabul edilebilir bir oran var mı (ör. 100 cevapta 1)? Yoksa sıfır tolerans mı, ve bu durumda "emin değilsen cevap verme" tercihinin artması (daha sık "bulunamadı") kabul mü? | Eşik ayarı, pilot başarı kriterleri (llm-degerlendirme.md 4.4) | 🔴 |
| Genel bilgi | Manuelde olmayan ama genel sektör bilgisi olan cevaplar (ör. "genelde dikiş atlamasının sebepleri") verilebilir mi, yoksa **sadece manuel** mi? Verilirse "manuelde değil, genel bilgi" etiketiyle mi? | Prompt kuralı 1 (prompt-taslak.md), R4 | 🟡 |
| Sorumluluk | Sistemin cevabıyla yapılan bir işte hata çıkarsa son onay kimde? Kritik değerlerde (tolerans, ölçü) kullanıcının kaynağı görüp onaylaması zorunlu mu olmalı? | Arayüzde onay adımı, denetim izi | 🟡 |
| Çeviri | Kaynak İngilizce olduğunda ekranda orijinal İngilizce alıntı da gösterilsin mi (önerilen), yoksa sadece Türkçe cevap mı? | Çeviri hatasına karşı önlem (llm-degerlendirme.md 0.5) | ⚪ |
| İnsan değerlendirmesi | Pilotta cevapları "bu cevapla dikim yapar mıydım?" diye puanlayacak bir kalite uzmanı ayrılabilir mi? | Değerlendirme (4.4) | 🟡 |

> **Hata toleransı Cevap:**
>
> **Genel bilgi Cevap:**
>
> **Sorumluluk Cevap:**
>
> **Çeviri Cevap:**
>
> **İnsan değerlendirmesi Cevap:**

---

## B. Bizim tarafımızda açık kalanlar (soru değil, yapılacak iş)

Bunlar kimseye sorulmayacak. Pilotta ölçülecek veya kesin seçimden önce kontrol edilecek.

| Konu | Ne yapılacak | Nerede takip ediliyor |
|------|--------------|-----------------------|
| Retrieval doğrulamaları | `bge-m3` TR↔EN, hybrid vs. dense, BM25 vs. BGE-M3 sparse, Türkçe kök bulucu, reranker gecikmesi, query translation (Q6) | req.md 6.1, [rag-temelleri.md → Doğrulanacaklar](rag-temelleri.md) |
| Parser karşılaştırması | Docling dışındaki araçlar (Marker, PyMuPDF4LLM) aynı zor sayfalarda | req.md 6.2, pdf-isleme.md 2.3 |
| Faz 1'den devredilenler | OCR satır kaybı, tablo satırı temizliği, basılı ↔ PDF sayfa eşleme, tarayıcıda vurgunun gözle kontrolü | req.md 6.2, [faz1_output/report.md](../../faz1_output/report.md) |
| Görsel anlama | VLM açıklaması (A+B) ile ColPali (C+B) karşılaştırması, görsel test soruları | kaynak-gosterme.md 5. bölüm |
| TTS denemesi | 4 test cümlesiyle aday karşılaştırması, Chatterbox Türkçe kalitesi (R6), gecikme | req.md 6.1, tts.md 2.2 |
| Fiyat ve lisans doğrulaması | Seçilecek servislerin fiyat ve lisanslarını resmi sayfalardan kontrol etmek. Azure container'da Türkçe ses var mı? | tts.md, ileride Adım 4 / 7 |
| Test setinin eksikleri | Türkçe doküman yok, aynı dokümanın iki versiyonu yok, Brother parça kitabı (M3) formatı kontrol edilmedi | [manual-envanteri.md](manual-envanteri.md) |
| Streamlit davranışı | PDF görüntüleyicide gezinmenin rerun tetikleyip tetiklemediği | arayuz-orkestrasyon.md 0.2 ara soru |
