# Arama ölçümü: asama4_yeni_varsayilan

2026-10-27T11:23:43 · commit `fe1e2a0+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Donanım: geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez · ağ: geliştirme makinesinin bağlantısı (ofis/ev)

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions', 'questions_ek', 'sekil_sorular']`, `timing_sets=['questions']`, `repeats=3`, `warmup=3`, `rerank=True`, `access=None`, `source_strip=True`, `qdrant_mode=embedded`, `qdrant_url=None`, `collection=manuals`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,72 | 0,89 | 0,94 | 0,79 |
| questions | 12 | 0,83 | 1,00 | 1,00 | 0,89 |
| questions_ek | 12 | 0,83 | 0,83 | 0,83 | 0,83 |
| sekil_sorular | 12 | 0,50 | 0,83 | 1,00 | 0,65 |

## Süre (soru başına; setler: questions; 3 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 42 | 213 ms | 210 ms | 257 ms |
| qdrant_open | 42 | 0 ms | 0 ms | 0 ms |
| qdrant | 42 | 238 ms | 240 ms | 273 ms |
| total | 42 | 451 ms | 452 ms | 528 ms |

## Bellek

mode: embedded · points: 4232 · rss_delta_mb: 236.6 · disk_mb: 53.6

## Filtresiz (doküman filtresi kaldırılmış, bütün koleksiyon, rerank'lı)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 36 | 0,67 | 0,86 | 0,94 | 0,75 |
| questions | 12 | 0,75 | 0,92 | 1,00 | 0,81 |
| questions_ek | 12 | 0,75 | 0,83 | 0,83 | 0,78 |
| sekil_sorular | 12 | 0,50 | 0,83 | 1,00 | 0,65 |

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 39 | 205 ms | 196 ms | 257 ms |
| qdrant_open | 39 | 0 ms | 0 ms | 0 ms |
| qdrant | 39 | 281 ms | 279 ms | 320 ms |
| total | 39 | 486 ms | 478 ms | 552 ms |

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): questions_ek:Q27, questions_ek:Q28

İlk sırada değil: questions:Q03 (3.), questions:Q06 (3.), sekil_sorular:G1 (3.), sekil_sorular:G2 (2.), sekil_sorular:N1 (10.), sekil_sorular:G7 (3.), sekil_sorular:N2 (2.), sekil_sorular:N3 (16.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka), questions_ek:Q30 (expect_clarify)
