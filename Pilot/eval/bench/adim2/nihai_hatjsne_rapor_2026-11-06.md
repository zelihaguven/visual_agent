# Bağlanacak hattın uçtan uca ölçümü: `nihai_hatjsne`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 242 | 0 | 54/54 (100%) | **0** | 121 / 1 / 24 | 96/106 (91%) | 13/15 (87%) | 8/13 (62%) | 2 (belge içi varyant doğru 2/2) | 393 ms / 997 ms | 1,41 sn / 2,59 sn | 0.0636 USD |

## İlk görünen kelime (gri akış C; gizlenen değerler hariç ilk tam kelime)

| Varyant | cevaplı | model tarafı p50 / p95 | uçtan uca p50 / p95 |
|---|---|---|---|
| 8 kaynak | 150 | 1,12 sn / 1,93 sn | 1,82 sn / 2,65 sn |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 131 | 1,41 sn / 2,57 sn | **2,15 sn / 3,27 sn** | 122/131 (93%) | 1,10 sn / 1,78 sn | 681 ms / 1,04 sn |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 245 | 677 ms / 1,04 sn | 499 ms / 822 ms | 4/245 (2%) | 0 | 181 ms | 133 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | cevap / verified |
| sekil_sorular:G7 | netlestirme / clarify |

Çeviri maliyeti: 0.0034 USD · cevap: 8 kaynak 0.0636 USD


## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)

Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.

İşaretlenen cevap yok.

