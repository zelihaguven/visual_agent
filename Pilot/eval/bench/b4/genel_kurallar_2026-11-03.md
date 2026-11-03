# Etiket düzeltmesi ve genel kural önerileri (2026-11-03)

İlke (2026-11-03): pipeline'a dokümana özgü, elle yapılan hiçbir düzeltme girmez; her kural hiç görülmemiş bir dokümanda otomatik çalışmalı. Soru setindeki etiket düzeltmeleri bunun dışında (değerlendirme verisi). Bu rapordaki 1. bölüm uygulandı; 2–5 yalnız öneri, uygulanmadı. Bulut çağrısı yapılmadı.

## 1. Etiket: dil kopyaları `kabul`a eklendi (uygulandı)

Kural: beklenen parçanın aynı dokümandaki **birebir çevirisi** kabul edilen kaynaklara eklenir (`"dil_kopyasi": true` işaretiyle). Adaylar bge-m3 vektör benzerliği ve anahtar kelimeyle (ölçüler, model numaraları, kod) bulundu; her çift metin olarak karşılaştırıldı. `dogrulandi` alanları değişmedi. Tutarlılık için üç dilli iki kılavuzdan (Bosch RA1171: en/fr/es, Mr. Coffee: en/es) beklenen parçası olan 18 aday sorunun hepsine bakıldı; 16'sına toplam 26 kaynak eklendi.

| Soru | Beklenen (İngilizce) | Eklenen birebir çeviriler | Not |
|---|---|---|---|
| A098 | mrcoffee-2003-00054 s. 9 | mrcoffee-2003-00094 (es, s. 15) | |
| A099 | mrcoffee-2003-00055 s. 10 | mrcoffee-2003-00073 (es, s. 12) | |
| A100 | mrcoffee-2003-00071 s. 12 | mrcoffee-2003-00075 (es, s. 13) | 00090 ("1 taza = 5 onzas", ölçü tablosu) aynı bilgiyi veriyor ama bu paragrafın çevirisi değil: eklenmedi |
| A101 | mrcoffee-2003-00100 s. 16 | mrcoffee-2003-00048 (es, s. 8) | parça sınırı farklı (son cümle sonraki parçada); bilgi tam |
| A102 | mrcoffee-2003-00113 s. 18 | mrcoffee-2003-00037 (es, s. 6–7) | çeviride devam cümleleri de var |
| A105 | mrcoffee-2003-00139 s. 21 | mrcoffee-2003-00012 (es, s. 3) | |
| A106 | bosch-ra1171-00009 s. 2 | bosch-ra1171-00196 (fr, s. 32), bosch-ra1171-00400 (es, s. 63) | çevirilerde bir önceki madde de var |
| A107 | bosch-ra1171-00144 s. 19 | bosch-ra1171-00340 (fr, s. 49), bosch-ra1171-00543 (es, s. 81) | |
| A108 | bosch-ra1171-00121 s. 14 | bosch-ra1171-00314 (fr, s. 44), bosch-ra1171-00518 (es, s. 76) | |
| A109 | bosch-ra1171-00124 s. 15 | bosch-ra1171-00318 (fr, s. 45), bosch-ra1171-00521 (es, s. 77) | |
| A110 | bosch-ra1171-00170 s. 25 | bosch-ra1171-00369 (fr, s. 55), bosch-ra1171-00569 (es, s. 87) | parça sınırı farklı; cevap (≈1/4″) ikisinde de |
| A111 | bosch-ra1171-00187 s. 31 | bosch-ra1171-00390 (fr, s. 61), bosch-ra1171-00591 (es, s. 93) | |
| A112 | bosch-ra1171-00155 s. 21 | bosch-ra1171-00352 (fr, s. 51), bosch-ra1171-00554 (es, s. 83) | |
| A113 | bosch-ra1171-00097 s. 8 | bosch-ra1171-00287 (fr, s. 38), bosch-ra1171-00492 (es, s. 70) | parça listesi satırı |
| A150 | mrcoffee-2003-00100, -00107 | mrcoffee-2003-00048 (es, s. 8), mrcoffee-2003-00039 (es, s. 7) | |
| A151 | bosch-ra1171-00155 s. 21 | bosch-ra1171-00352 (fr, s. 51), bosch-ra1171-00554 (es, s. 83) | A112 ile aynı parça |

Eklenmeyenler: **A103** (sorun giderme tablosu İspanyolcada farklı satırlara bölünmüş; birebir karşılığı olan tek parça yok), **A104** (etiket zaten iki dili de kabul ediyordu). Bilinen setlerdeki Q06, Q32 (alan dışı, doküman düzeyi) ve G6, G7 (şekil sayfası) parça düzeyinde etiketli olmadığı için bu kurala girmedi.

**Etkisi** (kayıtlı aday listeleri ve reranker skorlarından yeniden hesap; 10k, 160 cevaplı soru, geçici, onaysız set):

| hit@1 / hit@5 | A rerank'sız | C rerank'sız | Üçlü rerank'sız | A + reranker | C + reranker |
|---|---|---|---|---|---|
| Filtreli, önce | 0,69 / 0,84 | 0,62 / 0,82 | 0,75 / 0,89 | 0,72 / 0,89 | 0,70 / 0,86 |
| **Filtreli, sonra** | 0,74 / 0,87 | 0,67 / 0,84 | **0,80 / 0,94** | **0,79 / 0,93** | 0,76 / 0,88 |
| Prosedür (20), filtreli, sonra | 0,80 / 0,90 | 0,80 / 0,90 | 0,85 / 1,00 | 0,85 / 0,90 | 0,85 / 0,95 |
| Filtresiz, sonra | 0,74 / 0,86 | 0,68 / 0,81 | 0,79 / 0,93 | 0,76 / 0,89 | 0,73 / 0,87 |

A'nın reranker sonrası filtreli kaçırdığı soru 18 → 12 (A100, A102, A108, A111, A112, A151). Not: eşleşme doküman + sayfa düzeyinde; A151'de ilk 5'e giren, kilitleme adımının Fransızca çevirisiyle aynı sayfadaki (s. 51) şalter parçaları, çevirinin kendisi değil. Önceki "prosedür zayıf" bulgusunun büyük kısmı etiketten geliyordu.

**Dikkat:** `bench/aday_sorular.py` `eval/aday_sorular.json`'u kendi içindeki taslaktan yeniden yazar; çalıştırılırsa bu eklemeler kaybolur. `aday_sorular.md` ve inceleme tablosu güncel JSON'dan yeniden üretildi (betik çalıştırılmadı).

## 2. Dil: parça bazında otomatik tespit (öneri)

**Sorun:** Parçanın dili kayıttaki elle girilmiş alandan geliyor (`default_lang`, `lang_ranges`); Mr. Coffee'de aralık girilmediği için İspanyolca bölüm `en` işaretli. Kaba tahmin (yaygın sözcük sayımı, yalnız tahmin için; önerilen yöntem değil): Mr. Coffee'de 164 parçanın **64'ü İspanyolca ama `en`**; Bosch'ta kayıt aralıkları büyük ölçüde doğru (10 uyumsuzluğun çoğu bu kaba yöntemin içindekiler sayfalarında ve fr/es ortak sözcüklerde yanılması). Kısa parçalarda (tablo satırları) dil bu yöntemle belirlenemiyor: 4.232 parçanın 1.148'i.

**Önerilen adım (indeksleme sırasında, bulut yok):**
1. Her metin parçası için dil tespiti (sayılar, kodlar ve birimler atılarak). Güven eşiği altında ya da kısa (ör. < 40 harf) parçalar için: aynı sayfadaki güvenli parçaların çoğunluk dili; o da yoksa dokümanın çoğunluk dili.
2. Kayıttaki dil alanı yalnız yöneticinin beyanı olarak kalır: tespitle çeliştiği sayfalar kapsam raporunda (G13) gösterilir, yönetici onaylar ya da düzeltir. Elle aralık girmek gerekmez.
3. Soru dili zaten tespit ediliyor (`query.question_lang`); dil kopyalarında kullanıcının diline ya da tercih edilen dile yakın kopyayı öne almak sonraki adım.

**Kütüphane seçenekleri:**

| | Lisans | Boyut / bellek | Hız | Kısa metin | Not |
|---|---|---|---|---|---|
| **lingua** (lingua-language-detector) | Apache-2.0 | dil kümesi kısıtlanabilir (ör. 10 dil); tüm diller yüksek doğrulukta ~1 GB'a kadar çıkabilir, ölçülmeli | parça başına ms düzeyi | en iyisi | önerim: dil kümesi yapılandırmadan (dokümana değil kuruluma özgü) |
| fastText lid.176.ftz | model CC BY-SA 3.0 | ~1 MB model | µs düzeyi | orta | en hızlı; atıf gerekli |
| py3langid / langid.py | BSD | küçük | hızlı | orta | |
| langdetect | Apache-2.0 | küçük | yavaş | zayıf | sabit tohum gerekir (rastgele) |

**Maliyet:** bulut yok; 4.232 parça için saniyeler (lingua'da onlarca saniye). Sanal ortamda şu an hiçbiri kurulu değil.

**Yan etki:** `chunk.py` dil değişiminde parçayı kapatıyor (`lang_of(page)`). Tespit edilen dil bu kurala girerse Mr. Coffee'nin parça sınırları ve kimlikleri değişir: o doküman yeniden parçalanıp yeniden gömülmeli (~164 parça). İki seçenek: (a) sınır kuralı tespit edilen sayfa diline geçer (doğru olan), (b) sınır kuralı aynı kalır, yalnız `lang` alanı tespitten gelir (kimlikler korunur). Önerim (a), ama bir kez kimlik değişikliği demek.

## 3. `registry.py`: elle girilmiş alanlar (rapor)

(a) gerçek üründe yükleme sırasında yöneticinin girebileceği bilgi mi · (b) otomatik çıkarılmalı mı · (c) pipeline'da şu an nerede kullanılıyor.

| Alan | (a) | (b) | (c) Kullanım |
|---|---|---|---|
| `doc_id` | hayır | evet (sistem kimliği) | parça kimliği, filtre, her yer |
| `file` / `path` | hayır | evet (yüklenen dosya) | ayrıştırma (`parse.py`), sayfa etiketi ve yer imi (`chunk.py`), şekil (`figures.py`), sayfa görseli (`app.py`) |
| `brand` | evet (üretici/marka) | öneri olarak PDF metninden/kapaktan | `embed_text` başı (`chunk._embed_text`), payload + Qdrant marka filtresi (`index.PAYLOAD_INDEXES`, `retrieve._filter`), pipeline marka kapsamı, LLM kaynak etiketi, arayüz |
| `product` | evet (ürün/model adı) | öneri olarak | `embed_text` başı, LLM kaynak etiketi, netleştirme seçeneklerinin adları, arayüz |
| `doc_type` | evet (kapalı liste: şartname, makine kılavuzu, terzilik/onarım kitabı) | öneri olarak sınıflandırılabilir | netleştirme mantığı (`pipeline.py` 144, 168, 181, 218; `query.MUST_MATCH`), VLM şekil istemi, LLM istemi |
| `default_lang`, `lang_ranges` | yönetici beyanı olabilir | **evet** (§2) | parçanın `lang` alanı, dil değişiminde parça sınırı (`chunk.py`), LLM istemindeki `dil=` |
| `aliases` | kısmen (yönetici kısaltma ve takma ad girer) | kısmen: model numaraları ve doküman başlığından çıkarılabilir; Türkçe eş anlamlılar departman verisi | sorudan doküman kapsamı (`query.py` 164), kaynak ifadesini aramadan çıkarma, model adının kod sanılmaması (`pipeline.py` 122) |
| `access` | evet (yetki) | hayır | payload + Qdrant yetki filtresi (`index.with_access`, `retrieve._filter`), `registry.visible` |
| `BRAND_ALIASES` | hayır | **evet**: aynı `brand` değerli dokümanların gruplanmasıyla | `query.py` (yalnız marka geçen soruda bütün modeller), `app.py` |
| `CUSTOMER_BRANDS` | evet (müşteri kaydı) | hayır | `query.py` (yalnız müşteri markası geçen soru) |

İlkeye aykırı görünenler: `gl-pd-14-04a` takma adlarındaki "coat", "jacket" yorumda bir test sorusu (Q16) için eklendiği yazıyor; `BRAND_ALIASES` elle tutulan bir tablo. Kayıt dışında aynı türden elle tablolar: `query.FOREIGN_BRANDS`, `query.MUST_MATCH`, `terms.GLOSSARY` (sözlük, departmana özgü isteğe bağlı veri olarak tasarlanmıştı).

## 4. Kod normalleştirme: "e50" → "E050" (öneri)

**Sorun:** `pipeline.code_lookup` sorudaki kodu birebir arıyor (harf–rakam arası tire/boşluk farkı zaten yok sayılıyor). "e50", korpustaki "E050" ile eşleşmiyor; kod "kapsamda yok" sayılabilir ve BM25 de eşleşmez (A146).

**Genel kural:** kod = 1–3 harf + isteğe bağlı ayırıcı + 2–5 rakam (mevcut `CODE_TOKEN_RE`). Karşılaştırma anahtarı **(harfler büyük harfle, rakamların sayısal değeri)**: baştaki sıfırlar yok sayılır, değer farklıysa kod farklıdır.
- İndekslemede her doküman için korpustaki kodlardan otomatik bir tablo: anahtar → korpustaki yazım(lar). Dokümana özgü eşleme yok.
- Sorguda kod birebir yoksa anahtarla aranır; kapsamda **tek** yazıma düşüyorsa sorudaki kod o yazımla değiştirilir (`code_lookup`, BM25 ve dense aynı metni görür). Birden çok yazıma düşerse hepsi aranır; hiçbirine düşmezse bugünkü "kapsamda yok" yolu.

**Mevcut korpusta etkisi:** 754 farklı kod; **72'si baştaki sıfırla yazılmış** (Brother E050, E051 …; JUKI E01, E02 …; Granovsky'deki OCR artıkları dahil) ve sıfırsız yazılan soruyla artık bulunur. Aynı doküman içinde aynı anahtara düşen farklı yazım: **1** (Brother `TO099` / `TO99`, aynı kodun iki yazımı). Değerler farklı kaldığı için J9 ayrımı korunur: JUKI `E05` (5) ile Brother `E050` (50) karışmaz. A146'da "e50" → `E050` → kod tablosu satırı birebir bulunur.

## 5. Türkçe soru / İngilizce metin: BM25'e çevrilmiş sorgu (öneri, koşulmadı)

**Yaklaşım:** soru dili (`query.question_lang`) aranan kapsamın dilinden (§2'deki parça dili; kapsamsız soruda korpusun çoğunluk dili) farklıysa soru o dile çevrilir. **BM25 koluna çevrilmiş sorgu** (kodlar ve sayılar olduğu gibi), dense kola özgün soru (çok dilli model) verilir. Sözlük ya da dokümana özgü eşleme yok; çeviri her soruda aynı genel adımdır. Aynı soru için çeviri önbelleğe alınır.

| Seçenek | Ek gecikme | Maliyet | Not |
|---|---|---|---|
| Bulut LLM (ZDR'li küçük model) | ağ ~0,4–0,8 sn; sorgu embed'iyle (Qwen3-8B, ~0,6–0,8 sn) paralel çalışırsa duvar saatine ek ~0–0,3 sn | ~60–80 token/soru, ~0,00001 USD/soru (1.000 soru ~0,01 USD); fiyat ölçülmeli | soru metni zaten embed için ZDR'li buluta gidiyor; yeni veri türü yok |
| Yerel MT (ör. Marian tr→en, ~300 MB) | CPU'da ~0,1–0,3 sn | yok | yalnız eğitildiği dil çiftleri; gündelik/aksansız yazımda zayıf |

Rakamlar tahmin; reranker ölçümündeki ağ süreleri (medyan 0,38 sn) ve token sayısından.

**Kaçırılan 5 soruda beklenen etki** (beklenen parçanın metni ve terimlerin korpustaki sıklığına bakarak; ölçülmedi):

| Soru | Beklenen parçada | Beklenen etki |
|---|---|---|
| A081 "Uzun kruvaze paltoda düğmelenmeyen alt kat nasıl sabitlenir?" | "In the long **double-breasted coat**, the under extension, if not buttoned, should be held…" | **Yüksek:** "double-breasted" korpusta 3 parçada; doğru çeviri BM25'e nadir ve güçlü bir terim verir (bugün BM25 hiç bulmuyor, dense 22.) |
| A079 "Kalın kumaşlarda makine dikiş boyu nasıl seçilir?" | "**Machine stitch length** should be the same… the longer stitch for **bulky** materials" | **Orta:** "machine stitch length" yalnız bu parçada; ama "kalın" → "thick/heavy" metindeki "bulky" ile eşleşmez; JUKI ve Brother'ın dikiş boyu bölümleri rakip. İlk 20'ye girmesi olası |
| A148 "pantolon cep agzi kac inc" | "pocket **openings** measuring not less than 6 **inches**" | **Orta:** "pocket opening" 23 parçada (dikiş tablosu satırları rakip); aksansız yazım çeviriyi zorlaştırabilir. Kapsam pantolon şartnamesiyle sınırlı, ilk 20 olası |
| A151 "freze tablası şalteri nasıl kitlenir" | "To **lock switch** in the OFF position… **lockout key**" | **Yüksek:** yeni etiketle sayfa düzeyinde yakalanıyor (Fransızca çevirinin sayfası s. 51 ilk 5'te, kilitleme parçasının kendisi değil); çeviri İngilizce kilitleme parçasını doğrudan öne alır |
| A146 "s7300a e50 ne demek" | kod satırı "E050" | **Yok:** sorun dil değil kod biçimi; §4 çözer |

Riskler: alan terimlerinin yanlış çevrilmesi ("cep ağzı" → "pocket mouth"); kodların ve sayıların bozulması (çeviri istemi bunları korumalı, ayrıca §4'teki kod adımı çeviriden önce çalışmalı); BM25'te özgün Türkçe sorgunun da tutulması Türkçe dikkat dağıtıcıları geri getirir (B3b'de görüldü), bu yüzden yalnız çeviri önerilir.
