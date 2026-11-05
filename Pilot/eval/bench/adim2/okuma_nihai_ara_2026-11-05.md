# Adım 2 nihai tur: ara okuma (2026-11-05, 16:11–16:40)

Ham rapor: [nihai_c_rapor_2026-11-05.md](nihai_c_rapor_2026-11-05.md) (`python -m bench.answer_models --report-c nihai_c`). Plan: [§20](plan_cevap_modeli_2026-11-05.md).
- Set: 199 soru; 192 model çağrısı, 7 soru kural çıkışı.
- **Gemma 4 NextBit koşusu sürüyor**: bazı çağrılar akışın ortasında ~150 sn takılıyor. Tablodaki satırı kısmi (38 soru).
- Süre turu 1 ve 2, şemalı/şemasız ek süre ölçümü ve yerel taban henüz koşulmadı.

## Şema C, 8 yapılandırma (onaylı set, 199 soru)

| Yapılandırma | JSON/şema hatası | doğru "bulunamadı" | doğrulanmış görünen yanlış | cevaplı ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı (kapı 5/5) | değer aynı | gereksiz netleştirme (kapı 0) | ilk doğrulanmış cümle p50 / p95 (model; kapı ≤ 2,0 sn) | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemma 4, DeepInfra fp8 | 2 | 17/17 | 0 | 109 / 2 / 19 | %95 | 4/5 | 8/13 | 2 | 2,52 / 6,33 sn | 0,045 |
| Gemma 4, Parasail bf16 | **34** (yarıda kesik) | 17/17 | 0 | 97 / 3 / 14 | %82 | 2/5 | 1/13 | 0 | 1,55 / 2,98 sn | 0,062 |
| Gemma 4, Venice bf16 | 1 | 17/17 | 0 | 114 / 2 / 16 | %96 | 4/5 | 9/13 | 2 | 2,82 / 7,19 sn | 0,075 |
| Gemma 4, NextBit bf16 | (sürüyor) | | | | | | | | | |
| Gemma 4 31B, Crusoe bf16 (referans) | **32** (yarıda kesik) | 17/17 | 0 | 92 / 3 / 10 | %70 | 4/5 | 7/13 | 3 | 1,46 / 2,87 sn | 0,083 |
| Qwen3.6, DeepInfra | 9 | 16/17 | **1** | 110 / 1 / 10 | %86 | 3/5 | 2/13 | 2 | 2,13 / 3,30 sn | 0,079 |
| GPT-5.4 mini, Azure | 2 | 16/17 | **1** | 136 / 0 / 3 | %87 | 2/5 | 1/13 | 0 | 1,64 / 6,70 sn | 0,337 |
| Mistral Small 2603 | 5 | 17/17 | 0 | 108 / 4 / 25 | %81 | 3/5 | 5/13 | 0 | 1,16 / 2,21 sn | 0,060 |

**JSON hataları:**
- **Parasail ve Crusoe:** hataların hepsi yarıda kesik (`finish=length`). Model şemaya zorlanınca bazı cevaplarda alanlar arasına token sınırına kadar boşluk basıyor. Bu, o sağlayıcıların yapılandırılmış çıktı motorundan kaynaklanıyor. §16 gereği yama yazılmaz; JSON metriğinde görünür. Aynı Gemma 4 DeepInfra ve Venice'te 1–2 hata var.
- **Qwen3.6:** 6 kez `tur=netlestirme` seçilip seçenekler yazılmamış (şema dışı).

**Kapılar (§18), ara durum:**
- **Değer farklı 5/5 netleştirme: hiçbir yapılandırma geçmiyor.** En iyisi 4/5: Gemma 4 DeepInfra/Venice ve Gemma 4 31B.
- **Gereksiz netleştirme 0:** Parasail, GPT-5.4 mini ve Mistral geçiyor; diğerlerinde 2–3.
- **Doğrulanmış görünen yanlış 0:** GPT-5.4 mini ve Qwen3.6'da 1. Gemma 4 ve Mistral geçiyor.
- **İlk doğrulanmış cümle ≤ 2,0 sn (model tarafı p95):** hiçbiri. En yakın Mistral (2,21), sonra Gemma 4 31B (2,87) ve Parasail (2,98). Gemma 4 DeepInfra ve Venice'te p95 6–7 sn.
- **≥ 2 ZDR sağlayıcı:** GPT-5.4 mini ve Mistral 1 sağlayıcılı.
- **Sonuç: Bu turda kapıların hepsini geçen yapılandırma yok.** Ayrıntılı karar süre turları ve NextBit bitince.

## Gemma 4: iki koşu ve iki şema (DeepInfra, 181 soru, aynı oturum)

| Koşu | doğru "bulunamadı" | yanlış ret | cevaplı ✓ / ⚠ / ✖ | beklenen değer | JSON | ilk token p50 / p95 | toplam p50 / p95 |
|---|---|---|---|---|---|---|---|
| Bugünkü şema, ilk tur (11:16) | 17/17 | 18/159 | 118 / 11 / 12 | 93/112 | 0 | 0,39 / 1,04 sn | 3,0 / 10,3 sn |
| Bugünkü şema, yeniden (16:16) | 17/17 | 18/159 | 118 / 11 / 12 | 92/112 | 0 | 0,41 / 0,93 sn | 4,0 / 11,0 sn |
| Şema C (16:16) | 17/17 | **25**/159 | 109 / 2 / **19** | 88/93 | 2 | 0,40 / 0,80 sn | 4,4 / 16,8 sn |

**Koşudan koşuya oynama (aynı şema, aynı sağlayıcı):** 180 sorunun hiçbirinde çıkış değişmedi; 6 rozet ve 1 beklenen değer değişti. Oynama küçük; aşağıdaki farklar şemadan geliyor.

**Şema C'nin Gemma 4'e etkisi:**
- Yanlış ret 18 → 25.
- ✖ 12 → 19: öğe başına doğrulama daha sıkı; sayının yalnız kendi alıntısında aranması dahil.
- ⚠ 11 → 2.
- Değer farklı netleştirme 2/5 → 4/5.
- Toplam süre p95 11 → 17 sn: alıntılar her cümlede tekrar ediyor.

**Bugünkü şemada 18 netleştirme sorusu (5 model):**
- Değer farklı: hepsi 2/5. Bunlar kural katmanının ceket/pantolon netleştirmeleri; model kendisi sormuyor ya da sorduğu netleştirme gösterilmiyor (atlanan 1–8).
- Değer aynı: Qwen3.6 5/13, GPT-5.4 mini 9/13, Gemma 4 8/13, Gemma 4 31B 7/13, Mistral 7/13.
- Şema C'de değer farklı en iyi 4/5; netleştirme modu modelin sorusunu kullanıcıya ulaştırıyor.

Harcama (nihai_* toplamı, NextBit kısmi dahil): 0,95 USD; sınır 3,0 USD.
