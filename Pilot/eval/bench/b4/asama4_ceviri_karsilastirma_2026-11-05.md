# BM25 sorgu çevirisi: model ve sağlayıcı etkisi (yalnız ölçüm aracı)

Üç kol her soruda iç içe, sırası dönerek; tek sağlayıcıya sabit, yeniden denemesiz. Süre: çağrının tamamı (istek → cevabın sonu). Başarı ölçütü p95 ve 1,2 sn sınırını aşma oranı; p50 de veriliyor. `filtreli` çağrı uygulamanın yolu (hedef diller kapsamdan); `filtresiz` bütün korpus dilleri. Kalite (BM25 isabeti) aynı çevirilerle ayrı raporda. Plan: [Adım 2 planı §14](../adim2/plan_cevap_modeli_2026-11-05.md).

## Süre ve çıktı tokeni (filtreli: uygulamanın yolu)

| Tur | Kol | çağrı | süre p50 | p95 | > 1,2 sn | çıktı tokeni p50 | p95 | düşünce tokeni | hata | sağlayıcı | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|
| t1 (14:25) | g3_deepinfra | 175 | 2,14 sn | 4,06 sn | 168/175 (96%) | 25 | 55 | 0 | 0 | {'DeepInfra': 175} | 0.0020 |
| t1 (14:25) | g3_nextbit | 175 | 838 ms | 2,05 sn | 62/175 (35%) | 24 | 37 | 0 | 0 | {'NextBit': 175} | 0.0017 |
| t1 (14:25) | g4_nextbit | 175 | 530 ms | 1,04 sn | 3/175 (2%) | 23 | 59 | 0 | 0 | {'NextBit': 175} | 0.0028 |

Sınırı aşan: süre > 1,2 sn ya da hata (uygulamada ikisi de çevirisiz BM25 demek).

## Bütün çağrılar (filtreli + filtresiz)

| Tur | Kol | çağrı | süre p50 | p95 | > 1,2 sn | hata |
|---|---|---|---|---|---|---|
| t1 | g3_deepinfra | 350 | 2,07 sn | 3,33 sn | 96% | 0 |
| t1 | g3_nextbit | 350 | 794 ms | 2,05 sn | 28% | 0 |
| t1 | g4_nextbit | 350 | 527 ms | 985 ms | 1% | 0 |

## Çeviri farkı (tur t1, filtreli, g3_deepinfra'ya göre)

| Kol | soru | birebir aynı BM25 sorgusu |
|---|---|---|
| g3_deepinfra | 179 | 179 |
| g3_nextbit | 179 | 44 |
| g4_nextbit | 179 | 16 |

Farklı çeviriler (ilk 12, g3_deepinfra → g4_nextbit):

- `questions:Q01`: How many stitches per inch should there be on the outer seams of the jacket? → How many stitches per inch should there be in the visible external seams of the jacket?
- `questions:Q02`: What should the SPI be for the outer seams of the trousers? → What should the SPI be for the outer seams of the pants?
- `questions:Q03`: What is the required stitch count in the buttonholes? → What should be the number of stitches in the jacket buttonholes?
- `questions:Q04`: What should I do if the upper thread tension is incorrect on the S-7300A? → The upper thread is not tense on the S-7300A, what should I do?
- `questions:Q05`: On the S-7300B, the sewing machine is producing skipped stitches. What should I do? → The S-7300B is skipping stitches, what should I do?
- `questions:Q06`: How to clean the coffee machine? ¿Cómo limpiar la máquina de café? → How to clean the coffee machine? Cómo limpiar la cafetera?
- `questions:Q09`: What fabric should be used for the pocket lining of the trousers and what should its grammage be? → What fabric should be used for the pant pocket lining and what should its weight be?
- `questions:Q10`: At what temperature should aircraft engine oil be changed? → At what temperature should the aircraft engine oil be changed?
- `questions:Q11`: What is the number of stitches per inch required for overedge stitching on the jacket? → How many stitches per inch should there be in the overlock (overedge) seams of the jacket?
- `questions:Q12`: What should the SPI (stitches per inch) be for the overlock seams on the trousers? → What should the SPI be for the overlock (overedge) stitches of the trousers?
- `questions:Q13`: What is the minimum number of consecutive stitches required in the eyelet stitching on the chuck? → What is the minimum number of overlapping stitches required for the eyelet stitching on the jacket?
- `questions:Q14`: What does error code E050 mean on the S-7300A, and what corrective actions should be taken? → What does error code E050 mean on the S-7300A, and what should I do?
