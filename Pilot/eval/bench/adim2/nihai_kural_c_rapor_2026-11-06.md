# Bağlanacak hattın uçtan uca ölçümü: `nihai_kural_c`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 59 | 0 | 15/15 (100%) | **0** | 10 / 0 / 2 | 7/7 (100%) | 13/15 (87%) | 8/13 (62%) | 1 (belge içi varyant doğru 0/0) | 414 ms / 1,15 sn | 2,19 sn / 3,48 sn | 0.0154 USD |

## İlk görünen kelime (gri akış C; gizlenen değerler hariç ilk tam kelime)

| Varyant | cevaplı | model tarafı p50 / p95 | uçtan uca p50 / p95 |
|---|---|---|---|
| 8 kaynak | 16 | 1,58 sn / 2,74 sn | 2,36 sn / 3,46 sn |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 14 | 2,19 sn / 3,46 sn | **2,93 sn / 4,13 sn** | 9/14 (64%) | 1,22 sn / 1,96 sn | 743 ms / 987 ms |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 62 | 737 ms / 971 ms | 485 ms / 667 ms | 1/62 (2%) | 0 | 197 ms | 268 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | None / None |
| sekil_sorular:G7 | None / None |

Çeviri maliyeti: 0.0007 USD · cevap: 8 kaynak 0.0154 USD


## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)

Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.

İşaretlenen cevap yok.

