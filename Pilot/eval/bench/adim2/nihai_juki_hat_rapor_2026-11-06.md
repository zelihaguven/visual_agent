# JUKI (görülmemiş belge), tek seferlik doğrulama: seçilen hat ve yalnız arama

Hat: ikili yol (Gemma 4 NextBit çevirisi, 1,2 sn sınırı + bge-m3 + BM25, uygulamanın `manuals` koleksiyonu, gömülü Qdrant, rerank yok) → Gemma 4 c150b-J (max_tokens 1200, DeepInfra'ya sabit) → doğrulama (verify_c). Plan §26 / §28. İki varyant (5 / 8 kaynak) aynı arama adaylarıyla, her soruda rastgele sırayla.

**Karşılaştırma notu:** Bu sayılar uygulamanın pilot korpusunda (`manuals`). 10k koleksiyonundaki arama ölçümleriyle (b4 raporları) doğrudan karşılaştırılamaz: korpus ve aday havuzu farklı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 8 kaynak | 13 | 0 | 1/1 (100%) | **0** | 8 / 0 / 2 | 8/8 (100%) | – | – | 1 (belge içi varyant doğru 0/0) | 479 ms / 1,00 sn | 1,71 sn / 3,22 sn | 0.0034 USD |

## Süre (gerçek akış; uçtan uca arama dahil)

| Varyant | cevaplı | ilk doğrulanmış cümle (model) p50 / p95 | **uçtan uca ilk doğrulanmış cümle** p50 / p95 | ≤ 3 sn (PRD) | uçtan uca ilk token p50 / p95 | istek öncesi (arama dahil) p50 / p95 |
|---|---|---|---|---|---|---|
| 8 kaynak | 9 | 1,71 sn / 3,22 sn | **2,32 sn / 3,90 sn** | 5/9 (56%) | 1,09 sn / 1,53 sn | 611 ms / 701 ms |

## Arama adımı (soru başına bir kez)

| arama | arama p50 / p95 | çeviri p50 / p95 | çeviri 1,2 sn sınırını aşan | çeviri boş/hata | embed p50 | Qdrant p50 |
|---|---|---|---|---|---|---|
| 14 | 583 ms / 696 ms | 433 ms / 555 ms | 0/14 (0%) | 0 | 169 ms | 130 ms |

## Okuma uyarısı

- Set küçük: 14 soru, 12 cevaplı + 2 "bulunamadı". Cevaplı sorularda 1 soru ≈ 8 puan.
- JUKI ayrı tutulan görülmemiş belge testi. **Bu sonuca göre hiçbir ayar değiştirilmeyecek** (karar 2026-11-06).
- Koşu tek seferlik ve ayar değiştirmeden yapıldı:
  - (a) seçilen hat: ikili yol (`manuals`, gömülü) + c150b-J + 8 kaynak, DeepInfra, uçtan uca;
  - (b) yalnız arama: 10k koleksiyonunda varsayılan (bge-m3 + çevirisiz BM25), ikili yol (bge-m3 + çevirili BM25) ve üçlü füzyon (Qwen3-8B + bge-m3 + çevirili BM25); filtreli, rerank'sız.
- (a) ve (b) farklı korpuslarda: (a) pilot korpus, (b) 10k. Arama sıraları doğrudan karşılaştırılamaz.

## Soru soru

| Soru | Soru metni | Beklenen | (a) çıkış | (a) rozet / değer | (a) u2u ilk doğr. cümle | arama sırası: varsayılan / ikili / üçlü (10k, filtreli) |
|---|---|---|---|---|---|---|
| J1 | JUKI MO-6800S'in maksimum dikiş hızı nedir? | s.[3] | cevap | ✓ · değer ✓ | 3,57 sn | 1 / 2 / 1 |
| J2 | MO-6800S'te dikiş boyu aralığı nedir? | s.[3] | cevap | ✓ · değer ✓ | 4,11 sn | 1 / 1 / 1 |
| J3 | MO-6800S'te overlok genişliği kaç mm? | s.[3] | netlestirme | netleştirme | – | 1 / 1 / 1 |
| J4 | MO-6800S hangi iğne tipini kullanır? | s.[3] | cevap | ✖ · değer ✓ | – | 4 / >20 / 2 |
| J5 | MO-6800S'te yağ ne sıklıkla değiştirilmeli? | s.[13] | cevap | ✓ · değer ✓ | 3,46 sn | 1 / 2 / 2 |
| J6 | MO-6800S'te iplik gerginliği nasıl artırılır? | s.[19] | cevap | ✓ | 2,04 sn | 1 / 1 / 1 |
| J7 | MO-6800S'te E02 hatası ne demek? | s.[46] | cevap | ✓ · değer ✓ | 3,19 sn | 1 / 1 / 1 |
| J8 | JUKI makinesinde E07 hatası çıktı, ne yapmalıyım? | s.[46] | cevap | ✓ · değer ✓ | 2,32 sn | 1 / 1 / 1 |
| J9 | MO-6800S'te E050 hatası ne demek? | bulunamadı | kural:kod_yok | bulunamadı | – | – / – / – |
| J10 | Overlok makinesinde dikiş boyu nasıl ayarlanır? | s.[21] | cevap | ✖ | 2,13 sn | 7 / 3 / 1 |
| J11 | MO-6800S'in garanti süresi kaç yıl? | bulunamadı | bulunamadi | bulunamadı | – | – / – / – |
| J12 | MO-6800S'in ana parçaları nelerdir? | s.[4] | bulunamadi | bulunamadı | – | >20 / >20 / 18 |
| J13 | How much does the JUKI MO-6800S weigh? | s.[3, 5] | cevap | ✓ · değer ✓ | 1,60 sn | 1 / 1 / 1 |
| J14 | JUKI'de E01 hatası hangi voltajda çıkar? | s.[46] | cevap | ✓ · değer ✓ | 2,21 sn | 1 / 1 / 1 |

| Yol (10k, filtreli) | hit@1 | hit@5 |
|---|---|---|
| varsayilan | 9/12 (75%) | 10/12 (83%) |
| ikili | 7/12 (58%) | 10/12 (83%) |
| uclu | 9/12 (75%) | 11/12 (92%) |

- (a) uçtan uca: 12 cevaplı sorunun 8'i ✓ (değer 8/8 doğru), 2'si ✖, 1'i netleştirme, 1'i "bulunamadı". 2 "bulunamadı" sorusunun ikisi de doğru (J9 kural, J11 model). Doğrulanmış görünen yanlış 0.
- **J3** (overlok genişliği): netleştirme. Değer modele göre değişiyor (MO-6804 / 6814S / 6816S; 2026-10-16'daki sütun varyantı vakası). Clarify kapısının "belge içi varyant" tanımına göre doğru davranış. Rapor tablosu bunu "gereksiz netleştirme 1" sayıyor, çünkü JUKI'nin netleştirme sınıfı tanımlı değil (JUKI'ye dokunulmadı).
- **J4** ✖: "DC X 27" değeri doğru, ama alıntı [6] kaynakta birebir değil. Pilot korpusta s.3 ilk 8'de yok.
- **J10** ✖: sesli metinde alıntıda olmayan "1". Güvenli yönde.
- **J12** "bulunamadı": yanlış ret. Ana parçalar listesi (s.4) üç yolda da ilk 5'te yok (10k'da en iyisi üçlü füzyonda 18. sıra). Arama sorunu.
- Süre: uçtan uca ilk doğrulanmış cümle p50 2,32 sn, p95 3,90 sn; 9 sorunun 5'i ≤ 3 sn. İlk iki sorunun 3,6–4,1 sn'si ısınma sonrası ilk çağrılar.
- (b) 10k, filtreli: hit@5 varsayılan 10/12, ikili 10/12, üçlü 11/12. hit@1'de ikili yol 7/12 ile en düşük (J1, J5 2. sırada; J4 ilk 20'de yok). 12 soruda 1 soru 8 puan.
