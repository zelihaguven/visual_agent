# Arama ölçümü: asama2_gomulu

2026-10-23T15:10:12 · commit `675b7af+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions', 'questions_ek', 'sekil_sorular']`, `repeats=5`, `warmup=3`, `rerank=False`, `access=None`, `qdrant_mode=embedded`, `qdrant_url=None`, `collection=manuals`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,50 | 0,86 | 0,92 | 0,64 |
| questions | 12 | 0,58 | 1,00 | 1,00 | 0,75 |
| questions_ek | 12 | 0,67 | 0,83 | 0,92 | 0,74 |
| sekil_sorular | 12 | 0,25 | 0,75 | 0,83 | 0,43 |

## Süre (soru başına; setler: questions, questions_ek, sekil_sorular; 5 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 195 | 191 ms | 188 ms | 226 ms |
| qdrant_open | 195 | 0 ms | 0 ms | 0 ms |
| qdrant | 195 | 291 ms | 306 ms | 358 ms |
| total | 195 | 483 ms | 500 ms | 571 ms |

## ANN recall (dense, rastgele sorgu)

500 sorgu · recall@5: 1,00 · recall@20: 1,00

## Bellek

mode: embedded · points: 4196 · rss_delta_mb: 217.3 · disk_mb: 51.2

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'sız: RRF sırası)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,50 | 0,83 | 0,92 | 0,63 |
| questions | 12 | 0,67 | 0,92 | 1,00 | 0,77 |
| questions_ek | 12 | 0,58 | 0,83 | 0,92 | 0,69 |
| sekil_sorular | 12 | 0,25 | 0,75 | 0,83 | 0,43 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 209 ms | 204 ms | 248 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 170 ms | 170 ms | 206 ms |
| total | 39 | 379 ms | 369 ms | 443 ms |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, sekil_sorular:N1, sekil_sorular:N2

İlk sırada değil: questions:Q03 (3.), questions:Q05 (2.), questions:Q06 (3.), questions:Q12 (3.), questions:Q15 (2.), questions_ek:Q25 (12.), questions_ek:Q28 (3.), questions_ek:Q29 (2.), sekil_sorular:G1 (5.), sekil_sorular:G2 (3.), sekil_sorular:G3 (2.), sekil_sorular:G7 (4.), sekil_sorular:G8 (3.), sekil_sorular:G9 (2.), sekil_sorular:N3 (19.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
