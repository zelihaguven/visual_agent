# Reranker karşılaştırması: rerank_duzeltme_qwen3-8b_full

2026-10-27T12:32:29 · commit `f130ac4+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,78 | 0,89 | 0,83 | – | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 | 0,89 | 0,80 | 0,78 / 0,92 / 0,83 | 4.45 sn | 3.90 sn | 8.46 sn | 2596 | 37.3 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,75 | 0,92 | 0,83 | 0,81 / 0,89 / 0,85 | 5.10 sn | 4.66 sn | 8.14 sn | 2592 | 0.0 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,69 | 0,92 | 0,79 | 0,83 / 0,94 / 0,88 | 3.52 sn | 3.32 sn | 5.58 sn | 2415 | 5.7 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,72 | 0,92 | 0,81 | 0,83 / 0,94 / 0,89 | 3.80 sn | 3.37 sn | 6.81 sn | 2547 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,75 | 0,92 | 0,83 | 0,75 / 0,94 / 0,83 | 440 ms (ağ 383 ms) | 383 ms | 623 ms | 2294 | 1.1 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 | 0,94 | 0,83 | 0,78 / 0,92 / 0,84 | 474 ms (ağ 365 ms) | 365 ms | 991 ms | 2171 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,72 | 0,97 | 0,83 | 0,78 / 0,94 / 0,84 | 469 ms (ağ 367 ms) | 367 ms | 770 ms | 1994 | 0.0 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,75 / 0,92 / 0,83 | 0,72 / 0,89 / 0,81 | 0,72 / 0,89 / 0,80 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,81 / 0,94 / 0,86 | 0,78 / 0,92 / 0,84 | 0,75 / 0,92 / 0,83 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,72 / 0,94 / 0,83 | 0,69 / 0,92 / 0,80 | 0,69 / 0,92 / 0,79 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,72 / 0,94 / 0,83 | 0,72 / 0,92 / 0,81 | 0,72 / 0,92 / 0,81 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,75 / 0,97 / 0,84 | 0,75 / 0,94 / 0,83 | 0,75 / 0,92 / 0,83 |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 / 0,94 / 0,83 | 0,75 / 0,92 / 0,83 | 0,75 / 0,94 / 0,83 |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,75 / 0,94 / 0,84 | 0,75 / 0,94 / 0,84 | 0,72 / 0,97 / 0,83 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,78 | 0,86 | 0,83 | – | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,64 | 0,89 | 0,75 | 0,81 / 0,94 / 0,85 | 5.53 sn | 5.42 sn | 9.71 sn | 2700 | 37.3 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,72 | 0,94 | 0,82 | 0,86 / 0,92 / 0,89 | 6.56 sn | 6.13 sn | 10.35 sn | 2611 | 0.0 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,56 | 0,92 | 0,70 | 0,83 / 0,94 / 0,88 | 4.42 sn | 3.72 sn | 6.22 sn | 2426 | 5.7 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,72 | 0,92 | 0,81 | 0,81 / 0,94 / 0,87 | 4.39 sn | 4.08 sn | 6.34 sn | 2438 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,72 | 0,92 | 0,82 | 0,75 / 0,92 / 0,83 | 519 ms (ağ 428 ms) | 428 ms | 910 ms | 2260 | 1.1 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 | 0,92 | 0,83 | 0,78 / 0,92 / 0,83 | 563 ms (ağ 437 ms) | 437 ms | 1.76 sn | 2379 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,72 | 0,97 | 0,83 | 0,78 / 0,94 / 0,84 | 484 ms (ağ 394 ms) | 395 ms | 821 ms | 2353 | 0.0 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 / 0,92 / 0,80 | 0,64 / 0,89 / 0,75 | 0,64 / 0,89 / 0,75 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,78 / 0,97 / 0,86 | 0,75 / 0,94 / 0,84 | 0,72 / 0,94 / 0,82 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,64 / 0,94 / 0,77 | 0,56 / 0,94 / 0,71 | 0,56 / 0,92 / 0,70 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,75 / 0,94 / 0,84 | 0,72 / 0,94 / 0,82 | 0,72 / 0,92 / 0,81 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,75 / 0,97 / 0,84 | 0,72 / 0,94 / 0,82 | 0,72 / 0,92 / 0,82 |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 / 0,94 / 0,84 | 0,75 / 0,92 / 0,83 | 0,75 / 0,92 / 0,83 |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,75 / 0,94 / 0,84 | 0,75 / 0,94 / 0,84 | 0,72 / 0,97 / 0,83 |
