# Adım 2, ilk tur: okuma (2026-11-05)

> **Set onayı (2026-11-05 akşam, ölçüt düzeltildi):** Aday setin 154/155 sorusu onaylı; A038 kullanıcıda. Onay ölçütü model çıktısı değil: kanıt cümlesi beklenen sayfada ve beklenen değer kanıtta, "bulunamadı" sorularında 27 Ekim korpus araması ([aday_sorular.md](../../aday_sorular.md)). Model çelişkisi yalnız bilgi. Daha önce model çıktısına dayanan ilk onaydaki yanlılık bu ölçütle kalktı. OCR soruları (14) raporda ayrıca gösteriliyor. Beklenen değer eşleştiricisi değer olarak karşılaştırıyor ("0.4–0.7" = "0.4 ile 0.7"); ilk tur yeniden puanlandı.
> **Bu koşu ön elemedir; nihai seçim onaylı ve büyütülmüş sette yapılacak.**
> **Aşırı uyum notu:** Aday arama ayarları bu setle seçildi; görülmemiş doküman testi ayrı tutulan JUKI seti.

Ham tablo: [adim2_cevap_modeli_2026-11-05.md](adim2_cevap_modeli_2026-11-05.md). Plan: [plan_cevap_modeli_2026-11-05.md](plan_cevap_modeli_2026-11-05.md).

Ek koşular:
- **İkinci süre turu: 14:41'de koşuldu** (16:30 yerine; 30 soru × 4 model, sabahtan farklı saat, yeni `verify.py`). 429, hata ve cevapsız soru yok; 0,097 USD. Toplam harcama 1,17 USD (sınır 1,5).
- Yerel taban qwen2.5:7b: ertelendi, nihai turda yeni şemayla (plan §17).

## Özet tablo (cevaplı: onaylı 37 soru; "bulunamadı": modelin karar verdiği 17 soru)

| | Gemma 4 26B A4B | Qwen3.6 35B A3B | GPT-5.4 mini | Mistral Small 2603 |
|---|---|---|---|---|
| Doğru "bulunamadı" (17) | **17** | 10 | 12 | **17** |
| … doğrulanmış görünen yanlış cevap (hedef 0) | **0** | 4 | 5 | **0** |
| Yanlış ret, onaylı / onaysız | 11% / 11% | 0% / 7% | 5% / 6% | 5% / 8% |
| … bunların kaynağı ilk 5'teydi (model hatası) | 1 / 3 | 0 / 2 | 1 / 2 | 1 / 3 |
| Cevaplarda ✓ / ⚠ / ✖, onaylı (verify A+B) | 27 / 5 / 1 | 26 / 5 / 6 | **29 / 4 / 2** | 9 / 17 / 7 |
| … onaysız (verify A+B; önceki ✖) | 91 / 6 / 12 (29) | 94 / 7 / 14 (18) | 100 / 10 / 6 (8) | 49 / 32 / 29 (41) |
| Beklenen değer cevapta, onaylı | 17/18 | 17/21 | 18/20 | 18/19 | *(eski eşleştirici, onay öncesi 37 soru)*
| Beklenen değer cevapta, bütün cevaplı (yeni eşleştirici) | 92/100 (%92) | 90/106 (%85) | 89/106 (%84) | 84/102 (%82) |
| JSON sorunu (177 çağrı) | 0 | 0 | 0 | 5 yarıda kesik |
| İlk token p50 / p95 | 388 ms / 1,04 sn | 648 ms / 1,57 sn | 762 ms / 1,36 sn | 449 ms / 991 ms |
| … ikinci tur (14:41, 30 soru) | 350 ms / 1,90 sn | 715 ms / **10,7 sn** | 776 ms / 1,06 sn | 468 ms / 840 ms |
| Toplam süre p95 | 10,3 sn | 17,1 sn | 3,2 sn | 5,2 sn |
| … ikinci tur | 5,5 sn | 24,5 sn (5 çağrı > 20 sn) | 2,7 sn | 5,6 sn |
| ZDR sağlayıcı sayısı | 13 | 9 | 1 (Azure) | 1 (Mistral) |
| 429 / cevapsız | 0 / 0 | 0 / 0 | 0 / 0 | 0 / 0 |
| Soru başına maliyet | 0,00023 USD | 0,00047 USD | 0,00197 USD | 0,00034 USD |

## Okuma (ön eleme; karar değil)

- **"Bulunamadı" hedefinde (≥ %90, doğrulanmış görünen yanlış 0) iki model var: Gemma 4 ve Mistral Small 2603.** İkisi de modelin karar verdiği 17 sorunun hepsinde doğru "bulunamadı" dedi; Taban %48'di (21 soru, 2026-10-27).
  - GPT-5.4 mini ve Qwen3.6 bu hedefi tutmuyor. Cevapsız sorulara cevap yazdılar ve bunların 4–5'i ✓/⚠ rozeti aldı: kullanıcının güveneceği yanlış cevap.
- **Bedeli yanlış ret.** Gemma 4 cevaplı soruların %11'inde "bulunamadı" diyor. Bunların çoğunda doğru kaynak zaten ilk 5'te yoktu (arama hatası); kaynak ilk 5'teyken reddettiği 4 soru var. Mistral'de yanlış ret %5–8.
- **Cevap kalitesi: GPT-5.4 mini en temiz.**
  - GPT-5.4 mini: onaylı sette 29/35 ✓, yalnız 2 ✖. Ama en pahalı (Gemma'nın ~8,5 katı) ve tek ZDR sağlayıcılı.
  - Gemma 4: 27/33 ✓. ✖'lerin ana nedeni cevapta alıntıda olmayan sayı (28), sonra eksik [n] atfı (15).
  - Mistral 2603: formata en az uyan model. 61 cevapta geçerli [n] atfı yok, 35'inde alıntıda olmayan sayı var, 5 çağrıda JSON yarıda kesildi. Bu yüzden ✓ sayısı düşük (6/33). Modele özel istem ayarı yapılmadı (karar).
- **Süre, ikinci tur:** Mistral ve GPT-5.4 mini iki turda da kararlı (ilk token p95 ≤ 1,1 sn). Gemma 4'ün p95'i 1,04 → 1,90 sn (DeepInfra, 30 soruda 3 yavaş çağrı); Qwen3.6 öğleden sonra DeepInfra'da belirgin yavaş (p95 10,7 sn). Tek sağlayıcı ölçümü saatten saate değişiyor; Gemma 4'ün bf16 sağlayıcıları nihai turda (§12).
- **Süre:** Dördünün de ilk token p50'si 0,4–0,8 sn. Gemma 4 ve Mistral'de p95 ~1 sn; Qwen3.6'da 1,6 sn. Toplam sürede Qwen3.6 (p95 17 sn, 6 çağrı > 20 sn) ve Gemma 4 (p95 10 sn) uzun; uzun cevap yazıyorlar.
- **Dayanıklılık:** Bu koşuda 429 ya da hata yok. Gemma 4 (13) ve Qwen3.6 (9) çok sağlayıcılı; GPT-5.4 mini ve Mistral tek sağlayıcılı. 5 Kasım sabahki süre ölçümünde tek sağlayıcılı gösterge model (mistral-small 2501, DeepInfra) 160 sorunun 11'inde 429 vermişti.
- **Ön eleme önerisi:** Gemma 4 önde. "Bulunamadı" hedefini tutuyor, en ucuz, en çok sağlayıcılı, ilk tokeni hızlı. Zayıf yanı cevaplardaki alıntıda olmayan sayılar ve yanlış ret. Mistral Small 2603 ikinci; format sorunları onaylı sette yeniden bakılmalı.
  - Nihai seçim onaylı ve büyütülmüş "bulunamadı" setinde yapılacak (plan §8).

## Kayıtlardan ek analiz ve verify.py A+B (model kararı bekliyor)

[okuma_sayi_uzunluk_2026-11-05.md](okuma_sayi_uzunluk_2026-11-05.md); araç çıktısı [adim2_analiz_2026-11-05.md](adim2_analiz_2026-11-05.md). Yeni model çağrısı yok.
- **"Alıntıda olmayan sayı" vakalarının çoğu doğrulayıcıdan.** `verify.py` yalnız `[1]` biçimini atıf sayıyor: Gemma'nın `[1, 2]` yazdığı atıfların içindeki sayılar ✖ yapıyor. Genel düzeltme (A+B) 2026-11-05'te **uygulandı**; ilk tur kayıtlardan yeniden puanlandı (yukarıdaki tablo). Etkisi:
  - Gemma 4 onaysız sette ✖ 29 → 12;
  - GPT-5.4 mini 8 → 6;
  - hiçbir cevap kötüleşmedi.
  - Bu son yama; sonraki adım yapılandırılmış cevap şeması (plan §15) ve "model değişikliği yalnız yapılandırma" ilkesi (§16).
- **Gerçek uydurma:** Gemma 0, Qwen3.6 0, GPT-5.4 mini 0, Mistral 2.
- **OCR'ı bozuk kaynak değerleri** ("112 inch" = ½): Modeller yorumluyor, bazen yanlış. Doğrulayıcı bunları doğru yakalıyor.
- **Uzunluk:** Uzun cevapta ✖ daha sık. Ortak sınır şimdilik önerilmiyor (plan §13).
- **Gemma 4 sağlayıcıları:** İlk tur DeepInfra **fp8** üzerindeydi. Önerilen üretim listesi NextBit, Parasail ve Venice; üçü de bf16. Bu ölçüm nihai tura taşındı (§12): Gemma 4 orada doğrudan bu üç sağlayıcıda koşulacak, DeepInfra fp8 referans. Nihai tur için ayrı bütçe gerekiyor (~1,3 USD tahmini).

## Ölçümle ilgili not

İlk koşu geçersiz sayıldı ve saklanıyor: [adim2_cevap_modeli_2026-11-05_bozuk.md](adim2_cevap_modeli_2026-11-05_bozuk.md). Nedeni ölçüm aracındaki bir hataydı: akış satırları Latin-1 çözüldü, "±" ve Türkçe harfler bozuldu, alıntı doğrulaması yanlış sonuç verdi.

Düzeltip yeniden koşuldu ve teste bağlandı. Modellerin "bulunamadı"/cevap kararları iki koşuda da aynı yönde. Qwen3.6 bu koşuda 12 yerine 10 doğru "bulunamadı" verdi; temperature 0'da bile koşular arasında küçük oynama var.

Harcama: ilk tur 0,54 USD, geçersiz koşuyla birlikte 1,08 USD (sınır 1,5 USD). İkinci süre turu için tahmin ~0,09 USD.
