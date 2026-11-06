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

## Kararlar 2026-11-06 (öğle): c150bT bırakıldı; çalışma biçimi c150b

## 2'. Doğrulayıcı alan etiketini tanıyor

- Kural (`pilot/tables.field_quote_ok`, `bench/schema_c._quote_ok`): Alıntı "<Sütun>: <hücrenin bitişik bir parçası>" ise ve parçada aynı hücre o sütun etiketiyle varsa kabul edilir.
  - Hücre içeriği yine birebir olmalı.
  - " | " ile birden çok hücreyi birleştiren alıntı kabul edilmez (A017, A073 türü).
  - Gerekçe: etiket bizim satır serileştirmemize ait, bütün belgeler ve modeller için geçerli.
- Testler: `tests/test_tables.py` ve `tests/test_bench.py`. 438 test geçti.
- Kayıtlardan yeniden puanlama: bütün şema C koşuları (c, c150, c150b, c150bT, sure1, mt1200, ek). **54 değişiklik, hepsi ✖ → ✓.** Hepsi E050/E055/E210 ailesi "Remedy: ・…" alıntıları; hedef dışında A037 ve A061 de aynı kalıp.

**Soru soru** (önce → sonra):

| Soru | bugün | c150b DeepInfra | c150b Venice |
|---|---|---|---|
| Q14 | ✓ | ✖ → **✓** | ✖ → **✓** |
| A146 | ✓ | ✖ → **✓** | ✓ (değişmedi) |
| A038 | ✓ | ✖ → **✓** | ✖ → **✓** |
| A062 | ✓ | ✖ → **✓** | ✖ → **✓** |
| Q20 | ✓ | ✓ (değişmedi) | ✓ (değişmedi) |
| A155 | ✓ | ✓ (değişmedi) | ✓ (değişmedi) |

- Q20 ve A155 c150b'de zaten ✓ idi; c150bT ve c150'de ✖ → ✓ oldular.

**Bugünkü şemaya göre kalan fark** (cevaplı 160 soru, kural çıkışları hariç):

| | ✓ | ⚠ | ✖ | yanlış ret | JSON | beklenen değer |
|---|---|---|---|---|---|---|
| bugün DeepInfra | 118 | 11 | 12 | 19 | 0 | 90/113 |
| c150b DeepInfra | 116 | 1 | **15** | **25** | 2 | 88/94 |
| c150b Venice | 117 | 0 | 14 | 25 | 2 | 89/93 |

- ✖ farkı +6'dan **+3**'e indi. Yanlış ret farkı +6 ve değişmedi.
- Bugün ✓/⚠ olup c150b'de ✖ ya da ret olanlar (DeepInfra):
  - Ret: Q09, A024, A086, A102, A106.
  - Cümle sayısı alıntıda yok: A007, A025, A066, A109, A111, Q24 (sesli metin).
  - Alıntı birebir değil: Q04, A017, A077.
  - Aynı cümle tekrar: A047, A113.
  - Kesik (700): A074, A080. max_tokens 1200 ile A080 ✓ oldu, A074 ✖.
- Bugünkü şemanın 11 ⚠'sinin çoğu c150b'de ✓'ye ya da ✖'ye ayrışıyor; c150b'de ⚠ yok denecek kadar az.

## 5. c150b-J ("JSON'u girintisiz, tek satırda yaz"), tam set, max_tokens 1200, üç sağlayıcı paralel (0,149 USD)

Rapor: [nihai_c150bJ_rapor_2026-11-06.md](nihai_c150bJ_rapor_2026-11-06.md). İlk doğrulanmış cümle **gerçek akış zaman çizelgesinden** (192 satırın hepsinde kayıtlı). c150b satırları yaklaşık değer ve 2026-11-05 akşamı.

| Koşu | girintili | kesik | ✓ / ⚠ / ✖ | beklenen değer | netl. değer farklı / aynı | gereksiz netl. | ilk doğrulanmış cümle p50 / p95 |
|---|---|---|---|---|---|---|---|
| c150b DeepInfra (11-05, 700) | 0 % | 2 | 116 / 1 / 15 | 94 % | 4/5 · 8/13 | 0 | 2,37 / 4,70 sn (yaklaşık) |
| **c150b-J DeepInfra** | 0 % | **0** | 114 / 2 / 15 | 96 % | 4/5 · 8/13 | 2 (Q05, G7) | **1,56 / 2,56 sn** |
| **c150b-J Venice** | 0 % | **16** | 104 / 2 / 15 | 85 % | 3/5 · 5/13 | 0 | 1,39 / 2,30 sn |
| **c150b-J Parasail** | 0 % | **12** | 106 / 3 / 15 | 89 % | 3/5 · 6/13 | 0 | 1,26 / 2,05 sn |

- **Kural girintiyi kaldırdı** (üç sağlayıcıda da %0), ama Venice ve Parasail'in kesikleri sürüyor.
- **Asıl neden: boşluk kaçağı.** Model JSON'un ortasında, bir değerden sonra durmadan boşluk ya da satır sonu üretiyor ve 1200 token'a kadar devam ediyor. Örnek Q02 Venice: `"sesli_metin":"…olmalıdır."` ve ardından yalnız boşluk; JSON'un kapanmasına yalnız `,"celiski_var":false}` kalmıştı.
- Kayıtlarda kesik (finish=length) satırların dökümü:

| Koşu | JSON ortasında boşluk kaçağı | kaçak yok (gerçekten uzun) |
|---|---|---|
| c150b-J Venice / Parasail | 16 / 12 | 0 / 0 |
| c150bT Venice | 31 | 6 |
| c NextBit / Parasail / 31B (11-05) | 29 / 29 / 31 | 0 / 5 / 1 |
| DeepInfra, bütün koşular | **0** | 0–2 |

- Dün "girinti kesiği" sandığımız kesiklerin neredeyse hepsi bu kaçak; girinti eşlik eden bir belirti.
- **İkincil sağlayıcı: ölçüte göre aday yok.** Ölçüt c150b DeepInfra kesik düzeyi (2); Venice 16, Parasail 12.
- DeepInfra (c150b-J): ✖ 15 değişmedi. A074 ve A080 1200 sınırıyla ✓ oldu, A070 doğru netleştirmeye döndü. Koşudan koşuya oynama: Q32, A045, A081, A022 ✓ → ✖; A017, A047, A113, A144, A025 ✖ → ✓. Q05 ve G7'de gereksiz netleştirme.

## Kararlar 2026-11-06 (öğleden sonra): çalışma biçimi c150b-J (max_tokens 1200 dahil); §26 onaylandı

## 6. Akış bekçisi benzetimi (kayıtlardan; model çağrısı yok)

Tam tablo (N = 20 / 40 / 80): [akis_bekcisi_2026-11-06.md](akis_bekcisi_2026-11-06.md), araç `bench/akis_bekcisi.py`.

- **N'nin etkisi yok.** 20, 40 ve 80'de yakalanan sayısı aynı, yakalama anı 0,1 sn içinde. **Hiçbir koşuda yanlış alarm yok**: tamamlanmış hiçbir cevapta 20'den uzun boşluk dizisi bulunmuyor. Öneri N = 40.
- Yakalama: kaçakların hepsi yakalanıyor. Kaçan kesikler "gerçekten uzun" cevaplar (c150bT Venice 6, c Parasail 5); onlar 1200 token sınırının işi.
- **Kaçak soruya bağlı.** Aynı sağlayıcının iki koşusunda, birinde kaçan soru öbüründe de kaçıyor: Venice %38, Parasail %43, NextBit %60, 31B %75. Aynı sağlayıcıya yeniden deneme bu oranda yine boşa gider.

N = 40, c150b-J koşuları (gerçek akış zaman çizelgesi):

| | yakalanan kesik | yakalama anı p50 / p95 | yeniden deneme bedeli p50 / p95 (yakalama + ikinci deneme ilk doğr. cümle) | ikinci denemede yine kaçak | kullanıcıya ulaşmayan (tahmin) |
|---|---|---|---|---|---|
| Venice | 16 / 16 | 1,70 / 2,62 sn | 3,09 / 4,91 sn | %38 | **~%3,2** |
| Parasail | 12 / 12 | 1,68 / 4,98 sn | 2,94 / 7,01 sn | %43 | **~%2,7** |
| DeepInfra | 0 | – | – | – | %0 (c150b 700 sınırında %1,0) |

**Sağlayıcı önerisi:**
- Bekçiyle de **Venice ve Parasail ikincil olamaz** (ölçüt ≤ ~%1; tahmin %2,7–3,2).
- Kaçağın yeniden deneme bedeli p50'de ~3 sn; PRD'nin 3 sn ilk doğrulanmış cümle hedefini tek başına aşıyor.
- **Öneri: DeepInfra tek sağlayıcı.** Bekçi (N = 40) yine de ucuz bir sigorta olarak plana girsin: DeepInfra'da hiç tetiklenmedi, yanlış alarmı yok. Tetiklenirse aynı sağlayıcıya bir kez yeniden deneme.
- Uygulamaya bağlanmadı (karar).
- Not: 11-05 koşularında akış zaman çizelgesi yok; yakalama anları karakter konumundan yaklaşık (tabloda ≈).

## 7. Bağlanacak hattın uçtan uca ölçümü (§26; 0,121 USD)

Rapor: [hat_rapor_2026-11-06.md](hat_rapor_2026-11-06.md), araç `bench/hat_olcumu.py`.
- Hat: ikili yol (`manuals`, gömülü Qdrant) → c150b-J DeepInfra → verify_c.
- 245 soru, 5 ve 8 kaynak her soruda rastgele sırayla. Ölçüme girmeyen bir ısınma adımı var.
- Bu sayılar 10k ölçümleriyle doğrudan karşılaştırılamaz (korpus farklı).

| | ✓ / ⚠ / ✖ (cevaplı) | yanlış ret | beklenen değer | doğru "bulunamadı" | doğrulanmış görünen yanlış | netl. değer farklı / aynı | gereksiz netl. | u2u ilk doğr. cümle p50 / p95 | ≤ 3 sn |
|---|---|---|---|---|---|---|---|---|---|
| 5 kaynak | 123 / 0 / 23 | 11 | 93 % | 50/51 | **1 (B012)** | 12/15 · 11/13 | 2 | 2,27 / 3,63 sn | 88 % |
| 8 kaynak | 125 / 1 / 20 | 11 | 93 % | 51/51 | **0** | 13/15 · 10/13 | 2 | 2,40 / 3,63 sn | 84 % |

- **İkili yol yanlış reti 25'ten 11'e indirdi** (aynı 160 soru, varsayılan yol + c150b-J'ye göre). ✓ 114 → 123 / 125. ✖ 15 → 23 / 20: daha çok soru cevaplanıyor ve bir kısmı doğrulamada güvenli yönde kalıyor.
- Netleştirme teşhis soruları: Q07, C001, C003 ve C004 artık doğru netleştiriyor. C009 çeviri hatası yüzünden hâlâ "bulunamadı".
- Arama adımı p50 / p95: 627 ms / 1,06 sn. Çeviri p50 469 ms, 1,2 sn sınırını aşan %1 (3/245).
- **PRD (≤ 3 sn):** p50'de karşılanıyor (2,3–2,4 sn), p95'te karşılanmıyor (3,63 sn). Soruların %84–88'i 3 sn içinde.
- İzlenen sorular: Q05 iki varyantta da ✓ cevap. G7: 5 kaynakta ✖, 8 kaynakta gereksiz netleştirme.
- **5 / 8 önerisi: 8 kaynak**, kıl payı.
  - 8 kaynakta doğrulanmış görünen yanlış 0 (5 kaynakta B012 1), ✖ 3 daha az, değer farklı netleştirme 1 daha fazla.
  - Bedeli: u2u p50 +0,13 sn, ≤ 3 sn oranı −4 puan, maliyet +%17.
  - 24 soru varyantlar arasında iki yöne de değişiyor; fark gürültü düzeyine yakın. Belirleyici olan B012: 5 kaynakta niteleyici uyuşmazlığı tekrarlandı.

## Karar 2026-11-06: 8 kaynak (doğrulanmış görünen yanlış kapısını geçen varyant)

## 8. JUKI, tek seferlik (0,004 USD)

Rapor ve soru soru tablo: [nihai_juki_hat_rapor_2026-11-06.md](nihai_juki_hat_rapor_2026-11-06.md). Set küçük (12 cevaplı + 2 "bulunamadı"; 1 soru ≈ 8 puan). Bu sonuca göre ayar değişmez.
- (a) seçilen hat: ✓ 8 / ✖ 2 (J4, J10) / netleştirme 1 (J3; belge içi varyant, kapı tanımına göre doğru) / yanlış ret 1 (J12, arama). Değer 8/8, doğru "bulunamadı" 2/2, doğrulanmış görünen yanlış 0. Uçtan uca ilk doğrulanmış cümle p50 2,32 / p95 3,90 sn.
- (b) yalnız arama, 10k, filtreli: hit@1 / hit@5 varsayılan 9/12 · 10/12, ikili 7/12 · 10/12, üçlü 9/12 · 11/12.
- **Düzeltme (kayıtlardan):** İkili yolun JUKI'deki hit@1 kaybı J1 ve J5'te 1 → 2 sıra (ilk 5 içinde), J4'te 4 → ilk 20'nin dışı. J10'da kazanç 7 → 3. İkili yolun dev setteki kazancı JUKI'de hit@1 düzeyinde görünmedi; hit@5 eşit. Set küçük; gerçek belgelerle kurulacak yeni sette yeniden bakılacak.
- J4 ✖: karakter değişimi (kaynak "DC × 27", model "DC X 27"); model bilgisinden değil. J10 ✖: "❶" → sesli metinde "1". Yeni kayıt türleri ve dev set taraması JUKI raporunda.

## 9. İkincil yalnız yedek: benzetim (kayıtlardan)

- **Rol:** ikincil sağlayıcı yalnız DeepInfra hata, 429 ya da zaman aşımı verdiğinde çağrılır.
- **DeepInfra hata oranı** (bütün Adım 2 kayıtları, 2.704 çağrı): ilk denemede hata **0**. %95 üst sınır ~%0,11.
- **Kaçakta yeniden denemeyi diğer yedeğe göndermek** (Venice ↔ Parasail, c150b-J, aynı tur, 192 soru):
  - Venice'te kaçan 16 sorunun 7'sinde Parasail de kaçıyor (**%44**). Parasail'de kaçan 12 sorunun 7'sinde Venice de (%58). Ortak sorular: Q02, A087, A091, A093, A095, A137, A138.
  - Kaçak soruya bağlı. Diğer yedeğe göndermek aynı sağlayıcıya yeniden denemeden (%38–43) belirgin biçimde iyi değil.
  - Yedek kipinde (DeepInfra kesintideyken) ulaşmayan cevap ≈ 7/192 = **%3,6** (Venice → Parasail).
- **Toplamda:** ulaşmayan cevap ≈ P(DeepInfra kesintisi) × %3,6. Ölçülen kesinti 0 (üst sınır %0,11) ise toplam ≤ ~%0,004. Yalnız yedek rolünde ≤ %1 ölçütü sağlanıyor.
- Öneri: yedek Venice (bf16; c150b'de kalite DeepInfra'yla eşit), kaçakta Parasail'e bir kez. Bekçi N = 40.

## 10. Karakter normalleştirmesi (2026-11-06 akşam)

`verify.canon_chars`: NFKC + küçük genel tablo (× ✕ → x, ⁄ → /, daireli rakam blokları → rakam). NFKC tek başına yetmiyor: ①'i 1 yapıyor ama ×, ❶, ➀, ➊, ⓵, ⓫'e dokunmuyor ve ½'yi "1⁄2" (kesir eğik çizgisi) yapıyor.
- Bütün kayıtlar kayıttan yeniden puanlandı: dev set şema C ve bugünkü şema, yeni set, hat 5/8 kaynak, JUKI.
- Sonuç: **yalnız JUKI J4 ve J10 ✖ → ✓; ✓ → ✖ yok.**
- Kontrol: hat ve JUKI kayıtlarında arama kayıtlı BM25 metniyle yeniden kuruldu. Normalleştirme kapalıyken 0 değişiklik çıktı, yani kurulum birebir.
- Duman testi kaydında ham çıktı yoktu; yeniden puanlanamadı. Artık c kipinde ham çıktı ve akış zaman çizelgesi cevap kaydında tutuluyor.
- Not: geçersiz sayılmış ilk tur (`bozuk1_*`) yanlışlıkla `--force` ile yeniden puanlandı; tarihsel kayıt olduğu için git'ten geri alındı. Rozeti ya da değeri değişmeyen öteki kayıtlar da geri alındı (yalnız damga alanları değişmişti).

## 11. Kural katmanı ve "jacket" (kayıtlardan; silme kararı kullanıcıda)

**"Jacket" sorusunda ne oldu:** Netleştirme arama **öncesi** değil, arama **sonrası** kuraldan (K7, `post_search_ambiguity`) geldi.
- "jacket" hiçbir dokümanın kayıtlı adlarında yok, bu yüzden soru kapsamsız arandı.
- İlk 3 sonuç iki ayrı ürün şartnamesinden geldiği için kural "hangi ürün?" diye sordu.
- Ürün adının nerede eşleşeceğini `pilot/registry.py`'deki **elle yazılmış `aliases`** belirliyor:
  - Ceket: ("ceket", "acucoat", "gl-pd-14-04a");
  - Pantolon: ("pantolon", "trouser", "gl-pd-07-14a").
- Liste düzensiz: pantolonun İngilizcesi var, ceketin ("jacket", "coat") yok.

**İlke ihlali olarak raporlanan elle yazılmış listeler** ("belgeye özel kural yok" ilkesi):

| Liste | Yer | Ne yapıyor | Değerlendirme |
|---|---|---|---|
| `DocMeta.aliases` | registry.py | Sorudaki adı dokümana eşler; kapsam ve arama öncesi netleştirme | **İhlal (veri kodda):** ürün adı ve model kodu yükleme formundan gelebilir; elle seçilmiş çok dilli eşanlamlılar ("trouser", "acucoat", "kahve/coffee", "freze") belgeye özel ayar |
| `CUSTOMER_BRANDS` | registry.py | "US Army" → ceket + pantolon (arama öncesi "hangi ürün?") | **İhlal (veri kodda):** gerçek sistemde müşteri kaydından gelmeli |
| `FOREIGN_BRANDS` | query.py | 26 marka (Nike, Zara …) → model çağrılmadan "bu marka için doküman yok" | **İhlal (elle liste):** gerçek sistemde marka kaydı ve yetkiyle |
| `MUST_MATCH`, `KIND_OF_DOC_TYPE` | query.py | doküman türüne göre varlık rolleri | genel (türe göre, belgeye göre değil) |
| söylenmiş kod harfleri, dil ipuçları | query.py | konuşma ve dil işleme | genel |

**Kayıtlarda kural çıkışları** (c150b-J varsayılan yol + yeni set; hat k8 ikili yol):

| Kural çıkışı | sınıf | varsayılan yol | ikili yol |
|---|---|---|---|
| arama sonrası netleştirme (K7) | değer farklı | 7 (doğru) | 7 (doğru) |
| | değer aynı | 1 | 3 |
| | "bulunamadı" sorusu | 1 | 1 |
| arama öncesi ürün netleştirmesi (aliases / CUSTOMER_BRANDS) | – | **0** | **0** |
| kod yok / yabancı marka | "bulunamadı" | 3 / 2 | 3 / 2 |
| **Modelin kendi netleştirmesi** (şema C) | değer farklı / değer aynı / cevaplı | 3 / 9 / 4 | 7 / 8 / 3 |

- **Arama öncesi ürün netleştirmesi bu setlerde hiç tetiklenmiyor.** Gereklilik kayıtlardan ölçülemez; yalnız soru marka adı ("US Army") ya da birden çok dokümana uyan bir ad içerdiğinde çalışıyor.
- **K7, değer farklı netleştirmelerin yarısını taşıyor** (iki yolda 7). Kural kapalıyken modelin bu sorularda ne yapacağına dair kayıt yalnız 2 soruda var (kuralın bir yolda çıkıp öbür yolda modelin karar verdiği sorular):
  - A142: model doğru netleştirdi;
  - C004: model "bulunamadı" dedi (yanlış).
  - İki soruyla karar verilemez.
- K7'nin olası zararı: 1 "bulunamadı" sorusunda netleştirme sorması (gereksiz) ve "jacket" türü, ürünü soruda söylenmiş ama kayıtlı adı eşleşmeyen sorular. Değer aynı netleştirmeleri sınıf tanımına göre kabul edilebilir.
- **Kararınız için ölçüm önerisi (koşulmadı):** K7 kapalı, ikili yol, kuralın çıktığı ~11 soru + "bulunamadı" sorusu, Gemma 4 c150b-J DeepInfra: ~12 çağrı, **~0,003 USD**.
  - Ölçülecekler: değer farklı / aynı netleştirme ve gereksiz netleştirme, kural açık/kapalı.
  - Arama öncesi kural için ayrıca "US Army" ve aliases eşleşmeli sorulardan küçük bir set gerekir; bugünkü sette yok.
- "Jacket" türü için genel çözüm önerisi (koşulmadı): kayıtlı adlar yükleme formundaki ürün adı ve model kodundan alınır, eşanlamlı çevirisi otomatik yapılır (çeviri modeli, yükleme anında bir kez). Elle yazılmış eşanlamlı listesi yerine.

## 12. Sonraki adımlar (özet; koşulmadı)

**PRD yol haritası, Adım 2'den sonra.** Yol haritası PRD'de görsel olarak duruyor. Adımların içeriğini "Açık kararlar" tablosunun "Engellediği adım" sütunundan ve bileşen notlarından çıkardım:
- **Adım 3:** arka uç servisi (Streamlit test arayüzü servise bağlanır), giriş (A5), üretim sunucusu (A6).
- **Adım 4:** yetki ve doküman yönetimi: iki katmanlı yetki, yükleme ve kapsam raporu, departmanlar arası paylaşım (G11–G13, A4).
- **Adım 5:** ses: akışlı sesli cevap (G5), STT / TTS / VLM yerleşimi (A3), kodların okunuşu (A10).
- **Adım 6:** gerçek veri ve K1 kapısı: uzman onaylı soru seti (A2), denetim kaydı (G14, A8), sözleşme izni (A9).

**Açık işler, öncelik önerisiyle:**

| Öncelik | İş | Neden şimdi / ne zaman | Maliyet |
|---|---|---|---|
| 1 | **Gri "doğrulanıyor" akışı (devir f): ürün kararı** | PRD "ilk cümle ≤ 3 sn" p95'te tutmuyor (3,32–3,63 sn). Metnin hemen akması ilk görünen kelimeyi ~1,1 sn'ye indirir. Adım 3'te servis API'sinin akış biçimi buna göre tasarlanır; karar API'den önce gerekir | karar; ölçüm planı f'de |
| 2 | **K7 / aliases kararı** (§11) | Netleştirme davranışını belirliyor. Elle yazılmış listeler ilke ihlali. "Jacket" türü kaçış kullanıcıya görünür | ölçüm ~0,003 USD |
| 3 | **§23 niteleyici uyuşmazlığı, adım 1** (ölçüme ekleme) | Kod, çağrı yok; her raporda otomatik tarama. İstem varyantı (adım 2) sonra | 0; varyant ~0,12 USD |
| 4 | **Sunucu: Qwen embed, B3a / B3c** | Adım 3'ü engelliyor (A6). Sunucu gelince paralel yürür; süre bütçesinin arama kısmı ve eşzamanlı kullanıcı kapasitesi orada ölçülür | sunucuya bağlı |
| 5 | **J12 türü liste / şekil sayfaları** (arama) | Parça listesi, şekil sayfaları ilk 5'e girmiyor (J12, G-soruları). Gerçek belgelerle kurulacak sette ölçülmeli; tek JUKI sorusuyla ayar yapılmaz | yeni set |
| 6 | **C009 türü çeviri hataları** | Teknik terimin yanlış çevirisi BM25'i boşa düşürüyor ("baskı" → "print"). Genel çözüm adayı: çeviriye korpus terim listesinden ipucu ya da çevirisiz BM25'i ek kol olarak tutmak. Yeni sette sıklığı ölçülmeli | yeni set |
| 7 | **"bugun" kipinin silinmesi** | Bir sürüm tutulacak (karar). Öneri: Adım 3'ün ilk servis sürümüyle birlikte silinsin; `verify.py`'nin serbest metin yamaları (§15.1) da onunla gider | kod |
| 8 | **c150b-O** (`ilgili_kaynaklar`, erken ret) | İkili yolla yanlış ret 25'ten 11'e indi; kalan erken retler (A102, A106) azaldı. Getirisi düştü | ~0,12 USD |

## 13. Adım 6 (gerçek veri) için şirketten istenecek bilgiler

1. **Departman(lar)** ve her biri için doküman yetkilisi ve konu uzmanı (soru setini kontrol edecek kişi, A2).
2. **Belge sayısı ve toplam sayfa**, departman başına.
3. **Belge türleri:** makine kılavuzu, ürün şartnamesi / teknik föy, iş talimatı, kalite prosedürü, dikim kaynağı vb. ve her türün payı.
4. **Biçim ve kalite:** PDF metin mi, taranmış mı (oran); Word / Excel / görsel var mı; diller; şekil ve tablo yoğunluğu.
5. **Sürümler:** aynı belgenin birden çok sürümü var mı, güncelleme sıklığı; eskisi silinecek mi, tutulacak mı.
6. **Ürün / model / müşteri markası listesi:** yükleme formundaki "ürün" alanına girecek adlar, aynı ailenin modelleri, müşteri markaları. Elle yazılmış listelerin yerine geçecek veri.
7. **Yetki yapısı:** kim hangi belgeyi görür (gruplar), departmanlar arası paylaşım örnekleri (A4).
8. **Gizlilik ve sözleşme:** hangi belgelerin parçaları ZDR'li buluta gidebilir, hangileri kesinlikle yerelde kalmalı (A9).
9. **Soru seti:**
   - kimden (uzman ve ustalar), kaç soru (öneri: departman başına 50–100);
   - içerik: yaklaşık %20 cevabı belgede olmayan, %10 netleştirme gerektiren soru; gerçek usta soruları ve sesli soru örnekleri;
   - her soru için beklenen değer ve kanıt sayfası;
   - onaylayan kişi.
10. **Kabul ölçütü:** yanlış değer toleransı (PRD: doğrulanmış görünen yanlış 0, değer doğruluğu ≥ %98) şirketçe kabul ediliyor mu (A2).
11. **Kullanım ortamı:** cihaz (tablet modeli), ağ / Wi-Fi kapsamı, gürültü; kodların atölyede nasıl söylendiği (A10).
12. **Terim sözlüğü** (isteğe bağlı departman verisi): atölye terimi → belge terimi.
13. **Denetim kaydı:** ne kadar saklanacak, kim görecek (A8).

## 14. Elle yazılmış listeler ve K7 ölçümü (2026-11-06; 62 soru × 3 durum, yeni hat, 8 kaynak, DeepInfra; 0,040 USD)

Etkilenen sorular: 28 netleştirme sorusu, kayıtlarda kural çıkışı olanlar ve listeler kapanınca kapsamı değişenler. Dağılım: 28 netleştirme, 18 "bulunamadı", 16 cevaplı. Raporlar: `nihai_kural_{a,b,c}_rapor_2026-11-06.md`.

| Durum | değer farklı netl. | değer aynı netl. | belge içi varyant | gereksiz netl. | doğru "bulunamadı" | doğrulanmış görünen yanlış | cevaplı ✓ / ✖ / ret | model çağrısı | maliyet |
|---|---|---|---|---|---|---|---|---|---|
| (a) bugünkü hal | 12/15 | 10/13 | 0/0 | 1 (B033) | 17/18 | 0 [] | 10 / 3 / 3 (n=16) | 46 | 0.0123 |
| (b) listeler kapalı, K7 çeviriyle | 12/15 | 10/13 | 0/0 | 2 (A150, B033) | 17/18 | 0 [] | 10 / 2 / 3 (n=16) | 48 | 0.0124 |
| (c) listeler ve K7 kapalı | 13/15 | 8/13 | 0/0 | 1 (A150) | 18/18 | 0 [] | 10 / 2 / 3 (n=16) | 59 | 0.0152 |

| Soru | sınıf | (a) bugünkü hal | (b) listeler kapalı, K7 çeviriyle | (c) listeler ve K7 kapalı |
|---|---|---|---|---|
| aday_sorular:A110 | cevap | cevap/failed | cevap/verified | cevap/verified |
| aday_sorular:A134 | deger_ayni | cevap/failed ✗ | cevap/failed ✗ | cevap/verified ✗ |
| aday_sorular:A140 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular:A143 | deger_ayni | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | cevap/failed ✗ |
| aday_sorular:A144 | deger_ayni | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | cevap/failed ✗ |
| aday_sorular:A145 | deger_ayni | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular:A150 | cevap | cevap/verified | netlestirme/clarify | netlestirme/clarify |
| aday_sorular:A151 | cevap | bulunamadi/not_found | cevap/verified | cevap/verified |
| aday_sorular_ek:B033 | bulunamadı | kural:netlestirme_sonra/clarify | kural:netlestirme_sonra/clarify | bulunamadi/not_found |
| aday_sorular_ek:C004 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular_ek:C005 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular_ek:C006 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular_ek:C007 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular_ek:C008 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| aday_sorular_ek:C010 | deger_farkli | kural:netlestirme_sonra/clarify ✓ | kural:netlestirme_sonra/clarify ✓ | netlestirme/clarify ✓ |
| questions:Q07 | deger_farkli | cevap/verified ✗ | cevap/verified ✗ | netlestirme/clarify ✓ |
| questions:Q08 | bulunamadı | kural:yabanci_marka/not_found | bulunamadi/not_found | bulunamadi/not_found |
| questions:Q18 | bulunamadı | kural:yabanci_marka/not_found | bulunamadi/not_found | bulunamadi/not_found |
| sekil_sorular:N2 | cevap | cevap/verified | bulunamadi/not_found | bulunamadi/not_found |

**Okuma** (set küçük; 1–2 soru farkı gürültü düzeyinde, Q07 aynı durumda bile koşudan koşuya değişiyor):
- **Listeleri kapatmak, (a) → (b):** netleştirme metrikleri aynı (değer farklı 12/15, değer aynı 10/13).
  - Yabancı marka soruları (Q08, Q18) liste olmadan da doğru "bulunamadı" alıyor; artık model veriyor (kural yerine).
  - Yan etkiler, takma ad kaybıyla:
    - N2 ✓ → yanlış ret ("Granovsky" adı ürün alanında yok);
    - A150 gereksiz netleştirme ("kahve" adı kayıp, kapsam açıldı);
    - A110 ✖ → ✓ ve A151 yanlış ret → ✓ (kazanç).
  - K7'nin çevrilmiş soruda ürün araması bu sette hiçbir şeyi değiştirmedi: ürün alanları Türkçe, çeviri İngilizce.
- **K7'yi de kapatmak, (c):**
  - değer farklı 13/15: model C004–C010 netleştirmelerini kuralsız da yapıyor, Q07'yi de;
  - "bulunamadı" 18/18: B033'teki gereksiz kural netleştirmesi kalkıyor;
  - değer aynı 10/13 → 8/13: A143 ve A144'te kural soruyordu, model iki ürünün kaynağını göstermeden cevapladı ve ✖ oldu;
  - model çağrısı 46 → 59: kural çıkışları anlık, model çağrısı ~2–3 sn ve maliyet.
- Doğrulanmış görünen yanlış üç durumda da **0**.
- **Silme kararı kullanıcıda.**
  - Veriye göre üç liste kalite kaybı olmadan kaldırılabilir. Yan etkileri kayıt alanlarıyla kapatılabilir: N2 ve A150 gibi adlar ürün/marka alanından gelmeli.
  - K7'nin kaldırılması değer farklı ve "bulunamadı" sorularında iyileştiriyor, değer aynı sorularda 2 soru kaybettiriyor ve süreyi uzatıyor.

## 15. Kararlar 2026-11-06 (akşam): listeler silindi, K7 kapalı, gri akış c150b-J, OCR zorunlu

- **c150b-JM reddedildi.** Gri akış C c150b-J ile; arayüz bağlama planı API planı §10'da.
- **Üç liste silindi.** Kayıt alanları `title` ve `author` eklendi (test belgeleri ilk sayfadan dolduruldu; metadata). Adlar: ürün adı, model kodu, tam başlık, yazar soyadı, doküman kimliği. Karşılaştırma anahtarında ı/i farkı yok sayılıyor (İngilizce büyük harfli başlık).
- **K7 kapalı** (`PILOT_K7=0` varsayılan). Açılırsa ürün adını çevrilmiş soruda da arar.
- **Kayıtlardan yeniden puanlama** (62 soru; çağrı yok): yeni kayıtla her sorunun kapsamı ölçülmüş bir durumla aynı. 55 soru (c)'nin kapsamında, 7 soru (a)'nın kapsamında (kaynak belgeleri doğrulandı). Sonuç o kayıtlardan:

| | değer farklı | değer aynı | gereksiz netl. | doğru "bulunamadı" | doğrulanmış görünen yanlış | cevaplı ✓ / ✖ / ret (16) |
|---|---|---|---|---|---|---|
| (c) ölçülen | 13/15 | 8/13 | 1 (A150) | 18/18 | 0 | 10 / 2 / 3 |
| **yeni kayıt (türetilmiş)** | 13/15 | 8/13 | 1 (A150) | 18/18 | 0 | **11 / 2 / 2** |

- **N2 düzeldi:** yazar soyadı "Granovsky" kapsamı geri getiriyor, (a)'daki gibi ✓. Aynı yolla Granovsky ve Strickland adını anan N1, A095, A115, A126, A152 ve B023 de (a)'daki kapsama döndü.
- **A150 düzelmedi:** "kahve makinası kireç nasil temizlenir" sorusu kayıttaki ürün adıyla ("Kahve makinesi") yazım farkı yüzünden eşleşmiyor. İngilizce başlık ("Mr. Coffee Coffeemaker Instructions") Türkçe soruyla eşleşemez. Çeviri üzerinden ad eşleşmesi yalnız K7 içinde ve K7 kapalı.
  - Genel çözüm adayları (koşulmadı): kapsam tespitinde ürün adını çevrilmiş soruda da aramak (başlık İngilizce); ad eşleşmesinde Türkçe ek/yazım toleransı.
- **Yan etki:** tek kelimelik İngilizce ad ("trousers", "jacket") artık kapsam belirlemiyor; eskiden "trouser" takma adı vardı. Başlık tam eşleşiyor, kelime düzeyi eşleşme riskli ("repair", "safety" gibi kelimeler yanlış belgeye kilitlerdi). Kaynağı arama bulur, belirsizliği model sorar.

**Öncelik listesi (güncel):**
1. Gri akış C (c150b-J): arayüze bağlama, API planı §10.
2. **OCR, pilot öncesi zorunlu:** [docs/PLAN-OCR.md](../../../../docs/PLAN-OCR.md).
3. §23 niteleyici, adım 2 (istem varyantı), gerekirse.
4. Sunucu: Qwen embed, B3a / B3c.
5. J12 türü liste / şekil sayfaları.
6. C009 türü çeviri hataları.
7. `bugun` kipinin silinmesi (Adım 3'ün ilk servis sürümüyle).
8. c150b-O.
9. **(Düşük öncelik)** Çok kelimeli ürün adlarında küçük yazım toleransı ("makinası" ~ "makinesi"). Yalnız adın bütün kelimeleri eşleşirse; tek kelimelik eşleşme yok (karar 2026-11-06). A150 türü.

## 16. Ses ölçümü, gri akış ölçümü, metin katmanı kontrolü (2026-11-06 öğleden sonra)

**Ses (c150b-JS, `sesli_metin` yok; tam set, yeni hat, 8 kaynak; 0,061 USD).**
- Bu koşu, listelerin silinmesinden ve K7'nin kapatılmasından **sonra** yeni kodla yapıldı. Taban (c150b-J) eski kurallarla ölçülmüştü; tüm sette iki etki karışıyor.
- Sesli metnin kendi etkisi, iki koşuda da kural çıkışı olmayan ve kaynak belgeleri aynı 151 cevaplı soruda:

| | ✓ / ⚠ / ✖ | yanlış ret | beklenen değer |
|---|---|---|---|
| sesli_metin var | 120 / 1 / 18 | 9 | 93/100 |
| **sesli_metin yok** | 124 / 2 / 16 | 6 | 96/103 |

- **Kalite bozulmuyor.** Yalnız sesli metin yüzünden ✖ olan 2 soru (Q04, Q24) ✓ oldu. Çıktı tokeni p50 180 → 137 (%−24).
- Süreler bu koşuda daha kötü (ilk doğrulanmış cümle p95 3,63 → 5,08 sn). Koşu öğleden sonra yapıldı; `sesli_metin` JSON'un son alanı olduğu için ilk doğrulanmış cümleyi etkileyemez. Ağ yüküne bağlanıyor; aynı saatte yan yana ölçülmedi.
- **B012** bu koşuda yine doğrulanmış görünen yanlış oldu. Varyanttan bağımsız, koşudan koşuya çıkan risk; §23 adım 2 (istem kuralı) önem kazanıyor.
- Öneri: `sesli_metin` şemadan çıkarılsın (c150b-JS çalışma biçimi olur). Karar kullanıcıda.

**Gri akış C, uygulama yolu (25 soru, c150b-J; 0,007 USD).** Rapor: [gri_akis_2026-11-06.md](gri_akis_2026-11-06.md).

| Ölçü | Değer |
|---|---|
| İlk görünen kelime p50 / p95 | **1,91 / 2,48 sn** |
| İlk doğrulanmış cümle p50 / p95 | **2,18 / 3,37 sn** (14/17 ≤ 3 sn) |
| ✖ kartı | 1 öğe (A086) |
| Cevap tamamlanamadı / sıfırlama | 0 / 0 |
| Akışta sızan rakam | **0** |
| Sağlayıcı | DeepInfra 25/25 |

**Metin katmanı kontrolü** (`pilot/text_layer.py`, ayrıştırma günlüğüne bağlı, testli). Test belgelerinde:

| Belge | dijital | taranmış + OCR katmanı | zayıf (yeniden OCR) | metin yok |
|---|---|---|---|---|
| Ceket (GL-PD-14-04A) | 54 | 2 | 0 | 0 |
| **Pantolon (GL-PD-07-14A)** | 0 | **48** | 0 | 0 |
| S-7300A / B | 107 / 116 | 1 / 0 | 0 | 0 / 1 |
| **Strickland** | 0 | **136** | 0 | **28** |
| **Granovsky** | 0 | 0 | **269** (harf aralıklı) | 2 |
| JUKI / Mr. Coffee / Bosch | 49 / 21 / 95 | 0 / 1 / 0 | 1 / 0 / 1 | 0 |

- Kalibrasyonla çıkan sonuç: harf/rakam karışıklığı teknik belgede bozulma işareti değil ("LSd-1", "3/16-inch", "230psi"). Bu sinyal çıkarıldı.
- Bilinen sayısal OCR hataları ("112", "IS", "3116") metinden anlaşılamaz. Bu yüzden "taranmış + OCR katmanı" ayrı sınıf ve yeniden OCR karşılaştırmasına aday.

## 17. Kararlar (2026-11-06 akşam) ve B012 tekrar ölçümü

- **Çalışma biçimi c150b-JS** (sesli_metin yok; ses yalnız doğrulanmış öğe metinlerinden). Gri akış sonucu kabul.
- **B012, 10 tekrar** (uygulama c yolu, yeni hat, 8 kaynak; 0,006 USD; `bench/b012_tekrar.py`):

| Şema | sonuç | doğrulanmış görünen yanlış |
|---|---|---|
| c150b-JS | 10/10 ✓ ("kaldırma kolu … standart yükseklik 6 mm") | **10/10** |
| c150b-JSN (niteleyici kuralı) | 10/10 "bulunamadı" | **0/10** |

- c150b-JS'de B012 bu hatta her seferinde yanlış cevap veriyor (önceki koşulardaki "bazen" görüntüsü arama ve kural farklarındandı).
- İstem kuralı ("sorudaki ayırt edici niteleyici kaynakta yoksa o konuyu başka parçanın bilgisiyle cevaplama; bulunamadı") oranı 10/10'dan 0/10'a indirdi.
- Tam set regresyon kontrolü (c150b-JSN, ~0,06 USD) sürüyor.
- **OCR araçları kuruldu:**
  - Tesseract 5.4 (kullanıcı klasörüne, Türkçe dil verisiyle);
  - OCRmyPDF 17.13 (uygulama ortamına).
  - **Ghostscript kurulamadı:** yönetici izni gerekti, onay penceresi iptal edildi.
  - OCRmyPDF Ghostscript'siz çalışabiliyor (`--rasterizer pypdfium`, `--output-type pdf`). Bu durumda AGPL'li Ghostscript gerekmiyor; yalnız PDF/A çıktısı yok (ihtiyaç da yok).
