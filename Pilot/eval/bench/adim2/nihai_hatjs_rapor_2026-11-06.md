# Bağlanacak hattın uçtan uca ölçümü: `nihai_hatjs`

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 242 | 0 | 53/54 (98%) | **1** | 131 / 2 / 18 | 100/108 (93%) | 12/15 (80%) | 8/13 (62%) | 2 (belge içi varyant doğru 1/2) | 386 ms / 852 ms | 2,19 sn / 4,33 sn | 0.0607 USD |

## İlk görünen kelime (gri akış C; gizlenen değerler hariç ilk tam kelime)

| Varyant | cevaplı | model tarafı p50 / p95 | uçtan uca p50 / p95 |
|---|---|---|---|
| 8 kaynak | 157 | 1,58 sn / 3,65 sn | 2,28 sn / 4,52 sn |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 141 | 2,17 sn / 4,31 sn | **2,84 sn / 5,08 sn** | 82/141 (58%) | 1,11 sn / 1,66 sn | 692 ms / 962 ms |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 245 | 685 ms / 937 ms | 491 ms / 734 ms | 0/245 (0%) | 0 | 192 ms | 166 ms |

## İzlenen sorular (c150b-J'de yeni gereksiz netleştirme)

| Soru | 5 kaynak | 8 kaynak |
|---|---|---|
| questions:Q05 | cevap / verified |
| sekil_sorular:G7 | netlestirme / clarify |

Çeviri maliyeti: 0.0034 USD · cevap: 8 kaynak 0.0607 USD


## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)

Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.

| Koşu | Soru | Eksik niteleyici | Durum | Soru metni |
|---|---|---|---|---|
| nihai_hatjs_k8_gemma4.json | aday_sorular_ek:B012 | dijital | verified | S-7300A'da dijital baskı ayağı kaldırıcısının kaldırma yüksekliği nasıl ayarlanı |

