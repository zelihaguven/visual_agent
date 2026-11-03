# Arama ölçümü: asama1_onerilen

2026-10-23T14:43:06 · commit `377ad66+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Parametreler: `PREFETCH_K=30`, `FUSED_K=15`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions']`, `repeats=3`, `warmup=3`, `rerank=True`, `qdrant_mode=embedded`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,75 | 0,86 | 0,89 | 0,79 |
| questions | 12 | 0,83 | 1,00 | 1,00 | 0,90 |
| questions_ek | 12 | 0,67 | 0,83 | 0,92 | 0,71 |
| sekil_sorular | 12 | 0,75 | 0,75 | 0,75 | 0,75 |

## Süre (soru başına; setler: questions; 3 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 42 | 517 ms | 502 ms | 670 ms |
| qdrant_open | 42 | 0 ms | 0 ms | 0 ms |
| qdrant | 42 | 242 ms | 249 ms | 260 ms |
| rerank | 42 | 2.57 sn | 2.71 sn | 3.53 sn |
| total | 42 | 3.33 sn | 3.56 sn | 4.20 sn |

## ANN recall (dense, rastgele sorgu)

500 sorgu · recall@5: 1,00 · recall@20: 1,00

## Bellek

Mod: embedded · parça: 4196 · RAM artışı: 217.5 MB · disk: 51.2 MB

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'lı)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,69 | 0,86 | 0,89 | 0,77 |
| questions | 12 | 0,75 | 1,00 | 1,00 | 0,86 |
| questions_ek | 12 | 0,58 | 0,83 | 0,92 | 0,70 |
| sekil_sorular | 12 | 0,75 | 0,75 | 0,75 | 0,75 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 635 ms | 626 ms | 843 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 245 ms | 253 ms | 298 ms |
| rerank | 39 | 3.90 sn | 3.91 sn | 6.95 sn |
| total | 39 | 4.78 sn | 4.74 sn | 8.01 sn |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, sekil_sorular:N1, sekil_sorular:N2, sekil_sorular:N3

İlk sırada değil: questions:Q04 (2.), questions:Q15 (3.), questions_ek:Q24 (4.), questions_ek:Q25 (4.), questions_ek:Q28 (13.)

Bulunamadı beklenen, en iyi rerank skoru: questions:Q09 -5.47, questions:Q10 -3.97, questions_ek:Q31 -5.97

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
