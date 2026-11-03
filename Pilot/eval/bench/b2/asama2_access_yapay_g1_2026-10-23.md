# Arama ölçümü: asama2_access_yapay_g1

2026-10-23T15:21:22 · commit `675b7af+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions', 'questions_ek', 'sekil_sorular']`, `repeats=5`, `warmup=3`, `rerank=False`, `access=['g1']`, `qdrant_mode=server`, `qdrant_url=http://127.0.0.1:6333`, `collection=manuals_access`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,44 | 0,75 | 0,83 | 0,56 |
| questions | 12 | 0,58 | 0,92 | 1,00 | 0,72 |
| questions_ek | 12 | 0,67 | 0,83 | 0,92 | 0,72 |
| sekil_sorular | 12 | 0,08 | 0,50 | 0,58 | 0,26 |

## Süre (soru başına; setler: questions, questions_ek, sekil_sorular; 5 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 195 | 299 ms | 301 ms | 420 ms |
| qdrant_open | 195 | 0 ms | 0 ms | 0 ms |
| qdrant | 195 | 16 ms | 15 ms | 24 ms |
| total | 195 | 315 ms | 319 ms | 438 ms |

## ANN recall (dense, rastgele sorgu)

500 sorgu · recall@5: 1,00 · recall@20: 1,00

## Bellek

mode: server · rss_mb: 149.1 · storage_mb: 1582.9 · points: 4196 · indexed_vectors: 4196 · segments: 6 · collection_disk_mb: 791.4

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'sız: RRF sırası)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,50 | 0,72 | 0,83 | 0,58 |
| questions | 12 | 0,75 | 0,83 | 1,00 | 0,79 |
| questions_ek | 12 | 0,58 | 0,83 | 0,92 | 0,67 |
| sekil_sorular | 12 | 0,17 | 0,50 | 0,58 | 0,30 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 323 ms | 309 ms | 415 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 18 ms | 17 ms | 23 ms |
| total | 39 | 341 ms | 330 ms | 432 ms |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, sekil_sorular:G1, sekil_sorular:G2, sekil_sorular:G4, sekil_sorular:N1, sekil_sorular:N2

İlk sırada değil: questions:Q02 (2.), questions:Q03 (5.), questions:Q06 (6.), questions:Q12 (2.), questions:Q16 (4.), questions_ek:Q23 (4.), questions_ek:Q25 (9.), questions_ek:Q28 (4.), sekil_sorular:G3 (2.), sekil_sorular:G5 (2.), sekil_sorular:G7 (3.), sekil_sorular:G8 (3.), sekil_sorular:G9 (3.), sekil_sorular:N3 (13.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
