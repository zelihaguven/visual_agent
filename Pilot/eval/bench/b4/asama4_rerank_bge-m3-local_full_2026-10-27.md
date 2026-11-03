# Reranker karşılaştırması: asama4_rerank_bge-m3-local_full

2026-10-27T10:18:42 · commit `5f35276+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,44 | 0,86 | 0,61 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,75 | 0,86 | 0,81 | 7.02 sn | 6.93 sn | 10.96 sn | 2179 | 35.3 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,72 | 0,89 | 0,79 | 5.41 sn | 5.46 sn | 7.75 sn | 1932 | 5.8 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 | 0,89 | 0,77 | 490 ms (ağ 416 ms) | 417 ms | 859 ms | 1784 | 1.4 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 / 0,86 / 0,80 | 0,78 / 0,89 / 0,83 | 0,75 / 0,86 / 0,81 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,72 / 0,86 / 0,78 | 0,72 / 0,89 / 0,79 | 0,72 / 0,89 / 0,79 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 / 0,86 / 0,77 | 0,72 / 0,89 / 0,79 | 0,69 / 0,89 / 0,77 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,50 | 0,86 | 0,63 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,75 | 0,89 | 0,80 | 7.38 sn | 7.42 sn | 11.57 sn | 2137 | 35.3 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,64 | 0,89 | 0,74 | 5.38 sn | 5.80 sn | 8.47 sn | 1973 | 5.8 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,64 | 0,89 | 0,74 | 642 ms (ağ 430 ms) | 430 ms | 1.29 sn | 2079 | 1.4 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 / 0,86 / 0,79 | 0,75 / 0,89 / 0,81 | 0,75 / 0,89 / 0,80 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,61 / 0,86 / 0,71 | 0,64 / 0,89 / 0,74 | 0,64 / 0,89 / 0,74 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,64 / 0,86 / 0,74 | 0,64 / 0,89 / 0,75 | 0,64 / 0,89 / 0,74 |
