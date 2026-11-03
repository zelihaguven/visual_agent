# Aşama 4: embedding × reranker

Aynı aday listesi (RRF ilk 20) üzerinde rerank. Süre p50: aday aşaması (sorgu embed + Qdrant, `questions` seti) + rerank. Geliştirme dizüstü, bulut çağrıları bu makinenin bağlantısından: üretimi temsil etmez. 36 soru: 5–8 puanın altındaki farklar gürültü.

## Filtreli (pipeline: doküman filtresi)

| Embedding | Reranker | hit@1 | hit@5 | MRR | rerank p50 | toplam p50 |
|---|---|---|---|---|---|---|
| bge-m3-local-bm25_full | yok | 0,72 | 0,89 | 0,79 | – | 227 ms |
| bge-m3-local-bm25_full | bge-reranker-v2-m3 int8 | 0,72 | 0,86 | 0,79 | 5.34 sn | 5.56 sn |
| bge-m3-local-bm25_full | jina-reranker-v2-base-multilingual | 0,67 | 0,92 | 0,77 | 4.21 sn | 4.43 sn |
| bge-m3-local-bm25_full | qwen3-reranker-8b | 0,72 | 0,94 | 0,81 | 385 ms | 611 ms |
| bge-m3-local_full | yok | 0,44 | 0,86 | 0,61 | – | 358 ms |
| bge-m3-local_full | bge-reranker-v2-m3 int8 | 0,75 | 0,86 | 0,81 | 6.93 sn | 7.29 sn |
| bge-m3-local_full | jina-reranker-v2-base-multilingual | 0,72 | 0,89 | 0,79 | 5.46 sn | 5.81 sn |
| bge-m3-local_full | qwen3-reranker-8b | 0,69 | 0,89 | 0,77 | 417 ms | 775 ms |
| qwen3-8b_full | yok | 0,78 | 0,89 | 0,83 | – | 692 ms |
| qwen3-8b_full | bge-reranker-v2-m3 int8 | 0,72 | 0,89 | 0,80 | 5.37 sn | 6.06 sn |
| qwen3-8b_full | jina-reranker-v2-base-multilingual | 0,69 | 0,92 | 0,79 | 4.24 sn | 4.94 sn |
| qwen3-8b_full | qwen3-reranker-8b | 0,75 | 0,92 | 0,83 | 382 ms | 1.07 sn |
| te3-large_full | yok | 0,78 | 0,92 | 0,83 | – | 722 ms |
| te3-large_full | bge-reranker-v2-m3 int8 | 0,72 | 0,89 | 0,81 | 4.96 sn | 5.69 sn |
| te3-large_full | jina-reranker-v2-base-multilingual | 0,67 | 0,94 | 0,77 | 3.84 sn | 4.57 sn |
| te3-large_full | qwen3-reranker-8b | 0,81 | 0,94 | 0,87 | 373 ms | 1.10 sn |

## Filtresiz (bütün koleksiyon)

| Embedding | Reranker | hit@1 | hit@5 | MRR | rerank p50 | toplam p50 |
|---|---|---|---|---|---|---|
| bge-m3-local-bm25_full | yok | 0,67 | 0,86 | 0,75 | – | 227 ms |
| bge-m3-local-bm25_full | bge-reranker-v2-m3 int8 | 0,61 | 0,89 | 0,72 | 6.46 sn | 6.68 sn |
| bge-m3-local-bm25_full | jina-reranker-v2-base-multilingual | 0,58 | 0,92 | 0,71 | 5.07 sn | 5.29 sn |
| bge-m3-local-bm25_full | qwen3-reranker-8b | 0,69 | 0,94 | 0,78 | 442 ms | 669 ms |
| bge-m3-local_full | yok | 0,50 | 0,86 | 0,63 | – | 358 ms |
| bge-m3-local_full | bge-reranker-v2-m3 int8 | 0,75 | 0,89 | 0,80 | 7.42 sn | 7.78 sn |
| bge-m3-local_full | jina-reranker-v2-base-multilingual | 0,64 | 0,89 | 0,74 | 5.80 sn | 6.16 sn |
| bge-m3-local_full | qwen3-reranker-8b | 0,64 | 0,89 | 0,74 | 430 ms | 789 ms |
| qwen3-8b_full | yok | 0,78 | 0,86 | 0,83 | – | 692 ms |
| qwen3-8b_full | bge-reranker-v2-m3 int8 | 0,64 | 0,89 | 0,75 | 6.79 sn | 7.48 sn |
| qwen3-8b_full | jina-reranker-v2-base-multilingual | 0,56 | 0,92 | 0,70 | 5.50 sn | 6.20 sn |
| qwen3-8b_full | qwen3-reranker-8b | 0,69 | 0,92 | 0,80 | 402 ms | 1.09 sn |
| te3-large_full | yok | 0,72 | 0,78 | 0,75 | – | 722 ms |
| te3-large_full | bge-reranker-v2-m3 int8 | 0,61 | 0,89 | 0,74 | 7.43 sn | 8.16 sn |
| te3-large_full | jina-reranker-v2-base-multilingual | 0,56 | 0,89 | 0,69 | 5.23 sn | 5.96 sn |
| te3-large_full | qwen3-reranker-8b | 0,69 | 0,89 | 0,79 | 467 ms | 1.19 sn |
