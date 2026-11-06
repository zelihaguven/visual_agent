# Adım 2 nihai tur, şema C: `nihai_c150bT`

Şema C (plan §15.0): her cümle kendi alıntısıyla; tur = cevap | netlestirme | bulunamadi. Rozet öğe başına doğrulamadan (`bench/schema_c.py`). Pipeline'ın varyant kuralı C'de uygulanmadı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | 192 | 1 | 17/17 (100%) | **0** | 114 / 1 / 17 | 89/94 (95%) | 4/5 (80%) | 8/13 (62%) | 1 (belge içi varyant doğru 1/2) | 406 ms / 893 ms | 1,94 sn / 3,81 sn | 0.0444 USD |
| gemma4_venice | 192 | 37 | 17/17 (100%) | **0** | 95 / 2 / 10 | 76/96 (79%) | 2/5 (40%) | 2/13 (15%) | 0 (belge içi varyant doğru 0/2) | 733 ms / 1,04 sn | 1,52 sn / 2,23 sn | 0.0620 USD |

İlk doğrulanmış cümle: model isteğinden, akışta ilk geçen öğenin tamamlandığı ana (model tarafı; uçtan uca süre ayrıca, arama öncesi dahil). Değer aynı: netleştirme ya da iki ürünün kaynağını birlikte gösteren doğrulanmış cevap doğru sayılır.

## Girintili JSON (sağlayıcı ve koşu bazında)

Aynı istek ve şemada sağlayıcının JSON'u girintili yazıp yazmadığı. Girinti çıktı tokeni ve kesik demek.

| Koşu | başlangıç | sağlayıcı | şema | girintili / çıktılı | çıktı tokeni p50 (cevap) | kesik (finish=length) | ilk doğrulanmış cümle p50 / p95 |
|---|---|---|---|---|---|---|---|
| nihai_c_gemma4 | 2026-11-05 16:16 | deepinfra | c | 0/192 (0%) | 254 | 1 | 2,52 sn / 6,74 sn |
| nihai_c_gemma4_nextbit | 2026-11-05 16:16 | nextbit | c | 178/192 (93%) | 248 | 29 | 2,58 sn / 4,45 sn |
| nihai_bugun_gemma4 | 2026-11-05 16:16 | deepinfra | bugun | 0/192 (0%) | 211 | 0 | – / – |
| nihai_c_gemma4_parasail | 2026-11-05 16:16 | parasail | c | 184/192 (96%) | 246 | 34 | 1,53 sn / 2,80 sn |
| nihai_c_gemma4_venice | 2026-11-05 16:16 | venice | c | 0/192 (0%) | 261 | 1 | 2,74 sn / 6,67 sn |
| nihai_sure1_gemma4 | 2026-11-05 16:37 | deepinfra | c | 0/29 (0%) | 245 | 0 | 1,83 sn / 3,36 sn |
| nihai_sure1_gemma4_nextbit | 2026-11-05 16:37 | nextbit | c | 26/29 (90%) | 338 | 7 | 2,26 sn / 3,14 sn |
| nihai_sure1_gemma4_parasail | 2026-11-05 16:55 | parasail | c | 28/29 (97%) | 282 | 5 | 1,66 sn / 2,30 sn |
| nihai_sure1_gemma4_venice | 2026-11-05 16:56 | venice | c | 0/29 (0%) | 244 | 0 | 1,98 sn / 3,14 sn |
| nihai_c150b_gemma4 | 2026-11-05 17:57 | deepinfra | c150b | 0/192 (0%) | 176 | 2 | 2,37 sn / 4,69 sn |
| nihai_c150_gemma4 | 2026-11-05 17:57 | deepinfra | c150 | 0/192 (0%) | 233 | 0 | 2,42 sn / 4,30 sn |
| nihai_c150_gemma4_venice | 2026-11-05 17:57 | venice | c150 | 0/192 (0%) | 227 | 2 | 2,57 sn / 4,37 sn |
| nihai_c150b_gemma4_venice | 2026-11-05 17:57 | venice | c150b | 0/192 (0%) | 179 | 2 | 2,72 sn / 4,63 sn |
| nihai_ek_gemma4 | 2026-11-06 09:12 | deepinfra | c150b | 0/39 (0%) | 400 | 0 | 1,74 sn / 2,03 sn |
| nihai_ek_gemma4_venice | 2026-11-06 09:12 | venice | c150b | 29/39 (74%) | 223 | 1 | 2,32 sn / 2,32 sn |
| nihai_mt1200_gemma4 | 2026-11-06 09:24 | deepinfra | c150b | 0/3 (0%) | 631 | 0 | 1,98 sn / 2,10 sn |
| nihai_mt1200_gemma4_venice | 2026-11-06 09:24 | venice | c150b | 3/3 (100%) | 900 | 1 | 1,49 sn / 1,51 sn |
| **nihai_c150bT_gemma4** | 2026-11-06 09:25 | deepinfra | c150bT | 0/192 (0%) | 182 | 1 | 1,94 sn / 3,81 sn |
| **nihai_c150bT_gemma4_venice** | 2026-11-06 09:35 | venice | c150bT | 180/192 (94%) | 214 | 37 | 1,53 sn / 2,24 sn |
