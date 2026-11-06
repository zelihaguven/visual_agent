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

## 11. Netleştirme: aile kavramı gerekmiyor (güncelleme 2026-11-05 akşam)

**Karar:** Makine "ailesi" kavramı gerekmiyor.
- Model, kaynaklarda doküman ve ürün adını zaten görüyor (`format_sources`: `<kaynak doküman="brother-s7300a" ürün="S-7300A düz dikiş makinesi" …>`).
- İstemin 6. maddesi, soruda ürün belli değilse ve değerler ürüne göre değişiyorsa netleştirmeyi zaten istiyor.
- Aşağıdaki eski görüş (otomatik türetme / yükleme alanı ile aile) bu yüzden kapandı. Kaldığı yer yalnız "ürün" alanının kaynağı.

**Önceki netleştirme ölçümü geçerli değil.** `bench/doc_rules_diff.py` modeli çağırmadan yapıldı: Yalnız kural katmanının netleştirmesini ölçtü. Modelin netleştirme sorup sormadığı ve seçeneklerinin ekrana gelip gelmediği hiç ölçülmedi.

**Bulgu: `clarify_options` bugün ürün adlarını atıyor** (kayıtlardan, model çağrısı yok):
- Netleştirme beklenen 18 sorunun 15'inde netleştirme modele kalıyor. Kalan 3'ü (A140, A142, A143) kural katmanında "Ceket / Pantolon" seçenekleriyle soruluyor.
- Bu 15 soruda bulunan kaynakların ürün adlarını ("S-7300A düz dikiş makinesi", "Pantolon"…) ve doküman kimliklerini `clarify_options`'a verdiğimde **hepsi atıldı (15/15 soruda 0 seçenek kaldı)**.
- Neden: `clarify_options` seçeneği yalnız parça metninde arıyor (`pipeline.py`: `sources = {no: chunk["text"]}`). Ürün adı ve doküman kimliği, modelin gördüğü başlıkta var, metinde yok.
- 2'den az seçenek kalınca pipeline netleştirmeyi hiç göstermiyor (`atlanan_netlestirme`). Yani model doğru "hangi ürün?" sorusunu sorsa bile kullanıcıya ulaşmıyor.
- Adım 2 kayıtlarında modelin sorduğu 18 netleştirmenin hepsi tek doküman içi varyant (Type I/II, beden, reçete); ürün adı seçeneği hiç geçmiyor. O turda netleştirme beklenen sorular sete alınmamıştı.

**Ölçüm planı (koşulmadı; model çağrısı, onayınızla):** Netleştirme beklenen 18 soru, **Gemma 4 ile**, arama uygulamanın varsayılan yolu, dört durum:

| Durum | Açıklama |
|---|---|
| (a) taban | `BRAND_ALIASES` açık (bugünkü elle yazılmış tablo) |
| (b) | ilke dışı kurallar kapalı (varsayılan) |
| (c) | kurallar kapalı + `clarify_options` seçenekleri bulunan kaynakların **doküman/ürün adıyla da** eşleştirir (genel; belgeye özel değil) |
| (d) | (c) + netleştirme beklenmeyen sorularda gereksiz netleştirme (160 cevaplı + 21 "bulunamadı" soru) |

- Metrikler:
  - netleştirme soruldu mu;
  - seçenekler doğru mu (`expect_docs` ile; `doc_rules_diff`'teki metrik);
  - gereksiz netleştirme oranı (d).
- Ayrıca soruldu ama `clarify_options` yüzünden gösterilmedi sayısı.
- **Tahmini maliyet:** (a)–(c) 3 × 18 = 54 çağrı + (d) ~181 çağrı = ~235 çağrı × 0,00024 USD ≈ **0,06 USD** (Gemma 4, DeepInfra fiyatıyla).
- **Karar kuralı: (c) tabanı (a) yakalıyorsa** (soruldu ve seçenekler doğru en az aynı) ve (d)'de gereksiz netleştirme artmıyorsa `BRAND_ALIASES` ve S-7300 grubu silinir.

**Sonuç (koşuldu 2026-11-05 15:40–15:55; Gemma 4, DeepInfra; 212 çağrı, 0,050 USD; [netlestirme_modelle_2026-11-05.md](netlestirme_modelle_2026-11-05.md)):**

| Durum | netleştirme soruldu (18) | seçenekler doğru | model sordu ama gösterilmedi |
|---|---|---|---|
| (a) BRAND_ALIASES açık (taban) | 13 | 12 (Q07 yanlış: S-7300A/B) | 1 |
| (b) kurallar kapalı | 3 | 3 | 4 |
| (c) kapalı + seçenek ürün/doküman adıyla | 3 | 3 | 5 |
| (d) netleştirme beklenmeyen 181 soru, (c) ile | gereksiz netleştirme **0** | – | 1 |

- **(c) tabanı yakalamıyor (3/18'e karşı 13/18): kurala göre `BRAND_ALIASES` ve S-7300 grubu silinmez.**
- Tabandaki 13'ün çoğu modelden değil kural katmanından geliyor (aile → model çağrılmadan "hangi model?").
- **Neden (c) işe yaramadı:** Gemma 4, S-7300 sorularında doğru soruyu soruyor ("Hangi makine modeli için? S-7300A mı yoksa S-7300B mi?"). Ama seçenekleri soru metnine yazıp `netlestirme_secenekleri`'ni boş bırakıyor ve bir cevap da yazıyor. Pipeline bu durumda netleştirmeyi gösterilmeden atlıyor (`asks and len(options) < 2`). Süzülecek seçenek olmadığı için (c) etkisiz.
- Kalan 10 soruda model hiç sormuyor; iki ürünün değerini birlikte ya da birini veriyor.
- **Olası genel düzeltme (e), ölçülmedi:** Model netleştirme soruyor ama 2'den az seçenek kalıyorsa ve kaynaklarda ≥ 2 farklı doküman varsa, bulunan dokümanlar düğme olarak sunulsun. Bu, cevapsız netleştirme yolunun bugünkü davranışı.
- Kayıtlardan tahmin: (c)+(e) en fazla 8/18. Tabana yine yetmiyor; model sormadığı 10 soru için istem ya da şema (C'de ayrı netleştirme öğesi) gerekir. (e) ve şema etkisi nihai turda ölçülür (§15), BRAND_ALIASES o zamana kadar bayrakla kalır.

**"Ürün" alanı nereden geliyor:**
- Bugün kayıtta elle yazılı (`pilot/registry.py`, `DocMeta(..., product="Ceket", ...)`).
- Gerçek yüklemede otomatik çıkarma güvenilir değil:
  - PDF metadata 9 test dokümanının 7'sinde boş; doluysa da dosya adı ("GL-PD-14-04A.pdf").
  - İlk sayfa makine kılavuzlarında model adını veriyor ("S-7300A", "MO-6800S"); ama taranmış belgelerde OCR bozuk ("GLlPD 07-14A"), kitaplarda (Granovsky, Strickland) ürün yok.
- **Öneri:** Yükleme formunda zorunlu "ürün / model" alanı. Form ilk sayfadan bir öneri doldurur, yükleyen kişi onaylar ya da düzeltir.

---

*Önceki görüş (kapandı):* Bugün "S-7300" aile grubu ve `BRAND_ALIASES` elle yazılmış ve bayrakla kapalı (`PILOT_DOC_SPECIFIC_RULES`). Bayrak kapalıyken aynı ailenin iki modelinin kılavuzu aynı bölümü içerdiğinde "hangi model?" netleştirmesi sorulmuyor (ölçüm: [asama4_ilke_kurallari_10k](../b4/)). İki seçenek var:
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

**Karar (2026-11-05): şimdi koşulmuyor, nihai tura taşındı.** Nihai turda (onaylı ve büyütülmüş set):
- Gemma 4 doğrudan **NextBit, Parasail ve Venice (bf16)** üzerinde koşulur.
- **DeepInfra fp8 referans** olarak kalır.
- Diğer modeller kendi ZDR sağlayıcılarında.
- Yukarıdaki ölçüm adımları (kalite tam set, süre iki saatte iç içe) o turun parçasıdır.

**Nihai tur için ayrı bütçe gerekiyor.** Bu turun 1,5 USD sınırı ön elemeye ait; bugünkü harcama 1,08 USD ve 16:30 turuyla ~1,17 USD olacak. Nihai turun kaba tahmini, büyütülmüş set ilk turdakinin ~1,5 katıysa:
- Dört model + taban, tek sağlayıcıda: ~0,8 USD (GPT-5.4 mini ~0,5).
- Gemma 4'ün 3 bf16 sağlayıcısı: ~0,3 USD.
- Süre turları: ~0,15 USD.
- Yeni cevap şeması varsa (§15) aynı tur o şemayla koşulur, ek maliyet yok.

Toplam **~1,3 USD**. Set büyüklüğü kesinleşince yeniden hesaplanıp onayınıza sunulur.

## 14. Plan (onaylandı 2026-11-05): Gemma 4 çeviri modeli olarak (yalnız ölçüm aracında)

**Onayla gelen değişiklikler:**
- **Üç kol, model etkisi ve sağlayıcı etkisi ayrışsın diye:**
  - Gemma 3 DeepInfra
  - Gemma 3 NextBit
  - Gemma 4 NextBit
- **Süre ölçütü çağrının tamamı** (ilk token değil; çeviri bitmeden BM25 başlayamaz). Başarı ölçütü p95 ve 1,2 sn sınırını aşma oranı; p50 de raporlanır.
- **Çeviri çıktı tokeni p50/p95** kaydedilir.
- Uygulamaya bağlanmaz; sonuç B4 özet §10'a.

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

## 15. Öneri (koşulmadı): yapılandırılmış cevap şeması

### 15.0 Güncelleme 2026-11-05 akşam: önerilen seçenek **C**, karşılaştırma için B

| Seçenek | `cevap` | Not |
|---|---|---|
| A (aşağıdaki ilk öneri) | `[{metin, kaynaklar: [no]}]`, alıntılar ayrı `alintilar` alanında | Cümlenin sayısı yalnız kaynak numarasıyla bağlı; hangi alıntı belli değil |
| B | `alintilar: [{no, kaynak_no, metin}]` numaralı; `cevap: [{metin, alinti: [no]}]` | Karşılaştırma için tutuluyor |
| **C (önerilen)** | `[{alinti: {kaynak_no, metin}, metin}]`: her cümle kendi alıntısını **hemen önünde** taşır | Alıntı ile cümle aynı öğede; akışta cümle cümle doğrulanabilir |

**C ile `verify.py`:**
- Her cümlenin sayıları **yalnız kendi alıntısında** aranır (bugün bütün alıntıların birleşiminde).
- `sesli_metin`'deki sayılar da kontrol edilir: bütün cümlelerin alıntılarının birleşiminde.
- Alıntı birebir kontrolü, tolerans, tekrar ve yabancı alfabe kontrolleri öğe başına.
- Atıf ve liste numarası ayıklama gerekmez: metinde `[n]` yok, sıra dizinin sırası.

**Akış sırasında doğrulama (C'nin asıl kazancı):**
- Model öğe öğe yazar. Her öğe (alıntı + cümle) tamamlanınca doğrulanır; geçen cümle hemen gösterilir ve seslendirilir.
- Yarıda kesilen cevapta (süre sınırı, bağlantı, JSON kesilmesi) tamamlanmış ve doğrulanmış cümleler geçerli kalır.
- Bugünkü şemada bütün JSON bitmeden doğrulama yapılamıyor.

**Yeni süre metriği: kullanıcının gördüğü ilk doğrulanmış cümle (p50/p95).**
- "İlk token"dan ayrı raporlanır.
- Bugünkü şema için kayıtlardan tahmin edildi (yeni koşu yok; araç: kayıttaki ham çıktıda `"cevap"` alanının konumu ve çağrının kendi token hızı):
  - **cevap ilk kelimesi** = ilk token + (cevap alanından önceki JSON, yani alıntılar) / token hızı;
  - **ilk cümle sonu** = cevabın ilk cümlesinin bittiği an. Bugünkü şemada doğrulama tüm JSON'u bekliyor; bu değer C'de olabilecek en iyi durumun yaklaşığı.

| Model | Tur | ilk token p50 / p95 | cevap ilk kelimesi p50 / p95 | ilk cümle sonu p50 / p95 |
|---|---|---|---|---|
| Gemma 4 (DeepInfra) | ana | 386 ms / 871 ms | 1,39 / 4,72 sn | 2,02 / 5,76 sn |
| Gemma 4 | ikinci | 343 ms / 1,96 sn | 1,37 / 2,98 sn | 1,91 / 3,85 sn |
| Qwen3.6 (DeepInfra) | ana | 648 ms / 1,25 sn | 3,13 / 8,63 sn | 4,50 / 10,98 sn |
| Qwen3.6 | ikinci | 738 ms / 11,17 sn | 5,33 / 15,44 sn | 7,27 / 17,40 sn |
| GPT-5.4 mini (Azure) | ana | 765 ms / 1,40 sn | 1,19 / 2,28 sn | 1,31 / 2,15 sn |
| GPT-5.4 mini | ikinci | 753 ms / 1,06 sn | 1,14 / 1,90 sn | 1,30 / 2,11 sn |
| Mistral 2603 (Mistral) | ana | 449 ms / 1,01 sn | 1,07 / 2,53 sn | 1,25 / 2,25 sn |
| Mistral 2603 | ikinci | 468 ms / 897 ms | 1,00 / 2,38 sn | 1,26 / 2,68 sn |

Kapsam: cevaplı sorularda üretilen cevaplar. "İlk token" bu tabloda yalnız bu cevaplar için; rapordaki değer bütün çağrılar.
- Bugünkü şemada alıntılar cevaptan önce yazılıyor: ilk token ile cevabın ilk kelimesi arasında p50 ~0,4 sn (GPT-5.4 mini) ile ~2,5 sn (Qwen3.6) arası var.
- Gemma ve Qwen'de alıntılar uzun ve DeepInfra yavaş.

**Kayıtlardan: "sayı başka bir alıntıda var ama yanlış cümlede" (C'nin daha sıkı kontrolü kaç cevabı etkiler):**
- Bugünkü cevaplarda her cümlenin sayısı, cümlenin atıf yaptığı kaynağın alıntısında mı diye bakıldı. Atıf, cümle sonundaki noktadan sonra da yazılabiliyor; önceki cümleye bağlandı.

| Model (ana tur) | kendi alıntısında | **yanlış cümlede** (başka alıntıda var) | hiçbir alıntıda | atıfsız cümlede |
|---|---|---|---|---|
| Gemma 4 | 179 | **2** | 17 | 54 |
| Qwen3.6 | 214 | **5** | 37 | 36 |
| GPT-5.4 mini | 202 | **0** | 3 | 69 |
| Mistral 2603 | 134 | **1** | 9 | 220 |

- Yanlış cümle vakası nadir (0–5).
- C'de asıl değişecek olan **atıfsız cümleler**: her cümle kendi alıntısını taşımak zorunda. Bugün giriş ya da özet cümlesinde geçen sayılar (Mistral'de 220) C'de ya kendi alıntısıyla yazılır ya ✖ olur.

**Karar kuralı (nihai tur):**
- Bugünkü şema ile C, dört model + taban, aynı sorularda yan yana.
- **C'ye geçilir, eğer** ilk doğrulanmış cümle p95 kötüleşmiyorsa ve JSON hatası (şemaya uymama dahil) artmıyorsa.
- Şemaya zorlamanın (`response_format` json_schema) ilk istekteki ek süresi **sağlayıcı bazında** ölçülür: Aynı modelde şemalı ve şemasız ilk token, aynı sağlayıcıda iç içe.
- C'ye geçişte `verify.py`'den kalkacak yamalar aşağıdaki A metnindeki listeyle aynı.

### 15.1 İlk öneri (A)

**Neden:** `verify.py`'deki atıf ve sayı ayıklama yamalarının kaynağı, cevabın tek bir serbest metin olması ve atıfların metne gömülmesi. Doğrulayıcı aynı metinde hangi rakamın atıf, liste numarası, kod ya da değer olduğunu tahmin ediyor. Yamaların listesi:
- 16 Ekim: alıntı sonunda yarım atıf;
- liste numaraları;
- 5 Kasım: çoklu atıf, `<br>`, Markdown.

Her yeni model yeni bir biçim getiriyor. **A+B (2026-11-05) bu türden son yamadır.**

**Önerilen şema** (yalnız `cevap` değişir; diğer alanlar aynı):
```json
"cevap": [{"metin": "Dış görünür dikişlerde inç başına 11 (± 1) dikiş olmalıdır.", "kaynaklar": [1]},
          {"metin": "Overlok dikişlerinde 10 (± 2) dikiş olmalıdır.", "kaynaklar": [1, 2]}]
```
- Her öğe bir cümle ya da bir madde. `metin` içinde `[n]` olmaz.
- Liste numarası yazılmaz; sıra dizinin sırasıdır.
- `kaynaklar` boş olamaz (`minItems: 1`). `cevap` en fazla 8 öğe; `metin` en fazla 250 karakter.
- İstemde yalnız biçim değişir: "her cümleyi ayrı öğe yaz, dayandığı kaynak numaralarını `kaynaklar`a koy".

**`verify.py`:**
- Sayılar yalnız `metin`lerden okunur: atıf ve liste numarası metinde olmadığı için ayıklama gerekmez.
- Atıf geçerliliği `kaynaklar`dan okunur: her öğenin kaynakları geçerli kaynak numarası mı. Ayrıca bir öğenin sayıları, o öğenin kaynaklarından alıntılanan metinde mi (bugün bütün alıntılara bakılıyor; öğe bazında daha sıkı).
- Tolerans kontrolü, tekrar kontrolü (öğeler arası) ve yabancı alfabe kontrolü aynı kalır.

**Ekranda gösterim ve sesli metin:**
- Ekran: öğeler sırayla. Tek öğe paragraf; birden çok öğe numaralı liste (numara koddan). Her öğenin sonuna kaynak etiketleri `[1][2]`, koddan.
- Kaynak kartları `kaynaklar` birleşiminden (`app.cited_sources` bugün metinden ayıklıyor).
- `sesli_metin` model alanı olarak kalır; seslendirme kuralları (R15) aynı. Yedek yol, sesli metin yoksa ya da tolerans düşmüşse öğe `metin`lerinin birleşimidir; atıf temizliği gerekmez.

**Kaldırılabilecek yamalar** (şema geçişinden ve ölçümden sonra):
- `CITE_RE` ile cevap metninden atıf ayıklama, `MULTI_CITE_RE` / `split_cites` / `cites_in` / `strip_cites`;
- `LIST_MARK_RE` ve `<br>` işleme (yalnız cevap tarafı; alıntılar kaynak metni olduğu için sayı ayıklamada kod (`CODE_RE`) yine gerekir);
- `speech.py`'deki atıf silme;
- **16 Ekim yarım atıf (`CUT_CITE_RE`)**: alıntıda atıf yazma gerekçesi kalkıyor; istem "alıntıya atıf yazma" der, yine yazılırsa alıntı birebir tutmaz (✖).
- **Kalacaklar:** `_cut_quote_prefix` (300 karakter sınırında kesilen alıntı; atıfla değil uzunluk sınırıyla ilgili), `CODE_RE`, değer kanonikleştirme ve alıntıda yazıyla sayı (bunlar biçim değil anlam karşılaştırması).

**Geriye uyumluluk:**
- `verify` iki biçimi de kabul eder: `cevap` metinse bugünkü yol, diziyse yeni yol. Geçiş süresince ikisi de çalışır.
- Kayıtlı eski cevaplar ve eski ölçüm dosyaları yeniden puanlanabilir kalır.
- Uygulamada `answer["cevap"]` metin bekleyen yerler (app, `tables.variant_check`, denetim kaydı) tek bir yardımcıdan (`answer_text(answer)`) okur.
- Eski yol, yeni şema nihai turda geçince ve bir sürüm sonra kaldırılır.

**Yerel model (Ollama):**
- `format=<JSON şeması>` iç içe dizi ve nesneyi destekliyor (bugün `ANSWER_SCHEMA` böyle gidiyor).
- Ollama'nın şemadaki `maxLength`/`maxItems`'ı üretimde ne ölçüde uyguladığı denemede kontrol edilecek. Sınırlar her durumda `verify`'de de kontrol edilir.
- Önce taban qwen2.5:7b ile 20 soruda biçim denemesi (yerel, maliyetsiz).

**Ölçüm:**
- Adım 2 nihai turunda dört model + taban bu şemayla koşulur. Bugünkü şemayla aynı soruda karşılaştırma için ilk turun kayıtları referans.
- Ek metrik: şemaya uyma (öğe yapısı, boş `kaynaklar`, metinde `[n]` kalması) JSON metriğinin parçası. Bir model uymuyorsa bu metrikte görünür; ona özel yama yazılmaz (§16).

**Tahmini maliyet:**
- Şema denemesi: yerel, 0 USD.
- Bulutta tek başına bir ön deneme istenirse: 4 model × 30 soru ≈ 0,12 USD.
- Nihai turun kendisi zaten koşulacak (§12 notu); şema ek maliyet getirmez, yalnız çıktı tokeni ~%10 artabilir.

**Uygulama sırası (onaydan sonra):**
1. `verify` ikili biçim + testler.
2. İstem ve şema değişikliği yalnız ölçüm aracında.
3. Yerel deneme.
4. Nihai tur.
5. Sonuçlar iyiyse uygulamaya geçiş ve yamaların kaldırılması.

## 16. İlke (öneri): model değişikliği yalnız yapılandırma değişikliğidir

Cevap modelini değiştirmek yalnız yapılandırmadır (model kimliği, sağlayıcı listesi, düşünme kapatma parametresi).
- **Bir model ölçüm setinden kod değişmeden geçmiyorsa elenir.**
- Ona özel istem, ayrıştırıcı ya da doğrulama yaması yazılmaz.
- Biçim sorunları JSON ve rozet metriklerinde görünür. Ortak bir hata birden çok modelde görülürse genel çözüm şemadır (§15), modele özel yama değildir.

PRD açık kararlar listesine **A11** olarak önerildi ([docs/PRD.md](../../../../docs/PRD.md)).

## 17. Ertelenen ölçümler (2026-11-05 akşamı; bilgisayar gece açık kalmıyor)

Bütün `VisualAgent_*` zamanlanmış görevleri devre dışı. `StartWhenAvailable` ve `WakeToRun` kapalı: Hiçbir görev sonraki açılışta kendiliğinden başlamaz.

| Ölçüm | Durum | Neden | Ne zaman |
|---|---|---|---|
| Yerel taban qwen2.5:7b (23:00) | **ertelendi**, görev devre dışı | Gece koşusu yapılamıyor. Taban, nihai turda yeni cevap şemasıyla (§15) koşulacak; bugünkü şemayla ayrı koşmak tekrar olur. | Adım 2 nihai turu |
| İkinci süre turu (16:30, 30 soru × 4 model) | **koşuldu** 14:41–14:52 (16:30 yerine, elle) | Oturum akşam açık değil; sabahtan farklı saat sayıldı | yapıldı (0,097 USD; toplam 1,17 USD) |
| Çeviri karşılaştırması tur t2 (19:00) | **onaya bağlı**, görev devre dışı | Süre için başka bir saat gerekiyor; oturum akşam açık değil | Süre turundan sonra onaylanırsa hemen, yoksa bir sonraki oturumda başka bir saatte |
| Gemma 4 üretim sağlayıcıları (§12) | ertelendi | Kararla nihai tura taşındı | Adım 2 nihai turu (ayrı bütçe) |
| Kuyruk ölçümü t3 (B4 §9.2) | ertelendi | Kullanıcı elle başlatacak | Kullanıcı kararı |

## 18. Nihai tur: seçim kuralı, referans model, bütçe (öneri, 2026-11-05)

**Set:** Onaylı ve büyütülmüş set (§8). Hesapta büyütülmüş set bugünkü 177 çağrının ~1,5 katı, yani model başına **~265 soru**.

**Set onayı (2026-11-05 akşam, ölçüt düzeltildi):** Model çıktıları onay ölçütü değil (döngüsel olurdu: sistemin zorlandığı soruları setten atar). Ölçüt:
- kanıt cümlesi beklenen sayfada ve beklenen değer kanıtta (OCR soruları hariç; onlarda beklenen değer okunaklı);
- "bulunamadı" sorularında 27 Ekim korpus araması.

Sonuç: 155 sorudan 154'ü onaylı; A038 kullanıcıda (kanıt cümlesinde E050 kodu yok). 14 OCR sorusu `ocr` etiketli ve raporlarda ayrıca gösteriliyor. "Model çelişkisi" (27 soru) yalnız bilgi alanı (`model_celiskisi`); onayı etkilemiyor. Önceki, model çıktısına dayalı onaydaki yanlılık bu ölçütle kalktı.

Aşırı uyum notu korunur: arama ayarları bu setle seçildi; görülmemiş doküman testi JUKI.

**Seçim kuralı, sırayla (bir model bir kapıdan geçemezse elenir; §16 gereği modele özel yama yazılmaz):**
1. **Kalite kapısı** (onaylı sette):
   - doğru "bulunamadı" (modelin karar verdiği sorularda) **≥ %90**;
   - doğrulanmış görünen yanlış (✓/⚠ alan yanlış cevap) **0**;
   - uydurma **0**: ✖'lerdeki "alıntıda olmayan sayı" vakaları elle okunur, kaynakta da olmayan değer uydurmadır;
   - **beklenen değer cevapta ≥ %85** (kapsama ölçütü). Yeni eşleştiriciyle ilk turun bütün cevaplı sorularında: Gemma %92, Qwen %85, GPT-5.4 mini %84, Mistral %82. Yanlış ret ayrıca raporlanır, kapı değil.
   - **Netleştirme (karar 2026-11-05 gece):**
     - Değer farklı netleştirme sorularında **5/5 doğru netleştirme** (seçenekler tam beklenen ürünler);
     - netleştirme beklenmeyen sorularda **gereksiz netleştirme 0**;
     - değer aynı sorularda netleştirme YA DA iki ürünün kaynağını birlikte gösteren doğrulanmış cevap doğru sayılır (şema C bunu `atif_dokumanlari` ile kaydediyor). Bu sınıf kapı değil, raporlanır.
     - Kural katmanının netleştirmesi de sayılır (sistemin davranışı).
   - **PRD'deki "değer doğruluğu ≥ %98" ile farkı:** İkisi farklı şeyi ölçer.
     - *Beklenen değer cevapta* bir **kapsama** ölçütüdür: Cevap üretilen sorularda beklenen değer cevapta geçiyor mu? Değer eksikse düşer. Cevapta yanlış bir değerin bulunup bulunmadığını ölçmez.
     - *Değer doğruluğu* bir **kesinlik** ölçütüdür: Cevapta verilen değerlerin yüzde kaçı doğru? Yanlış değer içeren her cevap düşürür.
     - Nihai turda ikisi ayrı raporlanır. Değer doğruluğu = 1 − (beklenen değerle ya da kaynakla çelişen değer içeren cevap / değer içeren cevap). Çelişki adayları otomatik çıkarılır (beklenen değer cevapta yok ama başka bir sayı var) ve elle okunur.
     - %98 kapısı ✓/⚠ rozetli cevaplarda uygulanır; ✖ zaten kullanıcıya doğrulanmış gösterilmiyor.
2. **Dayanıklılık ve süre:**
   - **≥ 2 ZDR sağlayıcı** (aynı nicemleme). Bugün GPT-5.4 mini ve Mistral 2603 yalnız 1 sağlayıcıda; bu kapıda elenirler, ancak ikinci bir ZDR sağlayıcısı açılırsa geçerler.
   - **Süre kapısı, iki ayrı ölçü (p95, iki ayrı saatte):**
     - **Uçtan uca ilk doğrulanmış cümle ≤ 3 sn** (PRD: "ilk cümle ekranda ≤ 3 sn"). Soru metni hazır olduğu andan ekrana ilk doğrulanmış cümlenin gelişine kadar. **Arama öncesi süre dahil** (çeviri ve embed beklemesi, Qdrant, füzyon), sonra cevap modeli. Sesli soruda STT ayrı bütçe (≤ 1 sn), dahil değil.
     - **Yalnız cevap modeli: istekten ilk doğrulanmış cümleye ≤ 2,0 sn.** 3 sn'den PRD'deki arama bütçesi (≤ 1 sn) düşülünce kalan. Önceki taslaktaki 2,5 sn yalnız model içindi ve arama bütçesiyle 3 sn'yi aşıyordu; düzeltildi. PRD'deki "LLM ilk kelime ≤ 1,5 sn" ayrıca raporlanır.
     - Bugünkü şemada model tarafı tahmini (ilk cümle sonu): GPT-5.4 mini 2,1, Mistral 2,3–2,7, Gemma 4 (DeepInfra) 3,9–5,8 sn. Gemma 4'ün bf16 sağlayıcıları ve C şeması bunu düşürmeli. Ölçülecek.
     - Arama öncesi süre bugün korumalı yolda grup 1 p95 ~1,5 sn (B4 §10.6). Çeviriyi Gemma 4 NextBit'e almak çeviri p95'ini ~1,0 sn'ye indiriyor (§14). Bu durumda model tarafına ~1,5 sn kalıyor; kapı kararı uçtan uca ölçümle verilir.
3. **Maliyet:** Kapılardan geçenler arasında soru başına maliyet. Fark %50'den azsa sağlayıcı sayısı fazla olan seçilir.

**Üst sınıf referans model** (kapılara girmez; "daha büyük model ne kazandırır" sorusunun cevabı):

| Aday | ZDR | Fiyat (giriş/çıkış, USD/M) | Soru başına | ~265 soru |
|---|---|---|---|---|
| **Gemma 4 31B** (önerilen) | 13 sağlayıcı (bf16: Crusoe, Novita) | 0,14 / 0,40 | ~0,0004 USD | ~0,11 USD |
| GPT-5.4 | yalnız Azure | 2,50 / 15,00 | ~0,0089 USD | ~2,4 USD |

Öneri: Gemma 4 31B, aynı ailenin büyüğü, ucuz ve çok sağlayıcılı. GPT-5.4 tek sağlayıcılı ve yalnız referans olarak 20 kat pahalı; istenirse yalnız C şemasıyla eklenir.

**Bütçe hesabı** (ilk turun soru başına maliyetleriyle; ~265 soru):

| Kalem | Tahmin |
|---|---|
| 4 model, bugünkü şema (Gemma 4 0,06; Qwen3.6 0,12; GPT-5.4 mini 0,52; Mistral 0,09) | 0,80 USD |
| Aynı 4 model, C şeması (yan yana, §15.0) | 0,80 USD (çıktı tokeni ~%10 fazla olabilir) |
| Gemma 4, 3 bf16 sağlayıcı (§12), C şeması | 0,27 USD |
| Referans Gemma 4 31B, iki şema | 0,22 USD |
| Süre turları: iki saat × 30 soru × 6 yapılandırma, şemalı/şemasız ilk istek ölçümü dahil | ~0,20 USD |
| Yerel taban qwen2.5:7b, iki şema | 0 |
| Netleştirme ölçümü (§11, ayrı onay) | 0,06 USD |
| Düşünme kontrolleri, tekrarlar için pay (%10) | ~0,24 USD |
| **Toplam** | **~2,6 USD** |
| GPT-5.4 referansı eklenirse (yalnız C) | +2,4 USD → ~5,0 USD |

**Bugünkü harcama:** 1,17 / 1,5 USD (ön eleme). Nihai tur bu sınırın içine sığmıyor.

**Yeni sınır önerisi: nihai tur için ayrı 3,0 USD** (GPT-5.4 referansı olmadan). Toplam Adım 2 harcaması ~4,2 USD olur. GPT-5.4 referansı istenirse sınır 5,5 USD. Koşu, sınırı geçecekse durur ve haber verir (bugünkü kural).

**Karar (2026-11-05 akşam):** bütçe **3,0 USD**, referans **Gemma 4 31B**, GPT-5.4 yok.

**Ön koşullar (koşmadan önce bitmeli):**
1. Beklenen değer eşleştiricisi: **tamam** (`bench.common.value_in`, testli; ilk tur yeniden puanlandı).
2. `clarify_options` düzeltmesi: ölçüldü (§11), ürün adı eşleştirmesi (c) **etkisiz**. Önerilen yerine geçecek genel düzeltme (e) ölçüm aracına eklenecek: model soruyor ama < 2 seçenek varsa bulunan dokümanlar düğme. **Karar bekliyor.**
3. Şema C ölçüm aracında: **yapılmadı** (ANSWER_SCHEMA_C, cümle bazlı verify, akışta ilk doğrulanmış cümle zamanı).

Üçü hazır olunca plan ve kesin maliyetle onayınız istenecek.

## 19. Not: Qwen3-8B embed için sağlayıcı sabitleme bir seçenek mi? (kayıtlardan, 2026-11-05)

B4 özet §10.9: Süre sınırı ölçümünde Qwen embed çağrıları DeepInfra (84) ve Nebius (72) arasında bölündü; **ikisinde de p95 ~10,7 sn** ve çağrıların ~yarısı 1,5 sn'nin üstünde. 429 yok.
- **Sonuç: Sağlayıcı sabitleme tek başına bir çözüm değil.** O ölçümde kuyruk iki ana sağlayıcıda birlikteydi; sabitlemek yalnız hangi kuyruğu beklediğimizi seçer.
- Sabitleme ancak şu koşulda seçenek olur: Kısa bir iç içe ölçümde (DeepInfra / Nebius / SiliconFlow, aynı dakikalarda, iki farklı saatte, ~30 çağrı × 3 sağlayıcı × 2 saat ≈ 0,001 USD) bir sağlayıcı p95 ≤ 1,5 sn'yi iki saatte de tutarsa. 3 Kasım kuyruk ölçümü sağlayıcı kaydetmediği için bugün bu ayrım yapılamıyor.
- Bu ölçüm koşulmadı (onayınızla). Sonuç olumsuzsa Qwen'i sunucuya taşıma (B4) ya da mevcut koruma (1,5 sn yedek yol + devre kesici) yolu kalır.

**Ölçüm, tur p1 (2026-11-05 15:32; 30 sorgu × 3 sağlayıcı, iç içe, sabitlenmiş; 0,00004 USD; [qwen_saglayici_2026-11-05.md](../b4/qwen_saglayici_2026-11-05.md)):** DeepInfra p50 1,94 / p95 4,33 sn, Nebius 2,07 / 5,43 sn, SiliconFlow 2,90 / 12,2 sn; üçünde de çağrıların ~2/3'ü 1,5 sn'nin üstünde, 429 yok. **Bu saatte hiçbir sağlayıcı ölçütü tutmuyor: sabitleme seçenek değil.** İkinci tur başka bir saatte (bir sonraki oturum); o da tutmazsa Qwen'i sunucuya taşıma ya da yalnız koruma (1,5 sn yedek yol + devre kesici) kalır.

## 20. Nihai tur planı (hazır; onayınızı bekliyor)

**Karar (2026-11-05 gece):** Netleştirme için (e) düzeltmesi yapılmadı. Netleştirme bir şema sorunu (serbest metin ↔ alan); kalıcı çözüm şema C'nin netleştirme modu.

**Şema C, netleştirme modu dahil (ölçüm aracında hazır; uygulamaya bağlı değil)** — `bench/schema_c.py`, `python -m bench.answer_models --schema c`:
- Üst düzey `tur`: `cevap` | `netlestirme` | `bulunamadi` (enum). Model birini seçer; hem sorup hem cevap yazarsa şema dışı sayılır (JSON metriğinde görünür).
- `netlestirme`: `{soru, secenekler: [{kaynak_no}]}`, en az 2. Seçenekler kaynak numarası; ölçümde dokümana çevrilip `expect_docs` ile karşılaştırılır. Arayüz belge/ürün adını kendisi gösterir; `clarify_options` süzgecine gerek yok.
- `cevap`: `[{alinti: {kaynak_no, metin}, metin}]`. `bulunamadi`: cevap boş.
- Doğrulama öğe başına: alıntı birebir; cümlenin sayıları yalnız kendi alıntısında; tolerans; sesli metnin sayıları alıntıların birleşiminde.
- **İlk doğrulanmış cümle:** akış zaman çizelgesinden (istekten ilk geçen öğenin tamamlandığı an).
- İstem uygulamanınki; yalnız alan ve biçim kuralları uyarlandı (`system_prompt_c`). Uygulama istemi değişirse araç hata verir.
- Sınama: testler; sahte modelle 199 soruluk kuru koşu (model çağrısı yok) uçtan uca geçti.
- Pipeline'ın varyant kuralı (beden/stil tablosu) C'de uygulanmadı; ayrıca raporlanır.

**Netleştirme metriği, iki sınıf** ([eval/netlestirme_siniflari.json](../../netlestirme_siniflari.json), model çağrılmadan anahtarlardan):
- **Değer farklı (5):** Q07, A133, A138, A140, A142. Netleştirme zorunlu, seçenekler doğru olmalı.
- **Değer aynı (13):** Q17, Q30, A131, A132, A134, A135, A136, A137, A139, A141, A143, A144, A145. Netleştirme YA DA iki ürünün kaynağını birlikte gösteren doğrulanmış cevap doğru.
- §11 ölçümü bu tanımla kayıtlardan yeniden puanlandı:

| Durum | değer farklı: doğru netleştirme | değer aynı: netleştirmeyle doğru | değer aynı: sorulmadı (cevap kaydedilmemiş, sonuç bilinmiyor) |
|---|---|---|---|
| (a) BRAND_ALIASES açık | 4/5 (Q07 yanlış seçenek) | 8/13 | 5 |
| (b) kurallar kapalı | 2/5 (Q07, A133, A138 sorulmadı) | 1/13 | 12 |
| (c) + ürün adı | 2/5 | 1/13 | 12 |

- Değer aynı sorularda modelin iki kaynağı birlikte gösterip göstermediği o ölçümde kaydedilmemişti. C ölçümü bunu kaydediyor (`atif_dokumanlari`).
- **BRAND_ALIASES kararı şema C ölçümünden sonra.**

**Set:** 199 soru = 160 cevaplı + 21 "bulunamadı" + 18 netleştirme. 155/155 aday onaylı (A038 ve A008 kullanıcı kararıyla; A008 yeniden yazıldı, G8 beklenen değeri "14 1/2").
- "Bulunamadı" setinin büyütülmesi (§8) sizin onayınızı bekliyor. Büyütülmezse nihai tur bu 199 soruyla koşulur.
- Arama önbelleği netleştirme soruları ve A008'in yeni metniyle genişletildi (yerel; eski kural çıkışları değişmedi).

**Koşular ve kesin maliyet tahmini** (soru başına maliyet ilk turdan; C çıktısı için %10 pay; model çağrısı 192/199, 7'si kural çıkışı):

| Koşu | Model / sağlayıcı | Çağrı | Tahmin |
|---|---|---|---|
| C, tam set | Gemma 4 (DeepInfra fp8, referans), Qwen3.6, GPT-5.4 mini, Mistral 2603 | 4 × 192 | 0,64 USD |
| C, tam set | Gemma 4 bf16: NextBit, Parasail, Venice | 3 × 192 | 0,22 USD |
| C ve bugünkü şema, tam set | Gemma 4 31B (Crusoe bf16, üst sınıf referans) | 2 × 192 | 0,17 USD |
| Bugünkü şema, yalnız 18 netleştirme sorusu | 4 model | 4 × 18 | 0,05 USD |
| Süre turları: iki ayrı saat × 30 soru, C | 8 yapılandırma | 480 | 0,27 USD |
| Şemalı / şemasız ilk istek ek süresi, sağlayıcı bazında | 8 yapılandırma × 10 × 2 | 160 | 0,09 USD |
| Yerel taban qwen2.5:7b, iki şema | yerel | 2 × 192 | 0 |
| Düşünme kontrolleri, tekrar payı (%10) | | | ~0,15 USD |
| **Toplam** | | | **~1,6 USD** (sınır 3,0 USD) |

- Bugünkü şemanın 181 sorusu için ilk turun sonuçları kullanılır: aynı arama önbelleği, yeni `verify.py` ve eşleştiriciyle yeniden puanlanmış.
- Aynı saatte yan yana istenirse bugünkü şema da tam set yeniden koşulur: +0,60 USD → ~2,2 USD.
- Yerel taban gece değil gündüz koşulmalı (dizüstü ~2–3 saat).

**Koşu sırası:**
1. Düşünme kontrolleri.
2. C tam set, 8 bulut yapılandırması sırayla.
3. 18 netleştirme sorusu bugünkü şemayla.
4. Süre turu 1.
5. Başka saatte süre turu 2 ve şemalı/şemasız ölçüm.
6. Yerel taban.
7. Rapor (`--report-c`), kapılar (§18), seçim önerisi. BRAND_ALIASES kararı netleştirme sonuçlarıyla.

## 21. Karar ve bağlama planı (2026-11-05 gece; uygulamaya henüz bağlanmadı)

**Karar:** Cevap modeli **Gemma 4 26B A4B, şema C**.

**Sağlayıcı listesi:**
- YALNIZ **Venice (bf16, birincil)** ve **DeepInfra (fp8, ikincil)**. **(2026-11-06: değişti, DeepInfra birincil; ikincil c150b-J sonucuyla. §25)**
- OpenRouter isteğinde `provider: {"order": ["venice", "deepinfra"], "only": ["venice", "deepinfra"], "allow_fallbacks": true}`. Yedeğe düşme bu ikisiyle sınırlı; ZDR kısıtı ve Safety Retention dışlaması (`cloud.openrouter_body`) aynen kalır.
- Nicemleme farkı (bf16/fp8) bu sette kaliteyi değiştirmedi (bulunamadı, değer, netleştirme aynı). Yine de yanıtı veren sağlayıcı her cevapta denetim kaydına yazılır.

**Bağlama adımları (sırayla; her biri ayrı commit, testli, ölçümle doğrulanır):**
1. `pilot/prompts.py`: şema C (`ANSWER_SCHEMA_C`) ve istemi. Süre ölçümü (c150 / c150b) sonucuna göre son biçim seçilir. `bench/schema_c.py`'deki kod `pilot/verify.py`'ye taşınır: öğe başına doğrulama, iki biçim geçiş süresince birlikte.
2. `pilot/llm.py` / `pilot/cloud.py`: bulut cevap modeli istemcisi (akışlı, UTF-8 bayt satır, düşünme kapalı, yukarıdaki sağlayıcı listesi). Yerel Ollama yolu taban olarak kalır.
3. `pilot/pipeline.py`:
   - `tur=netlestirme` → seçenekler kaynak numarasından doküman ve ürün adı (arayüz gösterir); `clarify_options` C yolunda kullanılmaz.
   - `tur=bulunamadi` → mevcut "bulunamadı" akışı.
   - Akışta her öğe tamamlanınca doğrulama ve gösterim: ilk doğrulanmış cümle.
4. `app.py`: öğe listesi gösterimi (tek öğe paragraf, çok öğe numaralı liste, kaynak etiketleri koddan); sesli metin R15 kurallarıyla.
5. `verify.py` yamalarının kaldırılması (§15.1 listesi): eski biçim bir sürüm daha okunur, sonra kalkar.
6. Ölçüm: uygulama yolundan uçtan uca 30 soru (ilk doğrulanmış cümle ≤ 3 sn kapısı, arama öncesi dahil), sonra onaylı setin tamamı.

**Çeviri (BM25 kolu; dondurulan aday yol bağlanırken):**
- Gemma 4, **NextBit birincil**.
- **İkinci sağlayıcı: Venice ya da DeepInfra.** Çeviri ölçümünde DeepInfra Gemma 3 yavaştı (p50 2,1 sn); Gemma 4'ün DeepInfra ve Venice'teki çeviri süresi ölçülmedi. Bağlamadan önce 30 çağrı × 2 sağlayıcı kısa ölçüm (~0,001 USD), sonra `only: [nextbit, <ikinci>]`.
- **Kayıtlardan takılma kontrolü:** Çeviri ölçümlerinde (t1/t2, 2 × 1050 çağrı) takılma yok. Gemma 4 NextBit'te en uzun çağrı 1,64 sn, en uzun çıktı 87 token; DeepInfra Gemma 3'te 5–6 sn'lik birkaç çağrı. NextBit'in cevap modelindeki takılmaları uzun ve şemaya zorlanmış çıktılarda; çevirinin kısa `json_object` çıktısında görülmedi.

**Q07 arama bulgusu (B4):**
- Uygulamanın varsayılan yolunda (Türkçe soruyla BM25) BM25 İngilizce belgelerde hiçbir şey bulamıyor. Dense arama "stitch"ten Brother kılavuzlarını getiriyor; ceket ve pantolon ilk 5'te yok.
- Çevirili BM25'te:
  - Gemma 3 çevirisi ("stitches per inch (SPI) … exterior seams"): pantolon s.19 ve ceket s.22–23 ilk 5'te; netleştirme mümkün.
  - Gemma 4 çevirisi ("SPI … visible stitches"): pantolon s.19 ve ceket s.25 (başka tablo); ceket s.22–23 BM25'te 5. sırada, birleşik ilk 5'e girmiyor.
- **Sonuç:** Q07 cevap modelinin değil, çevirisiz varsayılan aramanın sorunu. Dondurulan aday yolun (çevirili BM25) bağlanması gerekiyor. Gemma 4 çevirisinde terim seçimi ("visible stitches") bu soruda Gemma 3'ten zayıf; tek soruda karar verilmez, onaylı setteki BM25 isabeti §10.8'de.

## 22. Kararlar (2026-11-05 gece, son)

- **Cevap modeli:** Gemma 4 26B A4B. **Sağlayıcılar yalnız Venice (bf16, birincil) ve DeepInfra (fp8, ikincil)** (§21).
- **Şema C'nin çalışma biçimi: c150b.** Alıntı en fazla 150 karakter, ilk öğe yalnız cevabın özü, öğe başına 1–2 alıntı.
- **Açık fark:** c150b bugünkü şemaya göre hâlâ **+6 yanlış ret** (18 → 24) ve **+6 ✖** (12 → 18) getiriyor (Gemma 4 DeepInfra, 159 cevaplı soru). İkisi de güvenli yönde: yanlış değer göstermek yerine reddetmek ya da doğrulanmadı demek. c150b bundan sonra bugünkü şemayla da karşılaştırılacak. Ayrıntı ve sıradaki işler: [DEVIR_2026-11-06.md](DEVIR_2026-11-06.md).

**Çeviri ikinci sağlayıcı (ölçüldü 2026-11-06):** Gemma 4 Venice p95 1,21 sn (%7 > 1,2 sn), DeepInfra 1,82 sn (%20), NextBit 917 ms (%0). Öneri: `only: [nextbit, venice]`. [asama4_ceviri_saglayici_2026-11-06.md](../b4/asama4_ceviri_saglayici_2026-11-06.md).

## 23. Yeni hata türü: niteleyici uyuşmazlığı (2026-11-06; plan, koşulmadı)

**Tanım:** Alıntı kaynakta birebir ve sayı alıntıda, yani cevap doğrulanmış görünüyor. Ama soru başka bir şeyi soruyor: sorudaki niteleyici (dijital, elektronik, -5, Premier, Type II, Class 2, model kodu…) cevabın dayandığı parçada yok.
- Sayım: **doğrulanmış görünen yanlış**.
- İlk örnek B012 (Gemma 4 DeepInfra, c150b). "Dijital ayak kaldırıcı" sorusuna mekanik kaldırma kolunun 6 mm ayarıyla cevap verdi. Etiket doğru kalıyor (karar 2026-11-06): S-7300A'da dijital kaldırıcı yok.

**Tarama** (`python -m bench.niteleyici_tarama`; model çağrısı yok):
- Kapsam: bugünkü şema (DeepInfra), c150b (DeepInfra, Venice), yeni set (DeepInfra, Venice).
- Niteleyici içeren 133 doğrulanmış ya da kısmi cevap tarandı; uyuşmazlık **yalnız B012**.
- Bugünkü şemanın Venice kaydı yok; bugünkü şema nihai turda yalnız DeepInfra'da koşuldu.
- Sınır: tarama sabit iki dilli niteleyici listesine ve model kodlarına bakıyor. Ürün adı düzeyindeki anlam uyuşmazlıklarını (ceket ↔ pantolon) yakalamaz; onlar netleştirme kapısının işi.

**Çözüm önerisi** (sırayla; hiçbiri koşulmadı):
1. **Ölçüme ekle (kod, model çağrısı yok):** Şema C raporuna "niteleyici uyuşmazlığı" satırı eklenir; bu tarama her turda çalışır. İşaretlenen her cevap elle okunur ve gerçekse doğrulanmış görünen yanlış sayılır. Bu türden yeni sorular (soruda olmayan bir varyantı soran "bulunamadı" soruları) kanıt sayfasıyla onaylanarak eklenir; model çıktısı onay ölçütü olmaz.
2. **İstem kuralı (ayrı varyant, ör. c150b-N):** "Sorudaki model, varyant ya da tip niteleyicisi (dijital, -5, Premier…) alıntıda ya da kaynağın başlığında yoksa o kaynakla cevap verme; bulunamadi ya da 'kaynaklarda <niteleyici> için bilgi yok' de."
   - Tam set, iki sağlayıcı, ~0,12 USD.
   - Risk: haklı cevaplarda da ret artabilir (niteleyicinin sayfada olup parçada olmadığı A045/A069 türü). Regresyon kontrolü bugünkü şema ve c150b'ye göre yapılır.
3. **Doğrulamada uyarı (yalnız 2 yetmezse; karar sizde):** Tarama kuralı uygulamaya taşınır. Niteleyicisi kaynakta olmayan cevap "kısmi" olur, rozet verilmez ve "Kaynak sorudaki 'dijital' için olmayabilir" uyarısı gösterilir.
   - Güvenli yönde ve geneldir, ama §16'daki "verify A+B son düzeltme" ilkesine aykırıdır.
   - Yanlış alarm örneği: "-[][]3" gibi model kodu yazımları. Taramada bu kalıp genelleştirildi.

## 24. Girintili JSON: ölçüm ve "girintisiz yaz" varyantı (2026-11-06; plan, koşulmadı)

**Bulgu:** Aynı istek ve şemayla bazı sağlayıcılar JSON'u girintili (satır sonu + boşluk) yazıyor. Metrik her şema C raporunda "Girintili JSON" tablosunda (`bench/answer_models.indent_table`).
- 2026-11-05: NextBit %93, Parasail %96 girintili. Venice ve DeepInfra %0.
- 2026-11-06 sabah: Venice %74–97 girintili; DeepInfra hâlâ %0.
- Girinti çıktı tokeni harcar ve 700 sınırında kesik üretir. NextBit/Parasail'in şema C'deki kesikleri (29 / 34) büyük olasılıkla bu yüzden.

**Varyant c150b-J (koşulmadı):** istemin "Cevap biçimi" kısmına "JSON'u tek satırda, girintisiz ve satır sonu olmadan yaz" kuralı eklenir.
- Genel bir istem kuralı; modele ya da sağlayıcıya özel değil.
- Ölçüm: tam set, Venice + DeepInfra, ~0,12 USD. Bakılacaklar: girintili oran, kesik, ilk doğrulanmış cümle, ✓ / ✖ (c150b ile regresyon).
- Not: Girinti sağlayıcı tarafında açılıp kapanıyor (dün %0, bugün %97). İstem kuralı tutmazsa tek çare sağlayıcı sırası.
- İstek gövdesinde girintiyi kapatan bir parametre (`response_format`'ta) OpenRouter'da yok; bu yüzden istem kuralı.

**§21 için öneri (2026-11-06, karar bekliyor): birincil/ikincil sırası değişsin.** `order: ["deepinfra", "venice"]` (DeepInfra fp8 birincil, Venice bf16 ikincil).
- Gerekçe: Venice 2026-11-06'da JSON'u girintili yazmaya başladı (c150bT %94). Kesik 2'den 37'ye çıktı (192 soru).
- DeepInfra bütün koşularda girintisiz ve kesik 0–2. Kalite c150b'de iki sağlayıcıda eşitti (✓ 112 / 113, değer %94 / %96).
- Ayrıntı: [okuma_nihai_ara_2026-11-06.md](okuma_nihai_ara_2026-11-06.md) bölüm a ve 4, plan §24.

## 25. Kararlar (2026-11-06 öğle): §21'e işlenenler

- **Çalışma biçimi c150b.** c150bT bırakıldı.
- **Doğrulayıcı alan etiketini tanır** (`pilot/tables.field_quote_ok`): "<Sütun>: <aynı hücrenin bitişik parçası>" kabul edilir; hücreleri " | " ile birleştiren alıntı kabul edilmez. Bu kural bizim veri biçimimize ait, §16'ya takılmaz. Bağlamada uygulamanın şema C doğrulamasına girer.
- **max_tokens 1200 kalıcı.** Bağlamada cevap çağrısının `max_tokens` değeri 1200; `LLM_NUM_PREDICT` (yerel Ollama yolu) ayrı. Ölçümlerde `--max-tokens 1200`.
- **Sağlayıcı sırası: DeepInfra birincil.** İkincil, c150b-J sonucuna göre belirlenecek (aday: Venice ya da Parasail; ölçüt: kesik c150b DeepInfra düzeyine inerse).
  - §21'deki `order: ["venice", "deepinfra"]` bunun yerine `order: ["deepinfra", <ikincil>]`, `only: ["deepinfra", <ikincil>]` olur.
- c150b-O ertelendi.

## 26. Bağlanacak hattın uçtan uca ölçümü (PLAN; koşulmadı, onay bekliyor)

Devir notunun e (gerçek akışla süre) ve g (onaylı set + JUKI doğrulaması) maddelerini birleştirir. f (gri "doğrulanıyor" akışı) yalnız plan olarak kalıyor.

**Hat (soru başına, tek saat ölçüsü):**
1. Paralel: sorgu çevirisi (Gemma 4 NextBit, düşünme kapalı, **1,2 sn sınırı**; aşarsa BM25 çevirisiz) ‖ bge-m3 sorgu embed'i (CPU).
2. Paralel Qdrant: bge-m3 dense ‖ BM25 sparse (çevrilmiş sorgu). RRF.
3. Uygulamanın kural katmanı (yabancı marka, kod yok, arama sonrası netleştirme) olduğu gibi: `pipeline.soru_cevapla`, `search` yerine ikili yol.
4. Cevap: Gemma 4, şema **c150b**, `max_tokens` 1200, **DeepInfra'ya sabit** (`allow_fallbacks: false`; ikincil ayrı ölçülüyor, §25), akışlı.
5. Doğrulama: `verify_c` (alan etiketi kuralı dahil). İlk doğrulanmış cümle **gerçek akış zaman çizelgesinden**.

**Varyant:** cevap modeline 5 kaynak / 8 kaynak. Çeviri ve arama soru başına bir kez yapılır, iki varyant aynı adayları kullanır. İki cevap çağrısı her soruda arka arkaya ve sırası dönerek yapılır (aynı dakika, aynı ağ).

**Korpus:** uygulamanın pilot korpusu (`manuals`, Qdrant sunucusu; bge-m3 + BM25 vektörleri hazır). 10k koleksiyonunda yalnız arama sonuçları zaten var (§b4 ikili yol raporu).

**Set:** onaylı 199 + yeni 46 = 245 soru (netleştirme soruları dahil).

**Metrikler** (varyant başına):
- §18 kalite kapıları: doğru "bulunamadı", doğrulanmış görünen yanlış (ve niteleyici taraması), ✓ / ⚠ / ✖, beklenen değer, JSON / kesik.
- Netleştirme: değer farklı, değer aynı, gereksiz, belge içi varyant.
- Yanlış ret.
- İlk doğrulanmış cümle (model tarafı, gerçek akış).
- **Uçtan uca ilk doğrulanmış cümle** (sorudan, arama dahil); p50 / p95; PRD kapısı ≤ 3 sn.
- Adım dökümü: çeviri, embed, Qdrant, ilk token.
- Çevirinin 1,2 sn sınırını aşma oranı, girintili JSON oranı.

**Ardından JUKI (14 soru), tek seferlik:** ayar değiştirmeden. Önerim: önce 5 / 8 kararınızı alayım, JUKI'yi seçilen varyantla bir kez koşayım. İkisini birden koşmak "tek seferlik" ilkesine daha az uyar.

**Araç:** yeni `bench/hat_olcumu.py`. `latency_e2e` / `latency_guard`'ın paralel adımları ve `answer_models`'in akış, şema C, puanlama kodu yeniden kullanılır.
- Model çağıran kısım yalnız çeviri ve cevap; embed yerel.
- Kayıt: `eval/bench/adim2/ham/hat_<varyant>.json`, rapor `hat_rapor_<tarih>.md`.

**Maliyet tahmini** (c150b DeepInfra kayıtlarından):

| Kalem | USD |
|---|---|
| Cevap, 5 kaynak, 245 soru | ~0,052 |
| Cevap, 8 kaynak, 245 soru (girdi ~+60 %) | ~0,08 |
| Çeviri, 245 soru | ~0,005 |
| JUKI, 14 soru, tek varyant | ~0,004 |
| **Toplam** | **~0,14** |

- Süre: ~40 dk (245 soru × 2 cevap) + JUKI ~2 dk.
- Başka saatte koşulması önerilir (devir e: süre ölçümü farklı saatte).
- Bütçe: harcanan ~1,53 + c150b-J ~0,18; kalan ~1,29 / 3,0.

## 27. c150b-J sonucu ve boşluk kaçağı (2026-11-06; öneri, koşulmadı)

- c150b-J girintiyi kaldırdı. Kesiklerin asıl nedeni ise **JSON ortasında boşluk kaçağı** (Venice 16, Parasail 12; DeepInfra 0). Ayrıntı okuma 2026-11-06 §5.
- **İkincil sağlayıcı: §25 ölçütüne göre şu an aday yok.** Bağlamada önerim: DeepInfra tek sağlayıcı (`only: ["deepinfra"]`). DeepInfra çağrısı hata verirse cevap "kaynakları gösterir, cevap yok" yoluna düşer.
- **Kaçağa karşı genel önlem (öneri, koşulmadı):** akış bekçisi.
  - Akışta art arda 40+ boşluk karakteri gelirse akış kesilir ve istek ikincil sağlayıcıya bir kez yeniden gönderilir.
  - Modele ya da sağlayıcıya özel değil; uygulamanın akış okuyucusunda genel bir kural. Kesik JSON'u "onarma" önerilmez.
  - Ölçüm: c150b-J Venice + Parasail kayıtları üzerinde benzetim (kaçak anı kayıtta var; model çağrısı yok), ardından istenirse gerçek koşu.
- **c150b-J'yi çalışma biçimine almak:** DeepInfra'da kalite c150b ile aynı düzeyde, girintiyi sağlayıcıdan bağımsız kapatıyor. Önerim: alınsın (karar sizde).

## 28. Kararlar ve akış bekçisi (2026-11-06 öğleden sonra)

- **Çalışma biçimi c150b-J** (girintisiz tek satır JSON, max_tokens 1200).
- Akış bekçisi benzetimi (okuma 2026-11-06 §6): N = 20/40/80 aynı sonucu veriyor, yanlış alarm yok. Bekçiyle de Venice ve Parasail'de kullanıcıya ulaşmayan cevap %2,7–3,2 (ölçüt ≤ ~%1).
- **Öneri: DeepInfra tek sağlayıcı** (`only: ["deepinfra"]`, `allow_fallbacks: false`). Bekçi N = 40, tetiklenirse aynı sağlayıcıya bir kez yeniden deneme; bağlama planına girer, henüz bağlanmadı.
- §26 onaylandı: c150b-J, DeepInfra'ya sabit. Ek koşullar:
  - Rapor `manuals` korpusu sayılarının 10k ölçümleriyle doğrudan karşılaştırılamayacağını yazar.
  - 5 ve 8 kaynağın sırası her soruda rastgele.
  - Q05 ve G7'deki gereksiz netleştirmeler ayrıca izlenir.
  - JUKI kullanıcının 5/8 kararından sonra, tek seferde iki ölçüm: (a) seçilen hattın uçtan uca sonucu, (b) yalnız arama: varsayılan, ikili yol, üçlü füzyon (Qwen embed dahil), hit@1 / hit@5. Ayar değişmez.
