# Kaynak Gösterme ve Sayfa Görüntüleme (Adım 3)


> **Başlangıç:** 2026-10-08
> **İlgili plan:** [req.md, Adım 3](../req.md) · Önceki: [rag-temelleri.md](rag-temelleri.md), [pdf-isleme.md](pdf-isleme.md) · Test seti: [manual-envanteri.md](manual-envanteri.md)


---
### 0.1 Geri izlenebilirlik (citation / source grounding)

**Ne demek?** Cevaptaki bir bilgiden, o bilginin **geldiği yere geri gidebilmek.** 
"Bu cevap nereden çıktı?" sorusuna her zaman net bir cevap verebilmek: hangi doküman, hangi sayfa, hangi paragraf.


**İlgili terimler:**
| Terim | Türkçesi | Anlamı |
|-------|----------|--------|
| *Citation* | Atıf, kaynak gösterme | Cevabın yanına kaynağı yazmak: "[1] GL-PD-14-04A, s. 12" |
| *Grounding* | Dayandırma, temellendirme | Cevabın **sadece** verilen kaynaklara dayanması, kaynakta olmayan bilgi içermemesi |
| *Traceability* | İzlenebilirlik | Cevaptan kaynağa geri gidilebilmesinin genel adı |

> Citation "kaynağı göster", grounding "kaynağın dışına çıkma" demek. İkisi birlikte izlenebilirliği sağlar.

**Neden lazım?**
| Sebep | Açıklama | Bizim projede örnek |
|-------|----------|---------------------|
| **Güven** | Kullanıcı bir makinenin söylediğine körü körüne güvenmez, kaynağı görmek ister | Usta "11 SPI" bilgisini manuelin kendisinde görmek ister |
| **Doğrulama / hata yakalama** | LLM yanlış bilgi verirse kaynakla karşılaştırınca fark edilir | Cevap "12 SPI" der ama kaynak "11 (± 1)" diyorsa hata yakalanır (halüsinasyona karşı önlem, rag-temelleri.md S11) |
| **Sorumluluk / denetim** | Bir karar verildiğinde neye dayanarak verildiği belgelenir | Müşteri şikayetinde "Bu ürün hangi şartnamenin hangi maddesine göre dikildi?" sorusuna cevap |
| **Güncellik kontrolü** | Bilginin hangi versiyondan geldiği görünür | "Bu değer Rev. A'dan mı, Rev. B'den mi?" |
| **Projenin kendisi** | Sayfayı ekranda göstermek için önce **hangi sayfa** olduğunu bilmek gerekir | Geri izlenebilirlik olmadan sayfa gösterme ve vurgulama hiç yapılamaz |

**İzlenebilirlik olmazsa:** Sistem "11 SPI olmalı" der, ama kimse bunun nereden geldiğini, doğru olup olmadığını, hangi dokümana ait olduğunu bilemez. Yanlışsa fark edilmez ve yanlış dikim yapılır.

### 0.2 PDF sayfasını görsele çevirme (rendering)

**Ne demek?** PDF dosyası aslında bir **talimat listesidir:** "Şu harfi şu koordinata çiz, şu çizgiyi şuraya çek" (pdf-isleme.md, 2. bölüm). *Rendering* (işleme/çizdirme), bu talimatları uygulayıp sayfayı **piksellerden oluşan bir resme (PNG/JPG)** dönüştürmektir. PDF okuyucunuzda bir sayfayı açtığınızda arka planda olan şey budur.



**Neden lazım?**
| Sebep | Açıklama |
|-------|----------|
| **Arayüzde göstermek** | Web arayüzleri (Streamlit, Gradio, tarayıcı) resmi kolayca gösterir, PDF'i sayfa sayfa göstermek ayrıca uğraş ister |
| **Orijinal görünümü korumak** | Kullanıcı sayfayı **manuelde göründüğü haliyle** görür: tablo düzeni, çizimler, kalın yazılar, logolar. Parse edilmiş düz metin bunları göstermez |
| **Üstüne çizim yapabilmek** | Vurgu kutusu resmin üstüne çizilir (0.3) |
| **Taranmış dokümanlarda gerçeği göstermek** | Taranmış sayfanın resmi **orijinal taramanın kendisidir.** OCR metni hatalı olsa bile kullanıcı gerçek değeri görür (pdf-isleme.md K3) |

### 0.3 Vurgulama (highlight / bbox)

**Ne demek?** Gösterilen sayfada, cevabın dayandığı **metnin tam yerini işaretlemek.** Genelde yarı saydam renkli bir kutuyla. Kutunun yeri, parser'ın verdiği **bbox** koordinatlarından gelir (rag-temelleri.md 1.7).

**Benzetme:** Birine bir kitaptan bilgi gösterirken sayfayı açıp **fosforlu kalemle** ilgili cümlenin üstünü çizmek.

**Neden lazım? Sadece sayfayı göstermek yetmez mi?**
- Bir şartname sayfasında **onlarca değer** olabilir: dış dikiş 11 ± 1, overedge 10 ± 2, ilik 54 ± 2... Sadece sayfa gösterilirse kullanıcı doğru satırı **kendisi aramak** zorunda kalır ve **yanlış satırı okuyabilir.**
- Vurgulama kullanıcının bilgiyi **saniyeler içinde** bulmasını ve cevapla karşılaştırmasını sağlar.
- Makine kılavuzlarında "Şekil 3'teki A vidası" gibi talimatlarda ilgili çizimi işaretlemek, ustanın doğru parçaya bakmasını sağlar.

**Vurgulama olmazsa:** Doğrulama zahmetli olur, kullanıcılar zamanla kaynağa bakmayı bırakır ve izlenebilirliğin faydası kaybolur.

### 0.4 Multimodal / görsel tabanlı retrieval (ColPali vb.)

**Ne demek?**
- **Multimodal:** Birden fazla veri türüyle (*modality*) çalışmak: metin + görsel (+ ses, video).
- **Görsel tabanlı retrieval:** Aramayı **metin üzerinde değil, sayfa resimleri üzerinde** yapmak. Sayfadan metin çıkarmadan, sayfanın görüntüsü doğrudan "anlamına göre" aranır.
- **ColPali:** Bu işi yapan bilinen bir model ailesi (2024'te yayınlandı).

**Neden konuşuyoruz?** Şimdiye kadarki yöntemimiz "PDF → metin → ara". Ama bazı bilgiler **metinde yoktur**:
- Stitch Guide'da bir dikiş tipinin nasıl göründüğü **çizimdedir.**
- Brother kılavuzunda bir parçanın yeri **montaj çizimindedir.**
- Taranmış bir sayfada OCR yanlış okuyabilir.

Metin tabanlı arama bu bilgileri bulamaz, çünkü onları hiç "görmez". Görsel tabanlı arama sayfayı bir insan gibi **görerek** arar.

**"Gerekliliği"**: Bu daha pahalı ve karmaşık yaklaşıma bizim projede gerçekten ihtiyaç var mı, yoksa metin tabanlı arama yeterli mi?  (kısaca: Gerçek dokümanlarda dikiş, ölçü ve makine görselleri olduğu için **görsel anlama bir ihtiyaç.** Açık olan, bunun ColPali ile mi yoksa daha ucuz bir yöntemle mi yapılacağı. Ayrıntı 5. bölümde: "Bizim için gerekli mi?").

### 0.5 Dört kavram birbirine nasıl bağlanıyor?

```
Soru → Arama (metin tabanlı ve/veya görsel tabanlı ← 0.4)
     → LLM cevap + kaynak numarası
     → Geri izlenebilirlik: hangi doküman, sayfa, paragraf? (0.1)
     → Sayfayı resme çevir (0.2)
     → İlgili yeri vurgula (0.3)
     → Kullanıcı cevabı orijinal sayfada kendi gözüyle doğrular
```
Zincirin ilk halkası **geri izlenebilirlik.**  !! 

---

## 1. Sistem 

Sıradan bir RAG sistemi sadece metin cevap verir.  Burada kaynağı da gösterecek:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Soru: "Ceketin dış dikişlerinde SPI kaç olmalı?"                   │
├──────────────────────────────┬──────────────────────────────────────┤
│  CEVAP                       │  KAYNAK SAYFA                        │
│                              │  ┌────────────────────────────────┐  │
│  Dış görünür dikişler inç    │  │ 3.5 Stitching                  │  │
│  başına 11 (± 1) dikiş       │  │ ████████████████████████████   │  │
│  olmalıdır. [1]              │  │ █ All outside visible stitch █ │  │ ← vurgu
│                              │  │ █ shall be 11 (± 1) SPI...   █ │  │
│  [1] GL-PD-14-04A, s. 12     │  │ ████████████████████████████   │  │
│                              │  │ Overedge shall be ...          │  │
│  🔊 Sesli oku                │  └────────────────────────────────┘  │
└──────────────────────────────┴──────────────────────────────────────┘
```

Bunun için üç şey gerekiyor:
1. **Kaynak bağlama (citation):** Cevaptaki her bilginin hangi chunk'tan geldiğini bilmek.
2. **Sayfa görüntüleme:** O chunk'ın sayfasını ekranda göstermek.
3. **Vurgulama (highlight):** Sayfada ilgili yeri işaretlemek.

> Halüsinasyona karşı alınacak önlemlerden üçüdür. 

---

## 2. Kaynak bağlama (citation / grounding)

### Kavramlar

- **Grounding (dayandırma):** Cevabın verilen kaynaklara dayanması, kaynakta olmayan bilgi içermemesi.
- **Citation (atıf):** Cevaptaki bir bilginin hangi kaynaktan geldiğinin belirtilmesi. Örn. "[1] GL-PD-14-04A, s. 12".
- **Attribution (iz sürme):** Bir cümlenin kaynaktaki **hangi parçaya** karşılık geldiğini bulmak. Vurgulama için gerekli.

### LLM'e kaynak gösterttirme nasıl yapılır?

**Adım 1: Chunk'lara kimlik ver.** LLM'e giden promptta her chunk numaralandırılır:
```
[1] (GL-PD-14-04A, s.12) All outside visible stitching shall be 11 (± 1) stitches per inch...
[2] (GL-PD-14-04A, s.12) Overedge or pre-hemming shall be 10 (± 2) stitches per inch...
[3] (GL-PD-07-14A, s.9)  The seams for all outside visible stitching shall be 10-14 SPI...

Soru: Ceketin dış dikişlerinde SPI kaç olmalı?
Kural: Her bilgiden sonra kaynağını [numara] olarak yaz. Kaynaklarda yoksa "bulunamadı" de.
```

**Adım 2: LLM numarayla cevap verir:** "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır [1]."

**Adım 3: Kod numarayı metadata'ya çevirir:** `[1]` → chunk 1 → `doc_id = gl-pd-14-04a`, `pages = [12]`, `bboxes = [...]` → sayfa görüntülenir, kutu çizilir.

> LLM sayfa numarasını **kendisi yazmaz**, sadece chunk numarasını verir. Sayfa ve bbox bilgisi **metadata'dan** gelir. Böylece LLM sayfa numarasını yanlış yazamaz.

#### Soru: Bir sonraki sayfaya kayan cümleler kesilmez mi?

**Kimlik (ID) sayfaya değil, chunk'a verilir.** Bir cümlenin kesilip kesilmemesi ID'ye değil, **chunk'ların nasıl oluşturulduğuna** bağlıdır.

| Chunking yöntemi | Sayfa sonunda ne olur? |
|------------------|------------------------|
| **Sayfa bazlı** (her sayfa bir chunk) | ❌ Cümle **kesilir:** "All outside visible stitching shall be" (s.12) + "11 (± 1) stitches per inch." (s.13) iki ayrı chunk'a düşer. Hiçbiri tek başına anlamlı değildir |
| **Başlık/bölüm bazlı** (bizim seçimimiz, rag-temelleri.md 1.2) | ✅ Kesilmez. Parser metni **okuma sırasıyla, sayfalardan bağımsız** bir akış olarak verir. Chunk bölüm sınırında başlar ve biter, sayfa sınırı arada kalabilir |

**Kesilmemesi için ingestion'da yapılanlar:**
1. **Temizlik adımı** (pdf-isleme.md 5.1): Sayfa sonundaki üst/alt bilgi ("Page 12", doküman no.) atılır. Yoksa cümlenin ortasına "GL-PD-14-04A Page 12" girer.
2. **Paragraf birleştirme:** Parser bazen bir paragrafı sayfa başına iki ayrı öğe olarak verir. Kural: Sayfanın son öğesi nokta ile bitmiyorsa ve sonraki sayfanın ilk öğesi küçük harfle başlıyorsa, ikisi birleştirilir. Satır sonu tirelemesi ("stitch-" / "ing") de burada birleştirilir.
3. **Uzun bölümler bölünürken cümle sınırına dikkat:** Bölüm chunk boyutundan uzunsa, kelime ortasından değil **cümle sonundan** bölünür ve parçalar arasında biraz örtüşme (overlap) bırakılır.
4. **Sayfayı aşan tablolar** ayrıca birleştirilir (pdf-isleme.md 5.1).

**Birleşen chunk'ın metadata'sı:** İki sayfayı da bilir.
```json
{ "pages": [12, 13],
  "bboxes": [ {"page": 12, "box": [72, 700, 523, 760]},
              {"page": 13, "box": [72, 60, 523, 95]} ] }
```
**Ekranda:** 12. sayfa açılır ve alttaki kısım vurgulanır, "devamı s.13" ile 13. sayfanın üstündeki devam kısmı da vurgulanmış olarak gösterilir (veya iki sayfa alt alta).

**Dikkat edilecek nokta:** Bu birleştirme kuralları her dokümanda kusursuz çalışmayabilir (örn. sayfa sonunda bir tablo, sonraki sayfada yeni bir başlık varsa yanlış birleştirmemek gerekir). Faz 1 denemesinde sayfa geçişleri özellikle kontrol edilecek.

### Kaynak doğrulama

LLM yanlış numara verebilir (bilgi [1]'den geldiği halde [3] yazmak). Kontroller:
| Kontrol | Nasıl |
|---------|-------|
| Numara geçerli mi? | Cevaptaki [n] gerçekten verilen chunk'lardan biri mi? |
| Alıntı chunk'ta var mı? | LLM'den kısa bir alıntı da istenirse (S11, Katman 4), alıntının o chunk'ta geçtiği metin karşılaştırmasıyla kontrol edilir |
| Sayılar chunk'ta var mı? | Cevaptaki "11", "± 1" gibi değerler atıf yapılan chunk'ta geçiyor mu? |

Kontrol başarısızsa cevap reddedilir veya uyarıyla gösterilir.

### Detay seviyesi

| Seviye | Örnek | Bizim için |
|--------|-------|------------|
| Doküman | "Kaynak: GL-PD-14-04A" | Yetersiz |
| Sayfa | "GL-PD-14-04A, s. 12" | Minimum |
| **Chunk / paragraf** | Sayfa + vurgulanan paragraf | **Hedef** |
| Cümle / kelime | Sadece "11 (± 1)" ifadesi vurgulanır | İdeal ama zor (bkz. 4. bölüm) |

---

## 3. Sayfa görüntüleme

İki temel yaklaşım var:

| Yaklaşım | Nasıl çalışır | Artı | Eksi |
|----------|---------------|------|------|
| **A. Sunucuda sayfayı resme çevirmek** | Python tarafında sayfa PNG/JPG'ye çevrilir (render), arayüze resim olarak gönderilir | Basit, her arayüzde çalışır (Streamlit, Gradio dahil). Vurgu kutusu doğrudan resmin üstüne çizilebilir | Yakınlaştırınca bulanıklaşır (çözünürlüğe bağlı). Metin seçilemez |
| **B. Tarayıcıda PDF'i göstermek** | PDF dosyası tarayıcıya gönderilir, **PDF.js** gibi bir kütüphane ilgili sayfayı açar | Net görüntü, yakınlaştırma, metin seçme, sayfa çevirme | Daha karmaşık, özel web arayüzü gerekir. Vurgu katmanını ayrıca kodlamak gerekir |

**Sayfayı resme çevirme araçları (A):**
| Araç | Not |
|------|-----|
| **PyMuPDF** (`page.get_pixmap(dpi=150)`) | Çok hızlı, ek kurulum yok. ⚠️ AGPL lisansı (pdf-isleme.md 2.2) |
| **pdf2image** (Poppler kullanır) | Yaygın, MIT lisansı. Poppler'ın ayrıca kurulması gerekir |
| **pypdfium2** (Google'ın PDFium'u) | Hızlı, serbest lisans (Apache/BSD). PyMuPDF'e iyi bir alternatif |

**Çözünürlük (DPI) dengesi:**
| DPI | Kullanım |
|-----|----------|
| 72–100 | Küçük önizleme |
| **150** | **Ekranda okumak için genelde yeterli** |
| 200–300 | Küçük yazılı tablolar, yakınlaştırma |

**Performans:** Sayfalar ingestion sırasında **önceden resme çevrilip saklanabilir** (*pre-render*). Böylece soru geldiğinde bekleme olmaz. Bedeli disk alanı (sayfa başına ~100–500 KB).

### Soru: Sadece tek bir sayfa resmi mi gösterilecek? Kullanıcı öncesini/sonrasını okumak isterse?

Haklı bir endişe. "Sayfayı resme çevirmek" **tek bir sayfa resmi gösterip bırakmak** anlamına gelmek zorunda değil, ama A yönteminin en basit hali böyle olur ve bu kullanıcı için yetersiz kalabilir: Bir dikiş kuralının devamı, bir tablonun başlığı veya bir uyarı notu bir önceki/sonraki sayfada olabilir.

**Neden resme çevirmeyi düşünmüştük?** Üç sebep: (1) Streamlit/Gradio gibi hızlı prototip arayüzleri resmi doğrudan gösterebilir, (2) vurgu kutusu resmin üstüne kolayca çizilir, (3) kullanıcıya **dokümanın tamamı değil, sadece ilgili sayfa** gönderilir (gizlilik açısından avantaj, aşağıda).

#### İki yöntemin gerçek sorunları ve çözümleri

**A. Sayfayı resme çevirmek**
| Sorun | Çözüm |
|-------|-------|
| Sadece tek sayfa görünür, öncesi/sonrası okunamaz | Önceki/sonraki sayfa butonları veya sayfa kaydırıcısı (diğer sayfalar da aynı şekilde resim olarak getirilir) |
| Yakınlaştırınca bulanıklaşır | Daha yüksek DPI (200–300) ile render + tıklayınca büyük görüntüleme |
| Metin seçilip kopyalanamaz, sayfada arama yapılamaz | A ile çözülmez. Gerekirse "Dokümanın tamamını aç" bağlantısı: Tarayıcının kendi PDF görüntüleyicisinde ilgili sayfadan açılır (`dosya.pdf#page=12`). Ücretsiz ve kolay |
| Her sayfa geçişinde sunucudan yeni resim gelir | Ingestion'da önceden render + önbellek |

**B. Tarayıcıda PDF'i göstermek (PDF.js)**
| Sorun | Çözüm |
|-------|-------|
| "Maliyetli/zor" algısı | **Para maliyeti yok:** PDF.js ücretsiz, açık kaynak (Mozilla'nın, Firefox'un PDF görüntüleyicisi). Maliyet **geliştirme eforu**. Ama hazır bileşenler bu eforu çok azaltıyor: **`streamlit-pdf-viewer`** Streamlit içinde PDF.js ile PDF gösteriyor, **bbox ile vurgu (annotation)** destekliyor ve vurgulanan yere **otomatik kaydırabiliyor.** Yani B, prototipte bile mümkün |
| Büyük PDF'ler yavaş açılabilir | PDF.js dosyayı parça parça yükleyebilir (ilk sayfalar önce). Çok büyük dokümanlarda sayfa aralığı gönderilebilir |
| Vurgu koordinatları | PDF.js PDF'in kendi koordinat sistemiyle çalıştığı için parser'ın bbox'ı genelde **doğrudan** kullanılabilir (A'daki DPI ölçeklemesine gerek kalmaz). Yine de orijin (sol-üst/sol-alt) kontrol edilmeli |
| **Dokümanın tamamı kullanıcıya gider** | Kullanıcı PDF'in tamamını indirebilir. Gizli müşteri manuellerinde ve marka bazlı yetkilendirmede (Adım 7.3) sorun olabilir. Çözüm: Yetki kontrolü, sadece ilgili sayfa aralığını içeren bir PDF parçası göndermek veya indirmeyi kapatmak (tam güvenlik sağlamaz) |
| Bazı mobil/tablet tarayıcılarda performans | Fabrika tabletlerinde test edilmeli |

#### B'yi ne zaman tercih etmeliyiz? (Hangi ihtiyaçlar B'yi gerektirir?)

Aşağıdaki sorulara **"evet"** cevabı ne kadar çoksa B o kadar uygun:

| Soru | Evet ise |
|------|----------|
| Kullanıcı sadece "kanıtı görmek" değil, dokümanda **gezinmek, öncesini/sonrasını okumak** istiyor mu? | B |
| Kullanıcı **yakınlaştırma** (küçük yazılı tablolar, teknik çizim detayları) yapacak mı? | B (A'da yüksek DPI ile kısmen) |
| Kullanıcı metni **seçip kopyalamak** veya sayfa içinde **arama** yapmak istiyor mu? | B |
| Bir cevapta **birden fazla vurgu** (farklı sayfalarda) gösterilecek mi? | B (tek görüntüleyicide hepsi, aralarında atlama) |
| Kullanıcıya **dokümanın tamamının gitmesi** sorun mu? (gizlilik, yetki) | **A** (sadece ilgili sayfa gider) |
| Ekran çok basit mi olmalı (ör. atölyede, dokunmatik tablet, eldivenle kullanım)? | **A** (tek büyük resim, büyük butonlar) |

**Bizim durumumuz:** Kullanıcının öncesini/sonrasını okumak isteyeceği belli (senin ilk endişen), teknik çizimlerde yakınlaştırma da büyük ihtimalle gerekecek. Bu iki ihtiyaç **B'yi işaret ediyor.** B'yi engelleyebilecek tek ciddi konu **gizlilik:** Kullanıcının dokümanın tamamını görmesi/indirmesi kabul edilebilir mi?

**Güncellenmiş öneri:**
- **Prototip:** `streamlit-pdf-viewer` ile **B** (PDF.js + bbox vurgusu + vurguya otomatik kaydırma). A kadar kolay, kullanıcı tüm dokümanda gezinebilir.
- **Yedek:** Bileşen sorun çıkarırsa A + önceki/sonraki sayfa butonları + "dokümanı aç" bağlantısı.
- **Karar noktası:** Gizlilik ve yetkilendirme kararı (Adım 7, yeni req.md **Q9**). Kullanıcıya tüm doküman verilemiyorsa A'ya veya sayfa aralığı gönderilen B'ye dönülür.
- Nihai seçim arayüz tasarımında (Adım 6) kullanıcı ihtiyaçlarıyla birlikte kesinleşecek.

---

## 4. Vurgulama (highlight)

### Temel yöntem: bbox'ı resmin üstüne çizmek

```
1. Chunk'ın metadata'sından bbox'lar alınır:     [72, 210, 523, 268]  (PDF point)
2. Sayfa 150 DPI'da resme çevrilir.
3. Koordinatlar ölçeklenir:  piksel = point × (150 / 72) ≈ point × 2.08
                             → [150, 437, 1090, 558]  (piksel)
4. Resmin üstüne yarı saydam sarı dikdörtgen çizilir (Pillow, OpenCV veya PyMuPDF ile).
```

> Koordinat sistemi (orijin sol-üst mü sol-alt mı, birim point mi piksel mi) parser ile render aracı arasında **tutarlı olmalı.** Yoksa kutu yanlış yere düşer (rag-temelleri.md 1.7, Bounding box).

### Detay seviyesine göre seçenekler

| Seçenek | Ne vurgulanır | Nasıl | Zorluk |
|---------|---------------|-------|--------|
| **Chunk bbox'ı** | Chunk'ın kapladığı tüm alan (paragraf/tablo) | Metadata'daki `bboxes` doğrudan çizilir | ✅ Kolay. **Başlangıç için önerilen** |
| **Cümle / ifade** | Sadece cevabı destekleyen cümle veya "11 (± 1)" | LLM'in alıntısı sayfada **metin araması** ile bulunur (PyMuPDF `page.search_for("11 (± 1)")` kelimelerin kutularını verir) | 🟡 Orta. Alıntı birebir eşleşmezse bulunamaz. OCR'lı sayfalarda daha zor |
| **Tablo hücresi** | Tablonun sadece ilgili satırı/hücresi | Parser'ın hücre bbox'ları kullanılır | 🟡 Orta. Parser hücre koordinatı vermeli |
| **Çizim** | Şeklin tamamı | Şeklin bbox'ı | ✅ Kolay |

**Pratik yaklaşım (iki katmanlı):**
- Chunk alanı **açık renkle**, cevabı doğrudan destekleyen cümle **koyu renkle** vurgulanır.
- Cümle bulunamazsa sadece chunk alanı gösterilir. Bu her zaman çalışan **yedek** yöntemdir.

### Özel durumlar
| Durum | Çözüm |
|-------|-------|
| Chunk iki sayfaya yayılıyor | İlk sayfa gösterilir, "devamı s.13" bağlantısı. Veya iki sayfa alt alta |
| Birden fazla kaynak var ([1], [2], [3]) | Kaynaklar sekme/küçük resim olarak listelenir, tıklanan gösterilir |
| Taranmış sayfa | bbox'lar OCR'dan gelir. Resim zaten orijinal tarama olduğu için kullanıcı **gerçek değeri** görür (OCR hatasına karşı güvence, pdf-isleme.md K3) |

---

## 5. Görsel tabanlı (multimodal) retrieval: ColPali vb.

### Fikir

Şimdiye kadarki yaklaşım: **PDF → metin çıkar → metni ara.** Görsel tabanlı retrieval bunun yerine: **Sayfanın resmini doğrudan ara.**

```
Metin tabanlı (klasik):    Sayfa → Parser/OCR → Metin → Chunk → Embedding → Arama
                                     ▲ burada bilgi kaybolabilir (tablo, çizim, OCR hatası)

Görsel tabanlı (ColPali):  Sayfa → Resim → Görsel embedding → Arama
                                   (metin çıkarma adımı YOK)
```

### ColPali nasıl çalışır (basitçe)

1. Her sayfa resmi küçük **parçalara (patch)** bölünür (ör. 32×32'lik bir ızgara, ~1000 parça).
2. Bir görsel dil modeli (VLM) her parça için bir vektör üretir. Sayfa = **~1000 vektör**.
3. Soru da kelime kelime vektörlere çevrilir.
4. Sorudaki her kelime, sayfadaki **en uygun parçayla** eşleştirilir, puanlar toplanır (*late interaction :t sits right between fast single-vector search (bi-encoders) and ultra-accurate joint-attention search (cross-encoders)*, rag-temelleri.md'deki BGE-M3 multi-vector ile aynı fikir).
5. En yüksek puanlı sayfalar getirilir.

 ColPali (PaliGemma tabanlı), ColQwen2 / ColQwen2.5 (Qwen-VL tabanlı), ve türevleri. Karşılaştırma için **ViDoRe** benchmark'ı kullanılır.

### Artıları ve eksileri

| Artı | Eksi |
|------|------|
| Tablo, çizim, düzen bilgisini **doğrudan** yakalar | **Depolama:** Sayfa başına ~1000 vektör. Metin RAG'e göre yüzlerce kat fazla yer |
| OCR hatası ve parsing kaybı yok | GPU gerekir (ingestion ve sorgu) |
| Stitch Guide gibi çizim ağırlıklı dokümanlarda metin RAG'den belirgin şekilde iyi | **Sayfa bulur, cevap vermez:** Cevabı yazmak için sayfa resmini okuyabilen bir VLM yine gerekir |
| Patch eşleşme haritası, sayfanın **hangi bölgesinin** eşleştiğini gösterebilir (kaba bir vurgulama) | Bu harita kesin bir vurgu değil, daha çok **hata ayıklama** aracı |
| | Kelime/kod araması (ör. "E-07") metin aramasına göre zayıf olabilir |
| | Bbox ve chunk seviyesinde kesin konum vermez, **sayfa seviyesinde** çalışır |

### Bizim için gerekli mi?

**Güncellenmiş karar: Görsel anlama bir ihtiyaç, opsiyon değil.** Gerçek spec ve manuellerde dikim/dikiş çizimleri, ölçü çizimleri ve makine parça görselleri bulunuyor. Sistem bunları anlayamazsa bilginin önemli bir kısmı kaybolur. Açık olan soru "görsel anlama gerekli mi?" değil, **"hangi yöntemle, hangi maliyetle?"**

> Not: İlk versiyonda "şimdilik gerekli değil" denmişti. Gerekçelerden biri test setindeki dokümanların çoğunun metin ağırlıklı olmasıydı. Bu yanlış bir dayanaktı: Test seti öylesine seçilmiş örneklerden oluşuyor, **gerçek dokümanları temsil etmiyor.** Kararı test dokümanlarına göre değil, gerçek dokümanların özelliklerine göre vermek gerekiyor.

#### İki ayrı iş: Görseli bulmak ve görseli anlamak

"Görsel veriyle çalışmak" aslında iki ayrı iştir:

| İş | Soru | Örnek |
|----|------|-------|
| **1. Bulmak** (*retrieval*) | Cevap hangi sayfada / hangi çizimde? | "Overlok dikişi nasıl görünür?" → Stitch Guide s.5'teki çizim |
| **2. Anlamak** (*comprehension*) | Çizimde ne anlatılıyor, cevap ne? | Çizimdeki iplik geçişini okuyup "3 iplikli, kenarı saran bir dikiş" demek |

**ColPali sadece 1. işi yapar:** Doğru sayfayı bulur, ama çizimi "anlatamaz". 2. iş için her durumda **görseli okuyabilen bir model (VLM)** gerekir. Bu yüzden asıl karar şu: **VLM'i nerede kullanacağız ve aramayı nasıl yapacağız?**

#### Görselleri anlamak için seçenekler

| Seçenek | Nasıl çalışır | Bulmak | Anlamak | Maliyet | Vurgulama (bbox) |
|---------|---------------|--------|---------|---------|------------------|
| **A. Ingestion'da görsel açıklama** (*captioning*) | Her çizim **bir kez** VLM'e verilir, ayrıntılı metin açıklaması yazılır ("Bu çizim 504 tipi 3 iplikli overlok dikişini üstten ve alttan gösteriyor..."). Açıklama normal chunk gibi indekslenir | ✅ Metin araması açıklama üzerinden bulur | 🟡 Açıklamanın kalitesi kadar. Açıklamaya yazılmayan detay kaybolur | **Ucuz:** Her görsel için bir kez. Soru başına ek maliyet yok | ✅ Çizimin bbox'ı bilinir |
| **B. Cevap anında görseli VLM'e vermek** | Arama ilgili chunk'ı bulunca, chunk bir çizime aitse veya çizime atıf yapıyorsa, **sayfa/çizim resmi** de cevap üreten modele (VLM) verilir | (A veya C ile birlikte kullanılır) | ✅ En iyisi: Model çizimi soruyla birlikte **doğrudan görür** | Orta: Sadece görsel içeren sorularda, soru başına | ✅ |
| **C. ColPali ile görsel arama** | Sayfalar resim olarak indekslenir, soru doğrudan sayfa resimleriyle eşleştirilir | ✅ Görsel ağırlıklı sayfalarda en iyisi | ❌ Tek başına anlamaz, B gerekir | Pahalı: Sayfa başına ~1000 vektör, GPU | ❌ Sadece sayfa seviyesi |

#### Daha ucuz ve doğru bir alternatif var mı?

**Muhtemelen evet: A + B birlikte.**

```
INGESTION (bir kez):   Çizim → VLM açıklaması (metin) → indekslenir
                       Çizimin resmi ve bbox'ı da saklanır

SORGU (her soruda):    Soru → Metin araması (açıklamalar dahil) → chunk bulunur
                       Chunk bir çizime aitse → çizimin resmi + soru → VLM → cevap
                       Ekranda: sayfa + çizimin etrafında vurgu
```

**Neden bu kombinasyon?**
| Avantaj | Açıklama |
|---------|----------|
| **Tek arama sistemi** | Ayrı bir ColPali altyapısı (depolama, GPU, ikinci indeks) gerekmez |
| **Bulma işini A çözer** | Açıklama metni sayesinde "overlok dikiş görünümü" sorusu doğru çizimi bulur |
| **Anlama işini B çözer** | Açıklama eksik kalsa bile, cevap anında model çizimi **kendisi görür.** A'daki "açıklamaya yazılmayan detay kaybolur" riski büyük ölçüde kapanır |
| **Kesin vurgulama** | Çizimin bbox'ı bilindiği için ekranda doğru yer işaretlenir |
| **Maliyet kontrollü** | VLM ingestion'da bir kez çalışır. Cevap anında sadece görsel içeren sorularda devreye girer |

**ColPali ne zaman yine de gerekir?** A'daki açıklamalar arama için yetersiz kalırsa: Örneğin kullanıcı bir çizimi kelimelerle tarif edemiyorsa, ya da açıklamalar çok benzer çizimleri (onlarca dikiş tipi) ayırt edemiyorsa. Bu durumda ColPali metin aramasının **yanına** ikinci arama kanalı olarak eklenir.

**Gizlilik notu:** A ve B'de kullanılacak VLM'in lokal mi bulut mu olacağı req.md Q1'e bağlı (pdf-isleme.md, "VLM ile şekil açıklaması veri güvenliğini etkiler mi?"). Lokal açık VLM'ler (Qwen-VL ailesi vb.) bu iş için kullanılabilir.

#### Karar nasıl kesinleşecek?

Hangi yöntemin bizim dokümanlarımızda "daha doğru" olduğunu kaynaklardan bilemeyiz, **ölçmemiz** gerekir:
1. **Gerçek dokümanlardaki görsel türlerini öğrenmek** (req.md Q3 güncellendi): Dikiş tipi çizimleri mi, ölçülü teknik çizimler mi, fotoğraflar mı, makine parça çizimleri mi? Her türün zorluğu farklı.
2. Test setine **görsel sorular** eklemek (cevabı sadece çizimde olan sorular). Test dokümanları gerçeği temsil etmediği için, mümkünse gerçek dokümanlardaki görsel türlerine benzeyen örnekler seçilmeli.
3. Pilotta **A+B** ile **C+B**'yi aynı görsel sorularda karşılaştırmak: Doğru sayfa bulundu mu (Recall@5), cevap doğru mu, maliyet ve gecikme ne?

---

## 6. Kontrol soruları

> Kısa cevaplar yeterli, bilmediğine "bilmiyorum" yaz.

**K1.** LLM'e cevapta sayfa numarasını kendisi yazdırmak yerine neden sadece chunk numarası ([1], [2]) yazdırıyoruz?
> **C:** kontrol için bunu yapmamız cok daha mantıklı, sadece  sayfa numarası vs verse halüsinasyon olabilir ama chunk olduğunda ona verilmiş chunklar icinde miydi değil miydi kontrol edebiliriz.

✅ Doğru. Asıl sebep kontrol edilebilirlik. Tamamlayıcı noktalar:

LLM sayfa numarasını uydurabilir ya da yanlış yazabilir, örneğin s.12 yerine s.21.
Chunk numarası ise sınırlı bir küme (1–5). Cevaptaki numaranın verilen chunk'lardan biri olup olmadığı kolayca kontrol edilir.
Sayfa ve bbox bilgisi metadata'dan kesin olarak gelir.
Ek fayda: Alıntı ve sayı kontrolü de o chunk'a karşı yapılabilir.

**K2.** Bir sayfayı 150 DPI'da resme çevirdik ama vurgu kutusu yanlış yere çizildi. Sence en olası sebep ne?
> **C:**  neredeyse her zaman koordinat dönüşümü:

En olası: DPI ölçeklemesi yapılmamış. Bbox PDF point cinsinden, resim piksel cinsinden. 150 DPI'da her şey yaklaşık 2.08 katı büyür. Ölçekleme unutulursa kutu sol üst köşede, küçük bir yerde kalır.
Orijin farkı: PDF'te (0,0) noktası sol-altta, resimde sol-üstte. Dönüştürülmezse kutu dikeyde ayna konumuna düşer, örneğin sayfanın altındaki paragraf yerine üstüne.
Sayfa numarası kayması: Bazı araçlar sayfaları 0'dan, bazıları 1'den sayar. Kutu bir sonraki ya da önceki sayfaya çizilir.
Döndürülmüş sayfa veya PDF'in kırpma alanı farkı.

**K3.** Taranmış pantolon şartnamesinde OCR "11" yerine "ll" okudu. Kullanıcı ekranda sayfa görüntüsünü görüyorsa bu hata nasıl fark edilir? Sayfa gösterilmeseydi ne olurdu?
> **C:** Sayfa gösterilirse: Ekrandaki görüntü orijinal taramanın kendisi. Kullanıcı cevapta garip ya da yanlış bir değer görür, vurgulanan yerde ise "11" yazdığını görür. Uyuşmazlık hemen fark edilir.
Sayfa gösterilmezse: Hata sessiz kalır. Kaynak metnin kendisi bozuk olduğu için otomatik kontroller de geçer. Yanlış değerle dikim yapılır.

**K4.** "S-7300A'da üst iplik gerginliği nasıl ayarlanır?" sorusuna cevap verirken Brother kılavuzunun çizimli bir sayfası geliyor. Burada sadece chunk alanını vurgulamak mı, cümle vurgulamak mı daha faydalı? Neden?
> **C:** cümleyi vurgulayacak elbette ki bağlamdan anlaşılmalar yapılsın
🟡 Kısmen doğru. Cümle vurgusu faydalı, ama çizimli sayfada tek başına yetmez:

Talimat genelde "Şekil 5'teki gerginlik somununu (A) saat yönünde çevirin" gibi bir cümle. Cümleyi okumak yetmez, ustanın çizimde A parçasını görmesi gerekir.
En iyisi üç katmanlı vurgu:
Talimat bloğu (chunk) açık renkle
İlgili cümle koyu renkle
Atıf yapılan çizim de çerçeveyle
Gerekçenizde küçük bir düzeltme: Bağlamı chunk alanı korur, cümle vurgusu ise kesin yeri gösterir. İkisi birbirinin alternatifi değil, birbirini tamamlar. Cümle bulunamazsa chunk vurgusu yedek olarak kalır.

**K5.** ColPali sayfayı buluyor. Neden yine de "cevap vermez" diyoruz? Cevabı üretmek için ne gerekir?
> **C:** çümnkü o görselden metin cıkartamıyor 
🟡 Kısmen doğru. Yön doğru, ama ColPali'nin sorunu sadece "görselden metin çıkaramamak" değil. ColPali bir arama modeli: Çıktısı metin değil vektör. Soruyu ve sayfayı karşılaştırıp bir benzerlik puanı veriyor, hiç metin üretmiyor.

Benzetme: Kütüphanenin arama sistemi gibi. Kitabın hangi rafta olduğunu gösteriyor ama kitabı okuyup size anlatmıyor.
Cevap için gereken: Görseli okuyabilen üretici bir model (VLM). Sayfa resmi ve soru birlikte VLM'e verilir, VLM cevabı yazar. Bu, 5. bölümdeki B seçeneği. Alternatif olarak sayfa OCR'dan geçirilip metin bir LLM'e verilebilir.

---

## 7. Derlenmiş Notlar

### 3.1 Citation / grounding
- Chunk'lar promptta numaralandırılır, LLM sadece **[n]** yazar. Sayfa ve bbox **metadata'dan** gelir.
- Cevap kullanıcıya gitmeden önce numara geçerliliği, alıntı ve sayı kontrolü yapılır (rag-temelleri.md S11 ile birlikte).
- Hedef detay seviyesi: **chunk / paragraf**. İdeali cümle seviyesi.

### 3.2 Sayfayı görsele çevirme
- Kullanıcı öncesini/sonrasını okumak ve yakınlaştırmak isteyeceği için **B (tarayıcıda PDF.js)** öne çıkıyor.
- Prototip: **`streamlit-pdf-viewer`** (PDF.js tabanlı, bbox vurgusu ve vurguya otomatik kaydırma destekli). Para maliyeti yok, efor düşük.
- Yedek: A (sunucuda render, PyMuPDF/pypdfium2, 150 DPI) + önceki/sonraki sayfa butonları + "dokümanı aç" (`#page=N`) bağlantısı.
- Karar noktası: Kullanıcıya dokümanın tamamının gitmesi gizlilik açısından kabul edilebilir mi? (req.md Q9, Adım 7). Nihai seçim Adım 6'da.

### 3.3 Vurgulama
- Başlangıç: **chunk bbox'larını** yarı saydam kutu olarak çizmek (her zaman çalışır).
- Geliştirme: LLM alıntısını sayfada **metin aramasıyla** bulup cümle seviyesinde koyu vurgu.
- Koordinat dönüşümü: `piksel = point × DPI / 72`, orijin tutarlılığı kontrol edilecek.

### 3.4 Multimodal retrieval
- ColPali / ColQwen: Sayfa resmini doğrudan arar. Tablo/çizimde güçlü, ama depolama ve GPU maliyetli, sayfa seviyesinde çalışır, cevap için ayrıca VLM gerekir.
- **Görsel anlama bir ihtiyaç** (gerçek spec/manuellerde dikiş, ölçü ve makine görselleri var). İki ayrı iş: **bulmak** (ColPali veya görsel açıklaması üzerinden metin araması) ve **anlamak** (her durumda VLM gerekir).
- **Önerilen başlangıç: A + B.** Ingestion'da her görsele VLM ile metin açıklaması (bulmak için), cevap anında ilgili görselin resmini VLM'e vermek (anlamak için). Tek arama sistemi, kesin bbox vurgusu, kontrollü maliyet.
- **ColPali:** Açıklamalar arama için yetersiz kalırsa ikinci arama kanalı olarak eklenir. Pilotta A+B ile C+B karşılaştırılacak.
- Karar test dokümanlarına göre değil, **gerçek dokümanlardaki görsel türlerine** göre kesinleşecek (req.md Q3).

### Faz 1 kontrol noktası (deneme planı)

Planda Faz 1 sonu için tanımlı kontrol noktası: *"Bir manualden bir chunk'ı sayfa no + bbox ile çıkarıp, o sayfayı highlight'lı gösterebiliyor muyuz?"*

**Deneme:**
1. Ceket şartnamesinin (dijital) dikiş sayfasını **Docling** ile parse et → öğeler + sayfa + bbox.
2. Dikiş paragrafını içeren öğeyi seç.
3. Vurguyu iki yolla göster: (a) **`streamlit-pdf-viewer`** ile PDF'i açıp bbox'ı annotation olarak ver, otomatik kaydırma çalışıyor mu bak; (b) karşılaştırma için sayfayı 150 DPI'da PNG'ye çevirip bbox'ı ölçekleyerek sarı kutu çiz.
4. Aynısını taranmış pantolon şartnamesinde (OCR ile) ve bir Brother kılavuzu sayfasında tekrarla.
5. **Başarı ölçütü:** Kutu gözle bakıldığında doğru paragrafın üstüne düşüyor mu?
6. **Sayfa geçişi kontrolü:** Sayfa sonunda başlayıp sonraki sayfada biten bir paragraf seç. Tek chunk olarak birleşmiş mi, araya üst/alt bilgi girmiş mi, iki sayfada da doğru vurgulanıyor mu?

Bu deneme pdf-isleme.md **2.3** (araç denemesi) ile birlikte yapılacak.

---

## Kaynaklar

- [ColPali: Efficient Document Retrieval with Vision Language Models (makale)](https://arxiv.org/pdf/2407.01449v1) · [ICLR 2025](https://mlanthology.org/iclr/2025/faysse2025iclr-colpali)
- [The rise of vision-driven document retrieval for RAG (Vespa)](https://blog.vespa.ai/the-rise-of-vision-driven-document-retrieval-for-rag/)
- [What exactly is ColPali? (Decoding ML)](https://decodingml.substack.com/p/the-king-of-multi-modal-rag-colpali)
- [Searching complex documents with ColPali (Elastic)](https://www.elastic.co/jp/search-labs/blog/elastiacsearch-colpali-document-search)
- [Reproducibility of Visual Document Retrieval with Late Interaction](https://arxiv.org/pdf/2505.07730)
- [Hybrid-vector Retrieval for Visually Rich Documents](https://awesomepapers.io/similarity-search/papers/kim2025hybrid)
- [ColPali vs OCR (Mixpeek)](https://mixpeek.com/comparisons/colpali-vs-ocr) · [Visual document retrieval guide](https://mixpeek.com/guides/visual-document-retrieval)
- [ColPali (Emergent Mind özet)](https://www.emergentmind.com/topics/colpali)
