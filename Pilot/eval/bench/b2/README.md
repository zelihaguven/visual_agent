# B2: Qdrant sunucu modu, koleksiyon şeması, yetki alanı

Commit `9140f79`. Sunucu modu, HNSW/quantization ayarları, `access` payload indeksi ve yetki filtresi. Doğruluk 36 bilinen soruda; süreler geliştirme dizüstünde, üretimi temsil etmez.

| Dosya | Tarih | Sonuç |
|---|---|---|
| [asama2_gomulu](asama2_gomulu_2026-10-23.md) | 2026-10-23 | Karşılaştırma tabanı, gömülü mod: Qdrant p50 306 ms, toplam 500 ms (rerank'sız) |
| [asama2_sunucu_http](asama2_sunucu_http_2026-10-23.md) | 2026-10-23 | Sunucu modu HTTP: Qdrant p50 13 ms |
| [asama2_sunucu_grpc](asama2_sunucu_grpc_2026-10-23.md) | 2026-10-23 | Sunucu modu gRPC: Qdrant p50 11 ms, toplam 231 ms |
| [asama2_sunucu_rerank](asama2_sunucu_rerank_2026-10-23.md) | 2026-10-23 | Sunucu modu + reranker: hit@1 0,75, toplam p50 14,4 sn (rerank baskın) |
| [asama2_access_hepsi_all](asama2_access_hepsi_all_2026-10-23.md) | 2026-10-23 | Bütün dokümanlar herkese açık (`all`), g1 kullanıcısının filtresiyle: filtre süreyi değiştirmiyor (Qdrant p50 14 ms) |
| [asama2_access_yapay_g1](asama2_access_yapay_g1_2026-10-23.md) | 2026-10-23 | Yapay departman dağılımında g1 kullanıcısı: yetkisiz dokümanlar aramaya hiç girmiyor, bu yüzden hit@5 0,75 |
| [asama2_access_yapay_filtresiz](asama2_access_yapay_filtresiz_2026-10-23.md) | 2026-10-23 | Aynı yapay dağılımlı koleksiyon, yetki filtresi olmadan: hit@5 0,86, Qdrant p50 13 ms |
| [mod_farki](mod_farki_2026-10-23.md) | 2026-10-23 | Gömülü ve sunucu modu: dense/sparse aynı, RRF sırası 39 sorunun 38'inde farklı (eşit skorlu sıralama) |
