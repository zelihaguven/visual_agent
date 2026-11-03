# Reranker karşılaştırması: asama4_rerank10k_uclu_tr

2026-11-03T16:56:42 · commit `e3b7480+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,86 | 0,98 | 0,91 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,84 | 0,98 | 0,89 | 0,83 / 0,99 / 0,90 | 442 ms (ağ 385 ms) | 385 ms | 647 ms | 2326 | 0.6 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,84 / 0,99 / 0,90 | 0,83 / 0,97 / 0,89 | 0,84 / 0,98 / 0,89 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,84 | 0,94 | 0,89 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,82 | 0,95 | 0,88 | 0,80 / 0,97 / 0,87 | 442 ms (ağ 382 ms) | 383 ms | 679 ms | 2433 | 0.6 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,81 / 0,96 / 0,87 | 0,80 / 0,96 / 0,87 | 0,82 / 0,95 / 0,88 |
