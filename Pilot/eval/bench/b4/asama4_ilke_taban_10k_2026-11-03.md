# Dürüst taban: ilke temizliği sonrası, 10k, rerank'sız — **geçici, onaysız set**

Aday listesi: RRF ilk 20, rerank'sız · aynı 159 cevaplı soru · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil, sayılar karar için kullanılmaz

Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.

## Filtreli

| Küme | n | A Qwen3-8B + BM25, önce: hit@1 | hit@5 | A Qwen3-8B + BM25, sonra: hit@1 | hit@5 | Üçlü füzyon, önce: hit@1 | hit@5 | Üçlü füzyon, sonra: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|
| Toplam | 159 | 0,74 | 0,87 | 0,74 | 0,87 | 0,80 | 0,94 | 0,80 | 0,94 |
| Tür: değer | 90 | 0,68 | 0,82 | 0,68 | 0,82 | 0,74 | 0,91 | 0,76 | 0,91 |
| Tür: prosedür | 19 | 0,79 | 0,89 | 0,79 | 0,89 | 0,84 | 1,00 | 0,84 | 1,00 |
| Tür: kod | 20 | 0,90 | 0,95 | 0,90 | 0,95 | 0,95 | 0,95 | 0,95 | 0,95 |
| Tür: arıza | 8 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 0,86 | 0,86 | 0,93 | 0,79 | 0,93 |
| Tür: diğer | 8 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 | 0,75 | 1,00 |

## Filtresiz

| Küme | n | A Qwen3-8B + BM25, önce: hit@1 | hit@5 | A Qwen3-8B + BM25, sonra: hit@1 | hit@5 | Üçlü füzyon, önce: hit@1 | hit@5 | Üçlü füzyon, sonra: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|
| Toplam | 159 | 0,74 | 0,86 | 0,74 | 0,86 | 0,79 | 0,92 | 0,79 | 0,92 |
| Tür: değer | 90 | 0,66 | 0,81 | 0,66 | 0,81 | 0,73 | 0,89 | 0,73 | 0,89 |
| Tür: prosedür | 19 | 0,84 | 0,89 | 0,84 | 0,89 | 0,84 | 1,00 | 0,84 | 1,00 |
| Tür: kod | 20 | 0,90 | 0,95 | 0,90 | 0,95 | 0,95 | 0,95 | 0,95 | 0,95 |
| Tür: arıza | 8 | 1,00 | 1,00 | 1,00 | 1,00 | 0,88 | 1,00 | 0,88 | 1,00 |
| Tür: şekil | 14 | 0,79 | 0,86 | 0,79 | 0,86 | 0,86 | 0,93 | 0,79 | 0,93 |
| Tür: diğer | 8 | 0,75 | 0,88 | 0,75 | 0,88 | 0,75 | 1,00 | 0,75 | 1,00 |

Koşular: A Qwen3-8B + BM25: önce `rr10k_a`, sonra `rr10k_a_ilke`; Üçlü füzyon: önce `rr10k_uclu`, sonra `rr10k_uclu_ilke`

