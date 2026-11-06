# Akış bekçisi benzetimi (kayıtlardan; model çağrısı yok)

Kural: akışta art arda N'den fazla boşluk karakteri gelirse akış kesilir, istek bir kez yeniden gönderilir. Uygulamaya bağlı değil. Araç: `bench/akis_bekcisi.py`. Yaklaşık (≈): kayıtta akış zaman çizelgesi yok, yakalama anı karakter konumundan doğrusal.

## N = 20

| Sağlayıcı | Koşu | model çağrısı | kesik: yakalanan / kaçan | yanlış alarm | yakalama anı p50 / p95 | ikinci deneme ilk doğr. cümle p50 / p95 | toplam bedel p50 / p95 | ikinci denemede yine kaçak (tahmin) | kullanıcıya ulaşmayan (tahmin) |
|---|---|---|---|---|---|---|---|---|---|
| Venice | c150bJ_gemma4_venice | 192 | 16 / 0 | 0 | 1,64 sn / 2,62 sn | 1,39 sn / 2,30 sn | 3,03 sn / 4,91 sn | 38% (koşu çiftleri: 18 / 47) | 6.1 (3.2%) |
| Venice | c150bT_gemma4_venice | 192 | 31 / 6 | 0 | ≈ 2,58 sn / 4,76 sn | 1,53 sn / 2,24 sn | ≈ 4,11 sn / 7,00 sn | 38% (koşu çiftleri: 18 / 47) | 17.9 (9.3%) |
| Venice | c150b_gemma4_venice | 192 | 0 / 2 | 0 | – / – | 2,72 sn / 4,63 sn | – / – | 38% (koşu çiftleri: 18 / 47) | 2.0 (1.0%) |
| Parasail | c150bJ_gemma4_parasail | 192 | 12 / 0 | 0 | 1,65 sn / 4,98 sn | 1,26 sn / 2,03 sn | 2,91 sn / 7,01 sn | 43% (koşu çiftleri: 24 / 56) | 5.1 (2.7%) |
| Parasail | c_gemma4_parasail | 192 | 29 / 5 | 0 | ≈ 1,68 sn / 4,69 sn | 1,53 sn / 2,80 sn | ≈ 3,21 sn / 7,48 sn | 43% (koşu çiftleri: 24 / 56) | 17.4 (9.1%) |
| Parasail | sure1_gemma4_parasail | 29 | 5 / 0 | 0 | ≈ 2,40 sn / 5,11 sn | 1,66 sn / 2,30 sn | ≈ 4,06 sn / 7,41 sn | 43% (koşu çiftleri: 24 / 56) | 2.1 (7.4%) |
| NextBit | c_gemma4_nextbit | 192 | 29 / 0 | 0 | ≈ 5,22 sn / 11,00 sn | 2,58 sn / 4,45 sn | ≈ 7,79 sn / 15,45 sn | 60% (koşu çiftleri: 6 / 10) | 17.4 (9.1%) |
| NextBit | sure1_gemma4_nextbit | 29 | 7 / 0 | 0 | ≈ 4,79 sn / 13,46 sn | 2,26 sn / 3,14 sn | ≈ 7,05 sn / 16,60 sn | 60% (koşu çiftleri: 6 / 10) | 4.2 (14.5%) |
| Gemma 31B (Crusoe) | c_gemma4_31b | 192 | 31 / 1 | 0 | ≈ 0,57 sn / 0,95 sn | 1,37 sn / 2,66 sn | ≈ 1,93 sn / 3,61 sn | 75% (koşu çiftleri: 6 / 8) | 24.2 (12.6%) |
| Gemma 31B (Crusoe) | sure1_gemma4_31b | 29 | 4 / 0 | 0 | ≈ 0,57 sn / 2,11 sn | 1,41 sn / 2,86 sn | ≈ 1,98 sn / 4,97 sn | 75% (koşu çiftleri: 6 / 8) | 3.0 (10.3%) |
| DeepInfra | c150bJ_gemma4 | 192 | 0 / 0 | 0 | – / – | 1,56 sn / 2,56 sn | – / – | 0% (koşunun kaçak oranı) | 0.0 (0.0%) |
| DeepInfra | c150b_gemma4 | 192 | 0 / 2 | 0 | – / – | 2,37 sn / 4,69 sn | – / – | 0% (koşunun kaçak oranı) | 2.0 (1.0%) |

## N = 40

| Sağlayıcı | Koşu | model çağrısı | kesik: yakalanan / kaçan | yanlış alarm | yakalama anı p50 / p95 | ikinci deneme ilk doğr. cümle p50 / p95 | toplam bedel p50 / p95 | ikinci denemede yine kaçak (tahmin) | kullanıcıya ulaşmayan (tahmin) |
|---|---|---|---|---|---|---|---|---|---|
| Venice | c150bJ_gemma4_venice | 192 | 16 / 0 | 0 | 1,70 sn / 2,62 sn | 1,39 sn / 2,30 sn | 3,09 sn / 4,91 sn | 38% (koşu çiftleri: 18 / 47) | 6.1 (3.2%) |
| Venice | c150bT_gemma4_venice | 192 | 31 / 6 | 0 | ≈ 2,64 sn / 4,82 sn | 1,53 sn / 2,24 sn | ≈ 4,17 sn / 7,05 sn | 38% (koşu çiftleri: 18 / 47) | 17.9 (9.3%) |
| Venice | c150b_gemma4_venice | 192 | 0 / 2 | 0 | – / – | 2,72 sn / 4,63 sn | – / – | 38% (koşu çiftleri: 18 / 47) | 2.0 (1.0%) |
| Parasail | c150bJ_gemma4_parasail | 192 | 12 / 0 | 0 | 1,68 sn / 4,98 sn | 1,26 sn / 2,03 sn | 2,94 sn / 7,01 sn | 43% (koşu çiftleri: 24 / 56) | 5.1 (2.7%) |
| Parasail | c_gemma4_parasail | 192 | 29 / 5 | 0 | ≈ 1,76 sn / 4,81 sn | 1,53 sn / 2,80 sn | ≈ 3,28 sn / 7,61 sn | 43% (koşu çiftleri: 24 / 56) | 17.4 (9.1%) |
| Parasail | sure1_gemma4_parasail | 29 | 5 / 0 | 0 | ≈ 2,49 sn / 5,19 sn | 1,66 sn / 2,30 sn | ≈ 4,15 sn / 7,49 sn | 43% (koşu çiftleri: 24 / 56) | 2.1 (7.4%) |
| NextBit | c_gemma4_nextbit | 192 | 29 / 0 | 0 | ≈ 5,45 sn / 11,45 sn | 2,58 sn / 4,45 sn | ≈ 8,02 sn / 15,90 sn | 60% (koşu çiftleri: 6 / 10) | 17.4 (9.1%) |
| NextBit | sure1_gemma4_nextbit | 29 | 7 / 0 | 0 | ≈ 4,96 sn / 13,76 sn | 2,26 sn / 3,14 sn | ≈ 7,22 sn / 16,90 sn | 60% (koşu çiftleri: 6 / 10) | 4.2 (14.5%) |
| Gemma 31B (Crusoe) | c_gemma4_31b | 192 | 31 / 1 | 0 | ≈ 0,61 sn / 1,07 sn | 1,37 sn / 2,66 sn | ≈ 1,97 sn / 3,74 sn | 75% (koşu çiftleri: 6 / 8) | 24.2 (12.6%) |
| Gemma 31B (Crusoe) | sure1_gemma4_31b | 29 | 4 / 0 | 0 | ≈ 0,61 sn / 2,17 sn | 1,41 sn / 2,86 sn | ≈ 2,02 sn / 5,04 sn | 75% (koşu çiftleri: 6 / 8) | 3.0 (10.3%) |
| DeepInfra | c150bJ_gemma4 | 192 | 0 / 0 | 0 | – / – | 1,56 sn / 2,56 sn | – / – | 0% (koşunun kaçak oranı) | 0.0 (0.0%) |
| DeepInfra | c150b_gemma4 | 192 | 0 / 2 | 0 | – / – | 2,37 sn / 4,69 sn | – / – | 0% (koşunun kaçak oranı) | 2.0 (1.0%) |

## N = 80

| Sağlayıcı | Koşu | model çağrısı | kesik: yakalanan / kaçan | yanlış alarm | yakalama anı p50 / p95 | ikinci deneme ilk doğr. cümle p50 / p95 | toplam bedel p50 / p95 | ikinci denemede yine kaçak (tahmin) | kullanıcıya ulaşmayan (tahmin) |
|---|---|---|---|---|---|---|---|---|---|
| Venice | c150bJ_gemma4_venice | 192 | 16 / 0 | 0 | 1,74 sn / 2,77 sn | 1,39 sn / 2,30 sn | 3,13 sn / 5,07 sn | 38% (koşu çiftleri: 18 / 47) | 6.1 (3.2%) |
| Venice | c150bT_gemma4_venice | 192 | 31 / 6 | 0 | ≈ 2,76 sn / 4,92 sn | 1,53 sn / 2,24 sn | ≈ 4,29 sn / 7,16 sn | 38% (koşu çiftleri: 18 / 47) | 17.9 (9.3%) |
| Venice | c150b_gemma4_venice | 192 | 0 / 2 | 0 | – / – | 2,72 sn / 4,63 sn | – / – | 38% (koşu çiftleri: 18 / 47) | 2.0 (1.0%) |
| Parasail | c150bJ_gemma4_parasail | 192 | 12 / 0 | 0 | 1,75 sn / 5,09 sn | 1,26 sn / 2,03 sn | 3,01 sn / 7,12 sn | 43% (koşu çiftleri: 24 / 56) | 5.1 (2.7%) |
| Parasail | c_gemma4_parasail | 192 | 29 / 5 | 0 | ≈ 1,90 sn / 5,07 sn | 1,53 sn / 2,80 sn | ≈ 3,43 sn / 7,87 sn | 43% (koşu çiftleri: 24 / 56) | 17.4 (9.1%) |
| Parasail | sure1_gemma4_parasail | 29 | 5 / 0 | 0 | ≈ 2,67 sn / 5,35 sn | 1,66 sn / 2,30 sn | ≈ 4,33 sn / 7,65 sn | 43% (koşu çiftleri: 24 / 56) | 2.1 (7.4%) |
| NextBit | c_gemma4_nextbit | 192 | 29 / 0 | 0 | ≈ 5,90 sn / 12,22 sn | 2,58 sn / 4,45 sn | ≈ 8,48 sn / 16,67 sn | 60% (koşu çiftleri: 6 / 10) | 17.4 (9.1%) |
| NextBit | sure1_gemma4_nextbit | 29 | 7 / 0 | 0 | ≈ 5,30 sn / 14,35 sn | 2,26 sn / 3,14 sn | ≈ 7,56 sn / 17,49 sn | 60% (koşu çiftleri: 6 / 10) | 4.2 (14.5%) |
| Gemma 31B (Crusoe) | c_gemma4_31b | 192 | 31 / 1 | 0 | ≈ 0,69 sn / 1,32 sn | 1,37 sn / 2,66 sn | ≈ 2,06 sn / 3,98 sn | 75% (koşu çiftleri: 6 / 8) | 24.2 (12.6%) |
| Gemma 31B (Crusoe) | sure1_gemma4_31b | 29 | 4 / 0 | 0 | ≈ 0,70 sn / 2,30 sn | 1,41 sn / 2,86 sn | ≈ 2,11 sn / 5,16 sn | 75% (koşu çiftleri: 6 / 8) | 3.0 (10.3%) |
| DeepInfra | c150bJ_gemma4 | 192 | 0 / 0 | 0 | – / – | 1,56 sn / 2,56 sn | – / – | 0% (koşunun kaçak oranı) | 0.0 (0.0%) |
| DeepInfra | c150b_gemma4 | 192 | 0 / 2 | 0 | – / – | 2,37 sn / 4,69 sn | – / – | 0% (koşunun kaçak oranı) | 2.0 (1.0%) |

