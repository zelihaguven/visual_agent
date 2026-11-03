# Embedding karşılaştırması (rerank'sız, RRF sırası)

Süre: sorgu embed (bulutta ağ dahil) + Qdrant (sunucu modu), `questions` seti, ısınma hariç. Doğruluk: bilinen 36 soru.

| Model | dense | filtreli hit@1 | hit@5 | hit@20 | MRR | filtresiz hit@5 | MRR | embed p50 | p95 | Qdrant p50 | toplam p50 | p95 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bge-m3-local-bm25 | full | 0,72 | 0,89 | 0,94 | 0,79 | 0,86 | 0,75 | 215 ms | 303 ms | 13 ms | 227 ms | 317 ms |
| bge-m3-local | full | 0,44 | 0,86 | 0,89 | 0,61 | 0,86 | 0,63 | 336 ms | 398 ms | 23 ms | 358 ms | 424 ms |
| bge-m3-or | full | 0,72 | 0,89 | 0,94 | 0,79 | 0,86 | 0,75 | 547 ms | 1.21 sn | 31 ms | 574 ms | 1.24 sn |
| gemini-001 | full | 0,64 | 0,86 | 0,92 | 0,72 | 0,81 | 0,71 | 1.29 sn | 1.37 sn | 31 ms | 1.32 sn | 1.39 sn |
| me5-large | full | 0,58 | 0,83 | 0,94 | 0,69 | 0,75 | 0,58 | 918 ms | 1.49 sn | 25 ms | 935 ms | 1.53 sn |
| nomic-v2-moe | full | 0,58 | 0,81 | 0,94 | 0,67 | 0,78 | 0,64 | 199 ms | 249 ms | 22 ms | 222 ms | 268 ms |
| nomic-v2-moe | short 256 | 0,58 | 0,69 | 0,83 | 0,64 | 0,69 | 0,59 | 189 ms | 229 ms | 21 ms | 209 ms | 253 ms |
| nomic-v2-moe | short_rescore 256 | 0,58 | 0,81 | 0,92 | 0,67 | 0,78 | 0,64 | 191 ms | 220 ms | 25 ms | 218 ms | 245 ms |
| qwen3-4b | full | 0,67 | 0,86 | 1,00 | 0,76 | 0,83 | 0,73 | 1.21 sn | 2.23 sn | 29 ms | 1.24 sn | 2.25 sn |
| qwen3-8b | full | 0,78 | 0,89 | 0,97 | 0,83 | 0,86 | 0,83 | 664 ms | 1.57 sn | 33 ms | 692 ms | 1.60 sn |
| qwen3-8b | short 256 | 0,64 | 0,89 | 0,94 | 0,74 | 0,86 | 0,70 | 607 ms | 1.97 sn | 22 ms | 628 ms | 2.01 sn |
| qwen3-8b | short 512 | 0,67 | 0,86 | 0,97 | 0,76 | 0,86 | 0,77 | 624 ms | 1.44 sn | 30 ms | 651 ms | 1.47 sn |
| qwen3-8b | short_rescore 256 | 0,78 | 0,89 | 0,97 | 0,83 | 0,86 | 0,83 | 624 ms | 1.08 sn | 35 ms | 656 ms | 1.14 sn |
| qwen3-8b | short_rescore 512 | 0,78 | 0,89 | 0,97 | 0,83 | 0,86 | 0,83 | 664 ms | 1.16 sn | 39 ms | 696 ms | 1.22 sn |
| te3-large | full | 0,78 | 0,92 | 0,97 | 0,83 | 0,78 | 0,75 | 691 ms | 1.12 sn | 28 ms | 722 ms | 1.16 sn |
| te3-large | short 256 | 0,67 | 0,92 | 0,97 | 0,76 | 0,69 | 0,61 | 621 ms | 1.01 sn | 33 ms | 659 ms | 1.04 sn |
| te3-large | short 512 | 0,72 | 0,92 | 0,97 | 0,79 | 0,72 | 0,65 | 528 ms | 884 ms | 30 ms | 547 ms | 919 ms |
| te3-large | short_rescore 256 | 0,78 | 0,92 | 0,97 | 0,83 | 0,78 | 0,75 | 581 ms | 1.10 sn | 36 ms | 625 ms | 1.13 sn |
| te3-large | short_rescore 512 | 0,78 | 0,92 | 0,97 | 0,83 | 0,78 | 0,75 | 581 ms | 960 ms | 34 ms | 614 ms | 993 ms |
