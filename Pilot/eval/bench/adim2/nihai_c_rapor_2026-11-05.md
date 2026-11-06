# Adım 2 nihai tur, şema C: `nihai_c`

Şema C (plan §15.0): her cümle kendi alıntısıyla; tur = cevap | netlestirme | bulunamadi. Rozet öğe başına doğrulamadan (`bench/schema_c.py`). Pipeline'ın varyant kuralı C'de uygulanmadı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | 192 | 2 | 17/17 (100%) | **0** | 109 / 2 / 19 | 88/93 (95%) | 4/5 (80%) | 8/13 (62%) | 0 (belge içi varyant doğru 2/2) | 402 ms / 764 ms | 2,52 sn / 6,33 sn | 0.0452 USD |
| gemma4_31b | 192 | 32 | 17/17 (100%) | **0** | 92 / 3 / 10 | 66/96 (69%) | 4/5 (80%) | 7/13 (54%) | 2 (belge içi varyant doğru 1/2) | 414 ms / 760 ms | 1,46 sn / 2,87 sn | 0.0832 USD |
| gemma4_nextbit | 192 | 29 | 14/17 (82%) | **0** | 96 / 3 / 20 | 82/95 (86%) | 2/5 (40%) | 2/13 (15%) | 0 (belge içi varyant doğru 1/2) | 349 ms / 628 ms | 2,54 sn / 4,79 sn | 0.1198 USD |
| gemma4_parasail | 192 | 34 | 17/17 (100%) | **0** | 97 / 3 / 14 | 79/96 (82%) | 2/5 (40%) | 1/13 (8%) | 0 (belge içi varyant doğru 0/2) | 560 ms / 1,19 sn | 1,55 sn / 2,98 sn | 0.0621 USD |
| gemma4_venice | 192 | 1 | 17/17 (100%) | **0** | 114 / 2 / 16 | 90/94 (96%) | 4/5 (80%) | 9/13 (69%) | 0 (belge içi varyant doğru 2/2) | 582 ms / 1,33 sn | 2,82 sn / 7,19 sn | 0.0750 USD |
| gpt54mini | 192 | 2 | 16/17 (94%) | **1** | 136 / 0 / 3 | 85/99 (86%) | 2/5 (40%) | 1/13 (8%) | 0 (belge içi varyant doğru 0/2) | 1,09 sn / 2,87 sn | 1,64 sn / 6,70 sn | 0.3370 USD |
| mistral2603 | 192 | 5 | 17/17 (100%) | **0** | 108 / 4 / 25 | 80/101 (79%) | 3/5 (60%) | 5/13 (38%) | 0 (belge içi varyant doğru 0/2) | 465 ms / 954 ms | 1,16 sn / 2,21 sn | 0.0604 USD |
| qwen36 | 192 | 9 | 16/17 (94%) | **1** | 110 / 1 / 10 | 76/91 (84%) | 3/5 (60%) | 2/13 (15%) | 2 (belge içi varyant doğru 0/2) | 566 ms / 1,04 sn | 2,13 sn / 3,30 sn | 0.0794 USD |

İlk doğrulanmış cümle: model isteğinden, akışta ilk geçen öğenin tamamlandığı ana (model tarafı; uçtan uca süre ayrıca, arama öncesi dahil). Değer aynı: netleştirme ya da iki ürünün kaynağını birlikte gösteren doğrulanmış cevap doğru sayılır.
