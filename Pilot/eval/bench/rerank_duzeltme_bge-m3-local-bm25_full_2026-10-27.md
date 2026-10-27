# Reranker karşılaştırması: rerank_duzeltme_bge-m3-local-bm25_full

2026-10-27T12:04:35 · commit `f130ac4+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,72 | 0,89 | 0,79 | – | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 | 0,86 | 0,79 | 0,78 / 0,89 / 0,83 | 5.27 sn | 5.09 sn | 8.73 sn | 2366 | 26.6 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,69 | 0,92 | 0,80 | 0,78 / 0,89 / 0,83 | 5.91 sn | 5.77 sn | 9.26 sn | 2356 | 0.0 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,67 | 0,92 | 0,77 | 0,78 / 0,89 / 0,83 | 3.78 sn | 3.78 sn | 6.06 sn | 2221 | 4.0 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,72 | 0,89 | 0,79 | 0,69 / 0,89 / 0,79 | 3.84 sn | 3.82 sn | 6.15 sn | 2425 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,72 | 0,94 | 0,81 | 0,75 / 0,89 / 0,82 | 667 ms (ağ 386 ms) | 387 ms | 1.62 sn | 1993 | 1.1 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 | 0,94 | 0,83 | 0,78 / 0,89 / 0,84 | 455 ms (ağ 384 ms) | 384 ms | 661 ms | 1839 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,72 | 0,89 | 0,81 | 0,75 / 0,89 / 0,81 | 436 ms (ağ 380 ms) | 380 ms | 665 ms | 1758 | 0.0 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,69 / 0,89 / 0,77 | 0,72 / 0,86 / 0,79 | 0,72 / 0,86 / 0,79 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,69 / 0,92 / 0,79 | 0,69 / 0,89 / 0,79 | 0,69 / 0,92 / 0,80 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,67 / 0,89 / 0,76 | 0,67 / 0,89 / 0,76 | 0,67 / 0,92 / 0,77 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,69 / 0,89 / 0,76 | 0,72 / 0,89 / 0,79 | 0,72 / 0,89 / 0,79 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 / 0,92 / 0,78 | 0,72 / 0,92 / 0,80 | 0,72 / 0,94 / 0,81 |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,72 / 0,92 / 0,80 | 0,75 / 0,92 / 0,82 | 0,75 / 0,94 / 0,83 |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,72 / 0,89 / 0,79 | 0,75 / 0,86 / 0,81 | 0,72 / 0,89 / 0,81 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | füzyonla hit@1 / hit@5 / MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,67 | 0,86 | 0,75 | – | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,61 | 0,89 | 0,72 | 0,72 / 0,86 / 0,79 | 6.06 sn | 5.76 sn | 9.49 sn | 2460 | 26.6 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,67 | 0,92 | 0,77 | 0,72 / 0,89 / 0,79 | 7.20 sn | 6.94 sn | 11.32 sn | 2342 | 0.0 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,58 | 0,92 | 0,71 | 0,72 / 0,86 / 0,78 | 4.51 sn | 4.40 sn | 6.56 sn | 2180 | 4.0 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,69 | 0,89 | 0,77 | 0,67 / 0,86 / 0,75 | 4.72 sn | 4.38 sn | 7.03 sn | 2211 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 | 0,94 | 0,78 | 0,69 / 0,86 / 0,78 | 492 ms (ağ 463 ms) | 463 ms | 884 ms | 2025 | 1.1 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 | 0,94 | 0,83 | 0,75 / 0,89 / 0,81 | 555 ms (ağ 466 ms) | 466 ms | 1.58 sn | 2285 | 0.0 sn |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,72 | 0,89 | 0,81 | 0,75 / 0,86 / 0,80 | 461 ms (ağ 473 ms) | 473 ms | 564 ms | 2111 | 0.0 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,64 / 0,86 / 0,73 | 0,61 / 0,86 / 0,72 | 0,61 / 0,89 / 0,72 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4@embed` | 0,67 / 0,89 / 0,76 | 0,69 / 0,89 / 0,78 | 0,67 / 0,92 / 0,77 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,53 / 0,83 / 0,67 | 0,56 / 0,86 / 0,68 | 0,58 / 0,92 / 0,71 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4@embed` | 0,64 / 0,86 / 0,72 | 0,67 / 0,89 / 0,75 | 0,69 / 0,89 / 0,77 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,67 / 0,86 / 0,75 | 0,69 / 0,92 / 0,78 | 0,69 / 0,94 / 0,78 |
| `openrouter:qwen/qwen3-reranker-8b@embed` | 0,75 / 0,89 / 0,80 | 0,75 / 0,92 / 0,82 | 0,75 / 0,94 / 0,83 |
| `openrouter:qwen/qwen3-reranker-8b@embed@inst` | 0,69 / 0,83 / 0,76 | 0,72 / 0,86 / 0,79 | 0,72 / 0,89 / 0,81 |
