# Şemaya zorlamanın ilk istekteki ek süresi (sağlayıcı bazında)

Aynı sorular, şemalı (json_schema, şema C) ve şemasız istek iç içe; ilk token. Adım 2 planı §15.0/§20.

| Tur | Yapılandırma | Sağlayıcı | n | şemalı p50 | p95 | şemasız p50 | p95 | fark p50 (eşli) | hata |
|---|---|---|---|---|---|---|---|---|---|
| s1 (16:37) | gemma4 | deepinfra | 10 | 394 ms | 845 ms | 354 ms | 1,11 sn | 9 ms | 0 |
| s1 (16:37) | qwen36 | deepinfra | 10 | 621 ms | 2,42 sn | 634 ms | 833 ms | 81 ms | 0 |
| s1 (16:37) | gpt54mini | azure | 10 | 1,33 sn | 4,81 sn | 935 ms | 1,23 sn | 395 ms | 0 |
| s1 (16:37) | mistral2603 | mistral | 10 | 463 ms | 915 ms | 475 ms | 704 ms | -34 ms | 0 |
| s1 (16:37) | gemma4_nextbit | nextbit | 10 | 324 ms | 660 ms | 260 ms | 453 ms | 72 ms | 0 |
| s1 (16:37) | gemma4_parasail | parasail | 10 | 814 ms | 1,10 sn | 580 ms | 875 ms | 146 ms | 0 |
| s1 (16:37) | gemma4_venice | venice | 10 | 534 ms | 852 ms | 438 ms | 1,18 sn | 60 ms | 0 |
| s1 (16:37) | gemma4_31b | crusoe | 10 | 496 ms | 2,01 sn | 443 ms | 674 ms | 86 ms | 5 |
