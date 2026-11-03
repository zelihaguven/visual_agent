# Netleştirme: ilk 3 sonuç ile doküman düzeyinde skor

Yeni varsayılan yol (rerank yok). Yalnız kaynak belirtmeyen sorular. Doküman skoru: ilk 20 adayın RRF skorları dokümana göre toplanır; en iyi doküman ile onunla yer değiştirebilen (iki ürün şartnamesi ya da aynı makine ailesi) en iyi rakibin oranı ≥ eşik ise sorulur. **Eşik seçilmedi**: aday sorular onaysız, eşik onaylı setle seçilecek.

## Onaylı setler (4 soru; 2 netleştirme beklenen)

| Yöntem | doğru netleştirme | yanlış negatif | yanlış pozitif | yanlış pozitif (alakasız) | doğru geçiş |
|---|---|---|---|---|---|
| ilk 3 sonuç (bugünkü) | 2 | 0 | 0 | 0 | 2 |
| doküman skoru, oran ≥ 0.4 | 1 | 1 | 0 | 0 | 2 |
| doküman skoru, oran ≥ 0.5 | 1 | 1 | 0 | 0 | 2 |
| doküman skoru, oran ≥ 0.6 | 1 | 1 | 0 | 0 | 2 |
| doküman skoru, oran ≥ 0.7 | 0 | 2 | 0 | 0 | 2 |
| doküman skoru, oran ≥ 0.8 | 0 | 2 | 0 | 0 | 2 |

## Aday taslak (onaysız, yalnız dağılım) (36 soru; 15 netleştirme beklenen)

| Yöntem | doğru netleştirme | yanlış negatif | yanlış pozitif | yanlış pozitif (alakasız) | doğru geçiş |
|---|---|---|---|---|---|
| ilk 3 sonuç (bugünkü) | 10 | 5 | 0 | 0 | 21 |
| doküman skoru, oran ≥ 0.4 | 7 | 8 | 2 | 0 | 19 |
| doküman skoru, oran ≥ 0.5 | 7 | 8 | 2 | 0 | 19 |
| doküman skoru, oran ≥ 0.6 | 7 | 8 | 2 | 0 | 19 |
| doküman skoru, oran ≥ 0.7 | 7 | 8 | 2 | 0 | 19 |
| doküman skoru, oran ≥ 0.8 | 6 | 9 | 2 | 0 | 19 |

## Oran dağılımı (2. doküman / 1. doküman; rakip yoksa 0)

| Soru | netleştirme bekleniyor | en iyi doküman | rakip | oran | ilk 3 sonuç |
|---|---|---|---|---|---|
| aday:A134 Alt iplik sayacı nasıl azalıyor? | evet | brother-s7300b | brother-s7300a | 0.98 | dogru_netlestirme |
| aday:A137 Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne | evet | brother-s7300b | brother-s7300a | 0.98 | dogru_netlestirme |
| aday:A133 İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı | evet | brother-s7300a | brother-s7300b | 0.96 | dogru_netlestirme |
| aday:A138 İplik kesme kamı ayarında iğne mili kaç mm kaldırılır? | evet | brother-s7300b | brother-s7300a | 0.92 | dogru_netlestirme |
| aday:A136 Topraklama vidası hangi torkla sıkılır? | evet | brother-s7300a | brother-s7300b | 0.90 | dogru_netlestirme |
| aday:A139 Makine kafası dik konuma nasıl getirilir? | evet | brother-s7300a | brother-s7300b | 0.90 | dogru_netlestirme |
| aday:A135 Aydınlatma LED'i nasıl açılıp kapatılır? | evet | brother-s7300a | brother-s7300b | 0.75 | yanlis_negatif |
| questions:Q07 Dış görünür dikişlerde SPI kaç olmalı? | evet | gl-pd-14-04a | gl-pd-07-14a | 0.68 | dogru_netlestirme |
| aday:A142 Beden etiketi nereye dikilir? | evet | gl-pd-14-04a | gl-pd-07-14a | 0.31 | dogru_netlestirme |
| questions_ek:Q30 E050 hatası ne demek? | evet | bosch-ra1171 | – | 0.00 | dogru_netlestirme |
| aday:A131 E050 ne demek? | evet | bosch-ra1171 | – | 0.00 | dogru_netlestirme |
| aday:A132 Dikişte ilmek oluşuyor, ne yapmalıyım? | evet | bosch-ra1171 | – | 0.00 | yanlis_negatif |
| aday:A140 İliklerde inç başına kaç dikiş olmalı? | evet | strickland-1956 | – | 0.00 | dogru_netlestirme |
| aday:A141 Cırt bant kenardan ne kadar içeriden dikilir? | evet | strickland-1956 | – | 0.00 | yanlis_negatif |
| aday:A143 Isırma testinde kollar böcek kafesinde kaç dakika tutul | evet | mrcoffee-2003 | – | 0.00 | dogru_netlestirme |
| aday:A144 Permetrin geri kazanımı en az yüzde kaç olmalı? | evet | bosch-ra1171 | – | 0.00 | yanlis_negatif |
| aday:A145 Cep kapağı punterizi kaç dikişli olur? | evet | gl-pd-14-04a | – | 0.00 | yanlis_negatif |
| aday:A079 Kalın kumaşlarda makine dikiş boyu nasıl seçilir? | hayır | brother-s7300a | brother-s7300b | 0.87 | dogru_gecis |
| aday:A084 Ok başı punteriz (arrowhead) nasıl yapılır? | hayır | brother-s7300a | brother-s7300b | 0.81 | dogru_gecis |
| questions:Q10 Uçak motoru yağı kaç derecede değiştirilir? | bulunamadı | granovsky-1986 | – | 0.00 | dogru_gecis |
| sekil_sorular:N3 Dişli çark türleri nelerdir? | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A080 Fransız etek ucu (French hem) nasıl yapılır? | hayır | strickland-1956 | – | 0.00 | dogru_gecis |
| aday:A081 Uzun kruvaze paltoda düğmelenmeyen alt kat nasıl sabitl | hayır | strickland-1956 | – | 0.00 | dogru_gecis |
| aday:A082 Klapede pad dikişine kırım çizgisinin ne kadar gerisind | hayır | strickland-1956 | – | 0.00 | dogru_gecis |
| aday:A083 Gömme cepler neden tela ile desteklenir? | hayır | strickland-1956 | – | 0.00 | dogru_gecis |
| aday:A085 İlik aralıklarını doğru işaretlemek için ne yapılır? | hayır | strickland-1956 | – | 0.00 | dogru_gecis |
| aday:A087 Bengalin kumaş hangi giysiler için uygundur? | hayır | strickland-1956 | – | 0.00 | dogru_gecis |
| aday:A088 Parçaları yıkamak için sabun çözeltisinde litre başına  | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A089 Kalın cidarlı dökme demir parçaları kaynatırken çelik p | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A090 Ring iplik makinesinde kondansatörün toplam stroku kaç  | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A091 Birinci tip çözgü makinesinin tamburunda koni açısı han | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A092 Dokuma tezgâhında orta onarım ne sıklıkla yapılır ve ka | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A093 Mekik kutusunda mekik yokken çözgü koruyucu uçları pedl | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A094 Topuk konisinin elektrik kıvılcımıyla doldurulmasında k | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A096 Tekstil makinesi parçalarında bakır kaplama ne için kul | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A097 Yağ damperi ayar düzeneğindeki lamba kaç voltluk? | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A102 Cam sürahideki beyaz kireç lekeleri nasıl çıkarılır? | hayır | granovsky-1986 | – | 0.00 | dogru_gecis |
| aday:A103 Sürahi ısıtma plakasından 30 saniyeden uzun alınırsa ne | hayır | bosch-ra1171 | – | 0.00 | dogru_gecis |
| aday:A105 Yedek su filtresi diskleri nereden alınır? | hayır | mrcoffee-2003 | – | 0.00 | dogru_gecis |
| aday:A113 Parça listesinde 38 numaralı Allen başlı bağlantı vidas | hayır | bosch-ra1171 | – | 0.00 | dogru_gecis |
