# Arama ölçümü: asama2_sunucu_rerank

2026-10-23T15:38:14 · commit `675b7af+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions']`, `repeats=3`, `warmup=3`, `rerank=True`, `access=None`, `qdrant_mode=server`, `qdrant_url=http://127.0.0.1:6333`, `collection=manuals`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,75 | 0,86 | 0,92 | 0,80 |
| questions | 12 | 0,92 | 1,00 | 1,00 | 0,94 |
| questions_ek | 12 | 0,67 | 0,83 | 0,92 | 0,74 |
| sekil_sorular | 12 | 0,67 | 0,75 | 0,83 | 0,72 |

## Süre (soru başına; setler: questions; 3 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 42 | 388 ms | 382 ms | 526 ms |
| qdrant_open | 42 | 0 ms | 0 ms | 0 ms |
| qdrant | 42 | 20 ms | 19 ms | 27 ms |
| rerank | 42 | 13.39 sn | 14.03 sn | 17.42 sn |
| total | 42 | 13.80 sn | 14.36 sn | 17.80 sn |

## Bellek

mode: server · rss_mb: 156.2 · storage_mb: 1582.9 · points: 4196 · indexed_vectors: 4196 · segments: 6 · collection_disk_mb: 791.4

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, sekil_sorular:N1, sekil_sorular:N2

İlk sırada değil: questions:Q12 (3.), questions_ek:Q24 (3.), questions_ek:Q25 (2.), questions_ek:Q28 (17.), sekil_sorular:G3 (2.), sekil_sorular:N3 (7.)

Bulunamadı beklenen, en iyi rerank skoru: questions:Q09 -5.81, questions:Q10 -3.82, questions_ek:Q31 -5.83

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
