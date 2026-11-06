# Adım 2 nihai tur: ara okuma (2026-11-05, 16:11–16:40)

Ham rapor: [nihai_c_rapor_2026-11-05.md](nihai_c_rapor_2026-11-05.md) (`python -m bench.answer_models --report-c nihai_c`). Plan: [§20](plan_cevap_modeli_2026-11-05.md).
- Set: 199 soru; 192 model çağrısı, 7 soru kural çıkışı.
- **Gemma 4 NextBit koşusu sürüyor**: bazı çağrılar akışın ortasında ~150 sn takılıyor. Tablodaki satırı kısmi (38 soru).
- Süre turu 1 ve 2, şemalı/şemasız ek süre ölçümü ve yerel taban henüz koşulmadı.

## Şema C, 8 yapılandırma (onaylı set, 199 soru)

| Yapılandırma | JSON/şema hatası | doğru "bulunamadı" | doğrulanmış görünen yanlış | cevaplı ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı (kapı 5/5) | değer aynı | gereksiz netleştirme (kapı 0) | ilk doğrulanmış cümle p50 / p95 (model; kapı ≤ 2,0 sn) | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|
| Gemma 4, DeepInfra fp8 | 2 | 17/17 | 0 | 109 / 2 / 19 | %95 | 4/5 | 8/13 | 2 | 2,52 / 6,33 sn | 0,045 |
| Gemma 4, Parasail bf16 | **34** (yarıda kesik) | 17/17 | 0 | 97 / 3 / 14 | %82 | 2/5 | 1/13 | 0 | 1,55 / 2,98 sn | 0,062 |
| Gemma 4, Venice bf16 | 1 | 17/17 | 0 | 114 / 2 / 16 | %96 | 4/5 | 9/13 | 2 | 2,82 / 7,19 sn | 0,075 |
| Gemma 4, NextBit bf16 | (sürüyor) | | | | | | | | | |
| Gemma 4 31B, Crusoe bf16 (referans) | **32** (yarıda kesik) | 17/17 | 0 | 92 / 3 / 10 | %70 | 4/5 | 7/13 | 3 | 1,46 / 2,87 sn | 0,083 |
| Qwen3.6, DeepInfra | 9 | 16/17 | **1** | 110 / 1 / 10 | %86 | 3/5 | 2/13 | 2 | 2,13 / 3,30 sn | 0,079 |
| GPT-5.4 mini, Azure | 2 | 16/17 | **1** | 136 / 0 / 3 | %87 | 2/5 | 1/13 | 0 | 1,64 / 6,70 sn | 0,337 |
| Mistral Small 2603 | 5 | 17/17 | 0 | 108 / 4 / 25 | %81 | 3/5 | 5/13 | 0 | 1,16 / 2,21 sn | 0,060 |

**JSON hataları:**
- **Parasail ve Crusoe:** hataların hepsi yarıda kesik (`finish=length`). Model şemaya zorlanınca bazı cevaplarda alanlar arasına token sınırına kadar boşluk basıyor. Bu, o sağlayıcıların yapılandırılmış çıktı motorundan kaynaklanıyor. §16 gereği yama yazılmaz; JSON metriğinde görünür. Aynı Gemma 4 DeepInfra ve Venice'te 1–2 hata var.
- **Qwen3.6:** 6 kez `tur=netlestirme` seçilip seçenekler yazılmamış (şema dışı).

**Kapılar (§18), ara durum:**
- **Değer farklı 5/5 netleştirme: hiçbir yapılandırma geçmiyor.** En iyisi 4/5: Gemma 4 DeepInfra/Venice ve Gemma 4 31B.
- **Gereksiz netleştirme 0:** Parasail, GPT-5.4 mini ve Mistral geçiyor; diğerlerinde 2–3.
- **Doğrulanmış görünen yanlış 0:** GPT-5.4 mini ve Qwen3.6'da 1. Gemma 4 ve Mistral geçiyor.
- **İlk doğrulanmış cümle ≤ 2,0 sn (model tarafı p95):** hiçbiri. En yakın Mistral (2,21), sonra Gemma 4 31B (2,87) ve Parasail (2,98). Gemma 4 DeepInfra ve Venice'te p95 6–7 sn.
- **≥ 2 ZDR sağlayıcı:** GPT-5.4 mini ve Mistral 1 sağlayıcılı.
- **Sonuç: Bu turda kapıların hepsini geçen yapılandırma yok.** Ayrıntılı karar süre turları ve NextBit bitince.

## Gemma 4: iki koşu ve iki şema (DeepInfra, 181 soru, aynı oturum)

| Koşu | doğru "bulunamadı" | yanlış ret | cevaplı ✓ / ⚠ / ✖ | beklenen değer | JSON | ilk token p50 / p95 | toplam p50 / p95 |
|---|---|---|---|---|---|---|---|
| Bugünkü şema, ilk tur (11:16) | 17/17 | 18/159 | 118 / 11 / 12 | 93/112 | 0 | 0,39 / 1,04 sn | 3,0 / 10,3 sn |
| Bugünkü şema, yeniden (16:16) | 17/17 | 18/159 | 118 / 11 / 12 | 92/112 | 0 | 0,41 / 0,93 sn | 4,0 / 11,0 sn |
| Şema C (16:16) | 17/17 | **25**/159 | 109 / 2 / **19** | 88/93 | 2 | 0,40 / 0,80 sn | 4,4 / 16,8 sn |

**Koşudan koşuya oynama (aynı şema, aynı sağlayıcı):** 180 sorunun hiçbirinde çıkış değişmedi; 6 rozet ve 1 beklenen değer değişti. Oynama küçük; aşağıdaki farklar şemadan geliyor.

**Şema C'nin Gemma 4'e etkisi:**
- Yanlış ret 18 → 25.
- ✖ 12 → 19: öğe başına doğrulama daha sıkı; sayının yalnız kendi alıntısında aranması dahil.
- ⚠ 11 → 2.
- Değer farklı netleştirme 2/5 → 4/5.
- Toplam süre p95 11 → 17 sn: alıntılar her cümlede tekrar ediyor.

**Bugünkü şemada 18 netleştirme sorusu (5 model):**
- Değer farklı: hepsi 2/5. Bunlar kural katmanının ceket/pantolon netleştirmeleri; model kendisi sormuyor ya da sorduğu netleştirme gösterilmiyor (atlanan 1–8).
- Değer aynı: Qwen3.6 5/13, GPT-5.4 mini 9/13, Gemma 4 8/13, Gemma 4 31B 7/13, Mistral 7/13.
- Şema C'de değer farklı en iyi 4/5; netleştirme modu modelin sorusunu kullanıcıya ulaştırıyor.

Harcama (nihai_* toplamı, NextBit kısmi dahil): 0,95 USD; sınır 3,0 USD.

## Süre turu 1 (şema C, 30 cevaplı soru, 16:37–17:00) ve şema ek süresi

[nihai_sure1_rapor_2026-11-05.md](nihai_sure1_rapor_2026-11-05.md). İlk doğrulanmış cümle model tarafı (istekten); kapı p95 ≤ 2,0 sn.

| Yapılandırma | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | toplam p95 | > 20 sn |
|---|---|---|---|---|
| Mistral 2603 | 490 ms / 1,07 sn | 1,25 / **2,16** sn | 3,7 sn | 0 |
| GPT-5.4 mini | 1,05 / 1,56 sn | 1,64 / **2,20** sn | 2,8 sn | 0 |
| Gemma 4, Parasail | 634 / 908 ms | 1,56 / **2,44** sn | 5,7 sn | 0 |
| Gemma 4, Venice | 571 / 923 ms | 1,99 / 3,03 sn | 5,7 sn | 0 |
| Gemma 4 31B, Crusoe | 444 / 892 ms | 1,46 / 3,08 sn | 6,0 sn | 0 |
| Gemma 4, NextBit | 401 / 600 ms | 2,30 / 3,15 sn | **135 sn** | **7** |
| Gemma 4, DeepInfra | 380 / 700 ms | 1,71 / 3,55 sn | 5,5 sn | 0 |
| Qwen3.6, DeepInfra | 685 ms / 1,38 sn | 3,82 / 8,89 sn | 10,3 sn | 0 |

- 2,0 sn kapısını bu turda da kimse tutmuyor. En yakınlar Mistral (2,16) ve GPT-5.4 mini (2,20), sonra Parasail (2,44).
- **NextBit:** ilk token en hızlısı ama 30 çağrının 7'si akış ortasında takılıp 20 sn'yi aşıyor (p95 135 sn). Ana koşuda da aynı. Üretim için uygun değil.
- **Şemaya zorlamanın ilk token ek süresi** (eşli p50, [sema_ek_suresi_2026-11-05.md](sema_ek_suresi_2026-11-05.md)): DeepInfra 9 ms, Mistral ~0, Venice 60, NextBit 72, Qwen3.6 81, Crusoe 86 (5 hata), Parasail 146, Azure 395 ms (şemalı p95 4,8 sn).
- Süre turu 2 (başka saatte), şema ek süresi s2 ve yerel taban sonraki oturumda.

## Tamamlandı: Gemma 4 NextBit (17:45) ve seçim önerisi

**NextBit (şema C, tam set):**
- 29 yarıda kesik JSON; bunların hepsi akış ortasında takılıp 20 sn'yi aşan çağrılar.
- Doğru "bulunamadı" 14/17 (%82).
- ✓ / ⚠ / ✖ 96 / 3 / 20; beklenen değer %86.
- İlk doğrulanmış cümle p95 4,79 sn; maliyet 0,12 USD.
- **Kalite kapısında ve JSON'da elenir.**

Nihai tur harcaması: **1,17 / 3,0 USD.**

**Kapı özeti (şema C, onaylı set):**

| Yapılandırma | kalite (bulunamadı ≥ %90, yanlış 0, değer ≥ %85) | JSON | netleştirme farklı 5/5 | gereksiz 0 | ≥ 2 ZDR | ilk doğrulanmış cümle ≤ 2,0 sn |
|---|---|---|---|---|---|---|
| Gemma 4, DeepInfra fp8 | **geçer** (17/17, 0, %95) | 2 | 4/5 (Q07) | 2 (Q26, A070) | geçer (13) | 3,55 sn (tur 1) |
| Gemma 4, Venice bf16 | **geçer** (17/17, 0, %96) | 1 | 4/5 (Q07) | 2 (Q26, A070) | geçer | 3,03 sn |
| Gemma 4, Parasail bf16 | değer %82 | **34 kesik** | 2/5 | 0 | geçer | 2,44 sn |
| Gemma 4, NextBit bf16 | bulunamadı %82 | **29 kesik** | 2/5 | 1 | geçer | 3,15 sn, takılmalar |
| Gemma 4 31B, Crusoe | değer %70 | **32 kesik** | 4/5 | 3 | geçer | 3,08 sn |
| Qwen3.6 | yanlış 1 | 9 | 3/5 | 2 | geçer (9) | 8,89 sn |
| GPT-5.4 mini | yanlış 1 | 2 | 2/5 | 0 | **1** | 2,20 sn |
| Mistral 2603 | değer %81 | 5 | 3/5 | 0 | **1** | 2,16 sn |

**Kapıların hepsini geçen yapılandırma yok.** Kalan farkların nedenleri:
- **Q07 (değer farklı, Gemma'da tek kaçan):** "Dış görünür dikişlerde SPI kaç olmalı?" Arama ceket/pantolon yerine makine kılavuzlarını getiriyor; Gemma "bulunamadı" diyor, Mistral S-7300A/B'yi soruyor. Bu bir **arama** sorunu, cevap modelinden bağımsız.
- **Gereksiz netleştirme Q26, A070:** İkisinde de belge içinde gerçek bir varyant ayrımı var (pantolon Type I/II overlok Tex'i; S-7300B -3/-5 spesifikasyonu). Kapı tanımı ürünler arası netleştirmeyi kastediyorsa bunlar gereksiz sayılmamalı. **Tanım kararı sizde.**
- **Süre:** Gemma 4'te ilk doğrulanmış cümle p95 3,0–3,6 sn (tur 1). C'de her öğe alıntıyla başlıyor; ilk öğenin alıntısı uzun.

**Öneri (karar sizde):**
1. **Cevap modeli: Gemma 4 26B A4B, şema C.** Sağlayıcılar **Venice (bf16) birincil, DeepInfra (fp8) ikincil.** İkisi bu sette aynı kalitede: bulunamadı, değer, netleştirme sonuçları aynı; nicemleme farkı burada etkisiz. ≥ 2 ZDR böyle sağlanır. Parasail, NextBit ve Crusoe şemaya zorlamada yarıda kesildiği için dışarıda (§16: yama yok).
2. **Süre kapısı için bir sonraki ölçüm (koşulmadı):** Bütün modellerde aynı şema değişikliği, alıntı üst sınırı 300 → 150 karakter ve "ilk öğe cevabın özü" kuralı. Yalnız ilk doğrulanmış cümle ve değer etkisi ölçülür. Tahmin: Gemma 4 iki sağlayıcı × 199 soru ≈ 0,13 USD.
3. **BRAND_ALIASES ve S-7300 grubu: silinebilir.** Şema C kurallar kapalıyken değer farklı 4/5, değer aynı 8–9/13 aldı. §11'in tabanı (a) 4/5 ve 8/13'tü; silme koşulu sağlanıyor.
4. **Q07** arama tarafında ayrıca incelenir (B4).
5. **Ertelenenler (sonraki oturum):** süre turu 2 ve şema ek süresi s2 (başka saatte), yerel taban (en düşük öncelik), yeni aday sorular (onayınızdan sonra, ilk iki model şema C ile).

## Şema C'nin kalite bedeli, Gemma 4 DeepInfra (kayıtlardan; karar 2026-11-05 gece)

Bugünkü şema (16:16 yeniden koşu) ile şema C (aynı oturum, aynı sağlayıcı), 180 soru.

**Yeni ✖ (12; ✖ → ✓ dönenlerle net +7):**

| Neden | Sorular | Sayı | Şemaya bağlı mı |
|---|---|---|---|
| Alıntıyı parçalayıp birleştirme: tablo satırının başlığı ("Remedy:", "Code:") ikinci maddeyle tek alıntıda, kaynakta bitişik değil | Q14, A146, A039, A075, A089 | 5 | **evet**: her cümle kendi alıntısını istediği için model satırı bölüyor |
| İki alıntıyı tek cümlede birleştirme (sayı başka öğenin alıntısında) | Q01 (IFF 8 (± 1) ile genel 11 (± 1) aynı cümlede) | 1 | **evet**: c150b (öğe başına 1–2 alıntı) bunu hedefliyor |
| OCR yorumu ("112 inch" = ½) | A021, A025 | 2 | hayır (bugünkü şemada da riskli; burada sıkı kontrol yakaladı) |
| Cümleye başka alfabeden karakter ("들") | N3, A015 | 2 | hayır (model hatası) |
| Diğer (alıntı sınırında kesilme vb.) | 2 | 2 | |

- Sizin tahmininiz (-3 ve -5 değerleri tek cümlede) bu sette 1 vakada (Q01) görüldü.
- Asıl bedel tablo satırlarının bölünmesi (5). c150b'de bir öğe iki alıntı alabildiği için ikisini de azaltması beklenir; ölçüm sürüyor.

**Yeni yanlış ret (7):**
- Çok parçalı ya da varyantlı soru (Q09 kumaş + gramaj, A033 iki etiket yeri): model her cümleye tek alıntı bulamayınca reddediyor (c150b ile ölçülecek).
- Uzun liste ya da prosedür (G7 panel düğmeleri, A102 kireç temizliği, A106 koruyucu ekipman): her maddeye alıntı gerektiği için ret.
- **Ret doğru yönde (2):** A024 (bugünkü şemada da "spesifik bilgi yok" diyen kaçamak cevap), A086 (bugünkü şemada yanlış konunun değeri: ilik boyu).
- Net: 7 retten 2'si iyileşme, 5'i şemanın bedeli.

**Netleştirme kapısı, yeni tanım (yeniden puanlandı):**
- Gereksiz netleştirme = değer aynıyken ya da soruda ürün/varyant belirtilmişken sorulan netleştirme.
- Belge içi varyant: netleştirme YA DA bütün varyantların değerleri doğru.
- Q26 ve A070 belge içi varyant ([eval/netlestirme_siniflari.json](../../netlestirme_siniflari.json)):
  - A070: S-7300B s.98'de 5 mm, s.102–103'te 6 mm.
  - Q26: pantolon s.8'de Tex 31–35, s.9'da 40 / 39 / 16 / 24–27.
- **İkisinin de beklenen cevabı varyantları kapsamıyor** (yalnız 5 ve 31–35). Güncelleme önerisi: beklenen "5 / 6 mm" ve "31–35 / 40…", onayınızla.
- Yeni tanımla Gemma 4 DeepInfra ve Venice: **gereksiz netleştirme 0**, belge içi varyant 2/2. Kalan kapı farkları: Q07 (arama; plan §21) ve süre.

## Süre ölçümü: şema C varyantları (c150, c150b), Gemma 4 DeepInfra + Venice, tam set (17:57–18:20)

Karar 2026-11-05 gece: bütün modellerde aynı genel değişiklik, iki varyant.
- **c150:** alıntı en fazla 150 karakter, ilk öğe yalnız cevabın özü.
- **c150b:** c150 + öğe başına 1–2 alıntı (`alintilar`, en fazla 2).

Kabul ölçütü: süre kısalırken beklenen değer ve yanlış ret kötüleşmemeli.

**Ölçüm aracı düzeltmesi:** Doğrulama aracı, sınıra dayanıp kesilen alıntıya toleransı yalnız 300 karakterde tanıyordu (`verify._cut_quote_prefix`, 16 Ekim kuralı). c150'de 150 karakterde kesilen alıntılar ✖ oluyordu. Tolerans artık varyantın kendi sınırına bağlı (`schema_c.QUOTE_LIMIT`). İki varyant kayıtlardan yeniden puanlandı (`--rescore-c`): koşu başına 19–21 rozet düzeldi.

**İlk doğrulanmış cümle:** Bu varyantların kayıtlarına akış zaman çizelgesi yazılmamıştı. Değer yaklaşık: ilk token ile toplam süre arasında, öğenin bittiği karakter konumuna göre doğrusal. Aynı yöntem şema C'nin gerçek akış ölçümüyle karşılaştırıldı: DeepInfra p95'te gerçek 6,33, yaklaşık 6,79 sn. Yakın, biraz kötümser.

| Şema | Sağlayıcı | yanlış ret | cevaplı ✓ / ⚠ / ✖ | beklenen değer | JSON | ilk doğrulanmış cümle p50 / p95 (yaklaşık) | toplam p95 |
|---|---|---|---|---|---|---|---|
| C | DeepInfra | 25/159 | 109 / 2 / 19 | 88/93 (%95) | 2 | 2,52 / 6,79 sn | 16,3 sn |
| C | Venice | 24/159 | 114 / 2 / 16 | 90/94 (%96) | 1 | 2,74 / 6,71 sn | 15,4 sn |
| c150 | DeepInfra | 24/159 | 103 / 1 / **27** | 88/93 (%95) | 1 | 2,42 / 4,08 sn | 10,2 sn |
| c150 | Venice | 24/159 | 99 / 2 / **28** | 88/93 (%95) | 3 | 2,57 / 4,14 sn | 10,2 sn |
| **c150b** | DeepInfra | 24/159 | 112 / 1 / 18 | 88/94 (%94) | 3 | 2,36 / **4,70** sn | 10,4 sn |
| **c150b** | Venice | 24/159 | 113 / 0 / 17 | 88/93 (%95) | 3 | 2,71 / **4,63** sn | 10,5 sn |

**Okuma:**
- **c150b kabul ölçütünü geçiyor:** p95 6,7–6,8 → 4,6–4,7 sn, toplam süre p95 16 → 10 sn. Beklenen değer aynı (88 doğru), yanlış ret aynı (24–25), ✖ aynı (19/16 → 18/17).
- **c150 süreyi biraz daha kısaltıyor (p95 ~4,1 sn) ama ✖ artıyor (19 → 27).** Tek alıntıyla sınırlı cümle, iki kaynak parçasına dayanan bilgiyi bölmek zorunda kalıyor; c150b bunu çözüyor.
- **Öneri: şema C'nin son biçimi c150b.**
- **2,0 sn kapısı (model tarafı p95) yine tutmuyor.** p50 ~2,4 sn; ilk öğenin alıntısı ve metni birlikte ~100–150 token. Kalan seçenekler (koşulmadı):
  - kapı tanımının ilk token + ilk öğe olarak gözden geçirilmesi;
  - arama öncesi süreyi kısaltıp (çeviri Gemma 4 NextBit, §14) uçtan uca 3 sn kapısını hedeflemek;
  - Venice/DeepInfra dışında hızlı bir ZDR sağlayıcısı. Parasail p95 2,4 sn'ydi ama şemaya zorlamada JSON kesiyor.
- Maliyet: dört koşu toplam ~0,24 USD.

## Kararlar (2026-11-05 gece)

- Cevap modeli Gemma 4 26B A4B; sağlayıcılar yalnız Venice (birincil) ve DeepInfra (ikincil).
- Şema C'nin çalışma biçimi **c150b**.
- **Açık fark:** c150b, bugünkü şemaya göre yanlış ret 18 → 24 (+6) ve ✖ 12 → 18 (+6) (Gemma 4 DeepInfra, aynı 159 soru). İkisi de güvenli yönde. c150b bundan sonra bugünkü şemayla da karşılaştırılacak (devir notu, madde d).

## 2026-11-06 (a): Q26 ve A070 varyant etiketiyle, kayıtlardan yeniden puanlama (model çağrısı yok)

**Beklenen cevaplar, varyant etiketiyle:**

| Soru | Varyant | Değer | Kaynak |
|---|---|---|---|
| A070 (S-7300B iplik kesme kamı, iğne mili) | standart | 5 mm | s.98 `<Thread trimming cam position adjustment>` |
| | **Premier** spesifikasyonu | 6 mm | s.102–103, "12-11-1. Thread trimming (Premier specifications)" |
| Q26 (pantolon overlok Tex) | **Type I** pantolon | 31–35 | TABLE I, s.8: Overedge stitching (raw edges) |
| | **Type II** pantolon | 40 (/ 39 / 16 / 24–27) | TABLE II, s.9: Overedge/Serge … raw edge cover |

**Eşleştirici** (`bench.common.variants_in`, testli):
- Her değer kendi etiketiyle aynı yan cümlede ya da öğede geçmeli. Etiketsiz "5 / 6 mm" ve ters eşleşme ("Premier 5 mm, standart 6 mm") doğru sayılmaz.
- Belge içi varyantta doğru = netleştirme YA DA iki varyantın da etiketiyle verilmesi.

**Yeniden puanlama sonucu (bütün kayıtlar):**
- **Bugünkü şema:** cevap veren her model iki soruda da yalnız tek varyantı veriyordu (31–35 ya da 5 mm). Önceki eşleştiricide "beklenen değer doğru" sayılan bu cevaplar artık doğru değil. Tek istisna Qwen3.6 ilk turda Q26: iki tipi etiketiyle verdi.
- **Şema C:**
  - Gemma 4 DeepInfra ve Venice, Gemma 4 NextBit (A070) ile c150 ve c150b Venice: netleştirme sordu, doğru.
  - c150b DeepInfra A070'te ve Gemma 4 31B A070'te yalnız 5 mm verdi, yanlış.
  - GPT-5.4 mini, Mistral ve Qwen3.6 tek varyantı verdi.
- Raporlar yeniden üretildi; beklenen değer sayıları bu iki soru kadar (≤ 2) değişebilir.
- Gemma 4 DeepInfra/Venice şema C: belge içi varyant 2/2, gereksiz netleştirme 0.

## 2026-11-06 (b): 46 yeni soru, Gemma 4 DeepInfra + Venice, c150b (0,017 USD)

`python -m bench.answer_models --schema c150b --setler aday_sorular_ek --tag nihai_ek --models gemma4 gemma4_venice`. Set: 36 "bulunamadı", 10 "değer farklı" netleştirme.

| | DeepInfra | Venice |
|---|---|---|
| "Bulunamadı": model kararıyla doğru | 33/34 | 33/34 (1 JSON yarıda kesik) |
| "Bulunamadı": kural çıkışı | 2 (kod yok 1, netleştirme 1) | 2 |
| "Bulunamadı" sorusunda **doğrulanmış cevap** | **1: B012** | 0 |
| Değer farklı netleştirme doğru | 6/10 (kural 5, model 1) | 6/10 |
| Maliyet | 0,0075 USD | 0,0096 USD |

**Kaynaktan birebir alıntıyla cevaplanan "bulunamadı" sorusu: B012 (DeepInfra), kullanıcıya:**
- Soru: "S-7300A'da dijital baskı ayağı kaldırıcısının kaldırma yüksekliği nasıl ayarlanır?"
- Cevap (✓, 6 öğenin hepsi doğrulandı): "Kaldırma kolu (lifting lever) (2) ile baskı ayağı (1) kaldırıldığında standart yükseklik 6 mm olmalıdır. Somunu (3) gevşetin…"
- Alıntı: "The standard height of the presser foot (1) is 6 mm when the presser foot (1) is raised by means of the lifting lever (2)…"
- Okuma: Cevap **mekanik kaldırma kolunun** ayarı; soru **dijital ayak kaldırıcıyı** soruyor. Aday ajan bu riski önceden işaretlemişti.
- **Karar sizde:** etiket doğruysa bu, kaynakta olmayan şeyi yakın bir konuyla cevaplayan doğrulanmış yanlıştır. Kaynakta dijital ayak kaldırıcı için bu ayar varsa etiket düzeltilir.

**Kaçan değer farklı netleştirmeler (iki sağlayıcıda aynı):**
- **C001** (S-7300A/B diz kaldırıcı yüksekliği 16 / 13 mm), **C004** (overlok SPI ceket/pantolon), **C009** (alt kenar baskı genişliği): model "bulunamadı".
- **C003** (besleme yörüngesi 1, 5,0 mm adımda hız): tek değer.
- S-7300 aile kuralı silindiği için bu sorular yalnız modele kalıyor; model bu üçünde netleştirme seçmiyor. Ürün şartnamesi soruları (ceket/pantolon) kural katmanının arama sonrası netleştirmesiyle doğru.

## 2026-11-06 (c): ikinci çeviri sağlayıcısı (Gemma 4, 15 soru × 2 mod, iç içe; 0,0016 USD)

[asama4_ceviri_saglayici_2026-11-06.md](../b4/asama4_ceviri_saglayici_2026-11-06.md):

| Sağlayıcı | çağrı | p50 | p95 | en uzun | > 1,2 sn |
|---|---|---|---|---|---|
| NextBit | 30 | 512 ms | 917 ms | 1,19 sn | 0 % |
| **Venice** | 30 | 783 ms | 1,21 sn | 1,23 sn | 7 % |
| DeepInfra | 30 | 899 ms | 1,82 sn | 3,15 sn | 20 % |

**Öneri: ikinci çeviri sağlayıcısı Venice** (`only: [nextbit, venice]`). DeepInfra 1,2 sn sınırını beşte bir aşıyor.

## 2026-11-06 (d): c150b'nin bugünkü şemaya kalan farkı, kayıtlardan (model çağrısı yok)

**Tablo başlığı + madde birleştirme** (c → c150b, DeepInfra / Venice):

| Soru | c | c150b DeepInfra | c150b Venice |
|---|---|---|---|
| Q01 | ✖ (11 alıntıda yok) | ✓ | ✓ |
| A039 | ✖ birebir değil | ✓ | ✓ |
| A075 | ✖ birebir değil | ✓ | ✓ |
| A089 | ✖ birebir değil | ✓ | ✓ |
| Q14 | ✖ | ✖ | ✖ |
| A146 | ✖ | ✖ | ✓ |

- Q14/A146 (ve aynı aileden A038, A062) hâlâ ✖. Model tablo hücresinin sütun başlığını ("Remedy: ") kaynakta ona bitişik olmayan **ikinci maddenin** önüne ekliyor: "Remedy: ・Turn off the power and check the connection of connector P2". Kaynakta başlıktan sonra birinci madde geliyor.
- Aynı öğedeki iki maddenin birlikte alıntısı birebir ve doğrulanıyor; hata yalnız ikinci maddeyi tek başına alıntılarken çıkıyor.
- Diğer "birebir değil" hatalarında tablo sütunları " | " ile birleştiriliyor: A017 ("Length: Long | Size 36: 17"), A073 ("(8) | Shortcut 1 key | …").
- c150b'de 22 / 21 ✖ var. Bunların 9'u alıntı birebir değil, 7'si cümle sayısı alıntıda yok, 3'ü JSON. ✖'ler güvenli yönde: rozet yok, kaynak gösteriliyor.

**Uzun liste retleri: token sınırı mı, maxItems mi? İkisi de değil.**

| Soru | bugün | c150b (iki sağlayıcı) |
|---|---|---|
| G7 (7 düğme) | ✓ | **✓ 7 öğe** (c'de ret idi; c150b düzeltti) |
| A102 (3 adım) | ⚠ atıfsız | ret, `finish=stop`, 33 token |
| A106 (4 KKD) | ✓ | ret, `finish=stop`, 31 token |
| Q09 | ✓ ama **değer yanlış** (gramaj yok dedi) | ret, 32 token |
| A033 | ✖ (başka etiketleri anlattı) | ret, 32 token |

- Retlerin hepsi ilk token'larda verilmiş "bulunamadi" kararı: liste yazılmaya başlanmamış, 8 öğe sınırına da gelinmemiş.
- **max_tokens 700 → 1200 bu retleri düzeltmez.** Q09 ve A033'te bugünkü şemanın cevabı da yanlıştı; ret orada daha iyi. Gerçek kayıp A102 ve A106.

**Kesik JSON'lar (max_tokens'ın gerçekten etkilediği yer):**
- A074 (iki sağlayıcı), A080 (DeepInfra), Q05 (Venice): `finish=length`, 700 token.
- Hepsi 8 öğe × 2 alıntılık arıza giderme listeleri.
- **A066 kesik değil:** `finish=stop`, 291 token; alıntının içinde kaçışsız sekme karakteri var, katı JSON okuyucu reddediyor. JSON okunsa da ikinci öğedeki "2.00" alıntıda olmadığı için ✖ olurdu.
- Uygulamanın JSON hata mesajı (pilot/pipeline.py:328) her durumda "uzunluk sınırında kesildi" diyor; A066'da bu yanlış.

**Tekrar eden alıntı:** cevap karakterlerinin %5'i aynı cevapta daha önce geçen alıntının tekrarı (199 sorunun 10'unda). Numarayla geri dönmenin hız kazancı küçük; asıl getirisi Q14 ailesi (ikinci maddeyi yeniden yazmak yerine önceki tam alıntıya dönmek).
