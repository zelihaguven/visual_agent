# Reranker düzeltmesi: önce / sonra

Aynı 36 soru, aynı aday listeleri (rerank'sız aramanın ilk 20'si). **Önce:** reranker'a başlıksız metin (`text`), sıra yalnız reranker skoru. **Sonra:** başlıklı metin (`embed_text`: marka, ürün, bölüm + metin) ve reranker sırası ile hibrit sıranın RRF birleşimi (k=60, standart sabit; bu sorulara göre seçilmedi). qwen3-reranker için ek olarak denenen görev talimatı (@inst) katkı vermedi, pipeline'a alınmadı. 36 soru: 5–8 puanın altındaki farklar gürültü. Teşhis: [rerank_teshis2_2026-10-27.md](rerank_teshis2_2026-10-27.md).

## bge-m3-local-bm25_full · filtreli

Rerank'sız: hit@1 0,72 · hit@5 0,89 · MRR 0,79

| Reranker | önce hit@1 / hit@5 / MRR | sonra hit@1 / hit@5 / MRR | Δ hit@1 |
|---|---|---|---|
| bge-v2-m3 int8 | 0,72 / 0,86 / 0,79 | 0,78 / 0,89 / 0,83 | +0,06 |
| jina-v2 | 0,67 / 0,92 / 0,77 | 0,69 / 0,89 / 0,79 | +0,03 |
| qwen3-reranker-8b (bulut) | 0,72 / 0,94 / 0,81 | 0,78 / 0,89 / 0,84 | +0,06 |

## bge-m3-local-bm25_full · filtresiz

Rerank'sız: hit@1 0,67 · hit@5 0,86 · MRR 0,75

| Reranker | önce hit@1 / hit@5 / MRR | sonra hit@1 / hit@5 / MRR | Δ hit@1 |
|---|---|---|---|
| bge-v2-m3 int8 | 0,61 / 0,89 / 0,72 | 0,72 / 0,89 / 0,79 | +0,11 |
| jina-v2 | 0,58 / 0,92 / 0,71 | 0,67 / 0,86 / 0,75 | +0,08 |
| qwen3-reranker-8b (bulut) | 0,69 / 0,94 / 0,78 | 0,75 / 0,89 / 0,81 | +0,06 |

## qwen3-8b_full · filtreli

Rerank'sız: hit@1 0,78 · hit@5 0,89 · MRR 0,83

| Reranker | önce hit@1 / hit@5 / MRR | sonra hit@1 / hit@5 / MRR | Δ hit@1 |
|---|---|---|---|
| bge-v2-m3 int8 | 0,72 / 0,89 / 0,80 | 0,81 / 0,89 / 0,85 | +0,08 |
| jina-v2 | 0,69 / 0,92 / 0,79 | 0,83 / 0,94 / 0,89 | +0,14 |
| qwen3-reranker-8b (bulut) | 0,75 / 0,92 / 0,83 | 0,78 / 0,92 / 0,84 | +0,03 |

## qwen3-8b_full · filtresiz

Rerank'sız: hit@1 0,78 · hit@5 0,86 · MRR 0,83

| Reranker | önce hit@1 / hit@5 / MRR | sonra hit@1 / hit@5 / MRR | Δ hit@1 |
|---|---|---|---|
| bge-v2-m3 int8 | 0,64 / 0,89 / 0,75 | 0,86 / 0,92 / 0,89 | +0,22 |
| jina-v2 | 0,56 / 0,92 / 0,70 | 0,81 / 0,94 / 0,87 | +0,25 |
| qwen3-reranker-8b (bulut) | 0,72 / 0,92 / 0,82 | 0,78 / 0,92 / 0,83 | +0,06 |

