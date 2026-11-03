# Üçlü füzyon (Qwen3-8B dense + bge-m3 dense + BM25), 10k, rerank'sız — **geçici, onaysız set**

Aday listesi: RRF ilk 20, rerank'sız · aynı 160 cevaplı soru · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil, sayılar karar için kullanılmaz

Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.

## Filtreli

| Küme | n | Rerank'sız, A Qwen3-8B + BM25: hit@1 | hit@5 | Rerank'sız, C bge-m3 + BM25: hit@1 | hit@5 | Rerank'sız, Üçlü füzyon: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|
| Toplam | 160 | 0,69 | 0,84 | 0,62 | 0,82 | 0,75 | 0,89 |
| Tür: değer | 90 | 0,63 | 0,81 | 0,57 | 0,78 | 0,70 | 0,88 |
| Tür: prosedür | 20 | 0,55 | 0,70 | 0,65 | 0,85 | 0,65 | 0,80 |
| Tür: kod | 20 | 0,90 | 0,95 | 0,90 | 0,95 | 0,95 | 0,95 |
| Tür: arıza | 8 | 0,88 | 1,00 | 0,50 | 0,75 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,50 | 0,79 | 0,86 | 0,93 |
| Tür: diğer | 8 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 |

## Filtresiz

| Küme | n | Rerank'sız, A Qwen3-8B + BM25: hit@1 | hit@5 | Rerank'sız, C bge-m3 + BM25: hit@1 | hit@5 | Rerank'sız, Üçlü füzyon: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|
| Toplam | 160 | 0,68 | 0,82 | 0,62 | 0,78 | 0,73 | 0,88 |
| Tür: değer | 90 | 0,60 | 0,80 | 0,54 | 0,72 | 0,68 | 0,84 |
| Tür: prosedür | 20 | 0,60 | 0,70 | 0,70 | 0,85 | 0,60 | 0,80 |
| Tür: kod | 20 | 0,90 | 0,95 | 0,90 | 0,95 | 0,95 | 0,95 |
| Tür: arıza | 8 | 1,00 | 1,00 | 0,62 | 0,62 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,57 | 0,79 | 0,86 | 0,93 |
| Tür: diğer | 8 | 0,75 | 0,88 | 0,75 | 1,00 | 0,75 | 1,00 |

Koşular: Rerank'sız: A Qwen3-8B + BM25 `rr10k_a`, C bge-m3 + BM25 `rr10k_c`, Üçlü füzyon `rr10k_uclu`

