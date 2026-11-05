# İlke dışı kurallar, kural bazında (10k, rerank'sız, geçici, onaysız set)

Bayrak: `PILOT_DOC_SPECIFIC_RULES` (varsayılan kapalı; kurallar: brand_aliases, s7300_family). Sorular: 199 (cevaplı 160, netleştirme beklenen 18, bulunamadı beklenen 21). Hattın karar katmanı model çağrılmadan çalıştı; arama `scale_bge_m3_10000` / `scale_qwen3_8b_10000`.

## Arama isabeti ve beklenen davranış

| Yol | Kurallar | aranan cevaplı | hit@1 | hit@5 | cevaplı → modele | netleştirme beklenen → netleştirme | netleştirme beklenmeyen → netleştirme | bulunamadı beklenen → kural çıkışı |
|---|---|---|---|---|---|---|---|---|
| Varsayılan: bge-m3 + BM25 | kapalı | 160 | 0,66 | 0,85 | 159 | 2/18 | 1 | 4/21 |
| Varsayılan: bge-m3 + BM25 | yalnız BRAND_ALIASES | 160 | 0,66 | 0,85 | 159 | 10/18 | 1 | 4/21 |
| Varsayılan: bge-m3 + BM25 | yalnız S-7300 grubu | 160 | 0,66 | 0,85 | 159 | 3/18 | 1 | 4/21 |
| Varsayılan: bge-m3 + BM25 | ikisi (eski davranış) | 160 | 0,66 | 0,85 | 159 | 10/18 | 1 | 4/21 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | kapalı | 160 | 0,86 | 0,98 | 159 | 4/18 | 1 | 4/21 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | yalnız BRAND_ALIASES | 160 | 0,86 | 0,98 | 159 | 14/18 | 1 | 4/21 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | yalnız S-7300 grubu | 160 | 0,86 | 0,98 | 159 | 5/18 | 1 | 4/21 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | ikisi (eski davranış) | 160 | 0,86 | 0,98 | 159 | 14/18 | 1 | 4/21 |

hit@k yalnız aranan sorular üzerinden (kural çıkışıyla aranmayan soru paydada yok).

## Netleştirme seçenekleri doğru mu (netleştirme beklenen sorular)

Beklenen: sorunun `expect_docs`'u, yani ayırt edilmesi gereken ürünler (ceket/pantolon, S-7300A/B). Netleştirme soruldu ama seçenekler başka ürünlerse (Q07: aynı ailenin modelleri) soru sorulmuş sayılır ama doğru değildir.

| Yol | Kurallar | netleştirme soruldu | doğru (tam beklenen ürünler) | beklenenleri kapsıyor, fazlası var | eksik ya da yanlış | seçenek yok |
|---|---|---|---|---|---|---|
| Varsayılan: bge-m3 + BM25 | kapalı | 2/18 | 2 | 0 | 0 | 0 |
| Varsayılan: bge-m3 + BM25 | yalnız BRAND_ALIASES | 10/18 | 9 | 0 | 1 | 0 |
| Varsayılan: bge-m3 + BM25 | yalnız S-7300 grubu | 3/18 | 3 | 0 | 0 | 0 |
| Varsayılan: bge-m3 + BM25 | ikisi (eski davranış) | 10/18 | 9 | 0 | 1 | 0 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | kapalı | 4/18 | 4 | 0 | 0 | 0 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | yalnız BRAND_ALIASES | 14/18 | 14 | 0 | 0 | 0 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | yalnız S-7300 grubu | 5/18 | 5 | 0 | 0 | 0 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | ikisi (eski davranış) | 14/18 | 14 | 0 | 0 | 0 |

Netleştirme sorulan sorular, seçenekler (kısaltılmış doküman kimlikleri):

| Soru | beklenen ürünler | Yol | Kurallar | seçenekler | değerlendirme |
|---|---|---|---|---|---|
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | yalnız BRAND_ALIASES | brother-s7300b, brother-s7300a | eksik ya da yanlış |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | ikisi (eski davranış) | brother-s7300b, brother-s7300a | eksik ya da yanlış |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | aday | kapalı | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız BRAND_ALIASES | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız S-7300 grubu | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| questions:Q07 | gl-pd-14-04a, gl-pd-07-14a | aday | ikisi (eski davranış) | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| questions:Q17 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| questions:Q17 | brother-s7300a, brother-s7300b | varsayilan | yalnız S-7300 grubu | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions:Q17 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions:Q17 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions:Q17 | brother-s7300a, brother-s7300b | aday | yalnız S-7300 grubu | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions:Q17 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| questions_ek:Q30 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A131 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A132 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A132 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A133 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A134 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A136 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A136 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300b, brother-s7300a | doğru (tam beklenen ürünler) |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A137 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A138 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A138 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | varsayilan | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | varsayilan | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | aday | yalnız BRAND_ALIASES | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A139 | brother-s7300a, brother-s7300b | aday | ikisi (eski davranış) | brother-s7300a, brother-s7300b | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | kapalı | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | yalnız BRAND_ALIASES | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | yalnız S-7300 grubu | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | ikisi (eski davranış) | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | aday | kapalı | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız BRAND_ALIASES | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız S-7300 grubu | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A140 | gl-pd-14-04a, gl-pd-07-14a | aday | ikisi (eski davranış) | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | kapalı | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | yalnız BRAND_ALIASES | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | yalnız S-7300 grubu | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | varsayilan | ikisi (eski davranış) | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | aday | kapalı | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız BRAND_ALIASES | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız S-7300 grubu | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A143 | gl-pd-14-04a, gl-pd-07-14a | aday | ikisi (eski davranış) | gl-pd-14-04a, gl-pd-07-14a | doğru (tam beklenen ürünler) |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | aday | kapalı | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız BRAND_ALIASES | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | aday | yalnız S-7300 grubu | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |
| aday_sorular:A144 | gl-pd-14-04a, gl-pd-07-14a | aday | ikisi (eski davranış) | gl-pd-07-14a, gl-pd-14-04a | doğru (tam beklenen ürünler) |

## Çıkışlar (bütün sorular; kural çıkışları model çıkışından ayrı)

| Yol | Kurallar | kod_yok | model | netlestirme_once | netlestirme_sonra | yabanci_marka |
|---|---|---|---|---|---|---|
| Varsayılan: bge-m3 + BM25 | kapalı | 2 | 192 | 0 | 3 | 2 |
| Varsayılan: bge-m3 + BM25 | yalnız BRAND_ALIASES | 2 | 184 | 0 | 11 | 2 |
| Varsayılan: bge-m3 + BM25 | yalnız S-7300 grubu | 2 | 191 | 1 | 3 | 2 |
| Varsayılan: bge-m3 + BM25 | ikisi (eski davranış) | 2 | 184 | 1 | 10 | 2 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | kapalı | 2 | 190 | 0 | 5 | 2 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | yalnız BRAND_ALIASES | 2 | 180 | 0 | 15 | 2 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | yalnız S-7300 grubu | 2 | 189 | 1 | 5 | 2 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | ikisi (eski davranış) | 2 | 180 | 1 | 14 | 2 |

## Kapalıya göre değişen sorular

| Soru | beklenen | Yol | kapalı | yalnız BRAND_ALIASES | yalnız S-7300 grubu | ikisi (eski davranış) |
|---|---|---|---|---|---|---|
| questions:Q07 — Dış görünür dikişlerde SPI kaç olmalı? | netleştirme | varsayilan | model (19) | netlestirme_sonra (19) | model (19) | netlestirme_sonra (19) |
| questions:Q17 — S-7300'ün maksimum dikiş hızı nedir? | netleştirme | varsayilan | model (1) | netlestirme_sonra (1) | netlestirme_once (None) | netlestirme_once (None) |
| questions:Q17 — S-7300'ün maksimum dikiş hızı nedir? | netleştirme | aday | model (1) | netlestirme_sonra (1) | netlestirme_once (None) | netlestirme_once (None) |
| questions_ek:Q30 — E050 hatası ne demek? | netleştirme | varsayilan | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| questions_ek:Q30 — E050 hatası ne demek? | netleştirme | aday | model (2) | netlestirme_sonra (2) | model (2) | netlestirme_sonra (2) |
| aday_sorular:A131 — E050 ne demek? | netleştirme | varsayilan | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A131 — E050 ne demek? | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A132 — Dikişte ilmek oluşuyor, ne yapmalıyım? | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A133 — İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı | netleştirme | varsayilan | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A133 — İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A134 — Alt iplik sayacı nasıl azalıyor? | netleştirme | varsayilan | model (6) | netlestirme_sonra (6) | model (6) | netlestirme_sonra (6) |
| aday_sorular:A134 — Alt iplik sayacı nasıl azalıyor? | netleştirme | aday | model (4) | netlestirme_sonra (4) | model (4) | netlestirme_sonra (4) |
| aday_sorular:A136 — Topraklama vidası hangi torkla sıkılır? | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A137 — Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne | netleştirme | varsayilan | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A137 — Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A138 — İplik kesme kamı ayarında iğne mili kaç mm kaldırılır? | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A139 — Makine kafası dik konuma nasıl getirilir? | netleştirme | varsayilan | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |
| aday_sorular:A139 — Makine kafası dik konuma nasıl getirilir? | netleştirme | aday | model (1) | netlestirme_sonra (1) | model (1) | netlestirme_sonra (1) |

Hücre: çıkış (beklenen kaynağın sırası).

Bulut: {"chat": null, "embed": {"requests": 0, "prompt_tokens": 0, "cost_usd": 0.0, "network_s": 0.0, "cached": 786, "retries": 0}, "eklenen_ceviri": []}
