# Adım 0: Hazırlık (araştırmaya başlamadan önce)

> **Tarih:** 2026-10-10 · **Plan:** [req.md → Adım 0](../req.md) · **Kaynak cevaplar:** [cevaplar.md](../cevaplar.md)
> **Çıktı (req.md'de vaat edilen):** cevaplar, örnek doküman listesi, soru seti taslağı

---

## 1. Adım 0 maddeleri: durum

| # | Madde | Durum | Cevap / sonuç |
|---|-------|-------|---------------|
| **0.1** | Manualler bulut API'ye gönderilebilir mi? | 🟡 Kısmen | **Karar:** Sözleşme sessizse müşteriden izin istenmeden geliştirilecek (müşteri bunu bilmiyor). **Açık:** Sözleşme bulutu *yasaklıyor mu* (7.1, Q1). Test aşaması public veri olduğu için etkilenmiyor |
| **0.2** | Örnek manuel seti | ✅ | 7 açık erişimli PDF, 611 sayfa, 5 kurum. Liste: aşağıda ve [manual-envanteri.md](manual-envanteri.md) |
| **0.3** | Dil | ✅ | Manueller çoğunlukla **İngilizce** (çevrilerek de gelebilir). Sorular **hep Türkçe**, İngilizce soru da olabilir → **model çift yönlü çalışmalı**. Terimlerde Türkçe karşılık tercih edilir |
| **0.4** | 10–20 örnek soru | ✅ 10 soru | AI yazdı, sayfaları PDF'ten doğrulandı: `Pilot/eval/questions.json`. Uzman kontrolü ve 50–100 soru **açık** (aşağıda) |
| **0.5** | Donanım (GPU) | 🟡 Kısmen | Geliştirme makinesi: **Apple M4 Pro, 24 GB** (NVIDIA yok). Pilotta 7B model sığdı, 30B sığmadı. Kurumsal GPU (Q5) ve bütçe **açık** |
| **0.6** | Geliştirme ortamı | ✅ | Python 3.12 (uv), Docling, Qdrant, Ollama. Kurulum: `Pilot/setup.sh` |

---

## 2. Örnek doküman listesi (0.2)

| doc_id | Kurum | Ürün | Dil | Tür | Sayfa |
|--------|-------|------|-----|-----|-------|
| gl-pd-14-04a | US Army (GL-PD) | Ceket | EN | Şartname, dijital | 56 |
| gl-pd-07-14a | US Army (GL-PD) | Pantolon | EN | Şartname, taranmış | 48 |
| brother-s7300a | Brother | S-7300A düz dikiş makinesi | EN | Makine kılavuzu | 108 |
| brother-s7300b | Brother | S-7300B düz dikiş makinesi | EN | Makine kılavuzu (model karışıklığı testi) | 117 |
| strickland-1956 | G. Strickland | Terzilik kitabı | EN | Yöntem kitabı, taranmış, iki kolon | 164 |
| mrcoffee-2003 | Mr. Coffee | Kahve makinesi | EN+ES | Alan dışı doküman | 22 |
| bosch-ra1171 | Bosch | Freze tezgâhı | EN/FR/ES | Alan dışı doküman | 96 |

> Envanterde "8 doküman" yazıyordu, gerçekte **7** doküman var ve hepsi klasörde. Brother parça kitabı (M3) aday listesindeydi, formatı kontrol edilmediği için sete eklenmedi.

---

## 3. Test soru seti taslağı (0.4)

10 soru, 6 tür. Kaynak: `Pilot/eval/questions.json`. "Beklenen sayfa" PDF sayfasıdır (basılı numara farklı olabilir).

| # | Tür | Soru | Beklenen kaynak | Beklenen sonuç |
|---|-----|------|-----------------|----------------|
| Q01 | değer | Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı? | gl-pd-14-04a s.22 | 11 (± 1) |
| Q02 | değer | Pantolonun dış dikişlerinde SPI kaç olmalı? | gl-pd-07-14a s.19 | 10-14 |
| Q03 | değer | Ceketteki düğme iliklerinde dikiş sayısı kaç olmalı? | gl-pd-14-04a s.22 | 54 (± 2) |
| Q04 | arıza | S-7300A'da üst iplik gergin değil, ne yapmalıyım? | brother-s7300a s.101 (basılı 90) | Arıza tablosu satırı |
| Q05 | tuzak | S-7300B'de dikiş atlıyor, ne yapmalıyım? | brother-s7300b s.82 / s.109 | S-7300A kullanılmamalı |
| Q06 | alan dışı | Kahve makinesi nasıl temizlenir? | mrcoffee-2003 s.16–17 | Temizleme adımları |
| Q07 | belirsiz | Dış görünür dikişlerde SPI kaç olmalı? (ürün yok) | gl-pd-14-04a s.22, gl-pd-07-14a s.19 | Netleştirme veya ürün başına değer |
| Q08 | cevapsız | Nike ceketlerinde yaka dikişi kaç mm olmalı? | — | "Bulunamadı" |
| Q09 | cevapsız | Pantolonun cep astarı hangi kumaştan yapılmalı ve gramajı kaç olmalı? | — | "Bulunamadı" (**elle kontrol gerekir**) |
| Q10 | cevapsız | Uçak motoru yağı kaç derecede değiştirilir? | — | "Bulunamadı" |

### Eksik olan (açık)

- `llm-degerlendirme.md` hedefi **50–100 soru, 8 tür**. Eksik türler: **prosedür**, **çapraz dil (İngilizce soru)**, **görsel** (çizime dayanan), **yetki** (marka dışı doküman).
- Sorular **AI tarafından yazıldı**: karar gereği bir uzman kontrol edecek. Kim olduğu açık ([sorulacaklar.md A5](sorulacaklar.md)).
- Gerçek kullanıcı soruları (atölyede gerçekte sorulanlar) toplanmadı.

---

## 4. Sonuç

Adım 0 çıktıları hazır. Gerçek veriye geçmeden önce kalanlar: Q1/7.1 (sözleşme), Q5 (GPU), uzman kontrollü ve genişletilmiş test seti.
