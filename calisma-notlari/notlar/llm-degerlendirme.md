# LLM Seçimi ve Yanıt Kalitesi (Adım 4)

> **Başlangıç:** 2026-10-09
> **İlgili plan:** [req.md, Adım 4](../req.md) · Prompt taslağı: [prompt-taslak.md](prompt-taslak.md) · Önceki: [rag-temelleri.md](rag-temelleri.md) (özellikle **S11**), [kaynak-gosterme.md](kaynak-gosterme.md), [tts.md](tts.md), [arayuz-orkestrasyon.md](arayuz-orkestrasyon.md) · Sorulacaklar: [sorulacaklar.md](sorulacaklar.md)



---

## 0. Kavramlar

### 0.1 LLM nedir, bizim sistemde ne iş yapıyor?

**Ne demek?** *Large Language Model* (büyük dil modeli): Çok büyük miktarda metinle eğitilmiş, verilen metnin devamını tahmin ederek cevap yazan model. ChatGPT, Claude, Gemini bunun örnekleri.

**sistemdeki rolü dar ve belirli:** LLM **bilgi kaynağı değil, okuyucu ve yazar.** Bilgi manuellerden gelir (retrieval). LLM'in işi:
1. Getirilen 3–5 parçayı (chunk) **okumak**,
2. Soruya cevap veren kısmı **bulmak** (ve kelimesi kelimesine **alıntılamak**),
3. Cevabı Türkçe, kısa ve **kaynak numarasıyla** yazmak,
4. Kaynaklarda cevap yoksa **"bulunamadı" demek.**



**Neden önemli?** Model seçerken "en bilgili" modeli değil, **en iyi açık kitap öğrencisini** arıyoruz: Verilen metne sadık, Türkçe yazabilen, İngilizce metni doğru okuyan, bilmediğini söyleyebilen.

### 0.2 Token, bağlam penceresi ve fiyatlandırma

| Terim | Türkçesi | Anlamı | Bizim için |
|-------|----------|--------|------------|
| *Token* | Jeton, metin parçası | Modelin okuduğu/yazdığı en küçük birim. Kabaca İngilizcede ~¾ kelime. **Türkçe eklemeli bir dil olduğu için aynı metin genelde daha çok token tutar** | Fiyat ve hız token'a göre |
| *Context window* | Bağlam penceresi | Modelin tek seferde okuyabildiği token sayısı (ör. 128K, 1M) | Bizim istekler küçük (~3–5K token). Bağlam penceresi **sorun değil** |
| *Input / output tokens* | Girdi / çıktı | Gönderilen (soru + chunk'lar + talimat) ve üretilen (cevap) token'lar. **Çıktı genelde 4–6 kat pahalı** | Cevaplar kısa olduğu için maliyet düşük |
| *Reasoning / thinking tokens* | Düşünme token'ları | Yeni modellerin cevaptan önce "içinden düşünmesi". Çıktı olarak faturalanır | Doğruluğu artırabilir, gecikme ve maliyeti artırır. Ayarlanabilir |
| *Prompt caching* | İstem önbelleği | Her istekte aynı olan kısım (sistem talimatı) önbellekten okunur, ~%90 ucuz | Sistem promptu her soruda aynı → otomatik tasarruf |

### 0.3 Bulut API mi, açık ağırlıklı (lokal) model mi?

- **Bulut API (kapalı model):** Model sağlayıcının sunucusunda çalışır (OpenAI, Anthropic, Google). Biz internet üzerinden metin gönderir, cevap alırız. Token başına ödeme.
- **Açık ağırlıklı model (*open-weight*):** Modelin ağırlıkları (eğitilmiş "beyni") indirilebilir. **Kendi bilgisayarımızda/sunucumuzda** çalıştırırız. Veri dışarı çıkmaz. Lisansa dikkat (tts.md 0.7'deki ağırlık lisansı konusunun aynısı).

| Terim | Anlamı |
|-------|--------|
| *Parametre* (7B, 27B, 70B) | Modelin büyüklüğü (milyar parametre). Büyük model genelde daha iyi, ama daha çok bellek ister |
| *Quantization* (niceleme, ör. 4-bit, Q4) | Modeli sıkıştırmak. Bellek ihtiyacı ~4 kat düşer, kalite biraz düşer. Lokal kullanımda standart |
| *VRAM* | Ekran kartının belleği. Lokal modelin sığıp sığmayacağını belirler |
| *Ollama, llama.cpp, vLLM* | Lokal model çalıştırma araçları. Ollama en kolayı, vLLM çok kullanıcılı sunucu için |


**Karar?** Q1 (bulut kabul mü) ve Q5 (GPU var mı). Bkz. [sorulacaklar.md](sorulacaklar.md) A1, A2.

### 0.4 Prompt, sistem promptu ve yapılandırılmış çıktı

| Terim | Anlamı | Bizim için |
|-------|--------|------------|
| *Prompt* | Modele verilen metin (talimat + veri + soru) | Her soruda: kurallar + numaralı chunk'lar + soru |
| *System prompt* (sistem talimatı) | Sabit "görev tanımı ve kurallar" kısmı. Her soruda aynı | "Sadece verilen kaynaklardan cevap ver..." ([prompt-taslak.md](prompt-taslak.md)) |
| *Temperature* | Rastgelelik ayarı. Düşük = tutarlı, tekrarlanabilir | Düşük tutulur. (Bazı yeni modellerde bu ayar kaldırıldı, yerini "düşünme derinliği / effort" ayarı aldı) |
| *Structured output* (yapılandırılmış çıktı) | Modelin cevabı **belirli bir şemada** (JSON) vermesinin zorunlu kılınması | Cevabı serbest metin değil `{cevap, alıntılar, kaynaklar, sesli_metin, bulunamadı}` alanları olarak alırız → **kod kontrol edebilir** (4.3). Tüm büyük sağlayıcılar ve çoğu lokal çalıştırıcı destekliyor |

**Neden yapılandırılmış çıktı bu kadar önemli?** S11 Katman 5'teki otomatik kontroller (alıntı chunk'ta var mı, sayı kaynakta var mı) için cevabın **parçalarını ayrı ayrı** almak gerekiyor. 

### 0.5 RAG'de halüsinasyon türleri

RAG sisteminde görülen türleri : 

| Tür | Örnek | Hangi katman yakalar (4.3) |
|-----|-------|---------------------------|
| **Kaynakta olmayanı eklemek** | Kaynak "11 (± 1) SPI" der, cevap "11 SPI, ayrıca 3 mm dikiş payı bırakın" (dikiş payı kaynakta yok) | Alıntı zorunluluğu, sayı kontrolü |
| **Değeri yanlış kopyalamak** | "11 (± 1)" → "11 (± 2)" veya "12" | **Sayı kontrolü** |
| **Toleransı / birimi düşürmek** | "11 (± 1) SPI" → "11 SPI" (tolerans kayboldu) | Sayı kontrolü (tolerans da sayı) |
| **Yanlış kaynağı birleştirmek** | Ceketin değerini (11 ± 1) pantolon sorusuna vermek | Metadata filtresi, kaynak gösterme, kullanıcı sayfada görür |
| **Yanlış modele ait cevap** | S-7300A sorusuna S-7300B kılavuzundan cevap | `product_model` filtresi, doküman adı ekranda |
| **Kendi genel bilgisini kullanmak** | Kaynak yetersizken "genelde 10–12 SPI kullanılır" demek | Sistem kuralı + eşik + alıntı zorunluluğu |
| **Bilmediğini söylememek** | Kaynakta cevap yokken bir şey uydurmak | Eşik (LLM hiç çağrılmaz), "bulunamadı" kuralı |
| **Çeviri hatası** | İngilizce "shall not exceed 12" → Türkçe "12 olmalı" (anlam değişti: üst sınır vs. kesin değer) | Alıntı (orijinal İngilizce cümle ekranda), kullanıcı sayfada görür |

> Son satır önemli:  sistemde **dil geçişi** var (İngilizce manuel → Türkçe cevap). "shall", "minimum", "not to exceed", "approximately" gibi ifadelerin anlamı çeviride kaymamalı. Bu yüzden **orijinal cümle (alıntı) her zaman ekranda** gösterilir.

### 0.6 Değerlendirme (evaluation) nedir, neden şart?

**Ne demek?** Sistemin ne kadar iyi çalıştığını **sayıyla** ölçmek. "Bence iyi cevap veriyor" yerine "50 test sorusunun 46'sında doğru sayfayı buldu, 44'ünde değeri doğru verdi, cevabı olmayan 10 sorunun 9'unda 'bulunamadı' dedi."

**Neden şart?**
- Model seçimini **bizim verimizde** yapmak için (genel sıralamalar bizim görevimizi ölçmüyor).
- Bir değişikliğin (yeni prompt, yeni model, yeni chunking) **iyileştirdi mi bozdu mu** olduğunu görmek için.
- Pilotun **başarılı sayılıp sayılmayacağına** karar vermek için (req.md 6.3).

| Terim | Anlamı |
|-------|--------|
| *Test seti / altın set (gold set)* | Cevabı ve geçtiği sayfa **önceden bilinen** sorular (req.md 0.4) |
| *Retrieval metrikleri* | Doğru chunk getirildi mi? Recall@k, MRR (rag-temelleri.md 1.5'te anlatıldı) |
| *Faithfulness* (sadakat) | Cevaptaki her iddia getirilen kaynaklarda var mı? |
| *Answer relevance* (ilgililik) | Cevap soruyu gerçekten cevaplıyor mu? |
| *Abstention* (cevaptan kaçınma) | Cevabı olmayan soruda "bulunamadı" demek. Bizim için **doğru davranış** |
| *LLM-as-judge* (LLM hakem) | Cevabı başka bir LLM'e puanlatmak. Hızlı ama kendisi de hata yapabilir, insan kontrolüyle kalibre edilmeli |

---

## 1. Anlatım

### 4.1 Model seçenekleri

#### Seçim kriterleri (bizim görev için)

| # | Kriter | Neden | Nasıl ölçülür |
|---|--------|-------|---------------|
| 1 | **Kaynağa sadakat** (uydurmamak) | R4 | Test setinde faithfulness + değer doğruluğu |
| 2 | **Bilmediğini söyleme** | S11 Katman 2–3 | Cevabı olmayan sorularda abstention oranı |
| 3 | **Türkçe yazma + İngilizce okuma** | Q2: EN manuel, TR cevap | Test seti (çapraz dil soruları) |
| 4 | **Talimat ve şemaya uyma** | Yapılandırılmış çıktı, kaynak no, alıntı kuralı | Şemaya uymayan / alıntısız cevap oranı |
| 5 | Gecikme | arayuz-orkestrasyon.md 6.2 (Süre sorusu) | Soru başına saniye |
| 6 | Maliyet | Bütçe sorusu | Aylık tahmin (aşağıda) |
| 7 | Gizlilik / çalışma yeri | Q1 | Bulut mu, lokal mi, sözleşme |
| 8 | Görsel okuma (VLM) | kaynak-gosterme.md 5. bölüm: çizimli sayfalarda B seçeneği | Görsel test soruları |


#### Bulut modeller (resmi fiyat sayfaları, 2026-10-09, 1M token başına USD)

| Sağlayıcı | Model | Girdi | Çıktı | Not |
|-----------|-------|-------|-------|-----|
| **Anthropic** | Claude Opus 5.5 | 4,00 | 20,00 | Üst seviye. 1M bağlam |
| | Claude Sonnet 5.5 | 2,00 | 10,00 | Orta seviye |
| | Claude Haiku 5.5 | 0,10 | 0,50 | Küçük ve hızlı |
| **OpenAI** | gpt-5.6-sol | 4,00 | 20,00 | Üst seviye |
| | gpt-5.6-terra | 2,00 | 12,00 | Orta seviye |
| | gpt-5.6-luna | 0,20 | 1,20 | Küçük ve hızlı |
| **Google** | gemini-3.1-pro-preview | 2,00 | 12,00 | "Preview" (önizleme) aşamasında |
| | gemini-3.8-flash | 0,75 | 3,75 | 1 Ocak 2027'de fiyat iki katına çıkacak (resmi sayfa) |
| | gemini-3.1-flash-lite | 0,25 | 1,50 | Küçük |

**Ortak özellikler:** Hepsi Türkçe destekliyor, hepsi görsel okuyabiliyor (VLM), hepsi yapılandırılmış çıktı ve önbellek destekliyor. **Aynı modeller Azure, AWS ve Google Cloud üzerinden de** (kurumsal sözleşmeyle) kullanılabiliyor: Örn. OpenAI modelleri Azure'da, Claude modelleri AWS Bedrock / Google Vertex / Microsoft Foundry'de. Şirketin zaten bir bulut sözleşmesi varsa (sorulacaklar.md Q1-a) bu önemli.

**Veri kullanımı (genel durum, doğrulanmalı):**
- Ücretli API'lerde gönderilen veri **varsayılan olarak modeli eğitmek için kullanılmıyor** (Google'ın resmi sayfası: ücretsiz katmanda "ürünleri geliştirmek için kullanılır", ücretli katmanda "kullanılmaz").
- Veriler kötüye kullanım denetimi için **bir süre saklanabiliyor** (genelde ~30 gün). **Sıfır saklama** (*zero data retention*, ZDR) çoğu sağlayıcıda **ayrı başvuru/sözleşme** ile mümkün. Bazı en üst modellerde ZDR sunulmayabiliyor (ör. Anthropic'in Fable modeli 30 gün saklama gerektiriyor).
- **Ücretsiz katmanlar / tüketici uygulamaları (ChatGPT, Gemini uygulaması) müşteri verisi için kullanılmamalı.**

#### Açık ağırlıklı (lokal) modeller

| Aile | Lisans | Türkçe | Not |
|------|--------|--------|-----|
| **Qwen** (Alibaba) | Çoğu boyut **Apache-2.0** (en büyük amiral model özel lisanslı, doğrulanmalı) | ✅ Çok dilli | Bir Türkçe doküman QA çalışmasında 7B boyutta **en iyi doğruluk/hız dengesi** (aşağıda) |
| **Gemma** (Google) | Kaynaklar çelişiyor: Apache-2.0 mı "Gemma License" mı (**model kartından doğrulanmalı**) | ✅ | Küçük boyutlar, cihaz üstü kullanım |
| **Mistral** | Small / Large serisinde Apache-2.0 (doğrulanmalı) | 🟡 | Aynı çalışmada Türkçede zayıf kaldı |
| **Llama** (Meta) | Meta topluluk lisansı (kullanım politikası, isim şartı, bölgesel koşullar) | ✅ | Lisans koşulları diğerlerinden karmaşık |
| **Türkçe uyarlanmış modeller** (Trendyol-LLM, Cosmos Turkish-Llama, Kocdigital vb.) | Modele göre değişiyor | ✅✅ | Türkçeye özel eğitilmiş. Ama "Türkçe uyarlama her zaman daha iyi değil" (aşağıda) |
| DeepSeek, Kimi, GLM, MiMo (büyük) | Çeşitli (çoğu serbest) | ? | Genel sıralamaların tepesinde, ama çok büyük (yüzlerce milyar parametre), lokalde çalıştırmak pahalı |

**Türkçe ve doküman QA hakkında bulunan en ilgili kanıt** ([arXiv 2609.28007](https://arxiv.org/html/2609.28007), 2026, doğrulanmalı):
- 5 açık model (7–8B), Türkçe doküman üzerinde retrieval'lı soru-cevap, **6 GB VRAM'li dizüstü GPU**, 4-bit.
- Doğruluk: Trendyol-LLM-8B %75, **Qwen2.5-7B %65**, Cosmos %54, Mistral %51, Kocdigital %49.
- Hız: Qwen2.5 **1,7 sn/soru**, Trendyol **23,9 sn/soru** ("düşünme modu" yüzünden ~14 kat yavaş).
- "Bilmiyorum" deme (20 cevapsız sorudan): Qwen2.5 19, Cosmos 18, Trendyol 18, Mistral 13, Kocdigital 9.
- Yazarların sonucu: **Türkçeye özel uyarlama, doküman tabanlı başarıyı garanti etmiyor.** Model seçimi, retrieval ve donanım ayrı ayrı ölçülmeli.
- **Bizim için anlamı:** 7–8B modeller ~%50–75 doğrulukta kalıyor. Bizim "yanlış değer = yanlış dikim" riskimiz için **bu seviye yeterli değil.** Lokal gidilecekse daha büyük model (ve buna yetecek GPU) gerekir. Ayrıca bu çalışma eski nesil (Qwen2.5) modellerle, yeni nesil daha iyi olabilir, **ölçülmeli.**

**Genel Türkçe benchmark'lar:** TurkishMMLU, TR-MMLU, **CETVEL** (EACL 2026). CETVEL'in bulgusu da aynı: Türkçeye özel modeller genelde genel amaçlı çok dilli modelleri geçemiyor. Ama bu benchmark'lar **genel bilgi ve dil** ölçüyor, bizim "verilen metne sadakat" görevimizi değil. Seçim **kendi test setimizle** yapılmalı.

#### Lokal donanım ihtiyacı 
| Model boyutu | Gereken VRAM (yaklaşık) | Örnek donanım | Bizim için |
|--------------|-------------------------|---------------|------------|
| 7–8B | ~5–8 GB | Dizüstü / giriş seviyesi GPU | Doğruluk muhtemelen yetersiz (yukarıdaki çalışma) |
| 14B | ~10–12 GB | 12–16 GB GPU | Ara seçenek |
| **27–32B** | **~18–24 GB** | **24 GB GPU (tek kart)** | **Lokal için makul hedef.** Ölçülmeli |
| 70B | ~40–48 GB | 2× 24 GB veya 48 GB kart | Daha iyi, pahalı |
| 100B+ / MoE | 80 GB+ | Sunucu GPU'ları | Pilot için fazla |

> GPU yoksa (Q5) lokal LLM pratikte zor: CPU'da 7B model bile soru başına onlarca saniye sürebilir.
> **Aynı GPU'yu paylaşacak diğer işler:** Embedding (bge-m3), reranker, ingestion'da VLM, belki TTS (Chatterbox) ve STT (Whisper). Lokal senaryoda GPU bütçesi **toplamda** düşünülmeli.

#### Kabaca maliyet (bulut)

Varsayım: Günde 200 soru, ayda ~6.000 soru. Soru başına ~4.000 girdi token'ı (sistem talimatı + 5 chunk + soru), ~600 çıktı token'ı (cevap + alıntılar + sesli metin), düşünme token'ları hariç.

| Seviye | Örnek model | ~Aylık |
|--------|-------------|--------|
| Üst | Claude Opus 5.5 / gpt-5.6-sol | ~170 $ |
| Orta | Claude Sonnet 5.5 / gpt-5.6-terra / gemini-3.1-pro | ~85–95 $ |
| Hızlı / ucuz | gemini-3.8-flash | ~30 $ |
| Küçük | Claude Haiku 5.5 / gpt-5.6-luna / gemini-3.1-flash-lite | ~5–10 $ |

**Sonuç:** Bu ölçekte LLM maliyeti de TTS gibi **karar verdirici değil.** Düşünme token'ları ve görsel (sayfa resmi) gönderimi maliyeti birkaç kat artırabilir, yine de yönetilebilir. Kararı **doğruluk (bizim test setimizde) ve gizlilik (Q1)** verecek. Sistem talimatı önbelleğe alındığı için girdi maliyeti daha da düşer.

#### Model seçim yöntemi 

1. **Test aşaması (public veri, bulut serbest):** Her sağlayıcıdan **bir orta seviye model** (3 aday) + bir küçük model aynı test setinde, **aynı prompt ve aynı chunk'larla** çalıştırılır. Sonuç: Bulut için "üst sınır" ve "yeterli olan en ucuz" model.
2. **Lokal aday (Q1 = bulut yok ihtimaline karşı):** Apache-2.0 lisanslı bir açık model (ör. Qwen ailesinden 27–32B sınıfı) aynı test setinde. Fark küçükse gerçek veride lokal kullanılabilir. (Pdf-isleme.md'deki VLM planıyla aynı mantık: bulut = üst sınır referansı, lokal = gerçek veri adayı.)
3. **Karar ölçütü** (4.4): Önce **değer doğruluğu ve doğru reddetme**, sonra faithfulness, sonra gecikme ve maliyet.
4. Bu ölçüm **pilotta** yapılır (araştırma aşamasında deneme yok, bkz. req.md 6.1).

### 4.2 Prompt tasarımı

Taslak sistem promptu ve çıktı şeması ayrı dosyada: **[prompt-taslak.md](prompt-taslak.md)**. Tasarım ilkeleri:

| İlke | Neden |
|------|-------|
| **Rol ve sınır:** "Sadece verilen kaynaklardan cevap ver. Kendi genel bilgini kullanma." | - |
| **Önce alıntı, sonra cevap** | Model önce kanıtı bulur, cevabı kanıta dayandırır. Kod alıntıyı kontrol edebilir (S11 Katman 4) |
| **Sayısal değerler sadece alıntıdan** | Değer kopyalama hatasını azaltır |
| **Her iddia için kaynak numarası [n]** | Sayfa/bbox metadata'dan gelir, model sayfa numarası yazmaz  |
| **"Bulunamadı" açık bir seçenek olarak tanımlanır** (şemada ayrı alan) | Modelin "bir şey söylemek zorunda" hissetmesini engeller |
| **Çelişkiyi bildir, seçme** | Ceket 11 ± 1, pantolon 10–14: İkisi de geliyorsa ikisini de kaynaklarıyla yaz (R3) |
| **Soru belirsizse sor** | "Hangi ürün için? Ceket mi pantolon mu?" |
| **Çeviri kuralları:** "shall / minimum / maximum / not to exceed / approximately" anlamlarını koru, birimleri dönüştürme | 0.5'teki çeviri hatası. Birim dönüşümü (inç → cm) model tarafından yapılmaz. Gerekirse **kod** yapar ve "yaklaşık" diye işaretler |
| **Yapılandırılmış çıktı (JSON şeması)** | Kodun alıntı/sayı/kaynak kontrolü yapabilmesi için |
| **Sesli metin ayrı alan** (tts.md 2.5) | Kısa, rakamlı, kaynak numarasız |
| **Kullanıcının sorusu ve doküman içeriği "veri"dir, talimat değil** | Doküman içindeki bir cümlenin modele talimat gibi davranmasını engellemek (*prompt injection*). Müşteri dokümanlarında olası değil ama ucuz bir önlem |

### 4.3 Halüsinasyon azaltma  (S11'in ayrıntılı hali)

Rag-temelleri.md S11'deki beş katman, her biri için **nasıl yapılacağı** ile:

```
Soru
 │
 ▼ KATMAN 1: Doğru bilgiyi getir (retrieval)
 │   metadata filtresi (marka, model, doküman türü) + hybrid + rerank
 ▼ KATMAN 2: Eşik
 │   en iyi rerank skoru < eşik  ──► "Bulunamadı" (LLM hiç çağrılmaz)
 ▼ KATMAN 3: Sıkı prompt (4.2)
 ▼ KATMAN 4: Önce alıntı, sonra cevap (yapılandırılmış çıktı)
 ▼ KATMAN 5: Otomatik doğrulama
 │   a) kaynak no geçerli mi?    b) alıntı chunk'ta birebir var mı?
 │   c) cevaptaki her sayı/tolerans/kod alıntıda var mı?
 │   d) bulunamadı tutarlılığı
 │   ── başarısız ──► 1 kez yeniden dene ──► yine başarısız ──► "Kaynağı kontrol edin" uyarısı / reddet
 ▼ KATMAN 6: İnsan (kullanıcı) doğrulaması
     cevap + orijinal alıntı + vurgulu sayfa + doğrulama rozeti aynı ekranda
```

#### Katman 2: Eşik nasıl belirlenir?

Eşik kafadan seçilmez, **test setiyle kalibre edilir** (*calibration*):
- Test setinde cevabı **olan** ve **olmayan** sorular var (4.4).
- Her soru için en iyi rerank skoru kaydedilir.
- Eşik, "cevabı olan soruların çoğu geçsin, cevabı olmayanların çoğu takılsın" noktasına konur.


#### Katman 4: Alıntı birebir mi olmalı?

- Alıntı **kaynak dilinde** (genelde İngilizce) ve **kelimesi kelimesine** istenir. Cevap Türkçe olabilir, alıntı çevrilmez.
- Kontrol: Alıntı, chunk metninde **birebir** (boşluk/satır sonu farkları normalize edilerek) geçiyor mu? OCR'lı metinde küçük farklar olabilir → çok küçük farklara tolerans (*fuzzy match:yaklaşık metin eşleştirme*) tanınabilir, ama **sayılarda tolerans yok.**
- Alıntı aynı zamanda **ekranda cümle vurgusu** için kullanılır (kaynak-gosterme.md 4. bölüm: `search_for(alıntı)`). Tek işlemle iki fayda.

#### Katman 5c: Sayı kontrolü nasıl çalışır?

```
1. Cevaptan ve alıntılardan "sayısal ifadeler" çıkarılır (kod, regex):
   "11 (± 1)", "10-14", "3/16", "½", "E-07", "S-7300A", "146391-001", "301", "LSc-2"
2. Normalize edilir: "½" → 1/2, "10–14" (uzun tire) → 10-14, "± 1" → ±1, boşluklar
3. Cevaptaki HER ifade, atıf yapılan chunk'ların metninde aranır.
4. Bulunamayan ifade varsa → doğrulama başarısız.
```

**Dikkat edilecek ince noktalar:**
- **Tolerans eksikliği de hata:** Kaynakta "11 (± 1)" var, cevapta sadece "11" varsa → uyarı (tolerans düşmüş). Kontrol sadece "cevaptaki sayı kaynakta var mı" değil, **"alıntıdaki sayı-tolerans çifti cevapta da tam mı"** yönünde de yapılır.
- **Çeviri biçim farkları:** Kaynak "1.5 mm", cevap "1,5 mm" → aynı değer. Normalizasyon ondalık ayırıcıyı tanımalı (tts.md 0.3).
- **Birim dönüşümü yapılmışsa** ("1/4 inç ≈ 6,35 mm"): Dönüştürülmüş değer kaynakta yok → kural: Dönüşümü model değil **kod** yapar ve ekranda "dönüştürülmüş, yaklaşık" etiketiyle gösterir.
- **Sesli metindeki sayılar da** aynı kontrolden geçer (tts.md 2.5, K4).

#### Katman 5d: "Bulunamadı" tutarlılığı

- Model "bulunamadı" dediyse cevap alanı boş olmalı.
- Model cevap verdiyse en az bir geçerli alıntı ve kaynak olmalı.
- Model "bulunamadı" dedi ama rerank skoru çok yüksekse → kayıt altına alınır (retrieval doğru ama model kaçınmış olabilir, ya da gerçekten yok). Pilotta incelenir.

#### Doğrulama başarısız olursa ne olur?

| Durum | Davranış |
|-------|----------|
| Alıntı chunk'ta yok | 1 kez yeniden dene ("alıntı kelimesi kelimesine olmalı"). Yine yoksa → cevabı gösterme, "Kaynağı kontrol edin" + kaynak sayfasını göster |
| Cevapta kaynakta olmayan sayı var | **Cevap gösterilmez.** Sadece kaynak sayfası ve alıntı gösterilir: "Bu bilgi için kaynağa bakın" |
| Tolerans düşmüş | Cevap gösterilir ama ⚠ rozet + alıntı vurgulanır |
| Geçersiz kaynak no | Yeniden dene, yine olmazsa reddet |

Tüm başarısızlıklar **denetim izine** (arayuz-orkestrasyon.md 6.3) yazılır. Pilotta "hangi tür hata ne sıklıkla" analiz edilir.

#### Ek önlemler (gerekirse, pilottan sonra)

| Önlem | Ne | Maliyet |
|-------|----|---------|
| İkinci model ile kontrol (*verifier*) | Ayrı bir (küçük) model "bu cevap bu kaynaklara dayanıyor mu?" diye kontrol eder | Ek çağrı, ek gecikme. Kod kontrolleri yetmezse |
| Çapraz dil anlam kontrolü | "shall not exceed" → "en fazla" çevirisi doğru mu? | Kural listesiyle başlanır |
| Sağlayıcının yerleşik atıf özellikleri | Bazı API'ler (ör. Anthropic Citations) cevabı doküman konumlarına bağlayan yerleşik atıf veriyor | Sağlayıcıya bağımlılık. Bizim [n] yöntemimiz sağlayıcıdan bağımsız, önce o |

### 4.4 Değerlendirme yöntemi

#### Test seti (req.md 0.4, sorulacaklar.md A3)

**Yapı:** Her soru için bir kayıt:

```json
{
  "id": "T07",
  "soru": "Ceketin dış görünür dikişlerinde SPI kaç olmalı?",
  "tur": "deger",                       // deger | prosedur | ariza | cevapsiz | tuzak | capraz_dil | gorsel
  "beklenen_doc": "gl-pd-14-04a",
  "beklenen_sayfa": [22, 23],
  "beklenen_degerler": ["11 (± 1)"],
  "beklenen_davranis": "cevapla",       // cevapla | bulunamadi | netlestir
  "not": "Pantolon (10-14) ile karışmamalı"
}
```

**Soru türleri ve neden gerekli:**

| Tür | Örnek | Neyi ölçer |
|-----|-------|------------|
| **Değer** | "Ceket dış dikiş SPI?" | Değer doğruluğu (en kritik) |
| **Prosedür** | "Üst iplik gerginliği nasıl ayarlanır?" | Adımların eksiksizliği |
| **Arıza** | "S-7300A'da dikiş atlıyor" | Arıza tablosu, doğru model |
| **Cevapsız** | "Nike ceketlerde düğme sayısı?" (sette Nike yok) | **Doğru reddetme** |
| **Tuzak** | "S-7300A'da ..." (cevap sadece B'de var) | Yanlış modele ait cevap vermemek |
| **Çapraz dil** | Türkçe soru, İngilizce kaynak | Diller arası retrieval + çeviri doğruluğu |
| **Görsel** | Cevabı sadece çizimde olan soru | Görsel anlama (kaynak-gosterme.md 5. bölüm) |
| **Alan dışı** | "Kahve makinesi kireç nasıl temizlenir?" dikim bağlamında | Doküman türü karışması (manual-envanteri.md) |

**Boyut:** Pilot için **50–100 soru** hedef (10–20 ile başlanır, büyütülür). Her türden yeterli örnek olmalı, özellikle **cevapsız ve tuzak** sorular (gerçek kullanımda en tehlikeli hatalar orada).


#### Metrikler

| Seviye | Metrik | Ne demek | Hedef (taslak, pilot başarı kriteri 6.3 için) |
|--------|--------|----------|-----------------------------------------------|
| Retrieval | **Recall@5** | Doğru sayfa ilk 5 sonuçta mı? | ≥ %90 |
| Retrieval | MRR | Doğru sayfa kaçıncı sırada? | İzlenir |
| Cevap | **Değer doğruluğu** | Beklenen değerler (tolerans dahil) cevapta **tam** mı? | **≥ %98**, yanlış değer = kritik hata |
| Cevap | **Kaynak doğruluğu** | Gösterilen sayfa beklenen sayfa mı? | ≥ %95 |
| Cevap | Faithfulness | Cevaptaki iddialar kaynakta var mı? | ≥ %95 |
| Cevap | Answer relevance | Soruya cevap veriyor mu? | İzlenir |
| Davranış | **Doğru reddetme** | Cevapsız sorularda "bulunamadı" oranı | ≥ %90 |
| Davranış | Gereksiz reddetme | Cevabı olan soruda "bulunamadı" oranı | ≤ %10 (kullanıcı güveni) |
| Davranış | Tuzak başarısı | Yanlış modelden/markadan cevap vermeme | %100 |
| Operasyon | Gecikme | Soru → doğrulanmış cevap | Kullanıcıya sorulacak (sorulacaklar.md "Süre") |
| Operasyon | Maliyet | Soru başına | İzlenir |


**Önemli ayrım:** "Yanlış cevap" ile "cevap yok" aynı şey değil. Bizim için **yanlış değer** en ağır hata, **gereksiz "bulunamadı"** hafif hata (kullanıcı kaynağa kendisi bakar). Metrikler bu ayrımı korumalı, tek bir "doğruluk %" yeterli değil.

#### Araçlar

| Araç | Ne | Bizim için |
|------|----|------------|
| **custom script** | Test setini `soru_cevapla()` ile çalıştırır, kural tabanlı metrikleri (değer doğruluğu, kaynak doğruluğu, reddetme, tuzak) hesaplar | **Temel.** En kritik metrikler zaten kural tabanlı, LLM hakem gerektirmiyor. Sonuçlar tabloya yazılır |
| **RAGAS** | RAG'e özel metrikler (faithfulness, answer relevancy, context precision). LLM hakem kullanır | Faithfulness için. **Türkçe için prompt uyarlama (dil adaptasyonu) özelliği var**, kullanılmalı |
| **DeepEval** | Test çatısı (pytest gibi), 50+ metrik, sürekli entegrasyon (CI) | Değişikliklerin otomatik test edilmesi gerekirse |
| **TruLens** | Üretimde izleme (RAG Triad) | Pilot sonrası canlı izleme için |

**LLM hakem hakkında dikkat:**
- Hakem model, cevap üreten modelden **farklı** olmalı (kendi cevabına yanlı davranabilir).
- Türkçe cevaplarda İngilizce odaklı hakemin güvenilirliği düşebilir → **küçük bir insan etiketli setle karşılaştırılmalı** (ör. 30 cevabı kalite ekibi puanlar, hakemle uyumu ölçülür).
- Bir 2026 kaynağı: Faithfulness yüksek çıksa bile bu sadece "cevap getirilen kaynağa uyuyor" demek, **kaynağın doğru kaynak olduğunu** göstermez (doğrulanmalı). Bu yüzden **kaynak doğruluğu ayrı ölçülüyor.**

#### İnsan değerlendirmesi

Otomatik metrikler gerekli ama yetmez. Pilotta:
- Kalite ekibinden bir kişi rastgele 30–50 cevabı **"bu cevapla dikim yapar mıydım?"** sorusuyla puanlar.
- Kullanıcılardan geri bildirim butonu (👍 / 👎 + "yanlış değer" seçeneği). 
---

## 2. Kontrol soruları


**K1.** Model seçerken neden "en bilgili / genel sıralamalarda en üstteki" modeli değil, "en iyi açık kitap öğrencisini" arıyoruz? Bu ölçüt için hangi metriklere bakarız?
> **C:** çünkü bir cevap üretmesini beklemiyoruz, bizde hazır olan cevaplardan sunmasını bekliyoruz 

🟡 Yön doğru, küçük bir düzeltme ve sorunun ikinci yarısı (metrikler) eksik.

- **Düzeltme:** Model yine de cevap **üretiyor**: İngilizce kaynağı okuyup Türkçe, kısa, atıflı bir cevap yazıyor. Ama ürettiği cevap **sadece verilen kaynağa dayanmalı.** Yani "cevap üretmesin" değil, "**kendi bilgisinden** cevap üretmesin".
- **Neden genel sıralama yetmez:** Genel sıralamalar (benchmark'lar) modelin **ne kadar çok şey bildiğini**, kodlama ve akıl yürütme becerisini ölçer. Bizim görevimiz farklı: "Verilen metne ne kadar sadık, bilmediğinde susuyor mu?" Bilgili bir model, kaynak yetersizken kendi bilgisini ekleme eğiliminde bile olabilir (R4 için kötü).
- **Bakılacak metrikler** (4.4):
  - **Değer doğruluğu**: Sayı ve toleranslar tam ve doğru mu? (En kritik)
  - **Faithfulness (sadakat)**: Cevaptaki her iddia kaynakta var mı?
  - **Doğru reddetme**: Cevapsız sorularda "bulunamadı" diyor mu?
  - **Kaynak doğruluğu / tuzak başarısı**: Yanlış ürün veya modelin kaynağını kullanıyor mu?
  - **Talimata ve şemaya uyma**: Alıntı birebir mi, [n] atıfları var mı?
  - **Çapraz dil doğruluğu**: İngilizce kaynağı Türkçeye anlamı bozmadan aktarıyor mu?

**K2.** Bir Türkçe doküman QA çalışmasında 7–8B açık modeller %49–75 doğruluk aldı. Bu bize lokal model kararında ne söylüyor? Q1 "bulut yasak" çıkarsa ne yaparız?
> **C:** 


- **Ne söylüyor?** 7–8B modeller 100 sorunun 25–50'sini yanlış cevaplıyor.  projede tek bir yanlış değer yanlış dikim demek.
-  Aynı çalışmada Türkçeye özel eğitilmiş modeller her zaman daha iyi çıkmadı. En doğru model (Trendyol) ise 14 kat daha yavaştı. Yani "Türkçe model = daha iyi" ya da "küçük model = yeterli" diye varsaymadan **kendi test setimizde ölçmek** gerekiyor.
- **Dikkat:** Çalışma eski nesil (Qwen2.5) ve tek bir doküman üzerinde. Yeni nesil modeller daha iyi olabilir. Bu bir uyarı işareti, kesin hüküm değil.
- **Q1 = "bulut yasak" çıkarsa:**
  1. **Daha büyük bir açık model** (~27–32B, Apache-2.0 lisanslı, ör. Qwen ailesi) ve buna yetecek **GPU** (~24 GB) gerekir. Daha da iyisi için 70B (2 GPU). Bu bir **donanım yatırımı** (Q5 ve bütçe sorusu).
  2. Pilotta bu lokal modeli **bulut modelleriyle aynı test setinde** karşılaştırırız. Fark küçükse lokal model gerçek veride kullanılır.
  3. Fark büyükse diğer katmanlar daha sıkı tutulur: daha yüksek eşik (daha sık "bulunamadı"), sıkı sayı kontrolü, kullanıcının kaynağı görüp onaylaması. Doğruluk düşükse sistem **daha çekingen** davranmalı.
  4. Ara çözüm de sorulabilir: **Kurumsal bulut** (kendi Azure/AWS hesabında, veri saklamama sözleşmesiyle). Hukuk bunu "bulut" sayıyor mu? (sorulacaklar.md Q1-a)

**K3.** Kaynakta "11 (± 1) stitches per inch" yazıyor. LLM'in cevabı "inç başına 11 dikiş olmalı [1]". Sayı kontrolü bunu yakalar mı? Yakalaması için kontrol nasıl kurulmalı?
> **C:**


- **Basit (tek yönlü) kontrol yakalamaz.** Basit kontrol şunu sorar: "Cevaptaki sayılar kaynakta var mı?" Cevapta "11" var, kaynakta da "11" var → **geçer.** Ama tolerans (± 1) kaybolmuş. Usta "tam 11 olmalı" diye anlar, 10 veya 12 SPI'lı kabul edilebilir ürünü reddedebilir (ya da tersi bir durumda yanlış ürünü kabul edebilir).
- **Rakam rakam karşılaştırmak daha da kötü:** "± 1"deki "1" de kaynakta var. Kontrol tek tek rakamlara bakarsa hiçbir şey yakalamaz.
- **Doğru kurulum (iki yönlü):**
  1. Sayılar tek tek değil, **bütün ifade** olarak çıkarılır: "11 (± 1)" tek bir birim, "10-14" tek bir birim, "3/16 to 1/4" tek bir birim.
  2. **Yön 1 (cevap → kaynak):** Cevaptaki her ifade alıntıda / chunk'ta var mı? (Uydurma değeri yakalar: "12" kaynakta yok.)
  3. **Yön 2 (kaynak → cevap):** **Alıntıdaki** her sayı-tolerans ifadesi cevapta **tam haliyle** var mı? (Düşen toleransı yakalar: "11 (± 1)" alıntıda var, cevapta sadece "11" var → ⚠.)
  4. Karşılaştırmadan önce normalize edilir: "±1" = "± 1", "10–14" = "10-14", "1.5" = "1,5".
- **Sonuç:** Bu durumda cevap ⚠ rozetle gösterilir ve alıntı vurgulanır, ya da model bir kez daha denenir ("toleransı da yaz"). Prompt kuralı 3 ("toleransı asla düşürme") bu hatayı baştan azaltmak için var. Kod kontrolü de kaçarsa yakalamak için.

**K4.** Test setine neden "cevapsız" ve "tuzak" sorular koyuyoruz? Sadece cevabı olan sorularla ölçseydik ne kaçırırdık?
> **C:** veremediği cevaplarda uydurup uydurmayacağını görmüş olurduk 

🟡 Cevapsız sorular için doğru. Tuzak sorular ve "ne kaçırırdık" kısmı eksik.

- **Cevapsız sorular ✅:** Kaynakta cevap yokken sistem uyduruyor mu, yoksa "bulunamadı" diyor mu? Gerçek kullanımda en tehlikeli an bu.
- **Tuzak sorular (eksik):** Cevabı **benzer ama yanlış** bir dokümanda olan sorular. Örnek: "S-7300A'da ..." sorusunun cevabı sadece S-7300B kılavuzunda var, ya da ceket sorusuna pantolon şartnamesindeki değer geliyor. Sistem "bir cevap buldum" diye **yanlış makineye ait** değeri verebilir. Bu, uydurma değil ama sonucu aynı: yanlış dikim veya yanlış ayar. Metadata filtresinin ve prompt kuralı 5'in işe yarayıp yaramadığını sadece bu sorular gösterir.
- **Sadece cevabı olan sorularla ölçseydik kaçıracaklarımız:**
  1. Sistem her soruya cevap verse bile skor yüksek çıkardı. "Her şeye cevap veren" ama uyduran bir sistem **iyi görünürdü.**
  2. **Eşik ayarı yapılamazdı:** Eşik, cevabı olan ve olmayan soruların skorlarını karşılaştırarak belirleniyor (4.3, Katman 2). Cevapsız soru yoksa karşılaştıracak bir şey yok.
  3. Tersi de ölçülemezdi: Sistem çok çekingense (cevabı olduğu halde "bulunamadı" diyorsa) bunu görmek için de iki tür soruya birlikte bakmak gerekiyor.

**K5.** LLM'den cevabı serbest metin yerine JSON şemasıyla (cevap, alıntılar, kaynaklar, sesli_metin, bulunamadı) almanın faydası ne?
> **C:** eksikliğin nerede olduğuna sistemin hangi kısmının doğru ya da eksik çalıştığını anlayabiliriz 

🟡 Doğru bir fayda (hata ayıklama), ama asıl sebep başka.

- **Asıl sebep: Otomatik doğrulama.** S11 Katman 5'teki kontroller (alıntı chunk'ta var mı, sayılar kaynakta var mı, kaynak numarası geçerli mi) için cevabın parçalarını **ayrı ayrı** almak gerekiyor. Alıntı `alintilar` alanında, cevap `cevap` alanında olunca kod bunları doğrudan karşılaştırır. Serbest metinde "hangi cümle alıntı, hangisi cevap" diye ayıklamak kırılgan, ayıklama hatası da doğrulamayı bozar.
- **Her alan farklı bir yere gidiyor:**
  - `cevap` → ekrandaki cevap metni
  - `alintilar` → doğrulama + sayfada **cümle vurgusu**
  - `sesli_metin` → normalizasyon + TTS
  - `bulunamadi` → "bulunamadı" ekranı
  - `netlestirme_sorusu` → kullanıcıya soru
  - `celiski_var` → uyarı rozeti
-  Denetim izinde her alan ayrı kaydedildiği için "model alıntıyı doğru buldu ama cevaba yanlış aktardı" ya da "model hiç alıntı bulamadı, yani retrieval yanlış chunk getirmiş" ayrımı yapılabilir.
- **Garanti:** Şema zorunlu kılındığında (*structured output*) model şemaya uymayan bir cevap **veremez.** Eksik alan, bozuk JSON gibi hatalar baştan engellenir.

---

## 3. Derlenmiş Notlar

### 4.1 Model seçenekleri
- LLM'in rolü: **bilgi kaynağı değil, okuyucu-yazar** (açık kitap sınavı). Kriter: kaynağa sadakat, bilmediğini söyleme, TR yazma + EN okuma, şemaya uyma. Bağlam penceresi kriter değil.
- **Bulut** (hepsi TR, görsel, yapılandırılmış çıktı destekli): Anthropic (Opus 5.5 / Sonnet 5.5 / Haiku 5.5), OpenAI (gpt-5.6 sol / terra / luna), Google (gemini-3.1-pro-preview, 3.8-flash, 3.1-flash-lite). Azure / AWS / Google Cloud üzerinden kurumsal sözleşmeyle de erişilebilir.
- **Açık:** Qwen (çoğu Apache-2.0), Gemma (lisans doğrulanmalı), Mistral, Llama (topluluk lisansı), Türkçe uyarlanmış modeller. 7–8B modeller bir Türkçe doküman QA çalışmasında %49–75 → **bizim için yetersiz.** Lokal hedef: ~27–32B, 24 GB GPU (ölçülmeli).
- Maliyet ~5–170 $/ay (6.000 soru), **karar verdirici değil.**
- **Seçim yöntemi:** Pilotta 3 bulut orta seviye + 1 küçük + 1 lokal aday, aynı test seti, aynı prompt. Sağlayıcı önceden seçilmiyor.

### 4.2 Prompt tasarımı
- Taslak: [prompt-taslak.md](prompt-taslak.md). İlkeler: sadece kaynak, önce alıntı, sayılar sadece alıntıdan, [n] atıf, açık "bulunamadı" seçeneği, çelişkiyi bildir, belirsizse sor, çeviri anlam kuralları, birim dönüşümü yok, yapılandırılmış çıktı, ayrı sesli metin, doküman içeriği talimat değil veri.

### 4.3 Halüsinasyon azaltma
- 6 katman: filtre + hybrid + rerank → **kalibre edilmiş eşik** → sıkı prompt → **birebir alıntı** (kaynak dilinde) → **otomatik doğrulama** (kaynak no, alıntı, **sayı-tolerans çifti iki yönlü**, bulunamadı tutarlılığı) → kullanıcı doğrulaması (alıntı + vurgulu sayfa + rozet).
- Başarısızlıkta: 1 yeniden deneme, sonra cevabı gösterme / uyarı + kaynak sayfası. Hepsi denetim izine.
- Birim dönüşümü modelde değil kodda, "yaklaşık" etiketiyle.

### 4.4 Değerlendirme
- Test seti: 50–100 soru, 8 tür (değer, prosedür, arıza, **cevapsız**, **tuzak**, çapraz dil, görsel, alan dışı). Gerçek veriye geçişte yeniden kurulacak.
- Metrikler: Recall@5, **değer doğruluğu**, kaynak doğruluğu, faithfulness, **doğru reddetme**, gereksiz reddetme, tuzak başarısı, gecikme, maliyet. "Yanlış değer" ile "cevap yok" ayrı tutulur.
- Araçlar: **custom script** (kural tabanlı metrikler) + RAGAS (faithfulness, Türkçe uyarlamalı). LLM hakem farklı model olmalı ve insan etiketli küçük setle kalibre edilmeli. İnsan değerlendirmesi: "bu cevapla dikim yapar mıydım?"

### Projemiz için ilk öneri

| Konu | Öneri | Alternatif | Gerekçe |
|------|-------|-----------|---------|
| **LLM (test aşaması)** | 3 sağlayıcıdan orta seviye birer model + bir küçük model pilotta karşılaştırılır | Tek sağlayıcıyla başlamak | Tarafsız, bizim verimizde ölçülmüş seçim |
| **LLM (Q1 = bulut yok)** | Apache-2.0 açık model, ~27–32B, 24 GB GPU | 70B (2 GPU) · Türkçe uyarlanmış model | 7–8B yetersiz kanıtı. Q5'e bağlı |
| **Çıktı biçimi** | Yapılandırılmış çıktı (JSON şeması) | Serbest metin + ayrıştırma | Otomatik doğrulama için şart |
| **Halüsinasyon** | 6 katman, kalibre eşik, iki yönlü sayı kontrolü | + İkinci model doğrulayıcı (gerekirse) | R4 |
| **Değerlendirme** | Kendi script + RAGAS (TR uyarlamalı) + insan değerlendirmesi | DeepEval (CI), TruLens (izleme) | Kritik metrikler kural tabanlı |
| **Test seti** | 50–100 soru, 8 tür, cevapsız ve tuzak dahil | — | Pilot başarı kriteri için şart |

**Açık kalanlar:** Q1, Q5, bütçe, test setini kimin hazırlayacağı (0.4), kabul edilebilir yanlış değer oranı ve "genel bilgi kullanılabilir mi" kararı (yeni, [sorulacaklar.md A5](sorulacaklar.md)).

---

## Kaynaklar

**Resmi fiyat / model sayfaları**
- [Anthropic: modeller ve fiyatlar](https://platform.claude.com/docs/en/about-claude/models/overview) · [Anthropic fiyatlandırma](https://www.anthropic.com/pricing)
- [OpenAI API fiyatlandırma](https://developers.openai.com/api/docs/pricing)
- [Google Gemini API fiyatlandırma](https://ai.google.dev/gemini-api/docs/pricing)

**Türkçe ve açık modeller**
- [Evaluating Open-Weight LLMs for Turkish Domain Documents Under Retrieval and Hardware Constraints (arXiv 2609.28007, 2026)](https://arxiv.org/html/2609.28007)
- [CETVEL: Turkish LLM benchmark (EACL 2026)](https://aclanthology.org/2026.eacl-long.46) · [arXiv 2508.16431](https://arxiv.org/pdf/2508.16431)
- [TurkishMMLU (arXiv 2407.12402)](https://arxiv.org/pdf/2407.12402) · [TR-MMLU](https://loan.bilgi.edu.tr/items/cbb9b062-8df6-4073-85e4-81d51227442e/full)

**Değerlendirme**
- [RAGAS: metrikleri hedef dile uyarlama](https://docs.ragas.io/en/stable/howtos/customizations/metrics/metrics_language_adaptation/)
- [MEMERAG: çok dilli RAG değerlendirme meta-benchmark'ı (ACL 2025)](https://aclanthology.org/2025.acl-long.1101)

**İkincil kaynaklar (doğrulanmalı)**
- [Best Open Source LLMs (October 2026, Thunder Compute)](https://www.thundercompute.com/blog/best-open-source-llms) · [BenchLM açık model sıralaması](https://benchlm.ai/best/open-source) · [Open-weight modeller ve lisanslar (layer3labs)](https://www.layer3labs.io/open-weights/best-open-weights-ai-models) · [Qwen vs Llama vs Mistral (promptquorum)](https://www.promptquorum.com/local-llms/qwen-vs-llama-vs-mistral)
- [OpenAI fiyat tablosu özeti (morphllm)](https://www.morphllm.com/openai-api-pricing) · [Gemini fiyatları 2026 (cloudzero)](https://www.cloudzero.com/blog/gemini-pricing/)
- [RAGAS vs TruLens vs DeepEval (Analytics Vidhya, 2026)](https://www.analyticsvidhya.com/blog/2026/07/rag-evaluation-frameworks/) · [LLM evaluation frameworks compared (Atlan)](https://atlan.com/know/llm-evaluation-frameworks-compared/) · [Best RAG evaluation tools 2026 (futureagi)](https://futureagi.com/blog/best-rag-evaluation-tools-2026/)
