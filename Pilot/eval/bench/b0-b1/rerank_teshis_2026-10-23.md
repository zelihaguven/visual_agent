# Reranker tek çağrı teşhisi: rerank_teshis

2026-10-23T12:04:50 · commit `377ad66+degisiklik` · sorular: questions:Q01, questions:Q04, sekil_sorular:G1 · 2 çağrı/soru (ısınma hariç)

Torch varsayılan iş parçacığı: 10 · FlagReranker örneği önbellekte: True · Flag batch_size: 128 · torch skorlarının flag'den en büyük farkı: 4.77e-06

| Çalıştırma | n | p50 | ort. | p95 | MHz ort. |
|---|---|---|---|---|---|
| flag (varsayılan) | 6 | 54.95 sn | 67.24 sn | 99.71 sn | 1855 |
| torch batch 20 | 6 | 27.64 sn | 32.25 sn | 47.72 sn | 1882 |
| torch batch 8 | 6 | 17.12 sn | 19.17 sn | 25.50 sn | 1834 |
| torch batch 4 | 6 | 15.30 sn | 15.84 sn | 18.51 sn | 1853 |
| torch batch 8, 2 iş parçacığı | 6 | 40.57 sn | 44.78 sn | 65.90 sn | 2422 |
| torch batch 8, 4 iş parçacığı | 6 | 32.01 sn | 36.82 sn | 51.53 sn | 2006 |
| torch batch 8, 6 iş parçacığı | 6 | 29.07 sn | 29.95 sn | 41.14 sn | 1944 |
| torch batch 8, 8 iş parçacığı | 6 | 26.03 sn | 33.74 sn | 63.73 sn | 1851 |
| torch batch 8, 12 iş parçacığı | 6 | 20.33 sn | 21.61 sn | 28.44 sn | 1868 |
