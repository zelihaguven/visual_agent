# İlke dışı kurallar bayrağı: açık / kapalı (10k, rerank'sız, geçici, onaysız set)

Bayrak: `PILOT_DOC_SPECIFIC_RULES` (varsayılan kapalı). Sorular: 199 (cevaplı 160, netleştirme beklenen 18, bulunamadı beklenen 21). Hattın karar katmanı model çağrılmadan çalıştı; arama `scale_bge_m3_10000` / `scale_qwen3_8b_10000`.

## Arama isabeti (cevaplı sorular, hattın verdiği kapsamla)

| Yol | Bayrak | aranan | hit@1 | hit@5 | modele ulaşan |
|---|---|---|---|---|---|
| Varsayılan: bge-m3 + BM25 | kapalı | 160 | 0,66 | 0,85 | 159 |
| Varsayılan: bge-m3 + BM25 | açık | 160 | 0,66 | 0,85 | 159 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | kapalı | 160 | 0,86 | 0,98 | 159 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | açık | 160 | 0,86 | 0,98 | 159 |

Not: hit@k yalnız aranan sorular üzerinden (kural çıkışıyla aranmayan soru paydada yok).

## Çıkışlar (bütün sorular)

| Yol | Bayrak | kod_yok | model | netlestirme_once | netlestirme_sonra | yabanci_marka |
|---|---|---|---|---|---|---|
| Varsayılan: bge-m3 + BM25 | kapalı | 2 | 192 | 0 | 3 | 2 |
| Varsayılan: bge-m3 + BM25 | açık | 2 | 184 | 1 | 10 | 2 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | kapalı | 2 | 190 | 0 | 5 | 2 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | açık | 2 | 180 | 1 | 14 | 2 |

## Beklenen davranış

| Yol | Bayrak | netleştirme beklenen → netleştirme | bulunamadı beklenen → kural çıkışı |
|---|---|---|---|
| Varsayılan: bge-m3 + BM25 | kapalı | 2/18 | 4/21 |
| Varsayılan: bge-m3 + BM25 | açık | 10/18 | 4/21 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | kapalı | 4/18 | 4/21 |
| Aday: Qwen3-8B + bge-m3 + çevirili BM25 | açık | 14/18 | 4/21 |

## Değişen sorular

| Soru | Yol | kapalı | açık |
|---|---|---|---|
| questions:Q07 — Dış görünür dikişlerde SPI kaç olmalı? | varsayilan | model (sıra 19) | netlestirme_sonra (sıra 19) |
| questions:Q17 — S-7300'ün maksimum dikiş hızı nedir? | varsayilan | model (sıra 1) | netlestirme_once (sıra None) |
| questions:Q17 — S-7300'ün maksimum dikiş hızı nedir? | aday | model (sıra 1) | netlestirme_once (sıra None) |
| questions_ek:Q30 — E050 hatası ne demek? | varsayilan | model (sıra 1) | netlestirme_sonra (sıra 1) |
| questions_ek:Q30 — E050 hatası ne demek? | aday | model (sıra 2) | netlestirme_sonra (sıra 2) |
| aday_sorular:A131 — E050 ne demek? | varsayilan | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A131 — E050 ne demek? | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A132 — Dikişte ilmek oluşuyor, ne yapmalıyım? | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A133 — İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı? | varsayilan | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A133 — İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı? | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A134 — Alt iplik sayacı nasıl azalıyor? | varsayilan | model (sıra 6) | netlestirme_sonra (sıra 6) |
| aday_sorular:A134 — Alt iplik sayacı nasıl azalıyor? | aday | model (sıra 4) | netlestirme_sonra (sıra 4) |
| aday_sorular:A136 — Topraklama vidası hangi torkla sıkılır? | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A137 — Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne olma | varsayilan | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A137 — Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne olma | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A138 — İplik kesme kamı ayarında iğne mili kaç mm kaldırılır? | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A139 — Makine kafası dik konuma nasıl getirilir? | varsayilan | model (sıra 1) | netlestirme_sonra (sıra 1) |
| aday_sorular:A139 — Makine kafası dik konuma nasıl getirilir? | aday | model (sıra 1) | netlestirme_sonra (sıra 1) |

Bulut: {"chat": {"requests": 18, "prompt_tokens": 1806, "completion_tokens": 354, "cost_usd": 0.00016695, "network_s": 15.777089299998806, "retries": 0}, "embed": {"requests": 7, "prompt_tokens": 327, "cost_usd": 5.9700000000000004e-06, "network_s": 13.971674300000814, "cached": 386, "retries": 0}, "eklenen_ceviri": ["Dış görünür dikişlerde SPI kaç olmalı?", "S-7300'ün maksimum dikiş hızı nedir? (sewing speed)", "E050 hatası ne demek?", "E050 ne demek?", "Dikişte ilmek oluşuyor, ne yapmalıyım?", "İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı? (upper thread)", "Alt iplik sayacı nasıl azalıyor? (lower thread)", "Aydınlatma LED'i nasıl açılıp kapatılır?", "Topraklama vidası hangi torkla sıkılır?", "Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne olmalı? (rotary hook, bobbin case, bobbin)", "İplik kesme kamı ayarında iğne mili kaç mm kaldırılır? (needle bar)", "Makine kafası dik konuma nasıl getirilir?", "İliklerde inç başına kaç dikiş olmalı? (buttonhole)", "Cırt bant kenardan ne kadar içeriden dikilir?", "Beden etiketi nereye dikilir?", "Isırma testinde kollar böcek kafesinde kaç dakika tutulur?", "Permetrin geri kazanımı en az yüzde kaç olmalı?", "Cep kapağı punterizi kaç dikişli olur? (backtack)"]}
