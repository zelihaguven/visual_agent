# Manual Envanteri

> **Durum (2026-10-10):** Test seti **7 doküman, 611 sayfa**, hepsi `Pre/manuals/public/` klasöründe ve parse edildi (3 şartname/yöntem + 2 Brother makine kılavuzu + 2 alan dışı). Ölçülmüş envanter tablosu aşağıda. Gerçek (müşteri) dokümanlar için Q2, Q3, Q7 bekleniyor.
> **İlgili plan:** [req.md, Adım 0.2 ve 2.1](../req.md) · [pdf-isleme.md](pdf-isleme.md)

## Strateji

| Aşama | Veri | Amaç |
|-------|------|------|
| **1. Geliştirme / test** | İnternetten bulunan **açık erişimli** manueller (bu liste) | Sistemi gizlilik riski olmadan kurmak, ölçmek, iyileştirmek |
| **2. Geçiş** | Kendi (müşteri) manuellerimiz | Sistem test setinde hedef oranlara ulaşınca (bkz. req.md 6.3) gerçek veriye geçmek |

**Bu yaklaşımın faydaları:**
- Gizlilik kararı (Q1) beklenmeden çalışmaya başlanabilir. Bulut API'leri de test aşamasında rahatça denenebilir.
- Test seti herkesle paylaşılabilir, sonuçlar tekrarlanabilir.

**Dikkat:**
- Public set, gerçek manuellere **benzemeli**: tedarikçi/kalite manuali tarzı, dikiş/ölçü değerleri, tablolar, şekiller, en az bir taranmış doküman. Yoksa test sonuçları gerçek veriye taşınmaz.
- Geçişte tekrar ölçüm şart. Gerçek veride çıkan farklar (format, dil, yapı) ayrıca not edilecek.
- Dokümanlar sadece **iç Ar-Ge testi** için kullanılacak, yeniden dağıtılmayacak.

## Seçim kriterleri

Set, gerçek manuellerde karşılaşacağımız durumların hepsini kapsamalı:

| Kriter | Neden |
|--------|-------|
| Birden fazla doküman / kaynak | Metadata filtresini test etmek |
| Benzer konular, farklı değerler | Yanlış kaynak riskini test etmek |
| Dijital PDF | Temel parsing |
| **Taranmış PDF** | OCR ihtiyacını test etmek |
| Tablo ağırlıklı sayfalar | Tablo ayrıştırma |
| Şekil / çizim ağırlıklı sayfalar | Şekil işleme, multimodal ihtiyacı |
| **Türkçe + İngilizce** | Diller arası arama, Türkçe stemming |
| Kodlar / standart numaraları | Hybrid search (BM25) testi |

## ✅ Seçilen test seti (2026-10-08)

| doc_id | Dosya | Kurum ("marka") | Ürün | Dil | Tür | Öne çıkan | Durum |
|--------|-------|-----------------|------|-----|-----|-----------|-------|
| `gl-pd-14-04a` | [GL-PD-14-04A_ACU-Coat.pdf](../../test-dokumanlari/GL-PD-14-04A_ACU-Coat.pdf) | US Army (GL-PD) | Ceket | EN | Dijital, ~56 sf. | SPI + tolerans, stitch/seam tablosu, ölçü tabloları | ✅ İndirildi |
| `gl-pd-07-14a` | [GL-PD-07-14A_Combat-Trousers.pdf](../../test-dokumanlari/GL-PD-07-14A_Combat-Trousers.pdf) | US Army (GL-PD) | Pantolon | EN | **Taranmış**, ~48 sf. | SPI, Table V (ASTM D6193), OCR testi | ✅ İndirildi |
| `brother-s7300a` | [Brother_S-7300A_Instruction.pdf](../../test-dokumanlari/Brother_S-7300A_Instruction.pdf) | Brother (üretici) | Düz dikiş makinesi | EN | Dijital, ~3.5 MB | Makine kılavuzu: ayar, **arıza giderme tablosu**, hata kodları, çizimli talimatlar | ✅ İndirildi |
| `brother-s7300b` | [Brother_S-7300B_Instruction_2025-04.pdf](../../test-dokumanlari/Brother_S-7300B_Instruction_2025-04.pdf) | Brother (üretici) | Düz dikiş makinesi | EN | Dijital, ~4.5 MB | S-7300A'nın yeni modeli → **model karışıklığı testi** | ✅ İndirildi |
| `strickland-1956` | [Strickland_A-Tailoring-Manual_1956.pdf](../../test-dokumanlari/Strickland_A-Tailoring-Manual_1956.pdf) | G. Strickland (Internet Archive) | Terzilik / dikim yöntemleri | EN | **Taranmış + OCR katmanlı**, 164 sf. (138'inde metin), 8.9 MB | **İki kolonlu sayfalar** (okuma sırası), çok sayıda çizim, **kesirli ölçülerde OCR hatası** ("½ inch" → "V2 inch", "⅛" → "Vb"), basılı ve PDF sayfa farkı (PDF s.128 = basılı s.114, numara sayfanın **üstünde**) | ✅ İndirildi (2026-10-09) |
| `mrcoffee-2003` | [MrCoffee_Coffeemaker_2003.pdf](../../test-dokumanlari/MrCoffee_Coffeemaker_2003.pdf) | Mr. Coffee / Sunbeam | Kahve makinesi | EN + ES | Dijital, 22 sf. | Makine kılavuzu: güvenlik uyarıları, temizlik, arıza giderme. **Kitapçık düzeni:** Bir PDF sayfasında iki basılı sayfa yan yana ("2" ve "43"), sayfa numarası eşlemesi için zor bir örnek. **Alan dışı doküman:** Dikim sorularında hiç gelmemeli | ✅ İndirildi (2026-10-09) |
| `bosch-ra1171` | [Bosch_RA1171_Operating-Safety_2005.pdf](../../test-dokumanlari/Bosch_RA1171_Operating-Safety_2005.pdf) | Bosch | Freze tezgâhı (elektrikli alet) | **EN / FR / ES** (bölümler arka arkaya: EN s.2-31, FR s.32-61, ES s.62+) | Dijital, 96 sf. | Makine kılavuzu: güvenlik, **parça listesi**, montaj çizimleri. **Aynı içerik üç dilde:** Dil filtresi (`lang`) ve "aynı bilgi farklı dilde" testi. **Alan dışı doküman** | ✅ İndirildi (2026-10-09) |

**Üç doküman türü var:** `product_standard` (şartnameler), `machine_manual` (Brother, Mr. Coffee, Bosch kılavuzları) ve `tailoring_guide` (Strickland: nasıl dikilir anlatan yöntem kitabı).

**Alan dışı dokümanlar neden sette?** Mr. Coffee ve Bosch dikimle ilgili değil, ama gerçek bir makine kılavuzunun yapısını taşıyorlar (güvenlik, arıza giderme, parça listesi). Ayrıca "yanlış doküman" testi sağlıyorlar: "Dikiş atlıyor" ya da "iplik gerginliği" sorularında kahve makinesi veya freze kılavuzundan cevap gelmemeli. Gelirse metadata filtresi veya arama kalitesinde sorun var demektir. Türler arası karışma ve sorgu yönlendirme bu setle test edilecek (bkz. rag-temelleri.md 1.7 → "Birden fazla doküman türü").

**Şartnameler hakkında:** GL-PD (*Purchase Description*) dokümanları ABD ordusunun kıyafet şartnameleridir. ABD hükümeti yayını oldukları için kamuya açıktır. Bir markanın tedarikçi manueline çok benzerler: dikiş sıklığı (SPI) ve toleranslar, dikiş/seam tipi tabloları, ölçü tabloları, teknik çizimler.

**Dokümanlardan doğrulanan örnek değerler** (arama sonuçlarından, parse edildikten sonra tekrar kontrol edilecek):
| Doküman | Örnek |
|---------|-------|
| GL-PD-14-04A (ceket) | "outside visible stitching 11 (± 1) SPI", "overedge 10 (± 2) SPI", "buttonholes 54 (± 2) SPI" |
| GL-PD-07-14A (pantolon) | "outside visible stitching 10-14 SPI", "buttonholes 52-56 SPI including tack" |

**Set neyi kapsıyor:**
- **Metin + tablo** (14-04A), **taranmış** (07-14A), **iki kolonlu taranmış kitap** (Strickland), **çizimli talimat** (Brother, Bosch). Farklı parsing zorlukları.
- **Aynı soru, farklı cevap:** Dış görünür dikiş SPI'ı → ceket 11 ± 1, pantolon 10–14.
- **Kodlar:** "301", "401", "LSc-2", "ASTM D6193" (şartnameler), hata kodları ve parça numaraları (Brother, Bosch).
- **Multimodal ihtiyacı:** Strickland'daki dikim çizimleri, Brother ve Bosch'taki montaj/parça çizimleri. Metin tabanlı RAG'in burada ne kadar yetersiz kaldığı değerlendirilecek (kaynak-gosterme.md 5. bölüm).
- Stitch Guide (ASTM D6193 / ISO 4915 dikiş tipi çizimleri) aday olarak değerlendirildi ama **sete eklenmedi** (2026-10-09).

**Eksik / sınırlar:**
- Türkçe doküman yok → diller arası test **Türkçe soru + İngilizce doküman** ile yapılacak.
- Aynı dokümanın iki versiyonu yok → versiyon filtresi testi şimdilik yapılamaz.
- Tüm şartnameler ABD ordusu formatında. Gerçek marka manuellerinin formatı farklı olabilir. Kendi verimize geçerken tekrar ölçüm şart.

## Genişletme: Makine kılavuzları (M1, M2 sete eklendi)

**Neden?** Sistem sadece dikiş standardı sorularına değil, ileride **makine kullanımı, ayarı, arıza tespiti ve tamiri** sorularına da cevap verebilmeli (örn. "Dikiş atlıyor, ne yapmalıyım?", "Üst iplik gerginliği nasıl ayarlanır?"). Makine kılavuzları ayrıca şartnamelerden farklı bir doküman türü olduğu için test setini çeşitlendirir.

| # | Doküman | Üretici | Dil | Tür | Neyi test eder | Durum |
|---|---------|---------|-----|-----|----------------|-------|
| M1 | **S-7300A Instruction Manual** (tek iğneli düz dikiş makinesi) | Brother (resmi site) | EN | Dijital PDF, ~3.5 MB | Kullanım ve ayar adımları, **arıza giderme tablosu** (belirti → sebep → çözüm), adım adım talimat + çizim, hata kodları | ✅ Doğrulama için indirildi |
| M2 | **S-7300B Instruction Manual** (Nisan 2025) | Brother (resmi site) | EN | Dijital PDF, ~4.5 MB | M1'in yeni modeli: **benzer doküman, farklı değerler** → model karışıklığı testi ("S-7300A'da" sorusuna S-7300B'den cevap gelmemeli) | ✅ Doğrulama için indirildi |
| M3 | Brother Parts Book (S-7300A) | Brother ([partsbook.brother.co.jp](https://partsbook.brother.co.jp/pub/machine/detail/en/12/274)) | EN | Web / PDF | **Patlatılmış montaj çizimleri + parça numaraları**: parça kodu araması (BM25), çizim + tablo birlikte | ⏳ Formatı kontrol edilecek |

**Bu dokümanlarla yeni test edilebilecekler:**
- **Arıza giderme tabloları:** "Belirti / Sebep / Çözüm" sütunlu tablolar. Tablo ayrıştırma ve "sorun → çözüm" sorularının testi.
- **Adım adım talimat + çizim:** Metin çizime atıf yapar ("Şekil 3'teki A vidasını gevşetin"). Cevapta sayfayı göstermenin en değerli olduğu durum.
- **Hata kodları ve parça numaraları:** "E-07 hatası", "parça no. 146391-001" → kelime araması (BM25) testi.
- **Model karışıklığı:** S-7300A ve S-7300B neredeyse aynı içerikte. Metadata filtresinin (`product_model`) gerekliliğini gösterir.
- **Uyarı/güvenlik bölümleri:** "Makineyi açmadan önce..." gibi kritik güvenlik bilgileri.

**Metadata'ya yeni alan ihtiyacı:** Makine kılavuzları için `doc_type = machine_manual`, `manufacturer`, `product_model` (örn. "S-7300A") alanları gerekecek (rag-temelleri.md 1.7'ye eklenecek).

**Türkçe makine dokümanı:** Uludağ Üniversitesi'nin "Sanayi Tipi Düz Dikiş Makinesi Bakım ve Kullanım Talimatı" (Türkçe, .docx) bulundu ama link şu an 404 veriyor. Resmi üretici kılavuzlarının Türkçe versiyonu bulunamadı. Türkiye distribütörlerinin sitelerinde ayrıca aranabilir.

## Envanter tablosu (ölçülmüş, 2026-10-10)

Kaynak: pilotta Docling parse sonuçları (`Pilot/data/parsed/`) ve PDF metin katmanı. Sayılar otomatik ölçüldü.

| doc_id | Kurum / ürün | Versiyon | Sayfa | MB | Dil | Tür | Metin / tablo / şekil | Tablo satırı | Parça | Yedek yola geçen sayfa |
|--------|--------------|----------|-------|----|-----|-----|-----------------------|--------------|-------|------------------------|
| gl-pd-14-04a | US Army (GL-PD), Ceket | A (GL/PD 14-04A) | 56 | 2,2 | EN | Şartname, dijital | Metin + 41 tablo, 8 şekil | 385 | 529 | 0 |
| gl-pd-07-14a | US Army (GL-PD), Pantolon | A (GL/PD 07-14A) | 48 | 1,3 | EN | Şartname, **taranmış** (PDF'te OCR katmanı) | Metin + 27 tablo, 7 şekil | 169 | 303 | 2 |
| brother-s7300a | Brother, S-7300A | Talimat kitabı | 108 | 3,5 | EN | Makine kılavuzu, dijital | 50 tablo, **337 şekil** | 277 | 501 | 6 |
| brother-s7300b | Brother, S-7300B | 2025-04 | 117 | 4,5 | EN | Makine kılavuzu, dijital | 59 tablo, **330 şekil** | 308 | 537 | 8 |
| strickland-1956 | G. Strickland | 1956 | 164 | 9,3 | EN | Yöntem kitabı, **taranmış**, iki kolon | Tablo yok, çizim ağırlıklı | 0 | 307 | **121** |
| mrcoffee-2003 | Mr. Coffee | 2003 | 22 | 1,3 | EN + ES | Ev aleti kılavuzu (alan dışı), dijital | 7 tablo, 77 şekil | 41 | 151 | 0 |
| bosch-ra1171 | Bosch, RA1171 | 2005 | 96 | 3,9 | EN / FR / ES (s.2–31, 32–61, 62+) | Alet kılavuzu (alan dışı), dijital | 15 tablo, 281 şekil | 276 | 593 | 6 |
| **Toplam** | | | **611** | **26** | | | | **1455** | **2921** | **143** |

## Format değerlendirmesi

| Doküman | Zorluk | Neden | Pilotta ne gördük |
|---------|--------|-------|-------------------|
| gl-pd-14-04a | 🟢 Düşük | Temiz dijital metin, düzenli tablolar | SPI ve tolerans doğru çıkıyor, paragraf sayfa 22–23'e yayılıyor ve birleşiyor |
| gl-pd-07-14a | 🟡 Orta | Taranmış, PDF'in kendi OCR katmanı küçük hatalar içeriyor ("confOlm", "protmding") | Aranabilir ama bozuk sözcükler eşleşmeyi düşürür. Docling'in kendi OCR'ı bir satırı kaybetmişti (Faz 1) |
| brother-s7300a / b | 🟡 Orta | Çok çizim, arıza tabloları, basılı ≠ PDF sayfa (s.90 = PDF s.101), A/B model karışıklığı | Tablo satırları iyi çıkıyor. A/B ayrımı sorgu analiziyle çözülüyor. Çizimler aranamıyor |
| strickland-1956 | 🔴 Yüksek | Tam sayfa tarama görseli, iki kolon, kesirli ölçülerde OCR hatası (½ → V2), basılı ≠ PDF sayfa | Docling metnin %94'ünü atladı, PDF metin katmanı yedeği ile 121 sayfa kurtarıldı |
| mrcoffee-2003 | 🟢 Düşük | Kısa. Kitapçık düzeni: bir PDF sayfasında iki basılı sayfa | Alan dışı kontrolü için kullanışlı. Basılı sayfa etiketi güvenilmez |
| bosch-ra1171 | 🟡 Orta | Üç dil arka arkaya, çok parça çizimi | Dil etiketi sayfa aralığından atanıyor. Parse en yavaşı (578 sn, MPS) |

### Sonuçlar (gerçek dokümanlara aktarılacaklar)

- **Taranmış PDF'te metin katmanı olabilir ama Docling bunu görmeyebilir**: her sayfada Docling kapsamı PDF katmanıyla karşılaştırılmalı (gerçek sistemde ingestion'a girmeli).
- **Şekil ağırlıklı sayfalar** (Brother, Bosch, Mr. Coffee: 77–337 şekil) metin aramasıyla bulunamaz: VLM açıklaması planlanmalı.
- **Basılı ↔ PDF sayfa numarası** her dokümanda farklı davranıyor: ayrı alan olarak tutulmalı.
- Gerçek dokümanlarda aynı sorular (taranmış oranı, görsel türleri, klasör/versiyon düzeni) bu tabloyu yeniden doldurmak için gerekli: [sorulacaklar.md](sorulacaklar.md) Q3, Q7, R3.

## Kaynaklar

- [GL-PD-14-04A: Army Combat Uniform Coat (PDF)](https://imlive.s3.amazonaws.com/Federal%20Government/ID339162058590411927735464482663559176426/Spec%20GL-PD-14-04A.pdf)
- [GL-PD-07-14A: Combat Trousers (PDF)](https://poseidonsciences.com/wp-content/uploads/2021/07/Military-specs-for-wash-resistance-of-repellent-clothing-GL-PD-07-14A.pdf)
- [Brother Industrial: Manual Download sayfası](https://industrialsewingmachine.global.brother/manual/index) · [S-7300A Instruction Manual (PDF)](https://industrialsewingmachine.global.brother/-/media/ap2/ism/pdf/manual-download/s7300a_in.pdf?rev=-1) · [S-7300B Instruction Manual (PDF)](https://industrialsewingmachine.global.brother/-/media/ap2/ism/pdf/manual-download/s-7300b_inst_en_2025_04.pdf?rev=351bbec5bbb44f449712a8353f5476e5)
- [Strickland, A Tailoring Manual, 1956 (Internet Archive, PDF)](https://dn790007.ca.archive.org/0/items/stricklandatailoringmanual1956/stricklandatailoringmanual1956.pdf)
- [Mr. Coffee kahve makinesi kılavuzu (Internet Archive, PDF)](https://dn790009.ca.archive.org/0/items/manualsonline-id-e6076373-d174-0e44-6110-226a0874155d/e6076373-d174-0e44-6110-226a0874155d.pdf)
- [Bosch RA1171 Operating/Safety Instructions (Internet Archive, PDF)](https://dn760106.eu.archive.org/0/items/manualsonline-id-48820843-e5f4-4818-a078-e1628ccd7415/48820843-e5f4-4818-a078-e1628ccd7415.pdf)
