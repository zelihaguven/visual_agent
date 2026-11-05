# Qwen3-8B embed: sağlayıcıya göre süre (sabitlenmiş, iç içe)

Adım 2 planı §19. Her çağrı tek sağlayıcıya sabit, yeniden denemesiz; süre çağrının tamamı. Ölçüt: bir sağlayıcı iki ayrı saatte de p95 ≤ 1,5 sn.

| Tur | Sağlayıcı | çağrı | p50 | p95 | en uzun | > 1,5 sn | 429 | diğer hata |
|---|---|---|---|---|---|---|---|---|
| p1 (15:32) | deepinfra | 30 | 1,94 sn | 4,33 sn | 5,47 sn | 19 | 0 | 0 |
| p1 (15:32) | nebius | 30 | 2,07 sn | 5,43 sn | 5,82 sn | 21 | 0 | 0 |
| p1 (15:32) | siliconflow | 30 | 2,90 sn | 12,22 sn | 16,60 sn | 20 | 0 | 0 |
