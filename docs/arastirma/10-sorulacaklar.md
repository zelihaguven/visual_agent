# Sorulacaklar ve Açık Kalanlar

> **Kaynak not:** `sorulacaklar.md` (başlangıç 2026-10-09) · Tüm adımların notlarından ve [plan](15-plan.md) "Açık Sorular ve Riskler" bölümünden (§11) derlenmiş.
> **Kullanım:** Sorular ilgili kişilere sorulup cevaplar [plan](15-plan.md)'daki tabloya ve ilgili nota işlenecek; yeni adımlarda çıkan sorular buraya eklenecek. **Durum (2026-10-09): hiçbir soru cevaplanmamış** (kaynaktaki tüm "Cevap" satırları boş; bu notta boş cevap satırları çıkarıldı). [Plan](15-plan.md) §11'deki kısmi durumlar: **Q2** — TR + EN destek bekleniyor; şu an EN manueller TR'ye çevriliyor, hedef çevirmeden kullanmak · **Q3** — gerçek spec ve manuellerde dikiş, ölçü ve makine görselleri olduğu biliniyor → görsel anlama gerekli; türler/oranlar açık · **Q7** — yön belirlendi: otomatik çıkarım (klasör/dosya adı kuralı + kapak regex'i + LLM), emin olunamayanlarda insan onayı; açık: gerçek klasör/adlandırma düzeni.
> **Bağlantılı:** [13-acik-sorular-ve-riskler.md](13-acik-sorular-ve-riskler.md) (konsolide liste), [06-veri-guvenligi-ve-erisim.md](06-veri-guvenligi-ve-erisim.md), [07-rag-temelleri.md](07-rag-temelleri.md), [08-tts.md](08-tts.md)
> **Beslediği çıktılar:** **Açık sorular ve riskler listesi** · Görev planı (ön koşullar)

**Öncelik:** 🔴 Birçok kararı birden belirliyor, önce sorulmalı · 🟡 Bir bileşenin tasarımını etkiliyor · ⚪ Pilotta da öğrenilebilir

## Özet

- 🔴 **Önce sorulacaklar (7):** Q1 (bulut mu şirket içi mi), Q1-a (bulut şartları), 7.1 (müşteri NDA'ları), Q5 (GPU), Ağ (atölyede internet/Wi-Fi), 0.4 (test soru setini kim hazırlar), hata toleransı (kabul edilebilir yanlış değer oranı).
- Soruların muhatapları: yönetim/hukuk, BT, doküman sahipleri/kalite ekibi, kullanıcılar (ustalar), kalite yönetimi.
- B bölümü kimseye sorulmayacak, bizim yapacağımız doğrulama işleri (çoğu pilota devredildi).

## A. Sorulacaklar

### A1. Yönetim / hukuk / müşteri sözleşmeleri

| # | Soru | Neden önemli (hangi kararı belirliyor) | Öncelik |
|---|------|----------------------------------------|---------|
| **Q1** (0.1) | Müşteri manuelleri (ve manuelden alıntı içeren cevaplar) **bulut servislere** (OpenAI, Anthropic, Google, Microsoft Azure, AWS) gönderilebilir mi, yoksa her şey **şirket içinde** mi çalışmalı? | LLM, embedding, OCR, VLM, TTS, STT seçiminin tamamı. Veri kurum dışına çıkabilecek noktalar: [02-pdf-isleme.md](02-pdf-isleme.md) "VLM ile şekil açıklaması veri güvenliğini etkiler mi?" | 🔴 |
| Q1-a | Bulut kabul edilirse şartlar ne? Veri saklamama (*zero data retention*) ve eğitimde kullanmama sözleşmesi yeterli mi? Verinin işlendiği bölge (AB / Türkiye) önemli mi? Şirketin zaten kurumsal bir Azure / AWS / Google hesabı var mı? | Hangi sağlayıcı, hangi sözleşme. Tek sağlayıcıda kalmak sözleşme sayısını azaltır ([08-tts.md](08-tts.md)) | 🔴 |
| **7.1** | Müşteri (marka) manuellerinde **NDA / gizlilik maddesi** var mı? Üçüncü taraf servise gönderilmesi açıkça yasak mı? Hukuka bakılacak 8 madde: üçüncü taraf, alt yüklenici izni, coğrafi kısıt, saklama/imha, güvenlik standardı, ihlal bildirimi, amaç sınırlaması, yapay zekâ maddesi ([06-veri-guvenligi-ve-erisim.md](06-veri-guvenligi-ve-erisim.md), kaynakta guvenlik.md 7.1) | Q1'in hukuki dayanağı | 🔴 |
| Müşteri izni | Sözleşme bulutu açıkça yasaklamıyor ama izin de vermiyorsa **müşteriden yazılı izin** istenebilir mi? (Kurumsal bulut, AB bölgesi, veri saklamama, eğitimde kullanmama güvenceleriyle) | Hibrit senaryonun (B) mümkün olup olmadığı ([06](06-veri-guvenligi-ve-erisim.md), kaynakta 7.2) | 🟡 |
| Silme | Müşteri sözleşmesi bitince dokümanların ve **türevlerinin** (chunk, vektör, sayfa resmi, loglardaki alıntılar) silinmesi gerekiyor mu? | Veri modelinde doküman bazlı silme tasarımı | ⚪ |
| Loglar | Kullanıcı soruları ve kimlikleri (denetim izi) **ne kadar süre** saklanmalı? Kim görebilir? Çalışanlara aydınlatma metni gerekiyor mu? (KVKK sorumlusu) | Denetim izi tasarımı, KVKK | 🟡 |
| **Q9** | Kullanıcı ekranda sadece cevabın geçtiği sayfayı mı görmeli, yoksa **dokümanın tamamında gezinebilmeli / indirebilmeli** mi? | Sayfa görüntüleme yöntemi ([03-kaynak-gosterme.md](03-kaynak-gosterme.md), kaynakta 3. bölüm), gizlilik | 🟡 |
| **7.3** | Her kullanıcı her markanın manuelini görebilir mi, yoksa **marka bazlı yetki** mi olmalı? (Örn. Nike hattındaki ekip sadece Nike'ı görür) | Retrieval filtresi, kullanıcı girişi | 🟡 |
| KVKK | Sesli soru (STT) eklenirse kullanıcının **ses kaydı** işlenebilir mi? Kaydedilmeli mi, hemen silinmeli mi? | STT kararı ([05-arayuz-ve-orkestrasyon.md](05-arayuz-ve-orkestrasyon.md), kaynakta 6.4) | ⚪ |
| Bütçe | Aylık bulut API bütçesi veya **donanım (GPU sunucu) yatırımı** için bir sınır var mı? | Bulut mu lokal mi (Q1 ile birlikte), LLM seçimi ([04](04-llm-secimi-ve-degerlendirme.md)) | 🟡 |

### A2. BT / altyapı

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q5** (0.5) | Kullanılabilecek bir **GPU** var mı? (Model, bellek miktarı/VRAM.) Yoksa sunucu veya bulut GPU alınabilir mi? | Lokal LLM, lokal OCR/VLM, lokal TTS (Chatterbox) ve STT (Whisper) uygulanabilirliği | 🔴 |
| Ağ | Atölyede **internet / Wi-Fi** var mı? Sistemi kullanacak cihazlar şirket ağına bağlı mı? | Bulut servisler için internet şart; yoksa her şey lokal olmalı | 🔴 |
| Giriş | Şirkette **kurumsal kullanıcı hesabı** (ör. Microsoft / Google ile tek giriş, SSO) var mı? | Kullanıcı girişi, marka bazlı yetki (7.3), arayüz teknolojisi | 🟡 |
| Sunucu | Sistem nerede çalışacak? Şirket içi sunucu mu, bulut sunucu mu? | Kurulum, bakım | 🟡 |

### A3. Doküman sahipleri / kalite ekibi

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q2** (0.3) | Gerçek manuellerin dili ne (TR / EN / karışık / başka)? Kullanıcılar hangi dilde soru soracak? İngilizce manueller şu an Türkçeye çevrilip mi kullanılıyor? | Embedding, LLM, TTS seçimi. **Kısmen cevaplı: TR + EN** | 🟡 |
| **Q8** | Sistem hangi **doküman türlerini** kapsayacak? (Marka şartnameleri, makine kılavuzları, terzilik/yöntem kitapları, iç talimatlar, başka?) | Metadata şeması (`doc_type`), sorgu yönlendirme ([07-rag-temelleri.md](07-rag-temelleri.md) §8.2, kaynakta 1.7) | 🟡 |
| **Q3** | Gerçek dokümanların ne kadarı **taranmış** PDF? Hangi **görsel türleri** var (dikiş tipi çizimleri, ölçülü teknik çizimler, fotoğraflar, makine parça çizimleri), ne sıklıkta? Mümkünse her türden 2–3 örnek sayfa | OCR ihtiyacı, görsel anlama yöntemi ([03](03-kaynak-gosterme.md), kaynakta 5. bölüm) | 🟡 |
| **Q7** | Manueller şu an nerede ve nasıl saklanıyor? **Klasör ve dosya adlandırma düzeni** ne? Marka, versiyon, yürürlük tarihi dosyada veya kapakta yazıyor mu? | Metadata'nın otomatik çıkarımı ([02](02-pdf-isleme.md), kaynakta 2.5) | 🟡 |
| **R3** | Aynı dokümanın **birden fazla versiyonu** var mı? Hangisinin geçerli olduğu nasıl biliniyor? Eski versiyonlar saklanıyor mu? | Çelişen bilgi riski, versiyon filtresi | 🟡 |
| Biçimler | Gerçek şartnamelerde **değerler hangi biçimde** yazılıyor? (Tolerans "11 ± 1" mi "10-12" mi; birimler, kesirler, kodlar, hata kodu ve parça no. biçimleri.) Örnek sayfalar yeterli | TTS normalizasyon kuralları ([08](08-tts.md) §2.1, §7), sayı doğrulaması (S11) | ⚪ |
| **0.4** | **Test soru seti:** kullanıcıların gerçekte sorduğu 10–20 soruyu **doğru cevabı ve geçtiği sayfayla** kim hazırlayabilir? (Kalite ekibi ideal) | Değerlendirme ([04](04-llm-secimi-ve-degerlendirme.md), kaynakta 4.4), pilot başarı kriterleri ([plan](15-plan.md) Faz 6.3). Test seti olmadan sistem ölçülemez | 🔴 |

### A4. Kullanıcılar (ustalar, kalite ekibi)

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q11** | Sistem hangi cihazda kullanılacak (PC, tablet, duvara asılı ekran / kiosk)? Ekran nerede duracak, aynı anda kaç kişi kullanacak? | Ekran düzeni, arayüz teknolojisi ([05](05-arayuz-ve-orkestrasyon.md), kaynakta 6.2) | 🟡 |
| **Q4** | Sesli soru sormak ister misiniz, yoksa yazmak yeterli mi? (Eller meşgul, eldiven, gürültü) | STT gerekli mi ([05](05-arayuz-ve-orkestrasyon.md), kaynakta 6.4) | ⚪ |
| **Q10-a** | Atölyede kodlar nasıl söyleniyor? Dikiş tipi **301**: "üç yüz bir" mi "üç sıfır bir" mi? Model **S-7300A**: "S yetmiş üç yüz A" mı? **LSc-2**, hata kodu **E-07** nasıl okunuyor? | TTS normalizasyon kuralları ([08](08-tts.md) §7) | ⚪ |
| **Q10-b** | İngilizce terimler mi Türkçe karşılıkları mı kullanılıyor? ("SPI" mi "inç başına dikiş" mi, "lockstitch" mi "düz dikiş" mi, "overedge" mi "overlok" mu) | Sesli metin ve ekran cevabının dili | ⚪ |
| **Q10-c** | Sesli cevap **hoparlörden** mi dinlenmeli, **kulaklıkla** mı? (Gürültü, iş güvenliği) | Donanım, TTS ses seviyesi | ⚪ |
| Okuma | Cevap otomatik mi sesli okunsun, butona basınca mı? Sesli cevap ne kadar uzun olmalı (kısa özet mi, tamamı mı)? | [08](08-tts.md) §7, [05](05-arayuz-ve-orkestrasyon.md) (kaynakta 6.2) | ⚪ |
| Marka | Soruda marka yazılmazsa sistem "Hangi marka için?" diye sorsun mu, yoksa ekranda marka seçme kutusu mu olsun? | Metadata filtresi ([07](07-rag-temelleri.md) §8, kaynakta S8 / 1.7) | ⚪ |
| Süre | Bir cevap için **ne kadar beklemek** kabul edilebilir? (3 sn? 10 sn?) | Pilot başarı kriteri ([plan](15-plan.md) Faz 6.3), doğrulamadan sonra gösterme kararı (R5, [plan](15-plan.md) §11; [08](08-tts.md) §5) | 🟡 |

### A5. Kalite yönetimi / süreç sahipleri (Adım 4'ten)

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| Hata toleransı | Sistemin **yanlış değer** vermesi için kabul edilebilir bir oran var mı (ör. 100 cevapta 1)? Yoksa sıfır tolerans mı; bu durumda "emin değilsen cevap verme" tercihinin artması (daha sık "bulunamadı") kabul mü? | Eşik ayarı, pilot başarı kriterleri ([04](04-llm-secimi-ve-degerlendirme.md), kaynakta 4.4) | 🔴 |
| Genel bilgi | Manuelde olmayan ama genel sektör bilgisi olan cevaplar (ör. "genelde dikiş atlamasının sebepleri") verilebilir mi, yoksa **sadece manuel** mi? Verilirse "manuelde değil, genel bilgi" etiketiyle mi? | Prompt kuralı 1 ([09-prompt-taslagi.md](09-prompt-taslagi.md)), R4 | 🟡 |
| Sorumluluk | Sistemin cevabıyla yapılan işte hata çıkarsa son onay kimde? Kritik değerlerde (tolerans, ölçü) kullanıcının kaynağı görüp onaylaması zorunlu mu olmalı? | Arayüzde onay adımı, denetim izi | 🟡 |
| Çeviri | Kaynak İngilizce olduğunda ekranda orijinal İngilizce alıntı da gösterilsin mi (önerilen), yoksa sadece Türkçe cevap mı? | Çeviri hatasına karşı önlem ([04](04-llm-secimi-ve-degerlendirme.md), kaynakta 0.5) | ⚪ |
| İnsan değerlendirmesi | Pilotta cevapları "bu cevapla dikim yapar mıydım?" diye puanlayacak bir kalite uzmanı ayrılabilir mi? | Değerlendirme (kaynakta 4.4) | 🟡 |

## B. Yapılması Gerekenler : 

Kimseye sorulmayacak; pilotta ölçülecek veya kesin seçimden önce kontrol edilecek.

| Konu | Ne yapılacak | Nerede takip ediliyor |
|------|--------------|-----------------------|
| Retrieval doğrulamaları | `bge-m3` TR↔EN, hybrid vs. dense, BM25 vs. BGE-M3 sparse, Türkçe kök bulucu, reranker gecikmesi, query translation (Q6) | [plan](15-plan.md) Faz 6.1, [07-rag-temelleri.md](07-rag-temelleri.md) §11 |
| Parser karşılaştırması | Docling dışındaki araçlar (Marker, PyMuPDF4LLM) aynı zor sayfalarda | [plan](15-plan.md) Faz 6.2, [02-pdf-isleme.md](02-pdf-isleme.md) (kaynakta 2.3) |
| Faz 1'den devredilenler | OCR satır kaybı, tablo satırı temizliği, basılı → fiziksel sayfa eşleme tablosu (kılavuz içi "Page 67" atıfları, kitapçık düzeni, üstte basılı numara; gösterim Faz 1'de çalışıyor), tarayıcıda vurgunun gözle kontrolü | [plan](15-plan.md) Faz 6.2, `faz1_output/report.md` (bu sette yok) |
| Görsel anlama | VLM açıklaması (A+B) ile ColPali (C+B) karşılaştırması, görsel test soruları | [03-kaynak-gosterme.md](03-kaynak-gosterme.md) (kaynakta 5. bölüm) |
| TTS denemesi | 4 test cümlesiyle aday karşılaştırması, Chatterbox Türkçe kalitesi (R6), gecikme | [plan](15-plan.md) Faz 6.1, [08-tts.md](08-tts.md) §9 |
| Fiyat ve lisans doğrulaması | Seçilecek servislerin fiyat ve lisanslarını resmi sayfalardan kontrol etmek; Azure container'da Türkçe ses var mı? | [08-tts.md](08-tts.md), ileride Adım 4 / 7 |
| Test setinin eksikleri | Türkçe doküman yok, aynı dokümanın iki versiyonu yok, Brother parça kitabı (M3) formatı kontrol edilmedi | [01-manual-envanteri.md](01-manual-envanteri.md) |
| Streamlit davranışı | PDF görüntüleyicide gezinmenin rerun tetikleyip tetiklemediği | [05-arayuz-ve-orkestrasyon.md](05-arayuz-ve-orkestrasyon.md) (kaynakta 0.2) |
