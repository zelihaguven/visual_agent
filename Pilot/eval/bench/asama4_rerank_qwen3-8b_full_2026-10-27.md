# Reranker karşılaştırması: asama4_rerank_qwen3-8b_full

2026-10-27T10:52:39 · commit `5f35276+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,78 | 0,89 | 0,83 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 | 0,89 | 0,80 | 5.82 sn | 5.37 sn | 10.56 sn | 2146 | 48.5 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,69 | 0,92 | 0,79 | 4.37 sn | 4.24 sn | 6.67 sn | 2012 | 9.0 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,75 | 0,92 | 0,83 | 410 ms (ağ 382 ms) | 382 ms | 543 ms | 1915 | 1.5 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,75 / 0,92 / 0,83 | 0,72 / 0,89 / 0,81 | 0,72 / 0,89 / 0,80 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,72 / 0,94 / 0,83 | 0,69 / 0,92 / 0,80 | 0,69 / 0,92 / 0,79 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,75 / 0,97 / 0,84 | 0,75 / 0,94 / 0,83 | 0,75 / 0,92 / 0,83 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,78 | 0,86 | 0,83 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,64 | 0,89 | 0,75 | 7.36 sn | 6.79 sn | 13.48 sn | 2155 | 48.5 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,56 | 0,92 | 0,70 | 5.24 sn | 5.50 sn | 8.16 sn | 2006 | 9.0 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 | 0,92 | 0,80 | 477 ms (ağ 402 ms) | 402 ms | 709 ms | 2113 | 1.5 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 / 0,92 / 0,80 | 0,64 / 0,89 / 0,75 | 0,64 / 0,89 / 0,75 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,64 / 0,94 / 0,77 | 0,56 / 0,94 / 0,71 | 0,56 / 0,92 / 0,70 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,72 / 0,97 / 0,83 | 0,69 / 0,94 / 0,81 | 0,69 / 0,92 / 0,80 |
