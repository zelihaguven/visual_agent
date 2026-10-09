# TTS: Metinden Sese (Adım 5)

> **Başlangıç:** 2026-10-09
> **İlgili plan:** [req.md, Adım 5](../req.md) · Önceki: [rag-temelleri.md](rag-temelleri.md), [pdf-isleme.md](pdf-isleme.md), [kaynak-gosterme.md](kaynak-gosterme.md) · Test seti: [manual-envanteri.md](manual-envanteri.md)
> **Ses örnekleri (5.2 denemesi yapılınca):** `Pre/notes/tts-samples/`


---

## 0. Kavramlar

### 0.1 TTS nedir?

**Ne demek?** *Text-to-Speech* (metinden sese, **ses sentezi**): Yazılı bir metni insan sesine benzeyen bir ses dosyasına çevirmek. Ters yöndeki iş *Speech-to-Text* (STT, **konuşma tanıma**): sesi metne çevirmek (Adım 6.4).

**Benzetme:** Bir spikere metni verip okutmak gibi. İyi bir spiker üç şey yapar:
1. Metni **anlar**: "Dr." yazanı "doktor", "%50" yazanı "yüzde elli" diye okur.
2. Doğru **telaffuz** eder: "overlok" kelimesini Türkçe, "lockstitch" kelimesini İngilizce okur.
3. Doğru **tonlama** yapar: Soru cümlesinde sesini yükseltir, virgülde durur, önemli kelimeyi vurgular.

TTS sistemi de aynı üç işi yapmak zorunda. Bizim projede en çok **1. adımda** (metni anlamak) sorun çıkacak (bkz. 0.3).

**neden lazım?** Usta elleri meşgulken (kumaş tutarken, makinenin başındayken) ekranı okuyamayabilir. Cevabı duyması işini bırakmadan bilgiyi almasını sağlar. Ama aynı zamanda **yeni bir hata kanalı** açar: Ekranda doğru yazan "11 (± 1)" sesli okunurken yanlış okunursa, usta yanlış değeri duyar (req.md **R2**, **R4**).

### 0.2 TTS nasıl çalışır? 

Klasik bir TTS sistemi metni birkaç adımda sese çevirir:

```
"Dikiş 11 (± 1) SPI olmalı."
    │
    ▼  1. Metin normalizasyonu (text normalization)
"Dikiş inç başına on bir, artı eksi bir dikiş olmalı."
    │
    ▼  2. Harften sese çevirme (G2P: grapheme-to-phoneme)
/d i c i ʃ   i n tʃ   b a ʃ ɯ n a .../      ← fonemler (ses birimleri)
    │
    ▼  3. Prozodi (tonlama, vurgu, duraklama, hız)
    │
    ▼  4. Akustik model → spektrogram (sesin "resmi")
    │
    ▼  5. Vocoder → ses dalgası (WAV/MP3)

```

| Terim | Türkçesi | Anlamı |
|-------|----------|--------|
| *Text normalization* | Metin normalizasyonu | Sayı, kısaltma, sembol ve birimleri okunacak kelimelere çevirmek (0.3) |
| *G2P (grapheme-to-phoneme)* | Harften sese çevirme | Yazılışı telaffuza çevirmek. Türkçe büyük ölçüde "yazıldığı gibi okunur", bu adım kolay. İngilizce terimlerde zor ("gauge" → "geyç") |
| *Phoneme* | Fonem, ses birimi | Bir dildeki en küçük ses birimi |
| *Prosody* | Prozodi, tonlama | Sesin yükselip alçalması, vurgu, duraklama, hız |
| *Vocoder* | Ses üretici | Spektrogramı duyulabilir ses dalgasına çeviren son adım |
| *Voice* | Ses (karakter) | Belirli bir konuşmacının sesi: "Emel (kadın, TR)", "Ahmet (erkek, TR)" |

**Yeni nesil modeller** (2024 sonrası, ElevenLabs, Chatterbox, XTTS vb.) bu adımların çoğunu **tek bir büyük sinir ağında** yapıyor. Bir dil modeli gibi metni okuyup doğrudan "ses parçacıkları" (*audio token*) üretiyorlar. Sonuç çok daha doğal, ama iki yan etkisi var:
- Adımlar birbirinden ayrılmadığı için **"bu sayıyı şöyle oku" diye müdahale etmek zorlaşıyor.** Klasik sistemlerde bunu SSML ile yaparsın (0.5).
- Model bazen bir kelimeyi atlayabiliyor, tekrar edebiliyor veya uydurabiliyor (**TTS halüsinasyonu**). Klasik sistemlerde bu neredeyse hiç olmaz. Bizim için önemli: Sesli okunan değer ekrandakiyle aynı olmak zorunda.

### 0.3 Metin normalizasyonu nedir?
**Ne demek?** Metindeki "okunuşu belirsiz" her şeyi, **sesli okunacağı haliyle kelimelere** çevirmek.

**Benzetme:** Bir yemek tarifini telefonda birine okurken "1/2 su bardağı" yazanı "bir bölü iki su bardağı" değil "yarım su bardağı" dersin. "180°C" yazanı "yüz seksen derece" dersin. Bunu düşünmeden yaparsın, çünkü **ne anlama geldiğini bilirsin.** TTS sistemi bilmez, tahmin eder.

***** Çünkü manuellerimiz tam olarak okunuşu belirsiz şeylerle dolu. Test setimizden gerçek örnekler:

| Metin | Doğru okunuş (TR) | Olası yanlış okunuş | Yanlış okunursa |
|-------|-------------------|---------------------|-----------------|
| `11 (± 1) stitches per inch` | "inç başına on bir, artı eksi bir dikiş" | "on bir parantez artı eksi bir" veya "±" hiç okunmaz → "on bir bir" | Usta tolerans olduğunu anlamaz veya "111" duyar |
| `10-14 SPI` | "inç başına on ile on dört dikiş" | "on eksi on dört S P I" | **Negatif sayı** gibi duyulur |
| `3/16 to 1/4-inch gauge` | "on altıda üç ile dörtte bir inç" | "üç bölü on altı...", "üç on altıncı", "Mart on altı" (tarih sanılır!) | Ölçü yanlış anlaşılır |
| `½ inch` | "yarım inç" | Hiç okunmaz veya "bir iki inç" | Değer kaybolur |
| `stitch type 301 or 401` | "üç yüz bir ya da dört yüz bir tipi dikiş" | "üç sıfır bir" de olabilir (atölyede hangisi kullanılıyor? bkz. 5.5) | Kabul edilebilir, ama tutarlı olmalı |
| `LSc-2` | "L S c iki" | "Lsc eksi iki" | Dikiş sınıfı kodu anlaşılmaz |
| `E-07` (hata kodu) | "E sıfır yedi" | "E eksi yedi", "E yedi" | Yanlış hata kodu aranır |
| `S-7300A` (model) | "S yetmiş üç yüz A" veya "S yedi bin üç yüz A" | "S eksi yedi bin üç yüz A" | Kafa karışıklığı |
| `146391-001` (parça no) | Rakam rakam, gruplu | "yüz kırk altı bin üç yüz doksan bir eksi bir" | **Yanlış parça sipariş edilir** |

> **Bu tablo req.md R4 (halüsinasyon / yanlış değer) riskinin sesli versiyonu.** Rag-temelleri.md S11'de LLM'in yanlış değer yazmasına karşı katmanlar kurduk. Ama doğru yazılmış bir değer **yanlış okunursa** o katmanların hiçbiri işe yaramaz. Normalizasyon, S11'in TTS tarafındaki devamı.

**Türkçeye özel zorluklar:**
- **Ekler:** "11'e", "E-07'de", "301'i" gibi sayı + ek birleşimlerinde ek, sayının **okunuşuna** göre seçilir ("on bire", "üç yüz biri"). TTS ekin nasıl okunacağını sayının okunuşundan bilmek zorunda.
- **Tire (-) belirsizliği:** Aralık mı ("10-14"), kod mu ("E-07"), parça no ayırıcısı mı ("146391-001"), eksi mi? Sadece bağlam söyler.
- **Diller arası karışım:** "SPI" İngilizce kısaltma ama Türkçe cümlede geçiyor (0.6).
- **Ondalık ayırıcı:** Türkçede virgül ("1,5 mm"), İngilizcede nokta ("1.5 mm"). İngilizce manuelden gelen "1.5" Türkçe sesle "bir nokta beş" veya "bin beş yüz" okunabilir.

**Üç yol (ayrıntısı 2.5'te):**
1. **TTS'in kendi normalizasyonuna güvenmek:** Kolay ama kontrolsüz. Bazı servisler bunu hız için kapatıyor (ör. ElevenLabs Flash v2.5'te varsayılan olarak kapalı).
2. **Kendi kurallarımızla normalizasyon** (kod: regex + sayı → kelime + birim/kısaltma sözlüğü): Kontrollü, tekrarlanabilir, test edilebilir.
3. **LLM'e ayrıca "sesli okunacak metin" yazdırmak:** Esnek, bağlamı anlar, ama LLM sayıyı **değiştirebilir** (yeni bir halüsinasyon noktası).

### 0.4 Gecikme ve streaming ne demek?

**Gecikme (*latency*):** Kullanıcının soruyu sorduğu andan **ilk sesi duyduğu** ana kadar geçen süre. TTS'e özel ölçü: **TTFA** (*time to first audio*, ilk sesin gelme süresi). Diğer ölçü: **RTF** (*real-time factor*, gerçek zaman katsayısı): 10 saniyelik sesi üretmek 2 saniye sürüyorsa RTF = 0,2. RTF < 1 ise sistem konuşulandan hızlı üretiyor demek, lokal modellerde önemli.

**Streaming (akış halinde üretim):** Sesin tamamını üretip sonra çalmak yerine, **ilk parçası hazır olur olmaz** çalmaya başlamak.

**sistemde gecikme nereden birikiyor?**
```
Soru → retrieval + rerank (~0,5–2 sn) → LLM cevabı (~2–10 sn) → [doğrulama] → TTS (~0,1–2 sn) → 🔊
```
Streaming olmadan usta tüm cevap yazılıp seslendirilene kadar sessizlik duyar. İki seviyede streaming var:
- **TTS streaming:** TTS sesi parça parça gönderir. Uzun bir paragraf için ilk ses 0,1–0,5 sn'de gelir.
- **LLM → TTS cümle cümle (*sentence chunking*):** LLM ilk cümleyi bitirir bitirmez TTS'e gönderilir, LLM ikinci cümleyi yazarken ilk cümle okunmaya başlar.

>  **çatışma var:** Rag-temelleri.md S11, Katman 5 "cevap kullanıcıya **gitmeden önce** alıntı ve sayı kontrolü" diyor. Cümle cümle seslendirmede ise cevap **daha bitmeden** okunmaya başlıyor. Yani doğrulanmamış bir değer usta tarafından duyulmuş olabilir. Bu çatışmanın çözümü 2.3'te.

### 0.5 SSML ve telaffuz sözlüğü (TTS'e "nasıl okuyacağını" söylemek)

**Ne demek?** *SSML (Speech Synthesis Markup Language)*: Metnin içine TTS'e talimat veren etiketler koymak. HTML'in sese uygulanmış hali gibi. Bulut servislerinin (Azure, Google, Polly) çoğu destekler.

```xml
<speak>
  Dikiş sıklığı <say-as interpret-as="cardinal">11</say-as> olmalı.
  <break time="300ms"/>
  Hata kodu <say-as interpret-as="characters">E07</say-as>.
  <sub alias="inç başına dikiş">SPI</sub>
</speak>
```

| Etiket | Ne yapar |
|--------|----------|
| `say-as` | "Bunu sayı / harf harf / tarih olarak oku" |
| `sub` | "Bu kısaltmayı şu kelimeyle oku" (SPI → "inç başına dikiş") |
| `phoneme` | Telaffuzu fonem olarak vermek (IPA alfabesiyle) |
| `break` | Duraklama |
| `prosody` | Hız, ses yüksekliği, ton |
| *Lexicon* (telaffuz sözlüğü) | Bir kelimenin nasıl okunacağını **bir kez** tanımlayıp her yerde kullanmak (ör. "overlok", "lockstitch", "Juki") |

**Neden önemli?** Normalizasyonu kendi kodumuzla yapsak bile bazı şeyleri (yabancı terim telaffuzu, duraklama) SSML ile vermek daha kolay. **Dikkat:** Her servis her etiketi her dilde desteklemiyor (ör. `say-as` türlerinin Türkçede çalışıp çalışmadığı servise göre değişiyor, **denenmeli**). Yeni nesil modellerin (ElevenLabs, Chatterbox, OpenAI) SSML desteği genelde **yok veya sınırlı**: Onlara "nasıl okuyacağını" metnin kendisini değiştirerek söylersin.

### 0.6 Çok dillilik ve dil karışımı (code-switching)

**Ne demek?** Aynı cümlede iki dilin karışması: *"Overlok makinesinde lockstitch 301 yerine 504 kullanın, SPI 10-14 olsun."* Buna *code-switching* (dil geçişi) denir.

**Neden sorun?** TTS bir "dil" seçilerek çalışır. Türkçe ses seçilirse "lockstitch" Türkçe okunur ("lokstiç" değil "loc-k-stitç" gibi bozuk çıkabilir). İngilizce ses seçilirse Türkçe kelimeler bozulur.

**Bizim durumumuz:** Manueller İngilizce, cevap Türkçe olabilir (req.md Q2). Cevapta İngilizce teknik terimler **kaçınılmaz** (usta da "overlok", "lockstitch" diyor). Seçenekler:
- **Çok dilli sesler** (*multilingual voice*): Aynı ses iki dili de okuyabilir. Azure'un "Multilingual" sesleri, ElevenLabs, OpenAI, Chatterbox böyle. Cümle içi geçişte ne kadar başarılı oldukları **denenmeli**.
- **Dil etiketi (SSML `<lang xml:lang="en-US">`):** Yabancı terimi işaretleyip o kısmı İngilizce okutmak.
- **Telaffuz sözlüğü:** Sık geçen terimlerin (overlok, lockstitch, bobbin) okunuşunu bir kez tanımlamak.
- **Terimi Türkçeleştirmek:** "stitches per inch" yerine "inç başına dikiş".

### 0.7 Ses klonlama ve lisans meselesi neden önemli?

**Ses klonlama (*voice cloning*):** Birkaç saniyelik ses kaydından o kişinin sesini taklit eden bir ses üretmek. *Zero-shot cloning*: Modeli yeniden eğitmeden, sadece 5–10 saniyelik örnekler kullan. 

**Bizim için gerekli mi?** **Muhtemelen hayır.** Hazır, net, anlaşılır bir ses yeterli. Kurumsal bir ses ("şirketimizin sesi") istenirse ileride düşünülür. Ama konuyu bilmek gerekiyor, çünkü:
1. **Lisanslar bu yüzden karışık:** Klonlama kötüye kullanıma (*deepfake*, dolandırıcılık) açık olduğu için birçok açık model ağırlıkları **ticari olmayan** lisansla yayınlanıyor.
2. **Ses sahibinin rızası:** Bir çalışanın sesi klonlanacaksa yazılı izin gerekir (KVKK açısından ses biyometrik veri sayılabilir, **hukuk onayı gerekir**).
3. **Yapay ses bildirimi:** Bazı sağlayıcılar (ör. OpenAI) kullanıcıya "duyduğun ses yapay zekâ ile üretildi" bilgisinin verilmesini kullanım koşulu olarak istiyor.

**üç ayrı lisans** var ve hepsine bakmak gerekiyor:

| Katman | Örnek | Neden önemli |
|--------|-------|--------------|
| **Kod lisansı** | Coqui TTS kütüphanesi: MPL-2.0 · Piper motoru: GPL-3.0 | Programı çalıştırma ve dağıtma koşulu |
| **Model ağırlıkları lisansı** | XTTS-v2: CPML (ticari değil) · F5-TTS: CC-BY-NC | **Asıl kısıt genelde burada.** Kod MIT olsa bile ağırlık NC (non-commercial) ise ticari kullanamazsın |
| **Eğitim verisi / ses lisansı** | Piper `tr_TR-dfki`: veri CC BY-NC-SA | Model ağırlığı veriden "türer". Veri ticari değilse model de ticari olmayabilir. **Bu kısıt fine-tune'lara da geçer** (ör. F5-TTS'in tüm Türkçe fine-tune'ları da NC) |


**"Ticari kullanım"   ne demek?** Sistem bir şirketin üretim sürecinde, iş amacıyla kullanılacak. Satılmasa bile, çoğu NC lisansın tanımında bu **ticari kullanım** sayılır (CPML örneğin "doğrudan veya dolaylı gelir" diyor). Yani NC lisanslı modeller **test için kullanılabilir, üretimde kullanılamaz.**

### 0.8 Kavramlar birbirine nasıl bağlanıyor?

```
LLM cevabı (ekran metni, kaynaklı, doğrulanmış)
   │
   ▼  Sesli okuma metni üret (kısa özet? → 2.5)
   ▼  Metin normalizasyonu (sayı, tolerans, kod, birim → kelime) (0.3)
   ▼  SSML / telaffuz sözlüğü (yabancı terimler, duraklama) (0.5, 0.6)
   ▼  TTS modeli (bulut veya lokal, lisansı uygun) (0.7)
   ▼  Streaming ile çalma (0.4)
🔊  + ekranda okunan cümle vurgulu (Adım 6)
```

---

## 1. Projede TTS'in yeri

Kaynak-gosterme.md'deki ekran taslağına göre TTS **üçüncü bir bilgi kanalı:**

| Kanal | Ne verir | Güvenilirliği |
|-------|----------|---------------|
| Ekrandaki cevap metni | Kaynaklı, doğrulanmış cevap | Yüksek (S11 katmanları) |
| Vurgulu manuel sayfası | **Orijinal kaynak** | En yüksek (gerçek doküman) |
| **Sesli okuma** | Cevabın sesi | Normalizasyon ve TTS kalitesine bağlı. **En zayıf halka** |

**Sonuç:** Ses **kolaylık** kanalı, **doğruluk** kanalı değil. Tasarım ilkesi:
- Ses, ekrandaki doğrulanmış metinden **türetilir**, ayrı bir bilgi kaynağı olmaz.
- Kritik değerler (sayı, tolerans, kod) seste de geçer, ama kişi **son kontrolü ekranda/sayfada** yapar.
- Okunması riskli olanı (uzun parça numaraları) okumak yerine **ekrana yönlendirmek** daha güvenli: "Parça numarası ekranda."

---

## 2. Anlatım

### 2.1 Seçenekler (5.1)

#### Bulut servisleri

| Servis | Türkçe ses | Fiyat (1M karakter, liste fiyatı) | Streaming | Normalizasyon / SSML | Not |
|--------|-----------|-----------------------------------|-----------|----------------------|-----|
| **Azure AI Speech** | ✅ `tr-TR-EmelNeural` (K), `tr-TR-AhmetNeural` (E) (standart neural) · ✅ `tr-TR-Elif` (K), `tr-TR-Aydın` (E): yeni **MAI-Voice-2** HD ve HD Flash sesler · Multilingual sesler Türkçeyi de destekliyor | Standart neural ~15–16 $ (doğrulanmalı) · HD daha pahalı · **Ücretsiz: ayda 0,5M karakter** (resmi sayfa) · Taahhüt paketlerinde indirim | ✅ | ✅ **En güçlü SSML** (say-as, phoneme, lexicon, lang). **Kelime sınırı olayları** (*word boundary*): hangi kelimenin okunduğu anlık bilinir → ekranda senkron vurgu | **Lokal çalıştırma seçeneği var:** Neural TTS **container** (bağlantılı) ve **bağlantısız container** (Microsoft onayı gerekir). Türkçe sesin container'da olup olmadığı **doğrulanmalı** |
| **Google Cloud TTS** | ✅ `tr-TR` **Chirp 3 HD** sesleri + eski nesil (Standard / WaveNet / Neural2) | Chirp 3 HD: **30 $** (ilk 1M ücretsiz) · eski nesiller daha ucuz (doğrulanmalı) | ✅ | SSML eski nesil seslerde güçlü. Chirp 3 HD'de SSML desteği **sınırlı** (doğrulanmalı) | Faturalamaya boşluk ve SSML etiketleri de dahil |
| **ElevenLabs** | ✅ Flash v2.5, Multilingual v2, v3, v4, v4 Turbo (hepsi Türkçe destekli) | Flash/Turbo: **50 $** · Multilingual v2 / v3: **100 $** (kullandıkça öde, doğrulanmalı) | ✅ (REST + WebSocket) | ⚠️ **Flash v2.5'te sayı normalizasyonu varsayılan olarak KAPALI** (gecikme için). Belge "normalizasyonu LLM'de yapın" diyor. SSML yok | En doğal ses kalitesi iddiası. Flash v2.5 ~75 ms (üretici rakamı, bağımsız ölçümde ~200 ms) |
| **OpenAI** | ✅ (ama "sesler İngilizce için optimize" diyor) | `tts-1`: **15 $** · `tts-1-hd`: **30 $** · `gpt-4o-mini-tts`: token bazlı (metin 0,60 $/1M token, ses 12 $/1M token) | ✅ (chunked) | SSML yok. `gpt-4o-mini-tts`'e **talimat** verilebilir ("sayıları yavaş ve net oku") | Kullanıcıya **"bu ses yapay zekâ"** bildirimi kullanım koşulu |
| **Amazon Polly** | ✅ **Burcu** (neural, 2024) · Filiz (standart, eski) | Neural ~16 $, standart ~4 $ (hafızadan ve bayi fiyatından, **doğrulanmalı**) | ✅ | ✅ Güçlü SSML + lexicon. Türkçe fonem tablosu yayınlanmış | Ses seçeneği az (tek neural Türkçe ses) |

**Gizlilik notu (Q1):** Bulut TTS'e giden şey **cevap metni**. İçinde manuelden alıntı ve değerler var ("11 (± 1)", parça numaraları). Pdf-isleme.md'deki "veri kurum dışına çıkabilecek noktalar" tablosunda bu satır zaten var. Bulut LLM kullanılıyorsa aynı metin zaten LLM sağlayıcısına gidiyor, TTS ek bir sağlayıcı (ek bir sözleşme) demek. **Aynı sağlayıcıda kalmak** (ör. LLM de TTS de Azure'da) sözleşme sayısını azaltır.

#### Açık kaynak / lokal modeller

| Model | Türkçe | Lisans (kod / **ağırlık**) | Ticari kullanım | Donanım | Not |
|-------|--------|----------------------------|-----------------|---------|-----|
| **Chatterbox Multilingual** (Resemble AI, 2025) | ✅ (23 dilden biri) | MIT / **MIT** | ✅ | GPU önerilir (500M parametre). CPU'da yavaş olabilir (doğrulanmalı) | **Lokal + ticari + Türkçe üçünü birden sağlayan en güçlü aday.** Ses klonlama var. Her çıktıya görünmez **filigran** (PerTh watermark) ekliyor. Türkçe kalitesi **bilinmiyor, denenmeli** |
| **Piper** | ⚠️ Sadece `tr_TR-dfki` sesi kaldı (fahrettin ve fettah sesleri sahiplerinin isteğiyle **kaldırıldı**) | Motor GPL-3.0 (eski MIT repo Ekim 2025'te arşivlendi) / dfki sesi: **CC BY-NC-SA** | ❌ (Türkçe ses için) | **CPU'da çok hızlı**, Raspberry Pi'de bile çalışır | Hız ve hafiflikte rakipsiz. Ticari Türkçe için **kendi sesimizi eğitmemiz** gerekir (lisanslı kayıt + eğitim eforu). Ses kalitesi yeni modellere göre daha "robotik" |
| **Coqui XTTS-v2** | ✅ | MPL-2.0 / **CPML (ticari değil)** | ❌ | GPU önerilir | Coqui şirketi 2023 sonu / 2024 başı kapandı, **ticari lisans satın alınabilecek kimse yok.** Sadece test için |
| **Kokoro-82M** | ❌ (8 dil, Türkçe yok) | Apache-2.0 | ✅ | CPU yeterli | Çok hızlı ve iyi, ama Türkçe yok. Sadece İngilizce okuma için düşünülebilir |
| **F5-TTS** | Resmi yok (topluluk fine-tune'ları var) | MIT / **CC-BY-NC** | ❌ | GPU | NC kısıtı tüm fine-tune'lara geçiyor |
| **Meta MMS-TTS** | ✅ | **CC-BY-NC** | ❌ | CPU/GPU, küçük | Test için |
| Qwen3-TTS, CosyVoice 3, Fish/OpenAudio S1, Voxtral | ❌ Türkçe listede yok | Apache-2.0 / NC karışık | — | GPU | Takip edilecek: Dil listeleri genişliyor |
| FreyaTTS (2026, akademik) | ✅ Türkçe öncelikli | Bilinmiyor | ? | ? | Yeni bir makale. Ağırlıkları ve lisansı **takip edilecek** |

**Önemli tespit:** 2026 itibarıyla **"Türkçe + ticari kullanılabilir lisans + yüksek kalite"** üçünü birden sağlayan açık model sayısı **çok az** (şu an görünen: Chatterbox Multilingual). Açık kaynak TTS sıralamalarının (Artificial Analysis Speech Arena vb.) üst sıralarındaki modellerin çoğu ya NC lisanslı ya da Türkçe desteklemiyor. Lokal TTS kararı büyük ölçüde **Chatterbox'ın Türkçe kalitesine** bağlı olabilir. Bu yeni bir risk (req.md **R6**).

**Lokal donanım (req.md 0.5 / Q5):**
| Model sınıfı | CPU (GPU yok) | GPU |
|--------------|---------------|-----|
| Piper, Kokoro (küçük, <100M) | ✅ Gerçek zamandan hızlı | Gereksiz |
| Chatterbox, XTTS, F5 (büyük, ~500M) | 🟡 Çalışır ama yavaş, uzun cevapta bekletir (doğrulanmalı) | ✅ Önerilir (~4–8 GB VRAM yeterli olabilir, doğrulanmalı) |

### 2.2 Türkçe / İngilizce kalite karşılaştırması (5.2)

Kaliteyi kaynaklardan okuyarak bilemeyiz. **Kulakla dinleyerek** ve mümkünse **ölçerek** karşılaştırmamız gerekiyor.

> **Kapsam kararı (2026-10-09):** Araştırma task'ı ([tasks.md](tasks.md)) deneme değil **araştırma notu** istiyor. Faz 1'deki deneme ise req.md'de açıkça tanımlı bir kontrol noktasıydı. Bu yüzden aşağıdaki **sistematik karşılaştırma** (kodla ses üretme, round-trip STT, puanlama) **pilota (req.md 6.1) devredildi.** Araştırma aşamasında yapılan: test planı ve cümleler. İsteğe bağlı: Kod yazmadan, servislerin **ücretsiz web demolarında** T2 ve T4 cümlelerini bir kez dinleyip izlenim notu almak (bkz. aşağıda "Hızlı dinleme").

**Test cümleleri** (öneri, onayınla değiştirilebilir):

| # | Dil | Cümle | Neyi test eder |
|---|-----|-------|----------------|
| T1 | TR, genel | "Dikiş atlıyorsa önce iğnenin doğru takıldığını ve ipliğin doğru yoldan geçtiğini kontrol edin." | Doğallık, akıcılık |
| T2 | TR + EN karışık, sayı | "Dış görünür dikişlerde inç başına 11 (± 1) dikiş olmalı. Stitch type 301 ya da 401 kullanılır, overlok kenarlarda SPI 10-14 arası." | **Normalizasyon + dil geçişi.** En kritik cümle |
| T3 | EN, teknik | "Overedge or pre-hemming shall be 10 (± 2) stitches per inch, with a 3/16 to 1/4-inch gauge." | İngilizce teknik okuma, kesir |
| T4 | Kod listesi | "E-07 hatası, S-7300A modeli, LSc-2 dikiş sınıfı, ½ inç, parça no. 146391-001." | Kod ve sembol okuma |

**Her cümle iki şekilde seslendirilir:**
- **Ham hali** (yukarıdaki gibi): TTS'in **kendi** normalizasyonu ne yapıyor?
- **Normalize edilmiş hali** ("inç başına on bir, artı eksi bir dikiş..."): Normalizasyonu biz yapınca sadece ses kalitesi karşılaştırılır.

**Değerlendirme:**
| Ölçüt | Nasıl |
|-------|-------|
| **Kritik değer doğruluğu** (en önemli) | T2 ve T4'teki her sayı/kod doğru okundu mu? Evet/hayır. **Tek bir yanlış değer, o aday için ham metinle kullanılamaz demek** |
| **Otomatik kontrol** (*round-trip*) | Üretilen ses Whisper (STT) ile tekrar yazıya çevrilir, sayılar orijinalle karşılaştırılır. Elle dinlemeyi tamamlar, ileride regresyon testi olarak da kullanılabilir |
| Anlaşılırlık / doğallık | 1–5 puan. Mümkünse **gerçek kullanıcılarla** (usta, kalite ekibi). Kurumsal adı: MOS (*Mean Opinion Score*) |
| Atölye koşulu | Aynı sesler arka planda makine gürültüsüyle ve gerçek hoparlörden dinlenir. Stüdyoda iyi olan ses gürültüde kaybolabilir |
| Hız | TTFA ve toplam süre (2.3) |

**Aday listesi (deneme için):** Azure (Emel/Ahmet + Elif/Aydın HD + bir Multilingual ses), Google Chirp 3 HD, ElevenLabs Flash v2.5 ve Multilingual v2, OpenAI gpt-4o-mini-tts, Amazon Polly Burcu, **Chatterbox Multilingual** (lokal). Test için NC lisanslı XTTS-v2 ve Piper dfki de "kalite referansı" olarak eklenebilir (üretimde kullanılamaz).

**Hızlı dinleme (isteğe bağlı, kod yok, ücretsiz):**
| Aday | Nerede | Hesap |
|------|--------|-------|
| Azure (Emel, Ahmet, Elif/Aydın HD, Multilingual) | [Voice Gallery / Speech Studio](https://speech.microsoft.com/portal/voicegallery) | Microsoft/Azure hesabı (ücretsiz katman yeterli) |
| ElevenLabs (Flash v2.5, Multilingual v2, v3) | elevenlabs.io web arayüzü | Ücretsiz hesap (aylık sınırlı karakter) |
| Chatterbox Multilingual | Resemble AI'ın Hugging Face Space demosu | Hesap gerekmez (genelde) |
| Google Chirp 3 HD | Google Cloud TTS ürün sayfasındaki demo kutusu | Hesap gerekmez (genelde) |

Sadece T2 ve T4 (sayı/kod içeren cümleler) ham haliyle yapıştırılır, **kritik değerler doğru okunuyor mu** diye not alınır. Bu bir ölçüm değil, izlenim. Amaç pilota hangi adaylarla girileceğini daraltmak.

> Test seti public dokümanlardan, bu yüzden test aşamasında bulut servislere metin göndermek sorun değil. Ama **karar test metinlerine göre değil, gerçek cevaplarda geçecek ifade türlerine göre** verilmeli. Gerçek müşteri şartnamelerinde hangi kod/birim/tolerans biçimleri var? Bu liste gerçek dokümanlardan çıkarılmalı.

### 2.3 Gecikme ve streaming (5.3)

**Rakamlar (üretici beyanı, ağ gecikmesi hariç):** ElevenLabs Flash v2.5 ~75 ms, v4 Turbo ~100 ms, v3 Conversational ~280 ms. Bağımsız bir ölçümde Flash v2.5 için medyan ~200 ms (ağ dahil). Azure, Google, OpenAI, Polly'nin hepsi streaming destekliyor. Kısacası **bulut TTS'in kendisi darboğaz değil.** Darboğaz LLM ve bizim doğrulama adımımız.

**Toplam gecikmenin parçaları:**
```
Retrieval + rerank     ~0,5–2 sn
LLM ilk token          ~0,5–2 sn
LLM tam cevap          ~2–10 sn   (cevap uzunluğuna bağlı)
Doğrulama (S11, K5)    ~0,1 sn    (metin karşılaştırma, hızlı)
TTS ilk ses            ~0,1–0,5 sn (bulut) / lokal modele bağlı
```

**Streaming ile doğrulama arasındaki çatışma (0.4) için seçenekler:**

| Seçenek | Nasıl | İlk ses | Güvenlik |
|---------|-------|---------|----------|
| **A. Önce tam cevap + doğrulama, sonra TTS (streaming TTS)** | LLM cevabı bitirir → alıntı/sayı kontrolü → **doğrulanmış metin** cümle cümle TTS'e gider | LLM süresi + ~0,5 sn | ✅ Duyulan her şey doğrulanmış |
| **B. Cümle cümle doğrulama + seslendirme** | LLM bir cümleyi bitirince o cümlenin sayıları kaynak chunk'larda var mı kontrol edilir, geçerse okunur | Çok hızlı | 🟡 Cümle düzeyinde kontrol mümkün, ama cevabın tamamına bakan kontroller (çelişki, eksik bilgi) sonradan gelir. Okunmuş bir cümle geri alınamaz |
| **C. Doğrulamasız cümle cümle** | Klasik sesli asistan yaklaşımı | En hızlı | ❌ R4 ile uyumsuz |

**Öneri: A ile başlamak.** Gerekçe:
- Usta bir sohbet asistanıyla konuşmuyor, **bilgi soruyor.** 2–4 saniye beklemek kabul edilebilir, yanlış değer duymak edilemez.
- Ekranda bu sürede "Kaynaklar aranıyor... Cevap hazırlanıyor..." gibi bir durum gösterilebilir. Ekran metni de LLM'den akarken gösterilebilir, ama **"doğrulanıyor"** etiketiyle (Adım 6 konusu).
- Sabit mesajlar ("Bu bilgi manuellerde bulunamadı...") **önceden seslendirilip** dosya olarak saklanır, gecikme sıfır.
- Gecikme pilotta sorun olursa B'ye geçilir.

**Atölye ortamı ve arayüz (Adım 6'ya not):**
- **Oynatma kontrolleri:** Durdur, tekrar dinle, yavaş oku (hız ayarı), sesi aç/kapat.
- **Senkron vurgu:** Okunan cümle ekrandaki cevapta vurgulanır. Azure ve bazı servisler okunan kelimenin zamanını (*word boundary*) veriyor. Ses ve ekran birbirini doğrular.
- **Kulaklık mı hoparlör mü:** Gürültülü atölyede hoparlör yetersiz kalabilir, ama kulaklık iş güvenliği ve konfor açısından sorun olabilir. Kullanıcılara sorulmalı.
- **Otomatik okuma mı, butonla mı:** Her cevabın otomatik okunması birden fazla kullanıcılı alanda rahatsız edici olabilir. Varsayılan: buton ile, ayarla otomatik.

### 2.4 Maliyet ve lisans (5.4)

**Kabaca bir hesap** (varsayım: günde 200 soru, sesli okunan metin cevap başına ~400 karakter):
```
200 × 400 = 80.000 karakter/gün ≈ 2,4M karakter/ay (30 gün)
```
| Servis | ~Aylık maliyet (liste fiyatı, ücretsiz kota düşülmeden) |
|--------|-----------------------------------|
| Azure standart neural (~15 $/1M) | ~36 $ |
| OpenAI tts-1 (15 $/1M) | ~36 $ |
| Google Chirp 3 HD (30 $/1M) | ~72 $ |
| ElevenLabs Flash (50 $/1M) | ~120 $ |
| ElevenLabs Multilingual v2 (100 $/1M) | ~240 $ |
| Lokal (Chatterbox / Piper) | Karakter ücreti yok. Donanım (GPU) ve bakım maliyeti |

**Sonuç:** Bu ölçekte TTS maliyeti **karar verdirici değil.** Kararı **gizlilik (Q1), Türkçe kalite ve normalizasyon kontrolü** verecek. Sesli metni kısa tutmak (2.5) maliyeti de düşürür.

**Lisans özeti:**
| Durum | Modeller |
|-------|----------|
| ✅ Ticari kullanılabilir, Türkçe var | Tüm bulut servisler (kendi kullanım koşullarıyla) · **Chatterbox Multilingual** (MIT) |
| ⚠️ Ticari kullanılabilir, Türkçe **yok** | Kokoro, Qwen3-TTS, CosyVoice (dil eklenirse tekrar bakılır) |
| ❌ Sadece test / araştırma | XTTS-v2 (CPML), F5-TTS (CC-BY-NC), MMS-TTS (CC-BY-NC), Piper `tr_TR-dfki` (CC BY-NC-SA), OpenAudio S1 (CC-BY-NC-SA) |
| ⚠️ Kod lisansı dikkat | Piper motoru **GPL-3.0** (ürüne gömülüp dağıtılırsa kaynak kodu açma yükümlülüğü doğabilir. Sadece kendi sunucumuzda çalıştırmak genelde sorun değil, **hukuk onayı**) |

**Bulut servislerde de lisans/kullanım koşulu var:** Ses çıktısının kullanım hakları, verinin eğitimde kullanılıp kullanılmadığı, veri saklama süresi, "yapay ses" bildirimi (OpenAI). Kurumsal sözleşmede kontrol edilecek (Adım 7.2).

### 2.5 Metin normalizasyonu ve sesli okuma metni (5.5)

#### Soru 1: Ekrandaki cevabın aynısı mı okunmalı, ayrı kısa bir metin mi?

Ekrandaki cevap **okumak için** yazılmış: Madde işaretleri, [1] kaynak numaraları, tablolar, parantezler, uzun alıntılar. Sesli okununca bunlar kötü duyulur:
- "Köşeli parantez bir köşeli parantez kapa" ya da sessizce atlanan kaynak numaraları
- 6 maddelik bir listeyi dinlemek zor, usta 3. maddede ilk maddeyi unutur
- İngilizce alıntı cümlesinin (S11 Katman 4) tamamını dinlemek gereksiz

**Öneri: Ayrı bir "sesli okuma metni" (*spoken text*).** Özellikleri:
- **Kısa:** 1–3 cümle, ~15–30 saniye. Cevabın özü + kritik değer(ler).
- **Kaynak numarası yok.** Gerekirse sonda tek cümle: "Kaynak ekranda gösteriliyor."
- **Liste yerine sıralı cümle:** "Üç adım var. Birincisi... İkincisi..." Uzun listelerde: "İlk üç adım şunlar... Diğerleri ekranda."
- **Riskli değerleri ekrana yönlendirme:** Uzun parça numaraları, tablolar → "Parça numarası ekranda."

#### Soru 2: Sesli metni kim üretecek?

| Yol | Artı | Eksi |
|-----|------|------|
| **a. LLM, cevapla birlikte ayrıca kısa bir sesli metin yazar** | Bağlamı anlar, doğal cümle kurar, listeyi özetler | LLM **değeri değiştirebilir** (11 → 12). Yeni bir halüsinasyon noktası |
| **b. Kod, ekran metninden kurallarla türetir** | Değer değişmez, tekrarlanabilir | Özetleme yapamaz, doğal olmayan cümleler |
| **c. a + b + kontrol (önerilen)** | LLM kısa sesli metni yazar (sayılar **rakamla**) → **sayı kontrolü:** sesli metindeki her sayı/kod ekran metninde ve kaynak chunk'ta var mı? → **kod** sayıları ve kodları kurallarla kelimeye çevirir | Biraz daha karmaşık |

**c'nin mantığı:** LLM'e **"ne söyleneceğini"** (hangi bilgi, ne kadar kısa) seçtiriyoruz. **"Sayının nasıl okunacağını"** kuralla belirliyoruz. LLM'e sayıyı kelimeyle yazdırmıyoruz ("on bir artı eksi bir"), çünkü yazıyla yazılmış sayıyı otomatik kontrol etmek zor. Rakamla yazdırıp kontrol ediyoruz, sonra kelimeye **kod** çeviriyor.

```
Ekran cevabı (doğrulanmış)  ──►  LLM: kısa sesli metin (rakamlarla)
                                     │
                                     ▼  Sayı/kod kontrolü (S11 Katman 5'in aynısı)
                                     ▼  Kural tabanlı normalizasyon (kod)
                                     ▼  SSML / telaffuz sözlüğü
                                     ▼  TTS
```

#### Normalizasyon kuralları (ilk taslak)

| Tür | Örnek | TR okunuş | Kural |
|-----|-------|-----------|-------|
| Tolerans | `11 (± 1)` | "on bir, artı eksi bir" | `X (± Y)` kalıbı |
| Aralık | `10-14`, `10–14` | "on ile on dört" (veya "ondan on dörde kadar") | Sayı-tire-sayı, **kod bağlamı değilse** |
| Kesir | `3/16`, `1/4` | "on altıda üç", "dörtte bir" | Türkçe kesir: payda + "-da/-de" + pay |
| Özel kesir karakteri | `½`, `¼`, `¾` | "yarım", "çeyrek", "üç çeyrek" | Sözlük |
| Ondalık | `1.5 mm` (EN), `1,5 mm` (TR) | "bir buçuk milimetre" / "bir virgül beş milimetre" | Kaynak dilin ayırıcısına dikkat |
| Birim | `mm`, `cm`, `in`, `"`, `SPI`, `°C` | "milimetre", "santimetre", "inç", "inç", "inç başına dikiş", "santigrat derece" | Birim sözlüğü |
| Hata kodu | `E-07` | "E sıfır yedi" | Harf-tire-rakam: harfler tek tek, **baştaki sıfır okunur** |
| Model kodu | `S-7300A` | "S yetmiş üç yüz A" (?) | **Kullanıcılara sorulmalı mı ?:** Atölyede nasıl söyleniyor? |
| Dikiş tipi / sınıfı | `301`, `401`, `504`, `LSc-2` | "üç yüz bir"? "üç sıfır bir"? · "L S c iki" | Sektör alışkanlığı sorulacak |
| Parça no | `146391-001` | Okunmaz → "Parça numarası ekranda" (veya 3'lü gruplar halinde rakam rakam) | 6+ haneli kodlar |
| Kısaltma | `SPI`, `ASTM`, `No.` | "inç başına dikiş", "A S T M", "numara" | Kısaltma sözlüğü (harf harf mi, açılımı mı) |
| Madde işareti | `- ...`, `1. ...` | "Birincisi... İkincisi..." | Liste → sıralı cümle |
| Kaynak no | `[1]`, `[2]` | (okunmaz) | Silinir |
| Ek | `11'e`, `E-07'de` | "on bire", "E sıfır yedide" | Ek, sayının **okunuşunun** son ünlüsüne göre. En kolayı: LLM'e "sayı ve kodlardan sonra ek kullanma" kuralı ("E-07 hatasında" gibi) |

**Araçlar:**
- **Sayı → kelime:** `num2words` kütüphanesinin Türkçe desteği var (doğrulanmalı, kesir ve ek desteği sınırlı olabilir).
- **Hazır Türkçe TTS normalizasyon kütüphanesi:** Kapsamlı, bakımlı bir tane **bulunamadı.** NVIDIA NeMo text processing'in kural sistemi (İngilizce için güçlü) Türkçe için hazır değil gibi görünüyor (doğrulanmalı). Yani kural tablosunu **kendimiz yazacağız.** İyi tarafı: Bizim alanımız dar (dikiş/makine terimleri), tablo yönetilebilir boyutta.
- **Bulut servislerin kendi normalizasyonu** bir yedek. Ama kendi kurallarımızdan sonra metin zaten "okunmaya hazır" olacağı için TTS'e kalan iş az. Bir platformda Türkçe sayıların **İngilizce kurallarla** okunduğu ("3+1" → "three plus one") bir hata raporu var: TTS'in normalizasyonuna güvenmemek için bir sebep daha.

**Normalizasyonun test edilmesi:** Kural tablosu bir **test listesiyle** birlikte yazılır (girdi → beklenen okunuş). 2.2'deki round-trip (TTS → Whisper → sayı karşılaştırma) kontrolü pilotta otomatik test olarak kullanılabilir.

---

## 3. Kontrol soruları

> Kısa cevaplar yeterli, bilmediğine "bilmiyorum" yaz.

**K1.** Ekranda doğru yazan "10-14 SPI" sesli okunurken nasıl yanlış anlaşılabilir? Bu neden req.md R4 (halüsinasyon / yanlış değer) riskiyle ilgili?
> **C:** on eksi on dört şeklinde okunabilir, böylece yanlış anlaşılmalar olur 

🟡 Kısmen doğru. "Nasıl yanlış okunur" kısmı doğru, ama "neden R4 ile ilgili" kısmı eksik.

- **Nasıl:** "On eksi on dört" (negatif sayı gibi), "on on dört" (tire hiç okunmaz, "1014" gibi duyulur) ya da "SPI" anlamsız harfler olarak "es pi ay" diye okunabilir. Usta aralığı değil tek bir değeri ya da anlamsız bir sayı duyar.
- **Neden R4:** R4'ün özü **yanlış değerle dikim yapılması.** Bunun kaynağı LLM'in değeri uydurması da olabilir, doğru değerin **yanlış duyulması** da. Sonuç aynı: yanlış dikim. S11'deki katmanlar (alıntı ve sayı kontrolü) sadece **yazılı metni** kontrol eder. Metin doğru olduğu için kontrollerin hepsi geçer, ama ses yanlıştır. Yani TTS, S11 katmanlarının **arkasında kalan yeni bir hata noktası.** Bu yüzden normalizasyonu S11'in devamı sayıyoruz (0.3).

**K2.** Bir açık kaynak TTS modelinin kodu MIT lisanslı, model ağırlıkları CC-BY-NC lisanslı. Bu modeli şirketimizin üretim sisteminde kullanabilir miyiz? Neden?
> **C:** nc lisanslar, üretimde kullanılamaz. çünkü ticari faaliyetlerde kullanılmama şartı bulunur. 

✅ Doğru. Tamamlayıcı noktalar:

- Kodun MIT lisanslı olması bir şey değiştirmez. Asıl kısıt **ağırlıklarda.** Modeli ağırlıklar olmadan kullanamazsın.
- Sistemi satmasak bile şirket içi üretim sürecinde kullanmak NC lisanslarda genelde **ticari kullanım** sayılır ("doğrudan veya dolaylı gelir").
- **Test ve araştırma** için kullanılabilir. Örneğin kalite referansı olarak dinlemek.
- Aynı modelin **fine-tune'ları** da NC kalır (eğitim verisinden ve ana ağırlıktan "bulaşır"). "Biri Türkçe fine-tune yapmış, ama onun lisansı MIT yazıyor" diye güvenmemek gerekir.

**K3.** LLM cevabı cümle cümle üretirken her cümleyi hemen seslendirmek gecikmeyi azaltır. Bizim projede bunu neden doğrudan yapmıyoruz? Önerilen yaklaşım ne?
> **C:** çünkü cümlenin kontrol edilmesi gerekiyor, özellikle önemli dikim değerleri vs. varsa kontrol edilmelidir. ilk bir cümle söylenebilir devamı kontrolle gitmelidir. 

🟡 Gerekçe doğru, öneri kısmında bir düzeltme var.

- **Gerekçe ✅:** S11 Katman 5'e göre cevap kullanıcıya **gitmeden önce** alıntı ve sayı kontrolünden geçmeli. Okunmuş bir cümle geri alınamaz.
- **"İlk cümle söylenebilir" 🟡:** LLM'in ürettiği ilk cümle doğrulanmadan okunmamalı. Çünkü ilk cümle çoğu zaman cevabın **kendisi**dir ("Dış dikişler inç başına 11 artı eksi 1 olmalı"). Fikrin iyi bir versiyonu şu: Beklerken **sabit, değer içermeyen** bir cümle okumak ("Ceket şartnamesinde buldum, kontrol ediyorum."). Bu cümle LLM'den değil sistemden gelir, önceden seslendirilmiş olabilir. Hem sessizliği doldurur hem de risk taşımaz.
- **Önerilen yaklaşım (A):** LLM cevabı bitirir → alıntı/sayı kontrolü → **doğrulanmış** metin cümle cümle streaming TTS ile okunur. Gecikme sorun olursa B: Her cümle kendi sayılarıyla tek tek kontrol edilip okunur (2.3).

**K4.** Sesli okuma metnini LLM'e yazdırırken sayıları neden **rakamla** yazdırıp kelimeye **kodla** çeviriyoruz? LLM doğrudan "on bir artı eksi bir" yazsa ne sorun olur?
> **C:** düzügn bir ifade olmayabilir ya da ll diye farklı okuyabilir 

🟡 Kısmen doğru. "Düzgün ifade olmayabilir" doğru yönde. "ll" ise OCR'ın sorunu (kaynak-gosterme.md K3), buradaki konu değil.

Asıl sebep **otomatik kontrol edilebilirlik:**
- Sayı kontrolü (S11 Katman 5) rakamları karşılaştırır: Sesli metinde "11" ve "± 1" var mı, kaynak chunk'ta da var mı? Bu basit bir metin karşılaştırması.
- LLM "on bir artı eksi bir" yazarsa kontrol için önce yazıyı tekrar sayıya çevirmek gerekir. Türkçede aynı sayı birçok biçimde yazılabilir ("on bir", "onbir", "on bire", "on birlik"). Kontrol kırılgan olur.
- Daha tehlikelisi: LLM kelimeyle yazarken değeri **değiştirebilir** ("on iki artı eksi bir"). Kelimeyle yazılmış sayıda bu hata gözden kaçmaya daha açık.
- Kural tabanlı kod ise her seferinde **aynı** sonucu verir, test edilebilir: "11 (± 1)" → her zaman "on bir, artı eksi bir".

Kısaca: **LLM ne söyleneceğini seçer, kod nasıl okunacağını belirler, aradaki rakamlar kontrol edilir.**

**K5.** Bulut TTS kullanmanın gizlilik açısından riski ne? (Ne gönderiliyor?) Q1'in cevabı "bulut kullanılamaz" çıkarsa elimizdeki en uygun lokal seçenek hangisi ve neden?
> **C:** verilecek sesli cevaplar gönderildiği için müşterinin dosyasında bulunan gizli kaynak vs verilmiş olabilir. 

🟡 Birinci kısım doğru, ikinci kısım (lokal seçenek) cevaplanmamış.

- **Risk ✅:** Bulut TTS'e **sesli okunacak cevap metni** gider. Bu metin müşteri manuelinden değerler, alıntılar, model/parça numaraları içerebilir. Tamamlayıcı noktalar:
  - Bulut LLM kullanılıyorsa aynı metin zaten LLM sağlayıcısına gidiyor. TTS **ikinci bir sağlayıcı** (ikinci bir sözleşme, ikinci bir veri saklama politikası) demek. Aynı sağlayıcıda kalmak (ör. LLM + TTS ikisi de Azure'da) riski azaltır.
  - Sesli metni kısa tutmak ve uzun kodları okumamak giden veri miktarını da azaltır.
- **Lokal seçenek (eksik):** **Chatterbox Multilingual.** Gerekçe: Türkçe destekliyor, ağırlıkları **MIT** lisanslı (ticari kullanım serbest), kurum içinde çalışır. Diğer adayların her biri bir şartı sağlamıyor: XTTS-v2, F5, MMS ve Piper'ın Türkçe sesi NC lisanslı, Kokoro'da Türkçe yok. Çekinceler: GPU önerilir (Q5), Türkçe kalitesi henüz bilinmiyor. Alternatifler: Azure container (Türkçe ses varsa, Microsoft onayıyla), kendi Piper sesimizi lisanslı kayıtlarla eğitmek.

---

## 4. Derlenmiş Notlar

### 5.1 Seçenek listesi
- **Bulut (hepsi Türkçe destekli):** Azure (Emel, Ahmet + yeni HD sesler Elif, Aydın + multilingual sesler), Google Chirp 3 HD, ElevenLabs (Flash v2.5, Multilingual v2, v3, v4), OpenAI (tts-1, tts-1-hd, gpt-4o-mini-tts), Amazon Polly (Burcu).
- **Azure'un ayrıcalıkları:** En güçlü SSML / telaffuz sözlüğü, kelime zamanlaması (ekran senkronu için), **container ile lokal çalıştırma** imkânı (Türkçe ses için doğrulanmalı).
- **Açık kaynak:** Türkçe + ticari lisans + kalite üçlüsünü sağlayan tek güçlü aday şu an **Chatterbox Multilingual** (MIT). Piper'ın ticari kullanılabilir Türkçe sesi yok. XTTS-v2, F5-TTS, MMS sadece test için (NC). Kokoro'da Türkçe yok.

### 5.2 Türkçe / İngilizce kalite
- 4 test cümlesi (genel TR, TR+EN karışık sayılı, EN teknik, kod listesi), her biri **ham** ve **normalize edilmiş** iki halde.
- Değerlendirme: Kritik değer doğruluğu (evet/hayır), round-trip STT kontrolü, 1–5 doğallık puanı (mümkünse ustalarla), atölye gürültüsünde dinleme.
- Sistematik deneme **pilota (req.md 6.1) devredildi** (araştırma task'ı deneme istemiyor). Çıktılar o zaman `Pre/notes/tts-samples/`.
- İsteğe bağlı: Web demolarında T2/T4 ile hızlı dinleme (kod yok), pilot aday listesini daraltmak için.

### 5.3 Gecikme ve streaming
- Bulut TTS'in ilk sesi ~0,1–0,5 sn. Darboğaz LLM.
- Cümle cümle seslendirme, S11 Katman 5 (cevap kullanıcıya gitmeden doğrulama) ile **çatışıyor.**
- **Öneri:** Önce tam cevap + doğrulama, sonra doğrulanmış metni streaming TTS ile okumak (A). Sabit mesajlar önceden seslendirilmiş. Gecikme sorun olursa cümle düzeyinde doğrulama (B).

### 5.4 Maliyet ve lisans
- Tahmini kullanımda (~2,4M karakter/ay) bulut maliyeti ayda ~36–240 $. **Maliyet karar verdirici değil.**
- Açık modellerde **üç lisans** kontrol edilir: kod, ağırlık, eğitim verisi. NC kısıtı fine-tune'lara geçer. Şirket içi kullanım da "ticari" sayılır.

### 5.5 Metin normalizasyonu
- Ekran metni ≠ sesli metin. **Ayrı, kısa (1–3 cümle) sesli metin** üretilir. Kaynak numaraları okunmaz, listeler sıralı cümleye çevrilir, uzun kodlar ekrana yönlendirilir.
- **LLM ne söyleneceğini seçer (rakamla), kod nasıl okunacağını belirler.** Arada sayı kontrolü.
- Türkçe hazır normalizasyon kütüphanesi yok → **alanımıza özel kural tablosu + test listesi** yazılacak.
- Kullanıcılara sorulacak: Model kodları, dikiş tipleri (301: "üç yüz bir" mi "üç sıfır bir" mi?) ve İngilizce terimler atölyede nasıl söyleniyor?

### Projemiz için ilk öneri

| Konu | Öneri | Alternatif | Gerekçe |
|------|-------|-----------|---------|
| **TTS (test aşaması)** | **Azure** (Türkçe neural + HD + multilingual sesler) | Google Chirp 3 HD, ElevenLabs | En güçlü SSML/telaffuz kontrolü, kelime zamanlaması, container ile lokale geçiş yolu. Public test verisiyle bulut kullanımı sorun değil |
| **TTS (Q1 = bulut yasak ise)** | **Chatterbox Multilingual** (lokal, GPU) | Azure container (Türkçe ses varsa, onay gerekir) · Kendi Piper sesimizi eğitmek (CPU, lisanslı kayıt gerekir) | Türkçe + ticari lisanslı tek güçlü açık model. **Türkçe kalitesi 5.2'de doğrulanmalı** |
| **Streaming** | Tam cevap + doğrulama → sonra streaming TTS | Cümle düzeyinde doğrulama + seslendirme | R4: Doğrulanmamış değer duyulmamalı |
| **Sesli metin** | LLM'den ayrı kısa sesli metin (rakamlarla) + sayı kontrolü + kural tabanlı normalizasyon | Ekran metninden sadece kurallarla türetme | Kısalık + değer güvenliği |
| **Normalizasyon** | Kendi kural tablomuz (tolerans, aralık, kesir, birim, kod, kısaltma) + test listesi | TTS'in kendi normalizasyonu (yedek) | Türkçe hazır kütüphane yok, alanımız dar |
| **Arayüz (Adım 6'ya)** | Butonla okuma, tekrar/yavaş oku, okunan cümle ekranda vurgulu | Otomatik okuma (ayarla) | Atölye ortamı, çok kullanıcılı alan |
| **Ses klonlama** | Gerek yok | Kurumsal ses istenirse (rıza + hukuk onayı) | Hazır net bir ses yeterli |

**Açık kalanlar:** Q1 (bulut mu lokal mi), Q5 (GPU), Chatterbox'ın Türkçe kalitesi, Azure container'da Türkçe ses var mı, atölyede terim/kod okunuş alışkanlıkları, kulaklık mı hoparlör mü.

---

## Kaynaklar

**Resmi dokümanlar**
- [Azure Speech dil ve ses desteği (tr-TR sesleri)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=tts)
- [Azure Speech fiyatlandırma](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/) (fiyatlar sayfada dinamik yükleniyor, hesaplayıcıdan kontrol edilmeli)
- [Azure Speech container'ları (genel bakış)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-container-overview) · [Neural TTS container](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-container-ntts)
- [Google Cloud TTS fiyatlandırma](https://cloud.google.com/text-to-speech/pricing) · [Chirp 3 HD sesleri](https://docs.cloud.google.com/text-to-speech/docs/chirp3-hd) · [Google SSML](https://docs.cloud.google.com/text-to-speech/docs/ssml)
- [ElevenLabs modeller (diller, gecikme, normalizasyon notları)](https://elevenlabs.io/docs/overview/models)
- [OpenAI Text-to-speech rehberi](https://developers.openai.com/api/docs/guides/text-to-speech) · [OpenAI fiyatlandırma](https://developers.openai.com/api/docs/pricing)
- [Amazon Polly: Burcu (neural Türkçe ses) duyurusu](https://aws.amazon.com/about-aws/whats-new/2024/02/amazon-polly-neural-turkish-voice-burcu) · [Polly sesleri](https://docs.aws.amazon.com/polly/latest/dg/available-voices.html) · [Polly Türkçe fonem tablosu](https://docs.aws.amazon.com/polly/latest/dg/ph-table-turkish.html)

**Açık modeller (model kartları / repolar)**
- [Chatterbox (Resemble AI)](https://resemble.ai/chatterbox) · [NVIDIA model kartı (Chatterbox Multilingual)](https://build.nvidia.com/resembleai/chatterbox-multilingual-tts/modelcard)
- [Piper Türkçe sesleri (Hugging Face)](https://huggingface.co/rhasspy/piper-voices/tree/main/tr/tr_TR) · [tr_TR-dfki MODEL_CARD](https://huggingface.co/rhasspy/piper-voices/blob/6fb8245d6d27fef8988272e0c8e9f5018da1bbbf/tr/tr_TR/dfki/medium/MODEL_CARD)
- [Fish Speech / OpenAudio S1 model kartı](https://huggingface.co/fishaudio/s1-mini/blob/main/README.md)
- [FreyaTTS: Turkish-first speech synthesis (arXiv, 2026)](https://arxiv.org/pdf/2607.09530)

**İkincil kaynaklar (doğrulanmalı: blog / pazarlama / üçüncü taraf)**
- [Open Source Turkish TTS: A Developer's Guide (ablt.dev)](https://www.ablt.dev/blog/turkish-tts/)
- [free-turkish-tts-models (GitHub listesi)](https://github.com/Rumeysakeskin/free-turkish-tts-models)
- [Best Open Source Self-Hosted TTS Models in 2026 (Pinggy)](https://pinggy.io/blog/best_open_source_self_hosted_text_to_speech_models/)
- [Best Open-Source TTS 2026 (findskill.ai)](https://findskill.ai/blog/best-open-source-tts-2026/)
- [XTTS-v2 review: lisans ve Coqui'nin kapanması (promptquorum)](https://www.promptquorum.com/power-local-llm/xtts-v2-review) · [Coqui TTS review](https://www.promptquorum.com/power-local-llm/coqui-tts-review)
- [Piper TTS review: GPL-3.0 geçişi (promptquorum)](https://www.promptquorum.com/power-local-llm/piper-tts-review)
- [F5-TTS lisans notları (soniqo)](https://soniqo.audio/guides/f5-tts) · [Kokoro dil listesi (soniqo)](https://soniqo.audio/guides/kokoro)
- [Azure TTS fiyat özeti (texttolab)](https://texttolab.com/blog/azure-text-to-speech-pricing)
- [Twilio: Polly neural ses fiyatı (bayi fiyatı)](https://twilio.com/en-us/changelog/new-text-to-speech-voices-for-say-update-03-2025)
- [Vapi Flash v2.5 bağımsız gecikme ölçümü](https://humannessindex.vapi.ai/models/elevenlabs-flash-v2-5)
- [Türkçe TTS'de sayıların İngilizce okunması hata raporu (Vapi)](https://vapi.ai/community/m/1447889126128091186)
- [Wikimedia: TTS metin normalizasyonu prototipi (NeMo)](https://phabricator.wikimedia.org/T426756)
- [Mintlemon Turkish NLP normalizer](https://mintlemon-turkish-nlp.readthedocs.io/en/latest/_module/normalizer.html)
- Streaming ve cümle bölme pratikleri: [Smallest AI](https://docs.smallest.ai/atoms/developer-guide/build/agents/patterns/streaming), [KugelAudio](https://docs.kugelaudio.com/streaming-best-practices), [Fish Audio realtime streaming](https://docs.fish.audio/features/realtime-streaming)
