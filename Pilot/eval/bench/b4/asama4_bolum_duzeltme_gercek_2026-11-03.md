# Bölüm adı düzeltmesi: gerçek 4.232 parça, önce/sonra (rerank'sız) — **geçici, onaysız set**

Aday listesi: RRF ilk 20, rerank'sız · aynı 128 cevaplı soru · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil, sayılar karar için kullanılmaz

Soru türü: aday setin türleri; bilinen setlerde şekil soruları ve 'görsel' etiketliler 'şekil', türü bu beşe girmeyenler (ör. EN soru, tuzak) 'diğer'.

## Filtreli

| Küme | n | Qwen3-8B + BM25, önce: hit@1 | hit@5 | Qwen3-8B + BM25, sonra: hit@1 | hit@5 | bge-m3 + BM25, önce: hit@1 | hit@5 | bge-m3 + BM25, sonra: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|
| Toplam | 128 | 0,70 | 0,84 | 0,70 | 0,84 | 0,62 | 0,80 | 0,63 | 0,80 |
| Tür: değer | 66 | 0,62 | 0,85 | 0,64 | 0,83 | 0,55 | 0,74 | 0,58 | 0,74 |
| Tür: prosedür | 13 | 0,38 | 0,54 | 0,38 | 0,54 | 0,54 | 0,77 | 0,62 | 0,77 |
| Tür: kod | 20 | 0,95 | 0,95 | 0,95 | 0,95 | 0,90 | 0,95 | 0,90 | 0,95 |
| Tür: arıza | 7 | 1,00 | 1,00 | 1,00 | 1,00 | 0,43 | 0,71 | 0,57 | 0,71 |
| Tür: şekil | 14 | 0,79 | 0,79 | 0,79 | 0,79 | 0,57 | 0,86 | 0,50 | 0,79 |
| Tür: diğer | 8 | 0,75 | 1,00 | 0,75 | 1,00 | 0,88 | 1,00 | 0,75 | 1,00 |
| Alt küme: etkilenen 34 | 23 | 0,61 | 0,78 | 0,61 | 0,74 | 0,70 | 0,83 | 0,74 | 0,83 |
| Alt küme: bölümü değişen 16 | 10 | 0,50 | 0,80 | 0,50 | 0,80 | 0,50 | 0,80 | 0,60 | 0,80 |

## Filtresiz

| Küme | n | Qwen3-8B + BM25, önce: hit@1 | hit@5 | Qwen3-8B + BM25, sonra: hit@1 | hit@5 | bge-m3 + BM25, önce: hit@1 | hit@5 | bge-m3 + BM25, sonra: hit@1 | hit@5 |
|---|---|---|---|---|---|---|---|---|---|
| Toplam | 128 | 0,70 | 0,83 | 0,70 | 0,82 | 0,62 | 0,78 | 0,64 | 0,77 |
| Tür: değer | 66 | 0,64 | 0,83 | 0,64 | 0,82 | 0,58 | 0,70 | 0,59 | 0,70 |
| Tür: prosedür | 13 | 0,38 | 0,54 | 0,38 | 0,54 | 0,54 | 0,77 | 0,62 | 0,77 |
| Tür: kod | 20 | 0,95 | 0,95 | 0,95 | 0,95 | 0,85 | 0,95 | 0,85 | 0,95 |
| Tür: arıza | 7 | 1,00 | 1,00 | 1,00 | 1,00 | 0,57 | 0,71 | 0,71 | 0,71 |
| Tür: şekil | 14 | 0,79 | 0,79 | 0,79 | 0,79 | 0,57 | 0,86 | 0,50 | 0,79 |
| Tür: diğer | 8 | 0,75 | 0,88 | 0,75 | 0,88 | 0,75 | 1,00 | 0,75 | 1,00 |
| Alt küme: etkilenen 34 | 23 | 0,61 | 0,78 | 0,61 | 0,74 | 0,70 | 0,74 | 0,74 | 0,74 |
| Alt küme: bölümü değişen 16 | 10 | 0,50 | 0,80 | 0,50 | 0,70 | 0,50 | 0,60 | 0,60 | 0,60 |

Koşular: Qwen3-8B + BM25: önce `bolum_once_qwen`, sonra `bolum_sonra_qwen`; bge-m3 + BM25: önce `bolum_once_bge`, sonra `bolum_sonra_bge`

