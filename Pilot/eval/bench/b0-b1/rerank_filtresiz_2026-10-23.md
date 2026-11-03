# Reranker karşılaştırması: rerank_filtresiz

2026-10-23T13:36:29 · commit `377ad66+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtresiz

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,50 | 0,83 | 0,63 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:torch:512:4` | 0,58 | 0,86 | 0,72 | 13.72 sn | 11.90 sn | 28.61 sn | 2248 | 27.9 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,67 | 0,86 | 0,75 | 6.03 sn | 5.37 sn | 13.03 sn | 2470 | 3.5 sn |
| `openrouter:cohere/rerank-v3.5` | 0,61 | 0,86 | 0,73 | 344 ms (ağ 303 ms) | 303 ms | 526 ms | 2661 | 0.2 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:torch:512:4` | 0,61 / 0,83 / 0,73 | 0,58 / 0,86 / 0,72 | 0,58 / 0,86 / 0,72 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,69 / 0,83 / 0,76 | 0,67 / 0,86 / 0,75 | 0,67 / 0,86 / 0,75 |
| `openrouter:cohere/rerank-v3.5` | 0,64 / 0,86 / 0,73 | 0,64 / 0,89 / 0,73 | 0,61 / 0,86 / 0,73 |
