# Pilot ölçüm sonucu

Soru sayısı: 10 · Model: kurulumdaki `PILOT_LLM_MODEL` · Arama: hibrit + reranker (CPU)

| # | Tür | Soru | Doğru | Doğrulama | Süre | Not |
|---|-----|------|-------|-----------|------|-----|
| Q01 | değer | Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı? | ✔ | ⚠ Kısmen doğrulandı | 25 sn | Cevapta geçerli [n] atfı yok |
| Q02 | değer | Pantolonun dış dikişlerinde SPI kaç olmalı? | ✔ | ⚠ Kısmen doğrulandı | 10 sn | Cevapta geçerli [n] atfı yok |
| Q03 | değer | Ceketteki düğme iliklerinde dikiş sayısı kaç olmalı? | ✖ | ⚠ Kısmen doğrulandı | 8 sn | Cevapta geçerli [n] atfı yok |
| Q04 | arıza | S-7300A'da üst iplik gergin değil, ne yapmalıyım? | ✔ | ⚠ Kısmen doğrulandı | 13 sn | Cevapta geçerli [n] atfı yok |
| Q05 | tuzak | S-7300B'de dikiş atlıyor, ne yapmalıyım? | ✔ | ⚠ Kısmen doğrulandı | 18 sn | Cevapta geçerli [n] atfı yok |
| Q06 | alan dışı | Kahve makinesi nasıl temizlenir? | ✖ | ✖ Doğrulanamadı | 22 sn | Model çıktısı bozuk (JSON tamamlanmadı) |
| Q07 | belirsiz | Dış görünür dikişlerde SPI kaç olmalı? | ✖ | ✖ Doğrulanamadı | 17 sn | Alıntı kaynakta birebir bulunamadı: 'For China: 4300 (sti/min) For Japan and General Export: 4000 sti/min F';  |
| Q08 | cevapsız | Nike ceketlerinde yaka dikişi kaç mm olmalı? | ✔ | ✖ Kaynaklarda bulunamadı | 11 sn |  |
| Q09 | cevapsız | Pantolonun cep astarı hangi kumaştan yapılmalı ve gramajı kaç olmalı? | ✖ | ⚠ Kısmen doğrulandı | 12 sn | Cevapta geçerli [n] atfı yok |
| Q10 | cevapsız | Uçak motoru yağı kaç derecede değiştirilir? | ✖ | ✖ Doğrulanamadı | 9 sn | Alıntı kaynakta birebir bulunamadı: 'No.: 102 / Setting range: -10 - 10 (Degrees) / Initial value: 0 (Degre';  |

**Doğru: 5/10** · Ortalama süre: 14.5 sn
