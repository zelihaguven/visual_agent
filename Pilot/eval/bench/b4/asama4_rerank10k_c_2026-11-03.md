# Reranker karşılaştırması: asama4_rerank10k_c

2026-11-03T15:43:43 · commit `5809129+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,62 | 0,82 | 0,71 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,71 | 0,89 | 0,78 | 0,70 / 0,86 / 0,77 | 481 ms (ağ 382 ms) | 383 ms | 1.00 sn | 2067 | 0.6 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,69 / 0,86 / 0,77 | 0,69 / 0,89 / 0,77 | 0,71 / 0,89 / 0,78 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,62 | 0,78 | 0,69 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,70 | 0,88 | 0,77 | 0,67 / 0,85 / 0,75 | 529 ms (ağ 484 ms) | 484 ms | 1.02 sn | 2073 | 0.6 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,70 / 0,83 / 0,76 | 0,68 / 0,86 / 0,75 | 0,70 / 0,88 / 0,77 |
