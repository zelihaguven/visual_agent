# Bağlanacak hattın uçtan uca ölçümü: `nihai_hatjsn`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 242 | 0 | 54/54 (100%) | **0** | 126 / 1 / 19 | 99/105 (94%) | 12/15 (80%) | 8/13 (62%) | 3 (belge içi varyant doğru 1/2) | 406 ms / 905 ms | 2,01 sn / 3,72 sn | 0.0614 USD |

## İlk görünen kelime (gri akış C; gizlenen değerler hariç ilk tam kelime)

| Varyant | cevaplı | model tarafı p50 / p95 | uçtan uca p50 / p95 |
|---|---|---|---|
| 8 kaynak | 148 | 1,52 sn / 2,71 sn | 2,24 sn / 3,47 sn |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 135 | 1,98 sn / 3,71 sn | **2,75 sn / 4,40 sn** | 89/135 (66%) | 1,11 sn / 1,75 sn | 653 ms / 968 ms |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 245 | 648 ms / 965 ms | 507 ms / 778 ms | 1/245 (0%) | 0 | 169 ms | 131 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | cevap / verified |
| sekil_sorular:G7 | netlestirme / clarify |

Çeviri maliyeti: 0.0034 USD · cevap: 8 kaynak 0.0614 USD


## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)

Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.

İşaretlenen cevap yok.

