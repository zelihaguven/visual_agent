# Sorulacaklar ve Açık Kalanlar

> **Başlangıç:** 2026-10-09 · **Güncelleme:** 2026-10-10 · **Kaynak:** Tüm adımların notları + [req.md → Açık Sorular ve Riskler](../req.md)
> **Kullanım:** Soruları ilgili kişilere sorup cevabı `> **Cevap:**` satırına yaz. Cevaplanan sorular bu dosyadan çıkarılır, kararlar aşağıdaki tabloya ve [cevaplar.md](../cevaplar.md) dosyasına işlenir.
> **Pilot etkisi:** Kalan soruların **hiçbiri pilotu engellemez** (pilot public dokümanlarla, lokal çalışıyor). Gerçek sisteme geçişte gerekir.

**Öncelik:** 🔴 Birçok kararı birden belirliyor, önce sorulmalı · 🟡 Bir bileşenin tasarımını etkiliyor · ⚪ Pilotta da öğrenilebilir

---

## Karara bağlananlar (2026-10-10, kaynak: [cevaplar.md](../cevaplar.md))

| Konu | Karar | Etkisi |
|------|-------|--------|
| Müşteri izni | Sözleşme sessizse müşteriden izin istenmeden geliştirilecek | Hibrit senaryo (B) önündeki engel kalktı. Sözleşme yasağı kontrolü (7.1) hâlâ açık |
| Silme | Sözleşme bitince doküman ve türevleri (chunk, vektör, sayfa resmi, log alıntıları) silinecek | Veri modelinde doküman bazlı silme zorunlu |
| Loglar / aydınlatma | Aydınlatma metni gerekli, izin alınacak. Logu kimin göreceği roller ile admin panelden belirlenecek | Rol modeli + admin paneli |
| Sayfa erişimi (Q9) | Yetkiye göre. Genelde en fazla bir önceki ve bir sonraki sayfa görülür | Görüntüleyici sayfa penceresi ile sınırlanacak |
| Marka yetkisi (7.3) | Marka bazlı yetki gerekli | Zorunlu pre-filter |
| STT ses kaydı | Ses kaydı saklanmayacak, metne dökülüp metin tutulabilir (saklamak için ayrıca izin) | STT'de ses kalıcı depolanmaz |
| Ağ | Muhtemelen fabrika ağı, ama bağlantı **kesilebilir** | Bulut bağımlılığı için çevrimdışı/yedek senaryo gerekir |
| Giriş (SSO) | Kurumsal SSO şart değil, yetkili e-posta veya kod ile giriş yeterli | Basit kimlik doğrulama |
| Sunucu | Muhtemelen harici bir hosting | Şirket içi sunucu varsayımı yok |
| Dil (Q2) | Manueller çoğunlukla İngilizce (çeviri ile gelebilir), sorular hep Türkçe, ama İngilizce de olabilir. **Model çift yönlü çalışmalı** | TR↔EN arama ve cevap |
| Doküman türü (Q8, Q3) | Şimdilik dijital veya taranmış PDF. Çizim ve görsel olabilir, her zaman olabileceği varsayılacak | OCR + şekil işleme tasarımda kalacak |
| Test seti (0.4) | Büyük ihtimalle AI hazırlar, uzman sonuçları kontrol eder | Pilotta uygulandı (eval/questions.json) |
| Sesli soru (Q4) | İsteniyor (ustanın eli dolu olabilir) | Pilot dışı, sonraki tur |
| Terim dili (Q10-b) | Türkçe karşılığı kullanılacak | Cevap ve sesli metin Türkçe terimli |
| Hoparlör (Q10-c) | Hoparlör | Ses seviyesi/gürültü testi |
| Okuma (kısmen) | "Soru sor" tuşu ile. İleride "hey asistan" benzeri sesli tetikleme | Otomatik başlatma yok |
| Marka seçimi | Sesli soruda marka sorulur. Yazılı soruda filtresiz tüm yetkili manueller, marka filtresi butonu görünür kalır | Pilot arayüzünde uygulandı |
| Bekleme süresi | 5 sn | Pilot hedefi. Ölçülen: 14,5 sn (lokal 7B, embedding/reranker CPU) |

---

## A. Sorulacaklar

### A1. Yönetim / hukuk / müşteri sözleşmeleri

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q1** (0.1) | Müşteri manuelleri (ve alıntı içeren cevaplar) **bulut servislere** (OpenAI, Anthropic, Google, Azure, AWS) gönderilebilir mi, yoksa her şey **şirket içinde / harici hostingde** mi çalışmalı? (Müşteriden izin istenmeyeceği kararlaştırıldı, ama sözleşme yasaklıyor mu?) | LLM, embedding, OCR, VLM, TTS, STT seçiminin tamamı | 🔴 |
| Q1-a | Bulut kabul edilirse şartlar: veri saklamama (*zero data retention*), eğitimde kullanmama, işlem bölgesi (AB / Türkiye), şirketin mevcut Azure / AWS / Google hesabı | Sağlayıcı ve sözleşme seçimi | 🔴 |
| **7.1** | Müşteri manuellerinde **NDA / gizlilik maddesi** var mı? Üçüncü taraf servise gönderilmesi yasak mı? ([guvenlik.md 7.1](guvenlik.md), 8 madde) | Q1'in hukuki dayanağı | 🔴 |
| Bütçe | Aylık bulut API bütçesi veya **GPU sunucu yatırımı** için sınır var mı? (Pilot: 24 GB'lık makinede 7B model yetersiz kaldı, daha büyük model donanım gerektiriyor) | Bulut mu lokal mi, model boyutu | 🔴 |

> **Q1 Cevap:**
>
> **Q1-a Cevap:**
>
> **7.1 Cevap:**
>
> **Bütçe Cevap:**

### A2. BT / altyapı

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q5** (0.5) | Kullanılabilecek bir **GPU** var mı (model, VRAM)? Yoksa sunucu veya bulut GPU alınabilir mi? | Lokal LLM, OCR/VLM, TTS, STT. Pilot: 24 GB Mac'te yalnızca ~7B model sığdı, 30B model GPU belleğini aştı | 🔴 |
| Çevrimdışı | Bağlantı kesilirse sistemin **hiç çalışmaması** kabul mü, yoksa lokal yedek model gerekli mi? | Hibrit senaryoda (bulut LLM) kesinti davranışı | 🟡 |

> **Q5 Cevap:**
>
> **Çevrimdışı Cevap:**

### A3. Doküman sahipleri / kalite ekibi

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q3** (kalan) | Gerçek dokümanların **taranmış oranı** ve görsel türlerinin sıklığı (dikiş çizimi, ölçülü teknik çizim, fotoğraf, parça çizimi)? Her türden 2–3 örnek sayfa | OCR yükü, şekil açıklaması (VLM) kapsamı | 🟡 |
| **Q7** | Manueller nerede, hangi **klasör ve dosya adı düzeniyle** saklanıyor? Marka, versiyon, yürürlük tarihi dosyada/kapakta yazıyor mu? | Metadata'nın otomatik çıkarımı ([pdf-isleme.md 2.5](pdf-isleme.md)) | 🟡 |
| **R3** | Aynı dokümanın **birden fazla versiyonu** var mı? Hangisinin geçerli olduğu nasıl anlaşılıyor? | Çelişen bilgi riski, versiyon filtresi | 🟡 |
| Biçimler | Gerçek şartnamelerde **değerler hangi biçimde** yazılıyor ("11 ± 1", "10-14", kesirler, kodlar)? Örnek sayfalar yeterli | Sesli metin kuralları, sayı doğrulaması | ⚪ |

> **Q3 Cevap:**
>
> **Q7 Cevap:**
>
> **R3 Cevap:**
>
> **Biçimler Cevap:**

### A4. Kullanıcılar (ustalar, kalite ekibi)

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| **Q11** | Hangi cihazda kullanılacak (PC, tablet, duvara asılı ekran / kiosk)? Ekran nerede duracak, aynı anda kaç kişi kullanacak? | Ekran düzeni, arayüz teknolojisi | 🟡 |
| **Q10-a** | Atölyede kodlar nasıl söyleniyor? Dikiş tipi **301**: "üç yüz bir" mi "üç sıfır bir" mi? **S-7300A**, **E-07** nasıl okunuyor? | Sesli metin kuralları. **Pilot (2026-10-13):** Sesli soruda (STT) "Es yetmiş üç yüz A", "E sıfır elli", "E bir üç üç" yazılı koda çevriliyor. Sesli **cevapta** (TTS) kodların nasıl okunacağı bu cevaba bağlı, kural tablosuna eklenmedi | ⚪ |
| Sesli cevap uzunluğu | Sesli cevap ne kadar uzun olmalı: **tek cümlelik özet** (ör. "11 artı eksi 1 dikiş"), **kısa özet + adımlar** mı, yoksa cevabın **tamamı** mı? | Ses süresi (pilotta 1 cümle ≈ 5 sn ses, ~12 sn üretim) | ⚪ |

> **Q11 Cevap:**
>
> **Q10-a Cevap:**
>
> **Sesli cevap uzunluğu Cevap:**

### A5. Kalite yönetimi / süreç sahipleri

| # | Soru | Neden önemli | Öncelik |
|---|------|--------------|---------|
| Hata toleransı | Yanlış değer için kabul edilebilir oran var mı (100 cevapta 1?) yoksa sıfır tolerans mı? "Emin değilsen cevap verme" tercihinin artması kabul mü? | Eşik ayarı, pilot başarı kriteri. Pilot: 10 sorunun 5'i doğru, doğrulama katmanı yanlışları yakaladı | 🔴 |
| Genel bilgi | Manuelde olmayan ama genel sektör bilgisi olan cevaplar verilebilir mi, yoksa **sadece manuel** mi? | Prompt kuralı 1 | 🟡 |
| Sorumluluk | Cevapla yapılan işte hata çıkarsa son onay kimde? Kritik değerlerde kaynağı görüp onaylama zorunlu mu? | Arayüzde onay adımı, denetim izi | 🟡 |
| Çeviri | Kaynak İngilizce iken ekranda orijinal İngilizce alıntı da gösterilsin mi (önerilen)? | Çeviri hatasına karşı önlem | ⚪ |
| İnsan değerlendirmesi | Cevapları "bu cevapla dikim yapar mıydım?" diye puanlayacak bir kalite uzmanı ayrılabilir mi? (Test setini uzmanın kontrol edeceği belirtildi, kim?) | Değerlendirme | 🟡 |

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

Kimseye sorulmayacak. Pilot sonucu ve kalan işler: [../../PILOT-RAPORU.md](../../PILOT-RAPORU.md).

| Konu | Durum | Nerede takip ediliyor |
|------|-------|-----------------------|
| Retrieval doğrulamaları (hybrid vs dense, BM25 vs sparse, TR→EN sorgu çevirisi, reranker gecikmesi) | **Kısmen:** 5 soruda hibrit ve dense sıralaması aynı çıktı (TR sorgu ile sparse kol işe yaramıyor). Çeviri, A/B ve gecikme optimizasyonu yapılmadı | [PILOT-RAPORU.md](../../PILOT-RAPORU.md) §8 |
| Parser karşılaştırması (Marker, PyMuPDF4LLM) | Yapılmadı. Docling + PyMuPDF yedeği kullanıldı | pdf-isleme.md 2.3 |
| Faz 1'den devredilenler | **Çözüldü:** basılı↔PDF sayfa eşleme (kısmen), OCR satır kaybına karşı PDF metin katmanı yedeği. **Açık:** tablo satırı başlık tekrarı, gerçek iki-OCR birleştirme | PILOT-RAPORU.md §6.2 |
| Görsel anlama (VLM vs ColPali) | Yapılmadı (şekiller atlanıyor) | kaynak-gosterme.md 5. bölüm |
| TTS denemesi | **Kısmen:** Chatterbox Türkçe denendi, kalite iyi (kullanıcı onayı), CPU'da gerçek zamanın ~2,5 katı. Aday karşılaştırması yapılmadı | PILOT-RAPORU.md §4 |
| Fiyat ve lisans doğrulaması | Yapılmadı | tts.md |
| Test setinin eksikleri | Türkçe doküman yok, aynı dokümanın iki versiyonu yok | [manual-envanteri.md](manual-envanteri.md) |
| Streamlit davranışı | Hatasız çalıştı (rerun sorunu görülmedi), tarayıcıda uzun süreli kullanım denenmedi | arayuz-orkestrasyon.md |
