# "Bulunamadı" davranışı uçtan uca

Cevabı olmayan sorular tam hattan geçirildi (model dahil). Doğru: herhangi bir 'bulunamadı' çıkışı. Yanlış: model alakasız kaynaktan cevap üretti (`model_cevap`) ya da gereksiz netleştirme. Skor: rerank açıkken reranker, kapalıyken RRF (hibrit). Onaylı sorular ve aday taslak (onaysız) ayrı. Sonradan cevaplı sayılıp çıkarılan: questions:Q09.

| Yol | soru | doğru 'bulunamadı' | oran | model cevap üretti | … doğrulanmış görünen | netleştirme | çıkışlar |
|---|---|---|---|---|---|---|---|
| eski_rerank | 21 | 13 | 62% | 7 | 2 | 1 | kod_yok 2, model_bulunamadi 9, model_cevap 7, netlestirme 1, yabanci_marka 2 |
| yeni_varsayilan | 21 | 10 | 48% | 7 | 3 | 4 | kod_yok 2, model_bulunamadi 6, model_cevap 7, netlestirme 4, yabanci_marka 2 |

## Soru soru

| Soru | eski_rerank | yeni_varsayilan | ilk 3 kaynak (skor) — eski_rerank |
|---|---|---|---|
| questions:Q08 Nike ceketlerinde yaka dikişi kaç mm olmalı? | yabanci_marka | yabanci_marka | arama yok |
| questions:Q10 Uçak motoru yağı kaç derecede değiştirilir? | model_cevap (✖ Doğrulanamadı):  | model_bulunamadi | granovsky-1986 s.[47, 48] (-3.82); granovsky-1986 s.[178] (-4.45); granovsky-1986 s.[225, 226] (-5.42) |
| questions:Q18 Nike tişörtlerinde yaka ribanası kaç cm olmalı? | yabanci_marka | yabanci_marka | arama yok |
| questions_ek:Q31 S-7300A'nın motor gücü kaç watt? | model_bulunamadi | model_cevap (✖ Doğrulanamadı):  | brother-s7300a s.[85] (-5.83); brother-s7300a s.[85] (-6.01); brother-s7300a s.[53] (-6.70) |
| aday:A114 Bosch freze tablası kaç kilogram ağırlığında? | model_cevap (⚠ Kısmen doğrulandı): Bosch freze tablası kg adımlarında ağırlık olarak belirtilmiştir. | model_cevap (⚠ Kısmen doğrulandı): Bosch freze tablası kg unitesinde ağırlığını ifade eder. | bosch-ra1171 s.[87] (-6.93); bosch-ra1171 s.[77] (-7.34); bosch-ra1171 s.[77] (-7.59) |
| aday:A115 Granovsky kitabına göre bilgisayarlı nakış makinesinin yazıl | model_bulunamadi | model_bulunamadi | granovsky-1986 s.[150, 151] (-7.69); granovsky-1986 s.[109] (-8.10); granovsky-1986 s.[148, 149] (-8.29) |
| aday:A116 Pantolon şartnamesinde kemer tokası kaç gram olmalı? | model_bulunamadi | netlestirme | gl-pd-07-14a s.[23] (-7.18); gl-pd-07-14a s.[13] (-8.44); gl-pd-07-14a s.[7] (-8.50) |
| aday:A117 S-7300A'da E133 hatası ne demek? | kod_yok | kod_yok | brother-s7300a s.[98] (-4.50); brother-s7300a s.[98] (-6.01); brother-s7300a s.[98] (-6.37) |
| aday:A118 S-7300A'da E-740 kodu çıktı, ne yapmalıyım? | model_cevap (✖ Doğrulanamadı):  | model_cevap (✖ Doğrulanamadı):  | brother-s7300a s.[100] (-4.35); brother-s7300a s.[100] (-5.09); brother-s7300a s.[100] (-5.23) |
| aday:A119 S-7300A'da E582 hatası neden olur? | kod_yok | kod_yok | brother-s7300a s.[100] (-2.58); brother-s7300a s.[100] (-6.31); brother-s7300a s.[99] (-6.34) |
| aday:A120 Bosch freze tablasının garanti süresi ne kadar? | model_bulunamadi | netlestirme | bosch-ra1171 s.[87] (-4.45); bosch-ra1171 s.[68] (-4.95); bosch-ra1171 s.[77] (-7.19) |
| aday:A121 Mr. Coffee kahve makinesi kaç watt? | model_bulunamadi | netlestirme | mrcoffee-2003 s.[17] (-4.09); mrcoffee-2003 s.[7] (-4.57); mrcoffee-2003 s.[17] (-4.90) |
| aday:A122 Mr. Coffee kahve makinesiyle süt nasıl köpürtülür? | model_bulunamadi | netlestirme | mrcoffee-2003 s.[16] (-3.87); mrcoffee-2003 s.[17] (-4.61); mrcoffee-2003 s.[7] (-5.09) |
| aday:A123 S-7300B'nin güç tüketimi kaç watt? | model_bulunamadi | model_bulunamadi | brother-s7300b s.[23] (-0.32); brother-s7300b s.[88] (-6.30); brother-s7300b s.[88] (-6.63) |
| aday:A124 Ceketin kapüşon ölçüleri nedir? | model_bulunamadi | model_bulunamadi | gl-pd-14-04a s.[49] (-4.63); gl-pd-14-04a s.[49] (-4.99); gl-pd-14-04a s.[49] (-5.01) |
| aday:A125 Ceket fermuarı hangi markadan olmalı? | model_cevap (⚠ Kısmen doğrulandı): Ceket fermuarı A-A-50199, Type II markasından olmalı. | model_cevap (✖ Doğrulanamadı):  | gl-pd-14-04a s.[3] (-6.66); gl-pd-14-04a s.[5] (-6.70); gl-pd-14-04a s.[9] (-7.56) |
| aday:A126 Strickland kitabına göre deri ceket nasıl dikilir? | model_cevap (✖ Doğrulanamadı): Deri ceket dikilirken, sırasıyla şunları yapmalısınız:
1. Ceket çelişine zıp ekleyerek zıp | model_cevap (⚠ Kısmen doğrulandı): Deri ceket derinliklerini açarak, omuz dartının kesilmiş kenarını altına indirirken, kalan | gl-pd-14-04a s.[26] (-7.25); strickland-1956 s.[158] (-7.31); strickland-1956 s.[83] (-7.68) |
| aday:A127 S-7300A Bluetooth ya da Wi-Fi ile nasıl bağlanır? | netlestirme | model_bulunamadi | brother-s7300a s.[55] (-4.58); brother-s7300a s.[19, 20] (-7.86); brother-s7300a s.[33] (-9.97) |
| aday:A128 Pantolon kumaşının su geçirmezlik (hidrostatik basınç) değer | model_cevap (✖ Doğrulanamadı): Pantolon kumaşının su geçirmezlik (hidrostatik basınç) değeri, 4.4.2 belirtilen testlerde  | model_cevap (✖ Doğrulanamadı): Pantolon kumaşının su geçirmezlik (hidrostatik basınç) değeri, 4.4.2 bölümünde belirtilen  | gl-pd-07-14a s.[7] (-4.01); gl-pd-07-14a s.[13] (-6.71); gl-pd-07-14a s.[5] (-6.81) |
| aday:A129 Terzilik kitabına göre overlok makinesi nasıl ayarlanır? | model_cevap (✖ Doğrulanamadı): Overlok makinesini ayarlamak için, ceket açılışının (placket) alt kenarında (underlap edge | model_cevap (⚠ Kısmen doğrulandı): Overlok makinesini ayarlamak için, işe koyulacak parçanın işlenmesi işaretlenen iş çizgisi | strickland-1956 s.[117, 118] (-5.97); strickland-1956 s.[81] (-6.57); strickland-1956 s.[136] (-6.93) |
| aday:A130 Mr. Coffee makinesiyle espresso nasıl yapılır? | model_bulunamadi | model_bulunamadi | mrcoffee-2003 s.[8] (2.12); mrcoffee-2003 s.[17] (1.36); mrcoffee-2003 s.[11, 12] (0.43) |
