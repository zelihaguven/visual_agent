# Adım 2 planı: cevap modeli seçimi, ilk tur (2026-11-05, onaylandı, ekleriyle)

> **"Bulunamadı" kararının 17 sorusu onaysız (A114–A130). Bu koşu ön elemedir; nihai seçim onaylı ve büyütülmüş
> sette yapılacak.**

**Onayla gelen ekler (2026-11-05):**
- **(a) Dayanıklılık metriği.** Her model için ZDR sağlayıcı sayısı, 429 ve hata oranı, cevapsız kalan soru sayısı ölçülecek. Yeniden deneme politikası bütün modellerde aynı ve raporda yazılı: ilk token gelmeden 429, 5xx ya da bağlantı hatası olursa 30 sn sonra bir kez yeniden denenir. 429 yüzünden cevapsız kalan sorular kalite metriklerinden ayrı sayılır; kalite yalnız cevap gelen sorularda ölçülür.
- **(b)** Raporun başına yukarıdaki not yazılacak.
- **(c)** Bütün modellerde aynı istem ve temperature 0. Modele özel istem ayarı yapılmayacak; formata uymayan model JSON metriğinde görünecek.
- **(d)** Bütçe sınırı 1,5 USD. Aşılırsa koşu durur ve haber verilir.
- Yerel taban gece koşulacak.

Amaç: Cevap modelini (PRD A1) aynı arama sonuçları üzerinde karşılaştırmak. K1'in en uzak ölçütü doğru "bulunamadı" oranı: bugün %48, hedef ≥ %90; "doğrulanmış görünen yanlış cevap" hedefi 0.

## 0. Önce: ZDR kontrolü (yapıldı, `323efdb`)

`/endpoints/zdr` listesi "Safety Retention" uç noktalarını da içeriyor. 2026-11-05 itibarıyla 1118 uç noktanın 56'sı bu sınıfta ve hepsi `google-vertex`. Bu uç noktalar, güvenlik incelemesi için istemi saklayabiliyor.

`require_zdr` artık model adına değil, uç noktanın saklama sınıfına bakıyor: yalnız `safety_retention: false` olanlar ZDR sayılıyor. Alan hiç yoksa uç nokta yine ZDR sayılmıyor. Ayrıca `zdr: true` tek başına Safety Retention uç noktalarını dışlamadığı için, modelin bu sınıftaki sağlayıcıları her istekte `provider.ignore` ile dışlanıyor. Testler eklendi.

| Model | Durum | ZDR sağlayıcıları | Dışlanan (Safety Retention) |
|---|---|---|---|
| `qwen/qwen3-embedding-8b` (bugünkü embed) | geçiyor | deepinfra, nebius, siliconflow | – |
| `google/gemma-3-12b-it` (bugünkü çeviri) | geçiyor | deepinfra, nextbit | – |
| `mistralai/mistral-small-24b-instruct-2501` (gösterge cevap modeli) | geçiyor | deepinfra | – |
| `qwen/qwen3-reranker-8b` | geçiyor | fireworks | – |

Hesap ayarındaki "ZDR only"yi siz açacaksınız; koddaki kontrol ondan bağımsız çalışıyor.

## 1. Adaylar (ilk tur), kimlikler OpenRouter'dan doğrulandı (2026-11-05)

| Aday | Kesin kimlik | ZDR | Ölçümde sabitlenecek sağlayıcı | Fiyat (USD / 1M token, giriş / çıkış) | Düşünme kapatma |
|---|---|---|---|---|---|
| Gemma 4 26B A4B | `google/gemma-4-26b-a4b-it` | geçiyor; 13 ZDR sağlayıcısı, **`google-vertex` Safety Retention, dışlanıyor** | `deepinfra` (fp8) | 0,07 / 0,34 | `reasoning: {enabled: false}`; boş düşünce bloğu ayrıştırıcıda tolere edilir (§5) |
| Qwen3.6 35B A3B | `qwen/qwen3.6-35b-a3b` | geçiyor; 9 sağlayıcı | `deepinfra` (fp8) | 0,10 / 0,95 | `reasoning: {enabled: false}` |
| GPT-5.4 mini | `openai/gpt-5.4-mini` | geçiyor; **yalnız `azure`** (openai'nin kendi uç noktası ZDR listesinde yok) | `azure` | 0,75 / 4,50 | `reasoning: {effort: "none"}` |
| Mistral Small, en yeni (referans) | `mistralai/mistral-small-2603` | geçiyor; yalnız `mistral` (zdr/eu/us) | `mistral` | 0,15 / 0,60 | `reasoning: {effort: "none"}` |
| Taban: qwen2.5:7b (yerel) | Ollama `qwen2.5:7b` (kurulu) | yerel, bulut yok | – | 0 | düşünme yok |

- Dört adayın hepsi ZDR'den geçiyor, çıkarılan aday yok.
- Kimlikler, sağlayıcılar ve fiyatlar koşudan hemen önce yeniden doğrulanacak (ZDR listesi değişebiliyor). O sırada ZDR'den geçmeyen aday çıkarılıp not edilecek.
- Seçilen dört sağlayıcının hepsi `structured_outputs` ve `response_format` destekliyor; şema, pipeline'ın `ANSWER_SCHEMA`'sı.

**Düşünmenin kapalı olduğunun doğrulanması:** Koşudan önce her modele 1 deneme çağrısı gidecek. Kontrol edilecekler:
- `usage.reasoning_tokens == 0`, ya da alan yok.
- Yanıtta düşünce metni yok.

Kapanmayan model koşulmayacak, size sorulacak.

## 2. Sağlayıcı kaydı ve aynı sağlayıcıda karşılaştırma

- Her model için sağlayıcı sabitlenecek: `provider: {order: [<sağlayıcı>], allow_fallbacks: false}`, ZDR kısıtı ve `ignore` ile birlikte. Her yanıttaki `provider` alanı kaydedilecek.
- Beklenenden farklı sağlayıcıdan gelen yanıt varsa o yanıt tablodan çıkarılıp sayılacak; ölçüm aynı sağlayıcıda yinelenecek.
- **Açık modeller aynı sağlayıcıda.** Gemma 4 ve Qwen3.6, ikisi de DeepInfra fp8'de koşacak; aralarındaki süre farkı sağlayıcıdan değil modelden gelsin diye.
- **Kapalı modeller tek sağlayıcılı.** GPT-5.4 mini (Azure) ve Mistral (Mistral) başka bir sağlayıcıda sunulmuyor. Süreleri bu yüzden açık modellerle doğrudan karşılaştırılabilir değil; raporda ayrı işaretlenecek.

## 3. Arama sabit

Arama, uygulamanın varsayılan yolu: bge-m3 + BM25, reranker kapalı (`PILOT_RERANK_PROVIDER=none`). Koleksiyon `manuals` (gerçek korpus, 4235 parça). İlke dışı kurallar bayrağı kapalı (`PILOT_DOC_SPECIFIC_RULES=0`, varsayılan).

Ölçüm `pipeline.soru_cevapla`'nın kendisiyle yapılacak. Yalnız `chat_json` ölçüm aracında buluta yönlendirilecek; uygulamaya bir şey bağlanmayacak.

Arama sonuçları her soru için bir kez hesaplanıp önbelleğe alınacak, böylece bütün modeller aynı 5 kaynağı görecek. Kaynak listesi ve sırası sonuç dosyasına yazılacak.

## 4. Soru setleri ve onay durumu

| Set | Onay | Cevaplı | "Bulunamadı" | Netleştirme | Kullanım |
|---|---|---|---|---|---|
| `questions` | onaylı | 13 | 3 (Q08, Q10, Q18) | 2 | evet |
| `questions_ek` | onaylı | 12 | 1 (Q31) | 1 | evet |
| `sekil_sorular` | onaylı | 12 | 0 | 0 | evet |
| `aday_sorular` | **onaysız** (`dogrulandi: false`) | 123 | **17 (A114–A130)** | 15 | evet; raporda ayrı sütun, "geçici" |
| `gorulmemis_juki` | onaylı, **ayrı tutulan** | 12 | 2 | 0 | **hayır**; ayar seçildikten sonra tek doğrulama |

**"Bulunamadı" seti 21 soru (%48'in ölçüldüğü set).** 4'ü onaylı, 17'si onaysız 155'in içinde (A114–A130). Bunların 4'ü model çağrılmadan kuralla çıkıyor: Q08 ve Q18 yabancı marka, A117 ve A119 kod yok. Modelin karar verdiği soru 17.

Bu küçüklükte bir sette bir soru yaklaşık 5 puan ediyor. %90 hedefini ölçmek için yeterli değil; büyütme önerisi §8'de.

## 5. Metrikler

Her model için iki sütun verilecek: onaylı ve onaysız (geçici).

| Metrik | Tanım |
|---|---|
| **Doğru "bulunamadı" oranı** | 21 cevapsız sorudan herhangi bir "bulunamadı" çıkışı alanlar. **Kural çıkışları ve model çıkışları ayrı sayılır** (§6). Asıl ölçüt, modelin karar verdiği 17 soruda modelin "bulunamadı" demesi. Netleştirme ya da cevap yanlış sayılır. Bugünkü tanımla aynı olduğu için %48 ile karşılaştırılabilir. |
| **Doğrulanmış görünen yanlış cevap** | Cevapsız soruda cevap üretilip "✓ doğrulandı" ya da "⚠ kısmen" rozeti alması. K1 hedefi 0. |
| **Yanlış ret oranı** | Cevaplı sorularda modelin "bulunamadı" demesi. İkiye ayrılır: (a) doğru kaynak ilk 5'te vardı, model reddetti (model hatası); (b) arama doğru kaynağı getirmedi, model reddetti (doğru davranış, arama hatası). |
| **Kaynağa dayanma** | `verify.py`'nin kontrolleri: alıntı birebir kaynakta, cevaptaki sayılar alıntıda, tolerans tam, atıflar geçerli. Rozet dağılımı (✓ / ⚠ / ✖). Ek olarak, beklenen ifadesi olan cevaplı sorularda (onaylı 21, onaysız 92) beklenen değerin cevapta geçme oranı. |
| **Kaynak sayfa doğruluğu** | Cevabın alıntı yaptığı kaynak numaralarının parçaları, beklenen doküman ve sayfayla (`kabul` / `expect_pages`, `is_match`) eşleşiyor mu. "Alıntılanan kaynaklardan en az biri doğru" ve "bütün alıntılar doğru" ayrı verilir. |
| **İlk token p50 / p95** | Akışlı çağrı, istek başından ilk içerik tokenine. §9.3 eşikleriyle: 1,2 sn (hedge) ve 1,5 sn (yedek sağlayıcı) altında kalanların oranı; toplam süre p50/p95 ve 20 sn sınırını aşan sayısı. |
| **JSON sorunları (ayrı metrik)** | Ayrı sayılacak dört durum: boş içerik, yarıda kesilen JSON (`finish_reason: length` ya da sonu eksik), ayrıştırılamayan JSON, şema dışı JSON (zorunlu alan eksik). Ayrıştırıcı önce kabul edilen düşünce bloklarını atar (Gemma 4'ün boş düşünce bloğu, `<think></think>`, kanal işaretleri), sonra ilk JSON nesnesini okur. Atılan blok ayrıca sayılır. |
| Sağlayıcı, token, maliyet | Her çağrıda: sağlayıcı, giriş/çıkış/düşünce tokeni, `usage.cost`. |
| **Hata ve hız sınırı** | Çağrı başına HTTP hatası; özellikle 429. 2026-11-05 süre sınırı ölçümünde gösterge model (tek ZDR sağlayıcılı mistral-small 2501) 160 sorunun 11'inde 429 verdi ve aynı sağlayıcıya giden hedge de aldı. Tek ZDR sağlayıcılı adaylarda (GPT-5.4 mini: Azure, Mistral Small 2603: Mistral) yedek sağlayıcı yok: seçim ölçütü olarak raporlanır. 429 alan soru 30 sn sonra bir kez yinelenir, iki deneme ayrı sayılır. |

## 6. Kural çıkışları ayrı

Model çağrılmadan dönen çıkışlar model sonuçlarına karışmayacak. Ayrı sayılacak çıkışlar:
- `yabanci_marka`
- `kod_yok`
- arama öncesi netleştirme
- konu belirsiz
- arama sonrası netleştirme

Bunlar modelden bağımsız olduğu için bir kez hesaplanacak. Ölçüm, ilke dışı kurallar bayrağı **kapalıyken** (varsayılan) yapılacak. Bayrağın açık/kapalı farkı ayrı raporda: [asama4_ilke_bayragi_10k](../b4/asama4_ilke_bayragi_10k_2026-11-05.md).

## 7. Taban: qwen2.5:7b (yerel)

%48, yerel qwen2.5:7b ile (Ollama, CPU) 21 soruda ölçüldü. Bu model de adaylarla aynı sette, aynı arama sonuçlarıyla ve aynı metriklerle koşulacak.
- İlk token süresi dizüstünde ölçülür ve üretimi temsil etmez; raporda ayrı işaretlenecek.
- Süre tahmini soru başına 50–140 sn, yaklaşık 177 soruda **4–5 saat**. Gece, Görev Zamanlayıcı'dan (pencere açmadan) koşulacak.

## 8. Öneri: "bulunamadı" setinin büyütülmesi (otomatik soru üretilmeyecek, önce onay)

21 soruda %90'ı %48'den ayırt etmek mümkün, ama ±1 soru ±5 puan ediyor. Önerim **+40 soru (toplam ~60)**, tür başına 6–8:
1. **Aynı belgede komşu ama yok olan değer:** "S-7300A'nın ağırlığı?", "ceket kumaşının yıkama sıcaklığı?" (cevaplı sorulara en çok benzeyen tür).
2. **Başka modelde/üründe olup sorulanda olmayan bilgi:** S-7300B'de olup S-7300A'da olmayan, pantolonda olup cekette olmayan.
3. **Belgedeki terimle sorulan ama farklı şey isteyen:** terim eşleşir, cevap yok.
4. **Alan dışı ama tekstil benzeri:** "dokuma makinesinde atkı kopması" (Granovsky'nin kapsamı dışında kalan).
5. **İngilizce cevapsız sorular** (bugün hepsi Türkçe).
6. **Kural çıkışına girmeyen kodlar:** yanlış biçimli kodlar ya da kapsam dışı bir belgede geçen kodlar.

Yöntem: Sorular insan tarafından yazılacak; isterseniz bir model aday sorular önerir, o da yalnız size sunulmak üzere. Her sorunun cevapsız olduğu iki yolla kontrol edilecek: korpusta arama (`bench/aday_inceleme.py`) ve uzman onayı. Set `dogrulandi: false` olarak girecek, onaydan sonra ölçümde sayılacak. Bu turun parçası değil; onayınızla ayrı iş.

## 9. Bütçe ve maliyet tahmini

Tahmin, bugünkü uçtan uca ölçümün token sayılarından: giriş medyanı 2576 token (en fazla 3072), çıkış medyanı ~200 token (en fazla 591). Hesapta 2800 giriş ve 300 çıkış tokeni kullanıldı. Modele giden soru sayısı ~177: 160 cevaplı + 17 cevapsız.

| Model | Tahmini maliyet, tam set (~177 çağrı) |
|---|---|
| Gemma 4 26B A4B (DeepInfra) | ~0,05 USD |
| Qwen3.6 35B A3B (DeepInfra) | ~0,10 USD |
| GPT-5.4 mini (Azure) | ~0,61 USD |
| Mistral Small 2603 (Mistral) | ~0,11 USD |
| qwen2.5:7b (yerel) | 0 |
| Düşünme kontrolü çağrıları (4 model) | < 0,01 USD |
| İkinci süre turu (30 soru × 4 model, başka saatte; kuyruk dakikalar içinde değişiyor) | ~0,15 USD |
| **Toplam tahmin** | **~1,0 USD** |

**Bütçe sınırı: 1,5 USD.** Koşu, harcama önceki çağrılarla birlikte sınırı geçerse durur. Sınıra en çok GPT-5.4 mini yaklaştırıyor. Ölçümlerin hepsi ZDR'li; LLM ile değerlendirme (hakem model) yok, değerlendirme kodla (`verify.py`, `is_match`) yapılacak.

## 10. Koşu sırası (onaydan sonra)

1. ZDR ve kimlikleri yeniden doğrula; her modele 1 düşünme kontrolü çağrısı.
2. Arama sonuçlarını önbelleğe al (bulut çağrısı yok).
3. 4 bulut modeli sırayla, her biri tek sağlayıcıda; sonra ikinci süre turu (30 soru, başka saatte).
4. qwen2.5:7b, gece, arka planda.
5. Tek rapor: model başına metrikler (onaylı/onaysız ayrı), kural çıkışları ayrı, JSON sorunları, sağlayıcı ve maliyet. Sonra commit; push sizin onayınızla.

## 11. Açık konu: makine ailesinin kaynağı (Adım 2'den sonra konuşulacak)

Bugün "S-7300" aile grubu ve `BRAND_ALIASES` elle yazılmış ve bayrakla kapalı (`PILOT_DOC_SPECIFIC_RULES`). Bayrak kapalıyken aynı ailenin iki modelinin kılavuzu aynı bölümü içerdiğinde "hangi model?" netleştirmesi sorulmuyor (ölçüm: [asama4_ilke_kurallari_10k](../b4/)). İki seçenek var:
1. **Otomatik türetme:** Aile, aynı markanın model adlarının ortak önekinden çıkarılır (s7300 ⊂ s7300a, s7300b).
2. **Yükleme sırasında ürün/model alanı:** Dokümanı yükleyen kişi ürün ailesini kayıtta seçer.

İkisinde de **yanlış aile oranı** ölçülmeli: aile sayılıp aslında farklı ürün olan, ve aile sayılmayıp aynı ürün olan çiftler. Bu şimdi yapılmayacak.

**`BRAND_ALIASES` da bu açık konunun parçası (karar 2026-11-05):** Silinmedi, bayrak kapalı. Tablo, marka adlarını ve aynı ürünün eş adlarını elle eşliyor. Netleştirme etkisinin neredeyse tamamı ondan geliyor: beklenen netleştirme varsayılan yolda 2 → 10/18, adayda 4 → 14/18. §11'in çözümü ölçülürken **taban olarak** kullanılacak: Otomatik türetme ya da yükleme alanı, bugünkü elle yazılmış tabloyla (bayrak açık) aynı soruda karşılaştırılır. Metrikler:
- netleştirme soruldu mu;
- **seçenekler doğru mu**: seçenekler sorunun ayırt edilmesi gereken ürünleri mi (`expect_docs`). Q07'de soru soruluyor ama seçenekler aynı ailenin modelleri; ceket/pantolon değil.
- yanlış aile oranı.

Seçenek metriği ölçüm aracına eklendi (`bench/doc_rules_diff.py`, 2026-11-05). İlk sonuç: BRAND_ALIASES açıkken varsayılan yolda netleştirmelerin 9/10'u doğru seçenekli (Q07 yanlış: S-7300A/B), adayda 14/14 ([B4 özet §10.7](../b4/ozet_dondurulan_aday_2026-11-03.md)).

## 12. Plan (koşulmadı): Gemma 4 üretim sağlayıcıları

İlk tur Gemma 4'ü **DeepInfra fp8** üzerinde ölçtü. ZDR'li 13 sağlayıcının çoğu bf16. Aşağıdaki gecikme ve hız değerleri OpenRouter'ın son 30 dakikalık anlık değerleri (2026-11-05 ~13:30); saatten saate değişir, kendi ölçümümüzün yerini tutmaz.

| Sağlayıcı (ZDR) | nicemleme | giriş / çıkış USD/M | ilk token p50 / p90 | hız p50 (tk/sn) | json_schema (structured_outputs) | 30 dk / 1 gün erişilebilirlik | not |
|---|---|---|---|---|---|---|---|
| **NextBit** | bf16 | 0,09 / 0,30 | 306 ms / 728 ms | 42 | var | 100 | önerilen |
| **Parasail** | bf16 | 0,13 / 0,40 | 599 ms / 1,37 sn | 61 | var | 100 | önerilen |
| **Venice** | bf16 | 0,13 / 0,40 | 706 ms / 1,21 sn | 44 | var | 100 | önerilen; çıktı sınırı 16k |
| DeepInfra | **fp8** | 0,07 / 0,34 | 420 ms / 1,34 sn | 41 | var | 100 | ilk turun sağlayıcısı (referans) |
| SiliconFlow | fp8 | 0,14 / 0,40 | 1,13 sn / 2,42 sn | 38 | var | 100 | fp8 ikinci seçenek |
| PrimeIntellect | bf16 | 0,036 / 0,108 | 525 ms / 9,40 sn | 43 | var | 100 / 95,8 | kuyruk uzun |
| DekaLLM | bf16 | 0,06 / 0,33 | 947 ms / 3,85 sn | 58 | **yok** | 100 | şema yok |
| Io Net | bf16 | 0,09 / 0,31 | 731 ms / 1,54 sn | 43 | **yok** (response_format da yok) | 100 | şema yok |
| CoreWeave | bf16 | 0,10 / 0,30 | 1,30 sn / 9,47 sn | 18 | var | 70 | erişilebilirlik düşük |
| Novita | bf16 | 0,13 / 0,40 | 6,67 sn / 17,5 sn | 48 | yok | 0 | o an erişilemiyordu |
| AkashML | fp4 | 0,07 / 0,24 | 916 ms / 1,88 sn | 51 | var | 100 | fp4 |
| Makora, Cloudflare | bilinmiyor | — | 1,05 sn / 9,26 sn; 2,29 sn / 8,13 sn | — | — | 100 | nicemleme açıklanmamış |

Google Vertex Safety Retention'lı olduğu için dışarıda (§0); Darkbloom ZDR listesinde yok.

**Öneri: NextBit, Parasail, Venice (üçü bf16, aynı nicemleme).** Üçünde de ilk token p90 düşük, structured outputs var, erişilebilirlik 100. Uygulamada `provider.order` bu üçü olur, `allow_fallbacks` yalnız bu üçü arasında. fp8'e düşmemesi için `quantizations: ["bf16"]` kullanılır. 429 durumunda bir sonrakine geçilir; tek sağlayıcı riskini bu kapatır. Aynı nicemleme tercih edildi: Sağlayıcı değişince cevap kalitesi değişmesin.

**Kısa kalite ve süre ölçümü (koşulmadı):**
1. Araç: `bench/answer_models.py`'e sağlayıcı ve nicemleme parametresi (yalnız ölçüm aracı). Her sağlayıcı ayrı koşu, `allow_fallbacks: false`. Arama, istem ve şema aynı (§3, ek c).
2. Kalite: tam set (177 çağrı), NextBit, Parasail ve Venice'te. Referans, DeepInfra fp8 ilk tur sonucu. Karşılaştırılacaklar:
   - doğru "bulunamadı" ve doğrulanmış görünen yanlış (cevapsız 17 soru);
   - ✓/⚠/✖ ve beklenen değer (onaylı ve onaysız ayrı);
   - JSON sorunu;
   - aynı soruda farklı karar sayısı (sağlayıcılar arası tutarlılık).
3. Süre: 30 soru × 4 sağlayıcı (DeepInfra dahil), iç içe sırayla, günün iki farklı saatinde. Ölçülen: ilk token p50/p95, toplam p95, 429 ve hata.
4. Tahmini maliyet: kalite 0,048 + 0,068 + 0,068 = **0,18 USD**, süre 2 × 0,039 = **0,08 USD**. Toplam **~0,26 USD**. Bugünkü harcama 1,08 USD, 16:30 süre turu tahmini 0,09 USD; bu ölçümle ~1,43 USD olur, 1,5 USD sınırının altında ama yakın. Onaylı ve büyütülmüş setteki nihai tur için ayrı bütçe gerekecek.

## 13. Cevap uzunluğu: ortak sınır (öneri: şimdilik yok)

Kayıtlardan ([adim2_analiz_2026-11-05.md](adim2_analiz_2026-11-05.md) §4), çıktı tokeni bütün JSON (alıntılar, cevap, sesli metin):

| Model | çıktı tokeni p50 / p95 | ✖ oranı (öneri A ile) < 200 / 200–399 / ≥ 400 tk |
|---|---|---|
| Gemma 4 | 205 / 424 | %4 / %11 / %25 |
| Qwen3.6 | 228 / 450 | %6 / %18 / %16 |
| GPT-5.4 mini | 217 / 440 | %3 / %6 / %17 |
| Mistral 2603 | 230 / 519 | %18 / %29 / %31 |

- Hiçbir cevap 700 token sınırına değmedi.
- Cevap metni dört modelde benzer (p95 370–445 karakter). JSON'un ~%40'ı alıntılar.
- Uzun cevaplarda ✖ daha sık, ama uzun cevaplar çok adımlı ve çok parçalı sorulardan geliyor. Uzunluk sebep olmayabilir.
- Gemma 4'ün toplam süre p95'i (10,3 sn) uzunluktan değil, DeepInfra'nın hızından (~41 tk/sn) geliyor. GPT-5.4 mini aynı uzunlukta 3,2 sn. Parasail (61 tk/sn) bunu kısaltır (§12).

**Öneri:** Bir sonraki turda ortak uzunluk sınırı **konmasın**. `max_tokens` ile kesmek yarım JSON üretir. İstemle sınırlamanın etkisi bu veriyle ayrıştırılamıyor.

İstenirse ayrı bir A/B olarak ölçülür (koşulmadı). Bütün modellerde aynı sistem talimatına tek bir cümle eklenir: "Cevap en fazla 4 cümle; adım sorularında en fazla 6 madde." `max_tokens` 700'de kalır. Ölçülecekler: ✖, beklenen değer cevapta, yanlış ret, toplam süre p95. Kural: Beklenen değer düşerse uygulanmaz. Maliyet, tam setin bir kez daha koşulması kadar: ilk turda 4 model 0,54 USD tuttu, GPT-5.4 mini hariç ~0,2 USD.

## 14. Plan (koşulmadı): Gemma 4 çeviri modeli olarak (yalnız ölçüm aracında)

Neden: Süre sınırı ölçümünde grup 1'i (arama öncesi paralel adımlar) **çeviri belirliyor**: 149 sorunun 107'sinde (%72) en uzun bekleme çeviriydi. Gemma 3 12B çeviri süresi p50 818 ms, p95 2,69 sn; 1,2 sn sınırını %37'sinde aştı ([asama4_sure_siniri](../b4/asama4_sure_siniri_2026-11-05.md), "Grup 1 ayrıştırma").

1. Araç:
   - `bench/translate_bm25.py`, `--model google/gemma-4-26b-a4b-it`.
   - Yalnız ölçüm aracında sağlayıcı sabitleme ve düşünme kapatma (`reasoning.enabled false`). `CloudChat` uygulamada değişmez.
   - Sağlayıcı §12'deki seçimle aynı (NextBit bf16).
2. Kalite (BM25 isabeti):
   - Aynı 160 soru, 10k.
   - `bench.triple_fusion --bm25-translations` ile Gemma 3 ve Gemma 4 çevirileri karşılaştırılır: BM25 kolu tek başına hit@1/hit@5, üçlü füzyon hit@1/hit@5.
   - Ayrıca birebir aynı çeviri sayısı ve farklı çevirilerin listesi (elle okunur).
3. Süre:
   - Çağrı başına süre p50/p95 ve 1,2 sn sınırını aşma oranı.
   - Gemma 3 ile **aynı saatte**, iç içe sırayla, günün iki farklı saatinde.
4. Tahmini maliyet:
   - Gemma 3'ün aynı seti 350 çağrıda 0,0038 USD tuttu. Gemma 4 NextBit fiyatıyla ~0,006 USD/koşu.
   - Toplam: 2 saat × (Gemma 4 + Gemma 3) ≈ **0,02–0,03 USD**. Arama değerlendirmesi yerel (Qdrant), bulutsuz.
5. Uygulamaya bağlanmaz. Sonuç B4 özet raporuna (§10) yazılır.
