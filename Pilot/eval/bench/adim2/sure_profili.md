# Gün içi süre profili (plan §33)

1 ölçüm, 1 gün, 10 soru. Uygulamanın c yolu, sabit 10 soru. Süreler sn, sorunun başından. Toplam maliyet 0.0028 USD.

| Saat dilimi | Ölçüm | Soru | ilk görünen kelime p50 / p95 | ilk doğrulanmış p50 / p95 | ≤ 3 sn | istek öncesi p50 | arama p50 | çeviri p50 / p95 | model ilk token p50 / p95 | sağlayıcı |
|---|---|---|---|---|---|---|---|---|---|---|
| 15–17 | 1 | 10 | 2,25 / 4,87 | 2,54 / 5,33 | 6/7 | 0,81 | 0,80 | 0,63 / 0,99 | 0,51 / 1,63 | {'deepinfra': 9, 'venice': 1} |

| Ölçüm | Soru | ilk doğrulanmış p50 / p95 | model ilk token p95 | çeviri sınırı aşıldı |
|---|---|---|---|---|
| 2026-11-06T16:41:00 | 10 | 2,54 / 5,33 | 1,63 | 0 |
