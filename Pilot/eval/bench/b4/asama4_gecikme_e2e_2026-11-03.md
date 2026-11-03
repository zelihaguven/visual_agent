# Uçtan uca gecikme: üçlü füzyon + çevirili BM25, reranker'sız (20 soru, 10k, filtreli)

Geliştirme dizüstü (i5-1335U, GPU yok), bulut çağrıları bu makinenin bağlantısından: **üretimi temsil etmez**. Isınma hariç; Qwen sorgu embed'i önbelleksiz (gerçek çağrı). Cevap modeli henüz seçilmedi (PRD A1): `mistralai/mistral-small-24b-instruct-2501` yalnız gösterge.

| Adım | Paralel grubu | p50 | p95 |
|---|---|---|---|
| Qwen3-8B sorgu embed'i (bulut) | 1 | 1,62 sn | 23,89 sn |
| bge-m3 sorgu embed'i (CPU) | 1 | 171 ms | 235 ms |
| Çeviri (google/gemma-3-12b-it) | 1 | 745 ms | 1,07 sn |
| **Grup 1 duvar saati** (üçü paralel) | – | 1,62 sn | 23,89 sn |
| Qdrant: Qwen dense kolu | 2 | 26 ms | 42 ms |
| Qdrant: bge-m3 dense kolu | 2 | 17 ms | 33 ms |
| Qdrant: BM25 kolu (çevrilmiş) | 2 | 16 ms | 33 ms |
| **Grup 2 duvar saati** (üçü paralel) | – | 31 ms | 48 ms |
| Füzyon (RRF) | – | 0 ms | 0 ms |
| Cevap ilk token (mistralai/mistral-small-24b-instruct-2501) | – | 374 ms | 19,82 sn |
| Cevap toplam (akış bitişi) | – | 5,40 sn | 26,97 sn |
| **Uçtan uca, ilk token** | – | 1,99 sn | 28,03 sn |
| **Uçtan uca, cevap bitişi** | – | 17,67 sn | 35,63 sn |

Çeviri çağrısı yapılan soru: 19/20. Harcama: çeviri 0.0002 USD, Qwen embed 0.00001 USD, cevap 0.0030 USD.

