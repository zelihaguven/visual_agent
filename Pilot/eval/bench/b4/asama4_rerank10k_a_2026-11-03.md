# Reranker karşılaştırması: asama4_rerank10k_a

2026-11-03T15:37:14 · commit `5809129+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,69 | 0,84 | 0,75 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,74 | 0,91 | 0,82 | 0,72 / 0,89 / 0,80 | 499 ms (ağ 386 ms) | 386 ms | 1.06 sn | 1898 | 0.9 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,72 / 0,87 / 0,79 | 0,74 / 0,91 / 0,81 | 0,74 / 0,91 / 0,82 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,68 | 0,82 | 0,74 | – | – | – | – | – | – |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,69 | 0,90 | 0,79 | 0,70 / 0,86 / 0,77 | 570 ms (ağ 481 ms) | 481 ms | 1.30 sn | 1892 | 0.9 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,68 / 0,86 / 0,76 | 0,69 / 0,88 / 0,77 | 0,69 / 0,90 / 0,79 |
