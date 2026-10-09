# Arayüz ve Orkestrasyon (Adım 6)

> **Başlangıç:** 2026-10-09
> **İlgili plan:** [req.md, Adım 6](../req.md) · Önceki: [rag-temelleri.md](rag-temelleri.md), [pdf-isleme.md](pdf-isleme.md), [kaynak-gosterme.md](kaynak-gosterme.md), [tts.md](tts.md) · Faz 1 denemesi: [faz1_output/report.md](../../faz1_output/report.md)



---

## 0. Kavramlar

### 0.1 Arayüz (frontend) ve arka uç (backend)

**Ne demek?**
- **Arayüz (*frontend*, *UI: user interface*):** Kullanıcının gördüğü ve dokunduğu kısım. Soru kutusu, cevap metni, PDF görüntüleyici, ses oynatıcı, butonlar. Genelde **tarayıcıda** çalışır.
- **Arka uç (*backend*):** Arka planda işi yapan kısım. Arama, LLM çağrısı, doğrulama, TTS. **Sunucuda** çalışır.
- İkisi bir **API** (uygulama programlama arayüzü) üzerinden konuşur: Arayüz "şu soruyu cevapla" der, arka uç cevabı, kaynak sayfayı, vurgu kutularını ve ses dosyasını geri gönderir.

**Benzetme:** Restoran. Salon (arayüz) müşterinin oturduğu, menüyü gördüğü yer. Mutfak (arka uç) yemeğin yapıldığı yer. Garson (API) siparişi mutfağa götürür, yemeği salona getirir. Salonu yenilemek mutfağı değiştirmeyi gerektirmez, yeter ki garson aynı dili konuşsun.

**neden önemli?** Faz 1 denemesinde ikisi **tek bir Python dosyasında** ([faz1-test.py](../../faz1-test.py)) iç içeydi. Bu deneme için doğru, ama ileride arayüzü değiştirmek isteyeceğiz (prototip → üretim, PC → tablet). arayüz değişse bile RAG hattı aynı kalacağı için problem yok. 

### 0.2 Python tabanlı arayüz çatıları vs. özel web arayüzü

**Ne demek?**
- **Python arayüz çatıları** (Streamlit, Gradio, NiceGUI, Chainlit): Sadece Python yazarak web arayüzü yapmayı sağlayan kütüphaneler. HTML/JavaScript bilmeye gerek yok. Hazır bileşenler var: metin kutusu, buton, ses oynatıcı, sohbet penceresi.
- **Özel web arayüzü** (React, Next.js, Vue + ayrı bir Python API, ör. FastAPI): Arayüz JavaScript ile, sıfırdan veya hazır parçalarla yazılır. Her piksel kontrol edilebilir.


**Neden önemli?** 
sıradan bir sohbet ekranı olmadığı için : 
- PDF sayfası + **vurgu kutusu** + sayfada gezinme
- Ses oynatıcı + okunan cümlenin ekranda vurgulanması (tts.md 2.3)
- Atölye koşulları:  eldiven vb. ekipman kullanımlarında da kolaylık sağlaması gerekebilir. ( ses ile kullanım hedefleniyor evet fakat manuel kullanım da düşünülmeli )


**Streamlitte : "yeniden çalıştırma" (*rerun*) modeli.** 
Streamlit'te kullanıcı **herhangi bir butona** bastığında Python dosyası **baştan sona yeniden çalışır.** Basit uygulamalarda bu çok kolaylık sağlar (durum yönetimini düşünmezsin). Ama ses çalarken bir butona basılınca sesin kesilmesi, cevabın yeniden üretilmesi gibi sorunlar çıkabilir. Çözüm: Sonuçları "oturum hafızasında" (*session state*) saklamak ve sadece ilgili parçayı yeniden çizmek (*fragment*). Öğrenilebilir, ama karmaşık etkileşimlerde zorlaşır.

> Ara soru: Rerun modeli Kullanmayacaksak yerine ne yapacağız?

**Kısa cevap:** bir **ödünleşim** (*trade-off*). Pilot için Streamlit'i kullanmaya devam ediyoruz. Sorun çıkmasın diye birkaç basit kural uygulamak yeterli. Bu kurallar "karmaşık bir yama" değil, Streamlit'te herkesin yazdığı **standart yöntem.**

**Benzetme:** Streamlit, her soru geldiğinde **tahtayı tamamen silip baştan yazan** bir öğretmen gibi.
- **Artısı:** Öğretmenin "tahtada neyin nerede olduğunu" aklında tutması gerekmez. Her seferinde temiz bir sayfa. Kod bu yüzden çok basit.
- **Eksisi:** Tahtada 10 dakikada çözülmüş bir soru varsa ve öğretmen onu da siliyorsa, aynı soruyu **yeniden çözmek** zorunda kalır.
- **Session state = öğretmenin defteri:** Öğretmen tahtayı silmeden önce önemli sonuçları deftere yazar. Tahtayı yeniden yazarken çözümü yeniden yapmaz, **defterden kopyalar.**
- **Fragment = tahtanın bir köşesini silmek:** Sadece değişen kısım silinip yeniden yazılır, gerisi yerinde kalır.

**somut örnek:**
```
1. Usta soruyu sorar → retrieval + LLM + doğrulama + TTS: ~5–10 sn, LLM ücreti
2. Cevap ekranda. Usta [2] numaralı kaynak sekmesine tıklar
3. Streamlit dosyayı baştan çalıştırır:
   ❌ Session state yoksa: Soru YENİDEN cevaplanır. 10 sn bekleme, ikinci LLM ücreti,
      ve en kötüsü: LLM bu sefer biraz FARKLI bir cevap yazabilir. Usta her tıklamada
      değişen bir cevap görür (güven kaybı, R4 ile de ilgili).
   ✅ Session state varsa: Cevap "defterden" alınır, anında görünür, değişmez.
```

**Uygulanacak kurallar (pilot için):**
1. **Ağır iş sadece "Sor" butonunda çalışır.** `soru_cevapla()` sadece kullanıcı yeni bir soru sorduğunda çağrılır, sonucu (cevap, kaynaklar, bbox'lar, ses dosyası) session state'e yazılır.
2. **Ekran her zaman session state'ten çizilir.** Diğer tüm tıklamalar (kaynak sekmesi, ayarlar) sadece "defterden okuyup tahtaya yazar", hiçbir şeyi yeniden hesaplamaz.
3. **Bağımsız parçalar fragment olur.** Örneğin kaynak görüntüleyici paneli: Sekme değişince sadece o panel yenilenir, ses oynatıcı yerinde kalır.

 Bazı etkileşimler **tarayıcının içinde** olur ve Python'a hiç gitmez:
- Ses oynatıcının oynat/durdur/ileri sar düğmeleri tarayıcının kendi oynatıcısı → rerun yok.
- PDF görüntüleyicide kaydırma ve yakınlaştırma PDF.js içinde → büyük ihtimalle rerun yok (pilotta kontrol edilecek).
- Rerun'u tetikleyenler: "Sor" butonu, kaynak sekmesi değiştirme, Streamlit'in kendi butonları (ör. "Yavaş oku" butonu Streamlit butonu olursa).

**"Karmaşık etkileşimlerde zorlaşır" ne demek?** Aynı anda birçok şey değişiyorsa: Ses çalarken okunan cümlenin ekranda **anlık** vurgulanması, mikrofon dinlerken ekranın güncellenmesi, birden fazla panelin birbirini etkilemesi. Bunlar her biri "deftere ne yazılacak, hangi köşe silinecek" planlaması ister ve kod karışır. **Pilotta bu özellikleri basit tutuyoruz** (ses butonla, cümle vurgusu yok veya sonradan), o yüzden sorun olmaz.

**Streamlit yetmezse yerine ne var?**
| Seçenek | Nasıl çalışır | Ne zaman |
|---------|---------------|----------|
| **Streamlit + 3 kural** (yukarıda) | Tahtayı silip defterden yeniden yazar | **Pilot.** Önerilen |
| **NiceGUI** (olay tabanlı, *event-driven*) | Butona basınca **sadece o butonun fonksiyonu** çalışır, gerisi yerinde kalır. Tahtayı silmeyen, sadece değişen satırı düzelten öğretmen. Hâlâ sadece Python | Streamlit'te etkileşimler çok karışırsa, ama Python'da kalmak istersek |
| **Özel web** (React + FastAPI) | Ekranı tarayıcı yönetir. Python'a (arka uca) sadece soru sorulurken gidilir | Üretim: Senkron vurgu, tablet, yetkilendirme gerekince |

**Sonuç:** Rerun modeli pilot için bir engel değil. "Mutfağı salondan ayırma" ilkesi (6.1) sayesinde Streamlit yetmezse NiceGUI'ye veya özel web'e geçmek RAG hattını etkilemez, sadece salon değişir.

### 0.3 Orkestrasyon nedir?

**Ne demek?** Sistemin adımlarını **doğru sırayla, doğru verilerle** çalıştıran yapı. RAG Hattında bir soru şu adımlardan geçiyor:

```
Soru → sorgu analizi (marka, dil, doküman türü) → hybrid retrieval → rerank
     → eşik kontrolü (emin değilse "bulunamadı") → LLM (kaynak numaralı cevap)
     → kaynak/alıntı/sayı doğrulaması → sesli metin + normalizasyon → TTS
     → arayüze: cevap + sayfa + bbox + ses
```

Bu adımları birbirine bağlayan, bir adım başarısız olunca ne yapılacağına karar veren, her adımı kaydeden koda **orkestrasyon** denir.


**Orkestrasyon çatısı (*framework*) ne demek?** LangChain, LlamaIndex, Haystack gibi kütüphaneler bu bağlama işini hazır parçalarla yapmayı vaat eder: "Retriever", "QueryEngine", "Pipeline" gibi hazır kalıplar. Alternatifi **çatısız (düz Python)**: Her adım normal bir Python fonksiyonu, birbirini sırayla çağırıyor.

**Soyutlama (*abstraction*) kavramı:** Çatılar ayrıntıyı gizler. "3 satırda RAG" mümkün olur. Ama gizlenen ayrıntı **bizim en çok kontrol etmek istediğimiz yer** olabilir (prompt'un tam metni, hangi chunk'ın neden geldiği, metadata'nın taşınıp taşınmadığı). Bu yüzden "çatı mı, düz Python mu" sorusu aslında **"ne kadar kontrol istiyoruz?"** sorusu.

### 0.4 STT (konuşma tanıma) ve sesli soru

**Ne demek?** *Speech-to-Text* (konuşmadan metne): Kullanıcının sesli sorusunu yazıya çevirmek. TTS'in tersi. Yazıya çevrilen soru sonra normal bir metin sorusu gibi işlenir.

| Terim | Anlamı |
|-------|--------|
| *WER (word error rate)* | Kelime hata oranı. %10 WER: 10 kelimeden biri yanlış. **Kod ve sayılarda tek bir hata bile önemli** |
| *Bas-konuş (push-to-talk)* | Kullanıcı butona basınca dinleme başlar. Telsiz gibi |
| *Uyandırma kelimesi (wake word)* | Sistem sürekli dinler, "Hey asistan" duyunca soruyu almaya başlar. Siri, Alexa gibi |
| *Sözlük ipucu (phrase list / prompt)* | STT'ye "bu terimler geçebilir" listesini vermek: "overlok, lockstitch, S-7300A, SPI" |


**neden önemli?** Usta elleri meşgulken yazamayabilir (eldiven, kirli el, kumaş tutuyor). Ama **sesli soru yeni bir hata kaynağı:** "S-7300A" yerine "S-7300B" duyulursa yanlış makinenin kılavuzunda arama yapılır. Bu da R4'e (yanlış değer) giden bir yol.

### 0.5 Kavramlar birbirine nasıl bağlanıyor?

```
┌──────────────── ARAYÜZ (tarayıcı) ────────────────┐
│ Soru (yazı veya ses → STT) · Cevap · PDF+vurgu · 🔊 │
└───────────────────────┬────────────────────────────┘
                        │ API (istek / cevap)
┌───────────────────────▼────────────────────────────┐
│ ARKA UÇ: ORKESTRASYON                               │
│ analiz → retrieval → rerank → eşik → LLM            │
│ → doğrulama → sesli metin → TTS                     │
└─────────────────────────────────────────────────────┘
```

---

## 1. Anlatım

### 6.1 Arayüz seçenekleri

####  ekranın ihtiyaçları (seçim kriterleri)

| # | İhtiyaç | Nereden geliyor | Önem |
|---|---------|-----------------|------|
| K-a | PDF sayfası + **bbox vurgusu** + gezinme + yakınlaştırma | kaynak-gosterme.md 3. bölüm, Q9 | 🔴 Zorunlu |
| K-b | Birden fazla kaynak arasında geçiş ([1], [2], [3]) | kaynak-gosterme.md 4. bölüm | 🔴 Zorunlu |
| K-c | Ses: oynat / durdur / tekrar / yavaş oku, **okunan cümleyi vurgulama** | tts.md 2.3 | 🟡 Önemli |
| K-d | Durum gösterimi: "aranıyor", "doğrulanıyor", "bulunamadı", uyarı | rag-temelleri.md S11, tts.md R5 | 🔴 Zorunlu |
| K-e | Mikrofon butonu + tanınan metni onaylama (STT gerekirse) | 6.4 | 🟡 Duruma bağlı |
| K-f | Tablet / dokunmatik, büyük butonlar, uzaktan okunabilir yazı | Atölye ortamı | 🟡 Önemli |
| K-g | Kullanıcı girişi, marka bazlı yetki | Adım 7.3 | 🟡 Üretimde zorunlu |
| K-h | Geliştirme hızı, bizim Python bilgimizle yapılabilmesi | Araştırma/pilot aşaması | 🔴 Pilot için kritik |

#### Seçenekler

| Seçenek | Ne | PDF + bbox (K-a) | Ses ve senkron vurgu (K-c) | Yerleşim esnekliği | Öğrenme / hız | Not |
|---------|----|------------------|----------------------------|--------------------|---------------|-----|
| **Streamlit** | Python ile veri uygulaması / panel | ✅ `streamlit-pdf-viewer` (PDF.js, bbox, vurguya kaydırma). **Faz 1'de çalıştı** | 🟡 `st.audio` var. Otomatik çalma, cümle cümle sıralı çalma ve senkron vurgu için **özel JavaScript bileşeni** gerekir | 🟡 Kolonlar, sekmeler yeterli. Piksel kontrolü sınırlı | ✅ En kolay | Rerun modeli (0.2) karmaşık etkileşimde zorlaşır. `st.audio_input` ile mikrofon kaydı var (sürüm doğrulanmalı) |
| **Gradio** | Python ile model demosu (Hugging Face'in aracı) | 🟡 `gradio_pdf` bileşeni PDF.js ile gösteriyor, **bbox vurgusu belgelenmemiş** (özel bileşen yazmak gerekebilir) | 🟡 Ses bileşeni güçlü (mikrofon, akış). Senkron vurgu için özel kod | 🟡 Demo odaklı, karmaşık yerleşim zor | ✅ Kolay | Model demosu için ideal, ürün ekranı için sınırlı |
| **NiceGUI** | Python ile uygulama arayüzü (FastAPI + Vue tabanlı) | 🟡 Hazır bileşen yok, PDF.js gömülebilir (efor orta) | ✅ Olay tabanlı, JavaScript çağırmak kolay | ✅ İyi | 🟡 Orta | Streamlit'ten daha "uygulama gibi". Ekosistem daha küçük (doğrulanmalı) |
| **Chainlit** | Python ile sohbet arayüzü | ❌ PDF + bbox için uygun değil (yan panelde eleman gösterilebilir, vurgu yok) | 🟡 Ses desteği var | ❌ Sohbet kalıbına bağlı | ✅ Kolay | Sohbet ürünü için iyi, bizim "cevap + sayfa" ekranına uymuyor |
| **Open WebUI** | Hazır, kurulup kullanılan ChatGPT benzeri arayüz | ❌ Sayfa görüntüleme + bbox yok | 🟡 TTS/STT entegrasyonu var | ❌ Hazır ürün, değiştirmek zor | ✅ Kurulum kolay | **Lisans:** v0.6.6'dan (Nisan 2025) beri **marka koruma maddesi:** 50'den fazla kullanıcıda "Open WebUI" adı/logosu kaldırılamaz, kaldırmak için kurumsal lisans gerekir. Bizim özel ekranımıza uymadığı için **elendi** |
| **Özel web** (React/Next.js + FastAPI) | Arayüz JavaScript ile, arka uç Python API | ✅ PDF.js veya hazır React bileşenleri (ör. `react-pdf`, `react-pdf-highlighter`, doğrulanmalı) ile tam kontrol | ✅ Tam kontrol: kelime zamanlamasıyla vurgu, sıralı çalma | ✅ Tam | ❌ En yavaş, JavaScript/React bilgisi gerekir | Üretim, tablet, yetkilendirme için en uygun |

#### Karşılaştırmadan çıkan sonuç

İki ayrı sorunun cevabı farklı:

| Soru | Cevap |
|------|-------|
| **Pilot için ne kullanalım?** | **Streamlit.** Faz 1'de PDF + bbox zaten çalışıyor, Python ile yazılıyor, haftalar değil günler sürer. Senkron vurgu gibi "olsa iyi olur" özellikler pilotta basit tutulur (butonla oynat, cümle vurgusu yok veya sonradan) |
| **Üretimde ne kullanalım?** | Muhtemelen **özel web (React + FastAPI).** Senkron vurgu, tablet uyumu, yetkilendirme ve kurum kimlik doğrulaması (SSO) burada en temiz çözülür. **Karar pilottan sonra:** Streamlit kullanıcıların ihtiyacını karşılıyorsa üretime de taşınabilir |

**Bunu mümkün kılan ilke: Mutfağı salondan ayırmak (0.1).** RAG hattı arayüzden bağımsız bir Python paketi olarak yazılır, tek bir giriş noktası olur:

```python
cevap = soru_cevapla(soru="...", kullanici=..., dil="tr")
# cevap: metin, kaynaklar [(doc_id, sayfa, basili_sayfa, bbox'lar)],
#        doğrulama sonucu, sesli metin, ses dosyası
```

Streamlit bu fonksiyonu doğrudan çağırır. İleride özel web'e geçilirse aynı fonksiyon bir FastAPI uç noktasının (*endpoint*) arkasına konur. **RAG hattında tek satır değişmez.**

### 6.2 Tek ekran düzeni (wireframe)

> Taslak çizim burada ASCII olarak. req.md'de `wireframe.png` deniyordu. Pilot arayüzü yapılınca ekran görüntüsüyle değiştirilebilir.

#### Geniş ekran (PC / yatay tablet)

```
┌───────────────────────────────────────────────────────────────────────────────┐
│ [Marka: Tümü ▾] [Doküman: Tümü ▾]                                    👤 Ayşe │
│ ┌─────────────────────────────────────────────────────────┐ ┌────┐ ┌──────┐  │
│ │ S-7300A'da üst iplik gergin değil, ne yapmalıyım?       │ │ 🎤 │ │ Sor  │  │
│ └─────────────────────────────────────────────────────────┘ └────┘ └──────┘  │
├────────────────────────────────────┬──────────────────────────────────────────┤
│ CEVAP                ✔ Kaynakla    │ KAYNAK  [1] Brother S-7300A ▸ [2] ...    │
│                        doğrulandı  │ s.90 (PDF s.101)        ◀ ▶  ➖ ➕  ⤢     │
│                                    │ ┌──────────────────────────────────────┐ │
│ Üst iplik gerginliği zayıf veya    │ │  Troubleshooting                     │ │
│ alt iplik gerginliği fazla olabilir│ │ ┌──────────────────────────────────┐ │ │
│ [1]. Önce üst iplik gerginliğini   │ │ │█ Upper thread is not tight     █│ │ │ ← sarı vurgu
│ artırın, gerekirse alt ipliği      │ │ │█ Is the upper thread tension...█│ │ │
│ ayarlayın (kılavuz s.65, s.67) [1].│ │ └──────────────────────────────────┘ │ │
│                                    │ │  (tablonun geri kalanı: açık mavi)   │ │
│ ┌────────────────────────────────┐ │ │                                      │ │
│ │ 🔊 ▶ Oynat  ⏸  ↺ Tekrar  🐢 Yavaş│ │ │                                      │ │
│ └────────────────────────────────┘ │ └──────────────────────────────────────┘ │
│                                    │ [Dokümanın tamamını aç]                  │
├────────────────────────────────────┴──────────────────────────────────────────┤
│ Önceki sorular: • Ceket dış dikiş SPI?  • E-07 hatası?                        │
└───────────────────────────────────────────────────────────────────────────────┘
```

#### Dar ekran (dikey tablet / telefon)

```
┌──────────────────────────────┐
│ [Soru................] 🎤 Sor│
├──────────────────────────────┤
│ CEVAP           ✔ Doğrulandı │
│ Dış dikişler: inç başına     │
│ ╔══════════════════════════╗ │
│ ║   11 (± 1) dikiş  [1]    ║ │ ← kritik değer büyük punto
│ ╚══════════════════════════╝ │
│ 🔊 ▶  ↺  🐢                  │
├──────────────────────────────┤
│ KAYNAK [1] GL-PD-14-04A s.22 │
│ ┌──────────────────────────┐ │
│ │  ...vurgulu sayfa...     │ │
│ └──────────────────────────┘ │
└──────────────────────────────┘
```

#### Tasarım kararları ve gerekçeleri

| Karar | Gerekçe |
|-------|---------|
| **Cevap solda, kaynak sağda, aynı anda görünür** | Usta değeri cevapta okur, gözünü sağa kaydırıp **kaynakta doğrular.** Kaynağı ayrı bir sekmeye gizlemek doğrulamayı azaltır (kaynak-gosterme.md 0.3) |
| **Kritik değer büyük punto ile ayrıca gösterilir** | Atölyede ekrana uzaktan bakılır. "11 (± 1)" cümle içinde kaybolmamalı. (Değer cevaptan **kodla** çıkarılır, LLM ayrıca yazmaz. Sayı kontrolünden geçmiş değer gösterilir) |
| **Doğrulama rozeti:** ✔ doğrulandı / ⚠ kısmen / ✖ bulunamadı | S11 Katman 5'in sonucunu kullanıcıya göstermek. ⚠ durumunda cevap gri ve "Kaynağı kontrol edin" uyarısıyla |
| **Basılı + PDF sayfa numarası birlikte:** "s.90 (PDF s.101)" | Faz 1'de çözüldü, usta basılı kılavuzda 90'a bakar |
| **Kaynak sekmeleri [1] [2]**, cevaptaki [1]'e tıklayınca o kaynak açılır | Çok kaynaklı cevaplar (kaynak-gosterme.md 4. bölüm) |
| **Ses: butonla başlar** (ayarla otomatik yapılabilir) | Çok kullanıcılı atölyede her cevabın kendiliğinden okunması rahatsız edebilir. Tarayıcılar da otomatik çalmayı genelde engeller (tts.md 2.3) |
| **"Bulunamadı" ekranı ayrı tasarlanır** | "Bu bilgi manuellerde bulunamadı. İlgili birimle teyit edin." + yakın sonuçlar (varsa) **"cevap değildir"** etiketiyle. Yanlış cevap vermek yerine bilmediğini açıkça söylemek (S11 Katman 2) |
| **Mikrofon → tanınan metin kutuya yazılır, kullanıcı onaylar** | 6.4: STT hatası yanlış makinede aramaya yol açmasın |
| **Büyük dokunma alanları** (≥ 48 px), yüksek kontrast | Tablet, eldiven, atölye ışığı |

#### Etkileşim sırası (bir soru için)

```
1. Kullanıcı soruyu yazar / söyler (söylerse: metin kutuya gelir, onaylar)
2. Ekran: "Kaynaklar aranıyor..."                         (retrieval + rerank)
3. Ekran: "Cevap hazırlanıyor..."                          (LLM)
4. Ekran: "Kaynakla kontrol ediliyor..."                   (doğrulama)
5. Cevap + rozet + kaynak sayfası (vurgulu) birlikte açılır
6. 🔊 butonu aktif (veya ayara göre otomatik okuma başlar)
```

**Neden cevap metni akarak (kelime kelime) gösterilmiyor?** Sohbet uygulamalarında alışılmış, bekleme hissini azaltıyor. Ama tts.md R5'teki çatışmanın aynısı burada da var: **Doğrulanmamış değer ekranda görünür.** Pilot önerisi: Cevap doğrulandıktan sonra bir kerede gösterilir. 2–4. adımlardaki durum mesajları beklemeyi anlamlı kılar. Kullanıcılar beklemeyi uzun bulursa: Metin akarak ama **gri ve "doğrulanıyor" etiketiyle** gösterilir, doğrulama bitince normal renge döner.

### 6.3 Orkestrasyon çatıları

#### hattın  özellikleri (seçim kriterleri)

1. **Doğrusal ve belirli (deterministik):** Her soru aynı adımlardan geçer. Bir "ajan" (*agent*) gibi modelin kendi kendine hangi aracı kullanacağına karar vermesi **gerekmiyor**. Hatta istenmiyor: Öngörülebilirlik R4 için önemli.
2. **Özel adımlar çok:** bbox/sayfa metadata'sının sonuna kadar taşınması, basılı sayfa numarası, eşik kontrolü, alıntı ve sayı doğrulaması, sesli metin ve normalizasyon. Bunların **hiçbiri** çatıların hazır parçalarında yok, her durumda kendimiz yazacağız.
3. **Şeffaflık:** Her soruda "hangi chunk geldi, skoru neydi, LLM'e tam olarak ne gitti, doğrulama neden başarısız oldu" görülebilmeli. Hem hata ayıklama hem **denetim izi** için (yanlış dikim şikâyetinde geriye dönüp bakmak).

#### Seçenekler

| Seçenek | Ne | Öğrenme eğrisi | Esneklik | Kaynak gösterme (citation) desteği | Not |
|---------|----|----------------|----------|-----------------------------------|-----|
| **LangChain (v1) / LangGraph** | En geniş ekosistem. v1 (Ekim 2025) ile **ajan odaklı** hale geldi (`create_agent`, LangGraph motoru üzerinde). Eski "chain" yapıları ayrı pakete (`langchain-classic`) taşındı | ❌ Yüksek: çok katman, sık değişen API | ✅ Her şey mümkün, ama soyutlamalarla "boğuşmak" gerekebilir | 🟡 Kalıplar var, ama bbox/sayfa ve doğrulama yine bizde | API sık değişiyor (v1 geçişi bunun örneği). Bizim doğrusal hattımız için ajan yapısı fazla |
| **LlamaIndex** | **Doküman ve retrieval odaklı.** Ingestion, indeksleme, sorgu motorları | 🟡 Orta | 🟡 İyi | ✅ En iyisi: Metadata (sayfa, dosya) chunk'lara taşınıyor, sayfa numaralı atıf örneği resmi dokümanda var, `CitationQueryEngine` | Ingestion tarafında (parse → chunk → indeks) işe yarar parçaları var |
| **Haystack 2.x** (deepset) | **Pipeline odaklı:** Bileşenler tipli, açıkça bağlanır, YAML ile tanımlanabilir | 🟡 Orta | ✅ İyi, yapı açık | 🟡 Genel destek var (doğrulanmalı) | Üretim odaklı, adımlar görünür. Çatılar içinde felsefe olarak bize en yakını |
| **Çatısız (düz Python)** | Her adım bir fonksiyon. Doğrudan kütüphaneler: `qdrant-client`, `FlagEmbedding` (bge-m3, reranker), LLM sağlayıcısının SDK'sı, TTS SDK'sı | ✅ En düşük (sadece Python) | ✅ Tam kontrol | Kendimiz yazarız. Ama kaynak-gosterme.md 2. bölümde zaten tasarladık: numaralı chunk → [n] → metadata | Bir kaynak ikinci bir yorumu destekliyor: "Tek doküman kümesi + tek LLM sağlayıcısı için SDK + vektör DB istemcisi yeterli" (doğrulanmalı) |

#### Bizim için anlamı

- Çatıların en büyük vaadi ("3 satırda RAG") bizim için **değerli değil:** Zor kısımlar (bbox, doğrulama, eşik, sesli metin) her durumda bizde.
- Çatının **maliyeti** ise gerçek: Ek öğrenme, gizlenen prompt/metadata akışı, sürüm değişikliklerinde kırılma.
- **Öneri: Çatısız (düz Python), modüler.** Her adım ayrı, test edilebilir bir modül:

```
visual_agent/
  ingestion/      parse (Docling) → temizlik → chunk → metadata → indeks
  retrieval/      sorgu analizi, hybrid arama (Qdrant), rerank, eşik
  generation/     prompt, LLM çağrısı, [n] ayrıştırma
  verification/   kaynak no / alıntı / sayı kontrolü        (S11 Katman 5)
  speech/         sesli metin, normalizasyon, TTS            (tts.md)
  pipeline.py     soru_cevapla(): adımları sırayla çağırır + her adımı loglar
  app_streamlit.py   pilot arayüzü (sadece pipeline'ı çağırır)
```

- **Seçici kullanım serbest:** Bir çatının tek bir parçası işe yarıyorsa (ör. LlamaIndex'in bir okuyucusu) o parça kullanılabilir. Hattın omurgası bizde kalır.
- **Loglama (denetim izi):** Her soru için tek bir kayıt: soru, filtreler, gelen chunk'lar ve skorları, LLM'e giden prompt, cevap, doğrulama sonucu, gösterilen sayfa. Basit JSON log ile başlanır. İleride LLM izleme araçları (Langfuse vb., doğrulanmalı) eklenebilir. Gizlilik: Loglar da müşteri verisi içerir, Adım 7'de ele alınacak.
- **Ne zaman çatıya geçmeyi düşünürüz?** Sistem çok adımlı ajan davranışına evrilirse (ör. "önce makine kılavuzuna bak, bulamazsan şartnameye bak, sonra karşılaştır"). O zaman LangGraph veya Haystack yeniden değerlendirilir.

### 6.4 STT (sesli soru)

#### Gerekli mi?

| Lehine | Aleyhine |
|--------|----------|
| Eller meşgul (kumaş, makine), eldiven, kirli el | **Atölye gürültüsü** tanıma doğruluğunu düşürür |
| Klavye kullanmayan kullanıcılar için daha kolay | **Kod ve model adları** ("S-7300A", "E-07", "LSc-2") en çok yanlış tanınan şeyler, ve tam da yanlış olmaması gerekenler |
| TTS ile birlikte "eller serbest" bir deneyim | Türkçe cümle + İngilizce terim karışımı ("lockstitch", "overlok") |
| | Ses kaydı **kişisel veri** (KVKK). Bulut STT'ye kullanıcının sesi gider |

**Sonuç:** Gerekli olup olmadığı **kullanıcıya bağlı** (req.md Q4 açık kalıyor). Ama iyi haber: STT mimariyi değiştirmiyor. Sesli soru yazıya çevrilir, gerisi aynı. Bu yüzden **sonradan eklenebilir.** Pilotta isteğe bağlı bir mikrofon butonu olarak denenip kullanıcı tepkisine göre karar verilebilir.

#### Nasıl yapılmalı? (gerekirse)

| Karar | Öneri | Gerekçe |
|-------|-------|---------|
| Dinleme şekli | **Bas-konuş** (butona basılı tut veya bas-bırak) | Sürekli dinleme (uyandırma kelimesi) gürültülü ortamda yanlış tetiklenir, gizlilik açısından da sorunlu |
| Tanınan metin | **Kutuya yazılır, kullanıcı görür ve onaylar/düzeltir**, sonra aranır | Yanlış tanınan model kodu yanlış manuelde aramaya yol açmasın. "Duyduğunu tekrar eden dinleyici" (0.4) |
| Terim ipucu | Marka, model, hata kodu ve teknik terim listesi STT'ye verilir (Azure *phrase list*, Whisper *prompt*) | Kodların tanınma doğruluğunu artırır. Liste ingestion'da metadata'dan otomatik çıkarılabilir (model adları, hata kodları) |
| Mikrofon | Gürültü önleyici kulaklık-mikrofon veya yakın mikrofon | Tablet mikrofonu atölyede yetersiz kalabilir (tts.md'deki kulaklık sorusu Q10 ile birlikte) |

#### Seçenekler

| Seçenek | Türkçe | Lokal mi | Not |
|---------|--------|----------|-----|
| **Whisper large-v3** (OpenAI, açık model, MIT) | ✅ | ✅ | En doğru Whisper. **GPU gerekir**, CPU'da gerçek zamandan yavaş |
| **Whisper large-v3-turbo** | ✅ | ✅ | ~2 kat hızlı, doğruluk biraz düşük (çok dilli ortalamada fark ~1,5 puan WER, Türkçe için ayrı rakam bulunamadı). Bir ölçümde CPU'da tek iş parçacığıyla gerçek zamandan ~4 kat yavaş (doğrulanmalı) → pratikte GPU |
| **faster-whisper** | ✅ | ✅ | Whisper'ın aynı modellerini daha hızlı çalıştıran motor (CTranslate2, int8). CPU'da kısa sorular (3–5 sn) için kabul edilebilir olabilir, **ölçülmeli** |
| **Azure Speech STT** | ✅ | Bulut (container seçeneği var) | *Phrase list* (eğitimsiz terim ipucu), gerekirse özel model (Custom Speech). TTS de Azure olursa tek sağlayıcı |
| **Google / OpenAI STT** (gpt-4o-transcribe vb.) | ✅ | Bulut | Kalite yüksek. Gizlilik Q1'e bağlı |

**Q1 ve Q5 ile bağlantı:** Bulut yasaksa ve GPU yoksa sesli soru zorlaşır (CPU'da faster-whisper ölçülmeli). GPU varsa Whisper lokalde rahat çalışır.

---

## 2. Kontrol soruları


**K1.** RAG hattını arayüzden ayrı bir Python paketi olarak yazmanın (`soru_cevapla()` fonksiyonu) bize ne faydası var? Streamlit'ten özel web arayüzüne geçerken ne değişir, ne değişmez?
> **C:** böylece rag hattı hep aynı kalır, arayüzü değiştirmiş olmak bir şeyi değiştirmez 

🟡 Ana fikir doğru. Sorunun "ne değişir" kısmı ve diğer faydalar eksik.

- **Değişmeyenler:** Ingestion, retrieval, rerank, eşik, LLM, doğrulama, sesli metin ve TTS. Yani `soru_cevapla()` ve altındaki her şey.
- **Değişenler:** Sadece salon. Streamlit dosyası (`app_streamlit.py`) yerine React ile yazılmış bir arayüz gelir. Arayüz artık Python içinde olmadığı için araya **bir FastAPI uç noktası** (`POST /soru`) eklenir. Bu uç nokta `soru_cevapla()`'yı çağırır ve sonucu JSON olarak döner.
- **Diğer faydalar:**
  - **Arayüzsüz test:** Test soru seti (Adım 0.4) ekran açmadan, bir script ile `soru_cevapla()` üzerinden otomatik çalıştırılabilir. Değerlendirme (Adım 4.4) bunu gerektiriyor.
  - **Birden fazla arayüz:** Aynı fonksiyon PC ekranından, tablet uygulamasından veya ileride başka bir sistemden çağrılabilir.
  - **Hata ayırma:** Sorun ekranda mı hatta mı, ayrı ayrı bakılabilir.

**K2.** Open WebUI ve Chainlit hazır ve kolay araçlar. Neden bizim ekranımız için uygun değiller?
> **C:** çünkü hazır frameworklerde gizlenen kısımlar belki de bizim kontrol sağlamak istediğimiz yerler, ayrıca bizim kullanacağımız ekran yapısı eldiven vb gibi ekipmanlarla da kullanılmaya uygun olması gerekebilir. klasik bir sohbet ekranı olmayacaktır. 

🟡 "Klasik bir sohbet ekranı olmayacak" doğru ve asıl sebep bu. İlk cümle ise başka bir sorunun cevabı.

- **"Gizlenen kısımlar"** orkestrasyon çatılarının (LangChain vb.) sorunuydu (K4). Open WebUI ve Chainlit **arayüz** araçları. Onlarda sorun gizlenen kısım değil, **ekranın kalıbının sabit olması.**
- **Asıl sebep:** Bizim zorunlu ihtiyacımız (K-a) **PDF sayfasının vurgu kutusuyla, gezinilebilir şekilde** gösterilmesi. İki araç da sohbet kalıbına bağlı ve sayfa + bbox vurgusu yok. Cevap ile kaynak sayfayı yan yana koyamıyoruz, doğrulama rozeti ve "bulunamadı" ekranı gibi özel durumları istediğimiz gibi tasarlayamıyoruz.
- **Open WebUI'ya özel:** v0.6.6'dan beri lisansta **marka koruma maddesi** var. 50'den fazla kullanıcıda "Open WebUI" adı ve logosu kaldırılamıyor, kaldırmak için kurumsal lisans gerekiyor.
- **Eldiven ve atölye konusu** doğru bir ihtiyaç, ama bu iki aracı eleme sebebi değil. Büyük butonlar ve kontrast her arayüzde ayrıca tasarlanmalı.

**K3.** Ekranda cevap metnini sohbet uygulamalarındaki gibi kelime kelime akıtarak göstermek beklemeyi azaltır. Bizim projede bunun riski ne, önerilen çözüm ne?
> **C:** kontrol yapılmadığı için yanlış bir bilgi aktarılmış olabilir, ilk başta sisteme kaydedilmiş örnek bir cümle  " şu anda x konusunun y bilgisini getiriyorum " gibi bi cümle ekrana gelirse beklemeyi de azaltmış olur 

✅ Risk doğru, önerin de tasarımdakiyle uyumlu (tts.md K3'teki "sabit cümle" fikrinin ekrandaki karşılığı). Tamamlayıcı noktalar:

- **Risk:** Metin akarken doğrulama henüz yapılmamış. Usta "12 SPI" gibi yanlış bir değeri doğrulama bitmeden görebilir. Metin sonradan düzeltilse bile ilk gördüğü değer aklında kalabilir.
- **Önerilen çözüm:** Cevap **doğrulandıktan sonra** bir kerede gösterilir. Beklerken adım adım durum mesajları: "Kaynaklar aranıyor... Cevap hazırlanıyor... Kaynakla kontrol ediliyor..." Senin önerdiğin cümle bunun daha bilgilendirici bir hali.
- **Dikkat:** "x konusunun **y bilgisini** getiriyorum" cümlesindeki bilgiler **sorudan veya filtreden** gelmeli ("Ceket şartnamesinde dış dikiş bilgisini arıyorum"), LLM'in cevabından değil. **Değer** (sayı, tolerans) içermemeli. Yoksa doğrulanmamış bilgi yine ekrana girer.
- **Alternatif (bekleme uzun bulunursa):** Metin akarak ama **gri ve "doğrulanıyor" etiketiyle** gösterilir, doğrulama bitince normal renge döner.

**K4.** LangChain veya LlamaIndex "3 satırda RAG" sunuyor. Neden bizim projede çatısız (düz Python) öneriliyor? Hangi durumda bu karar değişebilir?
> **C:** çünkü kontrol elimizde olmamış oluyor, içinde düzenlememiz gereken kısımlar olabilir. eğer gerekmiyorsa bu kullanabilir 

🟡 Yön doğru (kontrol). Somutlaştıralım, ikinci kısım da belirsiz kalmış.

**Neden çatısız:**
1. **Zor kısımlar çatıda yok:** bbox ve sayfa metadata'sının taşınması, basılı sayfa no, eşik kontrolü, alıntı ve sayı doğrulaması, sesli metin. Bunları çatı kullansak da **kendimiz yazacağız.** "3 satırda RAG" bize sadece kolay kısmı veriyor.
2. **Çatının maliyeti gerçek:** Ek öğrenme, prompt'un ve metadata akışının gizlenmesi, sürüm değişince kırılma (LangChain v1'de eski yapılar ayrı pakete taşındı).
3. **Hattımız doğrusal:** Her soru aynı adımlardan geçiyor. Ajan yapısına (modelin kendi kendine hangi aracı kullanacağına karar vermesi) ihtiyaç yok. Öngörülebilirlik R4 için bir avantaj.
4. **Şeffaflık:** Her adımı kendimiz yazınca her adımı kendimiz loglarız (denetim izi).

**Karar ne zaman değişir?** "Gerekmiyorsa" değil, **somut bir ihtiyaç doğarsa:**
- Sistem **çok adımlı ajan davranışına** evrilirse. Örnek: "Önce makine kılavuzuna bak, bulamazsan şartnameye bak, iki sonucu karşılaştır, gerekirse kullanıcıya soru sor." Bu durumda LangGraph veya Haystack yeniden değerlendirilir.
- Bir çatının **tek bir parçası** işimizi gerçekten kolaylaştırıyorsa (ör. bir doküman okuyucu), sadece o parça kullanılabilir. Omurga bizde kalır.

**K5.** Usta mikrofona "S yetmiş üç yüz A'da E sıfır yedi hatası" diyor, STT bunu "S-7300B'de E-07 hatası" olarak yazıyor. Ne olur? Tasarımda bu riski hangi önlemlerle azaltıyoruz?
> **C:** sesli özellikle duyulan her sey bir de model tarafından seslendirerek, bu doğru mu diye soruluyor böylece yanlış duyumların önüne geciliyor 

🟡 Önlem fikri doğru (duyduğunu tekrar edip onay almak). Ama "ne olur" kısmı cevaplanmamış, önerilen tasarım da biraz farklı.

**Ne olur?** Sistem **S-7300B'nin kılavuzunda** arama yapar. İki model benzer olduğu için büyük ihtimalle bir cevap da bulur, ama **yanlış makineye ait** bir cevap. E-07 kodunun B modelinde farklı bir anlamı olabilir, ayar değerleri ve parça numaraları farklı olabilir. Usta yanlış ayarı uygular. Bu, R4'ün (yanlış değer) STT'den gelen versiyonu. Üstelik sonraki tüm doğrulamalar geçer, çünkü cevap **S-7300B kılavuzuna göre** doğrudur.

**Tasarımdaki önlemler:**
1. **Tanınan metin ekranda kutuya yazılır, kullanıcı görür ve onaylar/düzeltir** (sesli değil, **görsel** onay). Usta "S-7300B" yazısını görünce fark eder, tek dokunuşla düzeltir.
2. **Terim ipucu listesi:** Model adları ve hata kodları (ingestion'da metadata'dan çıkarılır) STT'ye verilir. Tanıma doğruluğu artar.
3. **Bas-konuş:** Sürekli dinleme yok, gürültüden yanlış tetikleme azalır.
4. **Son kontrol, kaynak ekranı:** Cevabın yanında açılan sayfada doküman adı ("Brother S-7300B") görünür.

**Senin önerdiğin sesli onay ("S-7300B dediniz, doğru mu?")** ne zaman faydalı, ne zaman değil:
- ✅ Eller tamamen meşgulken ekrana bakılamıyorsa faydalı olabilir.
- ⚠️ Ama ek gecikme getirir, cevap ("evet") yine STT'den geçer, ve "A" ile "B" harfleri **seste de** karışabilir (TTS ve gürültü). Ekrandaki yazılı metin bu ayrımı çok daha net gösterir.
- Pilotta önce görsel onayla başlamak, kullanıcılar isterse sesli onayı eklemek mantıklı.

---

## 3. Derlenmiş Notlar

### 6.1 Arayüz seçenekleri
- Kriterler: PDF + bbox + gezinme (zorunlu), çok kaynak, durum/doğrulama gösterimi, ses kontrolleri ve senkron vurgu, tablet/atölye, yetki, geliştirme hızı.
- **Pilot: Streamlit** (Faz 1'de `streamlit-pdf-viewer` ile vurgu çalışıyor, en hızlı yol). Ses için basit oynatıcı, gelişmiş özellikler özel bileşenle.
- **Üretim: Muhtemelen özel web (React + FastAPI).** Karar pilottan sonra.
- Gradio (bbox vurgusu belgelenmemiş), Chainlit (sohbet kalıbı), Open WebUI (sayfa görüntüleme yok + marka koruma lisans maddesi) **elendi.** NiceGUI Streamlit'e alternatif olarak not edildi.
- **İlke:** RAG hattı arayüzden bağımsız (`soru_cevapla()`), arayüz değişince hat değişmez.

### 6.2 Tek ekran düzeni
- Cevap solda, vurgulu kaynak sayfası sağda, **aynı anda görünür.** Dar ekranda alt alta.
- Doğrulama rozeti (✔ / ⚠ / ✖), kritik değer büyük punto, basılı + PDF sayfa no, kaynak sekmeleri, ses kontrolleri (oynat, tekrar, yavaş), ayrı tasarlanmış "bulunamadı" ekranı, büyük dokunma alanları.
- Cevap **doğrulandıktan sonra** gösterilir. Bekleme süresince adım adım durum mesajları.
- Wireframe ASCII olarak bu dosyada. Pilot arayüzü yapılınca ekran görüntüsüyle güncellenir.

### 6.3 Orkestrasyon
- Hattımız doğrusal ve deterministik, ajan gerekmiyor. Kritik adımlar (bbox, eşik, doğrulama, sesli metin) her durumda bize özel.
- **Öneri: Çatısız, modüler düz Python** (ingestion / retrieval / generation / verification / speech / pipeline). Çatı parçaları seçici olarak kullanılabilir.
- Her soru için **denetim izi** (soru, chunk'lar, skorlar, prompt, cevap, doğrulama, gösterilen sayfa).
- Ajan davranışı gerekirse LangGraph / Haystack yeniden değerlendirilir.

### 6.4 STT
- Gerekliliği kullanıcıya bağlı (Q4 açık). Mimariyi değiştirmiyor, **sonradan eklenebilir.**
- Gerekirse: **bas-konuş + tanınan metni onaylama + terim ipucu listesi.**
- Lokal: Whisper large-v3 / turbo, faster-whisper (GPU önerilir, CPU'da ölçülmeli). Bulut: Azure STT (phrase list, TTS ile aynı sağlayıcı).
- Ses kaydı kişisel veri (KVKK), Adım 7'de ele alınacak.

### Projemiz için ilk öneri

| Konu | Öneri | Alternatif | Gerekçe |
|------|-------|-----------|---------|
| **Arayüz (pilot)** | Streamlit + `streamlit-pdf-viewer` | NiceGUI | Faz 1'de çalışıyor, en hızlı |
| **Arayüz (üretim)** | Özel web (React + FastAPI), pilottan sonra karar | Streamlit'te kalmak | Senkron vurgu, tablet, yetki, SSO |
| **Ekran düzeni** | Cevap + kaynak yan yana, rozet, büyük kritik değer, doğrulandıktan sonra göster | Akan metin + "doğrulanıyor" etiketi | R4: Doğrulanmamış değer görünmesin |
| **Orkestrasyon** | Çatısız, modüler Python + denetim izi | LlamaIndex (ingestion parçaları), Haystack | Doğrusal hat, özel adımlar, şeffaflık |
| **STT** | İsteğe bağlı mikrofon: bas-konuş + onay + terim listesi. Q4'e göre | Hiç olmaması | Kod tanıma hatası R4'e yol açabilir |
| **STT motoru** | Bulut serbestse Azure STT, değilse faster-whisper (Whisper large-v3-turbo) | Whisper large-v3 (GPU) | Q1 ve Q5'e bağlı |

**Açık kalanlar:** Q4 (STT gerekli mi), Q5 (GPU), Q9 (dokümanın tamamı gösterilebilir mi), yeni Q11 (hangi cihaz: PC, tablet, kiosk? ekran nerede duracak?), Q10 (kulaklık/hoparlör).

---

## Kaynaklar

**Resmi dokümanlar**
- [Streamlit: fragments (kısmi yeniden çalıştırma)](https://docs.streamlit.io/develop/concepts/architecture/fragments) · [st.audio](https://docs.streamlit.io/develop/api-reference/media/st.audio)
- [Gradio: PDF custom component rehberi](https://www.gradio.app/guides/pdf-component-example) · [gradio-pdf (PyPI)](https://pypi.org/project/gradio-pdf)
- [Open WebUI lisansı (marka koruma maddesi)](https://docs.openwebui.com/license/)
- [LangGraph v1 geçiş rehberi (create_agent)](https://docs.langchain.com/oss/python/migrate/langgraph-v1)
- [LlamaIndex: PDF sayfa numaralı atıf örneği](https://developers.llamaindex.ai/python/examples/citation/pdf_page_reference/) · [Document/metadata kullanımı](https://developers.llamaindex.ai/python/framework/module_guides/loading/documents_and_nodes/usage_documents/)
- [Azure Custom Speech ile doğruluk artırma](https://azure.microsoft.com/en-us/blog/improve-speechtotext-accuracy-with-azure-custom-speech/) · [Azure AI Speech LLM 2607 duyurusu (phrase list iyileştirmeleri)](https://devblogs.microsoft.com/foundry/announcing-azure-ai-speech-llm-2607/)

**İkincil kaynaklar (doğrulanmalı)**
- [Open WebUI lisansının işletmeler için anlamı (wz-it)](https://wz-it.com/en/blog/open-webui-license-branding-business/) · [Is it really FOSS? Open WebUI](https://isitreallyfoss.com/projects/open-webui)
- [Streamlit vs NiceGUI (bitdoze)](https://www.bitdoze.com/md/streamlit-vs-nicegui.md) · [Streamlit vs Gradio vs Chainlit (markaicode)](https://markaicode.com/vs/streamlit-vs-gradio-vs-chainlit/)
- Streamlit ses/otomatik çalma tartışmaları: [autoplay](https://discuss.streamlit.io/t/how-to-get-autoplay-audio-in-streamlit-ui/65450), [streaming audio](https://discuss.streamlit.io/t/streaming-audio-response-from-streamlit-app/65910), [sıralı çalma](https://discuss.streamlit.io/t/autoplay-multiple-audios-in-a-streamlit-app-one-after-another/67165)
- [LangChain vs LlamaIndex vs Haystack 2026 (toolhalla)](https://toolhalla.ai/blog/langchain-vs-llamaindex-vs-haystack-2026) · [Best RAG framework 2026 (techsy)](https://techsy.io/en/blog/best-rag-framework-2026) · [index.dev karşılaştırması](https://www.index.dev/skill-vs-skill/ai-langchain-vs-llamaindex-vs-haystack)
- [LangChain 1.0 vs LangGraph 1.0 (clickittech)](https://www.clickittech.com/ai/langchain-1-0-vs-langgraph-1-0/)
- [Whisper large-v3 vs turbo karar rehberi (vexascribe)](https://vexascribe.com/whisper-large-v3-vs-turbo) · [Türkçe STT CPU/GPU ölçümü (alphaneural, rakip satıcı)](https://app.alphaneural.io/models/mihuai/turkish-stt)
- [Chainlit bakım durumu (beamforai, üçüncü taraf takipçi)](https://www.beamforai.com/tools/157/status)
