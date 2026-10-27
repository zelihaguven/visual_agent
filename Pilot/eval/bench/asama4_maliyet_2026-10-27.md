# Aşama 4: embedding maliyeti ve indeksleme hızı (ölçülen)

Kurulum kayıtlarından (data/bench_cache/build_*.json). Hız: geliştirme dizüstünden (bulut: ağ dahil, 64'lük toplu istek, tek iş parçacığı; local: CPU). 1M projeksiyonu doğrusal; paralel istekle bulut hızı artar.
Bulut rerank (qwen3-reranker-8b): 0.2 USD/Mtok; 20 aday ≈ 4400 token → 1.000 soru ≈ 0.88 USD.

| Model | boyut | token/parça | bu korpus USD | parça/sn | 1M parça USD | 1M parça süre (saat) | 1.000 soru embed USD |
|---|---|---|---|---|---|---|---|
| bge-m3-local-bm25 | 1024 | – | 0.0000 | – | 0.00 | – | 0.0000 |
| bge-m3-or | 1024 | 134 | 0.0057 | 28.0 | 1.34 | 9.9 | 0.0004 |
| gemini-001 | 3072 | 123 | 0.0779 | 13.5 | 18.41 | 20.6 | 0.0060 |
| me5-large | 1024 | 135 | 0.0057 | 16.7 | 1.35 | 16.6 | 0.0004 |
| nomic-v2-moe | 768 | – | 0.0000 | 2.7 | 0.00 | 101.6 | 0.0000 |
| qwen3-4b | 2560 | 131 | 0.0111 | 12.5 | 2.62 | 22.3 | 0.0008 |
| qwen3-8b | 4096 | 131 | 0.0061 | 19.1 | 1.45 | 14.5 | 0.0004 |
| te3-large | 3072 | 127 | 0.0699 | 26.3 | 16.52 | 10.5 | 0.0052 |

Local bge-m3 (bugünkü indeks): CPU'da ~1,5 parça/sn (Aşama 2.5 yeniden indeksleme) → 1M parça ≈ 185 saat.
