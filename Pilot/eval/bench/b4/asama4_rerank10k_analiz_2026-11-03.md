# B4 adım 2 analizi: reranker gecikmesi, üçlü füzyon, kaçırılan sorular — **geçici, onaysız set**

Tarih: 2026-11-03 · 10k kademesi (`scale_qwen3_8b_10000`, `scale_bge_m3_10000`, bölüm adı düzeltmesi sonrası) · 160 cevaplı soru (bilinen setler + onaysız aday taslak) · bu analizde bulut çağrısı yok (sorgu vektörleri önbellekten, gecikme mevcut kayıtlardan).

Kaynaklar: [asama4_rerank10k_ozet](asama4_rerank10k_ozet_2026-11-03.md) (reranker koşusu), [asama4_uclu_fuzyon_10k](asama4_uclu_fuzyon_10k_2026-11-03.md) (üçlü füzyon tablosu, tür bazında), ham reranker sonuçları `asama4_rerank10k_{a,b,c}`.

Yollar: **A** Qwen3-8B + BM25 (256 ön eleme, bugünkü), **C** bge-m3 + BM25, **Üçlü** Qwen3-8B dense + bge-m3 dense + BM25.

## Kısaca

- **qwen3-reranker-8b gecikmesi:** sorgu başına medyan 0,38–0,48 sn, p95 1,0–1,3 sn (dizüstü, bulut ağı dahil; süre neredeyse tamamen ağ).
- **Üçlü füzyon rerank'sız A'yı reranker'lı A seviyesine taşıyor:** filtreli hit@1/hit@5 A 0,69/0,84 → üçlü 0,75/0,89 (A + reranker: 0,72/0,89). A ve C farklı soruları kaçırıyor; füzyon ikisinin güçlü yanlarını birleştiriyor.
- **A'nın reranker sonrası kaçırdığı 18 sorunun 7'si etiket kaynaklı** (5'inde üç dilli kılavuzlarda aynı bilginin Fransızca/İspanyolca kopyası ilk 5'te; etiket yalnız İngilizce sayfayı kabul ediyor). **Prosedürde 6 kaçıştan 3'ü bu.** Gerçek arama hatası 5, bilgi birden çok parçaya yayılmış 3, başlık/parçalama 3.

## 1. Reranker gecikmesi (qwen3-reranker-8b)

Kaynak: `compare` koşusunun çağrı başına kayıtları (`seconds`, `network_s`, `attempts`), 179 çağrı/kip, 20 aday/çağrı.

| Yol | Kip | medyan | p95 | en uzun | ağ medyanı | yeniden deneme |
|---|---|---|---|---|---|---|
| A | filtreli | 0,386 sn | 1,064 sn | 2,21 sn | 0,386 sn | 1 |
| A | filtresiz | 0,481 sn | 1,301 sn | 1,96 sn | 0,481 sn | 3 |
| B | filtreli | 0,378 sn | 1,172 sn | 2,06 sn | 0,378 sn | 1 |
| B | filtresiz | 0,479 sn | 1,181 sn | 2,16 sn | 0,479 sn | 1 |
| C | filtreli | 0,383 sn | 1,004 sn | 1,77 sn | 0,382 sn | 1 |
| C | filtresiz | 0,484 sn | 1,017 sn | 1,56 sn | 0,484 sn | 0 |

- Ölçüm dizüstünden, tek istemci, sıralı çağrılar; üretimi temsil etmez. Filtresiz kipteki fark adayların daha uzun olmasından (dikkat dağıtıcıların başlık + metni).
- Uçtan uca için aday aşaması eklenir (B4: Qwen3-8B sorgu embed + Qdrant p50 ~0,7 sn). Süre bütçesindeki "arama ≤ 1 sn" hedefine reranker'la birlikte p95'te sığmıyor.
- **Önerilen ölçüm (sunucuda, B3a/B3c ile):** aynı 179 aday listesi, ısınma sonrası 3 tur; eşzamanlı 1/5/10 istekle p50/p95; sağlayıcı gecikmesi ile ağ ayrı (`network_s`), 429/5xx ve yeniden deneme sayısı. Bulut çağrısı gerektiği için onayla.

## 2. Üçlü füzyon (rerank'sız)

Her kol PREFETCH_K = 30 aday; RRF (k = 2, pipeline ile aynı), eşitlikte Qwen dense skoru, sonra `chunk_id`; ilk 20. İki dense kol ayrı koleksiyonlardan, parçalar `chunk_id` ile eşlendi. Doğrulama: aynı kodla yalnız iki kol (Qwen dense + BM25) A'nın 358 aday listesinin 355'ini birebir verdi; kalan 3 fark eşit skorların sırası (pipeline nokta kimliğine, bu kod `chunk_id`'ye bakıyor).

| Filtreli, hit@1 / hit@5 | n | A | C | Üçlü | (A + reranker) |
|---|---|---|---|---|---|
| **Toplam** | 160 | 0,69 / 0,84 | 0,62 / 0,82 | **0,75 / 0,89** | 0,72 / 0,89 |
| değer | 90 | 0,63 / 0,81 | 0,57 / 0,78 | **0,70 / 0,88** | 0,69 / 0,90 |
| prosedür | 20 | 0,55 / 0,70 | **0,65 / 0,85** | 0,65 / 0,80 | 0,55 / 0,70 |
| kod | 20 | 0,90 / 0,95 | 0,90 / 0,95 | **0,95 / 0,95** | 0,90 / 0,90 |
| arıza | 8 | 0,88 / 1,00 | 0,50 / 0,75 | 0,88 / 1,00 | 1,00 / 1,00 |
| şekil | 14 | 0,79 / 0,86 | 0,50 / 0,79 | **0,86 / 0,93** | 0,79 / 0,93 |

Filtresiz: A 0,68/0,82, C 0,62/0,78, üçlü 0,73/0,88 (tablo: [asama4_uclu_fuzyon_10k](asama4_uclu_fuzyon_10k_2026-11-03.md)).

- Kazanç A'nın kaçırdığı yerden geliyor: A'nın reranker sonrası kaçırdığı 18 sorunun 7'sinde C doğru parçayı 1.–2. sıraya koyuyor (Q15, A066, A079, A081, A108, A146, A153).
- Prosedürde üçlü C'nin hit@5'inin (0,85) bir soru altında: oradaki kayıpların çoğu dil kopyası (§3).
- Bedeli: sorguda iki embedding (Qwen3-8B bulut + bge-m3 yerel; dizüstünde bge-m3 sorgusu ~0,2–0,3 sn CPU) ve iki koleksiyon (ya da iki dense vektörlü tek koleksiyon). Üçlü füzyon + reranker henüz ölçülmedi (bulut, ~0,35 USD).

## 3. Kaçırılan sorular: A, reranker sonrası, filtreli (hit@5 dışı)

160 sorudan 18'i (hit@5 0,89). "Rerank'sız" ve "reranker": doğru parçanın sırası (RRF ilk 20; yoksa –). "Derin": aynı yol, her kol 500 aday; "dense / BM25": tek kolun sırası. **C**: aynı sorunun C yolundaki reranker sonrası sırası.

| Soru | Tür | Rerank'sız → reranker | Derin · dense · BM25 | C | Reranker sonrası ilk 5 | Olası neden |
|---|---|---|---|---|---|---|
| Q15 "S-7300A'da hangi iğne tipi?" | kod | 1 → 7 | 1 · 1 · 4 | 1 | PFM modu, besleme lokusu, program ayarı | **Başlık/parçalama:** cevap teknik özellik tablosunun tek satırı ("Needle (DB×1, DP×5) \| #11 - #18"); bağlamsız kısa satırı reranker aşağı itiyor |
| Q28 "Ceket kalıplarında dikiş payı?" | değer | – → – | 38 · 19 · 71 | – | 1. s. 21 "…3/8-inch allowance for collar…", dikiş tablosu | **Etiket şüphesi:** cevap metni s. 21'de (1. sırada), etiket yalnız s. 20; o parçanın bölümü de kalan etiket metni ("INSECT REPELLENT APPAREL") |
| N1 "Granovsky: tarak şapkasında iğne şeridi değişimi" | şekil | 7 → 6 | 8 · 16 · 5 | 7 | aynı kitabın başka tarak sayfaları | **Başlık/parçalama:** Granovsky'de bölüm adı yok (boş), birbirine benzeyen tarak onarımı parçaları ayrışmıyor |
| A066 "S-7300B dikiş adımı varsayılanı ve birimi" | değer | 12 → 12 | 12 · 7 · 21 | 1 | 1. s. 37 aynı parametre tablosu (birim, başlangıç değeri) | **Birden çok parçaya yayılmış:** aynı "Stitch pitch" tablosu kılavuzda 4 yerde; etiket yalnız s. 53 |
| A075 "-3 tipi 4000 dev/dk'da en fazla dikiş adımı" | değer | 16 → 13 | 17 · 10 · 55 | 11 | s. 12 teknik özellik (hız/adım), parametre tabloları | **Etiket şüphesi:** s. 12'deki özellik tablosu da hız–adım ilişkisini veriyor (4 mm üstü / 4000), etiket s. 78 lokus tablosu; soru iki yere uyuyor |
| A079 "Kalın kumaşta makine dikiş boyu" | değer | – → – | 25 · 13 · – | 1 | JUKI dikiş boyu ayarı, Brother X-over | **Gerçek arama hatası:** kapsamsız Türkçe soru, Strickland'de bölüm adı yok; BM25 hiç bulmuyor, dense 13. |
| A081 "Kruvaze paltoda düğmelenmeyen alt kat" | prosedür | – → – | 43 · 22 · – | 1 | ceket fermuar tabloları | **Gerçek arama hatası:** aynı desen (Strickland, BM25 yok, dense 22.) |
| A100 "Bir fincan kaç ons?" | değer | 15 → 6 | 17 · 8 · 20 | 4 | 1. s. 14 İspanyolca "1 taza = 5 onzas" | **Etiket şüphesi (dil kopyası):** aynı bilgi İspanyolca bölümde 1. sırada |
| A102 "Sürahideki kireç lekesi" | **prosedür** | 17 → 10 | 19 · 9 · – | – | 1. s. 6–7 İspanyolca "Cómo Lavar la Jarra" (aynı talimat) | **Etiket şüphesi (dil kopyası)** |
| A108 "Freze modeli tabloda yoksa?" | **prosedür** | – → – | 39 · 19 · – | 2 | İspanyolca ve Fransızca karşılıkları (s. 44, 76) | **Etiket şüphesi (dil kopyası)** |
| A111 "Gönye kanalı hangi ölçüye uyar?" | değer | – → – | 23 · 12 · 278 | – | 1. s. 61 Fransızca karşılığı | **Etiket şüphesi (dil kopyası)** |
| A112 "Şalter kapalıyken nasıl kilitlenir?" | **prosedür** | 13 → 7 | 13 · 7 · 334 | 10 | İspanyolca s. 83 ve Fransızca s. 51 aynı adım | **Etiket şüphesi (dil kopyası)** |
| A146 "s7300a e50 ne demek" | kod | 19 → 9 | 17 · 11 · 9 | 2 | başka program ve hata kodu parçaları | **Gerçek arama hatası:** "e50" ile "E050" eşleşmiyor (kod biçimi normalleştirmesi) |
| A147 "ceket ilik dikis sayisi?" | değer | 11 → 8 | 10 · 14 · 6 | 7 | 3.7.5.1 Buttonholes, muayene tablosu | **Birden çok parçaya yayılmış:** ilik bilgisi 3.7.5.1'de, dikiş sıklığı 3.11.1'de; etiket yalnız 3.11.1 |
| A148 "pantolon cep agzi kac inc" | değer | – → – | 44 · 20 · 73 | – | dikiş tablosunun cep satırları | **Gerçek arama hatası:** aksansız gündelik yazım; "cep ağzı" ↔ "pocket opening" iki kolda da zayıf |
| A151 "freze tablası şalteri nasıl kitlenir" | **prosedür** | – → – | 21 · 11 · 334 | – | şalterin genel kullanımı (Fransızca s. 50–51), şalter montajı; kilitleme adımının çevirisi yok | **Gerçek arama hatası:** A112'nin gündelik ve yazım hatalı hali ("kitlenir"); BM25 bulmuyor, dense 11. |
| A152 "granovsky sabun kaç gram" | değer | – → – | 27 · 14 · 177 | – | Granovsky'nin OCR çöpü parçaları ("a> o", rastgele karakterler) | **Başlık/parçalama:** OCR çöpü parçalar kısa sorguda dense'te öne çıkıyor (veri kalitesi) |
| A153 "s7300a iplik gerginligi nasıl ayarlanır" | **prosedür** | – → – | 26 · 13 · 139 | 1 | iplik alma yayı, PFM ayarı | **Birden çok parçaya yayılmış:** alt ve üst iplik gerginliği ayrı parçalarda; etiket yalnız üst iplik |

**Neden dağılımı (18):** etiket şüphesi 7 (5'i dil kopyası: A100, A102, A108, A111, A112) · gerçek arama hatası 5 · birden çok parçaya yayılmış 3 · başlık/parçalama 3.

**Prosedür soruları (20 sorudan 6 kaçış, hit@5 0,70):** A102, A108, A112 dil kopyası; A081 ve A151 gerçek arama hatası (Strickland; gündelik yazım); A153 yayılmış bilgi. Dil kopyaları kabul edilseydi prosedür hit@5 0,85 olurdu (3 soru, üçünde de aynı talimatın çevirisi ilk 5'te). Bosch ve Mr. Coffee üç dilli; ayrıca Mr. Coffee'nin İspanyolca sayfaları meta veride `en` işaretli (`registry` dil aralığı eksik).

Desen: gerçek arama hatalarında dense kol doğru parçayı 13–22. sırada buluyor, BM25 hiç bulmuyor (Türkçe soru, İngilizce metin); RRF'de tek kol yetmiyor ve parça ilk 20'ye girmiyor. C bu soruların çoğunu 1. sıraya koyuyor; üçlü füzyonun kazancı buradan.

**A036 "Pantolon çiziminde hangi ölçüler verilmiş?"** A'da 1. sırada (çizim parçası), C'de 15. Düzeltmeden sonra ölçü tablosu "Table VII. Finished measurements" başlığıyla ilk 5'e giriyor (A'da 2.–4.). Soru hem çizimdeki ölçülere hem bitmiş ölçü tablosuna uyuyor: **etiket şüphesi** (soruyu "çizimdeki" diye daraltmak ya da tabloyu da kabul etmek).

## 4. Öneriler (uygulanmadı)

1. **Etiket:** üç dilli kılavuzlarda aynı bilginin dil kopyalarını `kabul`a eklemek (A100, A102, A108, A111, A112); Q28, A066, A075, A147, A153, A036 için kabul edilen sayfaları gözden geçirmek. İnceleme tablosunda bu sorular işaretlenebilir.
2. **Arama:** üçlü füzyon + reranker ölçümü (bulut, ~0,35 USD); dil kopyalarında arayüzün kullanıcı diline göre (ör. İngilizce) tercih etmesi; "e50 → E050" gibi kısa kod biçimleri için `spoken_codes` genişletmesi.
3. **Veri:** Mr. Coffee dil aralıkları (`registry`); Granovsky OCR çöpü parçalarının `nav` benzeri bir işaretle aramadan çıkarılması.

## 5. Qdrant

Sabah açılan sunucu 14:00–14:56 arasında kapanmıştı; o oturumun çıktısı yalnız terminale gittiği için neden bilinmiyor. 14:59'da yeniden başlatıldı, çıktısı `data/logs/qdrant_server_2026-11-03.log`'a yazılıyor ve hata/panik/kapanma satırları izleniyor. Bu raporun yazıldığı ana kadar kapanma yok; günlükte yalnız Windows'a özgü zararsız uyarılar var (yapılandırma dosyası yok, dosya sistemi türü denetlenemiyor, web arayüzü klasörü yok). Önceki günlerde aynı depoda "Access is denied (os error 5)" ile segment yeniden adlandırma hataları görülmüştü (27 Ekim, bu sabah `synth_1m`); Windows'ta dosya kilidi (ör. Defender taraması) olası bir kararsızlık kaynağı.
