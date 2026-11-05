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

## İlk kelime p95'inin aşama dökümü (korumalı yol, kayıttan; yeni koşu yok)

149 soru (cevabı gelen). Grup 2'de BM25 kolu ayrı kaydedilmedi: üç kol paralel, birlikte ölçüldü; BM25'e özgü bekleme çeviridir (grup 1).

| Aşama | p50 | p90 | p95 | en uzun | ortalama payı (en yavaş %10) |
|---|---|---|---|---|---|
| Qwen embed bekleme | 0 ms | 1,50 sn | 1,50 sn | 1,50 sn |  |
| Çeviri bekleme (BM25 kolu bunu bekler) | 824 ms | 1,20 sn | 1,20 sn | 2,68 sn |  |
| bge-m3 embed (CPU) | 262 ms | 397 ms | 470 ms | 5,04 sn |  |
| **Grup 1 duvar saati** (üçü paralel) | 1,12 sn | 1,50 sn | 1,51 sn | 5,04 sn | 57% |
| Grup 2: Qdrant 3 kol (BM25 dahil) + füzyon | 22 ms | 36 ms | 42 ms | 53 ms | 1% |
| Cevap modeli ilk token | 460 ms | 888 ms | 1,01 sn | 2,05 sn | 42% |
| **İlk kelime** | 1,56 sn | 2,21 sn | 2,42 sn | 5,53 sn |  |

**1,5 sn hangi aşamada aşıldı** (birikimli: grup 1 → grup 2 → cevap ilk token); ilk kelime p95 = 2,42 sn:

| Aşıldığı aşama | soru | oran |
|---|---|---|
| cevap modeli ilk token | 64 | 43% |
| aşılmadı | 61 | 41% |
| grup 1: Qwen bekleme | 23 | 15% |
| grup 1: bge-m3 embed | 1 | 1% |

En yavaş %10 (15 soru), soru başına zaman çizelgesi:

| İlk kelime | Qwen | çeviri | bge-m3 | grup 1 | grup 2 | cevap ilk token | 1,5 sn aşıldığı yer |
|---|---|---|---|---|---|---|---|
| 5,53 sn | 0 ms | 2,68 sn | 5,04 sn | 5,04 sn | 28 ms | 464 ms | grup 1: bge-m3 embed |
| 2,80 sn | 0 ms | 1,20 sn | 247 ms | 1,21 sn | 16 ms | 1,57 sn | cevap modeli ilk token |
| 2,73 sn | 609 ms | 1,07 sn | 242 ms | 1,07 sn | 29 ms | 1,63 sn | cevap modeli ilk token |
| 2,69 sn | 972 ms | 395 ms | 232 ms | 972 ms | 27 ms | 1,69 sn | cevap modeli ilk token |
| 2,62 sn | 1,50 sn | 1,22 sn | 358 ms | 1,51 sn | 19 ms | 1,10 sn | grup 1: Qwen bekleme |
| 2,49 sn | 1,50 sn | 1,20 sn | 225 ms | 1,51 sn | 19 ms | 966 ms | grup 1: Qwen bekleme |
| 2,49 sn | 0 ms | 846 ms | 266 ms | 846 ms | 34 ms | 1,61 sn | cevap modeli ilk token |
| 2,44 sn | 0 ms | 375 ms | 220 ms | 375 ms | 13 ms | 2,05 sn | cevap modeli ilk token |
| 2,40 sn | 1,50 sn | 563 ms | 252 ms | 1,50 sn | 16 ms | 883 ms | grup 1: Qwen bekleme |
| 2,40 sn | 1,47 sn | 1,20 sn | 233 ms | 1,47 sn | 21 ms | 906 ms | cevap modeli ilk token |
| 2,36 sn | 1,50 sn | 739 ms | 236 ms | 1,51 sn | 18 ms | 836 ms | grup 1: Qwen bekleme |
| 2,28 sn | 1,50 sn | 488 ms | 312 ms | 1,51 sn | 36 ms | 736 ms | grup 1: Qwen bekleme |
| 2,24 sn | 405 ms | 1,20 sn | 328 ms | 1,21 sn | 25 ms | 999 ms | cevap modeli ilk token |
| 2,23 sn | 1,50 sn | 1,20 sn | 278 ms | 1,50 sn | 27 ms | 696 ms | grup 1: Qwen bekleme |
| 2,21 sn | 1,50 sn | 219 ms | 208 ms | 1,50 sn | 19 ms | 693 ms | grup 1: Qwen bekleme |

Sağlayıcılar: Qwen {"SiliconFlow": 2, "DeepInfra": 86, "Nebius": 72}, cevap {"DeepInfra": 149, "null": 11}.

Harcama: Qwen 0.00005, çeviri 0.0018, cevap 0.0215 USD (toplam 0.0233; sınır 0.3).
