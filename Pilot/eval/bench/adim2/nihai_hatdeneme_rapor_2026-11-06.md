# Bağlanacak hattın uçtan uca ölçümü: `nihai_hatdeneme`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 kaynak | 3 | 0 | – | **0** | 3 / 0 / 0 | 2/3 (67%) | – | – | 0 (belge içi varyant doğru 0/1) | 327 ms / 460 ms | 1,18 sn / 1,36 sn | 0.0009 USD |
| 8 kaynak | 3 | 0 | – | **0** | 3 / 0 / 0 | 2/3 (67%) | – | – | 0 (belge içi varyant doğru 0/1) | 373 ms / 572 ms | 1,31 sn / 1,54 sn | 0.0009 USD |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 5 kaynak | 3 | 1,18 sn / 1,36 sn | **1,87 sn / 2,05 sn** | 3/3 (100%) | 1,08 sn / 1,16 sn | 696 ms / 744 ms |
| 8 kaynak | 3 | 1,31 sn / 1,54 sn | **2,18 sn / 2,25 sn** | 3/3 (100%) | 1,25 sn / 1,29 sn | 695 ms / 859 ms |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 3 | 693 ms / 744 ms | 558 ms / 611 ms | 0/3 (0%) | 0 | 198 ms | 132 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | None / None | None / None |
| sekil_sorular:G7 | None / None | None / None |

Çeviri maliyeti: 0.0001 USD · cevap: 5 kaynak 0.0009 USD · 8 kaynak 0.0009 USD

