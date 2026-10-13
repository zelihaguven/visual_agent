# RAG Temelleri (Adım 1)


> **Başlangıç:** 2026-10-08
> **İlgili plan:** [req.md, Adım 1](../req.md)

Bu doküman üç aşamada oluşur:
1. **Aklımda kalanlar :** RAG'i okuduğum şekliyle kendi cümlelerimle anlatırım.
2. **Soru-Cevap:** Eksik veya belirsiz kalan yerler sorularla netleşir.
3. **Derlenmiş notlar:** Hepsi birleştirilip temiz, sonradan dönüp bakılacak bir referans haline gelir.

---

## 1. İlk okuma sonrası aklımda kalanlar 

> RAG, generative modeller bizi cevaplarken halüsinasyona sebebiyet verebildiği için var. Kaydedilmiş data üzerinden cevapladığı için halüsinasyon yok. Doküman sisteme girdiğinde önce chunking dediğimiz küçük parçalara ayırma süreci oluyor, ardından o data embedding sürecine maruz kalıyor. Bu süreçte numerik vektörlere çevrilip anlamlı bir hale geliyor, sonrasında bu data veri tabanına kaydediliyor. Veri tabanı sonrasında ise bir soru sorulduğunda generative kısım yanıtı bu dosyalar ve datalar üzerinden üretiyor.

**Özetle anlatımdaki akış:**
`Doküman → Chunking → Embedding (vektör) → Veri tabanı → Soru gelir → LLM yanıtı veriden üretir`

---

## 2. Soru-Cevap

### Tur 1

**S1. Halüsinasyon tamamen bitiyor mu?**
"Kaydedilmiş data üzerinden cevapladığı için halüsinasyon yok" dedin. Sistem yanlış chunk'ı getirirse ya da doğru chunk'ta bilgi yoksa LLM ne yapar sence?
> **C:** yine halüsinasyon olur 

**Açıklama:** RAG halüsinasyonu **azaltır ama sıfırlamaz.**
- Yanlış chunk gelirse LLM yanlış bilgiyi emin bir dille anlatır.
- Getirilen chunk'larda bilgi yoksa LLM boşluğu kendi eğitim bilgisiyle doldurup uydurabilir.
- Önlemler: "bilgi yoksa *bulunamadı* de" talimatı, benzerlik skoru düşükse cevap vermeme eşiği, kaynak gösterme zorunluluğu. 

**S2. RAG'in tek sebebi halüsinasyon mu?**
LLM zaten internetteki bilgiyle eğitilmiş. Nike'ın bize özel gönderdiği dikiş manuali hakkında neden kendi başına cevap veremez? Bu, RAG'in var olma sebepleri hakkında sana ne söylüyor?
> **C:** özel bir data var elimizde confidential ya da yeni bir bilgiyse llmde yoktur 

**Açıklama:** RAG'in üç temel sebebi var:
1. **Özel veri:** Nike'ın bize gönderdiği manual internette yok, model onu hiç görmedi.
2. **Güncellik:** Modelin bilgisi eğitim tarihinde donar. Manualin yeni versiyonu çıkınca RAG'de dosyayı değiştirmek yeterli.
3. **İzlenebilirlik:** Cevabın hangi dosyanın hangi sayfasından geldiğini gösterebiliriz. **Bizim projede sayfayı ekranda göstermenin temeli bu.**

Alternatifi olan fine-tuning (modeli veriyle yeniden eğitmek) pahalıdır, güncellemesi zordur ve kaynak gösteremez.

**S3. Soru geldiğinde tam olarak ne oluyor?**
"Soru sorulduğunda LLM yanıtı veriden üretiyor" dedin. Veri tabanında binlerce chunk varsa, LLM'e hangilerinin verileceğine kim, nasıl karar veriyor? Bu sırada kullanıcının sorusuna ne oluyor?
> **C:** sorunun datası da embedding modeliyle vectore çevriliyor 

**Açıklama:** Anlatımda **retrieval (getirme)** adımı eksikti. RAG'in harfleri bu adımları anlatır:
1. **Retrieval:** Kullanıcının sorusu da **aynı embedding modeliyle** vektöre çevrilir. Vector DB, soru vektörüne en yakın k adet chunk'ı (örn. top-5) bulur. Yakınlık genelde *cosine similarity* ile ölçülür.
2. **Augmented:** Bulunan chunk'lar ve soru birlikte LLM'in promptuna konur.
3. **Generation:** LLM sadece bu chunk'lara bakarak cevap üretir.

LLM veri tabanının tamamını görmez, yalnızca kendisine verilen birkaç chunk'ı görür. Getirilen chunk yanlışsa cevap da yanlış olur. Bu yüzden **retrieval kalitesi, sistem kalitesinin en büyük belirleyicisidir.**

**Düzeltilmiş akış:**
```
INDEXLEME (bir kez):  Doküman → Parse → Chunking → Embedding → Vector DB (+ metadata)
SORGU (her soruda):   Soru → Embedding → Vector DB'de benzerlik araması → Top-k chunk
                      → Prompt (soru + chunk'lar) → LLM → Yanıt + kaynak
```

**S4. "Anlamlı hale geliyor" ne demek?**
Embedding'den sonra iki vektörün birbirine "yakın" olması neyi ifade eder? Örnek: "dikiş sıklığı" ile "stitch density" vektörleri yakın mı olur, uzak mı?
> **C:** Yakınsa anlamları da benzerdir.

**Geri bildirim:** ✅ Doğru. Ek olarak:
- "dikiş sıklığı" ile "stitch density"nin yakın çıkması için **çok dilli** bir embedding modeli gerekir. Sadece İngilizce bir modelde Türkçe metin anlamsız vektörlere dönüşür ve bu ikisi uzak çıkar. → Adım 1.3'te model seçiminin kritik noktası.
- Kelimeler farklı olsa da anlam aynıysa vektörler yakındır. Embedding'i klasik kelime aramasından ayıran en önemli özellik bu.

**S5. Chunk boyutu neden önemli?**
Chunk'ları çok küçük (1 cümle) veya çok büyük (10 sayfa) yaparsak ne gibi sorunlar çıkar sence?
> **C:** Karmaşıklık.

**Geri bildirim:** 🟡 Yön doğru, somutlaştıralım:
- **Çok küçük:** Bağlam kaybolur. "Bu değer 8–10 arasında olmalıdır" cümlesi tek başına bir chunk olursa, hangi değerden bahsettiği anlaşılmaz.
- **Çok büyük:** Bir vektör birden fazla konuyu temsil eder, anlam "sulanır" ve aramada isabet düşer. LLM'e gereksiz metin gider (maliyet artar, model dikkatini kaybeder). Hangi sayfadan geldiği belirsizleşir (bizim için kritik).
- **Pratikte:** Genelde 200–800 token arası chunk'lar ve aralarında biraz örtüşme (overlap) kullanılır. Manuallerde başlık/bölüm veya sayfa bazlı bölmek çoğu zaman daha iyi sonuç verir. → Adım 1.2

**S6. Bu veri tabanı normal bir veri tabanı mı?**
Vektörleri neden MySQL gibi klasik bir veri tabanında `WHERE metin LIKE '%dikiş%'` ile aramıyoruz da "vector DB" diye ayrı bir şey kullanıyoruz?
> **C:** Daha anlamlı çıktılar üretebilmek için.

**Geri bildirim:** ✅ Doğru yön. Ayrıntısı:
- `LIKE` sadece birebir kelime eşleşmesi yapar. "stitch density" aramasında "dikiş sıklığı" geçen sayfayı bulamaz, eş anlamlıları yakalayamaz.
- Vector DB, milyonlarca vektör içinde "en yakın komşuyu" çok hızlı bulmak için özel indeksler kullanır (ANN, örn. HNSW).
- **Ama:** Kelime araması tamamen işe yaramaz değil. "ISO 4915" gibi standart numaralarında veya ürün kodlarında birebir eşleşme vektörden daha başarılıdır. İkisini birleştirmeye **hybrid search** denir. → Adım 1.5
- Not: PostgreSQL'e `pgvector` eklentisi kurularak klasik veri tabanı da vector DB olarak kullanılabilir.

---

### Tur 2

**S7. Sayfa sınırı sorunu**
Bir konu manualde 12. sayfanın sonunda başlayıp 13. sayfada bitiyor. Chunk ikisini birden kapsarsa ekranda hangi sayfayı göstermeliyiz? Sen olsan bunu nasıl çözerdin?
> **C:** Bunu sayfa 12 ve 13 diyerek çözerdim. Chunklayacaksak bağlama bakarak bölmeliyiz.

**Geri bildirim:** ✅ İki fikir de doğru ve gerçek sistemlerde kullanılıyor:
- **Sayfa listesi:** Chunk metadata'sında tek `page` yerine `pages: [12, 13]` tutulur. Her sayfa için ayrı bbox saklanırsa ekranda 12. sayfa açılır, vurgu 13. sayfada devam eder ("devamı s.13" gibi).
- **Bağlama göre bölme:** Buna *yapı farkında (structure-aware) chunking* denir. Sabit karakter sayısıyla değil, başlık/bölüm sınırlarından bölünür. Manuallerde başlık yapısı belirgin olduğu için bizim için uygun.

**S8. Yanlış marka sorunu**
Kullanıcı "Nike dikiş standartları" diye sordu, ama vektör olarak en yakın chunk Adidas manualinden geldi (konu aynı, marka farklı). Bunu nasıl önleriz?
> **C:** Marka filtresi doldurulmuşsa o eşleşmeyi de dahil etmeliydi mantıken.

**Geri bildirim:** ✅ Doğru, buna **metadata filtreleme** denir. Her chunk'a `brand: "Nike"` etiketi eklenir, arama yalnızca `brand = "Nike"` olan chunk'lar içinde yapılır. Anlamsal benzerlik ne kadar yüksek olursa olsun Adidas chunk'ı hiç aday olmaz. Açık kalan iki soru:
- **Marka sorudan nasıl çıkarılır?** Seçenekler: bilinen marka listesiyle kelime eşleştirme, LLM ile çıkarım ya da arayüzde marka seçme kutusu (en güvenilir yol).
- **Soruda marka yoksa ne yapılır?** Tüm markalarda aranır ve cevapta hangi markaya ait olduğu belirtilir, ya da kullanıcıya "Hangi marka için?" diye sorulur.

**S9. Vektör mü, kelime mi?**
Kullanıcı "ISO 4915'e göre dikiş tipi nedir?" diye sorarsa, vektör araması mı kelime araması mı doğru sayfayı daha iyi bulur? Neden?
> **C:** Kelime araması.

**Geri bildirim:** ✅ Doğru. Nedeni: embedding modelleri sayıları ve kodları iyi ayırt edemez. "ISO 4915" ile "ISO 4916" vektör olarak neredeyse aynı görünür. Kelime araması (**BM25**) ise birebir eşleşmeyi bulur ve nadir geçen terimlere (kodlar gibi) yüksek puan verir. Sorunun "dikiş tipi" kısmında ise vektör araması daha iyidir. Bu yüzden ikisi birlikte kullanılır: **hybrid search**.

**S10. Sıralama sorunu**
Vector DB en yakın 10 chunk'ı getirdi, ama gerçekten doğru olan chunk 7. sırada. LLM'e kaç chunk verirsin? Hepsini mi, ilk 3'ü mü? Sıralamayı iyileştirmek için ne yapılabilir?
> **C:** Yakınlık ilk baktığımızdaki kriter olup en yakınların en doğrusuna odaklanmalıyız, daha uzak olsa bile fark etmez.

**Geri bildirim:** ✅ Sezgi tam olarak doğru: "en yakın" her zaman "en doğru" değildir. Bunu yapan adımın adı **reranking**. Çalışma şekli iki aşamalıdır:
1. **Hızlı ön eleme:** Vector DB (+ BM25) geniş bir aday listesi getirir (örn. top-20/50). Hızlıdır ama kaba bir sıralamadır.
2. **Hassas yeniden sıralama:** Bir *reranker* (cross-encoder) modeli soruyu ve her chunk'ı **birlikte** okuyup "bu chunk bu soruyu cevaplıyor mu?" puanı verir. Yavaştır ama çok daha isabetlidir.
3. LLM'e yalnızca en iyi **3–5** chunk verilir.

**Neden 10'unun hepsi verilmiyor?** Gereksiz chunk'lar modelin dikkatini dağıtır (uzun bağlamın ortasındaki bilgiyi gözden kaçırma eğilimi: *lost in the middle*), maliyeti ve gecikmeyi artırır ve yanlış sayfaya kaynak gösterme riskini yükseltir.

---

### Tur 3: Benim sorularım

**S11. Halüsinasyonu nasıl önleyeceğiz?**
> **Soru:** Manualde olmayan bir bilgi uydurulursa yanlış dikim yapılır. Bu çok kötü bir durum ve sistemi işe yaramaz hale getirir. Bunu nasıl önleyeceğiz?

**Cevap:** Hiçbir yöntem riski **%100 sıfırlamaz.** Ama tek bir önlem yerine üst üste katmanlar kurarak uydurmayı **hem çok nadir hem de fark edilebilir** hale getirebiliriz. Hedef iki parçalı: (1) sistem emin değilse **cevap vermesin**, (2) cevap verdiğinde kullanıcı **her bilgiyi kaynağında görebilsin.**

**Katman 1: Doğru bilgiyi getirmek (retrieval)**
Uydurmanın en büyük sebebi, LLM'e doğru chunk'ın hiç gelmemesidir. Hybrid search, marka/versiyon filtresi ve reranker bu riski azaltır.

**Katman 2: Emin değilse cevap vermemek (eşik)**
- Reranker skoru belirli bir eşiğin altındaysa LLM **hiç çağrılmaz.** Sistem doğrudan şunu söyler: *"Bu bilgi manuellerde bulunamadı. Lütfen ilgili birimle teyit edin."*
- "Bilmiyorum" demek, yanlış cevap vermekten her zaman iyidir. Sistem bu ilkeyle tasarlanmalı.

**Katman 3: Sıkı prompt kuralları**
- Sadece verilen kaynaklardan cevap ver, kendi bilgini kullanma.
- Her bilgiyi kaynağıyla (dosya + sayfa) belirt.
- Kaynaklarda yoksa "bulunamadı" de, tahmin yürütme.
- Kaynaklar çelişiyorsa çelişkiyi açıkça belirt, birini seçme.
- Düşük *temperature* (yaratıcılığı kısan ayar) kullan.

**Katman 4: Önce alıntı, sonra cevap**
- LLM'den önce manualdeki ilgili cümleyi **kelimesi kelimesine** alıntılaması, sonra cevabı yazması istenir.
- Sayısal değerler (8–10 SPI, 12 mm, toleranslar) **sadece alıntıdan** gelir, LLM bunları kendi cümlesiyle yeniden yazmaz.

**Katman 5: Otomatik doğrulama (cevap kullanıcıya gitmeden önce)**
- **Alıntı kontrolü:** LLM'in alıntıladığı metin gerçekten chunk'ta geçiyor mu? Basit metin karşılaştırmasıyla kontrol edilir. Geçmiyorsa cevap reddedilir.
- **Sayı kontrolü:** Cevaptaki her sayı ve birim kaynak chunk'larda var mı? Yoksa cevap reddedilir veya uyarıyla gösterilir.
- **İkinci kontrol (opsiyonel):** Ayrı bir model, cevabın kaynakla desteklenip desteklenmediğini puanlar (*faithfulness check*).

> Bu katman kritik, çünkü LLM'e güvenmek yerine **kodla doğrulanabilir** kontroller ekliyor.

**Katman 6: Arayüz, yani kullanıcının kendisinin doğrulayabilmesi**
- Manual sayfası **her zaman** ekranda gösterilir ve ilgili kısım vurgulanır. Projenin ana fikri zaten bu, halüsinasyona karşı da en güçlü önlem.
- Kritik değerler LLM'in cümlesi olarak değil, **manualden alıntı** olarak gösterilir.
- Konumlandırma: Asıl kaynak manual sayfasıdır, LLM cevabı ona yol gösteren bir özettir.
- Diller arası senaryoda alıntı orijinal dilde gösterilir, böylece çeviri hatası da fark edilebilir.

**Katman 7: Ölçmek ve izlemek**
- Test soru setine **manualde cevabı olmayan sorular** da eklenir. Sistemin bunlara "bulunamadı" demesi gerekir.
- Faithfulness (kaynağa sadakat) metriği düzenli ölçülür (RAGAS vb.).
- Arayüzde "yanlış/eksik" bildirme butonu olur. Tüm soru, cevap ve kaynaklar kayıt altına alınır (audit log).

**Katman 8: Doğru versiyon**
- Sadece **güncel** manual versiyonu aranır (metadata filtresi). Eski versiyondaki doğru ama geçersiz bilgi de yanlış dikime yol açabilir.

**Özet akış:**
```
Soru → Retrieval (filtre + hybrid + rerank)
     → Skor eşiğin altında mı? ── Evet → "Bulunamadı" (LLM çağrılmaz)
     → Hayır → LLM (önce alıntı, sonra cevap, kaynak zorunlu)
     → Otomatik doğrulama (alıntı var mı? sayılar kaynakta var mı?) ── Başarısız → "Bulunamadı / teyit edin"
     → Başarılı → Cevap + vurgulanmış manual sayfası + alıntı
```

**Ayrıntılı çalışma:** Adım 4.2 (prompt), 4.3 (halüsinasyon azaltma), 4.4 (değerlendirme). Bu risk projede **en yüksek öncelikli** olarak işaretlendi.

**S12. Bounding box burada tam olarak ne?**
> **Soru:** bbox normalde bir alanı sınırlayan kutucuk değil midir? Buradaki anlamı ne?

**Cevap:** Evet, aynı kavram. PDF sayfasındaki bir metin parçasını çevreleyen dikdörtgendir. Cevabın geldiği yeri sayfa üzerinde vurgulamak için kullanılır. Ayrıntılar (koordinat sistemi, ölçekleme, kutu listesi): **3. Derlenmiş Notlar → 1.7 → Kavram: Bounding box**.

**S13. BM25'in bu problem için en iyi algoritma olduğundan emin miyiz?**
> **Soru:** BM25'in en iyisi olduğundan emin miyiz? Alternatifler araştırılıp karşılaştırılabilir.

**Cevap:** Emin değiliz, emin olmamız da gerekmiyor: en iyisini **deneyle** seçeceğiz. Araştırmanın özeti:
- BM25 güçlü ve güvenilir bir başlangıç, ama Türkçede **kök bulma olmadan zayıf** kalır.
- **BGE-M3 sparse** ciddi bir alternatif: çok dilli ve embedding modelimizden ek maliyetsiz geliyor.
- SPLADE'in Türkçe desteği zayıf. BM42'nin değerlendirmesi tartışmalı.
- Karşılaştırma tablosu ve A–D deney planı: **3. Derlenmiş Notlar → 1.5**.

**S14. Recall@5 ve MRR nedir?**
> **Cevap:** İkisi de *bulma* adımının başarısını ölçer. **Recall@5:** Doğru chunk ilk 5 sonuçta mı? **MRR:** Doğru chunk kaçıncı sırada (1. sıra = 1, 2. sıra = 0.5 ...)? Örnekli açıklama: **1.5 → Kavram: Retrieval değerlendirme metrikleri**.

**S15. Sparse retrieval nedir, "sparse" ne demek, BGE-M3'ün adı mı?**
> **Cevap:** *Sparse* = **seyrek**. Değerlerinin neredeyse tamamı 0 olan, her boyutu bir kelimeye karşılık gelen vektör. Sparse retrieval = bu vektörlerle yapılan **kelime tabanlı arama** (BM25 de bir sparse yöntemdir). Karşıtı *dense* = **yoğun** vektörle yapılan anlam araması. Model adı değil: "BGE-M3 sparse", BGE-M3 modelinin ürettiği üç çıktıdan biri (dense, sparse, multi-vector). Ayrıntı: **1.5 → Kavram: Sparse ve Dense vektör**.

---

## 3. Derlenmiş Notlar

> Bu bölüm, yukarıdaki anlatım ve soru-cevapların temiz özetidir. Hızlı hatırlamak için buradan okumak yeterli.

### 1.1 RAG mimarisi ve bileşenleri

**RAG = Retrieval-Augmented Generation:** LLM'e cevap vermeden önce ilgili bilgiyi dışarıdan getirip prompta eklemek.

**Neden var?**
| Sebep | Açıklama |
|-------|----------|
| Özel veri | Müşteri manualleri internette yok, model onları hiç görmedi. |
| Güncellik | Model bilgisi eğitim tarihinde donar. RAG'de dosyayı değiştirmek yeterli. |
| İzlenebilirlik | Cevabın hangi dosya/sayfadan geldiği gösterilebilir. **Projemizin temeli bu.** |
| Halüsinasyon | **Azaltır ama sıfırlamaz.** Yanlış chunk gelirse ya da bilgi yoksa model yine uydurabilir. Önleme katmanları için bkz. **S11**. |

**İki ayrı hat:**
```
INGESTION / INDEXLEME (dokümanlar eklendiğinde, bir kez) → kavram: pdf-isleme.md, "Ingestion nedir?"
  PDF → Parse (metin + tablo + sayfa no + bbox)
      → Chunking (parçalara bölme)
      → Embedding (her chunk → vektör)
      → Vector DB'ye kaydet (vektör + metin + metadata)

SORGU (her soruda)
  Soru → Marka/filtre çıkarımı
       → Soru embedding'i (AYNI model ile)
       → Hybrid arama (vektör + BM25) + metadata filtresi → top-20/50 aday
       → Reranker → en iyi 3–5 chunk
       → Prompt (talimat + chunk'lar + soru) → LLM
       → Yanıt + kaynak (dosya, sayfa, bbox)
```

**Bileşenler:**
| Bileşen | Görevi |
|---------|--------|
| Parser | PDF'ten metni, tabloları, sayfa numarasını ve koordinatları çıkarır (Adım 2). |
| Chunker | Metni anlamlı parçalara böler. |
| Embedding modeli | Metni anlamını temsil eden sayı dizisine (vektöre) çevirir. |
| Vector DB | Vektörleri saklar ve en yakın olanları hızlıca bulur. |
| Retriever | Arama stratejisini yönetir (hybrid, filtre, top-k). |
| Reranker | Adayları soruya göre hassas şekilde yeniden sıralar. |
| LLM | Verilen chunk'lara dayanarak cevap ve kaynak üretir. |

**Temel kural:** LLM veri tabanının tamamını görmez, sadece kendisine verilen birkaç chunk'ı görür. **Getirilen chunk yanlışsa cevap da yanlış olur, yani sistem kalitesini en çok retrieval kalitesi belirler.**

### 1.2 Chunking stratejileri

| Strateji | Nasıl çalışır | Artı | Eksi |
|----------|---------------|------|------|
| Sabit boyut | Her N token'da bir böl (+ overlap) | Basit, hızlı | Cümle/tablo ortasından bölebilir |
| Recursive | Önce paragraf, sığmazsa cümle, sığmazsa kelimeden böl | Basit ve daha doğal sınırlar | Doküman yapısını bilmez |
| Sayfa bazlı | Her sayfa bir chunk | Sayfa izlenebilirliği mükemmel | Sayfa çok konulu olabilir, konu sayfa sınırını aşabilir |
| Başlık/bölüm bazlı (structure-aware) | Başlık sınırlarından böl, uzunsa alt böl | Anlam bütünlüğü yüksek, manuallere uygun | Başlıkları doğru tanıyan bir parser gerekir |
| Semantic | Cümle embedding'lerinde anlam değişen yerden böl | Konu geçişlerini yakalar | Yavaş, sonuç tutarsız olabilir |

**Boyut dengesi:**
- Çok küçük → bağlam kaybolur ("bu değer 8–10 olmalı", hangi değer?).
- Çok büyük → anlam sulanır, isabet düşer, maliyet artar, hangi sayfadan geldiği belirsizleşir.
- Tipik aralık: **200–800 token**, %10–20 overlap.

**Sayfa izlenebilirliği (bizim için kritik):**
- Her chunk'ta `pages: [12, 13]` ve sayfa başına `bbox` tutulur.
- Tablolar bölünmeden tek chunk olarak tutulmalıdır. Tablonun başlığı/başlık satırı chunk'a eklenir.
- Chunk'ın başına bağlam eklemek isabeti artırır: `[Nike > Dikiş Standartları > 3.2 Stitch Density]` gibi bir başlık yolu.

### 1.3 Embedding modelleri

#### Kavram: Embedding nedir?

**Tanım:** Bir metnin *anlamını* sabit uzunlukta bir sayı listesine (vektöre) çevirmek. Bu işi yapan modele **embedding modeli** denir.
```
"Dikiş sıklığı inç başına 8-10 olmalıdır"  →  [0.021, -0.143, 0.388, ..., -0.052]  (örn. 1024 sayı)
```

**Neden sayı?** Bilgisayar iki metnin aynı şeyi anlatıp anlatmadığını metne bakarak bilemez, ama iki noktanın arasındaki **mesafeyi** hesaplayabilir. Embedding, "anlam benzerliği" sorusunu "iki nokta ne kadar yakın?" sorusuna çevirir.

**Harita benzetmesi:** Her metin bir haritada bir noktadır. Anlamca benzer metinler yan yana, farklı konular uzak bölgelerde durur. Gerçek harita yüzlerce veya binlerce boyutludur (`bge-m3` → 1024). Tek tek boyutların insan diliyle bir karşılığı yoktur, anlam tüm sayılara dağılmıştır.
```
   • "stitch density"   • "dikiş sıklığı"   • "SPI"       ← aynı bölge
                                    • "kumaş rengi"  • "boya haslığı"   ← başka bölge
   • "teslimat tarihi"                                                  ← başka bölge
```

**Nasıl öğreniyor?** Model milyonlarca metin çiftiyle eğitilir. İlişkili çiftler (soru ↔ cevap, cümle ↔ çevirisi) birbirine **yaklaştırılır**, ilişkisizler **uzaklaştırılır**. Sonunda model hiç görmediği bir cümleyi de anlamına uygun bir yere koyabilir.

**Yakınlık ölçüsü (cosine similarity):** ~1.0 neredeyse aynı anlam, ~0.5 ilişkili, ~0 ilgisiz.

**Kurallar:**
- Soru ve chunk'lar **aynı modelle** vektörleştirilmelidir. Her model kendi haritasını çizer, iki modelin koordinatları birbirine uymaz.
- Model değişirse **tüm dokümanların yeniden indekslenmesi** gerekir.

**Güçlü / zayıf yanlar:**
| Güçlü | Zayıf |
|-------|-------|
| Eş anlamlılar | Kodlar ve sayılar ("ISO 4915" ≈ "ISO 4916" görünür) → BM25 ile kapatılır |
| Diller arası eşleşme | Olumsuzluk ("8'den az" ≈ "8'den fazla" görünebilir) → reranker ile kapatılır |
| Aynı sorunun farklı kelimelerle sorulması | Çok uzun metinlerde anlam sulanır → doğru chunk boyutu |

#### Kavram: Diller arası (cross-lingual) arama

**Farklı dillerdeki metinler nasıl yan yana düşüyor?** Bunu yalnızca **çok dilli** modeller yapabilir. Üç etken var:
1. **Ortak kelime parçaları:** Tüm diller aynı tokenizer ile okunur. Sayılar, birimler ve kodlar ("ISO", "mm", "SPI") dillerde ortaktır.
2. **Çok dilli ön eğitim:** Model 100'den fazla dilde metin okur.
3. **Çeviri çiftleriyle eğitim (asıl etken):** "Dikiş sıklığı 8-10 olmalıdır" ↔ "Stitch density shall be 8-10" çifti aynı noktaya çekilir. Sonuçta model cümlenin hangi **dilde** olduğunu değil, **ne anlattığını** kodlar.

Sadece İngilizce bir model Türkçe cümleyi anlamsız bir noktaya koyar. **Çok dilliliği şart koymamızın sebebi bu.**

**Senaryo: İngilizce manual + Türkçe soru (ya da tersi), çeviri yapmadan**
```
Soru (TR): "Nike için dikiş sıklığı standardı nedir?"
   → çok dilli embedding → en yakın chunk bulunur
Chunk (EN, s.12): "Stitch density for Nike products shall be 8-10 SPI."
   → LLM'e verilir: İngilizce chunk + Türkçe soru + "Sorunun dilinde cevap ver" talimatı
Cevap (TR): "Nike ürünlerinde dikiş sıklığı inç başına 8-10 olmalıdır. (Kaynak: Nike_Manual.pdf, s.12)"
```
- **Bulma** işini çok dilli embedding modeli, **çevirip cevaplama** işini LLM yapar. Ayrı bir çeviri adımı gerekmez.
- Ekranda gösterilen sayfa **orijinal dildeki** sayfadır. TTS sorunun dilindeki cevabı okur.

**Dikkat edilecekler:**
| Konu | Risk | Çözüm |
|------|------|-------|
| Benzerlik skoru | Diller arası eşleşmede skor biraz daha düşük çıkar | Eşik değerini buna göre ayarla, reranker da çok dilli olsun |
| **BM25** | **Diller arası çalışmaz** ("stitch" Türkçe metinde geçmez) | Soruyu doküman diline de çevirip BM25'i o çeviriyle çalıştır (*query translation* ) |
| Teknik terimler | LLM sektöre özel terimi yanlış çevirebilir | Terim sözlüğü (glossary) hazırlayıp prompta eklemek |
| Alıntı | Cevap TR, kaynak metin EN olur | Sorun değil. Kaynak alıntısı orijinal dilde gösterilir |

#### Kavram: Query translation (sorgu çevirisi)

**Ne?** Arama yapılmadan önce kullanıcının **sorusu** doküman(lar)ın diline çevrilir. RAG'de sorgu tarafında yapılan bir ön işleme (preprocess) adımıdır. **Dokümanlar değil, yalnızca soru çevrilir.** Manueller orijinal dilinde kalır.

**Neden yapıyoruz?**
- **Dense arama** zaten diller arası çalışır. Çok dilli embedding "dikiş sıklığı" ile "stitch density"yi yan yana koyar, çeviriye ihtiyaç duymaz.
- **Sparse arama (BM25)** ise birebir kelime eşleşmesine dayanır. Türkçe soru ("dikiş sıklığı") İngilizce chunk'taki "stitch density" ile **tek bir ortak kelime paylaşmaz**, puan 0 çıkar. Hybrid search'ün kelime tarafı fiilen devre dışı kalır.
- Bu kayıp özellikle **kod ve standart numarası** içeren sorularda acıtır, çünkü hybrid'i bu sorular için kuruyoruz. Örnek: "ISO 4915'e göre dikiş tipi" sorusunda "ISO 4915" zaten eşleşir, ama "dikiş tipi" ↔ "stitch type" eşleşmesi kaybolur.
- Soru doküman diline çevrilince BM25 tekrar çalışır ve hybrid'in faydası geri gelir.

**Nasıl?**
```
Soru (TR): "Nike için dikiş sıklığı standardı nedir?"
   │
   ├──► Dense arama  ← orijinal TR soru ile (çok dilli embedding)
   │
   └──► Çeviri (LLM veya makine çevirisi servisi) → "What is the stitch density standard for Nike?"
            └──► BM25 / sparse arama  ← çevrilmiş EN soru ile
   │
   ▼
RRF ile birleştir → Reranker → LLM
```
- **Çeviriyi kim yapar?** İki seçenek var: (1) bir **LLM** ("Bu soruyu İngilizceye çevir" talimatıyla) veya (2) bir **makine çevirisi servisi** (MT, *Machine Translation*: yalnızca çeviri için yapılmış sistemler, örn. Google Translate API, DeepL, Azure Translator veya lokal çalışan NLLB / OPUS-MT modelleri). MT genelde daha hızlı ve ucuzdur. LLM ise terim sözlüğü gibi talimatlara daha iyi uyar.
- Hangi dile çevrileceği, aranan manuellerin `lang` metadata'sından bilinir. Manuel karışıksa soru her iki dilde aranabilir.
- Kodlar, numaralar ve birimler çeviride **olduğu gibi korunmalı** ("ISO 4915", "8-10 SPI").

**Maliyeti / riskleri:**
| Konu | Açıklama |
|------|----------|
| Gecikme | Her soruda ek bir çeviri çağrısı (~100–500 ms). Kısa metin olduğu için genelde küçük. |
| Çeviri hatası | Sektöre özel terim yanlış çevrilirse BM25 yanlış kelimeyi arar → terim sözlüğü (glossary) ile azaltılır. |
| Gizlilik | Çeviri bulut servisle yapılırsa soru dışarı gider (Adım 7). Lokal LLM ile de yapılabilir. |

**Alternatifi:** BGE-M3 sparse gibi çok dilli *learned sparse* yöntemler bu açığı kısmen kapatabilir. Query translation'ın gerçekten gerekli olup olmadığı 1.5'teki deneyde "TR soru + EN manual" sorularıyla ölçülecek (req.md, Q6).

 **Hedef, çevirmeden orijinal haliyle indekslemek.** Faydaları: çeviri maliyeti ve gecikmesi kalkar, çeviri hatası riski ortadan kalkar, gösterilen sayfa müşterinin orijinal dokümanı olur.

#### Model seçenekleri

**Gereksinimimiz:** Türkçe + İngilizce, diller arası arama (soru TR, manual EN veya tersi). Bu yüzden model **çok dilli (multilingual)** olmalı.

| Model | Tür | Not |
|-------|-----|-----|
| `BAAI/bge-m3` | Açık kaynak, lokal | Çok dilli, uzun metin (8K), aynı model hem dense hem sparse vektör üretebilir (hybrid için avantaj). Güçlü aday. |
| `intfloat/multilingual-e5-large` | Açık kaynak, lokal | Yaygın, dengeli, Türkçe desteği iyi. |
| `Qwen3-Embedding` ailesi | Açık kaynak, lokal | Çok dilli benchmark'larda üst sıralarda, farklı boyut seçenekleri var. |
| `jina-embeddings-v3` | Açık ağırlık / API | Çok dilli, ticari lisans koşullarına bakılmalı. |
| OpenAI `text-embedding-3-large` | Bulut API | Kolay, kaliteli. Veri dışarı gider. |
| Cohere `embed-multilingual` / `embed-v4` | Bulut API | Çok dilli odaklı. Veri dışarı gider. |

**Seçerken bakılacaklar:** Türkçe kalitesi, maksimum girdi uzunluğu, vektör boyutu (depolama/hız), lisans, lokal çalıştırılabilirlik (gizlilik, Adım 7), donanım ihtiyacı.
**Doğrulama:** [MTEB leaderboard](https://huggingface.co/spaces/mteb/leaderboard)'a bakılır, ama asıl karar **kendi test soru setimizle** (Adım 0.4) verilir.

>  Embedding modeli değişirse **tüm dokümanların yeniden indekslenmesi** gerekir. Soru ve dokümanlar mutlaka aynı modelle vektörleştirilmelidir.

### 1.4 Vector DB karşılaştırma

| DB | Tür | Metadata filtre | Hybrid (BM25) | Artı | Eksi |
|----|-----|-----------------|---------------|------|------|
| **Chroma** | Gömülü / hafif sunucu | ✅ | Sınırlı | Kurulumu en kolay, prototip için ideal | Büyük ölçekte ve üretimde zayıf |
| **Qdrant** | Sunucu (Docker) / bulut | ✅ Güçlü | ✅ (sparse vektör) | Hızlı, filtreleme çok iyi, hybrid desteği var, iyi dokümante | Ayrı servis çalıştırmak gerekir |
| **pgvector** | PostgreSQL eklentisi | ✅ (SQL) | Postgres full-text ile | Tek DB'de hem ilişkisel veri hem vektör, yetkilendirme kolay | Çok büyük ölçekte tuning gerekir |
| Weaviate / Milvus | Sunucu | ✅ | ✅ | Ölçeklenebilir, zengin özellikli | Bizim ölçeğimiz için ağır olabilir |

**Bizim ölçeğimiz:** Birkaç marka × onlarca manual × yüzlerce sayfa → on binlerce chunk. Hepsi bu ölçeği rahat kaldırır. Seçimi **filtreleme, hybrid desteği ve kurulum kolaylığı** belirler.

### 1.5 Hybrid search

| Arama türü | Güçlü olduğu yer | Zayıf olduğu yer |
|------------|------------------|------------------|
| Vektör (dense) | Anlam, eş anlamlılar, diller arası ("dikiş sıklığı" ↔ "stitch density") | Kodlar, sayılar ("ISO 4915" ≈ "ISO 4916") |
| Kelime (BM25 / sparse) | Birebir terimler, ürün kodları, standart numaraları | Eş anlamlıları ve başka dilde yazılmış karşılıkları bulamaz |

**Hybrid:** İki arama da yapılır, sonuç listeleri birleştirilir. En yaygın birleştirme yöntemi **RRF (Reciprocal Rank Fusion)**: puanlara değil sıralamalara bakar, iki listede de üstte olan chunk kazanır.

**Neden bizim için önemli:** Manuallerde standart numaraları (ISO, ASTM), ölçü birimleri ve ürün/malzeme kodları çok geçer.

#### Kavram: Sparse (seyrek) ve Dense (yoğun) vektör

**Türkçesi:** *sparse* = **seyrek**, *dense* = **yoğun**. İsimler, vektörün içindeki sayıların ne kadarının dolu olduğunu anlatır. 

| | **Dense (yoğun)** | **Sparse (seyrek)** |
|---|---|---|
| Uzunluk | Kısa: ~384–4096 boyut (`bge-m3` → 1024) | Çok uzun: kelime dağarcığı kadar (on binlerce – yüz binlerce boyut) |
| Doluluk | **Her** boyut bir sayı içerir | Neredeyse hepsi **0**, sadece metinde geçen kelimelerin boyutları dolu |
| Boyutun anlamı | Tek başına anlamsız, anlam tüm sayılara dağılmış | **Her boyut bir kelimedir** ("stitch" = 48213. boyut gibi) |
| Ne yakalar | Anlam benzerliği | Kelime eşleşmesi |
| Örnekler | `bge-m3` dense, `multilingual-e5`, OpenAI embedding | BM25, TF-IDF, SPLADE, BGE-M3 sparse |

```
Metin: "Stitch density shall be 8-10 SPI"

Dense  (1024 boyut, hepsi dolu):
[0.021, -0.143, 0.388, 0.007, -0.250, 0.119, ..., -0.052]

Sparse (~250.000 boyut, sadece birkaçı dolu):
{ "stitch": 0.31, "density": 0.27, "spi": 0.44, "8": 0.12, "10": 0.12 }   ← geri kalan ~249.995 boyut 0
```

Sparse vektörü saklarken sıfırlar yazılmaz, sadece `{kelime: ağırlık}` çiftleri tutulur. Bu yüzden çok uzun olmasına rağmen yer kaplamaz.

**Sparse retrieval:** Sparse vektörlerle yapılan arama, yani özünde **kelime tabanlı arama.** Soru ile chunk'ın ortak kelimeleri ve bu kelimelerin ağırlıkları üzerinden puan hesaplanır. "Kelime araması" dediğimiz şeyin teknik adı budur.
- **Klasik sparse:** BM25, TF-IDF. Ağırlıklar formülle hesaplanır (kelime sıklığı, nadirlik).
- **Öğrenilmiş (learned) sparse:** SPLADE, BGE-M3 sparse. Ağırlıkları bir sinir ağı belirler.

**Dense retrieval:** Dense vektörlerle yapılan arama, yani **anlam tabanlı arama.**

**Hybrid search = dense retrieval + sparse retrieval.**

#### "BGE-M3 sparse" ne demek?

"Sparse", modelin adının parçası değil, modelin **ürettiği çıktılardan birinin türü**. Model adındaki **M3** üç özelliği anlatır:
- **Multi-Linguality:** 100'den fazla dil
- **Multi-Granularity:** Kısa cümleden 8192 token'a kadar uzun metin
- **Multi-Functionality:** Tek modelden **üç farklı çıktı**:
  1. **Dense vektör:** Anlam araması için (1024 boyut)
  2. **Sparse vektör** (*lexical weights*): Kelime araması için, her kelimeye öğrenilmiş bir ağırlık
  3. **Multi-vector** (ColBERT tarzı): Her token için ayrı vektör, daha hassas ama daha pahalı eşleştirme

Yani "BGE-M3 sparse" = **BGE-M3 modelinin ürettiği seyrek vektör.** Avantajı, chunk'ı bir kez modelden geçirince hem dense hem sparse vektörün birlikte elde edilmesi. BM25 için ayrı bir sistem kurmaya gerek kalmaz.

#### Kelime (sparse) arama: BM25 tek seçenek mi?

**Hayır.** BM25 en yaygın ve en güvenilir *başlangıç noktası*dır, ama bizim problem için en iyisi olduğu kanıtlanmış değil. Hybrid search'ün "kelime" tarafında kullanılabilecek seçenekler:

| Yöntem | Nasıl çalışır | Artı | Eksi | Bizim için |
|--------|---------------|------|------|------------|
| **TF-IDF** | Kelime sıklığı × nadirlik | En basit | Uzun dokümanları kayırır, doygunluk yok | BM25 bunun gelişmiş hali, ayrıca denemeye gerek yok |
| **BM25** | TF-IDF + kelime sıklığı doygunluğu + doküman uzunluğu normalizasyonu | Eğitim gerektirmez, hızlı, açıklanabilir, onlarca yıldır sağlam bir baseline | Eş anlamlıları ve diller arası eşleşmeyi bulamaz. **Türkçe için kök bulma (stemming) şart** | ✅ Güçlü aday (baseline) |
| **BM25F / alan ağırlıklı** | Başlıkta geçen kelimeye gövdede geçenden fazla puan | Bölüm başlıkları belirgin manuellerde faydalı | Ayar gerektirir | ➕ BM25'e ek olarak denenebilir |
| **SPLADE** (learned sparse) | Bir transformer kelime ağırlıklarını öğrenir ve ilgili terimleri ekler (genişletme) | Eş anlamlı sorununu kısmen çözer | Çoğu model İngilizce odaklı, çok dilli versiyonları sınırlı. GPU ister | 🟡 Türkçe desteği zayıf, öncelikli değil |
| **BGE-M3 sparse** (lexical weights) | Dense vektörü üreten aynı model, her kelime için ağırlık da üretir | Çok dilli, **ek model gerektirmez** (embedding sırasında bedavaya gelir), Qdrant destekliyor | Kodlar/sayılar üzerinde BM25 kadar keskin olmayabilir. Tokenizer'a bağlı | ✅ Güçlü aday |
| **BM42** (Qdrant) | BM25'in IDF'i + transformer attention ağırlıkları | Kısa metinler için önerildi | **Yayınlanan değerlendirmesi tartışmalı.** Qdrant'ın kendi tekrar testlerinde iyi ayarlanmış BM25 daha yüksek recall verdi | ❌ Önerilmez |

**Türkçe için önemli not:** Türkçe eklemeli bir dil. "dikiş", "dikişin", "dikişlerde", "dikişlerinin" BM25 için ayrı kelimelerdir, kök bulma yapılmazsa eşleşmezler. Türkçe IR çalışmalarına göre:
- Kök bulma, Türkçede arama başarısını belirgin şekilde artırır (bir çalışmada **%20'ye kadar**).
- Morfolojik analizle kök bulma (örn. **Zemberek**) en iyi sonucu verir.
- Kelimenin **ilk 5 harfini almak** (prefix-5) şaşırtıcı derecede iyi ve çok ucuz bir alternatiftir.
- Manuallerimiz karışık dilde olacağı için her chunk kendi diline göre işlenmeli: `lang: tr` → Türkçe kök bulucu, `lang: en` → İngilizce stemmer.

**Kodlar ve sayılar için not:** "ISO 4915", "SPI-10", "M12x1.5" gibi ifadeler tokenizer tarafından parçalanabilir. Bunların bütün halde indekslenmesi (veya ayrı bir "keyword" alanında tutulması) birebir eşleşmeyi garantiler.

#### Birleştirme (fusion) yöntemleri

| Yöntem | Nasıl | Ne zaman |
|--------|-------|----------|
| **RRF** (Reciprocal Rank Fusion) | Puanlara değil sıralamalara bakar: `1 / (k + sıra)`, genelde k=60 | **Başlangıç için.** Ayar gerektirmez |
| **Ağırlıklı birleştirme** (convex) | `α × dense_skor + (1-α) × sparse_skor` | Elimizde etiketli test soruları (~50+) olunca α ayarlanarak RRF'i geçebilir |

#### Karar nasıl verilecek? (deney planı)

Hangi yöntemin en iyi olduğunu kaynaklardan değil, **kendi manuellerimiz ve test soru setimizle** ölçeceğiz:

| # | Yapılandırma |
|---|--------------|
| A | Sadece dense (`bge-m3`) |
| B | Dense + BM25 (Türkçe/İngilizce stemming ile) |
| C | Dense + BGE-M3 sparse |
| D | Dense + BM25 + BGE-M3 sparse (üçlü) |
| + | Her birinin reranker'lı versiyonu |

**Tablodaki terimler:**
- **Dense** = *dense retrieval*, yani `bge-m3`'ün ürettiği **yoğun vektörlerle anlam araması.** Evet, vektörün tüm boyutları doludur, ama tabloda kastedilen vektörün kendisi değil, onunla yapılan **arama yöntemidir.**
- **BM25 / BGE-M3 sparse** = **seyrek vektörlerle kelime araması** (sparse retrieval).
- **Reranker'lı versiyon** = Arama sonucu gelen ilk ~30 aday, LLM'e verilmeden önce bir reranker modeliyle **yeniden sıralanır** (bkz. 1.6). Böylece reranker'ın sonuca ne kadar katkı yaptığı ayrıca ölçülür.

**Ölçüt:** Recall@5 (doğru chunk ilk 5'te mi?), MRR (doğru chunk kaçıncı sırada?). Soru seti ayrı ayrı raporlanır: kod/numara içeren sorular, TR soru + EN manual, cevabı olmayan sorular.

#### Kavram: Retrieval değerlendirme metrikleri

Bu metrikleri hesaplamak için test setinde her sorunun **doğru chunk'ının (veya sayfasının) önceden bilinmesi** gerekir (Adım 0.4). Metrikler yalnızca *bulma* adımını ölçer, LLM cevabının kalitesi ayrıca ölçülür (Adım 4.4).

**Recall@k (k'da yakalama oranı):** Doğru chunk ilk **k** sonuç içinde mi? Her soru için cevap evet (1) ya da hayır (0) olur, tüm sorulardaki ortalama alınır.
- **Recall@5 = 0.80** → soruların %80'inde doğru chunk ilk 5 sonuçta.
- Neden önemli: LLM'e ilk 3–5 chunk'ı veriyoruz. Doğru chunk orada değilse LLM onu hiç görmez, doğru cevap verme şansı kalmaz.

**MRR (Mean Reciprocal Rank, ortalama ters sıra):** Doğru chunk **kaçıncı sırada**? Her soru için `1 / sıra` hesaplanır, ortalaması alınır.
- 1. sırada → 1/1 = **1.0**
- 2. sırada → 1/2 = **0.5**
- 5. sırada → 1/5 = **0.2**
- Hiç bulunamadı → **0**
- Neden önemli: Recall@5 "ilk 5'te mi?" diye sorar, 1. sırayla 5. sırayı ayırt etmez. MRR doğru chunk'ı **en üste** koyan sistemi ödüllendirir. Ekranda **ilk** kaynağın sayfasını göstereceğimiz için bu bizim için önemli.

**Örnek (4 soruluk test seti):**
| Soru | Doğru chunk'ın sırası | Recall@5 | 1/sıra |
|------|----------------------|----------|--------|
| S1 | 1 | ✅ 1 | 1.00 |
| S2 | 3 | ✅ 1 | 0.33 |
| S3 | 7 | ❌ 0 | 0.14 |
| S4 | bulunamadı | ❌ 0 | 0 |
| **Sonuç** | | **Recall@5 = 2/4 = 0.50** | **MRR = 1.47/4 ≈ 0.37** |

**Diğer sık görülen metrikler:**
| Metrik | Ne ölçer |
|--------|----------|
| Precision@k | İlk k sonucun yüzde kaçı gerçekten ilgili? (Birden fazla doğru chunk olduğunda anlamlı) |
| Hit Rate@k | Recall@k ile aynı fikir, tek doğru chunk olduğunda ikisi eşittir |
| nDCG@k | MRR gibi sıraya bakar, ama birden fazla doğru chunk ve "kısmen ilgili" sonuçları da hesaba katar. Akademik karşılaştırmalarda sık kullanılır |

**Bizim için hedef örneği (pilot):** Recall@5 ≥ 0.90, MRR ≥ 0.70. Kesin hedefler ilk ölçümden sonra belirlenecek.

### 1.6 Reranking

- **Sorun:** Vektör araması hızlıdır ama kaba sıralar. "En yakın" her zaman "en doğru" değildir.
- **Çözüm (iki aşamalı arama):**
  1. Hızlı ön eleme (bi-encoder + BM25) → top-20/50 aday
  2. Reranker (cross-encoder) soruyu ve chunk'ı **birlikte** okuyup puanlar → en iyi **3–5** chunk LLM'e gider
- **Neden hepsi verilmiyor:** Gürültü modelin dikkatini dağıtır (*lost in the middle*), maliyet ve gecikme artar, yanlış kaynağa atıf riski yükselir.
- **Seçenekler:** `BAAI/bge-reranker-v2-m3` (açık kaynak, çok dilli), Jina Reranker, Cohere Rerank (bulut).
- **Maliyet:** Soru başına ~100–500 ms ek gecikme (donanıma bağlı). Genelde kalite kazancı buna değer.

#### Kavram: Bi-encoder ve cross-encoder (reranker neden daha isabetli?)

| | **Bi-encoder** (embedding modeli, örn. `bge-m3`) | **Cross-encoder** (reranker, örn. `bge-reranker-v2-m3`) |
|---|---|---|
| Nasıl çalışır | Soru ve chunk **ayrı ayrı** vektöre çevrilir, sonra vektörler karşılaştırılır | Soru ve chunk **yan yana tek metin** olarak modele verilir, model doğrudan "ne kadar alakalı?" puanı üretir |
| Benzetme | İki kişinin özgeçmişine ayrı ayrı bakıp uyumlu mu diye tahmin etmek | İki kişiyi aynı masaya oturtup konuşmalarını dinlemek |
| Hız | Çok hızlı. Chunk vektörleri önceden hesaplanmış durumda, soru başına sadece soru vektörleştirilir | Yavaş. Her soru–chunk çifti için model ayrıca çalışır, önceden hesaplanamaz |
| İsabet | Kaba sıralama | Çok daha hassas: olumsuzluğu, sayıları, "soruyu gerçekten cevaplıyor mu?" sorusunu anlar |
| Kullanım | Binlerce chunk içinden ilk ~30 adayı bulmak | Bu ~30 adayı yeniden sıralayıp en iyi 3–5'i seçmek |

**Neden ikisi birlikte kullanılıyor?** Cross-encoder'ı on binlerce chunk'ın hepsine çalıştırmak çok yavaş olurdu. Bu yüzden önce bi-encoder hızlıca adayları daraltır, sonra cross-encoder sadece bu az sayıdaki aday üzerinde hassas karar verir.

**Örnek:** Soru: *"Nike'ta dikiş sıklığı en az kaç olmalı?"*
| Chunk | Arama sırası (bi-encoder) | Reranker puanı | Yeni sıra |
|-------|---------------------------|----------------|-----------|
| "Stitch density **should not be below** 8 SPI" | 4 | 0.94 | **1** |
| "Stitch density is measured in SPI" (tanım, değer yok) | 1 | 0.41 | 3 |
| "Thread density for embroidery: 12 SPI" (nakış, alakasız) | 2 | 0.22 | 4 |
| "Stitch density for Nike apparel: 8–10 SPI" | 3 | 0.88 | 2 |

Bi-encoder kelime ve konu benzerliğine bakarak tanım cümlesini en üste koydu. Reranker ise sorunun **"en az kaç"** sorusunu gerçekten cevaplayan chunk'ı birinci sıraya çıkardı.

### 1.7 Metadata filtreleme

#### Kavram: Metadata nedir?

**Metadata = "veri hakkında veri".** Chunk'ın **metni** asıl veridir. Metadata ise o metnin **kimliğini ve konumunu** anlatan etiketlerdir: hangi markaya ait, hangi dokümandan, hangi sayfadan, hangi dilde vb.

Vector DB'de her chunk üç parça halinde saklanır:
```
┌──────────────────────────────────────────────────────────────┐
│ 1. Vektör(ler)  → [0.021, -0.143, ...]  (arama için)          │
│ 2. Metin        → "Stitch density shall be 8-10 SPI..."       │
│ 3. Metadata     → {brand: "Nike", page: 12, lang: "en", ...}  │
└──────────────────────────────────────────────────────────────┘
```
Bir kütüphane benzetmesiyle: kitabın içeriği metin, kütüphane kartındaki yazar, yıl, raf numarası ise metadata'dır.

#### Kavram: Metadata filtreleme nedir?

**Tanım:** Vektör araması yapılmadan önce (veya yapılırken) aday chunk'ları **metadata koşullarına göre daraltmak.** Klasik veri tabanındaki `WHERE` koşulunun vector DB'deki karşılığıdır.

```
Filtresiz:  "dikiş sıklığı" → TÜM chunk'lar içinde en benzerler
            → Nike, Adidas, Puma chunk'ları karışık gelir

Filtreli:   "dikiş sıklığı" + WHERE brand = "Nike" AND version = latest AND lang IN (tr, en)
            → sadece güncel Nike chunk'ları içinde en benzerler
```

**Neden gerekli?** Vektör araması sadece **anlam benzerliğine** bakar, "bu chunk kime ait?" bilgisini bilmez. Nike ve Adidas'ın dikiş bölümleri neredeyse aynı cümlelerle yazılmış olabilir, vektörleri de birbirine çok yakın çıkar. Anlam benzerliği bunları ayırt edemez, metadata eder.

| Fayda | Örnek |
|-------|-------|
| **Doğruluk** | Nike sorusuna Adidas standardıyla cevap verilmez (yanlış dikim riski, bkz. S11). |
| **Güncellik** | Eski manual versiyonundaki geçersiz değer gelmez. |
| **Güvenlik** | Kullanıcı yetkisi olmayan markanın dokümanını hiç göremez (Adım 7.3). |
| **Hız** | Arama daha küçük bir küme üzerinde yapılır. |

**Filtreleme zamanlaması:**
| Tür | Nasıl | Artı / Eksi |
|-----|-------|-------------|
| **Pre-filter** (önce filtrele) | Önce `brand = Nike` olanlar seçilir, arama sadece onların içinde yapılır | ✅ Sonuç sayısı garanti, yanlış marka asla gelmez. **Önerilen yöntem.** Qdrant bunu verimli yapar. |
| **Post-filter** (sonra filtrele) | Önce tüm chunk'larda top-30 bulunur, sonra Nike olmayanlar atılır | ❌ Top-30'un çoğu Adidas ise elde 2–3 chunk kalabilir, doğru chunk kaybolabilir. |

**Filtre değerleri nereden gelir?**
1. **Arayüzden:** Kullanıcı marka/doküman seçer (en güvenilir).
2. **Sorudan:** "Nike için..." → bilinen marka listesiyle eşleştirme veya LLM ile çıkarım.
3. **Sistemden:** Kullanıcının yetkili olduğu markalar, `is_latest = true` gibi her zaman uygulanan kurallar.

Soruda marka yoksa tüm (yetkili) markalarda aranır ve cevapta marka belirtilir, ya da kullanıcıya "Hangi marka için?" diye sorulur.

#### Metadata'nın dört görevi

Metadata yalnızca filtreleme için tutulmaz. Bir alan şu işlerden bir veya birkaçına yarar:
1. **Filtreleme:** Aramayı daraltmak (`brand`, `version`, `lang`)
2. **Kaynak gösterme / görüntüleme:** Sayfayı açmak ve vurgulamak (`doc_name`, `pages`, `bboxes`)
3. **LLM'e bağlam vermek:** Prompta "Kaynak: Nike Manual v3, Bölüm 3.2" diye eklemek (`section_path`, `doc_title`)
4. **Yönetim:** Güncelleme, silme, yeniden indeksleme, denetim (`doc_id`, `file_hash`, `ingested_at`)

#### Tutulabilecek metadata alanları

**Doküman düzeyi** (dokümandaki tüm chunk'larda aynı):
| Alan | Örnek | Görevi | Neden |
|------|-------|--------|-------|
| `doc_id` | `nike-stitch-2025-v3` | Yönetim | Dokümanı tekil tanımlar. Güncellemede eski chunk'ları silmek için |
| `brand` / `customer` | `Nike` | Filtre | Marka filtresi (en kritik alan) |
| `doc_name` | `Nike_Stitching_Manual.pdf` | Kaynak | Ekranda ve cevapta gösterilir |
| `doc_title` | `Nike Apparel Stitching Standards` | Kaynak, bağlam | Dosya adından daha okunur |
| `doc_type` | `stitching_manual`, `quality_manual`, `packaging_guide`, `test_method` | Filtre | "Sadece kalite manuellerinde ara" |
| `version` | `2025-v3` | Filtre, kaynak | Hangi versiyondan geldiğini göstermek |
| `is_latest` | `true` | Filtre | **Sadece güncel versiyonda arama** (eski geçersiz bilgiye karşı) |
| `effective_date` | `2025-03-01` | Filtre, kaynak | Yürürlük tarihi. "Bu tarihten itibaren geçerli" |
| `lang` | `en`, `tr` | Filtre, işleme | Doğru stemmer seçimi, query translation hedef dili |
| `product_category` | `apparel`, `footwear`, `accessories` | Filtre | Aynı markada ayakkabı ve tekstil standardı farklı olabilir |
| `season` / `collection` | `FW25` | Filtre | Sezona özel kurallar varsa |
| `confidentiality` | `confidential`, `internal` | Erişim | Gizlilik seviyesi (Adım 7) |
| `allowed_groups` | `["nike-team", "qa"]` | Erişim | Kullanıcı yetkisine göre filtre (Adım 7.3) |
| `source_type` | `digital`, `scanned` | Kalite | Taranmış (OCR'lı) içerik daha az güvenilir olabilir |
| `file_hash` | `sha256:…` | Yönetim | Aynı dosyanın tekrar yüklenmesini ve değişip değişmediğini tespit etmek |
| `ingested_at` | `2026-10-08T14:20` | Yönetim | Ne zaman indekslendi |

**Konum** (chunk'ın dokümandaki yeri):
| Alan | Örnek | Görevi | Neden |
|------|-------|--------|-------|
| `pages` | `[12, 13]` | Kaynak | Hangi sayfa(lar) gösterilecek |
| `page_labels` | `["3-4", "3-5"]` | Kaynak | PDF'in iç sayfa numarası basılı numaradan farklı olabilir (kapak, içindekiler vb.). Kullanıcıya basılı numara gösterilir |
| `bboxes` | `[{page: 12, box: [...]}, ...]` | Görüntüleme | Sayfada vurgulama |
| `section_path` | `["3. Dikiş", "3.2 Stitch Density"]` | Bağlam, filtre | Başlık hiyerarşisi. Chunk'ın başına eklenir, isabeti artırır |
| `chunk_index` | `47` | Yönetim | Dokümandaki sıra. Komşu chunk'ları getirmek için |
| `prev_chunk_id` / `next_chunk_id` | `…46` / `…48` | Bağlam | Cevap chunk sınırında kesiliyorsa komşuyu da LLM'e vermek |

**İçerik** (chunk'ın kendisi hakkında):
| Alan | Örnek | Görevi | Neden |
|------|-------|--------|-------|
| `chunk_type` | `text`, `table`, `figure`, `list` | Filtre, işleme | Tablolar farklı gösterilebilir. "Sadece tablolarda ara" |
| `table_caption` / `figure_caption` | `Table 3: Stitch types by seam` | Bağlam | Tablo/şekil açıklaması aramada çok işe yarar |
| `keywords` / `codes` | `["ISO 4915", "SPI", "301"]` | Arama | Kod ve standart numaralarını ayrıca tutmak, birebir eşleşmeyi garantiler (bkz. 1.5) |
| `token_count` | `412` | İşleme | Prompt'a sığdırma hesabı |
| `ocr_confidence` | `0.87` | Kalite | Düşük güvenli OCR metnine dayanırken uyarı vermek |

#### Tam örnek

```json
{
  "doc_id": "nike-stitch-2025-v3",
  "brand": "Nike",
  "doc_name": "Nike_Stitching_Manual.pdf",
  "doc_title": "Nike Apparel Stitching Standards",
  "doc_type": "stitching_manual",
  "version": "2025-v3",
  "is_latest": true,
  "effective_date": "2025-03-01",
  "lang": "en",
  "product_category": "apparel",
  "confidentiality": "confidential",
  "allowed_groups": ["nike-team", "qa"],
  "source_type": "digital",

  "pages": [12, 13],
  "page_labels": ["3-4", "3-5"],
  "bboxes": [
    {"page": 12, "box": [72, 210, 523, 268]},
    {"page": 12, "box": [72, 275, 523, 410]},
    {"page": 13, "box": [72, 60, 523, 140]}
  ],
  "section_path": ["3. Stitching Requirements", "3.2 Stitch Density"],
  "chunk_index": 47,

  "chunk_type": "text",
  "codes": ["SPI", "ISO 4915"],
  "token_count": 412
}
```

**Örnek filtre (pseudo):**
```
brand = "Nike"
AND is_latest = true
AND "nike-team" IN allowed_groups        ← kullanıcının yetkisi
AND product_category = "apparel"         ← soruda/arayüzde belirtildiyse
```

> **Pilot için öneri:**  *Zorunlu çekirdek:*  `doc_id`, `brand`, `doc_name`, `version`, `is_latest`, `lang`, `pages`, `bboxes`, `section_path`, `chunk_type`. Gerisi ihtiyaç ortaya çıktıkça eklenir. Ancak sonradan alan eklemek yeniden indeksleme gerektirebilir, bu yüzden **marka ve ürün kategorisi gibi filtrelerin baştan netleştirilmesi** iyi olur. Kesin şema Adım 2.5'te belirlenecek.

> **Açık soru:** Bu metadata'nın bir kısmı (marka, versiyon, ürün kategorisi, yürürlük tarihi) PDF'ten otomatik çıkarılamayabilir. Doküman yüklenirken **kim, nasıl girecek?** (Yükleme formu, dosya adlandırma kuralı, LLM ile otomatik çıkarım + insan onayı.)

#### Birden fazla doküman türü: Ürün standartları + makine kılavuzları karışmaz mı?

**Soru:** Sisteme hem marka/ürün standartları (dikiş şartnameleri) hem makine kılavuzları girerse, "dikiş sıklığı" diye sorulduğunda sistem standarttan mı, makineden mi cevap verecek? Ürünler birbirine karışmaz mı?

**Kısa cevap:** Doğru kurulursa karışmaz. Çözüm üç parçalı: (1) metadata'yı **katmanlı** tutmak, (2) sorunun **hangi türe ait olduğunu** anlamak, (3) gerçekten belirsizse **sormak** veya iki kaynağı birlikte kullanmak.

**1. Katmanlı metadata: Önce tür, sonra türe özel alanlar**

Her chunk'ın en üst etiketi **`doc_type`**dır. Her türün kendine özel alanları olur:

| Alan | Ürün standardı / şartname | Makine kılavuzu |
|------|---------------------------|-----------------|
| `doc_type` | `product_standard` | `machine_manual` |
| **Kime ait** | `brand` = "Nike" (müşteri) | `manufacturer` = "Brother" (üretici) |
| **Neyle ilgili** | `product_category` = "ceket", "pantolon" | `product_model` = "S-7300A" |
| Ortak alanlar | `doc_id`, `version`, `is_latest`, `lang`, `pages`, `bboxes`, `section_path`, `chunk_type` | aynı |

> ⚠️ **Önemli ayrım:** "Brother" bir **makine üreticisi**, "Nike" bir **müşteri markası**. İkisi aynı `brand` alanına yazılmamalı. Aynı alana yazılırsa "marka filtresi" iki farklı anlama gelir ve karışıklık burada başlar.

**2. Sorunun türünü anlamak (*query routing* / sorgu yönlendirme)**

| Yöntem | Nasıl | Artı | Eksi |
|--------|-------|------|------|
| **Arayüzde seçim** | Ekranda sekme veya seçim kutusu: "Ürün standartları" / "Makine" | En güvenilir, hiç tahmin yok | Kullanıcıya bir adım ekler |
| **Kural tabanlı** | Soruda model kodu ("S-7300A"), hata kodu ("E-07") veya "makine, iğne, bobin, ayar, arıza" gibi kelimeler varsa → makine. Marka adı ("Nike") varsa → ürün standardı | Hızlı, açıklanabilir | Her durumu yakalayamaz |
| **LLM ile sınıflandırma** | Soru kısa bir LLM çağrısıyla sınıflandırılır: `{tür: "machine_manual", model: "S-7300A"}` veya `{tür: "product_standard", marka: "Nike", ürün: "ceket"}` | Esnek, karmaşık soruları anlar | Ek gecikme, nadiren yanlış sınıflandırabilir |

Sınıflandırmanın sonucu doğrudan **metadata filtresine** dönüşür:
| Soru | Anlaşılan | Uygulanan filtre |
|------|-----------|------------------|
| "Nike ceketinde dış dikiş SPI kaç olmalı?" | Ürün standardı, Nike, ceket | `doc_type = product_standard AND brand = Nike AND product_category = ceket` |
| "S-7300A'da E-07 hatası ne demek?" | Makine, S-7300A | `doc_type = machine_manual AND product_model = S-7300A` |
| "Dikiş atlıyor, ne yapmalıyım?" | Makine (arıza), model belli değil | `doc_type = machine_manual` → cevapta hangi modelin kılavuzundan geldiği belirtilir, ya da "Hangi makine?" diye sorulur |

**3. Gerçekten belirsiz sorular**

Bazı sorular **iki türü birden** ilgilendirir:
> *"Nike ceketi için dikiş sıklığını makinede nasıl ayarlarım?"*

Bu bir karışıklık değil, aslında **iki kaynaklı bir soru**:
- Standarttan: "Nike ceketinde dış dikiş 11 ± 1 SPI olmalı" (hedef değer)
- Makine kılavuzundan: "Dikiş uzunluğu ayar düğmesiyle ayarlanır, 11 SPI ≈ 2.3 mm dikiş uzunluğu" (nasıl yapılır)

Bu durumda sistem iki türden de arar ve cevapta **iki kaynağı ayrı ayrı** gösterir. Bu, sistemin en değerli kullanım senaryolarından biri olabilir.

Soru belirsiz ve tek kaynaklıysa (örn. sadece "dikiş sıklığı kaç?") sistem kullanıcıya sorar: *"Bir ürün standardındaki değeri mi, makine ayarını mı soruyorsunuz?"*

**4. Tek koleksiyon mu, ayrı koleksiyonlar mı?**

| Seçenek | Nasıl | Ne zaman |
|---------|-------|----------|
| **Tek koleksiyon + `doc_type` filtresi** | Tüm chunk'lar aynı vector DB koleksiyonunda, tür bir metadata alanı | **Önerilen başlangıç.** Basit, iki türden birlikte arama kolay |
| **Ayrı koleksiyonlar** | Standartlar ve makine kılavuzları ayrı koleksiyonlarda | Türler çok farklılaşırsa (farklı chunking, farklı erişim kuralları) |

**Özet:** Karışma riski gerçek, ama metadata'daki **`doc_type` katmanı + sorgu yönlendirme + kaynağı cevapta gösterme** ile yönetilebilir. Test setimize makine kılavuzlarını eklemek bu mekanizmayı **test etmemizi sağlar.** Gerçek veride de büyük ihtimalle birden fazla doküman türü olacak.

#### Kavram: Bounding box (bbox)

**Evet, genel anlamıyla aynı kavram:** Bir alanı çevreleyen dikdörtgen kutu. Görüntü işlemede bir nesnenin (araba, yüz) etrafına çizilen kutu neyse, bizde de **PDF sayfasındaki bir metin parçasının etrafına çizilen kutudur.**

**Dört sayıyla tanımlanır:** `[x0, y0, x1, y1]` → sol-üst köşe ve sağ-alt köşe.
```
 Sayfa 12 (595 × 842 pt, A4)
 (0,0) ┌───────────────────────────────────────┐
       │  3. DİKİŞ STANDARTLARI                │
       │                                       │
       │  (72,210) ┌─────────────────────────┐ │
       │           │ 3.2 Stitch Density      │ │  ← chunk'ın bbox'ı
       │           │ Stitch density shall be │ │     [72, 210, 523, 268]
       │           │ 8-10 SPI for all ...    │ │
       │           └─────────────────────────┘ │
       │                          (523,268)    │
       │  [Şekil 3: Dikiş tipleri]             │
       └───────────────────────────────────────┘ (595,842)
```

**Bizim projede ne işe yarıyor?** Cevabın geldiği metni sayfa görüntüsü üzerinde **vurgulamak** (sarı kutu / çerçeve) için. Kullanıcı sayfanın tamamını okumadan bilginin tam yerini görür. Halüsinasyona karşı önlemlerden biri de bu (bkz. S11, Katman 6).

**Bilinmesi gerekenler:**
| Konu | Açıklama |
|------|----------|
| **Birim** | PDF koordinatları **point** cinsindendir (1 pt = 1/72 inç). A4 sayfa ≈ 595 × 842 pt. |
| **Orijin** | PDF standardında (0,0) **sol-alt** köşedir. Bazı kütüphaneler (örn. PyMuPDF) bunu **sol-üst** köşeye çevirir. Hangi kütüphane kullanılıyorsa ona göre hesaplanmalı, yoksa kutu yanlış yere çizilir. |
| **Görsele çizerken ölçekleme** | Sayfa PNG'ye çevrilirken (örn. 150 DPI) koordinatlar ölçeklenir: `piksel = pt × (DPI / 72)`. |
| **Detay seviyesi** | Parser'lar kelime, satır veya blok (paragraf) seviyesinde bbox verebilir. Highlight için genelde **satır veya blok** seviyesi yeterli. |
| **Bir chunk = birden çok kutu** | Bir chunk birkaç paragraf veya iki sayfa olabilir. Bu yüzden tek kutu değil, sayfa bilgili **kutu listesi** tutulur (yukarıdaki JSON'daki `bboxes`). Tek büyük kutu, aradaki alakasız şekli de kapsayabilir. |
| **Taranmış PDF** | Metin katmanı yoktur. bbox'ı **OCR** üretir (her tanınan kelime için kutu verir). |

**bbox'ı nereden alıyoruz?** PDF parser'dan (Adım 2.6). Örn. PyMuPDF `page.get_text("dict")` her blok/satır/kelime için koordinat döndürür. Docling, Unstructured gibi araçlar da öğe başına bbox verir.

### Proje için ilk öneri


| Bileşen | Öneri (pilot) | Alternatif | Gerekçe |
|---------|---------------|------------|---------|
| Chunking | Başlık/bölüm bazlı + sayfa/bbox metadata, tablolar bütün | Recursive (300–600 token) | Manuallerde yapı belirgin, sayfa izlenebilirliği şart |
| Embedding | `bge-m3` (lokal) | `multilingual-e5-large`, bulut API (izin varsa) | Çok dilli, lokal, hybrid için sparse vektör de üretiyor |
| Vector DB | **Qdrant** | Chroma (sadece hızlı deneme), pgvector | Güçlü metadata filtresi + yerleşik hybrid + Docker ile kolay |
| Arama | Hybrid: dense + sparse, RRF ile birleştirme. Sparse tarafı için **BM25 (TR/EN stemming)** ve **BGE-M3 sparse** deneyle karşılaştırılacak | Sadece vektör | Standart numaraları ve kodlar çok geçiyor |
| Reranker | `bge-reranker-v2-m3` | Cohere Rerank | Çok dilli, lokal |
| Filtre | Arayüzde marka seçimi + sorudan otomatik çıkarım | Sadece LLM çıkarımı | Yanlış marka riski en düşük |
| top-k | Aday: 30 → LLM'e: 3–5 | | Kalite / gecikme dengesi |

**Doğrulanacaklar:**
> ⏸️ **Ertelendi → Pilot / prototip aşaması.** Bu deneyler için gerçek manuellerin parse edilip chunk'lanmış olması (Adım 2) ve test soru setinin (Adım 0.4) hazır olması gerekiyor. Araştırma aşamasında yapılamaz. [req.md, Faz 6](../req.md) içinde takip ediliyor.

- [ ] `bge-m3` Türkçe soru ↔ İngilizce manual eşleşmesinde yeterli mi? (test seti ile)
- [ ] Hybrid, sadece vektör aramaya göre ne kadar fark yaratıyor? (Recall@5 karşılaştırması)
- [ ] Sparse tarafında BM25 mi, BGE-M3 sparse mı, ikisi birden mi? (1.5'teki A–D deneyi)
- [ ] Türkçe chunk'larda hangi kök bulucu (Zemberek / Snowball / prefix-5)?
- [ ] Reranker'ın gecikme etkisi kabul edilebilir mi?

---

## Kaynaklar

- [MTEB Leaderboard](https://huggingface.co/spaces/mteb/leaderboard): embedding model karşılaştırması
- [BGE-M3 model kartı](https://huggingface.co/BAAI/bge-m3)
- [Qdrant: Hybrid search dokümantasyonu](https://qdrant.tech/documentation/concepts/hybrid-queries/)
- [Lost in the Middle (makale)](https://arxiv.org/abs/2307.03172): uzun bağlamda ortadaki bilginin kaçırılması
- [Comparing SPLADE Sparse Vectors with BM25 (Zilliz)](https://zilliz.com/learn/comparing-splade-sparse-vectors-with-bm25)
- [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined](https://blog.premai.io/hybrid-search-for-rag-bm25-splade-and-vector-search-combined): RRF k=60 ile başlama önerisi
- [Milco: Learned Sparse Retrieval Across Languages](https://arxiv.org/pdf/2510.00671): çok dilli learned sparse
- [Qdrant BM42 makalesi](https://qdrant.tech/articles/bm42/) ve [bm42_eval deposu](https://github.com/qdrant/bm42_eval): BM42 ve tartışmalı değerlendirmesi
- [Haystack: BM42 hybrid retrieval cookbook](https://haystack.deepset.ai/cookbook/hybrid_retrieval_bm42/): BM42 hakkındaki uyarı notu
- [Turkish Text Retrieval Experiments Using Lemur Toolkit](https://arxiv.org/pdf/1405.1740): Türkçede stemming etkisi
- [First large-scale IR experiments on Turkish texts (Bilkent)](https://repository.bilkent.edu.tr/items/4ed9cb10-6abb-4530-8b35-cbec3bd72cc3/full): prefix-5 ve lemmatizer karşılaştırması
