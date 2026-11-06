# Çeviri: ikinci sağlayıcı süre ölçümü (Gemma 4; NextBit ile iç içe)

Adım 2 planı §21, devir notu c (2026-11-06). Tek sağlayıcıya sabit, yeniden denemesiz; süre çağrının tamamı. Filtreli (uygulamanın yolu) ve filtresiz çağrılar birlikte.

| Tur | Kol | çağrı | p50 | p95 | en uzun | > 1,2 sn | hata | sağlayıcı | maliyet |
|---|---|---|---|---|---|---|---|---|---|
| s1 (09:14) | g4_venice | 30 | 783 ms | 1,21 sn | 1,23 sn | 2/30 (7%) | 0 | {'Venice': 30} | 0.00072 |
| s1 (09:14) | g4_deepinfra | 30 | 899 ms | 1,82 sn | 3,15 sn | 6/30 (20%) | 0 | {'DeepInfra': 30} | 0.00047 |
| s1 (09:14) | g4_nextbit | 30 | 512 ms | 917 ms | 1,19 sn | 0/30 (0%) | 0 | {'NextBit': 30} | 0.00045 |
