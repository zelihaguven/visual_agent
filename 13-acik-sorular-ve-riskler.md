# Açık Sorular ve Riskler (konsolide liste)

> **Kaynak:** Bu not yeni bilgi içermez; [10-sorulacaklar.md](10-sorulacaklar.md) ile 01–09 numaralı notların, [15-plan.md](15-plan.md) §11 (Q1–Q11, R1–R10) ve [16-arastirma-sentezi.md](16-arastirma-sentezi.md) §8–9'un "Açık sorular ve riskler" bölümlerinin birleştirilmiş halidir. Tekrarlar tek satıra indirildi; her satırda kaynak not belirtildi.
> **Durum (2026-10-09):** Hiçbir açık soru cevaplanmamış (Q2 kısmen: TR + EN).
> **Beslediği çıktılar:** **Açık sorular ve riskler listesi**

**Öncelik:** 🔴 Birçok kararı birden belirliyor · 🟡 Bir bileşenin tasarımını etkiliyor · ⚪ Pilotta da öğrenilebilir (öncelikler [10](10-sorulacaklar.md)'dan; orada önceliği olmayan maddeler "—")

---

## 1. Özet

- **Kilit karar Q1** (bulut mu şirket içi mi): LLM, embedding, OCR, VLM, TTS, STT seçiminin tamamını ve dağıtım senaryosunu (A/B/C) belirliyor. Hukuki dayanağı 7.1 (NDA maddeleri), uygulanabilirliği Q5 (GPU), Ağ (internet) ve Bütçe.
- **Ölçülebilirlik ön koşulu 0.4:** test soru setini (doğru cevap + sayfa) kim hazırlayacak; test seti olmadan pilot başarı kriteri ölçülemez.
- **En yüksek öncelikli risk R4** (halüsinasyon / yanlış değer) ve onun ekrandaki (akan metin), sesteki (TTS normalizasyonu) ve girişteki (STT kod tanıma) versiyonları.
- Risk listesi artık plandan tanımlı: **R1–R6** planda, **R7–R10** sentezde eklendi ([15](15-plan.md) §11, [16](16-arastirma-sentezi.md) §8).

## 2. Açık sorular (paydaşlara)

### 2.1 Yönetim / hukuk / müşteri sözleşmeleri

| # | Soru | Etkilediği karar | Öncelik | Kaynak |
|---|------|------------------|---------|--------|
| Q1 | Manueller ve alıntılı cevaplar bulut servislere gönderilebilir mi? | Tüm model/servis seçimi, dağıtım A/B/C | 🔴 | [10](10-sorulacaklar.md), [02](02-pdf-isleme.md), [04](04-llm-secimi-ve-degerlendirme.md), [06](06-veri-guvenligi-ve-erisim.md), [08](08-tts.md) |
| Q1-a | Bulut şartları: ZDR + eğitimde kullanmama yeterli mi, bölge (AB/TR), mevcut kurumsal Azure/AWS/Google hesabı; hukuk kurumsal bulutu "bulut" sayıyor mu? | Sağlayıcı ve sözleşme; tek sağlayıcıda kalma | 🔴 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md) |
| 7.1 | Müşteri manuellerinde NDA / gizlilik maddesi (8 madde: üçüncü taraf, alt yüklenici, coğrafi kısıt, saklama/imha, güvenlik standardı, ihlal bildirimi, amaç sınırlaması, yapay zekâ maddesi) | Q1'in hukuki dayanağı | 🔴 | [10](10-sorulacaklar.md), [06](06-veri-guvenligi-ve-erisim.md) |
| Müşteri izni | Sözleşme sessizse müşteriden yazılı izin alınabilir mi? | Hibrit (B) mümkün mü | 🟡 | [10](10-sorulacaklar.md), [06](06-veri-guvenligi-ve-erisim.md) |
| Silme | Sözleşme bitince doküman ve türevleri (chunk, vektör, sayfa resmi, log alıntıları) silinmeli mi? | `doc_id` bazlı silme tasarımı | ⚪ | [10](10-sorulacaklar.md), [06](06-veri-guvenligi-ve-erisim.md) |
| Loglar | Soru/kimlik logları ne kadar saklanır, kim görür, aydınlatma metni gerekir mi? | Denetim izi, KVKK | 🟡 | [10](10-sorulacaklar.md), [06](06-veri-guvenligi-ve-erisim.md) |
| Q9 | Kullanıcı sadece ilgili sayfayı mı görmeli, dokümanın tamamında gezinip indirebilmeli mi? | Sayfa görüntüleme yöntemi (PDF.js vs render), gizlilik | 🟡 | [10](10-sorulacaklar.md), [03](03-kaynak-gosterme.md), [05](05-arayuz-ve-orkestrasyon.md) |
| 7.3 | Marka bazlı yetki gerekli mi? | Retrieval filtresi, giriş, koleksiyon yapısı, `allowed_groups` | 🟡 | [10](10-sorulacaklar.md), [02](02-pdf-isleme.md), [06](06-veri-guvenligi-ve-erisim.md) |
| KVKK (ses) | STT eklenirse ses kaydı işlenebilir mi, saklanır mı? | STT kararı | ⚪ | [10](10-sorulacaklar.md), [05](05-arayuz-ve-orkestrasyon.md) |
| Bütçe | Aylık bulut API bütçesi / GPU yatırımı sınırı | Bulut vs lokal, LLM seçimi | 🟡 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md) |
| Veri sorumlusu | Veri sorumlusunun kim olduğu | KVKK süreçleri | — | [06](06-veri-guvenligi-ve-erisim.md) (kaynakta tanımlanmamış) |

### 2.2 BT / altyapı

| # | Soru | Etkilediği karar | Öncelik | Kaynak |
|---|------|------------------|---------|--------|
| Q5 | Kullanılabilir GPU var mı (model, VRAM)? Alınabilir mi? | Lokal LLM (~24 GB), OCR/VLM, Chatterbox, Whisper | 🔴 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md), [08](08-tts.md) |
| Ağ | Atölyede internet / Wi-Fi var mı, cihazlar şirket ağında mı? | Bulut servisler mümkün mü | 🔴 | [10](10-sorulacaklar.md), [06](06-veri-guvenligi-ve-erisim.md) |
| Giriş | Kurumsal hesap / SSO var mı? | Giriş, marka yetkisi, arayüz teknolojisi | 🟡 | [10](10-sorulacaklar.md), [06](06-veri-guvenligi-ve-erisim.md) |
| Sunucu | Sistem şirket içi mi bulut sunucuda mı çalışacak? | Kurulum, bakım | 🟡 | [10](10-sorulacaklar.md) |

### 2.3 Doküman sahipleri / kalite ekibi

| # | Soru | Etkilediği karar | Öncelik | Kaynak |
|---|------|------------------|---------|--------|
| Q2 | Gerçek manuellerin ve soruların dili? (kısmen cevaplı: TR + EN) | Embedding, LLM, TTS | 🟡 | [10](10-sorulacaklar.md), [08](08-tts.md) |
| Q8 | Hangi doküman türleri kapsanacak? | `doc_type`, sorgu yönlendirme | 🟡 | [10](10-sorulacaklar.md), [07](07-rag-temelleri.md) |
| Q3 | Taranmış PDF oranı ve görsel türleri (örnek sayfalarla) | OCR ihtiyacı, görsel anlama (A+B / C+B) | 🟡 | [10](10-sorulacaklar.md), [01](01-manual-envanteri.md), [02](02-pdf-isleme.md), [03](03-kaynak-gosterme.md) |
| Q7 | Manueller nerede, adlandırma düzeni, marka/versiyon/yürürlük tarihi nerede yazıyor? | Metadata'nın otomatik çıkarımı | 🟡 | [10](10-sorulacaklar.md), [02](02-pdf-isleme.md) |
| R3 | Aynı dokümanın birden fazla versiyonu var mı, geçerli olan nasıl biliniyor? | Versiyon filtresi, çelişki riski | 🟡 | [10](10-sorulacaklar.md) |
| Biçimler | Değerler gerçek şartnamelerde hangi biçimde yazılıyor (tolerans, birim, kesir, kod)? | TTS normalizasyonu, sayı doğrulaması | ⚪ | [10](10-sorulacaklar.md), [08](08-tts.md) |
| 0.4 | Test soru setini (10–20 soru, doğru cevap + sayfa) kim hazırlar? | Değerlendirme, pilot başarı kriterleri | 🔴 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md) |

### 2.4 Kullanıcılar

| # | Soru | Etkilediği karar | Öncelik | Kaynak |
|---|------|------------------|---------|--------|
| Q11 | Hangi cihaz (PC, tablet, kiosk), ekran nerede, kaç kişi aynı anda? | Ekran düzeni, arayüz teknolojisi | 🟡 | [10](10-sorulacaklar.md), [05](05-arayuz-ve-orkestrasyon.md) |
| Q4 | Sesli soru isteniyor mu? | STT gerekli mi | ⚪ | [10](10-sorulacaklar.md), [05](05-arayuz-ve-orkestrasyon.md) |
| Q10-a | Kodlar atölyede nasıl söyleniyor (301, S-7300A, LSc-2, E-07)? | Normalizasyon kuralları | ⚪ | [10](10-sorulacaklar.md), [08](08-tts.md) |
| Q10-b | İngilizce terim mi Türkçe karşılık mı (SPI, lockstitch, overedge)? | Sesli metin ve ekran dili | ⚪ | [10](10-sorulacaklar.md), [08](08-tts.md) |
| Q10-c | Hoparlör mü kulaklık mı? | Donanım, ses seviyesi | ⚪ | [10](10-sorulacaklar.md), [05](05-arayuz-ve-orkestrasyon.md), [08](08-tts.md) |
| Okuma | Otomatik mi butonla mı okuma, sesli cevap uzunluğu | TTS ve arayüz | ⚪ | [10](10-sorulacaklar.md), [08](08-tts.md) |
| Marka | Soruda marka yoksa sistem sorsun mu, seçim kutusu mu? | Metadata filtresi | ⚪ | [10](10-sorulacaklar.md), [07](07-rag-temelleri.md) |
| Süre | Kabul edilebilir bekleme süresi (3 sn? 10 sn?) | Pilot başarı kriteri, doğrulamadan sonra gösterme | 🟡 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md), [05](05-arayuz-ve-orkestrasyon.md) |

### 2.5 Kalite yönetimi

| # | Soru | Etkilediği karar | Öncelik | Kaynak |
|---|------|------------------|---------|--------|
| Hata toleransı | Kabul edilebilir yanlış değer oranı mı, sıfır tolerans mı (daha sık "bulunamadı" kabul mü)? | Eşik, pilot başarı kriterleri | 🔴 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md) |
| Genel bilgi | Manuelde olmayan genel sektör bilgisi verilebilir mi (etiketle)? | Prompt kuralı 1, R4 | 🟡 | [10](10-sorulacaklar.md), [09](09-prompt-taslagi.md) |
| Sorumluluk | Son onay kimde, kritik değerlerde kullanıcı onayı zorunlu mu? | Arayüzde onay adımı, denetim izi | 🟡 | [10](10-sorulacaklar.md) |
| Çeviri | Orijinal İngilizce alıntı da gösterilsin mi (önerilen)? | Çeviri hatası önlemi | ⚪ | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md) |
| İnsan değerlendirmesi | "Bu cevapla dikim yapar mıydım?" puanlaması için kalite uzmanı ayrılabilir mi? | Değerlendirme | 🟡 | [10](10-sorulacaklar.md), [04](04-llm-secimi-ve-degerlendirme.md) |

### 2.6 Teknik açık sorular (deneyle cevaplanacak)

| # | Soru | Kaynak |
|---|------|--------|
| Q6 | Diller arası aramada BM25 için soru doküman diline çevrilmeli mi (*query translation*)? (hybrid search kalitesi) | [07](07-rag-temelleri.md), [15](15-plan.md) §11 |
| — | `bge-m3` TR soru ↔ EN manuel yeterli mi; hybrid farkı; sparse: BM25 / BGE-M3 sparse / ikisi; TR kök bulucu (Zemberek / Snowball / prefix-5); reranker gecikmesi | [07](07-rag-temelleri.md) §11 |
| — | Docling ceket dikiş tablosu; taranmış pantolon şartnamesinde OCR sayıları ("10-14", "52-56"); lokal vs bulut OCR farkı; Strickland/Brother çizimlerinde VLM açıklaması | [02](02-pdf-isleme.md) §9 |
| — | A+B vs C+B (Recall@5, cevap doğruluğu, maliyet, gecikme) | [03](03-kaynak-gosterme.md) §7.2 |
| — | TR vs EN sistem talimatı; alıntı birebirlik oranı; "bulunamadı" aşırı tetiklenmesi; sesli metin kurallarına uyum; görsel sorularda talimat değişikliği; netleştirme sorusunun sıklığı | [09](09-prompt-taslagi.md) §5 |
| — | Chatterbox Türkçe kalitesi; Azure container'da Türkçe ses; fiyat/lisansların resmi sayfalardan doğrulanması; `num2words` Türkçe | [08](08-tts.md) |
| — | Streamlit: PDF.js kaydırma/yakınlaştırma rerun tetikliyor mu; `streamlit-pdf-viewer`'ın fabrika tabletlerinde performansı | [05](05-arayuz-ve-orkestrasyon.md), [03](03-kaynak-gosterme.md) |
| — | Doğrulanmamış bilgiler: `st.audio_input` sürümü, NiceGUI ekosistemi, React PDF bileşenleri, Haystack citation desteği, Langfuse, Whisper turbo CPU ölçümü; vektörlerden içerik geri çıkarılabilirliği | [05](05-arayuz-ve-orkestrasyon.md), [06](06-veri-guvenligi-ve-erisim.md) |

## 3. Numaralı riskler (R1–R10)

Tanımlar [plan](15-plan.md) §11 (R1–R10) ve [sentez](16-arastirma-sentezi.md) §8'den (önlem ve durum sütunları sentezden).

| Kod | Risk | Etki | Önlem | Durum | İlgili notlar |
|-----|------|------|-------|-------|---------------|
| **R4** | **🔴 Yanlış veya uydurulmuş (halüsinasyon) değer → yanlış dikim** | Yanlış üretim, müşteri kaybı | Altı katmanlı doğruluk güvencesi, iki yönlü sayı-tolerans kontrolü, kaynak sayfanın gösterilmesi | **En yüksek öncelik** | [07](07-rag-temelleri.md) §9, [04](04-llm-secimi-ve-degerlendirme.md) §5, [09](09-prompt-taslagi.md) |
| R1 | Tablo ve şekil/çizim ağırlıklı sayfalarda metin tabanlı RAG zayıf kalabilir | Eksik/yanlış cevap | Şekil açıklaması (VLM), tablo satırı düzeyinde parçalama, gerekirse görsel tabanlı arama | Pilotta ölçülecek | [03](03-kaynak-gosterme.md) §7, [02](02-pdf-isleme.md) |
| R2 | Türkçe sesli okumada teknik terim, sayı ve birimlerin yanlış okunması | Yanlış değer duyulması (R4 ile bağlantılı) | Ayrı kısa sesli metin, sayı kontrolü, kural tabanlı normalizasyon, uzun kodlar okunmaz → ekrana | Kural tablosu taslak | [08](08-tts.md) §7 |
| R3 | Aynı konunun farklı doküman versiyonlarında çelişen bilgi | Yanlış cevap | Versiyon metadata'sı (`is_latest`), çelişkinin cevapta bildirilmesi (`celiski_var`) | Gerçek veride versiyon düzeni sorulacak | [04](04-llm-secimi-ve-degerlendirme.md), [09](09-prompt-taslagi.md), [10](10-sorulacaklar.md) |
| R5 | LLM → TTS cümle cümle seslendirme / akan metin, S11 Katman 5 ("cevap gitmeden doğrulama") ile çatışıyor: doğrulanmamış değer iletilebilir | Yanlış değer, R4 | Doğrulamadan sonra gösterim ve seslendirme (streaming seçeneği A) | Tasarımda çözüldü | [08](08-tts.md) §5, [05](05-arayuz-ve-orkestrasyon.md) |
| R6 | Türkçe + ticari lisanslı + kaliteli kurum içi TTS çok az (şu an yalnız Chatterbox Multilingual); Q1 "bulut yok" çıkarsa seçenek daralır | Bulut yoksa sesli okuma kalitesi | Chatterbox denenecek (pilot), Azure container yolu araştırılacak | Pilotta ölçülecek | [08](08-tts.md) |
| R7 | OCR'ın bir satırı sessizce kaybetmesi (Faz 1 denemesinde görüldü) | Bilgi aranamaz hale gelir | Bozuk OCR uyarısı, iki OCR kaynağının birleştirilmesi, her zaman orijinal sayfa görüntüsü | Uygulamaya devredildi (plan Faz 6.2) | [02](02-pdf-isleme.md), [15](15-plan.md) §10 |
| R8 | Yetki filtresinin bir erişim noktasında (PDF, önbellek, loglar) unutulması | Gizli bilginin yetkisiz kişiye gösterilmesi | Merkezi zorunlu filtre, tüm erişim noktalarının kontrolü, test setinde yetki testleri | Tasarımda tanımlandı | [06](06-veri-guvenligi-ve-erisim.md) §6 |
| R9 | Sesli soruda model kodunun yanlış tanınması (S-7300A → S-7300B) | Yanlış makinenin kılavuzundan cevap | Tanınan metnin kullanıcı onayı, terim listesi | STT kararına bağlı | [05](05-arayuz-ve-orkestrasyon.md) §7 |
| R10 | Test setinin gerçek dokümanları temsil etmemesi | Pilot sonuçları gerçek veriye taşınmaz | Gerçek veriye geçişte test setinin yeniden kurulması ve yeniden ölçüm | Planlandı | [01](01-manual-envanteri.md) |

## 4. Diğer riskler (konu bazında)

### 4.1 Veri / test seti
- Türkçe doküman yok → TR doküman parsing'i test edilmemiş olacak; diller arası test TR soru + EN doküman ile ([01](01-manual-envanteri.md)).
- Aynı dokümanın iki versiyonu yok → versiyon filtresi test edilemiyor ([01](01-manual-envanteri.md)).
- Temsil riski: şartnamelerin hepsi ABD ordusu formatında; gerçek veriye geçişte tekrar ölçüm şart ([01](01-manual-envanteri.md)).
- Brother parça kitabı (M3) formatı kontrol edilmedi ([01](01-manual-envanteri.md), [10](10-sorulacaklar.md)).

### 4.2 Parsing / ingestion
- Sessiz hatalar (taranmış sayfada boş metin, bozuk sayı, düşen tolerans); OCR/sayı hataları sıfıra inmez → `ocr_confidence`, iki OCR karşılaştırması, kritik tablolarda insan kontrolü, orijinal sayfa gösterimi ([02](02-pdf-isleme.md)).
- VLM uydurma riski (tablo değeri, şekil açıklaması); VLM açıklamalarının eksik/yanlış olması ([02](02-pdf-isleme.md), [03](03-kaynak-gosterme.md)).
- Docling sayfa aşan tabloyu birleştirmiyor; paragraf/tablo birleştirme kuralları yanlış birleştirme yapabilir ([02](02-pdf-isleme.md), [03](03-kaynak-gosterme.md)).
- Metadata çıkarım hatası (`brand`, `is_latest`) filtrelemeyi bozar; `brand` / `manufacturer` karışması ([02](02-pdf-isleme.md), [07](07-rag-temelleri.md)).
- Koordinat sistemi uyumsuzluğu (DPI, orijin, sayfa indeksi, rotasyon/kırpma) ([02](02-pdf-isleme.md), [03](03-kaynak-gosterme.md)).
- Faz 1'den devredilenler: OCR satır kaybı, tablo satırı temizliği, basılı ↔ PDF sayfa eşleme, vurgunun gözle kontrolü ([10](10-sorulacaklar.md)).

### 4.3 Retrieval
- Embedding modeli veya metadata alanı değişirse tüm dokümanların yeniden indekslenmesi ([07](07-rag-temelleri.md)).
- Diller arası benzerlik skorunun düşük çıkması (eşik ayarı), BM25'in diller arası çalışmaması, terim çeviri hataları ([07](07-rag-temelleri.md)).
- Embedding'in kod/sayı ve olumsuzlukta zayıflığı; doküman türleri arası karışma; post-filter ile doğru chunk kaybı ([07](07-rag-temelleri.md)).

### 4.4 LLM / cevap kalitesi
- Lokal 7–8B modellerin yetersiz doğruluğu (bir TR doküman QA çalışmasında %49–75) ([04](04-llm-secimi-ve-degerlendirme.md)).
- LLM'in yanlış [n] vermesi → doğrulama şart ([03](03-kaynak-gosterme.md)).
- Çeviri kaynaklı anlam kayması (shall / not to exceed) ([04](04-llm-secimi-ve-degerlendirme.md), [09](09-prompt-taslagi.md)).
- LLM hakemin Türkçe güvenilirliği; yüksek faithfulness'ın yanlış kaynağı gizleyebilmesi ([04](04-llm-secimi-ve-degerlendirme.md)).
- Cümle vurgusunun alıntı birebir değilse veya OCR'lı sayfada çalışmaması ([03](03-kaynak-gosterme.md)).

### 4.5 Ses (TTS / STT)
- TTS halüsinasyonu (kelime atlama, tekrar, uydurma) yeni nesil uçtan uca modellerde ([08](08-tts.md)).
- Normalizasyon hataları: tolerans, aralık ("10-14" → negatif sayı), kesir (tarih gibi), ondalık ayırıcı, kod ve parça no ([08](08-tts.md)).
- STT'nin model/hata kodunu yanlış tanıması → yanlış makine kılavuzu; doğrulamalar yakalamaz ([05](05-arayuz-ve-orkestrasyon.md)).
- Streamlit rerun modelinin karmaşık etkileşimlerde (senkron vurgu, mikrofon) zorlaşması ([05](05-arayuz-ve-orkestrasyon.md)).

### 4.6 Güvenlik / gizlilik
- Ingestion'da bulut kullanımı → dokümanların tamamı dışarı ([06](06-veri-guvenligi-ve-erisim.md)).
- Yetki filtresinin unutulması (tek koleksiyonda) → markalar arası sızıntı (LLM08); yan kapılar (PDF URL, önbellek, geçmiş, ses dosyaları, loglar, statik sayfa resimleri) ([06](06-veri-guvenligi-ve-erisim.md)).
- Yetki kararını prompt'a bırakmak; prompt injection ([06](06-veri-guvenligi-ve-erisim.md), [09](09-prompt-taslagi.md) kural 10).
- Tam doküman gösterimi (Q9) → gizli manuellerde ve marka yetkisinde sorun ([03](03-kaynak-gosterme.md)).
- ZDR'nin kısmi kapsamı (durum tutan özellikler, bazı modellerde yok) ([04](04-llm-secimi-ve-degerlendirme.md), [06](06-veri-guvenligi-ve-erisim.md)).
- Türkiye'de kalma şartı çıkarsa bulut LLM pratikte imkânsız → C senaryosu ve 24 GB+ GPU ([06](06-veri-guvenligi-ve-erisim.md)).
- KVKK yurt dışı aktarım bildirim yükümlülüğü (idari para cezası); ses kaydı ve loglar kişisel veri ([06](06-veri-guvenligi-ve-erisim.md), [05](05-arayuz-ve-orkestrasyon.md)).
- TTS ikinci bulut sağlayıcısı = ikinci sözleşme; ses klonlamada KVKK (ses biyometrik veri sayılabilir) ([08](08-tts.md)).

### 4.7 Lisans / maliyet
- PyMuPDF AGPL; Marker ağırlıkları ayrı lisans; MinerU özel lisans ([02](02-pdf-isleme.md)).
- LLM lisans belirsizlikleri (Gemma, Qwen amiral, Mistral, Llama) ([04](04-llm-secimi-ve-degerlendirme.md)).
- TTS: NC lisansların fine-tune'lara geçmesi (XTTS-v2 CPML, F5-TTS, MMS-TTS, Piper dfki) → sadece test; Piper motoru GPL-3.0 ([08](08-tts.md)).
- Fiyat değişimi (ör. gemini-3.8-flash 1 Ocak 2027'de iki katı); TTS/Polly fiyatları doğrulanmalı ([04](04-llm-secimi-ve-degerlendirme.md), [08](08-tts.md)).
- ColPali depolama ve GPU maliyeti ([03](03-kaynak-gosterme.md)).

## 5. Kaynaklardaki tutarsızlıklar

**Plan ile çözülenler:**
- **"tts.md R5" atfı:** R5 bir plan riski ("LLM → TTS cümle cümle seslendirme ↔ S11 Katman 5"); tts.md'de etiket olarak geçmiyor ama tanım planda var ([15](15-plan.md) §11).
- **Basılı ↔ PDF sayfa numarası:** Faz 1'de **gösterim** çalışıyor ("s.90 (PDF s.101)"); devredilen iş, kılavuz içi atıflar ("Page 67") için **basılı → fiziksel sayfa eşleme tablosu** ve özel düzenler (Mr. Coffee kitapçık: bir PDF sayfasında iki basılı sayfa; Strickland: numara üstte) ([15](15-plan.md) §5, §10). İkisi çelişmiyor.
- **"Faz" numaraları:** Faz 1–6 **araştırma** içi çalışma sırası; Faz 6 = uygulama planı + pilot (6.1 pilot tanımı, 6.2 task listesi, 6.3 başarı kriterleri). Önceki sürümde "Faz 6 = gerçek veriye geçiş" varsayımı düzeltildi.

**Hâlâ çözülmemiş:**
- **Doküman sayısı:** [01](01-manual-envanteri.md) başlığı 5, envanter tablosu 7 (hepsi "✅ İndirildi"), plan günlüğü "toplam 8 doküman" diyor. 8. dokümanın hangisi olduğu (ör. ⏳ M3 Parts Book) belirtilmemiş.
- **Ceket SPI örneğinin sayfası:** [03](03-kaynak-gosterme.md) ve [07](07-rag-temelleri.md) örneklerinde s. 12(–13), [04](04-llm-secimi-ve-degerlendirme.md) test setinde s. 22–23, [05](05-arayuz-ve-orkestrasyon.md) wireframe'inde s. 22 (03/07'dekiler açıklayıcı örnek olabilir; parse ile teyit edilmeli).
- **Pilot başarı kriteri:** plan Faz 6.3 örneği "doğru sayfa **ilk 3'te %80+**", taslak hedefler ([04](04-llm-secimi-ve-degerlendirme.md), [16](16-arastirma-sentezi.md)) "**Recall@5 ≥ %90**"; 6.3 hâlâ açık, kesin hedefler paydaşlarla.
- **Plan Adım 3 kutucukları** işaretsiz, oysa [03](03-kaynak-gosterme.md) notu tamamlanmış öneriler içeriyor.
- **Pilot kapsamı:** görev tanımı "birkaç manuel", plan/sentez "**3–5 manuel**" (çelişki değil, plan daraltıyor).
