# Manual Envanteri ve Test Seti

> **Kaynak not:** `manual-envanteri.md` · **İlgili plan:** req.md Adım 0.2 ve 2.1 · **Bağlantılı notlar:** [02-pdf-isleme.md](02-pdf-isleme.md)
> **Durum (2026-10-09):** Test seti seçildi ve indirildi: 7 doküman (2 şartname + 1 terzilik kitabı + 4 makine kılavuzu). Envanter tablosu parse sonrası doldurulacak.
> **Beslediği çıktılar:** Manual envanteri ve format değerlendirmesi · Açık sorular & riskler · Görev/faz planı (geçiş stratejisi)

---

## 1. Özet

- Geliştirme ve test, **açık erişimli (public) manuellerle** yapılacak; sistem hedef oranlara ulaşınca (req.md 6.3) **kendi (müşteri) manuellerimize** geçilecek.
- Seçilen set: 2 ABD ordusu kıyafet şartnamesi (GL-PD), 1 taranmış terzilik kitabı (Strickland, 1956), 2 Brother endüstriyel dikiş makinesi kılavuzu, 2 alan dışı makine kılavuzu (Mr. Coffee, Bosch).
- Set; dijital, taranmış, taranmış + OCR katmanlı, iki kolonlu, tablo ağırlıklı, çizim ağırlıklı, kitapçık düzenli ve çok dilli dokümanları kapsıyor.
- **Eksik:** Türkçe doküman yok; aynı dokümanın iki versiyonu yok; şartnamelerin hepsi ABD ordusu formatında.

## 2. Strateji: Public set → gerçek veri

| Aşama | Veri | Amaç |
|-------|------|------|
| **1. Geliştirme / test** | İnternetten bulunan açık erişimli manueller | Sistemi gizlilik riski olmadan kurmak, ölçmek, iyileştirmek |
| **2. Geçiş** |Müşteri manuelleri | Test setinde hedef oranlara ulaşınca (req.md 6.3) gerçek veriye geçmek |

**Eksi:**
- Public set gerçek manuellere **benzemeli** (tedarikçi/kalite manuali tarzı, dikiş/ölçü değerleri, tablolar, şekiller, en az bir taranmış doküman); yoksa test sonuçları gerçek veriye taşınmaz.
- Geçişte **tekrar ölçüm şart**; gerçek veride çıkan farklar (format, dil, yapı) ayrıca not edilecek.

## 3. Seçim kriterleri

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

## 4. Envanter: Seçilen test seti (2026-10-08 / 09)

Dosyalar `Pre/manuals/public/` klasöründe.

| doc_id | Dosya | Kurum / marka | Ürün | Dil | Format | Öne çıkan özellik | Durum |
|--------|-------|---------------|------|-----|--------|-------------------|-------|
| `gl-pd-14-04a` | GL-PD-14-04A_ACU-Coat.pdf | US Army (GL-PD) | Ceket | EN | Dijital, ~56 sf. | SPI + tolerans, stitch/seam tablosu, ölçü tabloları | ✅ İndirildi |
| `gl-pd-07-14a` | GL-PD-07-14A_Combat-Trousers.pdf | US Army (GL-PD) | Pantolon | EN | **Taranmış**, ~48 sf. (≈300 DPI) | SPI, Table V (ASTM D6193), OCR testi | ✅ İndirildi |
| `brother-s7300a` | Brother_S-7300A_Instruction.pdf | Brother | Düz dikiş makinesi | EN | Dijital, ~3.5 MB | Ayar, **arıza giderme tablosu**, hata kodları, çizimli talimatlar | ✅ İndirildi |
| `brother-s7300b` | Brother_S-7300B_Instruction_2025-04.pdf | Brother | Düz dikiş makinesi | EN | Dijital, ~4.5 MB | S-7300A'nın yeni modeli → **model karışıklığı testi** | ✅ İndirildi |
| `strickland-1956` | Strickland_A-Tailoring-Manual_1956.pdf | G. Strickland (Internet Archive) | Terzilik / dikim yöntemleri | EN | **Taranmış + OCR katmanlı**, 164 sf. (138'inde metin), 8.9 MB | **İki kolonlu sayfalar** (okuma sırası), çok sayıda çizim, **kesirli ölçülerde OCR hatası** ("½ inch" → "V2 inch", "⅛" → "Vb"), basılı/PDF sayfa farkı (PDF s.128 = basılı s.114, numara sayfanın **üstünde**) | ✅ İndirildi (2026-10-09) |
| `mrcoffee-2003` | MrCoffee_Coffeemaker_2003.pdf | Mr. Coffee / Sunbeam | Kahve makinesi | EN + ES | Dijital, 22 sf. | Güvenlik uyarıları, temizlik, arıza giderme. **Kitapçık düzeni:** bir PDF sayfasında iki basılı sayfa yan yana ("2" ve "43"). **Alan dışı** | ✅ İndirildi (2026-10-09) |
| `bosch-ra1171` | Bosch_RA1171_Operating-Safety_2005.pdf | Bosch | Freze tezgâhı (elektrikli alet) | **EN / FR / ES** (EN s.2–31, FR s.32–61, ES s.62+) | Dijital, 96 sf. | Güvenlik, **parça listesi**, montaj çizimleri. **Aynı içerik üç dilde** → `lang` filtresi testi. **Alan dışı** | ✅ İndirildi (2026-10-09) |

**Doküman türleri (`doc_type`):** `product_standard` (şartnameler), `machine_manual` (Brother, Mr. Coffee, Bosch), `tailoring_guide` (Strickland).

**Aday olup eklenmeyenler / bekleyenler:**

| # | Doküman | Durum |
|---|---------|-------|
| M3 | Brother Parts Book (S-7300A) — [partsbook.brother.co.jp](https://partsbook.brother.co.jp/pub/machine/detail/en/12/274); patlatılmış montaj çizimleri + parça numaraları (parça kodu araması / BM25, çizim + tablo birlikte) | ⏳ Formatı kontrol edilecek |
| — | Stitch Guide (ASTM D6193 / ISO 4915 dikiş tipi çizimleri) | Değerlendirildi, **sete eklenmedi** (2026-10-09) |
| — | Uludağ Üniversitesi "Sanayi Tipi Düz Dikiş Makinesi Bakım ve Kullanım Talimatı" (Türkçe, .docx) | Link şu an 404. Resmi üretici kılavuzlarının Türkçe versiyonu bulunamadı; Türkiye distribütör sitelerinde aranabilir |

## 5. Format değerlendirmesi: Set neyi test ediyor?

| Test edilen durum | Doküman(lar) |
|-------------------|--------------|
| Metin + tablo | GL-PD-14-04A |
| Taranmış doküman (OCR) | GL-PD-07-14A |
| İki kolonlu taranmış kitap, kesirli ölçü OCR hatası | Strickland |
| Çizimli talimat ("Şekil 3'teki A vidasını gevşetin") | Brother, Bosch |
| Arıza giderme tabloları (Belirti / Sebep / Çözüm) | Brother |
| **Aynı soru, farklı cevap** | Dış görünür dikiş SPI: ceket 11 ± 1, pantolon 10–14 |
| **Model karışıklığı** | S-7300A vs S-7300B (`product_model` filtresi gerekliliği) |
| Kod / numara araması (BM25) | "301", "401", "LSc-2", "ASTM D6193"; hata kodları ("E-07"), parça no. ("146391-001") |
| Multimodal ihtiyacı | Strickland dikim çizimleri, Brother/Bosch montaj ve parça çizimleri |
| Uyarı / güvenlik bölümleri | Brother, Mr. Coffee, Bosch |
| Basılı ↔ PDF sayfa numarası eşlemesi | Strickland, Mr. Coffee (kitapçık) |
| Dil filtresi, aynı bilgi farklı dilde | Bosch (EN/FR/ES), Mr. Coffee (EN/ES) |
| **Yanlış doküman / alan dışı** | Mr. Coffee, Bosch: "dikiş atlıyor", "iplik gerginliği" sorularına bunlardan cevap gelmemeli; gelirse metadata filtresi veya arama kalitesinde sorun var |

**Şartnameler hakkında:** GL-PD (*Purchase Description*) dokümanları ABD ordusunun kıyafet şartnameleri; ABD hükümeti yayını olduğu için kamuya açık. Bir markanın tedarikçi manueline çok benziyor: dikiş sıklığı (SPI) ve toleranslar, dikiş/seam tipi tabloları, ölçü tabloları, teknik çizimler.

**Dokümanlardan örnek değerler** (arama sonuçlarından; parse sonrası tekrar kontrol edilecek):

| Doküman | Örnek |
|---------|-------|
| GL-PD-14-04A (ceket) | "outside visible stitching 11 (± 1) SPI", "overedge 10 (± 2) SPI", "buttonholes 54 (± 2) SPI" |
| GL-PD-07-14A (pantolon) | "outside visible stitching 10-14 SPI", "buttonholes 52-56 SPI including tack" |

## 6. Makine kılavuzlarıyla genişletme (M1, M2)

**Neden:** Sistem ileride **makine kullanımı, ayarı, arıza tespiti ve tamiri** sorularına da cevap verebilmeli (ör. "Dikiş atlıyor, ne yapmalıyım?", "Üst iplik gerginliği nasıl ayarlanır?"). Makine kılavuzları ayrıca farklı bir doküman türü olarak test setini çeşitlendiriyor.

- **M1 – S-7300A** (tek iğneli düz dikiş): kullanım/ayar adımları, arıza giderme tablosu, adım adım talimat + çizim, hata kodları.
- **M2 – S-7300B** (Nisan 2025): benzer doküman, farklı değerler → "S-7300A'da" sorusuna S-7300B'den cevap gelmemeli.

**Metadata etkisi:** Makine kılavuzları için `doc_type = machine_manual`, `manufacturer`, `product_model` (ör. "S-7300A") alanları gerekecek (rag-temelleri.md 1.7'ye eklenecek).

## 7. Envanter tablosu (parse sonrası doldurulacak)

| doc_id | Dosya | Marka | Versiyon | Sayfa | Dil | Tür | Metin / Tablo / Şekil | Not |
|--------|-------|-------|----------|-------|-----|-----|-----------------------|-----|
| | | | | | | | | |

## 8. Açık sorular ve riskler

- **Türkçe doküman yok** → diller arası test **Türkçe soru + İngilizce doküman** ile yapılacak; Türkçe doküman parsing'i test edilmemiş olacak.
- **Versiyon filtresi test edilemiyor:** aynı dokümanın iki versiyonu yok.
- **Temsil riski:** Şartnamelerin hepsi ABD ordusu formatında; gerçek marka manuellerinin formatı farklı olabilir → gerçek veriye geçişte tekrar ölçüm.
- **M3 Parts Book** formatı henüz kontrol edilmedi.
- Gerçek veride taranmış manuel oranı ve görsel türleri bilinmiyor (req.md Q3).

## Kaynaklar

- [GL-PD-14-04A: Army Combat Uniform Coat (PDF)](https://imlive.s3.amazonaws.com/Federal%20Government/ID339162058590411927735464482663559176426/Spec%20GL-PD-14-04A.pdf)
- [GL-PD-07-14A: Combat Trousers (PDF)](https://poseidonsciences.com/wp-content/uploads/2021/07/Military-specs-for-wash-resistance-of-repellent-clothing-GL-PD-07-14A.pdf)
- [Brother Industrial: Manual Download sayfası](https://industrialsewingmachine.global.brother/manual/index) · [S-7300A Instruction Manual (PDF)](https://industrialsewingmachine.global.brother/-/media/ap2/ism/pdf/manual-download/s7300a_in.pdf?rev=-1) · [S-7300B Instruction Manual (PDF)](https://industrialsewingmachine.global.brother/-/media/ap2/ism/pdf/manual-download/s-7300b_inst_en_2025_04.pdf?rev=351bbec5bbb44f449712a8353f5476e5)
- [Strickland, A Tailoring Manual, 1956 (Internet Archive, PDF)](https://dn790007.ca.archive.org/0/items/stricklandatailoringmanual1956/stricklandatailoringmanual1956.pdf)
- [Mr. Coffee kahve makinesi kılavuzu (Internet Archive, PDF)](https://dn790009.ca.archive.org/0/items/manualsonline-id-e6076373-d174-0e44-6110-226a0874155d/e6076373-d174-0e44-6110-226a0874155d.pdf)
- [Bosch RA1171 Operating/Safety Instructions (Internet Archive, PDF)](https://dn760106.eu.archive.org/0/items/manualsonline-id-48820843-e5f4-4818-a078-e1628ccd7415/48820843-e5f4-4818-a078-e1628ccd7415.pdf)
- [Brother S-7300A Parts Book](https://partsbook.brother.co.jp/pub/machine/detail/en/12/274)
