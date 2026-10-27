# "Hangi ürün/model?" koruması: yanlış pozitif ve negatif

Yalnız kaynak belirtmeyen sorular (koruma yalnız bunlarda çalışır). Yanlış pozitif: netleştirme beklenmiyordu ama soruldu ('alakasız': cevabı olmayan soruda soruldu; koruma tam bunu önlemek içindi, Q10). Yanlış negatif: netleştirme bekleniyordu ama sorulmadı. Açık kalan: eşik onaylı soru setiyle hibrit/RRF skoruna göre yeniden ayarlanacak.

## Onaylı setler (bilinen 36 + bulunamadı soruları)

| Yol | soru | doğru netleştirme | yanlış negatif | yanlış pozitif | yanlış pozitif (alakasız) | doğru geçiş |
|---|---|---|---|---|---|---|
| eski_rerank (rerank local, sparse bge-m3) | 4 | 2 | 0 | 0 | 0 | 2 |
| yeni_varsayilan (rerank none, sparse bm25) | 4 | 2 | 0 | 0 | 0 | 2 |

## Aday taslak (onaysız; yalnız bilgi amaçlı, karar için kullanılmaz)

| Yol | soru | doğru netleştirme | yanlış negatif | yanlış pozitif | yanlış pozitif (alakasız) | doğru geçiş |
|---|---|---|---|---|---|---|
| eski_rerank (rerank local, sparse bge-m3) | 36 | 11 | 4 | 1 | 0 | 20 |
| yeni_varsayilan (rerank none, sparse bm25) | 36 | 10 | 5 | 0 | 0 | 21 |

eski_rerank: aday:A079 yanlis_pozitif (ilk 3: strickland-1956, brother-s7300a, brother-s7300b; skor -4.93); aday:A132 yanlis_negatif (ilk 3: brother-s7300a, strickland-1956, strickland-1956; skor -7.61); aday:A141 yanlis_negatif (ilk 3: gl-pd-14-04a, granovsky-1986, strickland-1956; skor -9.44); aday:A142 yanlis_negatif (ilk 3: granovsky-1986, gl-pd-14-04a, gl-pd-14-04a; skor -8.68); aday:A145 yanlis_negatif (ilk 3: gl-pd-14-04a, gl-pd-14-04a, gl-pd-14-04a; skor -3.42)

yeni_varsayilan: aday:A132 yanlis_negatif (ilk 3: strickland-1956, bosch-ra1171, strickland-1956; skor None); aday:A135 yanlis_negatif (ilk 3: juki-mo6800s, brother-s7300a, brother-s7300a; skor None); aday:A141 yanlis_negatif (ilk 3: strickland-1956, bosch-ra1171, strickland-1956; skor None); aday:A144 yanlis_negatif (ilk 3: gl-pd-07-14a, bosch-ra1171, gl-pd-07-14a; skor None); aday:A145 yanlis_negatif (ilk 3: gl-pd-14-04a, brother-s7300b, gl-pd-14-04a; skor None)

