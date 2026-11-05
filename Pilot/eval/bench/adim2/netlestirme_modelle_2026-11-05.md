# Netleştirme, modelle (Gemma 4, DeepInfra) — 2026-11-05

Adım 2 planı §11. Arama uygulamanın varsayılan yolu (canlı); aynı istem; model çağrısı yalnız kural katmanından geçen sorularda. 212 model çağrısı, 0.0501 USD. Araç: `python -m bench.clarify_model`.

## Netleştirme beklenen 18 soru

| Durum | soruldu | doğru (tam beklenen ürünler) | beklenenleri kapsıyor, fazlası var | eksik ya da yanlış | seçenek yok | model sordu ama gösterilmedi |
|---|---|---|---|---|---|---|
| (a) BRAND_ALIASES açık (taban) | 13/18 | 12 | 0 | 1 | 0 | 1 |
| (b) kurallar kapalı | 3/18 | 3 | 0 | 0 | 0 | 4 |
| (c) kapalı + seçenek ürün/doküman adıyla | 3/18 | 3 | 0 | 0 | 0 | 5 |

## (d) Netleştirme beklenmeyen sorular

Gereksiz netleştirme: **0/181**; model sordu ama gösterilmedi: 1.

| Soru | netleştirme sorusu | seçenekler |
|---|---|---|

## Soru başına (18 soru × a/b/c)

| Soru | beklenen | Durum | soruldu | seçenekler | değerlendirme | atlanan |
|---|---|---|---|---|---|---|
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | a | evet | brother-s7300b, brother-s7300a | eksik ya da yanlış |  |
| questions:Q17 | brother-s7300a, brother-s7300b | a | evet | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |  |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | a | evet | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |  |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | a | evet | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |  |
| aday_sorular:A132 | brother-s7300a, brother-s7300b | a | hayır | – | – |  |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | a | evet | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | a | evet | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |  |
| aday_sorular:A135 | brother-s7300a, brother-s7300b | a | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? (S-7300A veya S |
| aday_sorular:A136 | brother-s7300a, brother-s7300b | a | evet | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | a | evet | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A138 | brother-s7300a, brother-s7300b | a | evet | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |  |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | a | evet | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |  |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | a | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A141 | gl-pd-14-04a, gl-pd-07-14a | a | hayır | – | – |  |
| aday_sorular:A142 | gl-pd-14-04a, gl-pd-07-14a | a | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | a | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | a | hayır | – | – |  |
| aday_sorular:A145 | gl-pd-14-04a, gl-pd-07-14a | a | hayır | – | – |  |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | b | hayır | – | – |  |
| questions:Q17 | brother-s7300a, brother-s7300b | b | hayır | – | – | Hangi S-7300 modelinin hızını öğrenmek istiyorsunuz? S-7300A |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A132 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | b | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? S-7300A mı yoks |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A135 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A136 | brother-s7300a, brother-s7300b | b | hayır | – | – | Hangi makine modeli için topraklama vidası torkunu öğrenmek  |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A138 | brother-s7300a, brother-s7300b | b | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | b | hayır | – | – |  |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | b | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A141 | gl-pd-14-04a, gl-pd-07-14a | b | hayır | – | – |  |
| aday_sorular:A142 | gl-pd-14-04a, gl-pd-07-14a | b | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | b | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | b | hayır | – | – |  |
| aday_sorular:A145 | gl-pd-14-04a, gl-pd-07-14a | b | hayır | – | – |  |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | c | hayır | – | – |  |
| questions:Q17 | brother-s7300a, brother-s7300b | c | hayır | – | – | Hangi S-7300 modelinin hızını öğrenmek istiyorsunuz? S-7300A |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | c | hayır | – | – |  |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | c | hayır | – | – |  |
| aday_sorular:A132 | brother-s7300a, brother-s7300b | c | hayır | – | – |  |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | c | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | c | hayır | – | – |  |
| aday_sorular:A135 | brother-s7300a, brother-s7300b | c | hayır | – | – |  |
| aday_sorular:A136 | brother-s7300a, brother-s7300b | c | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | c | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? S-7300A mı yoks |
| aday_sorular:A138 | brother-s7300a, brother-s7300b | c | hayır | – | – | Hangi makine modeli için bilgi istiyorsunuz? S-7300A için 6  |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | c | hayır | – | – |  |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | c | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A141 | gl-pd-14-04a, gl-pd-07-14a | c | hayır | – | – |  |
| aday_sorular:A142 | gl-pd-14-04a, gl-pd-07-14a | c | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | c | evet | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |  |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | c | hayır | – | – |  |
| aday_sorular:A145 | gl-pd-14-04a, gl-pd-07-14a | c | hayır | – | – |  |
