# Bağlanacak hattın uçtan uca ölçümü: `nihai_hatjm`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 229 | 0 | 50/51 (98%) | **1** | 121 / 0 / 27 | 99/106 (93%) | 13/15 (87%) | 10/13 (77%) | 1 (belge içi varyant doğru 1/2) | 387 ms / 1,32 sn | 1,80 sn / 3,48 sn | 0.0618 USD |

## İlk görünen kelime (gri akış C; gizlenen değerler hariç ilk tam kelime)

| Varyant | cevaplı | model tarafı p50 / p95 | uçtan uca p50 / p95 |
|---|---|---|---|
| 8 kaynak | 151 | 674 ms / 1,73 sn | 1,39 sn / 2,62 sn |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 134 | 1,78 sn / 3,56 sn | **2,47 sn / 4,33 sn** | 98/134 (73%) | 1,12 sn / 2,11 sn | 670 ms / 1,27 sn |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 245 | 665 ms / 1,27 sn | 505 ms / 899 ms | 12/245 (5%) | 0 | 172 ms | 130 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | cevap / failed |
| sekil_sorular:G7 | cevap / verified |

Çeviri maliyeti: 0.0037 USD · cevap: 8 kaynak 0.0618 USD


## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)

Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.

| Koşu | Soru | Eksik niteleyici | Durum | Soru metni |
|---|---|---|---|---|
| nihai_hatjm_k8_gemma4.json | aday_sorular_ek:B012 | dijital | verified | S-7300A'da dijital baskı ayağı kaldırıcısının kaldırma yüksekliği nasıl ayarlanı |

