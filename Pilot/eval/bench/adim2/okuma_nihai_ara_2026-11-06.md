# Okuma notu: Adım 2, 2026-11-06 kararlarından sonrası

Önceki not: [okuma_nihai_ara_2026-11-05.md](okuma_nihai_ara_2026-11-05.md).

## 1. B012 ve niteleyici uyuşmazlığı (kayıtlardan)

- B012 etiketi doğru kalıyor: S-7300A'da dijital kaldırıcı yok. Gemma 4 DeepInfra'nın yeni setteki **1 doğrulanmış görünen yanlışı** olarak sayılıyor; [nihai_ek_rapor_2026-11-06.md](nihai_ek_rapor_2026-11-06.md) bunu zaten "doğrulanmış görünen yanlış: 1" diye gösteriyor.
- Yeni hata türü: **niteleyici uyuşmazlığı**. Tanım ve çözüm planı: [plan §23](plan_cevap_modeli_2026-11-05.md).
- Tarama (`bench/niteleyici_tarama.py`): niteleyici içeren 133 doğrulanmış ya da kısmi cevap (bugünkü şema DeepInfra, c150b iki sağlayıcı, yeni set iki sağlayıcı). Sonuç **yalnız B012**.
- İlk taramada A045 ve A069 da çıkmıştı; ikisi de yanlış alarmdı. Kaynakta "-[][]3 specifications" yazıyor ve iki cevabın değeri de doğru. Kalıp düzeltildi.

## 2. Netleştirme teşhisi (ilk 5 kaynak, kayıtlardan)

| Soru | Beklenen iki ürün | İlk 5'te | Model | Teşhis |
|---|---|---|---|---|
| Q07 SPI | ceket + pantolon şartnamesi | ikisi de **yok**; 5 parçanın 5'i Brother hız ayarı | bulunamadı | **arama** (Türkçe "SPI", çeviri yok) |
| C001 diz kaldırıcı | S-7300A + B s.12 | iki ürün var ama s.12 değer parçaları **yok**. A s.30: "knee lifter ile kalkar" (değersiz); kaynak 1–2: mekanik kolun 6 mm'si | bulunamadı (doğru davranış) | **arama** |
| C003 yörünge 1, 5,0 mm | S-7300A s.76 + B s.78 | A'nın değeri var (s.76, 2000 sti/min); B'nin s.78 parçası **yok** (B s.12 başka tablo) | A'nın değerini **ürün adı vermeden** yazdı | **arama** + model (ürün adı yok) |
| C004 overlok SPI | ceket + pantolon | ceket parçası var ama başka paragraf (00179, IFF 8 ± 1); pantolon **yok**; 2 JUKI, 2 Strickland | bulunamadı | **arama** |
| C009 alt kenar genişliği | ceket s.24 + pantolon s.20 | iki belge var ama beklenen parçalar **yok** (00138 desen kısaltmaları, 00109 cep kapağı) | bulunamadı | **arama** |

- Beşinde de birincil sorun arama: değeri taşıyan parça ilk 5'e girmiyor. Model kaynakta değer yokken netleştirme sormuyor; bu doğru, çünkü iki ürünün değeri görünmeden "değer ürüne göre değişiyor" denemez.
- C003'teki model hatası ayrı: tek ürünün değerini ürün adı vermeden genel cevap gibi yazıyor.
- Silinen kurallar geri gelmiyor (karar).

## 3. max_tokens 1200, kesik 3 soru (0,0040 USD)

| Sağlayıcı | Soru | 700 | 1200 | token | ilk doğrulanmış cümle / toplam |
|---|---|---|---|---|---|
| DeepInfra | Q05 | ✓ (692) | ✓ | 710 | 1,72 / 8,9 sn |
| DeepInfra | A074 | kesik | **tamamlandı ama ✖** (alıntı birebir değil; "5" alıntıda yok) | 631 | 2,38 / 7,4 sn |
| DeepInfra | A080 | kesik | **✓** | 631 | 2,05 / 8,0 sn |
| Venice | Q05 | kesik | **✓** | 889 | 1,55 / 6,4 sn |
| Venice | A074 | kesik | **✓** | 910 | 1,53 / 8,2 sn |
| Venice | A080 | ✓ (625) | **kesik (1200)** | 1200 | – / 13,2 sn |

- 1200 sınırı kesiklerin 6'sından 4'ünü kapattı. İlk doğrulanmış cümle süresi değişmedi (1,5–2,4 sn), çünkü yalnız uzun cevapların sonu uzuyor.
- Venice A080'deki kesik bir döngü değil: Venice JSON'u **girintili** yazdı ve boşluklar token tüketti.

**Yeni bulgu: Venice bugün girintili JSON yazıyor.**

| Kayıt | girintili JSON |
|---|---|
| c150b Venice, 2026-11-05 akşam | 0/192 |
| c Venice, 2026-11-05 | 0/192 |
| yeni set Venice, 2026-11-06 sabah | **29/39** |
| max_tokens 1200 Venice, 2026-11-06 | **3/3** |
| DeepInfra, bütün koşular | 0 |

- İstek ve şema aynı; değişiklik sağlayıcı tarafında. Sonuçları: daha fazla token, daha uzun toplam süre, daha çok kesik.
- c150bT koşusunun Venice kısmında da sayılacak.

## 7. JSON okuyucuda kontrol karakteri toleransı ve gerçek hata nedeni

- Ortak adım `pilot/jsonparse.py`: `json.loads(..., strict=False)`. Kullanan yerler: `pilot/llm.py` (uygulama), `bench/schema_c.parse_c`, `bench/answer_models.parse_answer`.
- Hata sınıfı artık gerçek nedeni söylüyor:
  - `finish=length` → "çıktı uzunluk sınırında yarıda kesildi";
  - diğer durumlar → "JSON okunamadı (<hata türü, konum>)".
  - Bench'te `kesik` artık yalnız `finish=length`; önceki "açık parantez fazla" sezgisi kaldırıldı.
- Testler: `tests/test_pipeline.py` (iki mesaj, kaçışsız sekme, kesik hata) ve `tests/test_bench.py` (parse_answer, parse_c). Toplam 436 test geçti.
- Kayıtlardan yeniden puanlama (`--rescore-c nihai_c nihai_c150 nihai_c150b nihai_mt1200`, `nihai_ek`):
  - `finish=stop` + okunamayan satırların **hepsi** artık okunuyor.
  - **A066** (c150 DeepInfra/Venice, c150b DeepInfra/Venice): JSON okunuyor ama **hâlâ ✖**. İkinci öğedeki "başlangıç değeri 2.00" alıntıda yok (alıntı ayar birimi satırı).
  - **A018** (c, DeepInfra): okunur oldu ve **✓**.
  - `finish=length` olan satırlar gerçekten kesik ve öyle kalıyor (ör. c'de Parasail 34, NextBit 29, Gemma 31B 32).
- Not: c150bT koşusunun DeepInfra kısmı eski kodla çalıştı (süreç değişiklikten önce başlamıştı), Venice kısmı yeni kodla. Koşu bitince iki dosya da kayıttan yeniden puanlanacak.

## 2b. Netleştirme teşhisi devamı: ikili yolda yalnız arama (0,0002 USD, yalnız çeviri)

Koşu: Gemma 4 NextBit çevirisi (`translate_compare --pass teshis_nl --ids …`), ardından `triple_fusion --arms bge,bm25 --bm25-translations … --ids …` (10k, yerel Qdrant, rerank'sız). Filtreli ve filtresiz sonuç aynı; bu sorularda kapsam süzgeci yok.

| Soru | Varsayılan yol: değer parçası ilk 5'te | İkili yol: beklenen parçaların sırası | İkili yol: iki ürün ilk 5'te |
|---|---|---|---|
| Q07 SPI | ikisi de yok | pantolon 00141: **3**, ceket 00178: 10 | yalnız pantolon |
| C001 diz kaldırıcı | ikisi de yok | S-7300A 00035: **5** ("Knee lifter … 16mm"), S-7300B 00032: 8 | yalnız A |
| C003 yörünge 1 | A var (s.76), B yok | A'nın s.76 değeri 1. sırada (kabul parçası 00354: 11), B 00374: 15 | yalnız A |
| C004 overlok SPI | ikisi de yok | pantolon 00141: **2**, ceket 00178: **4** | **ikisi de** |
| C009 alt kenar | ikisi de yok | ilk 20'de yok | hayır |

- İkili yol beş sorunun dördünde değer parçasını öne çekiyor, ama iki ürünü birlikte ilk 5'e yalnız C004'te getiriyor. Q07, C001 ve C003'te ikinci ürünün parçası 8–15. sırada.
- İkinci ürün ilk 5'e girmeyince model netleştirmeyi göremez; tek ürünün değerini yazma riski doğar (C003 türü).
- C009: çeviri "alt kenar baskısı" ifadesini (kıvırma payı, hem) "bottom edge print" yapmış ("baskı" → print). Arama ilk 20'de bile bulamıyor. Bu bir çeviri hatası; sözlük ekleme belgeye özel düzeltme olacağı için önerilmez.
- Sonuç: netleştirme kaçışlarının birincil nedeni arama, ikili yol kısmen iyileştiriyor. İki ürünün değer parçası 5–15. sıradaysa ilk 5 yetmiyor.
- Ayrı ölçülebilecek seçenekler (koşulmadı): netleştirme adayı sorularda bağlamı 8'e çıkarmak ya da aynı 5 soruyu üçlü füzyonda (Qwen kolu önbellekte yoksa embed çağrısı gerekir) yalnız arama olarak çalıştırmak.

## 4. c150bT (tablo hücresi kuralı), tam set, iki sağlayıcı (0,106 USD)

Rapor: [nihai_c150bT_rapor_2026-11-06.md](nihai_c150bT_rapor_2026-11-06.md). Aynı ölçütlerle karşılaştırma:

| Koşu | JSON hatası | ✓ / ⚠ / ✖ | beklenen değer | netl. değer farklı | netl. değer aynı | ilk doğrulanmış cümle p50 / p95 |
|---|---|---|---|---|---|---|
| c150b DeepInfra (11-05) | 2 | 112 / 1 / 19 | 94 % | 4/5 | 8/13 | 2,37 / 4,70 sn |
| **c150bT DeepInfra** | 1 | 108 / 1 / 23 | 95 % | 4/5 | 8/13 | 1,94 / 3,81 sn |
| c150b Venice (11-05) | 2 | 113 / 0 / 18 | 96 % | 4/5 | 8/13 | 2,72 / 4,63 sn |
| **c150bT Venice** | **37** | 89 / 2 / 16 | 79 % | 2/5 | 2/13 | 1,52 / 2,23 sn |

**Hedef sorular** (bugün | c150b → c150bT DeepInfra | c150b → c150bT Venice):

| Soru | bugün | DeepInfra | Venice |
|---|---|---|---|
| Q14 | ✓ | ✖ → ✖ | ✖ → ✖ |
| A146 | ✓ | ✖ → ✖ | ✓ → ✓ |
| A038 | ✓ | ✖ → ✖ | ✖ → ✖ |
| A062 | ✓ | ✖ → ✖ | ✖ → ✖ |
| A017 | ✓ | ✖ → ✓ | ✓ → ✖ |
| A073 | ✖ | ✖ → ✖ | ✖ → ✖ |

- **Kural tutmadı.** c150bT DeepInfra'da model hâlâ her maddenin önüne "Remedy: " yazıyor ("Remedy: ・Turn off the power and check the connection of connector P2."). Q20 (E055) ve A155 (E050) aynı hataya **yeni** düştü.
- **Regresyon (DeepInfra, c150b'ye göre, kesikler hariç):**
  - ✓ → ✖: Q20, A014, A081, A105, A155. A022 ✓ (değer yanlış) → ✖.
  - ✖ → ✓: A007, A017, A113.
  - Q06: ✓ → gereksiz netleştirme.
  - Net etki: ✓ 112 → 108. Bugünkü şemaya göre de geride.
- **Gözlem:** "Code: … | Cause: … | Remedy: ・… ・…" bir PDF tablo başlığı değil, bizim tablo satırı serileştirmemizin alan etiketi. Model etiketi alıntının parçası sayıyor. Genel çözüm adayı (koşulmadı, karar sizde): maddeli hücrelerde her maddenin parça metninde kendi satırında olması, ya da doğrulamanın "Alan: " önekini tanıması. İkincisi §16'ya takılır; birincisi indeksleme değişikliği.
- **Öneri: c150bT bırakılsın; çalışma biçimi c150b kalsın.**
- **Venice:** 37 kesik, girintili JSON yüzünden (aşağıda). Kalite farklarını bu karıştırıyor; Venice satırları kural etkisini ölçmüyor.

## a. Girintili JSON: sağlayıcı ve koşu bazında

Her şema C raporunda artık "Girintili JSON" tablosu var. Gemma 4 koşularının özeti:

| Sağlayıcı | 2026-11-05 | 2026-11-06 |
|---|---|---|
| DeepInfra | %0 (c, c150, c150b, sure1) | %0 (ek, mt1200, c150bT) |
| Venice | %0 (c, c150, c150b, sure1) | **%74 (ek), %100 (mt1200), %94 (c150bT)** |
| NextBit | %93 (c), %90 (sure1) | – |
| Parasail | %96 (c), %97 (sure1) | – |

| Venice | kesik (finish=length) | çıktı tokeni p50 | ilk doğrulanmış cümle p50 / p95 |
|---|---|---|---|
| c150b, 11-05 17:57 (girinti %0) | 2 | 179 | 2,72 / 4,63 sn |
| c150bT, 11-06 09:35 (girinti %94) | **37** | 214 | 1,53 / 2,24 sn |

- Venice'in ilk doğrulanmış cümle süresi bugün daha iyi; sabah saatinde yük daha düşük olabilir. Ama kesikler 2'den 37'ye çıktı: 192 sorunun %19'unda cevap yok.
- Karar ölçütü (ilk doğrulanmış cümle ya da kesik kötüleşirse) kesik sayısında karşılandı. **Öneri: birincil/ikincil sırası değişsin, DeepInfra birincil, Venice ikincil** (plan §21).
- DeepInfra bütün koşularda girintisiz ve kesik 0–2.
- "Girintisiz yaz" istem kuralı ayrı varyant olarak plan §24'te (c150b-J); koşulmadı.
