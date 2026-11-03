# Reranker karşılaştırması: rerank_jina_fp32

2026-10-23T13:45:04 · commit `377ad66+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,50 | 0,86 | 0,64 | – | – | – | – | – |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,69 | 0,92 | 0,78 | 4.29 sn | 4.18 sn | 7.79 sn | 2370 | 31.4 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,78 | 0,86 | 0,81 | 5.76 sn | 5.21 sn | 11.49 sn | 2450 | 4.4 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,69 / 0,86 / 0,76 | 0,69 / 0,89 / 0,78 | 0,69 / 0,92 / 0,78 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,78 / 0,83 / 0,81 | 0,78 / 0,86 / 0,81 | 0,78 / 0,86 / 0,81 |
