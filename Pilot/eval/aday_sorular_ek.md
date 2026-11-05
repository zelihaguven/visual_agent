> **Durum (2026-11-05, kullanıcı kararı):** B001, B035, B036, B037 çıkarıldı (JUKI'ye dokunuyor). C008'e `ocr` etiketi. Kalan 46 soru onaylandı (onaylayan: geliştirme ekibi) ve `eval/aday_sorular_ek.json` setine girdi (36 "bulunamadı", 10 "değer farklı" netleştirme). Aşağıdaki tablo taslak dökümüdür.

# Aday sorular ek seti (2026-11-05)

Değerlendirme setini büyütmek için model önerisi adaylar. **Hiçbiri onaylı değil** (`dogrulandi: false`); her satır kullanıcı onayı bekliyor. Model ya da bulut çağrısı yapılmadı. Kanıt, `data/chunks.jsonl` (juki dahil tüm korpus) ve PDF metin katmanında düzenli ifade araması (Granovsky'nin harf aralıklı metninde boşluksuz arama). juki-mo6800s'e dayanan soru yok. juki yalnız 'bulunamadı' kontrolünde arandı; B001, B035–B037'de tuzak olarak anılıyor.

- **B001–B040**: 40 'bulunamadı' adayı (1 komşu değer: 7, 2 başka üründe var: 8, 3 terim eşleşir: 6, 4 alan dışı tekstil: 7, 5 İngilizce: 6, 6 kural dışı kod: 6). Arama ifadesi ve en yakın parça JSON'da `nf_kontrol` ve `en_yakin_parcalar` alanlarında.
- **C001–C010**: 10 'değer farklı' netleştirme adayı (`netlestirme_sinifi: deger_farkli`). Soruda ürün yok, iki belgede değer farklı. Alıntılar parça metninden birebir (OCR hataları dahil).

Onay için: satırı kabul edin, düzeltin ya da eleyin. Kabul edilenler `aday_sorular.json`'a taşınırken `dogrulandi`, `onaylayan` ve `onay_tarihi` doldurulur.

## Bulunamadı adayları

| id | tür | soru | kanıt özeti |
|---|---|---|---|
| B001 | 1 komşu değer | S-7300A çalışırken gürültü seviyesi kaç dB? | A/B'de dB yok; yalnız juki'de 83 dB (tuzak) |
| B002 | 1 komşu değer | Ceket kumaşının gramajı (birim alan ağırlığı, oz/yd²) ne olmalı? | cekette oz/gsm yok; pantolonda yalnız cep kumaşı |
| B003 | 1 komşu değer | Pantolonun ana kumaşının yırtılma dayanımı en az kaç pound olmalı? | tear yalnız kusur listesinde; lb değerleri bağcık/kilit için |
| B004 | 1 komşu değer | Kahve makinesinin ısıtma plakası kaç derecede tutar? | ayarlanabilir plaka var, derece yok |
| B005 | 1 komşu değer | Bosch freze tablasının tabla üst yüzeyi kaç inç x kaç inç? | x ölçüleri yalnız vida; tabla ölçüsü yok |
| B006 | 1 komşu değer | S-7300A deniz seviyesinden en fazla kaç metre yükseklikte (rakımda) kullanılabilir? | sıcaklık/nem var, rakım yok |
| B007 | 1 komşu değer | Terzilik kitabına göre bir ceketin dikimi toplam kaç saat sürer? | yalnız ön hazırlık süreleri (6 sa, 1 sa) |
| B008 | 2 başka üründe var | Ceketin kemer köprüleri kaç adet ve kaç inç genişliğinde olmalı? | yalnız pantolonda (7 adet) |
| B009 | 2 başka üründe var | Ceketin kargo cebindeki lastikli bağcık (drawcord) kaç inç çapında olmalı? | yalnız pantolonda (1/8 inç) |
| B010 | 2 başka üründe var | Pantolonun kalem cebi kaç bölmeli ve kaç inç genişliğinde? | yalnız cekette (2 bölme) |
| B011 | 2 başka üründe var | Pantolondaki rütbe arması cırt bandı kaç inç olmalı? | yalnız cekette (2x2 inç) |
| B012 | 2 başka üründe var | S-7300A'da dijital baskı ayağı kaldırıcısının kaldırma yüksekliği nasıl ayarlanır? | yalnız S-7300B (-9 tipi) |
| B013 | 2 başka üründe var | S-7300A'da diz anahtarı (knee switch) nasıl bağlanır? | yalnız S-7300B |
| B014 | 2 başka üründe var | S-7300A'nın Premier tipinde iplik kesme ayarı nasıl yapılır? | Premier yalnız S-7300B'de |
| B015 | 2 başka üründe var | Alev almaz (FR) ceketin kumaşında kömürleşme (char) uzunluğu en fazla kaç inç olmalı? | yalnız pantolon cep kumaşında (4,5 inç) |
| B016 | 3 terim eşleşir | Ceket şartnamesine göre AATCC 135 yıkama testinde kumaşın çekmesi en fazla yüzde kaç olabilir? | AATCC 135 var, çekme % yok |
| B017 | 3 terim eşleşir | Pantolon şartnamesine göre ASTM D 3776 ile ölçülen ana (dış) kumaşın gramajı kaç olmalı? | D3776 yalnız lastik kordon; ana kumaş yok |
| B018 | 3 terim eşleşir | Ceket ana kumaşının ASTM D 5034 (grab) kopma mukavemeti en az kaç pound olmalı? | D5034 düğme testi için; lb yalnız fermuar |
| B019 | 3 terim eşleşir | S-7300A'da masuraya kaç metre iplik sarılabilir? | yalnız %80 kuralı; sayaç 0,1–99,9 m tuzak |
| B020 | 3 terim eşleşir | Bosch freze tablasının vakum portuna bağlanacak süpürgenin emiş gücü en az kaç watt olmalı? | port var (2-1/2″), emiş gücü yok |
| B021 | 3 terim eşleşir | Kahve makinesindeki su filtresi diski kaç mikron gözenekli? | karbon, %97 klor; mikron yok |
| B022 | 4 alan dışı tekstil | Yuvarlak örme makinesinde iğneler sık kırılıyorsa ne yapılmalı? | örme makinesi yok |
| B023 | 4 alan dışı tekstil | Granovsky kitabına göre jakar makinesinde kanca ve platin ayarı nasıl yapılır? | kitap 'jakar ele alınmıyor' diyor |
| B024 | 4 alan dışı tekstil | Jet boyama makinesinde kumaş düğümlenmesi nasıl önlenir? | boyama makinesi yok |
| B025 | 4 alan dışı tekstil | Ram (germe-kurutma) makinesinde iğneli zincir raylarının genişliği nasıl ayarlanır? | ram/stenter yok |
| B026 | 4 alan dışı tekstil | Tafting (tufting) halı makinesinde hav yüksekliği nasıl ayarlanır? | tufting yok; 'tufts' fırça kılı |
| B027 | 4 alan dışı tekstil | Yalancı büküm (false-twist) tekstüre makinesinde kıvrım (crimp) nasıl ayarlanır? | tekstüre makinesi yok |
| B028 | 4 alan dışı tekstil | İğneleme (needle-punch) nonwoven makinesinde iğne tahtası nasıl değiştirilir? | hiç geçmiyor |
| B029 | 5 İngilizce | How many minutes does it take to brew a full 12-cup pot on the Mr. Coffee coffeemaker? | yalnız temizleme ve zamanlayıcı süreleri |
| B030 | 5 İngilizce | How much does a pack of replacement water filter disks cost for the coffeemaker? | nereden alınır var, fiyat yok |
| B031 | 5 İngilizce | What IP protection rating does the S-7300A control box have? | IP sınıfı yok |
| B032 | 5 İngilizce | What router speed in RPM should be used for large-diameter bits on the Bosch router table? | yalnız sembol tablosu |
| B033 | 5 İngilizce | What is the shelf life of the permethrin-treated combat coat before it is issued? | yalnız GC numunesi 3 ay |
| B034 | 5 İngilizce | What torque should the router mounting plate screws be tightened to on the Bosch router table? | yalnız sembol tablosu |
| B035 | 6 kural dışı kod | S-7300A'da E07 hatası ne demek? | yalnız juki'de (kapsam dışı) |
| B036 | 6 kural dışı kod | S-7300B ekranında E14 çıktı, ne yapmalıyım? | yalnız juki'de (kapsam dışı) |
| B037 | 6 kural dışı kod | S-7300A'da P54 parametresi neyi ayarlar? | yalnız juki'de (kapsam dışı) |
| B038 | 6 kural dışı kod | S-7300A ekranında 'Err-4' yazıyor, ne anlama geliyor? | biçim ve kod yok |
| B039 | 6 kural dışı kod | S-7300B'de F12 hatası ne demek? | F kodu yok |
| B040 | 6 kural dışı kod | S-7300A'da E-4096 hata kodu çıktı, sebebi ne? | 4 haneli kod yok |

## Netleştirme adayları (değer farklı)

| id | soru | değerler | kanıt (birebir) | not |
|---|---|---|---|---|
| C001 | Diz kaldırıcıyla baskı ayağı en fazla kaç mm kalkar? | S-7300A: 16 mm (s.12) · S-7300B: 13 mm (s.12) | `brother-s7300a-00035`: "Presser foot height \| Lifting lever \| Knee lifter \| 6mm \| 16mm" / `brother-s7300b-00032`: "Presser foot height \| Lifting lever \| Knee lifter \| 6mm \| 13mm" | kaldırma kolu iki modelde 6 mm; ayar metni de 16/13 mm (A -00058 s.17, B -00056 s.17) |
| C002 | Dikiş makinesi yaklaşık kaç kilogram ağırlığında? | S-7300A: 34,5 kg (s.4) · S-7300B: 39 kg (s.4) | `brother-s7300a-00006`: "The sewing machine weighs approximately 34.5 kg (76lb)." / `brother-s7300b-00006`: "The sewing machine weighs approximately 39 kg (86lb)." | juki de korpusta: kapsam S-7300 ailesi değilse olası ürün listesi daha geniş çıkabilir |
| C003 | Besleme dişlisi yörüngesi 1 seçiliyken 5,0 mm dikiş adımında dikiş hızı en fazla kaç olur? | S-7300A: 2000 sti/min (s.76) · S-7300B: -3: 2500, -5: 3000 sti/min (s.78) | `brother-s7300a-00354`: "4000sti/min / 3.0 3500sti/min / 4.0 2000sti/min / 5.0" / `brother-s7300b-00374`: "-3 specifications 5000sti/min / 2.0 4000sti/min / 3.0 3500sti/min / 4.0 2500sti/min / 5.0 -5 specifications 4500sti/min / 2.5 4000sti/min / 3.0 3500sti/min / 4.0 3000sti/min / 5.0" | tablo satırı; 'yörünge 2' satırında da aynı fark var (A -00355, B -00375) |
| C004 | Overlok (overedge) ya da ön kıvırma dikişlerinde inç başına kaç dikiş olmalı? | Ceket: 10 ± 2 (s.22–23) · Pantolon: 6–10 (s.19) | `gl-pd-14-04a-00178`: "Overedge or pre-hemming shall be 10 (± 2) stitches per inch." / `gl-pd-07-14a-00141`: "Overedge or pre-hemming shall be 6-10 stitches per inch." | Q11/Q12 aynı değerleri tek ürünlü soruyor; netleştirme sürümü yok |
| C005 | Permetrinli giysilerde 20 yıkamadan sonra ısırma koruması en az yüzde kaç olmalı? | Ceket: Type I ≥%90, Type II/III ≥%80 (s.7) · Pantolon: ≥%90 (s.6) | `gl-pd-14-04a-00057`: "After 20 launderings \| Type I, Class 2: >/= 90% \| Type II, Class 2: >/= 80% \| Type III, Class 2: >/= 80%" / `gl-pd-07-14a-00053`: "Condition: After 20 launderings \| % Bite Protection: >/=90%" | ceket Type I ile pantolon aynı (%90); Type II'de fark var (ceket %80, pantolon %90) |
| C006 | Permetrin işlemli giyside başlangıçta permetrin miktarı kaç mg/cm² aralığında olmalı? | Ceket: Type I 0,095–0,135; Type II 0,087–0,130; Type III 0,095–0,140 (s.6) · Pantolon: 0,087–0,130 (s.6) | `gl-pd-14-04a-00050`: "Initial \| Type I, Class 2 mg/cm 2: 0.095 \| Type I, Class 2 mg/cm 2: 0.135 \| Type II, Class 2 mg/cm 2: 0.087 \| Type II, Class 2 mg/cm 2: 0.130 \| Type III, Class 2 mg/cm 2: 0.095 \| Type III, Class 2 mg/cm 2: 0.140" / `gl-pd-07-14a-00049`: "Initial \| Min: mg/cm2: 0.087 \| Max: mg/cm2: 0.130" | ceket Type II = pantolon; Type I/III farklı. 20 yıkama sonrası alt sınır (0,025) iki belgede aynı (A029) |
| C007 | İliklerde ilik örgüsü (purl) giysinin hangi yüzünde olmalı? | Ceket: iç yüz (s.11) · Pantolon: dış yüz (s.11) | `gl-pd-14-04a-00103`: "The purling shall be on the inside surface." / `gl-pd-07-14a-00092`: "The purling shall be on the outside surface." | A140 ile aynı öğe (ilik) ama farklı özellik; kesim boyu 3/4–7/8 inç iki belgede aynı |
| C008 | Yan dikişlerde LSc-2 çift bindirme dikişinin aralığı (gauge) ne olmalı? | Ceket: 3/16–1/4 inç (s.23) · Pantolon: 3/16–9/32 inç (s.20) | `gl-pd-14-04a-00182`: "Gauge: 3/16 to 1/4-inch gauge (double lap seam)" / `gl-pd-07-14a-00145`: "Gage: 3116 to 9/32 inch gauge (double lap seam)" | pantolon metninde OCR: '3116' = 3/16 |
| C009 | Alt kenar (etek ya da paça ucu) baskısı kaç inç genişliğinde olmalı? | Ceket: 1/2–3/4 inç (çift kıvrım) (s.24) · Pantolon: 1 inç (s.20) | `gl-pd-14-04a-00197`: "Gauge: 1/2 to 3/4-inch wide hem, double turned clean finished" / `gl-pd-07-14a-00153`: "Gage: 1 inch wide hem" | dikiş tipi iki belgede EFb-1 / 301 |
| C010 | FR tanıtım işareti (FR identification marker) giysinin neresine dikilir? | Ceket: sol kol manşeti (s.25) · Pantolon: sol kargo cebi kapağı (s.20) | `gl-pd-14-04a-00207`: "FR identification marker to left sleeve cuff, visible from outside (Types II and III only)" / `gl-pd-07-14a-00151`: "FR identification marker to left cargo pocket flap (Type II trouser only)" | A004 ceket için tek ürünlü soruyor; netleştirme sürümü yok |

## Elenen adaylar

| aday | neden |
|---|---|
| S-7300A'nın ağırlığı (görevdeki örnek) | Korpusta var: 34.5 kg (brother-s7300a-00006); C002'ye netleştirme olarak alındı |
| Ceket kumaşının yıkama sıcaklığı (görevdeki örnek) | Bakım etiketinde var: 'Wash in cold water' (gl-pd-14-04a-00146, s.17) |
| Dokuma makinesinde atkı kopması (görevdeki örnek) | Granovsky atkı çatalını (weft fork) anlatıyor (granovsky-1986-00646, -00681): kısmi cevap olabilir |
| S-7300A çalışma sıcaklığı / bağıl nem | Var: 5–35 °C, %45–85 (brother-s7300a-00007) |
| Mr. Coffee garanti süresi / otomatik kapanma / kablo | Var: 1 yıl (-00145), 2 saat (-00044), kısa kablo ve ayarlanabilir uzunluk (-00018/-00019) |
| Mr. Coffee su haznesi kapasitesi | 12 fincan x 5 oz'dan hesaplanabilir (-00043, -00073) |
| Open-end (rotor) iplik makinesi | Granovsky'de bölüm var (granovsky-1986-00448) |
| S-7300A USB ile veri aktarımı | Var: 6-11 USB media (brother-s7300a-00023) |
| Pantolon cep kumaşı gramajı | Var: 5.04 ve 7.0–8.0 oz/sq yd (gl-pd-07-14a-00044/-00045); Q09 kapsamı |
| Strickland'a göre ütü sıcaklığı | Nitel cevap var: 'moderately warm iron, never a hot one' (strickland-1956-00118) |
| Cırt bant SPI (netleştirme) | Ceket 10 ± 2 = 8–12, pantolon 8–12: değer aynı |
| Düğme dikiş ipliği Tex (netleştirme) | Ceket ve pantolon 71–105: değer aynı |
| İplik kesme kamı boşluğu A 0,6–0,8 / B 0,5–1,0 mm (netleştirme) | Değer farklı ama A138 ile aynı ayar prosedürü; B'de Premier/diğer ayrımı belirsiz |
| Permetrin numune yıkama koşulları (netleştirme) | Pantolon ek D.2 '50 yıkama' diyor, Tablo IX demiyor: belge içi tutarsızlık |
| 50 yıkama sonrası ısırma koruması (netleştirme) | C005 ile aynı tablo; tekrar olmasın diye biri seçildi |
