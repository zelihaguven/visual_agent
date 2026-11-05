# Sağlayıcıya göre süre ve 429 dökümü (2026-11-05, kayıtlardan; yeni çağrı yok)

Soru: Kuyruk (uzun süre) ve 429 sorunları belirli bir sağlayıcıda (özellikle DeepInfra) mı toplanıyor? Araç: `python -m bench.provider_breakdown`. Süre sınırı ölçümünde çeviri çağrısının sağlayıcısı kaydedilmemişti; 3 Kasım kuyruk ölçümü sağlayıcı kaydetmiyor. Adım 2 ve çeviri ölçümlerinde her model tek sağlayıcıya sabit (karşılaştırma modeller ve saatler arası); süre sınırı ölçümünde Qwen sağlayıcıyı OpenRouter seçti.

## Qwen3-8B embed (süre sınırı ölçümü, çağrının kendi süresi)

Sağlayıcı sabitlenmedi: OpenRouter ZDR'li sağlayıcılar arasında seçti. Hedge kazanan 2 soru dışarıda.

| Ölçüm | Sağlayıcı | çağrı | süre p50 | p95 | en uzun | > 1,5 sn | 429 | diğer hata |
|---|---|---|---|---|---|---|---|---|
| süre sınırı 09:19 | DeepInfra | 84 | 1,38 sn | 10,72 sn | 16,55 sn | 39 | 0 | 0 |
| süre sınırı 09:19 | Nebius | 72 | 2,38 sn | 10,66 sn | 18,55 sn | 46 | 0 | 0 |
| süre sınırı 09:19 | SiliconFlow | 2 | 2,40 sn | 3,75 sn | 3,90 sn | 1 | 0 | 0 |

## Cevap modelleri (ilk token)

429 ve diğer hata: çağrı denemeleri (süre sınırı: ilk akışın hatası).

| Ölçüm | Sağlayıcı | çağrı | ilk token p50 | p95 | en uzun | > 1,5 sn | 429 | diğer hata |
|---|---|---|---|---|---|---|---|---|
| Adım 2 ana 11:16 · gemma4 | DeepInfra | 177 | 388 ms | 1,04 sn | 9,70 sn | 7 | 0 | 0 |
| Adım 2 ana 11:28 · qwen36 | DeepInfra | 177 | 648 ms | 1,57 sn | 7,45 sn | 11 | 0 | 0 |
| Adım 2 ana 11:52 · mistral2603 | Mistral | 177 | 449 ms | 991 ms | 1,53 sn | 2 | 0 | 0 |
| Adım 2 ana 11:59 · gpt54mini | Azure | 177 | 762 ms | 1,36 sn | 3,81 sn | 6 | 0 | 0 |
| Adım 2 sure2 14:41 · gemma4 | DeepInfra | 30 | 350 ms | 1,90 sn | 2,45 sn | 3 | 0 | 0 |
| Adım 2 sure2 14:43 · qwen36 | DeepInfra | 30 | 715 ms | 10,70 sn | 22,87 sn | 7 | 0 | 0 |
| Adım 2 sure2 14:49 · mistral2603 | Mistral | 30 | 468 ms | 840 ms | 2,06 sn | 1 | 0 | 0 |
| Adım 2 sure2 14:50 · gpt54mini | Azure | 30 | 776 ms | 1,06 sn | 1,31 sn | 0 | 0 | 0 |
| süre sınırı 09:19 · mistral-small 2501 | DeepInfra | 159 | 456 ms | 997 ms | 2,05 sn | 3 | 12 | 0 |

## Çeviri (çağrının tamamı)

Kollar iç içe, tek sağlayıcıya sabit, yeniden denemesiz.

| Ölçüm | Sağlayıcı | çağrı | süre p50 | p95 | en uzun | > 1,5 sn | 429 | diğer hata |
|---|---|---|---|---|---|---|---|---|
| çeviri t1 (14:25 bitiş) · g3_deepinfra | DeepInfra | 350 | 2,07 sn | 3,33 sn | 6,20 sn | 305 | 0 | 0 |
| çeviri t1 (14:25 bitiş) · g3_nextbit | NextBit | 350 | 794 ms | 2,05 sn | 2,92 sn | 57 | 0 | 0 |
| çeviri t1 (14:25 bitiş) · g4_nextbit | NextBit | 350 | 527 ms | 985 ms | 1,31 sn | 0 | 0 | 0 |
| çeviri t2 (15:20 bitiş) · g3_deepinfra | DeepInfra | 350 | 2,17 sn | 3,92 sn | 6,38 sn | 304 | 0 | 0 |
| çeviri t2 (15:20 bitiş) · g3_nextbit | NextBit | 350 | 743 ms | 2,19 sn | 3,70 sn | 46 | 0 | 0 |
| çeviri t2 (15:20 bitiş) · g4_nextbit | NextBit | 350 | 473 ms | 826 ms | 1,64 sn | 1 | 0 | 0 |
