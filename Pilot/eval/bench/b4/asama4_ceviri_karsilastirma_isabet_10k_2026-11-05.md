# BM25 sorgu çevirisi: Gemma 3 DeepInfra / Gemma 3 NextBit / Gemma 4 NextBit, 10k, rerank'sız — **geçici, onaysız set**

Aday listesi: RRF ilk 20, rerank'sız · aynı 160 cevaplı soru · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil, sayılar karar için kullanılmaz

Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.

## Filtreli

| Küme | n | Yalnız BM25, g3 DeepInfra: hit@1 | hit@5 | Yalnız BM25, g3 NextBit: hit@1 | hit@5 | Yalnız BM25, g4 NextBit: hit@1 | hit@5 | Üçlü füzyon, g3 DeepInfra: hit@1 | hit@5 | Üçlü füzyon, g3 NextBit: hit@1 | hit@5 | Üçlü füzyon, g4 NextBit: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Toplam | 160 | 0,60 | 0,82 | 0,60 | 0,82 | 0,63 | 0,85 | 0,87 | 0,97 | 0,86 | 0,98 | 0,84 | 0,98 |
| Tür: değer | 90 | 0,56 | 0,84 | 0,61 | 0,84 | 0,66 | 0,88 | 0,84 | 0,97 | 0,82 | 0,97 | 0,82 | 0,97 |
| Tür: prosedür | 20 | 0,50 | 0,80 | 0,40 | 0,70 | 0,55 | 0,85 | 0,90 | 1,00 | 0,90 | 1,00 | 0,90 | 1,00 |
| Tür: kod | 20 | 0,90 | 0,90 | 0,90 | 0,90 | 0,85 | 0,90 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| Tür: arıza | 8 | 0,50 | 0,75 | 0,25 | 0,75 | 0,25 | 0,62 | 0,88 | 1,00 | 0,88 | 1,00 | 0,75 | 1,00 |
| Tür: şekil | 14 | 0,64 | 0,64 | 0,57 | 0,71 | 0,57 | 0,64 | 0,79 | 0,86 | 0,79 | 1,00 | 0,71 | 1,00 |
| Tür: diğer | 8 | 0,62 | 0,88 | 0,62 | 0,88 | 0,50 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,75 | 1,00 |

## Filtresiz

| Küme | n | Yalnız BM25, g3 DeepInfra: hit@1 | hit@5 | Yalnız BM25, g3 NextBit: hit@1 | hit@5 | Yalnız BM25, g4 NextBit: hit@1 | hit@5 | Üçlü füzyon, g3 DeepInfra: hit@1 | hit@5 | Üçlü füzyon, g3 NextBit: hit@1 | hit@5 | Üçlü füzyon, g4 NextBit: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Toplam | 160 | 0,57 | 0,78 | 0,53 | 0,77 | 0,57 | 0,80 | 0,83 | 0,94 | 0,84 | 0,93 | 0,84 | 0,96 |
| Tür: değer | 90 | 0,51 | 0,73 | 0,51 | 0,74 | 0,54 | 0,79 | 0,78 | 0,90 | 0,78 | 0,89 | 0,79 | 0,92 |
| Tür: prosedür | 20 | 0,55 | 0,80 | 0,35 | 0,70 | 0,60 | 0,85 | 0,95 | 1,00 | 0,90 | 1,00 | 0,95 | 1,00 |
| Tür: kod | 20 | 0,90 | 0,90 | 0,90 | 0,90 | 0,85 | 0,90 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| Tür: arıza | 8 | 0,50 | 0,75 | 0,12 | 0,62 | 0,25 | 0,62 | 0,88 | 1,00 | 0,88 | 1,00 | 0,75 | 1,00 |
| Tür: şekil | 14 | 0,57 | 0,79 | 0,50 | 0,79 | 0,50 | 0,79 | 0,79 | 0,93 | 0,86 | 0,93 | 0,86 | 1,00 |
| Tür: diğer | 8 | 0,50 | 0,88 | 0,62 | 1,00 | 0,50 | 0,75 | 0,75 | 1,00 | 0,88 | 1,00 | 0,75 | 1,00 |

Koşular: Yalnız BM25: g3 DeepInfra `cc_bm25_g3di`, g3 NextBit `cc_bm25_g3nb`, g4 NextBit `cc_bm25_g4nb`; Üçlü füzyon: g3 DeepInfra `cc_uclu_g3di`, g3 NextBit `cc_uclu_g3nb`, g4 NextBit `cc_uclu_g4nb`

