# İkili yol (bge-m3 + çevirili BM25, Qwen kolsuz) ile dondurulan aday, 10k, rerank'sız — **geçici, onaysız set**

Aday listesi: RRF ilk 20, rerank'sız · aynı 160 cevaplı soru · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil, sayılar karar için kullanılmaz

Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.

## Filtreli

| Küme | n | İkili: bge-m3 + çevirili BM25, : hit@1 | hit@5 | Aday: üçlü + çevirili BM25, : hit@1 | hit@5 |
|---|---|---|---|---|---|
| Toplam | 160 | 0,72 | 0,95 | 0,86 | 0,98 |
| Tür: değer | 90 | 0,68 | 0,94 | 0,83 | 0,97 |
| Tür: prosedür | 20 | 0,85 | 0,90 | 0,90 | 1,00 |
| Tür: kod | 20 | 0,95 | 1,00 | 1,00 | 1,00 |
| Tür: arıza | 8 | 0,75 | 0,88 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,50 | 1,00 | 0,79 | 1,00 |
| Tür: diğer | 8 | 0,62 | 1,00 | 0,88 | 1,00 |

## Filtresiz

| Küme | n | İkili: bge-m3 + çevirili BM25, : hit@1 | hit@5 | Aday: üçlü + çevirili BM25, : hit@1 | hit@5 |
|---|---|---|---|---|---|
| Toplam | 160 | 0,71 | 0,88 | 0,84 | 0,94 |
| Tür: değer | 90 | 0,66 | 0,84 | 0,79 | 0,90 |
| Tür: prosedür | 20 | 0,85 | 0,90 | 0,90 | 1,00 |
| Tür: kod | 20 | 0,95 | 1,00 | 1,00 | 1,00 |
| Tür: arıza | 8 | 0,50 | 0,75 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,57 | 0,86 | 0,79 | 0,93 |
| Tür: diğer | 8 | 0,88 | 1,00 | 0,88 | 1,00 |

Koşular: İkili: bge-m3 + çevirili BM25:  `cv_ikili_tr`; Aday: üçlü + çevirili BM25:  `cv_uclu_tr`

