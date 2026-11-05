# Adım 2, ilk tur: okuma (2026-11-05)

> **"Bulunamadı" kararının 17 sorusu onaysız (A114–A130). Bu koşu ön elemedir; nihai seçim onaylı ve büyütülmüş
> sette yapılacak.** Modelin karar verdiği 17 cevapsız sorunun 15'i onaysız: bir soru ≈ 6 puan.

Ham tablo: [adim2_cevap_modeli_2026-11-05.md](adim2_cevap_modeli_2026-11-05.md). Plan: [plan_cevap_modeli_2026-11-05.md](plan_cevap_modeli_2026-11-05.md).

Bekleyenler:
- İkinci süre turu: bugün 16:30, 30 soru × 4 model, başka saatte.
- Yerel taban qwen2.5:7b: bu gece 23:00.

Rapor, ikisi bitince aynı araçla yeniden üretilecek.

## Özet tablo (cevaplı: onaylı 37 soru; "bulunamadı": modelin karar verdiği 17 soru)

| | Gemma 4 26B A4B | Qwen3.6 35B A3B | GPT-5.4 mini | Mistral Small 2603 |
|---|---|---|---|---|
| Doğru "bulunamadı" (17) | **17** | 10 | 12 | **17** |
| … doğrulanmış görünen yanlış cevap (hedef 0) | **0** | 4 | 5 | **0** |
| Yanlış ret, onaylı / onaysız | 11% / 11% | 0% / 7% | 5% / 6% | 5% / 8% |
| … bunların kaynağı ilk 5'teydi (model hatası) | 1 / 3 | 0 / 2 | 1 / 2 | 1 / 3 |
| Cevaplarda ✓ / ⚠ / ✖, onaylı | 27 / 5 / 1 | 24 / 5 / 8 | **29 / 4 / 2** | 6 / 17 / 10 |
| Beklenen değer cevapta, onaylı | 17/18 | 17/21 | 18/20 | 18/19 |
| JSON sorunu (177 çağrı) | 0 | 0 | 0 | 5 yarıda kesik |
| İlk token p50 / p95 | 388 ms / 1,04 sn | 648 ms / 1,57 sn | 762 ms / 1,36 sn | 449 ms / 991 ms |
| Toplam süre p95 | 10,3 sn | 17,1 sn | 3,2 sn | 5,2 sn |
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
- **Süre:** Dördünün de ilk token p50'si 0,4–0,8 sn. Gemma 4 ve Mistral'de p95 ~1 sn; Qwen3.6'da 1,6 sn. Toplam sürede Qwen3.6 (p95 17 sn, 6 çağrı > 20 sn) ve Gemma 4 (p95 10 sn) uzun; uzun cevap yazıyorlar.
- **Dayanıklılık:** Bu koşuda 429 ya da hata yok. Gemma 4 (13) ve Qwen3.6 (9) çok sağlayıcılı; GPT-5.4 mini ve Mistral tek sağlayıcılı. 5 Kasım sabahki süre ölçümünde tek sağlayıcılı gösterge model (mistral-small 2501, DeepInfra) 160 sorunun 11'inde 429 vermişti.
- **Ön eleme önerisi:** Gemma 4 önde. "Bulunamadı" hedefini tutuyor, en ucuz, en çok sağlayıcılı, ilk tokeni hızlı. Zayıf yanı cevaplardaki alıntıda olmayan sayılar ve yanlış ret. Mistral Small 2603 ikinci; format sorunları onaylı sette yeniden bakılmalı.
  - Nihai seçim onaylı ve büyütülmüş "bulunamadı" setinde yapılacak (plan §8).

## Ölçümle ilgili not

İlk koşu geçersiz sayıldı ve saklanıyor: [adim2_cevap_modeli_2026-11-05_bozuk.md](adim2_cevap_modeli_2026-11-05_bozuk.md). Nedeni ölçüm aracındaki bir hataydı: akış satırları Latin-1 çözüldü, "±" ve Türkçe harfler bozuldu, alıntı doğrulaması yanlış sonuç verdi.

Düzeltip yeniden koşuldu ve teste bağlandı. Modellerin "bulunamadı"/cevap kararları iki koşuda da aynı yönde. Qwen3.6 bu koşuda 12 yerine 10 doğru "bulunamadı" verdi; temperature 0'da bile koşular arasında küçük oynama var.

Harcama: ilk tur 0,54 USD, geçersiz koşuyla birlikte 1,08 USD (sınır 1,5 USD). İkinci süre turu için tahmin ~0,09 USD.
