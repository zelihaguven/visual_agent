# Araştırma Sentezi (Faz 5)

> **Kaynak not:** `sentez.md` ("Visual Agent: Araştırma Sentezi", 2026-10-09, Aşama: Araştırma — Faz 5: Sentez). [15-plan.md](15-plan.md) Faz 5'in çıktısı; sunulabilir özet doküman.
> **Kapsam:** Araştırma bulguları, önerilen mimari, araç seçimleri, riskler ve bekleyen kararlar. Kaynaktaki üç şekil (SVG/PNG, `sentez-sekiller/`) bu sette yok; yerlerine notlardaki eşdeğer mermaid diyagramlarına bağlantı verildi.
> **Ayrıntılı notlar (kaynaktaki Ek A):** RAG → [07](07-rag-temelleri.md) · PDF işleme → [02](02-pdf-isleme.md) · Kaynak gösterme → [03](03-kaynak-gosterme.md) · Faz 1 deneme raporu (27/27) → `faz1_output/report.md` (bu sette yok) · TTS → [08](08-tts.md) · Arayüz/orkestrasyon/STT → [05](05-arayuz-ve-orkestrasyon.md) · LLM/doğruluk/değerlendirme → [04](04-llm-secimi-ve-degerlendirme.md) · Prompt ve şema → [09](09-prompt-taslagi.md) · Güvenlik → [06](06-veri-guvenligi-ve-erisim.md) · Test doküman envanteri → [01](01-manual-envanteri.md) · Bekleyen sorular → [10](10-sorulacaklar.md) · Araştırma planı ve günlük → [15-plan.md](15-plan.md)
> **Beslediği çıktılar:** Tüm beklenen çıktılar (özet düzeyinde): mimari · araç seçimi (durum sütunlu) · riskler R1–R10 · bekleyen kararlar · pilot önerisi ve uygulama sırası · taslak başarı hedefleri

---

## 1. Özet

Proje, atölye ve kalite ekiplerinin marka şartnameleri, makine kılavuzları ve dikim kaynakları hakkında soru sorabildiği bir sistem tasarlamayı amaçlamaktadır. Sistem, ilgili bilgiyi manuellerden bulur, **kaynağa dayalı** bir cevap üretir, bilginin geçtiği **manuel sayfasını vurgulu olarak** gösterir ve cevabı **sesli** okur.

Araştırma aşamasının ana sonuçları:

1. **Mimari netleşti.** Sistem iki hattan oluşur: dokümanların bir kez işlenip indekslendiği *doküman işleme hattı* ve her soruda çalışan *sorgu hattı* (Şekil 1). Çekirdek kısım (doküman ayrıştırma, sayfa ve konum bilgisinin korunması, sayfa üzerinde vurgulama) bir deneme ile doğrulandı: Üç farklı doküman türünde 27/27 test başarılı.
2. **En kritik risk yanlış değerdir.** Uydurulmuş veya yanlış aktarılmış bir değer (ör. dikiş sıklığı, tolerans) yanlış üretime yol açar. Bu risk için **altı katmanlı bir doğruluk güvencesi** tasarlandı (Şekil 2). İlke: Sistem emin değilse cevap vermez, cevap verdiğinde her değer kaynağında gösterilir.
3. **Veri güvenliği için hibrit yapı önerilmektedir.** Dokümanların tamamını işleyen adımlar kurum içinde, yalnızca cevap üretimi (ve sesli okuma) kurumsal sözleşmeli bulut serviste çalışır. Bu yapıda soru başına yalnızca 3–5 metin parçası kurum dışına çıkar (Şekil 3). Kesin karar, müşteri sözleşmelerinin incelenmesine bağlıdır.
4. **Model ve servis seçimi pilotta ölçülerek yapılacaktır.** Genel sıralamalar bu görevi (verilen metne sadakat, Türkçe-İngilizce geçiş, bilinmeyeni "bulunamadı" olarak bildirme) ölçmemektedir. Adaylar aynı test setiyle karşılaştırılacaktır.
5. **Maliyet karar verdirici değildir.** Tahmini kullanımda (günde ~200 soru) bulut LLM ve sesli okuma maliyeti aylık birkaç yüz doları aşmamaktadır. Kararları doğruluk ve gizlilik belirleyecektir.

**İlerlemek için gereken kararlar** (ayrıntı: §9):
- Müşteri manuelleri bulut servislerde işlenebilir mi? (Q1, müşteri sözleşmeleri)
- Kurum içinde GPU kullanılabilir mi? Atölyede internet erişimi var mı?
- Test soru seti (cevabı ve sayfası bilinen gerçekçi sorular) kim tarafından hazırlanacak?
- Yanlış değer için kabul edilebilir oran nedir?

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

> **Şekil 1** (önerilen mimari; yeşil: kurum içi bileşenler, turuncu: hibrit senaryoda kurumsal sözleşmeli bulut servis; bulut kullanılamazsa kurum içi alternatifleri var, §6) kaynakta SVG olarak (`sentez-sekiller/sekil1-mimari.svg`) ve **bu sette yok**. Notlardan derlenmiş mermaid karşılığı: [12-uctan-uca-mimari.md](12-uctan-uca-mimari.md) §2.

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
| **Hazır orkestrasyon çatısı yok** | Hat her soruda aynı adımları izler. Kritik adımlar projeye özeldir. Modüler Python kodu tercih edilmiştir (bkz. §4) |

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
| **STT (sesli soru)** | İsteğe bağlı. Bas-konuş + tanınan metni kullanıcı onayı + terim listesi | Hiç olmaması | Mimariyi değiştirmez, sonradan eklenebilir | ⏳ (Q4) |
| **Arayüz** | Pilot: Streamlit + PDF.js tabanlı görüntüleyici (vurgu destekli). Üretim: pilottan sonra karar (özel web arayüzü olası) | NiceGUI | Pilotta en hızlı yol, vurgulama denemede çalıştı | ✅ pilot / ⏳ üretim |
| **Orkestrasyon** | Çatısız, modüler Python + denetim izi | LlamaIndex parçaları, Haystack | Doğrusal hat, projeye özel doğrulama adımları, şeffaflık | ✅ |
| **Değerlendirme** | Kendi ölçüm betiği (değer doğruluğu, kaynak doğruluğu, doğru reddetme) + RAGAS (Türkçe uyarlamalı) + insan değerlendirmesi | DeepEval, TruLens | En kritik metrikler kural tabanlı ölçülebiliyor | ✅ (test seti ⏳) |
| **Yetkilendirme** | Kurumsal giriş (SSO) + rol → marka, aramadan önce zorunlu filtre, varsayılan kapalı | Marka başına ayrı koleksiyon | Sızıntı riski en düşük, esnek | ⏳ (iş kuralı) |

---

### 4.1 Ekran tasarımı (özet)

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

> **Şekil 2** (yanlış değer riskine karşı katmanlı önlemler; hiçbir katman tek başına yeterli değil, her katman bir öncekinin kaçırdığını yakalamak üzere tasarlandı) kaynakta SVG ve **bu sette yok**. Mermaid karşılığı: [04-llm-secimi-ve-degerlendirme.md](04-llm-secimi-ve-degerlendirme.md) §5.

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

> **Şekil 3** (bileşenlerin senaryolara göre çalıştığı yer; önerilen B kesikli çerçeveyle) kaynakta SVG ve **bu sette yok**. Mermaid karşılığı: [06-veri-guvenligi-ve-erisim.md](06-veri-guvenligi-ve-erisim.md) §5.2, [12-uctan-uca-mimari.md](12-uctan-uca-mimari.md) §4.

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
| **R4** | **Yanlış veya uydurulmuş değer** | 🔴 Yanlış üretim, müşteri kaybı | Altı katmanlı doğruluk güvencesi (§5), iki yönlü sayı-tolerans kontrolü, kaynak sayfanın gösterilmesi | En yüksek öncelik |
| R1 | Tablo ve çizim ağırlıklı sayfalarda metin tabanlı arama zayıf kalabilir | Eksik/yanlış cevap | Şekil açıklaması (VLM), tablo satırı düzeyinde parçalama, gerekirse görsel tabanlı arama | Pilotta ölçülecek |
| R2 | Türkçe sesli okumada teknik terim, sayı ve birimlerin yanlış okunması | Yanlış değer duyulması | Ayrı kısa sesli metin, kural tabanlı normalizasyon, uzun kodların okunmaması | Kural tablosu taslak |
| R3 | Aynı konunun farklı doküman versiyonlarında çelişen bilgi | Yanlış cevap | Versiyon metadata'sı, çelişkinin cevapta bildirilmesi | Gerçek veride versiyon düzeni sorulacak |
| R5 | Cevabın akarak gösterilmesi/seslendirilmesi, doğrulamadan önce değer iletebilir | Yanlış değer | Doğrulamadan sonra gösterim ve seslendirme | Tasarımda çözüldü |
| R6 | Türkçe, ticari lisanslı ve kaliteli kurum içi TTS seçeneği çok az | Bulut kullanılamazsa sesli okuma kalitesi | Chatterbox Multilingual denenecek, Azure kurum içi seçeneği araştırılacak | Pilotta ölçülecek |
| R7 | OCR'ın bir satırı sessizce kaybetmesi (denemede görüldü) | Bilgi aranamaz hale gelir | Bozuk OCR uyarısı, iki OCR kaynağının birleştirilmesi, kullanıcıya her zaman orijinal sayfa görüntüsü | Uygulama aşamasına devredildi |
| R8 | Yetki filtresinin bir erişim noktasında unutulması | Gizli bilginin yetkisiz kişiye gösterilmesi | Merkezi zorunlu filtre, tüm erişim noktalarının kontrolü, test setinde yetki testleri | Tasarımda tanımlandı |
| R9 | Sesli soruda model kodunun yanlış tanınması (ör. S-7300A → S-7300B) | Yanlış makinenin kılavuzundan cevap | Tanınan metnin kullanıcı onayı, terim listesi | STT kararına bağlı |
| R10 | Test setinin gerçek dokümanları temsil etmemesi | Pilot sonuçlarının gerçek veriye taşınmaması | Gerçek veriye geçişte test setinin yeniden kurulması ve yeniden ölçüm | Planlandı |

---

## 9. Bekleyen kararlar ve açık sorular

Ayrıntılı liste (kime sorulacağı ile): [10-sorulacaklar.md](10-sorulacaklar.md); konsolide: [13-acik-sorular-ve-riskler.md](13-acik-sorular-ve-riskler.md)

| Öncelik | Soru | Muhatap | Etkilediği karar |
|---------|------|---------|------------------|
| 🔴 | Müşteri manuelleri bulut servislerde işlenebilir mi? Hangi koşullarla? | Hukuk, müşteri | Dağıtım senaryosu (A/B/C), model seçimi |
| 🔴 | Müşteri sözleşmelerinde üçüncü taraf, coğrafi kısıt, silme ve yapay zekâ maddeleri | Hukuk | Senaryo B'nin uygulanabilirliği |
| 🔴 | Kurum içinde kullanılabilecek GPU var mı? | BT | Senaryo C, kurum içi modeller |
| 🔴 | Atölyede internet erişimi var mı? | BT | Bulut servislerin kullanılabilirliği |
| 🔴 | Test soru setini kim hazırlayacak? | Kalite ekibi | Pilot değerlendirmesi |
| 🔴 | Yanlış değer için kabul edilebilir oran | Kalite yönetimi | Eşik ayarı, pilot başarı kriteri |
| 🟡 | Marka bazlı erişim kuralı | Yönetim | Yetkilendirme modeli |
| 🟡 | Gerçek dokümanların dili, türleri, taranmış oranı, görsel türleri, dosya düzeni | Doküman sahipleri | Doküman işleme hattı |
| 🟡 | Kullanım cihazı ve ortamı (PC, tablet, kiosk) | Kullanıcılar | Arayüz |
| 🟡 | Kabul edilebilir bekleme süresi | Kullanıcılar | Pilot başarı kriteri |
| ⚪ | Sesli soru ihtiyacı, kodların atölyede okunuşu, hoparlör/kulaklık | Kullanıcılar | STT, sesli okuma kuralları |

---

## 10. Pilot önerisi ve sonraki adımlar

**Pilot kapsamı:** Tek marka, 3–5 manuel, uçtan uca prototip: soru → arama → kaynaklı cevap → doğrulama → vurgulu sayfa → sesli okuma.

**Pilotta yapılacak ölçümler** (araştırma aşamasında ertelenenler):

| Konu | Ölçüm |
|------|-------|
| Arama | Türkçe soru-İngilizce manuel eşleşmesi, hibrit aramanın katkısı, kelime araması yöntemi, Türkçe kök bulma, reranker gecikmesi |
| Doküman işleme | Docling ile diğer ayrıştırıcıların karşılaştırılması, OCR birleştirme, tablo satırı temizliği, basılı/PDF sayfa eşleme |
| Görsel anlama | VLM açıklaması ile görsel tabanlı aramanın görsel test sorularında karşılaştırılması |
| LLM | Bulut ve kurum içi adayların aynı test setinde karşılaştırılması, talimat dili, alıntı birebirlik oranı |
| Sesli okuma | Adayların test cümleleriyle karşılaştırılması (kritik değer doğruluğu, atölye gürültüsü), Chatterbox'ın Türkçe kalitesi |
| Arayüz | Vurgunun tarayıcıda gözle doğrulanması, kullanıcı tepkisi, sesli soru ihtiyacı |

**Önerilen uygulama sırası:**
1. Doküman işleme hattı (ayrıştırma, bölümleme, metadata, indeksleme)
2. Arama (hibrit + filtre + rerank) ve test setiyle ölçüm
3. Cevap üretimi, kaynak gösterme ve otomatik doğrulama
4. Sayfa görüntüleyici ve vurgulama
5. Sesli metin hazırlığı ve TTS
6. Arayüzün birleştirilmesi
7. Değerlendirme ve iyileştirme turu
8. Yetkilendirme ve güvenlik
9. Gerçek veriye geçiş (kontrol listesiyle) ve yeniden ölçüm

**Pilot başarı kriterleri** (taslak, paydaşlarla kesinleştirilecek): §5.1'deki hedefler + kabul edilebilir yanıt süresi + kullanıcı değerlendirmesi.

---

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
