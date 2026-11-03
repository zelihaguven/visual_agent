# Reranker karşılaştırması: asama4_rerank10k_uclu

2026-11-03T16:53:58 · commit `e3b7480+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,81 | 0,94 | 0,87 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,82 | 0,96 | 0,88 | 0,83 / 0,95 / 0,89 | 450 ms (ağ 375 ms) | 375 ms | 729 ms | 1966 | 0.8 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,80 / 0,94 / 0,87 | 0,81 / 0,96 / 0,87 | 0,82 / 0,96 / 0,88 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,79 | 0,93 | 0,86 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,80 | 0,96 | 0,87 | 0,82 / 0,95 / 0,87 | 457 ms (ağ 450 ms) | 450 ms | 612 ms | 1994 | 0.8 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,78 / 0,94 / 0,85 | 0,79 / 0,95 / 0,86 | 0,80 / 0,96 / 0,87 |
