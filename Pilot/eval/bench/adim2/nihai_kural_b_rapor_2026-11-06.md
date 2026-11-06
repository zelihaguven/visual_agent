# Bağlanacak hattın uçtan uca ölçümü: `nihai_kural_b`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 48 | 0 | 14/14 (100%) | **0** | 10 / 0 / 2 | 7/7 (100%) | 12/15 (80%) | 10/13 (77%) | 1 (belge içi varyant doğru 0/0) | 448 ms / 867 ms | 3,05 sn / 5,78 sn | 0.0125 USD |

## İlk görünen kelime (gri akış C; gizlenen değerler hariç ilk tam kelime)

| Varyant | cevaplı | model tarafı p50 / p95 | uçtan uca p50 / p95 |
|---|---|---|---|
| 8 kaynak | 15 | 2,18 sn / 4,88 sn | 2,93 sn / 5,54 sn |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 13 | 2,96 sn / 5,74 sn | **3,75 sn / 6,53 sn** | 1/13 (8%) | 1,21 sn / 1,73 sn | 751 ms / 897 ms |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 62 | 762 ms / 941 ms | 485 ms / 698 ms | 0/62 (0%) | 0 | 209 ms | 286 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | None / None |
| sekil_sorular:G7 | None / None |

Çeviri maliyeti: 0.0007 USD · cevap: 8 kaynak 0.0125 USD


## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)

Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.

İşaretlenen cevap yok.

