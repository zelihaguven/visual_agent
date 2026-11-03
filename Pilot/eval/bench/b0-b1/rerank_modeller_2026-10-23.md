# Reranker karşılaştırması: rerank_modeller

2026-10-23T13:16:47 · commit `377ad66+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel · 31.6 GB RAM

Aynı aday listesi (rerank'sız aramanın ilk 20'si). Süre: yalnız rerank çağrısı, 1 çağrı/soru. MHz: o çağrı sırasında CPU'nun gerçek ortalama frekansı.

## Filtreli

| Yapılandırma | hit@1 | hit@5 | MRR | süre ort. | p50 | p95 | MHz ort. | yükleme |
|---|---|---|---|---|---|---|---|---|
| rerank yok (RRF) | 0,50 | 0,86 | 0,64 | – | – | – | – | – |
| `local:BAAI/bge-reranker-v2-m3:torch:512:4` | 0,75 | 0,86 | 0,80 | 13.99 sn | 14.12 sn | 24.40 sn | 2116 | 45.7 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx:512:4` | 0,75 | 0,86 | 0,80 | 13.51 sn | 13.38 sn | 25.39 sn | 2115 | 5.0 sn |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,78 | 0,86 | 0,81 | 6.74 sn | 6.70 sn | 14.22 sn | 2349 | 3.7 sn |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,69 | 0,92 | 0,78 | 54.26 sn | 54.93 sn | 102.02 sn | 2577 | 2.9 sn |
| `local:cross-encoder/mmarco-mMiniLMv2-L12-H384-v1:torch:512:4` | 0,61 | 0,83 | 0,70 | 1.30 sn | 1.37 sn | 2.09 sn | 2226 | 2.9 sn |
| `local:BAAI/bge-reranker-base:torch:512:4` | 0,53 | 0,69 | 0,59 | 3.73 sn | 3.93 sn | 6.17 sn | 2278 | 3.8 sn |
| `openrouter:cohere/rerank-v3.5` | 0,69 | 0,86 | 0,78 | 454 ms (ağ 465 ms) | 465 ms | 676 ms | 2082 | 0.4 sn |

FUSED_K etkisi (doğruluk; aynı skorlar ilk K adaya kısıtlanarak):

| Yapılandırma | K=10 hit@1/hit@5/MRR | K=15 | K=20 |
|---|---|---|---|
| `local:BAAI/bge-reranker-v2-m3:torch:512:4` | 0,75 / 0,83 / 0,79 | 0,75 / 0,86 / 0,80 | 0,75 / 0,86 / 0,80 |
| `local:BAAI/bge-reranker-v2-m3:onnx:512:4` | 0,75 / 0,83 / 0,79 | 0,75 / 0,86 / 0,80 | 0,75 / 0,86 / 0,80 |
| `local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4` | 0,78 / 0,83 / 0,81 | 0,78 / 0,86 / 0,81 | 0,78 / 0,86 / 0,81 |
| `local:jinaai/jina-reranker-v2-base-multilingual:torch:512:4` | 0,69 / 0,86 / 0,76 | 0,69 / 0,89 / 0,78 | 0,69 / 0,92 / 0,78 |
| `local:cross-encoder/mmarco-mMiniLMv2-L12-H384-v1:torch:512:4` | 0,61 / 0,83 / 0,70 | 0,61 / 0,81 / 0,70 | 0,61 / 0,83 / 0,70 |
| `local:BAAI/bge-reranker-base:torch:512:4` | 0,50 / 0,69 / 0,59 | 0,53 / 0,72 / 0,60 | 0,53 / 0,69 / 0,59 |
| `openrouter:cohere/rerank-v3.5` | 0,69 / 0,86 / 0,77 | 0,69 / 0,89 / 0,77 | 0,69 / 0,86 / 0,78 |
**Not (ölçüm hatası):** Bu koşuda jina modeli transformers 5'in `dtype="auto"` varsayılanıyla **bfloat16** yüklendi; bu CPU'da bf16 hızlandırması yok. jina'nın süresi (54 sn) geçersiz. float32 ile yeniden ölçüm: [rerank_jina_fp32_2026-10-23.md](rerank_jina_fp32_2026-10-23.md) (4,2 sn, doğruluk aynı). bge-v2-m3, mmarco ve bge-base zaten float32; onların süreleri geçerli. gte-multilingual-reranker-base, uzak kodu transformers 5.19 ile çalışmadığı için ölçülemedi.
