# Visual Agent: Araştırma Sentezi

> **Tarih:** 2026-10-09 · **Güncelleme:** 2026-10-13 (pilot sonuçları, alınan kararlar ve risk durumları işlendi) · **Aşama:** Araştırma (Faz 5: Sentez) + pilot
> **Kapsam:** Manuel tabanlı soru-cevap, kaynak sayfa gösterimi ve sesli yanıt sisteminin araştırma bulguları, önerilen mimari, araç seçimleri, riskler ve bekleyen kararlar.
> **Diğer belgeler:** Pilot: [PILOT-RAPORU.md](PILOT-RAPORU.md) · Pilotun ve hedefin mimarisi: [MIMARI.md](MIMARI.md) · Uygulama planı: [UYGULAMA-PLANI.md](UYGULAMA-PLANI.md) · Bekleyen sorular: [sorulacaklar.md](calisma-notlari/notlar/sorulacaklar.md) · Ayrıntılı notlar: [Ek A](#ek-a-ayrıntılı-araştırma-notları)

---

## 1. Özet

Proje, atölye ve kalite ekiplerinin marka şartnameleri, makine kılavuzları ve dikim kaynakları hakkında soru sorabildiği bir sistem tasarlamayı amaçlamaktadır. Sistem, ilgili bilgiyi manuellerden bulur, **kaynağa dayalı** bir cevap üretir, bilginin geçtiği **manuel sayfasını vurgulu olarak** gösterir ve cevabı **sesli** okur.

Araştırma aşamasının ana sonuçları:

1. **Mimari netleşti.** Sistem iki hattan oluşur: dokümanların bir kez işlenip indekslendiği *doküman işleme hattı* ve her soruda çalışan *sorgu hattı* (Şekil 1). Çekirdek kısım (doküman ayrıştırma, sayfa ve konum bilgisinin korunması, sayfa üzerinde vurgulama) bir deneme ile doğrulandı: Üç farklı doküman türünde 27/27 test başarılı.
2. **En kritik risk yanlış değerdir.** Uydurulmuş veya yanlış aktarılmış bir değer (ör. dikiş sıklığı, tolerans) yanlış üretime yol açar. Bu risk için **altı katmanlı bir doğruluk güvencesi** tasarlandı (Şekil 2). İlke: Sistem emin değilse cevap vermez, cevap verdiğinde her değer kaynağında gösterilir.
3. **Veri güvenliği için hibrit yapı önerilmektedir.** Dokümanların tamamını işleyen adımlar kurum içinde, yalnızca cevap üretimi (ve sesli okuma) kurumsal sözleşmeli bulut serviste çalışır. Bu yapıda soru başına yalnızca 3–5 metin parçası kurum dışına çıkar (Şekil 3). Kesin karar, müşteri sözleşmelerinin incelenmesine bağlıdır.
4. **Model ve servis seçimi pilotta ölçülerek yapılacaktır.** Genel sıralamalar bu görevi (verilen metne sadakat, Türkçe-İngilizce geçiş, bilinmeyeni "bulunamadı" olarak bildirme) ölçmemektedir. Adaylar aynı test setiyle karşılaştırılacaktır.
5. **Maliyet karar verdirici değildir.** Tahmini kullanımda (günde ~200 soru) bulut LLM ve sesli okuma maliyeti aylık birkaç yüz doları aşmamaktadır. Kararları doğruluk ve gizlilik belirleyecektir.
6. **Pilot çalıştı, mimari doğrulandı, model yetersiz kaldı (2026-10-10 – 10-13).** 7 doküman (611 sayfa) ile tamamen lokal uçtan uca hat kuruldu: yazılı ve sesli soru, netleştirme, hibrit arama, kaynaklı cevap, otomatik doğrulama, vurgulu sayfa, sesli okuma. Son ölçüm (18 soru):
   - Arama, cevaplanabilir 12 sorunun **12'sinde** doğru sayfayı buldu. Genel sonuç **9/18**.
   - Hataların çoğu 7B lokal modelden: doğru parçadan yanlış sayı seçme, uydurma, dil kayması.
   - Doğrulama katmanı uydurma alıntıları, yabancı alfabeyi ve düşen toleransı yakaladı. Yanlış sayı seçimini yakalayamadı.
   - Belirsiz sorular modelden önce sorularak çözüldü.
   - 30B model 24 GB makineye sığmadı. GPU'suz makinede soru başına ~3 dk sürdü (hedef 5 sn).

   Ayrıntı: [Pilot raporu](PILOT-RAPORU.md).

**İlerlemek için gereken kararlar** (ayrıntı: Bölüm 9):
- Müşteri sözleşmeleri bulut servislerde işlemeyi yasaklıyor mu? (Q1, 7.1. Müşteriden izin istenmeden geliştirileceği kararlaştırıldı)
- Kurum içinde veya sunucuda GPU kullanılabilir mi? Pilot 7B modelin yetersiz, 30B modelin 24 GB makineye sığmadığını gösterdi (Q5, bütçe)
- Yanlış değer için kabul edilebilir oran nedir? (Hata toleransı)

*Karara bağlananlar:* test setini AI hazırlar, uzman kontrol eder · atölye ağı kesilebilir (yedek gerekli) · giriş e-posta/kod ile · marka bazlı yetki · ses kaydı saklanmaz · sözleşme bitince veri silinir. Tam liste: [calisma-notlari/notlar/sorulacaklar.md](calisma-notlari/notlar/sorulacaklar.md).

---

## 2. Sistemin amacı ve kullanım senaryosu

**Kullanıcılar:** Üretim ustaları, kalite ekibi. Ortam: atölye (gürültü, eldiven, ayakta kullanım).

**Örnek sorular:**
- "Nike ceketlerinde dış dikişlerin SPI değeri nedir?" (marka şartnamesi)
- "S-7300A'da dikiş atlıyor, ne yapmalıyım?" (makine kılavuzu, arıza giderme)
- "E-07 hatası ne anlama geliyor?" (hata kodu)

**Beklenen davranış:**

| Adım | Sistem ne yapar |
|------|-----------------|
| 1 | Sorudaki marka, ürün, makine modeli ve doküman türünü belirler. Kullanıcının yetkili olduğu dokümanlarla sınırlar |
| 2 | İlgili manuel parçalarını bulur (Türkçe soru, İngilizce manuel olabilir) |
| 3 | Kaynaktan **kelimesi kelimesine alıntı** yapar, cevabı Türkçe ve kısa yazar |
| 4 | Cevaptaki her değeri kaynakla otomatik karşılaştırır |
| 5 | Cevabı, orijinal alıntıyı ve **vurgulu kaynak sayfayı** aynı ekranda gösterir |
| 6 | İstenirse cevabın kısa halini sesli okur |
| — | Kaynaklarda bilgi yoksa: "Bu bilgi manuellerde bulunamadı" |

---

## 3. Önerilen mimari

![Şekil 1: Önerilen mimari](sekiller/sekil1-mimari.svg)

*Şekil 1. Önerilen mimari. Yeşil: kurum içinde çalışan bileşenler. Turuncu: hibrit senaryoda kurumsal sözleşmeli bulut servis (bulut kullanılamazsa kurum içi alternatifleri var, Bölüm 6).*

### 3.1 Doküman işleme hattı (her doküman için bir kez)

| Adım | Ne yapar | Neden önemli |
|------|----------|--------------|
| **Ayrıştırma + OCR** | PDF'ten metin, tablo ve şekilleri **sayfa numarası ve konum (bbox)** bilgisiyle çıkarır. Taranmış sayfaları OCR ile okur | Sayfa ve konum bilgisi, kaynak sayfanın gösterilmesi ve vurgulanması için şarttır |
| **Temizlik + şekil açıklaması** | Üst/alt bilgileri atar, sayfa geçişinde bölünen paragraf ve tabloları birleştirir. Çizimlere görsel dil modeliyle (VLM) metin açıklaması yazar | Dikiş, ölçü ve makine çizimlerindeki bilgi metin aramasıyla da bulunabilir hale gelir |
| **Bölümleme + metadata** | Dokümanı başlık/bölüm sınırlarından parçalara (chunk) böler. Her parçaya marka, ürün, makine modeli, doküman türü, sayfa ve konum bilgisi eklenir | Filtreleme (marka, model, yetki) ve kaynak gösterme bu bilgilere dayanır |
| **Embedding** | Her parçayı anlamını temsil eden bir vektöre çevirir (çok dilli model) | Türkçe soru ile İngilizce manuel arasında anlam eşleşmesi |
| **Vektör veritabanı** | Parçaları, vektörleri ve metadata'yı saklar | Hızlı ve filtreli arama |

### 3.2 Sorgu hattı (her soruda)

| Adım | Ne yapar |
|------|----------|
| **Sorgu analizi + yetki** | Marka, model, doküman türü belirlenir ve kullanıcının izinli markalarıyla kesiştirilir. Yetki filtresi **aramadan önce** ve sunucuda uygulanır |
| **Hibrit arama** | Anlamsal arama ile kelime aramasını birleştirir. Kelime araması kod ve numaralar (ör. "E-07", "ASTM D6193") için gereklidir |
| **Rerank + eşik** | Adayları daha isabetli bir modelle yeniden sıralar. En iyi skor eşiğin altındaysa cevap üretilmez: "Bulunamadı" |
| **LLM** | Önce alıntı, sonra cevap üretir. Çıktı sabit bir şemadadır (cevap, alıntılar, kaynak numaraları, sesli metin, bulunamadı) |
| **Otomatik doğrulama** | Kaynak numaraları, alıntının kaynakta birebir geçtiği ve sayı-tolerans değerleri kod tarafından kontrol edilir |
| **Sesli metin hazırlığı + TTS** | Kısa sesli metindeki sayı, tolerans, kod ve birimler okunacak kelimelere çevrilir ("11 (± 1)" → "on bir, artı eksi bir"), sonra seslendirilir |
| **Ekran** | Cevap + doğrulama rozeti + vurgulu kaynak sayfa + ses oynatıcı |
| **Denetim izi** | Her soru için hangi kaynakların kullanıldığı ve doğrulama sonucu kaydedilir |

### 3.3 Tasarım ilkeleri

| İlke | Açıklama |
|------|----------|
| **Kaynak gösterilmeden cevap yok** | LLM sayfa numarası yazmaz, yalnızca kaynak numarası verir. Sayfa ve konum metadata'dan gelir, bu nedenle uydurulamaz |
| **Doğrulanmadan gösterim ve seslendirme yok** | Cevap, otomatik doğrulamadan geçtikten sonra ekrana ve sese gönderilir |
| **Güvenlik kararları kodda** | Yetki ve filtreleme LLM'e bırakılmaz. Yetkisiz bilgi LLM'e hiç ulaşmaz |
| **Bileşenler değiştirilebilir** | Her bileşen bir adaptör arkasındadır. Bulut ile kurum içi model arasında geçiş, hattın geri kalanını değiştirmez |
| **Arayüz hattan bağımsız** | Soru-cevap hattı tek bir fonksiyon olarak çalışır. Arayüz (pilot veya üretim) bu fonksiyonu çağırır |
| **Hazır orkestrasyon çatısı yok** | Hat her soruda aynı adımları izler. Kritik adımlar projeye özeldir. Modüler Python kodu tercih edilmiştir (bkz. 4) |

---

## 4. Araç ve model seçim önerileri

**Durum sütunu:** ✅ araştırmayla netleşti · 🧪 pilotta ölçülerek kesinleşecek · ⏳ paydaş kararına bağlı

| Bileşen | Önerilen | Alternatif | Gerekçe | Durum |
|---------|----------|------------|---------|-------|
| **PDF ayrıştırma** | Docling | Marker, MinerU | Lokal, açık lisans (MIT), tablo yapısı, sayfa + konum bilgisi. Deneme ile doğrulandı | ✅ (diğer araçlarla karşılaştırma 🧪) |
| **OCR** | Docling içi OCR | Bulut OCR (karşılaştırma için), Surya | Lokal. Denemede bir satır kaybı görüldü, iki OCR'ın birleştirilmesi pilotta denenecek | 🧪 |
| **Şekil / çizim anlama** | Doküman işlemede VLM açıklaması + gerektiğinde cevap anında sayfa görselinin modele verilmesi | Görsel tabanlı arama (ColPali) | Tek arama sistemi, kesin vurgulama, kontrollü maliyet | 🧪 |
| **Bölümleme (chunking)** | Başlık/bölüm bazlı, tablolar bütün, sayfa ve konum listesiyle | Sabit uzunlukta bölme | Manuellerde yapı belirgin, sayfa izlenebilirliği şart | ✅ |
| **Embedding** | bge-m3 (lokal, çok dilli) | multilingual-e5, bulut embedding | Türkçe-İngilizce eşleşme, aynı model hem anlamsal hem kelime vektörü üretir | 🧪 (TR↔EN başarısı) |
| **Vektör veritabanı** | Qdrant (kurum içi) | pgvector | Güçlü metadata filtresi, yerleşik hibrit arama, kolay kurulum | ✅ |
| **Arama** | Hibrit (anlamsal + kelime) | Yalnızca anlamsal | Kodlar, standart ve parça numaraları sık geçiyor | ✅ (kelime tarafının yöntemi 🧪) |
| **Reranker** | bge-reranker-v2-m3 (lokal) | Bulut reranker | Çok dilli, lokal | 🧪 (gecikme) |
| **LLM** | Önceden seçilmemiştir. Pilotta 3 bulut sağlayıcıdan birer orta seviye model + 1 küçük model + 1 açık model aynı test setiyle karşılaştırılır | — | Görev, genel sıralamaların ölçmediği bir beceri gerektiriyor | 🧪 + ⏳ (Q1) |
| **Kurum içi LLM** (bulut kullanılamazsa) | Apache-2.0 lisanslı açık model, ~27–32B, 24 GB GPU | 70B (2 GPU) | 7–8B modeller Türkçe doküman soru-cevapta %49–75 doğrulukta kaldı (2026 çalışması) | 🧪 + ⏳ (GPU) |
| **TTS (sesli okuma)** | Test aşaması: Azure (Türkçe sesler, güçlü telaffuz kontrolü) | Google, ElevenLabs. Kurum içi: Chatterbox Multilingual | Telaffuz kontrolü, kelime zamanlaması, kurum içi çalıştırma seçeneği | 🧪 + ⏳ (Q1) |
| **Sesli metin hazırlığı** | Kural tablosu (sayı, tolerans, kesir, birim, kod) + test listesi | TTS'in kendi normalizasyonu | Türkçe için hazır kapsamlı araç yok, alan dar ve yönetilebilir | ✅ (okunuş alışkanlıkları ⏳) |
| **STT (sesli soru)** | Bas-konuş + tanınan metni kullanıcı onayı + terim listesi (sesli soru isteniyor, karar) | Hiç olmaması | Mimariyi değiştirmez, sonradan eklenebilir | ✅ (pilotta uygulandı) |
| **Arayüz** | Pilot: Streamlit + PDF.js tabanlı görüntüleyici (vurgu destekli). Üretim: pilottan sonra karar (özel web arayüzü olası) | NiceGUI | Pilotta en hızlı yol, vurgulama denemede çalıştı | ✅ pilot / ⏳ üretim |
| **Orkestrasyon** | Çatısız, modüler Python + denetim izi | LlamaIndex parçaları, Haystack | Doğrusal hat, projeye özel doğrulama adımları, şeffaflık | ✅ |
| **Değerlendirme** | Kendi ölçüm betiği (değer doğruluğu, kaynak doğruluğu, doğru reddetme) + RAGAS (Türkçe uyarlamalı) + insan değerlendirmesi | DeepEval, TruLens | En kritik metrikler kural tabanlı ölçülebiliyor | ✅ (test seti ⏳) |
| **Yetkilendirme** | Kurumsal giriş (SSO) + rol → marka, aramadan önce zorunlu filtre, varsayılan kapalı | Marka başına ayrı koleksiyon | Sızıntı riski en düşük, esnek | ⏳ (iş kuralı) |

---

### 4.1 Pilotta öğrenilenler (araç seçimi güncellemesi, 2026-10-13)

| Bileşen | Önceki durum | Pilot sonucu | Güncel durum |
|---------|--------------|--------------|--------------|
| PDF ayrıştırma | 🧪 Docling, diğerleriyle karşılaştırma | Docling (OCR kapalı) 0,8–2,7 sn/sayfa, tablo satırı ve bbox çalıştı. İki yerde yetmedi: Taranmış Strickland'ın %94'ü kaçırıldı (**PyMuPDF metin katmanı yedeği**, 143 sayfa). Arıza tablolarında hücreler kaydı (**PyMuPDF tablo yedeği**, kayma tespitiyle). Marker vb. ile karşılaştırma yapılmadı | ✅ Docling + yedekler + kalite kontrolü. Karşılaştırma 🧪 açık |
| OCR | 🧪 Docling içi OCR | Pilotta kapalı: tüm PDF'lerde metin katmanı var. İki OCR birleştirme denenmedi | 🧪 açık (gerçek taranmış veride) |
| Şekil / çizim anlama | 🧪 VLM açıklaması | **Yapılmadı.** Şekiller atlanıyor, çizimler aranamıyor | 🧪 açık, gerçek sistemde zorunlu (çizim olabileceği kararlaştırıldı) |
| Bölümleme | ✅ | Başlık sınırlı, tablo satırı parçaları, uzun paragraf cümle sınırından bölme (SPI değeri uzun paragrafta sulanıyordu). 2921 parça | ✅ doğrulandı |
| Embedding | 🧪 bge-m3 TR↔EN | CPU'da doğru (ilgili 0,65, ilgisiz 0,36–0,42). **Apple GPU'da (MPS) yanlış sonuç** (sessiz hata) | ✅ bge-m3, **CPU veya CUDA GPU**. MPS kullanılmaz |
| Vektör DB | ✅ Qdrant | Gömülü mod, dense + sparse + RRF çalıştı | ✅ |
| Arama | ✅ Hibrit, 🧪 kelime yöntemi | Son ölçümde doğru sayfa 12/12. Atölye terimleri eşleşmedi: **terim sözlüğü** ile sorgu genişletme eklendi. İçindekiler sayfaları sonuçları kirletti, filtrelendi. Sparse kolun TR sorgudaki katkısı A/B ile ölçülmedi | ✅ Hibrit + sözlük. 🧪 katkı ölçümü açık |
| Sorgu analizi ve netleştirme | (araştırmada "sorgu analizi" tek satırdı) | Belirsiz model/ürün/marka, kaynak uyumsuzluğu ve "neyi sorduğunu söylemeyen" soru, küçük modelde yanlış cevaba gidiyordu. Kurallarla modelden önce sorulunca çözüldü | ✅ Ayrı karar katmanı. 🧪 soru niyeti sınıflandırması |
| Reranker | 🧪 gecikme | CPU'da soru başına 20 aday ≈ 3–7 sn (Mac). Skorlar cevaplı/cevapsız ayırmıyor (18 soruda iç içe) | 🧪 GPU'da, eşik için 50–100 soru |
| LLM | 🧪 3 bulut + 1 küçük + 1 açık | **Sadece lokal denendi.** 7B: yanlış sayı seçme, uydurma, atıf yazmama, Çince/Korece karıştırma. 30B (18 GB): GPU belleği aşıldı. Bulut denenmedi | 🧪 + ⏳ büyük model için donanım/bulut kararı gerekli. Dil kayması seçim ölçütü olmalı |
| Kurum içi LLM | 🧪 ~27–32B, 24 GB GPU | 24 GB birleşik bellekte 30B sığmadı (GPU çalışma belleği ~16–18 GB) | ⏳ Q5 (GPU) ve bütçe |
| TTS | 🧪 Azure test, Chatterbox lokal | Chatterbox Multilingual (CPU) Türkçe kalite iyi (kullanıcı onayı), 4,6 sn ses için 11,6 sn üretim. MPS'te bozuk | ✅ Chatterbox adayı, 🧪 GPU/bulut ile gecikme |
| Sesli metin hazırlığı | ✅ Kural tablosu | Sayı, tolerans, aralık, kesir kuralları çalışıyor ve testli. Kod/model okunuşu belirsiz | ✅ (Q10-a ⏳) |
| STT | ⏳ | faster-whisper (CPU): terim ipucu olmadan model kodları bozuluyor, ipucuyla doğru. Gerçek seste kodlar kelimeyle yazıldı, dönüştürücü eklendi. small 4 sn, turbo 14 sn | ✅ faster-whisper + ipucu + onay. 🧪 gerçek seslerle ölçüm |
| Arayüz | ✅ pilot Streamlit | Netleştirme düğmeleri, vurgulu sayfa, mikrofon, ses çalıştı | ✅ pilot, ⏳ üretim (özel web) |
| Orkestrasyon | ✅ Çatısız | Modüler Python ~2.000 satır, 204 birim test | ✅ |
| Değerlendirme | ✅ Kendi betik | 18 soru, otomatik yargıç. En değerli hatalar kullanıcı denemelerinden çıktı. Uzman puanı ve 50–100 soruluk set yok | ✅ betik, ⏳ test seti (kullanıcı sorularıyla) |
| Yetkilendirme | ⏳ | Kararlar alındı (marka bazlı, e-posta/kod). Uygulanmadı | ⏳ uygulama |

---

### 4.2 Ekran tasarımı (özet)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ [Marka ▾] [Doküman türü ▾]      Soru: S-7300A'da üst iplik gergin değil...  🎤 Sor │
├────────────────────────────────────┬──────────────────────────────────────────┤
│ CEVAP                 ✔ Doğrulandı │ KAYNAK [1] Brother S-7300A   s.90 (PDF s.101)│
│                                    │ ┌──────────────────────────────────────┐ │
│ Üst iplik gerginliği zayıf veya    │ │ █ Upper thread is not tight        █ │ │
│ alt iplik gerginliği fazla         │ │ █ Is the upper thread tension...   █ │ │
│ olabilir [1] ...                   │ └──────────────────────────────────────┘ │
│ Orijinal alıntı: "Is the upper..." │ ◀ ▶  ➖ ➕   [Dokümanın tamamını aç]      │
│ 🔊 ▶ Oynat  ↺ Tekrar  🐢 Yavaş      │                                          │
└────────────────────────────────────┴──────────────────────────────────────────┘
```

- Cevap ve kaynak sayfa **yan yana**: Değer, kaynağında hemen doğrulanabilir.
- **Doğrulama rozeti:** ✔ doğrulandı · ⚠ kısmen (ör. tolerans eksik) · ✖ bulunamadı.
- **Kritik değerler büyük puntoyla**, orijinal (İngilizce) alıntı her zaman görünür.
- **Basılı ve PDF sayfa numarası birlikte** gösterilir (basılı kılavuzla karşılaştırma için).
- Ses **butonla** başlar (çok kullanıcılı atölye ortamı). Büyük dokunma alanları (eldivenle kullanım).
- Cevap, doğrulama tamamlandıktan sonra gösterilir. Beklerken adım adım durum mesajları.

---

## 5. Doğruluk güvencesi

![Şekil 2: Doğruluk güvencesi katmanları](sekiller/sekil2-dogruluk-katmanlari.svg)

*Şekil 2. Yanlış değer riskine karşı katmanlı önlemler. Hiçbir katman tek başına yeterli değildir; her katman bir öncekinin kaçırdığını yakalamak üzere tasarlanmıştır.*

**Öne çıkan noktalar:**

- **Eşik test setiyle kalibre edilir.** Şüphede "bulunamadı" tarafı tercih edilir: Yanlış cevap, cevapsızlıktan daha maliyetlidir.
- **Sayı kontrolü iki yönlüdür.** Cevaptaki her değerin kaynakta bulunması yetmez. Kaynaktaki sayı-tolerans ifadesinin cevapta **tam haliyle** bulunması da kontrol edilir. Örnek: Kaynak "11 (± 1)", cevap "11" ise tolerans düşmüştür ve basit kontrol bunu yakalamaz.
- **Dil geçişi riski:** İngilizce "shall not exceed 12" ifadesinin Türkçede "12 olmalı" diye aktarılması anlamı değiştirir. Bu nedenle orijinal alıntı her zaman ekranda gösterilir, çeviri kuralları talimatta tanımlanmıştır.
- **Birim dönüşümü modele bırakılmaz.** Gerekirse kod yapar ve "yaklaşık" olarak işaretler.
- **Sesli okuma da aynı güvenceye tabidir.** Sesli metindeki sayılar doğrulanır, okunuşları kural tablosuyla üretilir. Uzun parça numaraları okunmaz, ekrana yönlendirilir.

### 5.1 Değerlendirme yöntemi

| Unsur | Öneri |
|-------|-------|
| **Test seti** | 50–100 soru. Türler: değer, prosedür, arıza, **cevapsız**, **tuzak** (benzer ama yanlış doküman, ör. S-7300A / S-7300B), Türkçe soru-İngilizce kaynak, görsel, alan dışı, **yetki** |
| **Ana metrikler** | Doğru sayfa ilk 5'te (Recall@5), **değer doğruluğu**, kaynak doğruluğu, sadakat (faithfulness), **doğru reddetme**, gereksiz reddetme, gecikme, maliyet |
| **Taslak hedefler** | Recall@5 ≥ %90 · değer doğruluğu ≥ %98 · doğru reddetme ≥ %90 · tuzak ve yetki testlerinde %100. Kesin hedefler paydaşlarla belirlenecektir |
| **İnsan değerlendirmesi** | Kalite uzmanı, örnek cevapları "bu cevapla üretim yapılır mı?" sorusuyla puanlar |

> "Yanlış değer" ile "cevap yok" ayrı ölçülür. Tek bir "doğruluk yüzdesi" bu iki farklı hatayı gizler.

---

## 6. Veri güvenliği ve dağıtım senaryoları

### 6.1 Hangi veri, hangi kural

| Veri | Hassasiyet | Tabi olduğu kural | Karar mercii |
|------|-----------|-------------------|--------------|
| Müşteri manuelleri ve türevleri (parçalar, vektörler, sayfa görselleri, cevaplar) | Yüksek (ticari sır) | **Müşteri sözleşmesi / NDA** (müşteriye göre değişebilir) | Hukuk birimi, gerekirse müşteri |
| Kullanıcı soruları, kimlikleri, denetim izi, ses kayıtları | Orta (kişisel veri) | **KVKK** | KVKK sorumlusu |

**Tasarım ilkesi:** Bulut servislere kişisel veri gönderilmez (isteklere kullanıcı kimliği eklenmez, ses kurum içinde yazıya çevrilir veya kaydedilmez). Bu, KVKK kapsamındaki yurt dışı aktarım yükümlülüklerinden büyük ölçüde kaçınmayı sağlar (hukuk birimince teyit edilmelidir).

### 6.2 Üç dağıtım senaryosu

![Şekil 3: Dağıtım senaryoları](sekiller/sekil3-dagitim-senaryolari.svg)

*Şekil 3. Bileşenlerin senaryolara göre çalıştığı yer. Önerilen senaryo (B) kesikli çerçeveyle işaretlidir.*

**Temel gözlem:** Bulut kullanımının veri güvenliği etkisi, hangi adımda kullanıldığına göre çok farklıdır. Doküman işleme hattında (OCR, şekil açıklaması, embedding) bulut kullanmak **dokümanın tamamını** dışarı gönderir. Sorgu hattında bulut LLM kullanmak her soruda yalnızca **3–5 parça** gönderir. Kurum içinde çalıştırılması en kolay bileşenler, en çok veri gönderen bileşenlerdir. Hibrit senaryo (B) bu durumdan yararlanır.

- **Şu an (test aşaması):** Açık erişimli (public) test dokümanları kullanıldığı için Senaryo A serbestçe kullanılabilir.
- **Gerçek veriye geçiş:** Senaryo B önerilir. Bulut tarafı için hedeflenen güvenceler: kurumsal sözleşme, veri saklamama (zero data retention), eğitimde kullanmama, bölge seçimi (ör. AB), insan incelemesinin kapatılması.
- **Bulut kesinlikle kullanılamazsa:** Senaryo C. Cevap kalitesi kurum içi modelin pilot sonuçlarına bağlıdır, GPU yatırımı gerekir.
- Kurumun mevcut bir bulut sözleşmesi varsa (Azure, AWS, Google Cloud), modellerin bu platform üzerinden kullanılması hukuki süreci kısaltabilir.

### 6.3 Erişim yetkilendirmesi

- Kullanıcının izinli markaları kurumsal kimlik sisteminden alınır ve **her aramada, sunucu tarafında, aramadan önce** filtre olarak uygulanır. Arayüzdeki marka seçimi yalnızca daraltır.
- Aynı kontrol **tüm erişim noktalarında** uygulanır: PDF/sayfa görüntüleme ve indirme, önceki sorular, önbellek, ses dosyaları, loglar.
- Varsayılan kapalıdır: Markası atanmamış doküman kimseye görünmez.
- Olası iş kuralı: Makine kılavuzları ve genel kaynaklar herkese açık, marka şartnameleri ilgili ekibe özel (paydaşlarca teyit edilecek).

---

## 7. Maliyet ve donanım (yaklaşık)

**Varsayım:** Günde ~200 soru (ayda ~6.000). Fiyatlar 2026-10-09 tarihli resmi fiyat sayfalarından, liste fiyatıdır ve değişebilir.

| Kalem | Aylık yaklaşık | Not |
|-------|----------------|-----|
| Bulut LLM, orta seviye model | ~85–95 $ | Üst seviye ~170 $, küçük modeller ~5–30 $ |
| Bulut TTS | ~36–240 $ | Sesli metnin kısa tutulmasıyla düşer |
| Embedding, vektör DB, reranker | 0 $ (kurum içi) | Donanım ve bakım hariç |

| Senaryo | Donanım |
|---------|---------|
| A / B | Embedding ve reranker için orta seviye bir sunucu (GPU önerilir, şart değil) |
| C | Ek olarak LLM için 24 GB+ bellekli GPU, ayrıca sesli okuma ve şekil açıklaması için GPU kapasitesi |

---

## 8. Riskler

| # | Risk | Etki | Önlem | Durum |
|---|------|------|-------|-------|
| **R4** | **Yanlış veya uydurulmuş değer** | 🔴 Yanlış üretim, müşteri kaybı | Altı katmanlı doğruluk güvencesi (Bölüm 5), iki yönlü sayı-tolerans kontrolü, kaynak sayfanın gösterilmesi | En yüksek öncelik |
| R1 | Tablo ve çizim ağırlıklı sayfalarda metin tabanlı arama zayıf kalabilir | Eksik/yanlış cevap | Şekil açıklaması (VLM), tablo satırı düzeyinde parçalama, gerekirse görsel tabanlı arama | Pilotta ölçülecek |
| R2 | Türkçe sesli okumada teknik terim, sayı ve birimlerin yanlış okunması | Yanlış değer duyulması | Ayrı kısa sesli metin, kural tabanlı normalizasyon, uzun kodların okunmaması | Kural tablosu taslak |
| R3 | Aynı konunun farklı doküman versiyonlarında çelişen bilgi | Yanlış cevap | Versiyon metadata'sı, çelişkinin cevapta bildirilmesi | Gerçek veride versiyon düzeni sorulacak |
| R5 | Cevabın akarak gösterilmesi/seslendirilmesi, doğrulamadan önce değer iletebilir | Yanlış değer | Doğrulamadan sonra gösterim ve seslendirme | Tasarımda çözüldü |
| R6 | Türkçe, ticari lisanslı ve kaliteli kurum içi TTS seçeneği çok az | Bulut kullanılamazsa sesli okuma kalitesi | Chatterbox Multilingual denenecek, Azure kurum içi seçeneği araştırılacak | Pilotta ölçülecek |
| R7 | OCR'ın bir satırı sessizce kaybetmesi (denemede görüldü) | Bilgi aranamaz hale gelir | Bozuk OCR uyarısı, iki OCR kaynağının birleştirilmesi, kullanıcıya her zaman orijinal sayfa görüntüsü | Pilot: PDF metin katmanı yedeği kısmen çözdü, OCR birleştirme açık |
| R8 | Yetki filtresinin bir erişim noktasında unutulması | Gizli bilginin yetkisiz kişiye gösterilmesi | Merkezi zorunlu filtre, tüm erişim noktalarının kontrolü, test setinde yetki testleri | Tasarımda tanımlandı |
| R9 | Sesli soruda model kodunun yanlış tanınması (ör. S-7300A → S-7300B) | Yanlış makinenin kılavuzundan cevap | Tanınan metnin kullanıcı onayı, terim listesi | Pilotta uygulandı (2026-10-13): İpucusuz Whisper model kodlarını bozuyor, kayıttan üretilen terim ipucuyla 5/5 doğru (sentetik ses). Onay ekranında "sorudan okunan" doküman gösteriliyor. Gerçek seslerle ölçülmeli |
| R10 | Test setinin gerçek dokümanları temsil etmemesi | Pilot sonuçlarının gerçek veriye taşınmaması | Gerçek veriye geçişte test setinin yeniden kurulması ve yeniden ölçüm | Planlandı |
| **R11** | **Donanım sınırı:** 24 GB'lık makine yeterli büyüklükte modeli taşıyamıyor (30B GPU belleğini aştı, ekran bozulması yaşandı) | 7B ile kalite yetersiz, büyük model için donanım yatırımı veya bulut gerekli | GPU sunucu veya bulut LLM, bileşenlerin GPU belleğini paylaşımının hesaplanması | Pilotta görüldü, Q5 ve bütçe cevabı bekleniyor |
| **R12** | **Sessiz hata:** Apple GPU (MPS) üzerinde embedding ve TTS hata vermeden yanlış sonuç üretiyor | Anlamsız sıralama, bozuk ses fark edilmeden kullanılabilir | Her ortamda duman testi (benzerlik ve ses doğrulaması), MPS'in kapatılması | Pilotta görüldü, CPU'ya sabitlendi |
| **R13** | **Model atıf yazmıyor:** hiçbir cevap tam "doğrulandı" almıyor, kullanıcı hep "kısmen" görüyor | Doğrulama rozetinin değeri düşer | Daha güçlü model, doğrulama modları (atıfsız ama alıntı ve sayı doğru), prompt iyileştirme | Pilotta görüldü, açık |
| **R14** | **Belirsiz soruda (ürün/marka belirtilmemiş) yanlış doküman getiriliyor** ve model uydurma alıntı veriyor | Yanlış kaynaktan cevap | Belirsizlikte netleştirme sorusu, ürün başına ayrı cevap | Pilotta görüldü (Q07). **Pilotta çözüldü (2026-10-13):** model, ürün ve müşteri markası belirsizliğinde seçim; seçilen kaynak türüne göre varlık uyumu (eşleşmeli / bağlam); soru neyi sorduğunu söylemiyorsa konu seçimi. Açık: soru niyeti (makine ayarı mı, ürün gereksinimi mi) kuralla bilinmiyor |
| **R15** | **Sesli metinde tolerans düşüyor:** ekranda "11 (± 1)", seste "on bir dikiş" | Usta toleransı bilmeden değeri duyar | Sesli metnin ayrıca iki yönlü sayı-tolerans kontrolünden geçmesi | **Pilotta düzeltildi (2026-10-13):** ayrı kontrol, düşerse ses doğrulanmış cevaptan üretilir |
| **R16** | **Atölye terimleri kılavuz terimleriyle eşleşmiyor**, küçük model kendinden emin yanlış çeviriyor ("çağanoz = flywheel", "dizlik = bobbin") | Yanlış sayfa, yanlış değer | Uzman onaylı terim sözlüğü ile sorgu genişletme; LLM sadece aday önerir | Pilotta ölçüldü: bge-m3 1/5, qwen2.5:7b 0/5. **Taslak sözlük (29 terim) eklendi**, uzman onayı bekliyor |
| **R17** | **Model dil kayması:** küçük model cevaba Çince/Korece karıştırıyor | Okunamaz veya yanlış cevap | Doğrulamada yabancı alfabe kontrolü; model seçiminde ölçüt | Pilotta görüldü (2026-10-13), yakalanıyor ama önlenemiyor |

---

## 9. Bekleyen kararlar ve açık sorular

Ayrıntılı liste (kime sorulacağı ve cevap alanlarıyla): [calisma-notlari/notlar/sorulacaklar.md](calisma-notlari/notlar/sorulacaklar.md). **Cevaplananlar** (2026-10-10, [cevaplar.md](calisma-notlari/cevaplar.md)) listeden çıkarıldı.

| Öncelik | Soru | Muhatap | Etkilediği karar |
|---------|------|---------|------------------|
| 🔴 | Müşteri sözleşmeleri bulutta işlemeyi yasaklıyor mu? (müşteriden izin istenmeyeceği kararlaştırıldı) | Hukuk | Dağıtım senaryosu (A/B/C), model seçimi |
| 🔴 | Kurum içinde veya sunucuda GPU var mı, bütçe nedir? (pilot: 7B yetersiz, 30B 24 GB'a sığmadı) | BT, yönetim | Senaryo C, model boyutu |
| 🔴 | Yanlış değer için kabul edilebilir oran | Kalite yönetimi | Eşik ayarı, pilot başarı kriteri |
| 🟡 | Bağlantı kesilirse sistem hiç çalışmasın mı, yedek model mi? | BT, kullanıcılar | Yedek model, çevrimdışı davranış |
| 🟡 | Gerçek dokümanların taranmış oranı, görsel türleri, klasör düzeni, versiyonlar | Doküman sahipleri | Doküman işleme hattı, VLM kapsamı |
| 🟡 | Kullanım cihazı ve ortamı (PC, tablet, kiosk) | Kullanıcılar | Arayüz |
| 🟡 | Genel bilgi verilebilir mi, kritik değerde kullanıcı onayı, test setini kontrol edecek uzman | Kalite yönetimi | Prompt kuralı, arayüz onayı, değerlendirme |
| ⚪ | Kodların atölyede okunuşu (301, S-7300A, E-07), sesli cevap uzunluğu | Kullanıcılar | Sesli okuma kuralları |

**Karara bağlananlar:** sözleşme sessizse izinsiz geliştirme · bitişte veri silme · aydınlatma metni ve rol bazlı log erişimi · en fazla ±1 sayfa görünür · marka bazlı yetki · ses kaydı saklanmaz · ağ kesilebilir · e-posta/kod ile giriş · harici hosting · soru TR, manual EN (çift yönlü) · dijital ve taranmış PDF, çizim olabilir · test setini AI hazırlar · sesli soru istenir · Türkçe terim karşılığı · hoparlör · "soru sor" tuşu · sesli soruda marka sorulur · bekleme süresi 5 sn.

---

## 10. Pilot: sonuçlar ve sonraki adımlar

**Ayrıntı:** [PILOT-RAPORU.md](PILOT-RAPORU.md) (ölçümler, sorunlar ve çözümleri, açık kalanlar) · Mimari: [MIMARI.md](MIMARI.md) · Plan: [UYGULAMA-PLANI.md](UYGULAMA-PLANI.md)

**Planlanan kapsam:** Tek marka, 3–5 manuel, uçtan uca prototip.
**Yapılan:** 7 doküman (611 sayfa, 5 kurum), tamamen lokal, iki makine (Mac M4 Pro, GPU'suz Windows), yazılı ve sesli soru.

### 10.1 Başarı kriterleri: hedef ve sonuç

| Ölçüt | Taslak hedef | Pilot sonucu (18 soru) | Not |
|-------|--------------|------------------------|-----|
| Doğru sayfa ilk 5'te | ≥ %90 | **12/12** | Örneklem küçük |
| Değer doğruluğu | ≥ %98 | **6/9** | Model doğru parçadan yanlış sayı seçti (Q03, Q13) |
| Doğru reddetme | ≥ %90 | **2/4** | Bir kusur düzeltildi (yeniden ölçülmedi), bir sorunun beklentisi belirsiz |
| Belirsiz soruda netleştirme | – | **2/2** | Model çalışmadan |
| Tuzak (S-7300A/B, ceket/pantolon) | %100 | **2/2** | |
| Yanlış değerin "✔ Doğrulandı" ile geçmesi | 0 | **0** | Ama yanlış sayı "⚠ Kısmen" ile geçti |
| Yanıt süresi | ≤ 5 sn | Mac 14,5 sn · GPU'suz ~3 dk | GPU sunucu veya bulut şart |
| Eşik ile "bulunamadı" | Ayrışma | **Ayrışmıyor** | Skorlar iç içe, 50–100 soru gerekli |
| Yetki testleri | %100 | Yapılmadı | |

### 10.2 Araştırma önerilerine etkisi

| Araştırma önerisi | Pilottan sonra |
|-------------------|----------------|
| Mimari (iki hat, kaynak gösterme, doğrulama) | **Doğrulandı.** Değişmesi gerekmiyor |
| Sorgu analizi (tek adım) | **Genişledi:** ayrı bir karar katmanı gerekiyor (varlık, kaynak uyumu, netleştirme, soru niyeti) |
| Altı katmanlı doğruluk güvencesi | **Çalışıyor,** iki kör noktası var: ilgililik ve sayı seçimi. Cevap-alıntı hizalaması önerildi |
| Kurum içi küçük model | **Yetersiz.** Güçlü model şart (bulut ya da GPU'da büyük model) |
| Terim listesi (yalnız STT için düşünülmüştü) | **Arama için de şart:** uzman onaylı atölye terim sözlüğü |
| Docling | **Yeterli, ama yedek ve kalite kontrolüyle** |
| STT (isteğe bağlı) | **Uygulandı.** Terim ipucu ve onay adımı zorunlu |

Hedef mimari: [MIMARI.md, Bölüm B](MIMARI.md). Uygulama aşamaları ve karar kapıları: [UYGULAMA-PLANI.md](UYGULAMA-PLANI.md).

---

## Ek A: Ayrıntılı araştırma notları

| Konu | Not dosyası |
|------|-------------|
| RAG temelleri (bölümleme, embedding, vektör DB, hibrit arama, rerank, metadata) | [calisma-notlari/notlar/rag-temelleri.md](calisma-notlari/notlar/rag-temelleri.md) |
| PDF işleme (ayrıştırma araçları, OCR, şekiller, metadata şeması) | [calisma-notlari/notlar/pdf-isleme.md](calisma-notlari/notlar/pdf-isleme.md) |
| Kaynak gösterme ve sayfa vurgulama, görsel tabanlı arama | [calisma-notlari/notlar/kaynak-gosterme.md](calisma-notlari/notlar/kaynak-gosterme.md) |
| Çekirdek deneme raporu (27/27 test) | [calisma-notlari/faz1-test/faz1_output/report.md](calisma-notlari/faz1-test/faz1_output/report.md) |
| TTS (sesli okuma), metin normalizasyonu | [calisma-notlari/notlar/tts.md](calisma-notlari/notlar/tts.md) |
| Arayüz, orkestrasyon, STT | [calisma-notlari/notlar/arayuz-orkestrasyon.md](calisma-notlari/notlar/arayuz-orkestrasyon.md) |
| LLM seçimi, doğruluk güvencesi, değerlendirme | [calisma-notlari/notlar/llm-degerlendirme.md](calisma-notlari/notlar/llm-degerlendirme.md) |
| Taslak sistem talimatı ve çıktı şeması | [calisma-notlari/notlar/prompt-taslak.md](calisma-notlari/notlar/prompt-taslak.md) |
| Veri güvenliği ve erişim | [calisma-notlari/notlar/guvenlik.md](calisma-notlari/notlar/guvenlik.md) |
| Test doküman envanteri | [calisma-notlari/notlar/manual-envanteri.md](calisma-notlari/notlar/manual-envanteri.md) |
| **Görev özetleri** (her görev için karar tablosu ve önerilen sistem) | [calisma-notlari/notlar/gorev-ozetleri.md](calisma-notlari/notlar/gorev-ozetleri.md) |
| Hazırlık (cevaplar, doküman listesi, test soruları) | [calisma-notlari/notlar/00-hazirlik.md](calisma-notlari/notlar/00-hazirlik.md) |
| Bekleyen sorular | [calisma-notlari/notlar/sorulacaklar.md](calisma-notlari/notlar/sorulacaklar.md) |
| Pilot raporu (kurulum, ölçüm, problemler, öneriler) | [PILOT-RAPORU.md](PILOT-RAPORU.md) |
| Araştırma planı ve günlük | [req.md](calisma-notlari/req.md) |

## Ek B: Terimler

| Terim | Açıklama |
|-------|----------|
| **RAG** (Retrieval-Augmented Generation) | Cevabı üretmeden önce ilgili bilgiyi dokümanlardan bulup modele veren yöntem |
| **Chunk** (parça) | Dokümanın arama için bölündüğü bölüm |
| **Embedding** | Metnin anlamını temsil eden sayı dizisi (vektör). Anlamca yakın metinlerin vektörleri birbirine yakındır |
| **Hibrit arama** | Anlam araması ile kelime aramasının birlikte kullanılması |
| **Rerank** | İlk aramada bulunan adayların daha isabetli bir modelle yeniden sıralanması |
| **bbox** | Bir metin bloğunun sayfa üzerindeki konumu (dikdörtgen koordinatları). Vurgulama için kullanılır |
| **OCR** | Taranmış sayfa görüntüsündeki yazının metne çevrilmesi |
| **VLM** | Görselleri okuyabilen dil modeli |
| **LLM** | Büyük dil modeli. Bu sistemde bilgi kaynağı değil, verilen kaynakları okuyup cevap yazan bileşen |
| **Halüsinasyon** | Modelin kaynakta olmayan bilgiyi üretmesi |
| **TTS / STT** | Metinden sese / sesten metne çevirme |
| **SPI** | Stitches per inch: inç başına dikiş sayısı |
| **ZDR** (zero data retention) | Bulut sağlayıcının işlenen veriyi saklamaması taahhüdü |
| **SSO** | Kurumsal hesapla tek giriş |
| **Recall@5** | Doğru kaynağın ilk 5 sonuç içinde bulunma oranı |
