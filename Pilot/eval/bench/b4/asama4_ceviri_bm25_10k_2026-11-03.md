# BM25'e çevrilmiş sorgu (google/gemma-3-12b-it), 10k, rerank'sız — **geçici, onaysız set**

Aday listesi: RRF ilk 20, rerank'sız · aynı 158 cevaplı soru · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil, sayılar karar için kullanılmaz

Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.

## Filtreli

| Küme | n | A Qwen3-8B + BM25, çevirisiz: hit@1 | hit@5 | A Qwen3-8B + BM25, çevirili: hit@1 | hit@5 | Üçlü füzyon, çevirisiz: hit@1 | hit@5 | Üçlü füzyon, çevirili: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|
| Toplam | 158 | 0,75 | 0,87 | 0,82 | 0,97 | 0,81 | 0,94 | 0,86 | 0,98 |
| Tür: değer | 90 | 0,68 | 0,82 | 0,78 | 0,98 | 0,77 | 0,91 | 0,83 | 0,97 |
| Tür: prosedür | 19 | 0,79 | 0,89 | 0,89 | 1,00 | 0,84 | 1,00 | 0,89 | 1,00 |
| Tür: kod | 19 | 0,95 | 1,00 | 0,95 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| Tür: arıza | 8 | 0,88 | 1,00 | 1,00 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,79 | 0,79 | 0,93 | 0,79 | 0,93 | 0,79 | 1,00 |
| Tür: diğer | 8 | 0,75 | 1,00 | 0,75 | 0,88 | 0,75 | 1,00 | 0,88 | 1,00 |

## Filtresiz

| Küme | n | A Qwen3-8B + BM25, çevirisiz: hit@1 | hit@5 | A Qwen3-8B + BM25, çevirili: hit@1 | hit@5 | Üçlü füzyon, çevirisiz: hit@1 | hit@5 | Üçlü füzyon, çevirili: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|
| Toplam | 158 | 0,75 | 0,86 | 0,80 | 0,94 | 0,79 | 0,93 | 0,84 | 0,94 |
| Tür: değer | 90 | 0,66 | 0,81 | 0,73 | 0,90 | 0,73 | 0,89 | 0,79 | 0,90 |
| Tür: prosedür | 19 | 0,84 | 0,89 | 0,84 | 1,00 | 0,84 | 1,00 | 0,89 | 1,00 |
| Tür: kod | 19 | 0,95 | 1,00 | 0,95 | 1,00 | 1,00 | 1,00 | 1,00 | 1,00 |
| Tür: arıza | 8 | 1,00 | 1,00 | 1,00 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 1,00 | 0,79 | 0,93 | 0,79 | 0,93 |
| Tür: diğer | 8 | 0,75 | 0,88 | 1,00 | 1,00 | 0,75 | 1,00 | 0,88 | 1,00 |

Koşular: A Qwen3-8B + BM25: çevirisiz `cv_a`, çevirili `cv_a_tr`; Üçlü füzyon: çevirisiz `cv_uclu`, çevirili `cv_uclu_tr`

