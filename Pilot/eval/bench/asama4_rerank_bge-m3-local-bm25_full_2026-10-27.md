# Reranker karşılaştırması: asama4_rerank_bge-m3-local-bm25_full

2026-10-27T10:35:54 · commit `5f35276+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,72 | 0,89 | 0,79 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 | 0,86 | 0,79 | 5.72 sn | 5.34 sn | 9.84 sn | 2187 | 77.3 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,67 | 0,92 | 0,77 | 4.41 sn | 4.21 sn | 7.00 sn | 2070 | 10.3 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,72 | 0,94 | 0,81 | 425 ms (ağ 385 ms) | 385 ms | 617 ms | 1911 | 1.9 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,69 / 0,89 / 0,77 | 0,72 / 0,86 / 0,79 | 0,72 / 0,86 / 0,79 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,67 / 0,89 / 0,76 | 0,67 / 0,89 / 0,76 | 0,67 / 0,92 / 0,77 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 / 0,92 / 0,78 | 0,72 / 0,92 / 0,80 | 0,72 / 0,94 / 0,81 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,67 | 0,86 | 0,75 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,61 | 0,89 | 0,72 | 7.03 sn | 6.46 sn | 11.66 sn | 2198 | 77.3 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,58 | 0,92 | 0,71 | 5.35 sn | 5.07 sn | 7.70 sn | 2042 | 10.3 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 | 0,94 | 0,78 | 449 ms (ağ 442 ms) | 442 ms | 654 ms | 2151 | 1.9 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,64 / 0,86 / 0,73 | 0,61 / 0,86 / 0,72 | 0,61 / 0,89 / 0,72 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,53 / 0,83 / 0,67 | 0,56 / 0,86 / 0,68 | 0,58 / 0,92 / 0,71 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,67 / 0,86 / 0,75 | 0,69 / 0,92 / 0,78 | 0,69 / 0,94 / 0,78 |
