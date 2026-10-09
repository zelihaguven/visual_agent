# Manual Envanteri

> **Durum:** Test seti: 5 doküman (3 şartname/referans + 2 makine kılavuzu). 4'ü `Pre/manuals/public/` klasöründe, 
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
| `gl-pd-14-04a` | [GL-PD-14-04A_ACU-Coat.pdf](../manuals/public/GL-PD-14-04A_ACU-Coat.pdf) | US Army (GL-PD) | Ceket | EN | Dijital, ~56 sf. | SPI + tolerans, stitch/seam tablosu, ölçü tabloları | ✅ İndirildi |
| `gl-pd-07-14a` | [GL-PD-07-14A_Combat-Trousers.pdf](../manuals/public/GL-PD-07-14A_Combat-Trousers.pdf) | US Army (GL-PD) | Pantolon | EN | **Taranmış**, ~48 sf. | SPI, Table V (ASTM D6193), OCR testi | ✅ İndirildi |
| `brother-s7300a` | [Brother_S-7300A_Instruction.pdf](../manuals/public/Brother_S-7300A_Instruction.pdf) | Brother (üretici) | Düz dikiş makinesi | EN | Dijital, ~3.5 MB | Makine kılavuzu: ayar, **arıza giderme tablosu**, hata kodları, çizimli talimatlar | ✅ İndirildi |
| `brother-s7300b` | [Brother_S-7300B_Instruction_2025-04.pdf](../manuals/public/Brother_S-7300B_Instruction_2025-04.pdf) | Brother (üretici) | Düz dikiş makinesi | EN | Dijital, ~4.5 MB | S-7300A'nın yeni modeli → **model karışıklığı testi** | ✅ İndirildi |
| `strickland-1956` | [Strickland_A-Tailoring-Manual_1956.pdf](../manuals/public/Strickland_A-Tailoring-Manual_1956.pdf) | G. Strickland (Internet Archive) | Terzilik / dikim yöntemleri | EN | **Taranmış + OCR katmanlı**, 164 sf. (138'inde metin), 8.9 MB | **İki kolonlu sayfalar** (okuma sırası), çok sayıda çizim, **kesirli ölçülerde OCR hatası** ("½ inch" → "V2 inch", "⅛" → "Vb"), basılı ve PDF sayfa farkı (PDF s.128 = basılı s.114, numara sayfanın **üstünde**) | ✅ İndirildi (2026-10-09) |
| `mrcoffee-2003` | [MrCoffee_Coffeemaker_2003.pdf](../manuals/public/MrCoffee_Coffeemaker_2003.pdf) | Mr. Coffee / Sunbeam | Kahve makinesi | EN + ES | Dijital, 22 sf. | Makine kılavuzu: güvenlik uyarıları, temizlik, arıza giderme. **Kitapçık düzeni:** Bir PDF sayfasında iki basılı sayfa yan yana ("2" ve "43"), sayfa numarası eşlemesi için zor bir örnek. **Alan dışı doküman:** Dikim sorularında hiç gelmemeli | ✅ İndirildi (2026-10-09) |
| `bosch-ra1171` | [Bosch_RA1171_Operating-Safety_2005.pdf](../manuals/public/Bosch_RA1171_Operating-Safety_2005.pdf) | Bosch | Freze tezgâhı (elektrikli alet) | **EN / FR / ES** (bölümler arka arkaya: EN s.2-31, FR s.32-61, ES s.62+) | Dijital, 96 sf. | Makine kılavuzu: güvenlik, **parça listesi**, montaj çizimleri. **Aynı içerik üç dilde:** Dil filtresi (`lang`) ve "aynı bilgi farklı dilde" testi. **Alan dışı doküman** | ✅ İndirildi (2026-10-09) |

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

## Envanter tablosu (parse edildikten sonra doldurulacak)

| doc_id | Dosya | Marka | Versiyon | Sayfa | Dil | Tür | Metin / Tablo / Şekil | Not |
|--------|-------|-------|----------|-------|-----|-----|-----------------------|-----|
| | | | | | | | | |

## Kaynaklar

- [GL-PD-14-04A: Army Combat Uniform Coat (PDF)](https://imlive.s3.amazonaws.com/Federal%20Government/ID339162058590411927735464482663559176426/Spec%20GL-PD-14-04A.pdf)
- [GL-PD-07-14A: Combat Trousers (PDF)](https://poseidonsciences.com/wp-content/uploads/2021/07/Military-specs-for-wash-resistance-of-repellent-clothing-GL-PD-07-14A.pdf)
- [Brother Industrial: Manual Download sayfası](https://industrialsewingmachine.global.brother/manual/index) · [S-7300A Instruction Manual (PDF)](https://industrialsewingmachine.global.brother/-/media/ap2/ism/pdf/manual-download/s7300a_in.pdf?rev=-1) · [S-7300B Instruction Manual (PDF)](https://industrialsewingmachine.global.brother/-/media/ap2/ism/pdf/manual-download/s-7300b_inst_en_2025_04.pdf?rev=351bbec5bbb44f449712a8353f5476e5)
- [Strickland, A Tailoring Manual, 1956 (Internet Archive, PDF)](https://dn790007.ca.archive.org/0/items/stricklandatailoringmanual1956/stricklandatailoringmanual1956.pdf)
- [Mr. Coffee kahve makinesi kılavuzu (Internet Archive, PDF)](https://dn790009.ca.archive.org/0/items/manualsonline-id-e6076373-d174-0e44-6110-226a0874155d/e6076373-d174-0e44-6110-226a0874155d.pdf)
- [Bosch RA1171 Operating/Safety Instructions (Internet Archive, PDF)](https://dn760106.eu.archive.org/0/items/manualsonline-id-48820843-e5f4-4818-a078-e1628ccd7415/48820843-e5f4-4818-a078-e1628ccd7415.pdf)
