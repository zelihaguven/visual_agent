# Adım 2: cevap modeli seçimi, ilk tur (ön eleme)

> **"Bulunamadı" kararının 0 sorusu onaysız** (A114–A130; 21 sorunun 0'si; kural çıkışları hariç modelin karar verdiği 17 sorunun 0'i). **Bu koşu ön elemedir; nihai seçim onaylı ve büyütülmüş sette yapılacak.** Cevaplı sorularda da 1/160 onaysız. Süreler geliştirme makinesinin bağlantısından; üretimi temsil etmez.

Arama sabit: uygulamanın varsayılan yolu (bge-m3 + BM25, rerank kapalı, ilke dışı kurallar kapalı), `manuals` koleksiyonu; bütün modeller aynı kaynakları gördü. Aynı sistem talimatı ve şema, temperature 0, düşünme kapalı; modele özel istem ayarı yok. Yeniden deneme bütün modellerde aynı: ilk token gelmeden 429/5xx/bağlantı hatasında 30 sn sonra bir kez; yine olmazsa soru cevapsız (kalite metriklerine girmez). Plan: [plan_cevap_modeli_2026-11-05.md](plan_cevap_modeli_2026-11-05.md).

**Rozetler `verify.py` A+B (2026-11-05): çoklu atıf, liste numarası, değer biçimi, alıntıda yazıyla sayı ile.** Rozet davranışı değişti: çoklu atıf (`[1, 2]`) atıf sayılıyor ve içindeki rakamlar değer sayılmıyor; atıftan sonra, `<br>` sonrası ve Markdown kalın madde numaraları liste numarası; `2.00` = `2`, `.5` = `0.5`; alıntıda yazıyla geçen 1–12 (`six months`) alıntı sayısı. Birim dönüşümü, türetilmiş sayı ve alıntıda olmayan değer yine ✖. Gerekçe ve önce/sonra: [okuma_sayi_uzunluk_2026-11-05.md](okuma_sayi_uzunluk_2026-11-05.md). Önceki sürümle koşulan kayıtlar model çağrısı olmadan yeniden puanlandı (`--rescore`): gemma4 rozeti değişen 0, kesik kayıt 5, gpt54mini rozeti değişen 0, kesik kayıt 6, mistral2603 rozeti değişen 0, kesik kayıt 8, qwen36 rozeti değişen 0, kesik kayıt 3. Kesik kayıt: ham çıktı 1500 karakterde kesik kaydedilmiş, rozeti yaklaşık (sayı ve atıf kontrolleri kayıttaki cevabın ilk 600 karakterinden); tablolarda ayrı sütunda.

**Kural çıkışları (modelden bağımsız, bir kez):** {'yabanci_marka': 2, 'kod_yok': 2}; "bulunamadı" beklenen 21 sorudan 4 kuralla çıkıyor.

## Dayanıklılık

| Model | Sağlayıcı (sabit) | ZDR sağlayıcı sayısı | çağrı | 429 | diğer hata | yeniden deneme | cevapsız kalan | başka sağlayıcıdan gelen | düşünme kontrolü |
|---|---|---|---|---|---|---|---|---|---|
| gemma4 (`google/gemma-4-26b-a4b-it`) | deepinfra | 13 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |
| qwen36 (`qwen/qwen3.6-35b-a3b`) | deepinfra | 9 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |
| gpt54mini (`openai/gpt-5.4-mini`) | azure | 1 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |
| mistral2603 (`mistralai/mistral-small-2603`) | mistral | 1 | 177 | 0 | 0 | 0 | 0 | 0 | tamam |

## "Bulunamadı" (21 soru: 4 onaylı + 17 onaysız)

| Model | doğru "bulunamadı", toplam | … modelin karar verdiği soruda | netleştirme | cevap üretti | … doğrulanmış görünen yanlış (✓/⚠) | … kesik kayıt (yaklaşık) | JSON hatası | cevapsız (kaliteden ayrı) |
|---|---|---|---|---|---|---|---|---|
| gemma4 | 21/21 (100%) | 17/17 (100%) | 0 | 0 | **0** | 0 | 0 | 0 |
| qwen36 | 14/21 (67%) | 10/17 (59%) | 0 | 7 | **4** | 0 | 0 | 0 |
| gpt54mini | 16/21 (76%) | 12/17 (71%) | 0 | 5 | **5** | 1 | 0 | 0 |
| mistral2603 | 21/21 (100%) | 17/17 (100%) | 0 | 0 | **0** | 0 | 0 | 0 |

Taban (2026-10-27, yerel qwen2.5:7b, aynı 21 soru, o günkü arama): doğru "bulunamadı" %48, doğrulanmış görünen yanlış 3.

## Cevaplı sorular (kalite, cevap gelen sorularda)

| Model | Set | soru | yanlış ret | … kaynak ilk 5'teydi (model hatası) | … arama getirmedi | netleştirme | ✓ / ⚠ / ✖ | … kesik kayıt (yaklaşık) | beklenen değer cevapta | atıf: en az biri doğru sayfa | atıf: hepsi doğru | JSON hatası |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | onaylı | 159 | 18/159 (11%) | 4 | 14 | 0 | 117 / 11 / 13 | 5 | 91/99 (92%) | 127/141 (90%) | 115/141 (82%) | 0 |
| gemma4 | … onaylı, OCR soruları | 14 | 4/14 (29%) | 2 | 2 | 0 | 6 / 0 / 4 | 0 | 7/9 (78%) | 9/10 (90%) | 8/10 (80%) | 0 |
| gemma4 | onaysız | 1 | 0/1 (0%) | 0 | 0 | 0 | 1 / 0 / 0 | 0 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0 |
| qwen36 | onaylı | 159 | 8/159 (5%) | 2 | 6 | 0 | 119 / 12 / 20 | 3 | 89/105 (85%) | 130/151 (86%) | 111/151 (74%) | 0 |
| qwen36 | … onaylı, OCR soruları | 14 | 2/14 (14%) | 1 | 1 | 0 | 6 / 0 / 6 | 0 | 7/10 (70%) | 9/12 (75%) | 8/12 (67%) | 0 |
| qwen36 | onaysız | 1 | 0/1 (0%) | 0 | 0 | 0 | 1 / 0 / 0 | 0 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0 |
| gpt54mini | onaylı | 159 | 9/159 (6%) | 3 | 6 | 0 | 128 / 14 / 8 | 5 | 88/105 (84%) | 129/150 (86%) | 105/150 (70%) | 0 |
| gpt54mini | … onaylı, OCR soruları | 14 | 2/14 (14%) | 1 | 1 | 0 | 12 / 0 / 0 | 0 | 5/10 (50%) | 8/12 (67%) | 7/12 (58%) | 0 |
| gpt54mini | onaysız | 1 | 0/1 (0%) | 0 | 0 | 0 | 1 / 0 / 0 | 0 | 1/1 (100%) | 1/1 (100%) | 1/1 (100%) | 0 |
| mistral2603 | onaylı | 159 | 12/159 (8%) | 4 | 8 | 0 | 57 / 49 / 36 | 8 | 84/101 (83%) | 125/142 (88%) | 101/142 (71%) | 5 |
| mistral2603 | … onaylı, OCR soruları | 14 | 2/14 (14%) | 1 | 1 | 0 | 3 / 3 / 6 | 0 | 7/10 (70%) | 10/12 (83%) | 8/12 (67%) | 0 |
| mistral2603 | onaysız | 1 | 0/1 (0%) | 0 | 0 | 0 | 1 / 0 / 0 | 0 | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) | 0 |

Atıf doğruluğu: cevabın alıntı yaptığı kaynak numaralarının parçaları beklenen doküman ve sayfayla (`is_match`) eşleşiyor mu; alıntısız cevap paydada yok.

**Rozet nedenleri** (cevaplı sorularda üretilen cevaplar; `verify.py` kontrolleri, bir cevapta birden çok olabilir):

| Model | ✖: alıntıda olmayan sayı | ✖: alıntı birebir değil | ✖ / ⚠: geçerli [n] atfı yok | ⚠: değer varyanta göre değişiyor | ⚠: alıntı şekil açıklamasından |
|---|---|---|---|---|---|
| gemma4 | 10 | 5 | 3 | 6 | 3 |
| qwen36 | 13 | 9 | 0 | 9 | 4 |
| gpt54mini | 4 | 4 | 0 | 10 | 4 |
| mistral2603 | 14 | 23 | 45 | 8 | 7 |

## JSON (ayrı metrik, modele giden bütün çağrılar)

| Model | çağrı | ok | şema dışı | boş | yarıda kesik | ayrıştırılamadı | düşünce bloğu / öntext atıldı |
|---|---|---|---|---|---|---|---|
| gemma4 | 177 | 177 | 0 | 0 | 0 | 0 | 0 |
| qwen36 | 177 | 177 | 0 | 0 | 0 | 0 | 0 |
| gpt54mini | 177 | 177 | 0 | 0 | 0 | 0 | 0 |
| mistral2603 | 177 | 172 | 0 | 0 | 5 | 0 | 0 |

## İlk token ve süre (§9.3 eşikleri: 1,2 sn hedge, 1,5 sn yedek sağlayıcı, 20 sn toplam)

| Model | Tur | n | ilk token p50 | p95 | ≤ 1,2 sn | ≤ 1,5 sn | toplam p50 | p95 | > 20 sn | sağlayıcı |
|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | ana (11:16) | 177 | 388 ms | 1,04 sn | 169/177 (95%) | 170/177 (96%) | 2,97 sn | 10,26 sn | 1 | {'DeepInfra': 177} |
| gemma4 | ikinci (14:41) | 30 | 350 ms | 1,90 sn | 27/30 (90%) | 27/30 (90%) | 2,85 sn | 5,51 sn | 0 | {'DeepInfra': 30} |
| qwen36 | ana (11:28) | 177 | 648 ms | 1,57 sn | 164/177 (93%) | 166/177 (94%) | 7,41 sn | 17,14 sn | 6 | {'DeepInfra': 177} |
| qwen36 | ikinci (14:43) | 30 | 715 ms | 10,70 sn | 23/30 (77%) | 23/30 (77%) | 10,49 sn | 24,52 sn | 5 | {'DeepInfra': 30} |
| gpt54mini | ana (11:59) | 177 | 762 ms | 1,36 sn | 163/177 (92%) | 171/177 (97%) | 1,72 sn | 3,17 sn | 0 | {'Azure': 177} |
| gpt54mini | ikinci (14:50) | 30 | 776 ms | 1,06 sn | 29/30 (97%) | 30/30 (100%) | 1,80 sn | 2,72 sn | 0 | {'Azure': 30} |
| mistral2603 | ana (11:52) | 177 | 449 ms | 991 ms | 172/177 (97%) | 175/177 (99%) | 2,04 sn | 5,18 sn | 0 | {'Mistral': 177} |
| mistral2603 | ikinci (14:49) | 30 | 468 ms | 840 ms | 29/30 (97%) | 29/30 (97%) | 2,30 sn | 5,56 sn | 0 | {'Mistral': 30} |

qwen2.5:7b yerelde (dizüstü CPU): süreleri bulutla karşılaştırılamaz.

## Maliyet

| Model | Tur | USD | soru başına |
|---|---|---|---|
| gemma4 | ana | 0.0415 | 0.00023 |
| gemma4 | ikinci | 0.0073 | 0.00024 |
| qwen36 | ana | 0.0847 | 0.00047 |
| qwen36 | ikinci | 0.0148 | 0.00049 |
| gpt54mini | ana | 0.3559 | 0.00197 |
| gpt54mini | ikinci | 0.0621 | 0.00207 |
| mistral2603 | ana | 0.0608 | 0.00034 |
| mistral2603 | ikinci | 0.0123 | 0.00041 |

Bu rapordaki koşular: 0.6393 USD. Adım 2 turunun toplam harcaması (geçersiz sayılan koşular dahil, `ham/` altındaki bütün dosyalar): 1.1720 USD (sınır 1,5 USD).
