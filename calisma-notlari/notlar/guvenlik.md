# Veri Güvenliği ve Erişim (Adım 7)

> **Başlangıç:** 2026-10-09
> **İlgili plan:** [req.md, Adım 7](../req.md) · Sorulacaklar: [sorulacaklar.md](sorulacaklar.md) (A1, A2) · Önceki: [pdf-isleme.md](pdf-isleme.md) ("VLM ile şekil açıklaması veri güvenliğini etkiler mi?"), [rag-temelleri.md 1.7](rag-temelleri.md) (metadata filtreleme), [kaynak-gosterme.md 3. bölüm](kaynak-gosterme.md) (Q9), [tts.md](tts.md), [arayuz-orkestrasyon.md](arayuz-orkestrasyon.md), [llm-degerlendirme.md](llm-degerlendirme.md)

> **Durum:** Bu adımın kararlarının çoğu [sorulacaklar.md](sorulacaklar.md)'deki cevaplara (Q1, 7.1, 7.3, Q5, internet) bağlı. Bu not, cevaplar gelince hızlı karar verebilmek için **seçenekleri ve sonuçlarını** hazırlıyor.

---

## 0. Kavramlar

### 0.1 sistemde hangi veriler var?

 Sistemdeki veri türleri:

| Veri | Örnek | Ne kadar hassas |  Hukuki Temel |
|------|-------|-----------------|-------------|
| **Müşteri manuelleri** | Nike tedarikçi şartnamesi, ölçü tabloları | 🔴 Yüksek. Müşterinin **ticari sırrı**, genelde NDA kapsamında | Sözleşme (NDA), ticari sır |
| **Manuelden türeyen veriler** | Chunk metinleri, **embedding vektörleri**, sayfa resimleri, VLM açıklamaları | 🔴 Manuelle aynı. Vektörler de veriden türetilir, içerikleri kısmen geri çıkarılabilir (doğrulanmalı) | Aynı |
| **Cevaplar** | "Dış dikiş 11 (± 1) SPI [1]" + alıntı | 🔴 Manuelden alıntı içerir | Aynı |
| **Kullanıcı soruları ve denetim izi (log)** | "Nike ceket SPI?" + kim sordu, ne zaman | 🟡 Kullanıcı adıyla birlikte **kişisel veri.** Hangi markada çalışıldığını da gösterir | **KVKK** + sözleşme |
| **Ses kayıtları** (STT varsa) | Kullanıcının sesli sorusu | 🟡 Kişisel veri (ses kişiyi tanımlayabilir) | KVKK |
| **Kullanıcı hesapları** | Ad, rol, yetkili markalar | 🟡 Kişisel veri | KVKK |
|


### 0.2 Ticari sır (NDA) ve kişisel veri (KVKK)


| | **NDA / ticari sır** | **KVKK (kişisel veri)** |
|---|---|---|
| Neyi korur? | Müşterinin işini (şartname, ölçüler, üretim bilgisi) | **Gerçek kişileri** (ad, ses, davranış kayıtları) |
|Ne olabilir? | Manueller ve onlardan türeyen her şey | Kullanıcı hesapları, loglar, ses |
| Kural nereden? | **Müşteriyle yapılan sözleşmeden** (her müşteride farklı olabilir) | **Kanundan** (herkes için aynı) |
| Bulut için soru | "Sözleşme üçüncü tarafa / yurt dışına göndermeye izin veriyor mu?" | "Yurt dışına aktarım için gereken güvenceler var mı?" |

**Neden önemli?** Manueller büyük ihtimalle kişisel veri **değil** (içinde kişi adı yoksa), yani KVKK'dan çok **NDA** konusu. Ama sistemin logları ve kullanıcı hesapları **KVKK** konusu.

### 0.3 Veri sorumlusu, veri işleyen, yurt dışına aktarım

| Terim | Anlamı | Kim |
|-------|--------|-------|
| *Veri sorumlusu* (data controller) | Verinin neden ve nasıl işleneceğine karar veren |  |
| *Veri işleyen* (data processor) | Sorumlu adına veriyi işleyen | Bulut sağlayıcı (OpenAI, Anthropic, Microsoft, Google, AWS) |
| *Alt işleyen* (sub-processor) | İşleyenin kullandığı başka şirket | Ör. bir model sağlayıcının kullandığı veri merkezi |
| *DPA* (Data Processing Agreement) | Veri işleme sözleşmesi | Bulut sağlayıcılarının kurumsal sözleşme ekleri |
| *Yurt dışına aktarım* | Verinin Türkiye dışındaki bir sunucuya gitmesi | Bulut API'leri genelde yurt dışında |

**KVKK'da 2024 değişikliği:** 7499 sayılı Kanun ile yurt dışı aktarım rejimi değişti. Kısaca: (1) yeterlilik kararı varsa ona göre, (2) yoksa **uygun güvenceler**: en yaygını **standart sözleşme** (imzadan sonra **5 iş günü içinde Kurum'a bildirim**), (3) o da yoksa sınırlı istisnai haller. **Açık rıza artık yurt dışı aktarım için kalıcı bir dayanak değil** (geçiş süresi 1 Eylül 2024'te bitti). Bildirim yapılmazsa idari para cezası var.

**anlamı:** Buluta **kişisel veri** gidecekse (kullanıcı adı, ses kaydı) standart sözleşme süreci gerekebilir. Buluta **sadece cevap metni / chunk** gidiyorsa ve içinde kişisel veri yoksa KVKK yükü azalır, ama **NDA sorusu** (0.2) yine geçerli. Tasarım önerisi: **Buluta kişisel veri göndermemek** (kullanıcı adı, kimlik bilgisi isteklere eklenmez, ses lokal yazıya çevrilir veya hiç kaydedilmez).

### 0.4 Veri saklama, eğitimde kullanma, sıfır saklama (ZDR)

Bulut bir LLM'e metin gönderdiğimizde üç ayrı soru var:

| Soru | Terim | Tipik durum (ücretli API, doğrulanmalı) |
|------|-------|----------------------------------------|
| Gönderdiğim veriyle model **eğitilir** mi? | *Training use* | Ücretli API'lerde **varsayılan olarak hayır.** Ücretsiz katmanlarda / tüketici uygulamalarında evet olabilir |
| Sağlayıcı veriyi **ne kadar saklar?** | *Data retention* | Sağlayıcıya göre değişiyor: Hiç saklamamak ile kötüye kullanım denetimi için ~30 gün arası |
| **Hiç saklanmaması** mümkün mü? | *Zero Data Retention (ZDR)* | Çoğu sağlayıcıda **başvuru / kurumsal sözleşme ile**, ve **sadece bazı uç noktalarda (endpoint) ve modellerde** |

**Kötüye kullanım denetimi (*abuse monitoring*):** Sağlayıcılar, hizmetlerinin yasa dışı işlerde kullanılmasını engellemek için istekleri otomatik tarar ve bazen bir süre saklar. Bazı sağlayıcılarda bu saklama ve **insan incelemesi** başvuruyla kapatılabiliyor.


### 0.5 Veri yerleşimi (*data residency*)

Verinin **hangi ülkede/bölgede** işlendiği ve saklandığı. Bazı müşteri sözleşmeleri "veri AB dışına çıkamaz" veya "Türkiye'de kalmalı" diyebilir.
- Büyük bulut platformları (Azure, AWS, Google Cloud) **bölge seçimi** sunuyor. Ör. Azure'da "EU Data Zone": İstekler AB ülkelerinden birinde işlenir, saklanan veri seçilen coğrafyada kalır.
- Doğrudan model sağlayıcı API'lerinde (OpenAI, Anthropic, Google AI Studio) bölge seçeneği daha sınırlı olabilir (bazılarında var, doğrulanmalı).
- **Türkiye'de kalma şartı varsa** büyük bulut LLM'leri pratikte zorlaşır → lokal (on-prem) çözüm.

### 0.6 Kimlik doğrulama ve yetkilendirme

| Terim | Soru | Sistem |
|-------|------|-------|
| **Kimlik doğrulama** (*authentication*) | "Sen kimsin?" | Kullanıcı girişi (şirket hesabıyla tek giriş, SSO) |
| **Yetkilendirme** (*authorization*) | "Neyi görmeye iznin var?" | Kullanıcı A sadece Nike manuellerini görebilir |
| **Rol tabanlı erişim** (*RBAC*) | Yetkiler rollere bağlanır | "Nike hattı ekibi" rolü → Nike markası |
| **En az yetki ilkesi** (*least privilege*) | Herkes sadece işi için gerekene erişir | Varsayılan: hiçbir marka, rolle açılır |



### 0.7 LLM'e özgü güvenlik riskleri

(OWASP)

| Risk | Ne demek | Nasıl olabilir | Önlem |
|------|----------|---------------------|-------|
| **Prompt injection** (talimat enjeksiyonu, LLM01) | Metnin içine gizlenmiş bir talimatın modeli yönlendirmesi | Bir dokümanın içinde "önceki kuralları unut" gibi bir cümle (dolaylı enjeksiyon). Müşteri manuellerinde olası değil, ama dış kaynaklı doküman eklenirse mümkün | Kaynakları "veri" olarak işaretlemek (prompt-taslak.md kural 10), **yetki kararını asla LLM'e bırakmamak**, çıktı doğrulaması |
| **Hassas bilgi ifşası** (LLM02) | Modelin görmemesi gereken kişiye gizli bilgi göstermesi | Adidas yetkisi olmayan kullanıcıya Adidas chunk'ı gelmesi | **Yetki filtresi retrieval'dan önce** (7.3) |
| **Vektör ve embedding zayıflıkları** (LLM08, 2025'te yeni) | Vektör DB'nin yetkisiz erişime açık olması, yetki filtresinin unutulması | Tüm markaların vektörleri tek koleksiyonda, filtre unutulursa sızıntı | Yetki farkındalığı olan retrieval, test (7.3) |
| **Sistem talimatı sızıntısı** (LLM07) | Sistem talimatının kullanıcıya gösterilebilmesi | Sistem talimatımızda gizli bir şey yok | Sistem talimatına **sır koymamak** (API anahtarı, yetki kuralı vb.) |

**Ana ilke:** **Güvenlik kararları LLM'in dışında, kodda verilir.** LLM'e "Adidas'ı gösterme" demek bir güvenlik önlemi **değildir.** Adidas chunk'ı LLM'e hiç ulaşmamalıdır.

### 0.8 Veri nereden nereye gidiyor? (sistemin veri akışı)

```
INGESTION (doküman eklenirken, BİR KEZ, dokümanın TAMAMI işlenir)
  PDF ──► Parse / OCR ──► (VLM: şekil açıklaması) ──► Chunk ──► Embedding ──► Vektör DB
          [☁ bulut OCR?]   [☁ bulut VLM?]                       [☁ bulut embedding?]

SORGU (her soruda, sadece İLGİLİ PARÇALAR işlenir)
  Soru ──► (STT) ──► Embedding ──► Vektör DB (yetki filtresi) ──► Rerank ──► LLM ──► Doğrulama ──► TTS
          [☁ STT?]   [☁?]                                                     [☁ LLM?]              [☁ TTS?]
                                                                     │
  Ekran: cevap + PDF sayfası (yetki kontrolü) + ses                 └──► Denetim izi (log)
```

**Önemli gözlem:** Bulut kullanımında **riskin büyüklüğü hangi adımda** kullanıldığına göre çok farklı:
- **Ingestion'da bulut** (OCR, VLM, embedding) → Her dokümanın **tamamı** dışarı gider.
- **Sorguda bulut LLM** → Her soruda sadece **3–5 parça** (ve sadece sorulan konular) dışarı gider.

Bu ayrım, aşağıdaki "hibrit" senaryonun (7.2, Senaryo B) temeli.

---

## 1. Anlatım

### 7.1 Gizlilik gereksinimleri

#### Müşteri sözleşmelerinde (NDA) bakılacak maddeler
 "bulut kullanabilir miyiz?" diye genel sormak yerine, sözleşmelerde şu maddelere bakılması daha hızlı sonuç verir: 

| # | Madde | Neden önemli |
|---|-------|--------------|
| 1 | **Üçüncü taraflarla paylaşım** yasağı var mı? Bulut sağlayıcı (veri işleyen) "üçüncü taraf" sayılıyor mu? | Q1'in doğrudan cevabı |
| 2 | **Alt yüklenici / hizmet sağlayıcı** kullanımı için müşterinin **yazılı izni** gerekiyor mu? | İzin alınabilirse bulut mümkün |
| 3 | **Coğrafi kısıt** var mı? ("Türkiye dışına çıkamaz", "AB içinde kalmalı") | Veri yerleşimi (0.5) |
| 4 | **Saklama ve imha:** Sözleşme bitince dokümanların ve **kopyalarının** silinmesi isteniyor mu? | Türetilmiş veriler (chunk, vektör, sayfa resmi, log) de silinmeli → silme süreci tasarlanmalı |
| 5 | **Güvenlik standartları** (şifreleme, erişim kaydı, ISO 27001 vb.) şart koşuluyor mu? | Teknik önlem listesi |
| 6 | **İhlal bildirimi** yükümlülüğü var mı? | Olay müdahale süreci |
| 7 | Dokümanın **amaç sınırlaması** var mı? ("Sadece üretim için kullanılabilir") | Yapay zekâ sisteminde işlemek bu amaca uyuyor mu? |
| 8 | **Yapay zekâ / otomatik işleme** hakkında özel bir madde var mı? (Yeni sözleşmelerde görülmeye başladı, doğrulanmalı) | Doğrudan cevap |

> **Pratik bir yol:** Sözleşme bulut kullanımına açıkça izin vermiyorsa, **müşteriden yazılı izin** istemek bir seçenek. Özellikle "kurumsal bulut, AB bölgesi, veri saklamama, eğitimde kullanmama" gibi güvencelerle. Bu bir iş kararı (sorulacaklar.md A1).

#### KVKK açısından yapılacaklar (kişisel veri işlenen kısımlar)

| Konu | Ne gerekir |
|------|-------------------------------------|
| **Çalışanların bilgilendirilmesi** | Sistem kullanıcı sorularını ve kimliğini logluyorsa çalışanlara **aydınlatma metni** |
| **Log saklama süresi** | Denetim izi ne kadar tutulacak? (Ör. 1 yıl, sonra anonimleştirme veya silme) |
| **Ses kaydı** (STT olduğu durumda) | Kaydedilmemesi (yazıya çevirip hemen silmek) en basit yol |
| **Yurt dışı aktarım** | Buluta kişisel veri gidecekse standart sözleşme + bildirim. **Tasarımla kaçınılabilir:** İsteklere kullanıcı kimliği eklenmez |
| **Erişim** | Logları kim görebilir? (Sadece sistem yöneticisi ve kalite sorumlusu gibi) |

### 7.2 Bulut mu, on-prem mi? (bileşen bileşen)

#### Bileşen tablosu

| Bileşen | Ne zaman | Buluta ne gider | Hassasiyet | Lokal alternatif | Lokal donanım |
|---------|----------|-----------------|------------|------------------|---------------|
| **OCR** | Ingestion | Taranmış sayfa **resimlerinin tamamı** | 🔴 Tüm doküman | Docling içi OCR, Surya, Tesseract | CPU yeterli, GPU hızlandırır |
| **VLM** (şekil açıklaması) | Ingestion | **Tüm çizimler** | 🔴 Tüm çizimler | Lokal açık VLM (Qwen-VL ailesi vb.) | GPU (ingestion yavaş olabilir, kullanıcı beklemez) |
| **Embedding** | Ingestion + sorgu | **Tüm chunk metinleri** + sorular | 🔴 Tüm doküman metni | `bge-m3` (zaten önerilen, lokal) | CPU'da çalışır, GPU hızlandırır |
| **Vektör DB** | Sürekli | Tüm chunk'lar + vektörler (bulut DB kullanılırsa) | 🔴 | Qdrant (Docker, lokal) | CPU, disk |
| **Reranker** | Sorgu | Soru + aday chunk'lar | 🟡 | `bge-reranker-v2-m3` (lokal) | GPU önerilir |
| **LLM** | Sorgu | Soru + 3–5 chunk + (gerekirse sayfa resmi) | 🟡 Parçalar | Açık model ~27–32B (llm-degerlendirme.md) | **24 GB GPU** |
| **TTS** | Sorgu | Kısa sesli cevap metni | 🟡 Küçük parça | Chatterbox Multilingual (tts.md) | GPU önerilir |
| **STT** | Sorgu | Kullanıcının **sesi** | 🟡 + **kişisel veri** | Whisper / faster-whisper | GPU önerilir |
| **Uygulama sunucusu, loglar** | Sürekli | Her şey | 🔴 | Şirket içi sunucu | — |

**Gözlem:** Lokal yapılması **en kolay** olanlar (embedding, vektör DB, reranker, OCR) aynı zamanda dışarıya **en çok veri gönderenler.** Lokal yapılması **en zor** olan (büyük LLM) ise dışarıya **en az veri gönderen.** Bu, hibrit bir çözümü doğal hale getiriyor.

#### Üç senaryo

| | **A. Tamamen bulut** | **B. Hibrit** (önerilen ara çözüm) | **C. Tamamen lokal (on-prem)** |
|---|---|---|---|
| **Lokal** | Sadece arayüz | Ingestion (parse, OCR, embedding), vektör DB, reranker, loglar, (STT) | Her şey |
| **Bulut** | OCR, VLM, embedding, LLM, TTS, STT | **LLM** (+ TTS, + ingestion'da VLM gerekirse), **kurumsal sözleşmeyle** | Hiçbiri |
| **Dışarı giden** | Dokümanların tamamı + sorular | Soru başına 3–5 parça + kısa cevap metni | Hiçbir şey |
| **Kalite** | En yüksek | Yüksek (en kritik adım olan cevap üretimi bulut modeliyle) | Lokal LLM'e bağlı (pilotta ölçülecek) |
| **Donanım** | Yok | Orta (embedding + reranker için küçük/orta GPU veya güçlü CPU) | Yüksek (LLM için 24 GB+ GPU, ayrıca VLM, TTS, STT) |
| **Hukuki yük** | En yüksek | Orta (tek sağlayıcı sözleşmesi, ZDR) | En düşük |
| **Ne zaman uygun** | Sözleşmeler açıkça izin veriyor | Sözleşmeler kurumsal güvencelerle buluta izin veriyor (veya müşteri izni alınabiliyor) | Bulut kesin yasak, veya veri Türkiye'de kalmalı |

**Test aşaması (şimdi):** Public dokümanlarla çalıştığımız için A serbest. Ama mimari **B'ye ve C'ye geçilebilecek şekilde** kurulmalı:
- Her bileşen bir "adaptör" arkasında: `llm = BulutLLM(...)` ya da `llm = LokalLLM(...)`, kodun geri kalanı aynı. (arayuz-orkestrasyon.md 6.3'teki modüler yapı.)
- Embedding ve vektör DB **baştan lokal** (`bge-m3` + Qdrant zaten öyle önerildi). Böylece gerçek veriye geçişte en çok veri gönderen adımlar zaten içeride.

#### Bulut sağlayıcıların veri politikaları

| Sağlayıcı | Eğitimde kullanım (ücretli API) | Varsayılan saklama | ZDR | Bölge seçimi |
|-----------|--------------------------------|--------------------|-----|--------------|
| **Anthropic (Claude API)** | Hayır (açık izin olmadan) | İçerik varsayılan olarak saklanmıyor. **İstisna:** "Covered Models" (Fable / Mythos) 30 gün saklama gerektiriyor | Var (Messages API için, onaylı). Covered Models ZDR dışında | İşlem bölgesi seçeneği var (`inference_geo`, doğrulanmalı). AWS Bedrock / Google Cloud / Microsoft Foundry üzerinden de |
| **OpenAI (doğrudan API)** | Hayır | Kötüye kullanım denetimi için ~30 gün (kaynaklara göre) | Var, **satış ekibi üzerinden başvuru**, uç noktaların bir kısmı uygun değil | Bazı bölgesel seçenekler (doğrulanmalı) |
| **Azure OpenAI / Microsoft Foundry** | Hayır | Kötüye kullanım denetimi ~30 gün | "Değiştirilmiş denetim" (insan incelemesi yok) ve ZDR **başvuruyla**, kurumsal sözleşme (EA / MCA) gerekir | ✅ Güçlü: **EU Data Zone** (işlem AB içinde) |
| **Google Gemini API** | Ücretli katmanda hayır, **ücretsiz katmanda evet** | Kötüye kullanım tespiti için sınırlı süre loglama | Var (koşullu) | Vertex AI (Google Cloud) üzerinden bölge seçimi |

> **Dikkat:** "ZDR açık" demek her özelliğin kapsandığı anlamına gelmiyor. Dosya yükleme, toplu işlem (batch), sohbet geçmişi saklayan özellikler gibi **durum tutan** özellikler kendi saklama kurallarına sahip olabiliyor.  kullanımımız basit (tek istek → tek cevap) olduğu için ZDR kapsamında kalması kolay. Ama hangi API özelliklerini kullandığımız sözleşmeyle karşılaştırılmalı.
>
> **Şirketin zaten bir bulut sözleşmesi varsa** (sorulacaklar.md Q1-a), aynı platform üzerinden model kullanmak (ör. Azure'da OpenAI, AWS'de Claude) yeni bir sağlayıcı sözleşmesi yerine **mevcut sözleşmeyi** kullanmak demek. Hukuki süreç kısalır.

### 7.3 Marka bazlı yetkilendirme

#### Kim neyi görmeli? 

Olası modeller:

| Model | Kural | Ne zaman |
|-------|-------|----------|
| **Herkes her şeyi görür** | Yetki yok, sadece giriş | Tüm müşteriler sözleşmede iç paylaşıma izin veriyorsa, az kullanıcı varsa |
| **Marka bazlı** | Kullanıcının rolü → izinli markalar ("Nike hattı" → Nike) | Müşteri sözleşmeleri "sadece ilgili ekip görebilir" diyorsa |
| **Marka + doküman türü** | Ör. makine kılavuzları herkese açık, marka şartnameleri ekibe özel | Karma ihtiyaç (muhtemel) |
| **Doküman bazlı** | Her dokümanın kendi erişim listesi | Çok hassas tekil dokümanlar varsa |

**Tahmini en olası ihtiyaç:** Makine kılavuzları ve genel terzilik kaynakları **herkese açık**, marka şartnameleri **marka ekibine özel.** Kesin cevap paydaşlardan.

#### Nasıl uygulanır?

```
Kullanıcı girişi (SSO) ──► kullanıcının grupları ──► izinli markalar listesi
                                                        │
Soru ──► Retrieval:  filtre = (brand IN izinli_markalar) VE (diğer filtreler)
                       ▲ ZORUNLU, KODDA, SUNUCUDA eklenir. Arayüz veya LLM kararı değil.
     ──► LLM sadece filtreden geçmiş chunk'ları görür
     ──► PDF görüntüleyici: doküman isteği AYNI yetki kontrolünden geçer
     ──► Denetim izi: kim, neyi sordu, hangi dokümanlar gösterildi
```

**Uygulama kuralları:**

| # | Kural | Neden |
|---|-------|-------|
| 1 | **Yetki filtresi retrieval'dan ÖNCE** (pre-filter) uygulanır | Sonradan filtrelemek (post-filter) güvenli değil: Yetkisiz chunk zaten LLM'in bağlamına girmiş olabilir. Rag-temelleri.md 1.7'de seçilen pre-filter yöntemi burada güvenlik için de doğru |
| 2 | Filtre **sunucu tarafında, her istekte** eklenir. Kullanıcının seçtiği marka kutusu sadece **daraltır**, genişletemez | "Marka: Tümü" seçen kullanıcı yine sadece izinli markalarında arar |
| 3 | **Yetki kararı LLM'e bırakılmaz** | 0.7: Prompt'taki kural güvenlik değildir |
| 4 | **Her erişim noktası** aynı kontrolden geçer: arama, PDF/sayfa görüntüleme, "dokümanın tamamını aç" bağlantısı, önceki sorular, sesli cevap | Sızıntı en çok unutulan yan kapılardan olur (ör. PDF indirme bağlantısı) |
| 5 | **Varsayılan: kapalı** | Markası atanmamış bir doküman kimseye görünmez (ya da sadece yöneticiye), "herkese açık" etiketi bilinçli verilir |
| 6 | **Yetki değişiklikleri hemen geçerli olur** | Yetkiler vektör DB'ye kopyalanmaz, her sorguda kullanıcının **güncel** gruplarından hesaplanır. Dokümanın markası metadata'da, kullanıcının yetkisi kimlik sisteminde |
| 7 | **Önbellek (cache) kullanıcılar arasında paylaşılmaz** | "Bu soru daha önce soruldu, cevabı hazır" önbelleği varsa, farklı yetkili kullanıcıya başkasının cevabı gitmemeli |
| 8 | **Test:** Yetkisiz marka soruları test setine eklenir | "Nike yetkili kullanıcı Adidas sorusu soruyor → 'bulunamadı' / yetki yok" (llm-degerlendirme.md 4.4'e yeni tür: **yetki testi**) |

#### Vektör DB'de iki yol (Qdrant)

| Yol | Nasıl | Artı | Eksi |
|-----|-------|------|------|
| **Tek koleksiyon + filtre** (*payload filter*) | Tüm markalar aynı koleksiyonda, her chunk'ta `brand`, `access` alanı. Sorguda filtre | Basit, esnek (doküman türü bazlı karma kurallar kolay). Qdrant filtrelemede güçlü | **Filtreyi unutan tek bir kod satırı sızıntı demek.** Bu yüzden filtre tek bir yerden (merkezi fonksiyon) eklenmeli ve test edilmeli |
| **Marka başına ayrı koleksiyon** | Her marka ayrı koleksiyonda, kullanıcı sadece izinli koleksiyonlarda arar | **Yapısal ayrım:** Filtre unutulsa bile başka markanın verisine ulaşılamaz. Müşteri sözleşmesi bitince silmek kolay (koleksiyonu sil) | Çok markalı aramalar ve ortak dokümanlar (makine kılavuzları) için birden fazla koleksiyonda arayıp birleştirmek gerekir |

**Öneri:** Pilot (tek marka) için fark yok. Üretimde: **Tek koleksiyon + merkezi zorunlu filtre + yetki testleri** ile başlanır. Müşteri sözleşmeleri **sıkı ayrım** istiyorsa (ör. "verimiz diğer müşterilerin verisiyle aynı yerde tutulamaz") marka başına koleksiyona geçilir.

**Silme (7.1 madde 4) için:** Her chunk, vektör, sayfa resmi ve VLM açıklaması `doc_id` ile bağlı tutulur. "Bu dokümanı ve türevlerini sil" tek bir işlemle yapılabilmeli. Loglardaki alıntılar için ayrıca bir kural gerekir.

### 7.4 Diğer temel güvenlik önlemleri (kısa liste)

| Önlem | Neden |
|-------|-------|
| **API anahtarları** koda yazılmaz, ortam değişkeni veya sır yöneticisinde tutulur | Anahtar sızarsa başkası bizim adımıza (ve bizim sözleşmemizle) istek yapar |
| **Kurumsal hesap**, bireysel/ücretsiz hesap değil | Ücretsiz katmanlarda veri eğitimde kullanılabilir (0.4) |
| **Şifreleme:** Aktarımda (HTTPS) ve diskte (manuel dosyaları, vektör DB, loglar) | Standart |
| **LLM cevabı ekranda düz metin olarak** gösterilir (HTML olarak işlenmez) | Cevaba karışan bir kodun tarayıcıda çalışmasını engellemek |
| **Erişim kaydı** (denetim izi, arayuz-orkestrasyon.md 6.3) | Kim neyi gördü sorusuna cevap. Hem güvenlik hem R4 (yanlış dikim şikâyetinde geriye dönük inceleme) |
| **Test verisi ile gerçek veri ayrımı** | Public test ortamında kullanılan bulut ayarları gerçek veriye geçişte **kendiliğinden** taşınmamalı. Gerçek veriye geçiş bir kontrol listesiyle yapılır (Faz 6) |

---

## 2. Kontrol soruları

**K1.** Müşteri manuelleri ile kullanıcı logları neden farklı hukuk kurallarına tabi? Her biri için kime, hangi soruyu sorarız?
> **C:**  müşteri manualleri nda içerisine dahildir, kullanıcı lofları ise kvkk kapsamındadır. birini kvkk sorumlusuna sorarken diğerini bir hukukcuya sorabiliriz 

🟡 Ayrım doğru. "Neden" kısmı ve sorulacak sorular eksik.

- **Neden farklı:**
  - **Manueller** müşterinin **işini** korur (ticari sır). Kural **sözleşmeden** gelir, bu yüzden **her müşteride farklı** olabilir. İçlerinde kişi bilgisi olmadığı sürece KVKK kapsamında değildir.
  - **Loglar** (kim, ne zaman, ne sordu) **gerçek kişileri** tanımlar. Kural **kanundan** (KVKK) gelir, herkes için aynıdır.
- **Kime, hangi soru:**
  - Hukuk / sözleşme sorumlusu: "Müşteri sözleşmeleri dokümanların bulut bir hizmete (üçüncü taraf, yurt dışı) gönderilmesine izin veriyor mu?" Bakılacak 8 madde 7.1'de.
  - KVKK sorumlusu: "Kullanıcı sorularını ve kimliklerini ne kadar saklayabiliriz? Çalışanlara aydınlatma metni gerekir mi? Ses kaydı işleyebilir miyiz? Buluta kişisel veri giderse yurt dışı aktarım süreci gerekir mi?"
- **Not:** İkisi aynı kişi de olabilir (şirketin hukuk birimi). Önemli olan kişi değil, **iki ayrı sorunun** ayrı ayrı sorulması.

**K2.** Bulut kullanımında ingestion aşaması (OCR, VLM, embedding) ile sorgu aşaması (LLM) arasında veri güvenliği açısından ne fark var? Hibrit senaryo bu farktan nasıl yararlanıyor?
> **C:**  ingestionda kullandığında tüm belgeler ve tüm veriler bulutla dış kaynağa gönderilmiş olur,  sorgu sırasında yapıldığında ise belirli chunklar gönderilmiş olur 

🟡 Fark doğru açıklanmış. Sorunun ikinci yarısı (hibrit senaryo) eksik.

- **Hibrit senaryo bu farktan nasıl yararlanıyor?** İlginç bir denk gelme var:
  - En çok veri gönderen adımlar (OCR, embedding, vektör DB) **lokalde yapması en kolay** olanlar: `bge-m3` CPU'da bile çalışır, Qdrant ve OCR araçları ücretsiz.
  - En az veri gönderen adım (cevap üreten LLM) **lokalde yapması en zor** olan: büyük model, pahalı GPU.
  - Hibrit senaryo bu yüzden **kolay ve çok veri gönderen adımları içeride tutup**, sadece zor ve az veri gönderen LLM'i (ve kısa metinli TTS'i) **kurumsal sözleşmeli bulutta** çalıştırıyor. Kalite yüksek kalıyor, dışarı çıkan veri minimuma iniyor.
- **Ek faydalar:**
  - Sorguda bile dışarı çıkan sadece **kullanıcıların sorduğu konular.** Hiç sorulmayan bölümler hiç gönderilmez.
  - İndeks (vektörler) içeride olduğu için bulut sağlayıcı değiştirmek veya ileride tamamen lokale (C) geçmek, dokümanları yeniden işlemeyi gerektirmez.

**K3.** Sistem talimatına "Kullanıcı Nike yetkilisi ise Adidas bilgisi verme" yazmak neden yeterli bir güvenlik önlemi değil? Doğrusu ne?
> **C:** yetki sınırlandırmak daha doğrudur, sistem llm tabanlı olduğu için uydurmalar yapabilir 

🟡 Yön doğru ("yetkiyi sınırlamak"), ama hem gerekçe hem çözüm somutlaştırılmalı.

- **Neden yetmez? (uydurmadan daha fazlası):**
  1. **Bilgi zaten LLM'e ulaşmış olur.** Talimat "verme" diyor ama Adidas chunk'ı modelin önünde duruyor. Yani bulut senaryosunda Adidas verisi zaten dışarı gönderilmiş, yetkisi olmayan bir işlemde kullanılmış oluyor.
  2. **Model kurala her zaman uymaz.** Bu bir olasılık meselesi: Çoğu zaman uyar, bazen uymaz. Güvenlikte "çoğu zaman" yetmez.
  3. **Kural atlatılabilir.** Kullanıcı soruyu dolambaçlı sorabilir ("Diğer markaların değerleriyle karşılaştır") ya da bir dokümanın içine gizlenmiş bir talimat modeli yönlendirebilir (prompt injection, 0.7).
  4. Sistem talimatı **gizli değildir**, kullanıcı tarafından ortaya çıkarılabilir (OWASP LLM07).
- **Doğrusu:** Yetkisiz bilgi **LLM'e hiç ulaşmaz.** Kullanıcının izinli markaları kimlik sisteminden alınır, **arama yapılmadan önce** sunucuda, merkezi bir fonksiyonda filtre olarak eklenir. LLM sadece filtreden geçmiş parçaları görür, "Adidas'ı gösterme" diye bir karar vermesine gerek kalmaz. Varsayılan "kapalı", ve yetki testleri test setinde.

**K4.** Arama tarafında marka filtresi doğru çalışıyor. Ama kullanıcı yetkisi olmayan bir dokümanı yine de görebilir mi? Hangi "yan kapılar" kontrol edilmeli?
> **C:** 

❌ Cevaplanmamış. Doğru cevap: **Evet, görebilir.** Arama sistemin sadece bir kapısı. Doküman başka yollardan da kullanıcıya ulaşabiliyor:

| Yan kapı | Nasıl sızar | Önlem |
|----------|-------------|-------|
| **PDF görüntüleyici / "dokümanın tamamını aç"** | Görüntüleyici PDF'i bir adresten (ör. `/pdf/nike-spec.pdf`) alıyor. Kullanıcı adresi değiştirip `/pdf/adidas-spec.pdf` yazarsa? | Her PDF/sayfa isteğinde de **aynı yetki kontrolü** |
| **Önceki sorular / geçmiş** | Ekrandaki "önceki sorular" listesi başka kullanıcıların sorularını ve cevaplarını gösterirse | Geçmiş kişiye özel, ya da yetki filtresinden geçer |
| **Önbellek (cache)** | "Bu soru daha önce soruldu, cevabı hazır" önbelleği yetkisi farklı birine başkasının cevabını verebilir | Önbellek kullanıcılar arasında paylaşılmaz (ya da yetki kümesine göre ayrılır) |
| **Sesli cevap dosyaları** | Üretilen ses dosyaları herkese açık bir klasörde duruyorsa | Aynı yetki kontrolü, geçici dosyalar silinir |
| **Loglar / denetim izi** | Logları gören kişi tüm markaların alıntılarını görür | Log erişimi kısıtlı (yönetici, kalite sorumlusu) |
| **Sayfa resimleri, VLM açıklamaları** | Önceden üretilmiş sayfa resimleri doğrudan erişilebilir bir klasördeyse | Statik dosya olarak açık bırakılmaz |
| **Marka seçme kutusu** | Kullanıcı arayüzde "Adidas" seçerse filtre genişler mi? | Arayüz seçimi sadece **daraltır**, sunucu her zaman izinli markalarla kesiştirir |

**Genel ilke:** Yetki kontrolü bir "ekran" özelliği değil, **veriye dokunan her uç noktanın** (endpoint) özelliği.

**K5.** Bir bulut sağlayıcının "verilerinizi eğitimde kullanmıyoruz" demesi ile "sıfır veri saklama (ZDR)" arasındaki fark ne? Hangisi bizim için yeterli olabilir, kim karar verir?
> **C:** zdr olduğunda belirli durumlar dışında verimin tutulmadığına dair daha da eminliğim olur ama eğitimde kullanmaması saklamadığı anlamına gelmez 

🟡 Fark çok iyi yakalanmış ("eğitimde kullanmamak saklamamak demek değil"). "Hangisi yeterli, kim karar verir" kısmı eksik.

- **Fark ✅:**
  - "Eğitimde kullanmıyoruz": Veri modeli geliştirmek için kullanılmaz, ama **bir süre saklanabilir** (ör. kötüye kullanım denetimi için ~30 gün) ve bu sürede sınırlı durumlarda insanlar tarafından incelenebilir.
  - ZDR: İstek işlendikten sonra **saklanmaz** (yasal zorunluluklar gibi istisnalar hariç). Genelde **başvuruyla** verilir ve **her özelliği kapsamaz.**
- **Hangisi yeterli?** Teknik olarak karar veremeyiz, **müşteri sözleşmesine bağlı:**
  - Sözleşme "üçüncü tarafla paylaşma" diyorsa ikisi de yetmeyebilir (veri yine fiziksel olarak dışarı çıkıyor) → müşteri izni veya lokal (senaryo C).
  - Sözleşme "güvenlik önlemleri al" diyorsa: Asgari "eğitimde kullanmama + kurumsal sözleşme", daha güçlüsü **ZDR + bölge seçimi (AB) + kötüye kullanım incelemesinin kapatılması.** Bizim önerimiz hibrit senaryoda bu güçlü seti hedeflemek.
- **Kim karar verir?** **Hukuk birimi** (müşteri sözleşmelerine göre) ve gerekirse **müşterinin kendisi** (yazılı izin). BT ve biz seçenekleri ve sağlayıcıların güvencelerini hazırlarız (7.2'deki tablo), kararı onlar verir.

---

## 3. Derlenmiş Notlar

### 7.1 Gizlilik gereksinimleri
- İki ayrı hukuk: Manueller ve türevleri **NDA / ticari sır** (müşteri sözleşmesi), kullanıcı hesapları, loglar ve ses **KVKK.**
- NDA'da bakılacak 8 madde: üçüncü taraf, alt yüklenici izni, coğrafi kısıt, saklama/imha, güvenlik standartları, ihlal bildirimi, amaç sınırlaması, yapay zekâ maddesi. Sözleşme izin vermiyorsa müşteriden yazılı izin bir seçenek.
- KVKK: Aydınlatma metni, log saklama süresi, ses kaydetmeme, yurt dışı aktarımda standart sözleşme + bildirim (2024 değişikliği, hukukla teyit). **Tasarım ilkesi: Buluta kişisel veri gönderme.**

### 7.2 Bulut vs. on-prem
- Ingestion'da bulut = dokümanın **tamamı** dışarı. Sorguda bulut LLM = soru başına **3–5 parça.** En çok veri gönderen bileşenler (embedding, vektör DB, OCR) lokal yapması en kolay olanlar.
- Üç senaryo: **A** tamamen bulut, **B** hibrit (ingestion + embedding + vektör DB + reranker lokal, LLM ve TTS kurumsal bulut + ZDR), **C** tamamen lokal (24 GB+ GPU).
- Test aşamasında A serbest, ama mimari adaptörlerle **B ve C'ye geçilebilir** kurulur. Embedding ve vektör DB baştan lokal.
- Sağlayıcı politikaları: Ücretli API'lerde eğitimde kullanım yok (varsayılan), saklama ~0–30 gün, ZDR başvuruyla ve kısmi kapsamlı, bölge seçimi en güçlü Azure / büyük bulut platformlarında. **Mevcut bir bulut sözleşmesi varsa** onun üzerinden model kullanmak hukuki süreci kısaltır.

### 7.3 Marka bazlı yetkilendirme
- Muhtemel ihtiyaç: Makine kılavuzları herkese açık, marka şartnameleri marka ekibine özel (paydaşlardan teyit).
- **Yetki filtresi retrieval'dan önce, sunucuda, merkezi bir fonksiyonda, her istekte.** Arayüz sadece daraltır. LLM'e bırakılmaz. Varsayılan kapalı. Yetkiler her sorguda güncel gruplardan hesaplanır.
- **Yan kapılar:** PDF görüntüleme / indirme, "dokümanın tamamını aç", önceki sorular, önbellek, sesli cevap, loglar.
- Qdrant: Tek koleksiyon + zorunlu filtre ile başla, sözleşme sıkı ayrım isterse marka başına koleksiyon.
- Test setine **yetki testleri** eklenir. Doküman ve türevlerinin tek işlemle silinebilmesi tasarlanır.

### Proje için ilk öneri

| Konu | Öneri | Alternatif | Karar neye bağlı |
|------|-------|-----------|------------------|
| **Mimari** | Adaptörlü, A/B/C arasında geçilebilir. Embedding + vektör DB + reranker baştan lokal | — | — |
| **Gerçek veri senaryosu** | **B. Hibrit** (LLM ve TTS kurumsal bulut + ZDR + bölge seçimi) | C. Tamamen lokal | Q1, NDA maddeleri, müşteri izni, Q5 (GPU), internet |
| **Bulut sağlayıcı** | Şirketin mevcut bulut platformu (varsa) üzerinden | Doğrudan model sağlayıcı API'si | Q1-a, pilot sonuçları (llm-degerlendirme.md) |
| **Kişisel veri** | Buluta gönderilmez (kimlik yok, ses lokal veya kaydedilmez) | Standart sözleşme süreci | KVKK sorumlusu |
| **Yetkilendirme** | SSO + rol → marka, pre-filter, merkezi zorunlu filtre, varsayılan kapalı | Marka başına koleksiyon | 7.3 cevabı, NDA "ayrım" maddesi |
| **Denetim izi** | Her soru loglanır, erişim kısıtlı, saklama süresi belirlenir | — | KVKK sorumlusu |

**Açık kalanlar:** Hepsi [sorulacaklar.md](sorulacaklar.md)'de: Q1, Q1-a, 7.1 (NDA maddeleri), 7.3, KVKK, Q5, internet, giriş (SSO). Yeni eklenenler: müşteriden izin alınabilir mi, log saklama süresi, silme yükümlülüğü.

---

## Kaynaklar

**Resmi dokümanlar (sağlayıcılar)**
- [Anthropic: API ve veri saklama (ZDR, Covered Models)](https://platform.claude.com/docs/en/manage-claude/api-and-data-retention)
- [Microsoft: Azure OpenAI / Foundry veri gizliliği (Data Zone, kötüye kullanım denetimi)](https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy)
- [Google: Gemini API sıfır veri saklama](https://ai.google.dev/gemini-api/docs/zdr?hl=en) · [Gemini API fiyatlandırma (ücretsiz/ücretli katman veri kullanımı)](https://ai.google.dev/gemini-api/docs/pricing)
- [Qdrant: Multitenancy ve özel sharding](https://qdrant.tech/documentation/production-operations/multitenant-search/) · [Qdrant multitenancy makalesi](https://qdrant.tech/articles/multitenancy/)

**KVKK (ikincil kaynaklar, hukukla teyit edilmeli)**
- [Yurt dışına kişisel veri aktarımı rehberi neleri düzenliyor? (Erdem & Erdem)](https://www.erdem-erdem.av.tr/bilgi-bankasi/yurt-disina-kisisel-veri-aktarimi-rehberi-neleri-duzenliyor)
- [KVKK standart sözleşme bildirim modülü duyurusu (Alomaliye)](https://www.alomaliye.com/2024/10/30/kvkk-standart-sozlesme-bildirim-modulu/)
- [Standart sözleşme bildirim yükümlülüğü ve yaptırımları (Cottgroup)](https://www.cottgroup.com/en/legislation/item/standart-sozlesme-bildirim-yukumlulugu-ve-yaptirimlari)
- [Veri merkezi / bulut hizmet sözleşmeleri ve veri lokalizasyonu (Hukukçular Evi)](https://hukukcularevi.com/danismanlik/veri-merkezi-bulut-hizmet-sozlesmeleri-veri-lokalizasyonu/)

**LLM güvenliği (ikincil, doğrulanmalı)**
- [OWASP Top 10 for LLM Applications 2025 özeti (Confident AI)](https://www.confident-ai.com/blog/owasp-top-10-2025-for-llm-applications-risks-and-mitigation-techniques) · [Outpost24 özeti](https://outpost24.com/blog/owasp-top-10-llm-risks-explained/)
- [Vector store access control for RAG (tianpan.co, 2026)](https://tianpan.co/blog/2026/04/17/vector-store-access-control-rag-rls)
- [LlamaIndex: Qdrant ile hybrid RAG, multitenancy](https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid_rag_multitenant_sharding)

**Sağlayıcı politikaları (ikincil, doğrulanmalı)**
- [OpenAI ZDR kapsamı ve uygun olmayan uç noktalar (ecorpit)](https://ecorpit.com/openai-zero-data-retention-limits-endpoints-india-residency-2026/) · [ZDR ne gerektirir (spotdev)](https://www.spotdev.co.uk/blog/openai-zero-data-retention)
- [Azure OpenAI veri saklama politikası (anarlog)](https://anarlog.so/blog/azure-open-ai-data-retention-policy/)
