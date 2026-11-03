# Arama ölçümü: asama3b_scale_bge_m3

2026-11-03T13:06:10 · commit `67afaca` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions', 'questions_ek', 'sekil_sorular']`, `repeats=1`, `warmup=3`, `rerank=False`, `access=None`, `source_strip=True`, `qdrant_mode=server`, `qdrant_url=http://127.0.0.1:6333`, `collection=scale_bge_m3`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 37 | 0,73 | 0,89 | 0,92 | 0,80 |
| questions | 13 | 0,85 | 1,00 | 1,00 | 0,90 |
| questions_ek | 12 | 0,83 | 0,83 | 0,83 | 0,83 |
| sekil_sorular | 12 | 0,50 | 0,83 | 0,92 | 0,65 |

## Süre (soru başına; setler: questions, questions_ek, sekil_sorular; 1 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 193 ms | 194 ms | 221 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 15 ms | 16 ms | 20 ms |
| total | 39 | 208 ms | 210 ms | 239 ms |

## ANN recall (dense, rastgele sorgu)

300 sorgu · recall@5: 1,00 · recall@20: 1,00

## Bellek

mode: server · rss_mb: 6898.1 · storage_mb: 49528.2 · points: 10000 · indexed_vectors: 10000 · segments: 6 · collection_disk_mb: 914.3

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'sız: RRF sırası)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 37 | 0,70 | 0,86 | 0,89 | 0,76 |
| questions | 13 | 0,77 | 0,92 | 1,00 | 0,83 |
| questions_ek | 12 | 0,75 | 0,83 | 0,83 | 0,78 |
| sekil_sorular | 12 | 0,58 | 0,83 | 0,83 | 0,66 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 190 ms | 190 ms | 220 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 19 ms | 19 ms | 22 ms |
| total | 39 | 208 ms | 208 ms | 236 ms |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, questions_ek:Q28, sekil_sorular:N3

İlk sırada değil: questions:Q03 (3.), questions:Q06 (3.), sekil_sorular:G1 (3.), sekil_sorular:G2 (2.), sekil_sorular:N1 (10.), sekil_sorular:G7 (3.), sekil_sorular:N2 (2.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
