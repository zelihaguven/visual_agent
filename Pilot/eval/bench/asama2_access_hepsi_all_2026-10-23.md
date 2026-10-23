# Arama ölçümü: asama2_access_hepsi_all

2026-10-23T15:16:41 · commit `675b7af+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions', 'questions_ek', 'sekil_sorular']`, `repeats=5`, `warmup=3`, `rerank=False`, `access=['g1']`, `qdrant_mode=server`, `qdrant_url=http://127.0.0.1:6333`, `collection=manuals`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,44 | 0,83 | 0,92 | 0,61 |
| questions | 12 | 0,58 | 1,00 | 1,00 | 0,74 |
| questions_ek | 12 | 0,67 | 0,83 | 0,92 | 0,74 |
| sekil_sorular | 12 | 0,08 | 0,67 | 0,83 | 0,34 |

## Süre (soru başına; setler: questions, questions_ek, sekil_sorular; 5 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 195 | 283 ms | 288 ms | 396 ms |
| qdrant_open | 195 | 0 ms | 0 ms | 0 ms |
| qdrant | 195 | 16 ms | 14 ms | 24 ms |
| total | 195 | 299 ms | 307 ms | 410 ms |

## ANN recall (dense, rastgele sorgu)

500 sorgu · recall@5: 1,00 · recall@20: 1,00

## Bellek

mode: server · rss_mb: 124.9 · storage_mb: 1582.9 · points: 4196 · indexed_vectors: 4196 · segments: 6 · collection_disk_mb: 791.4

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'sız: RRF sırası)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,44 | 0,81 | 0,92 | 0,60 |
| questions | 12 | 0,50 | 0,92 | 1,00 | 0,68 |
| questions_ek | 12 | 0,58 | 0,83 | 0,92 | 0,68 |
| sekil_sorular | 12 | 0,25 | 0,67 | 0,83 | 0,43 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 300 ms | 247 ms | 528 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 17 ms | 16 ms | 24 ms |
| total | 39 | 318 ms | 264 ms | 558 ms |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, sekil_sorular:N1, sekil_sorular:N2

İlk sırada değil: questions:Q03 (3.), questions:Q05 (2.), questions:Q06 (4.), questions:Q12 (3.), questions:Q15 (2.), questions_ek:Q25 (12.), questions_ek:Q28 (4.), questions_ek:Q29 (2.), sekil_sorular:G1 (6.), sekil_sorular:G2 (3.), sekil_sorular:G3 (2.), sekil_sorular:G4 (2.), sekil_sorular:G5 (2.), sekil_sorular:G7 (4.), sekil_sorular:G8 (3.), sekil_sorular:G9 (2.), sekil_sorular:N3 (20.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
