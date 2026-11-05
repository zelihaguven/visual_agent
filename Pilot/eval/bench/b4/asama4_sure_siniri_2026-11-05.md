# Süre sınırı ve yedek yol: aday yapılandırma, 160 cevaplı soru (10k, hattın kapsamıyla, rerank'sız)

Yalnız ölçüm aracında (`bench/latency_guard.py`); uygulamaya bağlı değil. Geliştirme dizüstü ve bu makinenin bağlantısı: **üretimi temsil etmez**. Onaysız set: geçici. Cevap modeli seçilmedi (PRD A1); `mistralai/mistral-small-24b-instruct-2501` yalnız gösterge.

Ayarlar: Qwen hedge 1.0 sn, yedek yol 1.5 sn, devre kesici 3/5/120 (aşım/son N/sn); çeviri sınırı 1.2 sn (aşınca BM25 çevirisiz); cevap hedge 1.2 sn, toplam sınır 20.0 sn.

## Yedek yola düşme

| Qwen sonucu | soru | oran |
|---|---|---|
| ilk istek zamanında | 28 | 18% |
| hedge kazandı | 2 | 1% |
| yedek yol (1,5 sn aşıldı) | 24 | 15% |
| devre kesici açık (Qwen beklenmedi) | 106 | 66% |

Çeviri sınırı aşılan: 54/156 çeviri çağrısı. Cevapta hedge açılan: 16, hedge kazanan: 2, ilk token gelmeyen: 11 (bunlardan sağlayıcı hız sınırı, 429: 11; ilk kelime yüzdeliklerine girmez).

## Doğruluğa etkisi (filtreli, aynı sorular)

| | n | hit@1 | hit@5 |
|---|---|---|---|
| Korumasız (her çağrı beklenir) | 160 | 0,82 | 0,96 |
| **Korumalı** | 160 | 0,77 | 0,94 |
| Yalnız yedek yola düşen sorular, korumasız | 130 | 0,79 | 0,95 |
| Yalnız yedek yola düşen sorular, korumalı | 130 | 0,73 | 0,93 |

## İlk kelime süresi (soru başından cevabın ilk tokenine)

| | p50 | p90 | p95 | en uzun |
|---|---|---|---|---|
| Korumasız (bileşik) | 2,76 sn | 9,85 sn | 11,44 sn | 19,53 sn |
| **Korumalı** | 1,56 sn | 2,21 sn | 2,42 sn | 5,53 sn |

Adım süreleri (p50 / p95; Qwen ve çeviri: çağrının kendi süresi, beklensin beklenmesin): Qwen embed 1,70 sn / 10,76 sn, bge-m3 embed 260 ms / 466 ms, çeviri 777 ms / 2,68 sn, grup 1 (korumalı) 1,07 sn / 1,51 sn, grup 2 Qdrant 22 ms / 42 ms

Sağlayıcılar: Qwen {"SiliconFlow": 2, "DeepInfra": 86, "Nebius": 72}, cevap {"DeepInfra": 149, "null": 11}.

Harcama: Qwen 0.00005, çeviri 0.0018, cevap 0.0215 USD (toplam 0.0233; sınır 0.3).
