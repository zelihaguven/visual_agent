# Pilot ölçüm sonucu

Soru sayısı: 18 · Model: kurulumdaki `PILOT_LLM_MODEL` · Arama: hibrit + reranker (CPU)

| # | Tür | Soru | Doğru | Doğrulama | Süre | Not |
|---|-----|------|-------|-----------|------|-----|
| Q01 | değer | Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı? | ✔ | ⚠ Kısmen doğrulandı | 143 sn | Cevapta geçerli [n] atfı yok |
| Q02 | değer | Pantolonun dış dikişlerinde SPI kaç olmalı? | ✔ | ⚠ Kısmen doğrulandı | 131 sn | Cevapta geçerli [n] atfı yok |
| Q03 | değer | Ceketteki düğme iliklerinde dikiş sayısı kaç olmalı? | ✖ | ⚠ Kısmen doğrulandı | 139 sn | Cevapta geçerli [n] atfı yok |
| Q04 | arıza | S-7300A'da üst iplik gergin değil, ne yapmalıyım? | ✖ | ✖ Doğrulanamadı | 218 sn | Alıntı kaynakta birebir bulunamadı: '・Is the upper thread tension too weak? Is the lower thread tension too';  |
| Q05 | tuzak | S-7300B'de dikiş atlıyor, ne yapmalıyım? | ✖ | ✖ Doğrulanamadı | 420 sn | Cevapta geçerli [n] atfı yok; Model cevaba başka dilde metin karıştırdı (高空...): cevap güvenilmez |
| Q06 | alan dışı | Kahve makinesi nasıl temizlenir? | ✖ | ✖ Doğrulanamadı | 281 sn | Cevapta geçerli [n] atfı yok; Alıntıda olmayan sayı(lar): ['2', '5', '6', '7']; Model cevaba başka dilde metin |
| Q07 | belirsiz | Dış görünür dikişlerde SPI kaç olmalı? | ✔ | ❓ Netleştirme gerekli | 46 sn |  |
| Q08 | cevapsız | Nike ceketlerinde yaka dikişi kaç mm olmalı? | ✔ | ✖ Kaynaklarda bulunamadı | 0 sn |  |
| Q09 | cevapsız | Pantolonun cep astarı hangi kumaştan yapılmalı ve gramajı kaç olmalı? | ✖ | ⚠ Kısmen doğrulandı | 214 sn | Cevapta geçerli [n] atfı yok |
| Q10 | cevapsız | Uçak motoru yağı kaç derecede değiştirilir? | ✖ | ❓ Netleştirme gerekli | 27 sn |  |
| Q11 | değer | Ceketin overlok (overedge) dikişlerinde inç başına kaç dikiş olmalı? | ✔ | ⚠ Kısmen doğrulandı | 119 sn | Cevapta geçerli [n] atfı yok; Sesli metinde tolerans düşmüş: kaynak '10 (± 2)', seste ± 2 yok (sesli metin doğ |
| Q12 | tuzak | Pantolonun overlok dikişlerinde SPI kaç olmalı? | ✔ | ⚠ Kısmen doğrulandı | 149 sn | Cevapta geçerli [n] atfı yok |
| Q13 | değer | Ceketteki kuşgözü (eyelet) dikişinde en az kaç üst üste dikiş olmalı? | ✖ | ⚠ Kısmen doğrulandı | 152 sn | Cevapta geçerli [n] atfı yok |
| Q14 | kod | S-7300A'da E050 hatası ne anlama geliyor, ne yapmalıyım? | ✖ | ✖ Doğrulanamadı | 107 sn | Cevapta geçerli [n] atfı yok; Alıntıda olmayan sayı(lar): ['1', '2', '3'] |
| Q15 | kod | S-7300A makinesinde hangi iğne tipi kullanılır? | ✖ | ⚠ Kısmen doğrulandı | 70 sn | Cevapta geçerli [n] atfı yok |
| Q16 | EN soru | How many stitches per inch are required for buttonholes on the coat? | ✔ | ⚠ Kısmen doğrulandı | 160 sn | Cevapta geçerli [n] atfı yok; Sesli metinde tolerans düşmüş: kaynak '54 (± 2)', seste ± 2 yok (sesli metin doğ |
| Q17 | belirsiz | S-7300'ün maksimum dikiş hızı nedir? | ✔ | ❓ Netleştirme gerekli | 0 sn |  |
| Q18 | cevapsız | Nike tişörtlerinde yaka ribanası kaç cm olmalı? | ✔ | ✖ Kaynaklarda bulunamadı | 0 sn |  |

**Doğru: 9/18** · Ortalama süre: 132.0 sn
