> **GEÇERSİZ KOŞU (saklanıyor, karar için kullanılmaz).** Ölçüm aracı akış satırlarını Latin-1 çözdü; "±" ve Türkçe harfler bozuldu, alıntı doğrulaması (✓/⚠/✖), sayı ve beklenen değer metrikleri yanlış. Modelin "bulunamadı"/cevap kararları etkilenmedi. Geçerli rapor: [adim2_cevap_modeli_2026-11-05.md](adim2_cevap_modeli_2026-11-05.md). Ham: `ham/bozuk1_*.json`.

# Adım 2: cevap modeli seçimi, ilk tur (ön eleme)

> **"Bulunamadı" kararının 17 sorusu onaysız** (A114–A130, aday taslak; 21 sorunun 17'si; kural çıkışları hariç modelin karar verdiği 17 sorunun 15'i). **Bu koşu ön elemedir; nihai seçim onaylı ve büyütülmüş sette yapılacak.** Cevaplı sorularda da 123/160 onaysız. Süreler geliştirme makinesinin bağlantısından; üretimi temsil etmez.

Arama sabit: uygulamanın varsayılan yolu (bge-m3 + BM25, rerank kapalı, ilke dışı kurallar kapalı), `manuals` koleksiyonu; bütün modeller aynı kaynakları gördü. Aynı sistem talimatı ve şema, temperature 0, düşünme kapalı; modele özel istem ayarı yok. Yeniden deneme bütün modellerde aynı: ilk token gelmeden 429/5xx/bağlantı hatasında 30 sn sonra bir kez; yine olmazsa soru cevapsız (kalite metriklerine girmez). Plan: [plan_cevap_modeli_2026-11-05.md](plan_cevap_modeli_2026-11-05.md).

**Kural çıkışları (modelden bağımsız, bir kez):** {'yabanci_marka': 2, 'kod_yok': 2}; "bulunamadı" beklenen 21 sorudan 4 kuralla çıkıyor.

## Dayanıklılık

| Model | Sağlayıcı (sabit) | ZDR sağlayıcı sayısı | çağrı | 429 | diğer hata | yeniden deneme | cevapsız kalan | başka sağlayıcıdan gelen | düşünme kontrolü |
|---|---|---|---|---|---|---|---|---|---|
| gemma4 (`google/gemma-4-26b-a4b-it`) | deepinfra | 13 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |
| qwen36 (`qwen/qwen3.6-35b-a3b`) | deepinfra | 9 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |
| gpt54mini (`openai/gpt-5.4-mini`) | azure | 1 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |
| mistral2603 (`mistralai/mistral-small-2603`) | mistral | 1 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |

## "Bulunamadı" (21 soru: 4 onaylı + 17 onaysız)

| Model | doğru "bulunamadı", toplam | … modelin karar verdiği soruda | netleştirme | cevap üretti | … doğrulanmış görünen yanlış (✓/⚠) | JSON hatası | cevapsız (kaliteden ayrı) |
|---|---|---|---|---|---|---|---|
| gemma4 | 21/21 (100%) | 17/17 (100%) | 0 | 0 | **0** | 0 | 0 |
| qwen36 | 16/21 (76%) | 12/17 (71%) | 0 | 5 | **2** | 0 | 0 |
| gpt54mini | 16/21 (76%) | 12/17 (71%) | 0 | 5 | **4** | 0 | 0 |
| mistral2603 | 21/21 (100%) | 17/17 (100%) | 0 | 0 | **0** | 0 | 0 |

Taban (2026-10-27, yerel qwen2.5:7b, aynı 21 soru, o günkü arama): doğru "bulunamadı" %48, doğrulanmış görünen yanlış 3.

## Cevaplı sorular (kalite, cevap gelen sorularda)

| Model | Set | soru | yanlış ret | … kaynak ilk 5'teydi (model hatası) | … arama getirmedi | netleştirme | ✓ / ⚠ / ✖ | beklenen değer cevapta | atıf: en az biri doğru sayfa | atıf: hepsi doğru | JSON hatası |
|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | onaylı | 37 | 4/37 (11%) | 1 | 3 | 0 | 20 / 1 / 12 | 17/18 (94%) | 29/33 (88%) | 29/33 (88%) | 0 |
| gemma4 | onaysız | 123 | 12/123 (10%) | 3 | 9 | 0 | 64 / 5 / 42 | 59/83 (71%) | 99/110 (90%) | 88/110 (80%) | 0 |
| qwen36 | onaylı | 37 | 0/37 (0%) | 0 | 0 | 0 | 16 / 5 / 16 | 17/21 (81%) | 33/37 (89%) | 27/37 (73%) | 0 |
| qwen36 | onaysız | 123 | 8/123 (7%) | 2 | 6 | 0 | 74 / 6 / 35 | 56/85 (66%) | 99/115 (86%) | 87/115 (76%) | 0 |
| gpt54mini | onaylı | 37 | 2/37 (5%) | 1 | 1 | 0 | 17 / 3 / 15 | 18/20 (90%) | 32/35 (91%) | 25/35 (71%) | 0 |
| gpt54mini | onaysız | 123 | 9/123 (7%) | 2 | 7 | 0 | 78 / 12 / 24 | 59/84 (70%) | 101/114 (89%) | 82/114 (72%) | 0 |
| mistral2603 | onaylı | 37 | 1/37 (3%) | 0 | 1 | 0 | 8 / 8 / 17 | 18/20 (90%) | 29/33 (88%) | 26/33 (79%) | 3 |
| mistral2603 | onaysız | 123 | 9/123 (7%) | 3 | 6 | 0 | 31 / 34 / 46 | 52/84 (62%) | 97/111 (87%) | 75/111 (68%) | 3 |

Atıf doğruluğu: cevabın alıntı yaptığı kaynak numaralarının parçaları beklenen doküman ve sayfayla (`is_match`) eşleşiyor mu; alıntısız cevap paydada yok.

## JSON (ayrı metrik, modele giden bütün çağrılar)

| Model | çağrı | ok | şema dışı | boş | yarıda kesik | ayrıştırılamadı | düşünce bloğu / öntext atıldı |
|---|---|---|---|---|---|---|---|
| gemma4 | 177 | 177 | 0 | 0 | 0 | 0 | 0 |
| qwen36 | 177 | 177 | 0 | 0 | 0 | 0 | 0 |
| gpt54mini | 177 | 177 | 0 | 0 | 0 | 0 | 0 |
| mistral2603 | 177 | 171 | 0 | 0 | 6 | 0 | 0 |

## İlk token ve süre (§9.3 eşikleri: 1,2 sn hedge, 1,5 sn yedek sağlayıcı, 20 sn toplam)

| Model | Tur | n | ilk token p50 | p95 | ≤ 1,2 sn | ≤ 1,5 sn | toplam p50 | p95 | > 20 sn | sağlayıcı |
|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | ana (10:30) | 177 | 419 ms | 967 ms | 170/177 (96%) | 171/177 (97%) | 2,96 sn | 5,99 sn | 0 | {'DeepInfra': 177} |
| qwen36 | ana (10:40) | 177 | 600 ms | 2,12 sn | 158/177 (89%) | 160/177 (90%) | 6,08 sn | 17,00 sn | 4 | {'DeepInfra': 177} |
| gpt54mini | ana (11:08) | 177 | 757 ms | 1,87 sn | 160/177 (90%) | 164/177 (93%) | 1,81 sn | 3,39 sn | 1 | {'Azure': 177} |
| mistral2603 | ana (11:01) | 177 | 431 ms | 823 ms | 171/177 (97%) | 176/177 (99%) | 2,00 sn | 4,73 sn | 0 | {'Mistral': 177} |

qwen2.5:7b yerelde (dizüstü CPU): süreleri bulutla karşılaştırılamaz.

## Maliyet

| Model | Tur | USD | soru başına |
|---|---|---|---|
| gemma4 | ana | 0.0414 | 0.00023 |
| qwen36 | ana | 0.0842 | 0.00047 |
| gpt54mini | ana | 0.3474 | 0.00192 |
| mistral2603 | ana | 0.0597 | 0.00033 |

Toplam: 0.5327 USD (sınır 1,5 USD).
