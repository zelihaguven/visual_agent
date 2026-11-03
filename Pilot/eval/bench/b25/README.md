# B2.5: veri kalitesi düzeltmeleri, belirli sıralı RRF

Commit `5f35276`. Parçalama ve üst/alt bilgi düzeltmeleri (4196 → 4232 parça), istemcide belirli sıralı RRF, zorunlu ZDR.

| Dosya | Tarih | Sonuç |
|---|---|---|
| [asama25_once](asama25_once_2026-10-23.md) | 2026-10-23 | Düzeltmeden önce: hit@1 0,75, hit@5 0,86 |
| [asama25_sonra](asama25_sonra_2026-10-23.md) | 2026-10-23 | Düzeltmeden sonra: hit@1 0,72, hit@5 0,89 (±1 soru, gürültü sınırında) |
| [kayip_2](kayip_2026-10-23_2.md) | 2026-10-23 | Kayıp analizi yeniden: ilk 20'ye girmeyen 3 soru |
| [mod_farki_2](mod_farki_2026-10-23_2.md) | 2026-10-23 | Pipeline araması (belirli sıralı RRF) gömülü ve sunucu modunda 39/39 aynı sıra; Qdrant'ın kendi RRF'i 4/39 |
