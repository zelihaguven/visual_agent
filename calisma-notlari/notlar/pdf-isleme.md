# Manual / PDF İşleme (Adım 2)


> **Başlangıç:** 2026-10-08
> **İlgili plan:** [req.md, Adım 2](../req.md) · Önceki adım: [rag-temelleri.md](rag-temelleri.md) · Test seti: [manual-envanteri.md](manual-envanteri.md)

Bu konuda ön bilgi olmadığı için bu doküman **önce anlatım, sonra kontrol soruları** şeklinde ilerliyor (rag-temelleri.md'deki sıranın tersi).

---

## 1. Önce büyük resim: Bu adım neden önemli?

RAG hattının ilk adımı PDF'ten metni çıkarmak (**parsing**). Buradaki her hata zincirleme büyür:

```
PDF ──► Parsing ──► Chunking ──► Embedding ──► Arama ──► LLM ──► Cevap
         ▲
         └── Burada tablo bozulursa, sayı kaybolursa, okuma sırası karışırsa
             sonraki hiçbir adım bunu düzeltemez. LLM bozuk metne dayanarak
             yanlış değer söyler (bkz. rag-temelleri.md, S11 → halüsinasyon riski).
```

> **"Çöp girerse çöp çıkar"** (*garbage in, garbage out*). RAG projelerinde kalite sorunlarının büyük kısmı parsing'den çıkar.

### Kavram: Ingestion nedir?

**Kelime anlamı:** *Ingestion* = "yutma, içeri alma". Veri sistemlerinde **dışarıdaki ham verinin sisteme alınıp kullanılabilir hale getirilmesi** anlamına gelir. Türkçe metinlerde genelde "veri alımı" veya "doküman yükleme hattı" denir.

**RAG'de ingestion:** Bir PDF'in ham dosya halinden **aranabilir chunk'lar** haline gelene kadar geçirdiği adımların tamamı. rag-temelleri.md 1.1'de "INDEXLEME hattı" dediğimiz şey budur.

```
INGESTION HATTI (doküman eklendiğinde / güncellendiğinde çalışır)
┌─────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐
│ Yükleme │→ │ Tür      │→ │ Parsing      │→ │ Temizlik │→ │ Metadata │→ │ Chunking │→ │ Embedding │→ Vector DB
│ (PDF)   │  │ tespiti  │  │ (+ OCR)      │  │          │  │ ekleme   │  │          │  │ + kayıt   │
└─────────┘  └──────────┘  └──────────────┘  └──────────┘  └──────────┘  └──────────┘  └───────────┘
                └──────────── Adım 2 (bu doküman) ───────────┘              └──── Adım 1 ────┘

SORGU HATTI (her soruda çalışır)
Soru → Embedding → Arama → Reranker → LLM → Cevap + sayfa
```

**İki hattın farkı:**
| | **Ingestion** | **Sorgu (retrieval + generation)** |
|---|---|---|
| Ne zaman çalışır | Doküman eklenince, güncellenince, silinince | Kullanıcı her soru sorduğunda |
| Kullanıcı bekler mi | Hayır, arka planda çalışır (*offline*) | Evet, saniyeler içinde cevap gerekir (*online*) |
| Hız önemi | Düşük. Bir manuel dakikalar sürebilir | Yüksek |
| Kalite önemi | **Çok yüksek.** Burada kaybolan bilgi sorguda geri gelmez | Yüksek |
| Pahalı adımlar | OCR, VLM ile şekil açıklaması, embedding | Reranker, LLM |

> Bu yüzden pahalı ve yavaş ama kaliteli yöntemler (OCR, VLM açıklaması) **ingestion'a** konur. Bir kez yapılır, her soruda tekrar kullanılır.

**Ingestion ne zaman tekrar çalışır?**
| Durum | Yapılan |
|-------|---------|
| Yeni manuel geldi | Tüm hat çalışır, chunk'lar eklenir |
| Manuelin yeni versiyonu geldi | Yeni versiyon işlenir, eskisi `is_latest = false` yapılır veya silinir (`doc_id` ile) |
| Aynı dosya tekrar yüklendi | `file_hash` aynıysa atlanır (gereksiz maliyet olmasın) |
| Embedding modeli veya chunking stratejisi değişti | **Tüm dokümanlar baştan işlenir** (*re-ingestion / re-indexing*) |

**İyi bir ingestion hattının özellikleri:**
- **Tekrarlanabilir:** Aynı dosya iki kez işlenince aynı sonuç çıkar, kopya chunk oluşmaz.
- **Kayıt tutar (log):** Hangi doküman ne zaman işlendi, hangi sayfada OCR'a düştü, hangi sayfada hata oldu.
- **Hatayı sessiz geçmez:** Metin çıkmayan sayfa, boş tablo, düşük OCR güveni raporlanır (bkz. K1, K3).

Bizim için ayrıca iki ek görev var: her metin parçasının **sayfa numarasını** ve **sayfa üzerindeki konumunu (bbox)** da çıkarmak. Yoksa sayfayı gösterip vurgulayamayız.

---

## 2. PDF neden zor bir format?

**PDF bir "baskı" formatıdır, "metin" formatı değildir.** Word dosyası "bu bir başlık, bu bir paragraf, bu bir tablo" bilgisini tutar. PDF ise sadece şunu tutar: *"Şu karakteri, şu fontla, sayfanın şu koordinatına çiz."*

```
Ekranda gördüğümüz:              PDF'in içinde aslında olan:
┌──────────────────────┐         "S"  x=72  y=210  font=Arial-Bold 11pt
│ 3.2 Stitch Density   │         "t"  x=79  y=210  ...
│ Stitches shall be    │         "i"  x=83  y=210  ...
│ 11 (± 1) per inch.   │         ...
└──────────────────────┘         (paragraf, başlık, tablo bilgisi YOK)
```

Bu yüzden bir parser şunları **tahmin etmek** zorundadır:
- Hangi karakterler bir kelime, hangi kelimeler bir satır, hangi satırlar bir paragraf?
- Okuma sırası ne? (Sol kolon bitince sağ kolona mı geçiliyor?)
- Bu yazı başlık mı, gövde mi, sayfa altbilgisi mi?
- Bu çizgiler ve sayılar bir **tablo** mu? Hangi hücre hangi satıra ve sütuna ait?

---

## 3. PDF türleri

| Tür | Nasıl oluşur | İçinde metin var mı? | Nasıl anlaşılır | Test setimizde |
|-----|--------------|----------------------|-----------------|----------------|
| **Dijital** (*born-digital*) | Word/InDesign vb. programdan "PDF olarak kaydet" | ✅ Var | Metin fareyle seçilip kopyalanabiliyor | GL-PD-14-04A (ceket) |
| **Taranmış** (*scanned*) | Kağıt doküman tarayıcıdan geçirilmiş | ❌ Yok, her sayfa bir **fotoğraf** | Metin seçilemiyor, yakınlaştırınca pikseller görünüyor | GL-PD-07-14A (pantolon) |
| **Taranmış + OCR katmanlı** | Taranmış ama üstüne görünmez bir OCR metni eklenmiş | 🟡 Var ama hatalı olabilir | Metin seçilebiliyor ama kopyalanınca bozuk karakterler çıkabiliyor | Kontrol edilecek |
| **Görsel ağırlıklı** | Sunum, broşür, katalog | 🟡 Az. Bilgi büyük oranda **çizimlerde** | Metin kısa etiketlerden ibaret | Stitch Guide |

> **Önemli:** Taranmış PDF'te parser "metin çıkar" dediğinde **boş sonuç** döner, çünkü ortada metin yoktur, sadece resim vardır. Bu durumda **OCR** gerekir (bkz. 2.4).

---

## 4. Tipik zorluklar ve sonuçları

| Zorluk | Ne oluyor | Bizim için sonucu | Örnek |
|--------|-----------|-------------------|-------|
| **Tablolar** | Basit parser tabloyu satır satır düz metne döker, hücre-sütun ilişkisi kaybolur | "Yan dikiş → 301 → 11 SPI" ilişkisi kopar, LLM yanlış satırın değerini okur | Şartnamelerdeki dikiş operasyon tablosu |
| **Çok kolonlu sayfa** | Okuma sırası karışır: sol kolonun 1. satırı + sağ kolonun 1. satırı birleşir | Anlamsız cümleler, yanlış chunk | Broşür ve dergi düzenleri |
| **Üst / alt bilgi** | "GL-PD-14-04A, Page 12" her sayfada tekrar eder | Chunk'ları kirletir, aramada gürültü | Tüm şartnameler |
| **Sayfayı aşan tablo** | Tablo iki sayfaya bölünür, başlık satırı sadece ilk sayfada kalır | İkinci sayfadaki satırların hangi sütuna ait olduğu bilinmez | Uzun dikiş tabloları |
| **Şekiller / çizimler** | Parser resmi atlar veya sadece "[resim]" yazar | Çizimdeki bilgi tamamen kaybolur | Stitch Guide'daki dikiş çizimleri |
| **Özel karakterler** | "±", "½", "°" yanlış çıkabilir | "11 (± 1)" yerine "11 ( 1)" → **değer değişir** | SPI toleransları |
| **Satır sonu tirelemesi** | "stitch-" / "ing" ikiye bölünür | Kelime araması bulamaz | Uzun metinler |
| **OCR ( Optical Character Recognition ) hataları** | "1" ↔ "l", "0" ↔ "O", "5" ↔ "S" karışır | **Sayısal değer bozulur**, yanlış dikime yol açabilir | Taranmış pantolon şartnamesi |

> Sayı ve tolerans hataları doğrudan yanlış dikim demek. Parsing kalitesini ölçerken sayıların doğru çıkıp çıkmadığına özellikle bakılmalı.

---

## 5. Parsing yaklaşımları (basitten gelişmişe)

| Seviye | Nasıl çalışır | Artı | Eksi | Örnek araçlar |
|--------|---------------|------|------|---------------|
| **1. Düz metin çıkarma** | PDF'teki karakterleri sırayla okur | Çok hızlı, kurulumu kolay | Tablo, kolon, başlık yapısını bilmez. Taranmışta boş döner | `pypdf`, PyMuPDF (temel mod) |
| **2. Layout-aware (düzen farkında)** | Sayfayı bir görüntü gibi analiz eden bir model başlık/paragraf/tablo/şekil bölgelerini bulur, sonra her bölgeyi uygun yöntemle okur | Tablo yapısını, okuma sırasını, başlık hiyerarşisini korur. bbox verir | Daha yavaş, model indirir (GB'larca) | **Docling**, Marker, MinerU, Unstructured |
| **3. VLM tabanlı** (görsel dil modeli) | Sayfanın **resmini** bir multimodal LLM'e verip "bunu Markdown'a çevir" denir | Karmaşık tablolarda ve çizimlerde en iyi sonuç. Taranmışı da okur | Pahalı, yavaş, **uydurma riski** var (okumadığı sayıyı tahmin edebilir). Bulut ise veri dışarı gider | LlamaParse, GPT/Claude/Gemini vision, Mistral OCR |

**Çıktı formatı:** Gelişmiş araçlar genelde **Markdown** (başlıklar `#`, tablolar `| ... |`) veya **JSON** (her öğe için tür + metin + sayfa + bbox) üretir. Bizim için **JSON tarzı yapılandırılmış çıktı** daha önemli, çünkü sayfa ve bbox bilgisini taşır.

```
Layout-aware parser'ın gördüğü sayfa:
┌────────────────────────────────────┐
│ [başlık]   3. SEWING REQUIREMENTS  │
│ [paragraf] All seams shall be...   │
│ [tablo]    ┌─────┬──────┬──────┐   │
│            │ Op. │Stitch│ SPI  │   │
│            ├─────┼──────┼──────┤   │
│            │ Side│ 301  │ 11±1 │   │
│            └─────┴──────┴──────┘   │
│ [şekil]    (çizim)                 │
│ [altbilgi] Page 12 ← atılabilir    │
└────────────────────────────────────┘
Her bölge için: tür + metin + sayfa no + bbox
```

---

### 5.1 Bu yaklaşımlar 4. bölümdeki sorunların hepsini çözüyor mu?

**Hayır.** Hiçbir yaklaşım tek başına hepsini çözmüyor. Layout-aware parser'lar (seviye 2) sorunların **çoğunu** çözüyor, kalanlar için parsing'den sonra **ek adımlar** gerekiyor.

✅ çözer · 🟡 kısmen / araca göre değişir · ❌ çözmez

| Sorun (4. bölüm) | 1. Düz metin | 2. Layout-aware | 3. VLM | Kalan açık ve ek çözüm |
|------------------|:---:|:---:|:---:|------------------------|
| **Tablolar** | ❌ | ✅ Çizgili ve basit tablolarda iyi. Birleşik hücrelerde hata yapabilir | ✅ En iyisi | VLM tablo değerini **uydurabilir**. Tablo çıktısı test setinde elle kontrol edilmeli. Tablo bölünmeden tek chunk yapılmalı |
| **Çok kolonlu sayfa** | ❌ | ✅ | ✅ | Genelde çözülüyor. Çok karışık sayfalarda okuma sırası yine kontrol edilmeli |
| **Üst / alt bilgi** | ❌ | 🟡 Bazı araçlar "sayfa başlığı/altbilgisi" diye etiketler | 🟡 | **Kural tabanlı temizlik:** Her sayfada aynı yerde tekrar eden satırları at |
| **Sayfayı aşan tablo** | ❌ | 🟡 MinerU birleştiriyor, Docling birleştirmiyor | ❌ Genelde sayfa sayfa çalışır | **Birleştirme adımı:** Sayfa sonundaki tablo ile sonraki sayfanın başındaki tablonun sütun sayısı aynıysa birleştir, başlık satırını ikinci parçaya da ekle |
| **Şekiller / çizimler** | ❌ | 🟡 Şekli bulur ve kırpar, ama **içindeki bilgiyi okumaz** | ✅ Çizimi açıklayabilir | **VLM ile şekil açıklaması** (bkz. 7. bölüm, "Şekiller ve çizimler") veya görsel tabanlı retrieval (Adım 3.4). Açıklama yanlış olabilir |
| **Özel karakterler** (±, ½, °) | 🟡 Dijitalde çoğunlukla doğru, font kodlamasına bağlı | 🟡 Aynı | 🟡 | **Doğrulama:** Örnek sayfalarda "±" gibi karakterlerin doğru çıktığı kontrol edilmeli. Taranmışta OCR riskine dönüşür |
| **Satır sonu tirelemesi** | ❌ | 🟡 | ✅ | **Basit kural:** Satır "-" ile bitiyor ve sonraki satır küçük harfle başlıyorsa birleştir |
| **OCR hataları** (1↔l, 0↔O) | ❌ Taranmışta zaten metin yok | 🟡 Kullandığı OCR motoru kadar iyi | 🟡 Daha iyi okur, ama okuyamadığını **tahmin edebilir** | **Tamamen çözen yöntem yok.** Ek önlemler: OCR güven skorunu metadata'da tutmak, düşük güvenli sayılarda uyarı vermek, iki farklı OCR'ın sonucunu karşılaştırmak, kritik tabloları insan kontrolünden geçirmek |

**Sonuç:**
1. **Seviye 2 (layout-aware) temel olarak yeterli.** Tablo, kolon ve okuma sırası sorunlarının çoğunu çözüyor.
2. **Parsing sonrası bir "temizlik" adımı şart:** Üst/alt bilgi silme, tireleme birleştirme, sayfayı aşan tabloları birleştirme. Bunlar basit kurallarla yapılabilir.
3. **Şekiller için ayrı bir çözüm gerekiyor:** VLM açıklaması veya görsel tabanlı retrieval.
4. **OCR ve sayı hataları hiçbir zaman sıfıra inmiyor.** Bu yüzden asıl güvence, cevapla birlikte **orijinal sayfanın gösterilmesi** ve kullanıcının değeri kaynağında görebilmesi (bkz. rag-temelleri.md, S11, Katman 6).

Bu ek adımlar 7. bölümdeki "Önerilen ingestion hattı"nda "Temizlik" ve "Şekiller" adımları olarak yer alıyor.

---

## 6. Kontrol soruları

> Anlatımın oturduğunu görmek için. Kısa cevaplar yeterli, bilmediğine "bilmiyorum" yaz.

**K1.** Ceket şartnamesinden (dijital) ve pantolon şartnamesinden (taranmış) aynı basit kodla metin çıkarmaya çalışırsak ne olur? Neden?
> **C:** Taranmış olanda görsel olduğu, metin olmadığı için resim olarak gözükür sadece.

**Değerlendirme:** ✅ Doğru, temel fikir bu. Tamamlayıcı noktalar:
- **Ceket (dijital):** Metin çıkar, ama basit kod düzeni bilmediği için tablolar ve başlıklar düz metne dönüşür.
- **Pantolon (taranmış):** Kod **hata vermez, sessizce boş metin döner** (ya da sadece birkaç boşluk). Tehlikesi şu: Kimse fark etmezse doküman sistemde "yüklenmiş" görünür, ama içinden hiçbir şey aranamaz. Kullanıcı soru sorduğunda sistem "bulunamadı" der ya da başka dokümandan cevap verir.
- **Çözüm:** Her sayfa için çıkan metin uzunluğu kontrol edilir. Metin yok veya çok azsa sayfa otomatik olarak OCR'a gönderilir (7. bölümdeki ingestion hattının ilk adımı).

**K2.** Bir tablo düz metne dökülürse "yan dikişin SPI değeri nedir?" sorusunda ne gibi bir sorun çıkabilir?
> **C:** Cevaplanmış şekilde olmaz, "yan dikiş + 12 SPI" gibi bir şey olabilir. Dümdüz metin haline gelir, ilişkiler kaybolur.

**Değerlendirme:** ✅ Doğru, "ilişkiler kaybolur" tam olarak sorunun özü. Bir örnekle:
```
Orijinal tablo:                     Düz metne dökülmüş hali:
┌─────────────┬────────┬──────┐     "Operation Stitch SPI Side seam Sleeve seam
│ Operation   │ Stitch │ SPI  │      Hem 301 401 504 11 ± 1 8-10 6-8"
├─────────────┼────────┼──────┤
│ Side seam   │ 301    │ 11±1 │     → "Side seam"in değeri 11 ± 1 mi, 8-10 mu?
│ Sleeve seam │ 401    │ 8-10 │       Sütunlar satır satır değil, karışık
│ Hem         │ 504    │ 6-8  │       sırayla çıkabilir.
└─────────────┴────────┴──────┘
```
- LLM bu metinden **yanlış satırın değerini** okuyabilir ve bunu emin bir dille söyler. Hata cevaptan anlaşılmaz.
- **Çözüm:** Tablo yapısını koruyan bir parser (layout-aware), tabloyu bölmeden tek chunk yapmak ve tabloyu Markdown olarak ya da her satırı başlıklarıyla birlikte ("Side seam: stitch 301, SPI 11 ± 1") saklamak.

**K3.** OCR'ın "11 (± 1)" ifadesini "11 (+ 1)" veya "ll (± l)" olarak okuması bizim projede neden özellikle tehlikeli?
> **C:** Çünkü cm/mm hesap hatalarına sebebiyet verir ve yanlış dikim yapılır.

**Değerlendirme:** 🟡 Sonuç doğru (yanlış dikim), ama sebep cm/mm hesabı değil. SPI zaten "inç başına dikiş sayısı", birim dönüşümü gerektirmiyor. Asıl tehlikeler:
- **"11 (± 1)" → "11 (+ 1)":** Anlam değişir. Doğrusu 10–12 aralığı, hatalı okumada 11–12 olur. Alt sınır kaybolur. 10 SPI ile dikilmiş doğru bir ürün hatalı sayılabilir ya da tersi.
- **"11 (± 1)" → "ll (± l)":** Artık sayı değil **harf**. Kelime araması "11" diye aranınca bu chunk'ı bulamaz. LLM "ll" ifadesini görünce değeri **tahmin etmeye** çalışabilir.
- **En tehlikeli yanı, hatanın sessiz olması:** Bozuk değer makul görünür ve kimse fark etmez. Otomatik doğrulama da yakalayamaz: rag-temelleri.md S11'deki "cevaptaki sayı kaynakta var mı?" kontrolü geçer, çünkü **kaynak metnin kendisi bozuk.**
- **Bu yüzden:** Taranmış dokümanlarda kullanıcıya her zaman **orijinal sayfa görüntüsü** gösterilmeli (OCR metni değil). Düşük OCR güven skoru olan sayılarda uyarı verilmeli.

**K4.** Stitch Guide'daki bilgi çoğunlukla çizimlerde. Sadece metin çıkaran bir parser kullanırsak bu dokümandan RAG'e ne kalır? Sence nasıl çözebiliriz?
> **C:** Sadece dümdüz açıklama metinleri kalır ama hiçbir bağlam ifade etmez. 

**Değerlendirme:** 🟡 İlk kısım ✅ doğru: Geriye "301 Lockstitch", "Fig. 3" gibi kısa etiketler kalır, çizimin anlattığı (ipliğin nasıl geçtiği, dikişin üstten/alttan görünüşü) kaybolur. İkinci kısım eksik: **Hiçbir parser çizimi tek başına metne çevirmez.** Layout-aware parser bile sadece şeklin yerini bulup kırpar, içindeki bilgiyi okumaz. Çözüm  parsing'e eklenen **ayrı bir adım**:
1. **Şekil başlığı ve çevresindeki metni** chunk'a eklemek (en basit, ama yetersiz).
2. **VLM ile şekil açıklaması:** Kırpılan her çizim görsel bir LLM'e verilir ("Bu dikiş çizimini ayrıntılı açıkla"), açıklama metin olarak indekslenir. Açıklama yanlış olabilir, kontrol gerekir.
3. **Görsel tabanlı retrieval** (ColPali vb.): Sayfa resim olarak aranır, metne çevrilmez (Adım 3.4).
4. **Cevapta sayfa görüntüsünü göstermek:** Zaten sistemimizin parçası. Kullanıcı çizimi kendi gözüyle görür.

**K5.** VLM (görsel LLM) ile parsing en iyi sonucu veriyorsa, neden her şeyi onunla yapmıyoruz?
> **C:** Halüsinasyon.

**Değerlendirme:** 🟡 Doğru ve bizim için **en önemli** sebep bu: VLM okuyamadığı bir sayıyı tahmin edip yazabilir, üstelik normal parser'ın aksine "okuyamadım" demez. Ama tek sebep değil:
| Sebep | Açıklama |
|-------|----------|
| **Halüsinasyon** | Okuyamadığını uydurabilir (senin cevabın) |
| **Maliyet** | Sayfa başına ücret. Binlerce sayfalık manuel arşivinde ve her güncellemede tekrar ödenir |
| **Hız** | Sayfa başına saniyeler. Layout-aware parser çok daha hızlı |
| **Gizlilik** | Çoğu güçlü VLM bulutta. Müşteri manuelleri dışarı gider (req.md Q1). Lokal çalıştırmak güçlü GPU ister |
| **bbox** | Genelde metnin sayfadaki **koordinatını vermez** veya zayıf verir. Sayfada vurgulama yapamayız, bu bizim için kritik bir eksik |
| **Tekrarlanabilirlik** | Aynı sayfayı iki kez verince farklı çıktı üretebilir. Test ve hata ayıklama zorlaşır |

**Pratikte:** Hibrit yaklaşım. Varsayılan olarak layout-aware parser (Docling) kullanılır, VLM **sadece zor sayfalarda** (çizimler, karmaşık tablolar) devreye girer. VLM'in çıkardığı sayılar mümkünse OCR çıktısıyla karşılaştırılır.

---

### Kontrol soruları özeti

| Soru | Sonuç | Not |
|------|-------|-----|
| K1 | ✅ | Taranmışta metin yok. Ek: hata sessiz olur, sayfa bazlı kontrol gerekir |
| K2 | ✅ | İlişkiler kaybolur. Ek: tablo bütün ve yapılı saklanmalı |
| K3 | 🟡 | Sonuç doğru, sebep cm/mm değil: aralık değişir, sayı harfe döner, hata sessizdir |
| K4 | 🟡 | Çizim bilgisi kaybolur ✅. Çözüm parser değiştirmek değil, ek adım (VLM açıklaması, ColPali) |
| K5 | 🟡 | Halüsinasyon ✅. Ek: maliyet, hız, gizlilik, bbox eksikliği, tekrarlanabilirlik |

**Genel:** Konunun ana fikirleri oturmuş. Tamamlanan iki önemli nokta: (1) parsing hataları **sessizdir**, bu yüzden kontrol ve kaynak gösterimi şart; (2) çizimler için parser yetmez, **ayrı bir adım** gerekir.

---

## 7. Derlenmiş Notlar

### 2.1 Manual envanteri

Test seti seçildi: [manual-envanteri.md](manual-envanteri.md).

| Doküman | Tür | Parsing zorluğu |
|---------|-----|-----------------|
| GL-PD-14-04A (ceket) | Dijital, ~56 sf. | Tablolar, üst/alt bilgi, sayfa aşan tablolar olabilir |
| GL-PD-07-14A (pantolon) | **Taranmış**, ~48 sf. | **OCR şart.** Taranmış tablolar, sayı hataları riski |
| Strickland terzilik kitabı | Taranmış + OCR katmanlı, iki kolonlu, 164 sf. | Okuma sırası, kesirli ölçülerde OCR hatası, çizimler |
| Brother / Mr. Coffee / Bosch kılavuzları | Dijital, çizimli talimatlar, parça listeleri | Çizime atıf yapan talimatlar, kitapçık düzeni, çok dilli bölümler |

### 2.2 PDF parsing araçları

| Araç | Tür | Tablo | OCR | bbox | Lisans | Not |
|------|-----|-------|-----|------|--------|-----|
| **pypdf** | Düz metin | ❌ | ❌ | ❌ | BSD (serbest) | Sadece hızlı kontrol için |
| **pdfplumber** | Düz metin + tablo kuralları | 🟡 Çizgili tablolarda iyi | ❌ | ✅ Karakter seviyesinde | MIT | Çizgili, basit tablolarda başarılı |
| **PyMuPDF** (+ `pymupdf4llm`) | Düz metin → Markdown | 🟡 | 🟡 Tesseract ile | ✅ Çok detaylı | ⚠️ **AGPL** veya ücretli ticari lisans | Çok hızlı. **Sayfayı PNG'ye çevirme ve vurgulama** için de kullanılır (Adım 3). Lisansı ticari kullanımda sorun çıkarabilir |
| **Docling** (IBM) | Layout-aware | ✅ TableFormer modeli | ✅ EasyOCR / Tesseract / RapidOCR | ✅ | **MIT** | Lokal çalışır, CPU'da da olur. Sayfayı aşan tabloları birleştirmiyor (iki ayrı tablo verir) |
| **Marker** | Layout-aware (+ isteğe bağlı LLM) | ✅ | ✅ Surya OCR | ✅ | Kod Apache 2.0, **model ağırlıkları ayrı lisans** | Doğruluk kritikse LLM desteği açılabilir |
| **MinerU** | Layout-aware | ✅ Sayfa aşan tabloyu birleştirir | ✅ | ✅ | Apache 2.0 tabanlı özel lisans | Formül ve Çince/Japonca dokümanlarda güçlü. Büyük modeller indirir |
| **Unstructured** | Layout-aware | ✅ | ✅ | ✅ | Apache 2.0 (açık kaynak sürüm) | Çok format destekler (PDF, Word, HTML) |
| **LlamaParse** | VLM tabanlı, bulut | ✅ Birleşik/iç içe hücreler dahil | ✅ | 🟡 | Ücretli servis | Veri buluta gider |
| **Azure Document Intelligence / AWS Textract / Google Document AI** | Bulut OCR + layout | ✅ | ✅ Çok güçlü | ✅ | Ücretli servis | Taranmış dokümanlarda endüstri standardı. Veri buluta gider |

>  Lisans bilgileri değişebilir. Kesin seçimden önce resmi sayfalardan doğrulanmalı. Test aşamasında public veri kullandığımız için bulut servisleri de rahatça denenebilir. Gerçek veriye geçerken gizlilik kararı (Q1) belirleyici olacak.

**Genel tavsiye (kaynaklarda ortak görüş):** Bir parser'ın temiz raporlarda iyi çıkması, bizim dokümanlarımızda da iyi çıkacağı anlamına gelmez. **Karar kendi en zor sayfalarımızda yapılan denemeyle verilir.**

### 2.3 Araç denemesi


**Deney planı:**
1. Her dokümandan **en zor 2–3 sayfa** seçilir: dikiş tablosu olan sayfa, taranmış tablo, çizimli slayt.
2. Aday araçlar: **Docling**, **PyMuPDF4LLM**, **Marker** (+ karşılaştırma için bir bulut servis: Azure DI veya LlamaParse).
3. Her çıktı elle kontrol edilir:

| Ölçüt | Soru |
|-------|------|
| Metin doğruluğu | Kelimeler ve **sayılar** doğru mu? ("11 (± 1)", "52-56") |
| Tablo yapısı | Satır-sütun ilişkisi korunmuş mu? |
| Okuma sırası | Paragraflar doğru sırada mı? |
| Başlık hiyerarşisi | "3. → 3.2" yapısı çıkmış mı? (Chunking için gerekli) |
| Sayfa + bbox | Her öğe için sayfa no ve koordinat var mı? |
| Hız | Sayfa başına süre |
| Gürültü | Üst/alt bilgi ayıklanmış mı? |

### 2.4 OCR ihtiyacı

**OCR (Optical Character Recognition, optik karakter tanıma):** Bir **görüntüdeki** yazıyı makinenin okuyabileceği **metne** çeviren teknoloji.

```
Taranmış sayfa (resim) ──► OCR ──► "Stitches shall be 10-14 per inch"
                                   + her kelimenin bbox'ı
                                   + her kelimenin güven skoru (0.97, 0.62 ...)
```

**Nasıl çalışır (basitçe):**
1. **Ön işleme:** Görüntü düzeltilir (eğiklik giderme, kontrast, gürültü temizleme).
2. **Metin bölgesi tespiti:** Sayfada yazı olan alanlar bulunur.
3. **Tanıma:** Her bölgedeki karakterler/kelimeler bir modelle okunur.
4. **Çıktı:** Metin + konum (bbox) + **güven skoru**.

**Güven skoru neden önemli:** OCR emin olmadığı kelimeleri düşük skorla işaretler. Bunu metadata'da (`ocr_confidence`) tutarsak, düşük güvenli bir sayıya dayanan cevapta kullanıcıyı uyarabiliriz (bkz. rag-temelleri.md, S11).

**OCR kalitesini etkileyenler:** Tarama çözünürlüğü (en az 300 DPI önerilir; pantolon şartnamesi 300 DPI görünüyor ✅), eğik tarama, leke/gölge, küçük font, tablo çizgileri, el yazısı.

**Seçenekler:**
| Araç | Tür | Not |
|------|-----|-----|
| **Tesseract** | Açık kaynak, klasik | Yaygın, ücretsiz. Tablolarda zayıf |
| **EasyOCR / RapidOCR / PaddleOCR** | Açık kaynak, derin öğrenme | Tesseract'tan genelde daha iyi. Docling içinden kullanılabilir |
| **Surya** | Açık kaynak, derin öğrenme | Marker'ın OCR motoru, layout tespiti de yapar |
| **VLM tabanlı OCR** (Mistral OCR, GPT/Claude/Gemini vision) | Bulut / büyük model | Tablolarda çok iyi. Ama okuyamadığı yeri **tahmin edip uydurabilir**, sayılarda dikkat |
| **Azure DI / AWS Textract / Google Document AI** | Bulut | Taranmış tablolarda en güçlü seçeneklerden |

**Bizim karar noktamız:** Taranmış pantolon şartnamesi gerçek manuellerimizde taranmış doküman olup olmadığına dair bir **vekil**. Gerçek veride taranmış manuel oranı (req.md, Q3) bu adımın ne kadar önemli olduğunu belirleyecek.

### Şekiller ve çizimler 

Metin parser'ları çizimdeki bilgiyi okuyamaz. Üç yaklaşım var:

| Yaklaşım | Nasıl | Artı | Eksi |
|----------|-------|------|------|
| **Başlık / etiket kullanmak** | Şeklin altındaki açıklama ("Fig. 3: Stitch type 301") ve çevresindeki metin chunk'a eklenir | Basit, ucuz | Çizimin kendisindeki bilgi kaybolur |
| **Görsel açıklama üretmek** (*image captioning*) | Ingestion sırasında her şekil bir VLM'e verilir, "Bu çizimi ayrıntılı açıkla" denir, açıklama metin olarak indekslenir | Normal metin RAG'i ile çalışır | VLM yanlış açıklayabilir. Ek maliyet |
| **Görsel tabanlı retrieval** (ColPali vb.) | Sayfa **resim olarak** embedding'e çevrilir, metin çıkarılmadan aranır | Çizim ve tablo bilgisini doğrudan yakalar | Yeni bir altyapı. Ayrıntısı **Adım 3.4** |

#### VLM ile şekil açıklaması veri güvenliğini etkiler mi?

**Evet, VLM nerede çalıştığına bağlı.** Bulut VLM kullanılırsa (GPT, Claude, Gemini, LlamaParse vb.) manuelin çizimleri, yani müşterinin gizli dokümanının bir parçası **kurum dışına gönderilir.** Lokal VLM kullanılırsa veri kurum içinde kalır.

| Seçenek | Veri kurum dışına çıkar mı? | Artı | Eksi |
|---------|-----------------------------|------|------|
| **Bulut VLM, standart API** | ✅ Evet | En yüksek kalite, kurulum yok | Gizlilik riski. Sağlayıcının veri saklama politikasına bağlı |
| **Bulut VLM, kurumsal anlaşma** (örn. kendi Azure/AWS hesabında, veri saklamama (*zero data retention*) ve eğitimde kullanmama sözleşmesiyle) | 🟡 Fiziksel olarak evet, sözleşmeyle korunur | Kalite yüksek, hukuki güvence var | Müşteri sözleşmesi (NDA) buna izin veriyor mu? Hukuk/BT onayı gerekir |
| **Lokal açık VLM** (örn. Qwen-VL ailesi, Gemma, InternVL, Docling'in kendi küçük görsel modelleri) | ❌ Hayır | Veri tamamen kurum içinde | GPU gerekir (req.md 0.5). Kalite bulut modellerinden düşük olabilir |

**Lokal seçenek için iyi bir haber:** Şekil açıklaması **ingestion** adımında yapılır, yani her doküman için **bir kez**, arka planda. Kullanıcı beklemediği için yavaş bir lokal model de kabul edilebilir (bir manuelin işlenmesi dakikalar sürse de sorun olmaz).

**Aynı soru diğer bileşenler için de geçerli:** Veri kurum dışına çıkabilecek her nokta:
| Bileşen | Ne gönderilir | Lokal alternatif |
|---------|---------------|------------------|
| Bulut OCR (Azure DI, Textract) | Taranmış sayfa görüntüleri | Docling içi OCR, Surya, Tesseract |
| Bulut VLM (parsing / şekil açıklaması) | Sayfa ve çizim görüntüleri | Lokal açık VLM |
| Bulut embedding API | Tüm chunk metinleri | `bge-m3` (lokal) |
| Bulut LLM (cevap üretimi) | Soru + getirilen chunk'lar | Lokal açık LLM (Adım 4.1) |
| Bulut çeviri (query translation) | Kullanıcının sorusu | Lokal LLM veya NLLB / OPUS-MT |
| Bulut TTS | Cevap metni | Lokal TTS (Adım 5) |

**plan:**
- **Test aşamasında** public dokümanlar kullandığımız için bulut VLM rahatça denenebilir. Kalite için bir "üst sınır" referansı olur.
- **Aynı denemede** bir lokal VLM de çalıştırılır ve ikisi karşılaştırılır. Fark küçükse gerçek veride lokal model kullanılır.
- Gerçek veriye geçişte nihai karar req.md **Q1** (bulut API kullanılabilir mi?) ve **Adım 7** (veri güvenliği) ile verilecek.

### 2.5 Metadata şeması

Taslak şema: [rag-temelleri.md → 1.7](rag-temelleri.md).

**Parsing'den otomatik gelenler:** `pages`, `bboxes`, `section_path` (başlık hiyerarşisi), `chunk_type` (text/table/figure), `table_caption`, `ocr_confidence`, `source_type` (dijital/taranmış).

**Parsing'den doğrudan gelmeyenler:** `brand`, `version`, `is_latest`, `effective_date`, `product_category`, `allowed_groups` (bkz. req.md Q7).

#### Neden parsing'den doğrudan gelmiyorlar?

Parsing'i biz yapıyoruz, evet, ama bir araçla (Docling vb.) yapıyoruz ve bu aracın görevi sınırlı: **Sayfada ne yazıyorsa onu ve sayfanın yapısını çıkarmak.** Metnin **ne anlama geldiğini** yorumlamaz.

**Benzetme:** Parser bir daktilocu gibidir. Kağıtta ne yazıyorsa eksiksiz yazar, başlığı başlık, tabloyu tablo olarak ayırır. Ama "bu dokümanın markası ne, versiyonu ne?" diye bir **form doldurmaz.**

Kapak sayfasında "GL-PD-14-04A, Revision A, 10 June 2015" yazıyor olsun. Parser'ın çıktısı:
```
{ tür: "paragraf", metin: "GL-PD-14-04A", sayfa: 1, bbox: [...] }
{ tür: "paragraf", metin: "Revision A",   sayfa: 1, bbox: [...] }
{ tür: "paragraf", metin: "10 June 2015", sayfa: 1, bbox: [...] }
```
Metin orada, ama hiçbir yerde `version = "A"` ya da `effective_date = "2015-06-10"` diye **etiketlenmemiş.** Hangi yazının versiyon, hangisinin tarih olduğunu anlamak ayrı bir iştir.

**Alanlar üç gruba ayrılıyor:**
| Grup | Alanlar | Neden parser vermez |
|------|---------|---------------------|
| **Sayfada yazıyor ama etiketsiz** | `version`, `effective_date`, bazen `brand` | Parser yazıyı çıkarır ama "bu versiyondur" diye anlamlandırmaz |
| **Sayfada hiç yazmıyor olabilir** | `brand` (logo resim olabilir), `product_category` | Bilgi metinde değil, logoda, klasörde veya bağlamda |
| **Dokümanın içinde olamaz** | `is_latest`, `allowed_groups` | `is_latest` başka dokümanlarla **karşılaştırma** gerektirir (daha yeni versiyon var mı?). `allowed_groups` bizim **kurum içi kararımızdır**, PDF'te yazmaz |

**Yani:** Bu alanlar da **otomatik** elde edilecek, ama parser'ın kendisinden değil, ingestion hattımıza ekleyeceğimiz **ayrı bir "metadata çıkarım" adımından.** Parser metni verir, bu adım o metni (ve klasör, dosya adı gibi bilgileri) yorumlayıp alanları doldurur. Bu adım da bizim yazacağımız bir parça.

```
PDF → Parser (metin + yapı + sayfa + bbox) → Metadata çıkarım adımı (brand, version, ...) → Chunking → ...
       └── hazır araç ──────────────────┘    └── bizim kuracağımız adım ──────────────┘
```

#### Bu alanlar elle mi girilecek? Hayır, otomatik çekilecek

Yüzlerce manuel için kimsenin bu bilgileri tek tek girmesi beklenemez. Hedef: **otomatik çıkarım + sadece emin olunamayanlar için insan onayı.** Kullanılabilecek kaynaklar (birden fazlası birlikte kullanılır):

| Yöntem | Nasıl | Hangi alanlar | Örnek |
|--------|-------|---------------|-------|
| **1. Klasör / yükleme yeri** | Doküman hangi klasöre veya portal alanına yüklendiyse oradan alınır | `brand`, `product_category`, `allowed_groups` | `manuals/Nike/Apparel/...` → brand = Nike, kategori = apparel |
| **2. Dosya adlandırma kuralı** | Dosya adı belirli bir kalıpta tutulur ve ayrıştırılır | `brand`, `doc_type`, `version` | `Nike_StitchingManual_v3_2025-03.pdf` |
| **3. PDF'in kendi bilgileri** | PDF dosyasının içindeki gömülü bilgiler (başlık, yazar, oluşturma tarihi) okunur | `doc_title`, tarih (ipucu olarak) | Çoğu zaman boş veya yanlış, tek başına güvenilmez |
| **4. Kapak sayfasından kural tabanlı çıkarım** | İlk 1–2 sayfada kalıplar aranır (regex) | `version`, `effective_date`, doküman no. | "GL-PD-14-04A", "Revision B", "Effective: 01 March 2025" |
| **5. LLM ile yapılandırılmış çıkarım** | İlk sayfalar bir LLM'e verilir: "Bu dokümanın markası, versiyonu, yürürlük tarihi, ürün grubu nedir? JSON olarak ver, emin değilsen boş bırak" | Hepsi | Kural yazılamayan, formatı her markada farklı olan dokümanlar için |
| **6. Hesaplanan alanlar** | Diğer alanlardan otomatik türetilir | `is_latest`, `allowed_groups` | Aynı dokümanın en yüksek versiyonu → `is_latest = true`, diğerleri `false`. `brand = Nike` → `allowed_groups = ["nike-team", "qa"]` (bir eşleme tablosundan) |

**İnsan ne zaman devreye girer?** Sadece sistem emin olamadığında:
- LLM bir alanı boş bıraktıysa veya kaynaklar çelişiyorsa (klasör "Nike" diyor, kapak "Adidas" diyor).
- Bu durumda yükleme ekranında **önceden doldurulmuş bir form** gösterilir, kullanıcı sadece kontrol edip onaylar.

> Bu alanlardaki hata, filtrelemeyi bozar: `brand` yanlış girilirse Nike sorusuna o doküman hiç gelmez veya başka markanın sorusuna gelir. Bu yüzden `brand` ve `is_latest` gibi kritik alanlarda çıkarımın doğruluğu ayrıca kontrol edilmeli.

**Test setimizde:** Doküman numaraları kapakta yazılı ("GL-PD-14-04A", Rev. A). Yöntem 4 (regex) ve yöntem 5 (LLM) burada denenebilir. Sonuçları elle bildiğimiz değerlerle karşılaştırarak otomatik çıkarımın ne kadar doğru çalıştığını ölçeriz.




- Kullanıcı soru sorduğunda arama, otomatik olarak sadece kullanıcının gruplarına açık chunk'lar içinde yapılır (metadata filtresi, bkz. rag-temelleri.md 1.7).
- **Neden gerekli olabilir?** Bazı müşteriler, kendi manuellerinin sadece kendi projesinde çalışan ekip tarafından görülmesini sözleşmeyle isteyebilir. Cevapta ya da gösterilen sayfada başka markanın dokümanı çıkarsa bu bir **gizlilik ihlali** olur.
- **Gerekli mi?** Bu henüz belli değil. req.md **Adım 7.3** (marka bazlı yetkilendirme) sorusunun cevabına bağlı. Herkes her şeyi görebiliyorsa bu alana hiç gerek yok.
- **Nasıl doldurulur?** Elle değil. `brand` → grup eşleme tablosundan otomatik (yöntem 6).
- **Test setinde:** Gerekli değil, boş bırakılacak.

### 2.6 Bounding box

Kavram: [rag-temelleri.md → 1.7 → Bounding box](rag-temelleri.md).

**Hangi araç veriyor:** PyMuPDF (karakter/kelime/satır/blok seviyesinde, en detaylı), pdfplumber (karakter seviyesinde), Docling / Marker / MinerU / Unstructured (öğe seviyesinde: paragraf, tablo, şekil), OCR motorları (kelime seviyesinde).

**Dikkat:** Araçlar farklı koordinat sistemleri kullanabilir (orijin sol-üst veya sol-alt, birim point veya piksel). Seçilen araç ile sayfayı görsele çeviren araç arasında **koordinat dönüşümü** doğrulanmalı. Bunun en kolay testi: bir chunk'ın bbox'ını sayfa resmine çizip doğru yere düştüğünü gözle görmek.

### Önerilen ingestion hattı (taslak)

```
PDF
 │
 ├─ Dijital mi taranmış mı? (sayfa başına metin katmanı kontrolü)
 │     ├─ Dijital  → Layout-aware parser (Docling)
 │     └─ Taranmış → OCR (Docling içi OCR veya bulut OCR) → layout analizi
 │
 ├─ Öğeler: başlık / paragraf / tablo / şekil + sayfa no + bbox
 │
 ├─ Temizlik: üst/alt bilgi at, tirelemeyi birleştir, sayfa aşan tabloları birleştir
 │
 ├─ Şekiller → caption + (opsiyonel) VLM açıklaması
 │
 ├─ Doküman metadata'sı ekle (marka, versiyon, ürün ...)
 │
 └─ Chunking'e gönder (başlık bazlı, tablolar bütün) → rag-temelleri.md 1.2
```

###  ilk öneri

| Konu | Öneri | Alternatif | Gerekçe |
|------|-------|------------|---------|
| Ana parser | **Docling** | Marker, MinerU | MIT lisansı, lokal, tablo modeli, OCR entegrasyonu, bbox |
| Sayfa görselleştirme + vurgulama | PyMuPDF | pdf2image + Pillow | Hızlı ve detaylı. **AGPL lisansı ticari kullanımda kontrol edilmeli** |
| OCR | Docling içi (EasyOCR/RapidOCR) ile başla | Azure DI (karşılaştırma için), Surya | Önce lokal, sonra bulut ile kalite farkını ölç |
| Şekiller | Caption + VLM açıklaması (deneme) | ColPali (Adım 3.4) | Strickland ve Brother çizimlerinde test edilecek |
| Kalite kontrolü | Sayıların doğruluğu özel olarak kontrol edilecek | | Yanlış sayı = yanlış dikim |

**Doğrulanacaklar (2.3 deneyi ile):**
- [ ] Docling ceket şartnamesindeki dikiş tablosunu doğru çıkarıyor mu?
- [ ] Taranmış pantolon şartnamesinde OCR sayıları ("10-14", "52-56") doğru okuyor mu?
- [ ] Lokal OCR ile bulut OCR arasında anlamlı fark var mı?
- [ ] Strickland ve Brother çizimleri için VLM açıklaması işe yarıyor mu?

---

## Kaynaklar

- [Best Open-Source PDF-to-Markdown Tools in 2026: Marker vs Docling vs MinerU vs PyMuPDF4LLM](https://themenonlab.blog/blog/best-open-source-pdf-to-markdown-tools-2026)
- [From PDFs to Markdown: Evaluating Document Parsers for Air-Gapped RAG](https://dev.to/ashokan/from-pdfs-to-markdown-evaluating-document-parsers-for-air-gapped-rag-systems-58eh)
- [Document Parsing for Production RAG: Architecture, Tradeoffs](https://medium.com/@manikandan_t/document-parsing-for-production-rag-architecture-tradeoffs-and-when-to-use-what-7a89ab0af7b7)
- [Best PDF Parsers for RAG (Nutrient)](https://www.nutrient.io/blog/best-pdf-parsers-for-rag/) · [Docling alternatives](https://www.nutrient.io/blog/docling-alternatives.md)
- [Docling vs MinerU](https://www.file2markdown.ai/blog/docling-vs-mineru) · [Marker vs MinerU](https://www.file2markdown.ai/blog/marker-vs-mineru)
- [PDF Parser Benchmark (GitHub)](https://github.com/applied-artificial-intelligence/pdf-parser-benchmark)
- [PyMuPDF (GitHub, lisans bilgisi)](https://github.com/pymupdf/PyMuPDF)
- [LlamaIndex: Best Table Parsing AI](https://www.llamaindex.ai/insights/best-table-parsing-ai)
