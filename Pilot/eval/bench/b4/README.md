# B4: lokal ve bulut embedding/rerank karşılaştırması

Commit'ler `fe1e2a0` (karşılaştırma), `f130ac4` (yeni varsayılan), `af84cc9` (reranker düzeltmesi). 9 embedding (6 bulut, 3 lokal) × 3 reranker, 36 bilinen soru. Bulut çağrıları dizüstünün bağlantısından; süreler üretimi temsil etmez.

| Dosya | Tarih | Sonuç |
|---|---|---|
| [asama4_embedding](asama4_embedding_2026-10-27.md) | 2026-10-27 | Rerank'sız: bge-m3 + BM25 hit@1 0,72, hit@5 0,89, toplam p50 227 ms; Qwen3-8B hit@1 0,78, p50 692 ms |
| [asama4_matris](asama4_matris_2026-10-27.md) | 2026-10-27 | Embedding × reranker: iyi aday listesinde lokal reranker katkısız ya da eksi; qwen3-reranker-8b hit@5 0,94, 0,4 sn |
| [asama4_maliyet](asama4_maliyet_2026-10-27.md) | 2026-10-27 | 1M parça embed maliyeti: Qwen3-8B ~1,45 $, te3-large ~16,5 $; lokal bge-m3 CPU'da ~185 saat |
| asama4_rerank_bge-m3-local-bm25_full ([md](asama4_rerank_bge-m3-local-bm25_full_2026-10-27.md)), …_bge-m3-local_full ([md](asama4_rerank_bge-m3-local_full_2026-10-27.md)), …_qwen3-8b_full ([md](asama4_rerank_qwen3-8b_full_2026-10-27.md)), …_te3-large_full ([md](asama4_rerank_te3-large_full_2026-10-27.md)) | 2026-10-27 | Matrisin ham satırları: her embedding'in aday listesinde reranker başına doğruluk ve süre |
| [asama4_yeni_varsayilan](asama4_yeni_varsayilan_2026-10-27.md) | 2026-10-27 | **Karar:** bge-m3 + BM25, rerank kapalı; uçtan uca hit@1 0,72, hit@5 0,89, MRR 0,79, toplam p50 0,45 sn |
| [rerank_teshis2](rerank_teshis2_2026-10-27.md) | 2026-10-27 | Reranker hit@1'i neden bozuyor: kesilme değil (%0); başlıksız metin yüzünden başka parçayı ya da dokümanı öne alıyor |
| [rerank_duzeltme_ozet](rerank_duzeltme_ozet_2026-10-27.md) | 2026-10-27 | Başlıklı metin + RRF birleşimi: filtreli hit@1 +0,03…+0,06, filtresiz +0,08…+0,11; varsayılan yine rerank kapalı |
| rerank_duzeltme_bge-m3-local-bm25_full ([md](rerank_duzeltme_bge-m3-local-bm25_full_2026-10-27.md)), rerank_duzeltme_qwen3-8b_full ([md](rerank_duzeltme_qwen3-8b_full_2026-10-27.md)) | 2026-10-27 | Düzeltme sonrası ham satırlar |
| [asama4_on_eleme_10k](asama4_on_eleme_10k_2026-11-03.md) | 2026-11-03 | Embedding karşılaştırması adım 1 (10k, rerank'sız, bulut çağrısı yok): 256 ön eleme doğru parçayı hiçbir soruda ilk 20'den düşürmüyor; bugünkü değerde (160 aday) ilk sıra ve ilk 5 tam vektörle 143/143 aynı, 640 adayda liste birebir aynı. hit değerleri geçici (onaysız set) |
| [bolum_kurallari](bolum_kurallari_2026-11-03.md) | 2026-11-03 | Bölüm adı düzeltmesi (`pilot/chunk.py`, 4 kural): 606 parçanın bölümü değişti, parça sınırları ve kimlikler aynı; kural bazında sayılar ve önce→sonra örnekleri |
| [asama4_bolum_duzeltme_gercek](asama4_bolum_duzeltme_gercek_2026-11-03.md) | 2026-11-03 | Gerçek 4.232 parçada düzeltme önce/sonra (rerank'sız): nötr; Qwen3-8B + BM25 toplamda aynı, bge-m3 + BM25 hit@1 +0,01/+0,02. Geçici, onaysız set |
| [asama4_rerank10k_ozet](asama4_rerank10k_ozet_2026-11-03.md) | 2026-11-03 | 10k, 3 yol, qwen3-reranker-8b (başlıklı metin + RRF): reranker üç yolda da kazandırıyor; filtreli hit@1/hit@5 Qwen3-8B 0,72/0,89, bge-m3 0,70/0,86; ön eleme açık/kapalı birebir aynı. Ham sonuçlar: asama4_rerank10k_a/b/c. Geçici, onaysız set; 0,99 USD |
| [asama4_uclu_fuzyon_10k](asama4_uclu_fuzyon_10k_2026-11-03.md) | 2026-11-03 | Üçlü füzyon (Qwen3-8B dense + bge-m3 dense + BM25), rerank'sız: filtreli hit@1/hit@5 0,75/0,89 (A 0,69/0,84, C 0,62/0,82). Geçici, onaysız set |
| [**asama4_rerank10k_analiz**](asama4_rerank10k_analiz_2026-11-03.md) | 2026-11-03 | Reranker gecikmesi (medyan 0,38–0,48 sn, p95 1,0–1,3 sn), üçlü füzyon, A'nın kaçırdığı 18 sorunun nedenleri (7 etiket, 5'i dil kopyası; 5 gerçek arama hatası), Qdrant durumu |
