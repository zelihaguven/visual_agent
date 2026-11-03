# Arama ölçümü: qdrant_istemci_tek

2026-10-23T13:22:16 · commit `377ad66+degisiklik` · Intel64 Family 6 Model 186 Stepping 3, GenuineIntel (12 iş parçacığı), 31.6 GB RAM · Windows-11-10.0.26200-SP0

Parametreler: `PREFETCH_K=30`, `FUSED_K=20`, `TOP_K_SOURCES=5`, `EMBED_MODEL=BAAI/bge-m3`, `RERANK_MODEL=BAAI/bge-reranker-v2-m3`, `EMBED_MAX_LENGTH=512`, `EMBED_DEVICE=cpu`, `sets=['questions']`, `timing_sets=['questions']`, `repeats=3`, `warmup=3`, `rerank=False`, `qdrant_mode=embedded`, `qdrant_reuse=True`

## Doğruluk (netleştirme ve bulunamadı soruları hariç)

| Set | n | hit@1 | hit@5 | hit@20 | MRR |
|-----|---|-------|-------|--------|-----|
| all | 12 | 0,58 | 1,00 | 1,00 | 0,75 |
| questions | 12 | 0,58 | 1,00 | 1,00 | 0,75 |

## Süre (soru başına; setler: questions; 3 tur, ısınma hariç)

| Aşama | n | ort. | p50 | p95 |
|-------|---|------|-----|-----|
| embed | 42 | 167 ms | 170 ms | 191 ms |
| qdrant_open | 42 | 0 ms | 0 ms | 0 ms |
| qdrant | 42 | 237 ms | 241 ms | 276 ms |
| total | 42 | 404 ms | 413 ms | 448 ms |

## Bellek

Mod: embedded · parça: 4196 · RAM artışı: 218.0 MB · disk: 51.2 MB

## Soru ayrıntısı

Bulunamayan (ilk 20'de yok): –

İlk sırada değil: questions:Q03 (3.), questions:Q05 (2.), questions:Q06 (3.), questions:Q12 (3.), questions:Q15 (2.)

Bulunamadı beklenen, en iyi rerank skoru: –

Aranmayan (pipeline'da netleştirme): questions:Q07 (expect_clarify), questions:Q08 (yabanci_marka), questions:Q17 (netlestirme), questions:Q18 (yabanci_marka)
