# B3: ölçek (1M parça) ve yük

B3 üçe bölündü (2026-10-27). **B3b** (kalabalıkta doğruluk) dizüstünde koşuldu. **B3a** (süre) ve **B3c** (eşzamanlı kullanıcı) şirket içi sunucuda koşulacak (paket: `bench/onprem/`). Sunucudan dönen `asama3_sure_*` ve `asama3_yuk_*` sonuçları da bu klasöre yazılır.

| Dosya | Tarih | Sonuç |
|---|---|---|
| [asama3_hazirlik](asama3_hazirlik_2026-10-27.md) | 2026-10-27 | Plan: 1M korpus kaynakları ve lisanslar, kademeler, kalabalık testi tasarımı, internetsiz sunucu paketi, 300 parçalık kuru çalıştırma |
| [**asama3b_sonuc**](asama3b_sonuc_2026-11-03.md) | 2026-11-03 | **B3b raporu:** hit@5 1M'e kadar sabit (Qwen3-8B filtreli 0,92, filtresiz 0,86); hit@1 100k'dan sonra 0,76 → 0,70 (2 soru); ilk 5'e giren dikkat dağıtıcıların çoğu Türkçe Vikipedi |
| [asama3b_scale_qwen3_8b_gercek](asama3b_scale_qwen3_8b_gercek_2026-11-03.md) | 2026-11-03 | Qwen3-8B, yalnız gerçek 4.232 parça: hit@1 0,76, hit@5 0,92 |
| [asama3b_scale_qwen3_8b_10000](asama3b_scale_qwen3_8b_10000_2026-11-03.md) | 2026-11-03 | Qwen3-8B 10k: filtreli değişiklik yok; filtresiz hit@5 0,89 → 0,86 |
| [asama3b_scale_qwen3_8b_30000](asama3b_scale_qwen3_8b_30000_2026-11-03.md) | 2026-11-03 | Qwen3-8B 30k: 10k ile aynı |
| [asama3b_scale_qwen3_8b_100000](asama3b_scale_qwen3_8b_100000_2026-11-03.md) | 2026-11-03 | Qwen3-8B 100k: filtreli hit@1 0,70 (G3, N3 ilk sıradan düştü), hit@5 0,92 |
| [asama3b_scale_qwen3_8b](asama3b_scale_qwen3_8b_2026-11-03.md) | 2026-11-03 | Qwen3-8B 1M: filtreli hit@1 0,70, hit@5 0,92; filtresiz 0,70 / 0,86; ANN recall@5 0,98 |
| [asama3b_scale_bge_m3_gercek](asama3b_scale_bge_m3_gercek_2026-11-03.md) | 2026-11-03 | bge-m3 + BM25, yalnız gerçek parçalar: hit@1 0,73, hit@5 0,89 |
| [asama3b_scale_bge_m3_10000](asama3b_scale_bge_m3_10000_2026-11-03.md) | 2026-11-03 | bge-m3 + BM25 10k: filtreli hit@1 ve hit@5 aynı (0,73 / 0,89); N3 ilk 20'nin dışına çıktı (hit@20 0,95 → 0,92) |
| [asama3b_scale_bge_m3](asama3b_scale_bge_m3_2026-11-03.md) | 2026-11-03 | bge-m3 + BM25 ana koleksiyon (10k'ya kadar kuruldu): 10k ile aynı sonuç |

Süreler dizüstünde alındı; üretimi temsil etmez, karar için kullanılmaz.

**Paket başlık düzeltmesi öncesi:** 2026-11-03'te parçaların bölüm adları düzeltildi (`pilot/chunk.py`, 606 parça; [b4/asama4_bolum_duzeltme_gercek](../b4/asama4_bolum_duzeltme_gercek_2026-11-03.md)). 1M koleksiyonu (`scale_qwen3_8b`), `synth_1m` ve sunucu paketi (commit `7ba656e`) düzeltme öncesi `embed_text` ile kalıyor; bu rapordaki B3b sayıları da öyle. Paket, sunucu testi tarihi belli olunca güncellenecek.
