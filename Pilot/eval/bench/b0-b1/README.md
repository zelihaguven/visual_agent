# B0–B1: ölçüm düzeneği, temel çizgi ve reranker hızı

B0 (commit `377ad66`): ölçüm düzeneği ve temel çizgi. B1 (commit `675b7af`): reranker teşhisi, model karşılaştırması, FUSED_K × max_length. Doğruluk 36 bilinen soruda; 5–8 puanın altındaki farklar gürültü. Süreler geliştirme dizüstünde, üretimi temsil etmez.

| Dosya | Tarih | Sonuç |
|---|---|---|
| [baseline](baseline_2026-10-23.md) | 2026-10-23 | B0 temel çizgi: gömülü Qdrant + bge-m3 + reranker, hit@5 0,86, arama p50 56,7 sn; sürenin %95'i rerank |
| [rerank_teshis](rerank_teshis_2026-10-23.md) | 2026-10-23 | FlagEmbedding her çağrıda ilk batch'i fazladan hesaplıyor; torch backend aynı skorla çok daha hızlı |
| [rerank_modeller](rerank_modeller_2026-10-23.md) | 2026-10-23 | 7 reranker aynı aday listesinde: bge-reranker-v2-m3 onnx-int8 en iyi hit@1 (0,78), p50 6,7 sn |
| [rerank_filtresiz](rerank_filtresiz_2026-10-23.md) | 2026-10-23 | Doküman filtresi olmadan da onnx-int8 önde (hit@1 0,67); rerank'sız RRF 0,50 |
| [rerank_jina_fp32](rerank_jina_fp32_2026-10-23.md) | 2026-10-23 | jina-v2 hit@5'te önde (0,92), hit@1'de bge-v2-m3 int8'in gerisinde (0,69 / 0,78) |
| [rerank_izgara](rerank_izgara_2026-10-23.md) | 2026-10-23 | FUSED_K × max_length ızgarası: 15 × 256 aynı hit@5 ile daha hızlı (rerank p50 4,9 sn) |
| [kayip](kayip_2026-10-23.md) | 2026-10-23 | İlk 20 adaya girmeyen 3 soru, kol kol (dense/sparse, filtreli/filtresiz) izlendi |
| [qdrant_istemci_kapali](qdrant_istemci_kapali_2026-10-23.md) | 2026-10-23 | Her aramada yeni Qdrant istemcisi: açılış ~1 sn, toplam p50 1,55 sn (rerank'sız) |
| [qdrant_istemci_tek](qdrant_istemci_tek_2026-10-23.md) | 2026-10-23 | Tek istemci örneği: açılış 0, toplam p50 0,41 sn (rerank'sız), doğruluk aynı |
| [asama1_onerilen](asama1_onerilen_2026-10-23.md) | 2026-10-23 | B1 önerilen ayarlar (onnx-int8, 256, FUSED_K 15, tek istemci): arama p50 56,7 → 3,6 sn, hit@5 aynı (0,86) |
| openrouter_modeller_2026-10-23.json | 2026-10-23 | OpenRouter'daki embedding/rerank modellerinin listesi (yalnız JSON) |
