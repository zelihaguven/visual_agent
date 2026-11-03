# Arama ölçümü: asama3b_scale_qwen3_8b

2026-11-03T13:01:58 · commit `67afaca` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions', 'questions_ek', 'sekil_sorular']`, `repeats=1`, `warmup=3`, `rerank=False`, `access=None`, `source_strip=True`, `qdrant_mode=server`, `qdrant_url=http://127.0.0.1:6333`, `collection=scale_qwen3_8b`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 37 | 0,70 | 0,92 | 0,97 | 0,78 |
| questions | 13 | 0,62 | 1,00 | 1,00 | 0,74 |
| questions_ek | 12 | 0,92 | 0,92 | 0,92 | 0,92 |
| sekil_sorular | 12 | 0,58 | 0,83 | 1,00 | 0,69 |

## Süre (soru başına; setler: questions, questions_ek, sekil_sorular; 1 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 1.76 sn | 843 ms | 5.17 sn |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 26 ms | 25 ms | 37 ms |
| total | 39 | 1.78 sn | 869 ms | 5.20 sn |

## ANN recall (dense, rastgele sorgu)

300 sorgu · recall@5: 0,98 · recall@20: 0,96

## Bellek

mode: server · rss_mb: 5761.2 · storage_mb: 49528.2 · points: 999952 · indexed_vectors: 3088752 · segments: 10 · collection_disk_mb: 20564.8

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'sız: RRF sırası)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 37 | 0,70 | 0,86 | 0,95 | 0,77 |
| questions | 13 | 0,69 | 0,85 | 1,00 | 0,76 |
| questions_ek | 12 | 0,92 | 0,92 | 0,92 | 0,92 |
| sekil_sorular | 12 | 0,50 | 0,83 | 0,92 | 0,63 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 2.64 sn | 1.12 sn | 5.07 sn |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 41 ms | 42 ms | 54 ms |
| total | 39 | 2.68 sn | 1.17 sn | 5.12 sn |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q28

İlk sırada değil: questions:Q03 (3.), questions:Q06 (3.), questions:Q09 (4.), questions:Q12 (4.), questions:Q13 (2.), sekil_sorular:G3 (2.), sekil_sorular:N1 (7.), sekil_sorular:G6 (9.), sekil_sorular:G7 (3.), sekil_sorular:N3 (5.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
