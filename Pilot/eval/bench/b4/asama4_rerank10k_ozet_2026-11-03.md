# B4 adım 2: 10k, 3 yol, qwen3-reranker-8b (bölüm düzeltmesi sonrası) — **geçici, onaysız set**

Aynı 160 cevaplı soru · aday listesi RRF ilk 20 · reranker: `openrouter:qwen/qwen3-reranker-8b@embed`, sıra = reranker sırası + hibrit sıra RRF birleşimi (B4 düzeltmesi) · onaysız sorular dahil, sayılar karar için kullanılmaz

Harcama (reranker çağrıları, API'nin usage alanı): A: Qwen3-8B + BM25, 256 ön eleme 0.326 USD, B: Qwen3-8B + BM25, tam vektör 0.326 USD, C: bge-m3 + BM25 0.339 USD · toplam 0.991 USD

## Filtreli

| Küme | n | A: Qwen3-8B + BM25, 256 ön eleme, rerank'sız: hit@1 | hit@5 | A: Qwen3-8B + BM25, 256 ön eleme, reranker: hit@1 | hit@5 | B: Qwen3-8B + BM25, tam vektör, rerank'sız: hit@1 | hit@5 | B: Qwen3-8B + BM25, tam vektör, reranker: hit@1 | hit@5 | C: bge-m3 + BM25, rerank'sız: hit@1 | hit@5 | C: bge-m3 + BM25, reranker: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Toplam | 160 | 0,69 | 0,84 | 0,72 | 0,89 | 0,69 | 0,84 | 0,72 | 0,89 | 0,62 | 0,82 | 0,70 | 0,86 |
| Tür: değer | 90 | 0,63 | 0,81 | 0,69 | 0,90 | 0,63 | 0,81 | 0,68 | 0,90 | 0,57 | 0,78 | 0,63 | 0,83 |
| Tür: prosedür | 20 | 0,55 | 0,70 | 0,55 | 0,70 | 0,55 | 0,70 | 0,55 | 0,70 | 0,65 | 0,85 | 0,70 | 0,85 |
| Tür: kod | 20 | 0,90 | 0,95 | 0,90 | 0,90 | 0,90 | 0,95 | 0,90 | 0,90 | 0,90 | 0,95 | 0,95 | 1,00 |
| Tür: arıza | 8 | 0,88 | 1,00 | 1,00 | 1,00 | 0,88 | 1,00 | 1,00 | 1,00 | 0,50 | 0,75 | 0,75 | 0,75 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 0,93 | 0,79 | 0,86 | 0,79 | 0,93 | 0,50 | 0,79 | 0,71 | 0,79 |
| Tür: diğer | 8 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 |

## Filtresiz

| Küme | n | A: Qwen3-8B + BM25, 256 ön eleme, rerank'sız: hit@1 | hit@5 | A: Qwen3-8B + BM25, 256 ön eleme, reranker: hit@1 | hit@5 | B: Qwen3-8B + BM25, tam vektör, rerank'sız: hit@1 | hit@5 | B: Qwen3-8B + BM25, tam vektör, reranker: hit@1 | hit@5 | C: bge-m3 + BM25, rerank'sız: hit@1 | hit@5 | C: bge-m3 + BM25, reranker: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Toplam | 160 | 0,68 | 0,82 | 0,70 | 0,86 | 0,68 | 0,82 | 0,70 | 0,86 | 0,62 | 0,78 | 0,67 | 0,85 |
| Tür: değer | 90 | 0,60 | 0,80 | 0,63 | 0,84 | 0,60 | 0,80 | 0,63 | 0,84 | 0,54 | 0,72 | 0,59 | 0,82 |
| Tür: prosedür | 20 | 0,60 | 0,70 | 0,60 | 0,70 | 0,60 | 0,70 | 0,60 | 0,70 | 0,70 | 0,85 | 0,70 | 0,85 |
| Tür: kod | 20 | 0,90 | 0,95 | 0,90 | 0,95 | 0,90 | 0,95 | 0,90 | 0,95 | 0,90 | 0,95 | 0,95 | 1,00 |
| Tür: arıza | 8 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 0,62 | 0,62 | 0,75 | 0,75 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 0,93 | 0,79 | 0,86 | 0,79 | 0,93 | 0,57 | 0,79 | 0,64 | 0,79 |
| Tür: diğer | 8 | 0,75 | 0,88 | 0,75 | 1,00 | 0,75 | 0,88 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 |

