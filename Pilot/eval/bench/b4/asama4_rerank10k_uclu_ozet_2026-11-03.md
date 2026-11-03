# Üçlü füzyon + reranker, 10k (A + reranker ile karşılaştırma) — **geçici, onaysız set**

Aynı 158 cevaplı soru · aday listesi RRF ilk 20 · reranker: `openrouter:qwen/qwen3-reranker-8b@embed`, sıra = reranker sırası + hibrit sıra RRF birleşimi (B4 düzeltmesi) · onaysız sorular dahil, sayılar karar için kullanılmaz

Harcama (reranker çağrıları, API'nin usage alanı): A: Qwen3-8B + BM25 0.326 USD, Üçlü füzyon 0.325 USD, Üçlü, BM25 çevirili 0.324 USD · toplam 0.976 USD

## Filtreli

| Küme | n | A: Qwen3-8B + BM25, rerank'sız: hit@1 | hit@5 | A: Qwen3-8B + BM25, reranker: hit@1 | hit@5 | Üçlü füzyon, rerank'sız: hit@1 | hit@5 | Üçlü füzyon, reranker: hit@1 | hit@5 | Üçlü, BM25 çevirili, rerank'sız: hit@1 | hit@5 | Üçlü, BM25 çevirili, reranker: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Toplam | 158 | 0,75 | 0,87 | 0,80 | 0,93 | 0,81 | 0,94 | 0,83 | 0,95 | 0,86 | 0,98 | 0,83 | 0,99 |
| Tür: değer | 90 | 0,68 | 0,82 | 0,74 | 0,92 | 0,77 | 0,91 | 0,80 | 0,92 | 0,83 | 0,97 | 0,80 | 0,99 |
| Tür: prosedür | 19 | 0,79 | 0,89 | 0,84 | 0,89 | 0,84 | 1,00 | 0,89 | 1,00 | 0,89 | 1,00 | 0,89 | 1,00 |
| Tür: kod | 19 | 0,95 | 1,00 | 0,95 | 0,95 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 0,95 | 1,00 |
| Tür: arıza | 8 | 0,88 | 1,00 | 1,00 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 0,93 | 0,79 | 0,93 | 0,71 | 0,93 | 0,79 | 1,00 | 0,71 | 0,93 |
| Tür: diğer | 8 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |

## Filtresiz

| Küme | n | A: Qwen3-8B + BM25, rerank'sız: hit@1 | hit@5 | A: Qwen3-8B + BM25, reranker: hit@1 | hit@5 | Üçlü füzyon, rerank'sız: hit@1 | hit@5 | Üçlü füzyon, reranker: hit@1 | hit@5 | Üçlü, BM25 çevirili, rerank'sız: hit@1 | hit@5 | Üçlü, BM25 çevirili, reranker: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Toplam | 158 | 0,75 | 0,86 | 0,77 | 0,90 | 0,79 | 0,93 | 0,82 | 0,95 | 0,84 | 0,94 | 0,80 | 0,97 |
| Tür: değer | 90 | 0,66 | 0,81 | 0,69 | 0,86 | 0,73 | 0,89 | 0,77 | 0,92 | 0,79 | 0,90 | 0,74 | 0,96 |
| Tür: prosedür | 19 | 0,84 | 0,89 | 0,84 | 0,89 | 0,84 | 1,00 | 0,89 | 1,00 | 0,89 | 1,00 | 0,89 | 1,00 |
| Tür: kod | 19 | 0,95 | 1,00 | 0,95 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 0,95 | 1,00 |
| Tür: arıza | 8 | 1,00 | 1,00 | 1,00 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 0,93 | 0,79 | 0,93 | 0,71 | 0,93 | 0,79 | 0,93 | 0,71 | 0,93 |
| Tür: diğer | 8 | 0,75 | 0,88 | 0,75 | 1,00 | 0,75 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |

