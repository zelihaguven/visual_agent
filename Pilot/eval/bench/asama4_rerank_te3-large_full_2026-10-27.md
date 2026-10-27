# Reranker karşılaştırması: asama4_rerank_te3-large_full

2026-10-27T11:08:19 · commit `5f35276+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,78 | 0,92 | 0,83 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,72 | 0,89 | 0,81 | 5.11 sn | 4.96 sn | 8.59 sn | 2223 | 35.4 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,67 | 0,94 | 0,77 | 3.88 sn | 3.84 sn | 6.21 sn | 2096 | 4.8 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,81 | 0,94 | 0,87 | 421 ms (ağ 373 ms) | 373 ms | 530 ms | 1902 | 0.9 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,81 / 0,94 / 0,86 | 0,75 / 0,89 / 0,82 | 0,72 / 0,89 / 0,81 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,64 / 0,94 / 0,77 | 0,67 / 0,94 / 0,77 | 0,67 / 0,94 / 0,77 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,81 / 0,92 / 0,86 | 0,81 / 0,94 / 0,87 | 0,81 / 0,94 / 0,87 |

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,72 | 0,78 | 0,75 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,61 | 0,89 | 0,74 | 7.31 sn | 7.43 sn | 10.35 sn | 2232 | 35.4 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,56 | 0,89 | 0,69 | 5.28 sn | 5.23 sn | 7.45 sn | 2042 | 4.8 sn |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 | 0,89 | 0,79 | 485 ms (ağ 467 ms) | 467 ms | 764 ms | 2146 | 0.9 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,64 / 0,83 / 0,72 | 0,69 / 0,86 / 0,77 | 0,61 / 0,89 / 0,74 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,56 / 0,81 / 0,66 | 0,56 / 0,86 / 0,68 | 0,56 / 0,89 / 0,69 |
| `openrouter:qwen/qwen3-reranker-8b` | 0,69 / 0,78 / 0,74 | 0,69 / 0,86 / 0,78 | 0,69 / 0,89 / 0,79 |
