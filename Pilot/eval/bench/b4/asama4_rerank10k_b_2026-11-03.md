# Reranker karşılaştırması: asama4_rerank10k_b

2026-11-03T15:40:36 · commit `5809129+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,69 | 0,84 | 0,75 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,73 | 0,91 | 0,81 | 0,72 / 0,89 / 0,79 | 529 ms (ağ 378 ms) | 378 ms | 1.17 sn | 2201 | 0.7 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,72 / 0,87 / 0,79 | 0,72 / 0,91 / 0,80 | 0,73 / 0,91 / 0,81 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,68 | 0,82 | 0,74 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,69 | 0,90 | 0,79 | 0,70 / 0,86 / 0,78 | 561 ms (ağ 479 ms) | 479 ms | 1.18 sn | 2173 | 0.7 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,68 / 0,86 / 0,76 | 0,69 / 0,89 / 0,77 | 0,69 / 0,90 / 0,79 |
