# Adım 2 planı: cevap modeli seçimi, ilk tur (2026-11-05, onay bekliyor, koşulmadı)

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
