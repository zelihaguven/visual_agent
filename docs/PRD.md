# Visual Agent: Ürün Gereksinimleri (PRD)

Nov 3, 2026 · @Ilgın · Güncelleme: 6 Kasım 2026 (Adım 2 kararları: cevap modeli, şema, sağlayıcılar, kapılar)

## Amaç ve kapsam

Visual Agent, fabrikadaki ustaların ve departman çalışanlarının marka şartnameleri, makine kılavuzları ve dikim kaynakları hakkında yazılı ya da sesli soru sorup birkaç saniye içinde kaynaklı cevap aldığı bir sistemdir. Cevap kılavuzdan bulunur, kaynağa dayalı yazılır, bilginin geçtiği sayfa vurgulu gösterilir ve sesli okunur. Sistem emin değilse tahmin etmez: netleştirme sorusu sorar ya da "bulunamadı" der.

Bu belge ürünün tek güncel tanımıdır. `UYGULAMA-PLANI.md` (13 Ekim) ve `calisma-notlari/req.md` (9 Ekim) yerini bu belgeye bırakır; ikisi de arşive taşınır. `MIMARI.md` teknik ayrıntı belgesi olarak kalır, bu belgeyle çelişen yerleri güncellenir.

Aşama adları: bu belgede ürün adımları **Adım 1–6** diye geçer. Arama benchmark'ının kendi aşamaları **B0–B5** diye yazılır (eski adıyla Aşama 0–5). Eski uygulama planının Aşama 0–7 numaralandırması artık kullanılmaz.

## Kullanıcılar ve roller

Sistemde dört rol bulunur. Bir kişi aynı anda birden fazla departmanda rol alabilir.

| Rol | Kim | Yapabildikleri |
| --- | --- | --- |
| Kullanıcı | Usta, kalite ekibi, departman çalışanı | Yetkisi olan dokümanlara yazılı ya da sesli soru sorar, kaynak sayfayı görür, cevabı dinler |
| Departman yetkilisi | Her departmanda belirlenen bir ya da birkaç kişi | Kendi departmanına doküman ekler, günceller, siler; her doküman için kimin erişeceğini belirler; istisna olarak başka departmandan kişilere erişim verir |
| Sistem yöneticisi | BT | Departmanları ve yetkilileri tanımlar, sunucuyu ve yedekleri yönetir, denetim kayıtlarını görür |
| Geliştirme ekibi | Proje ekibi | Ölçüm ve deneme yapar; gerçek veriye geçene kadar yalnız açık erişimli dokümanlarla çalışır |

Kullanım ortamı fabrika zeminidir: tablet ya da bilgisayar, gürültülü ortam, eller çoğu zaman meşgul. Bu yüzden sesli soru ve sesli cevap temel özelliktir, ek bir seçenek değildir.

## Temel kullanım akışları

**A1. Soru sorma (ana akış)**

1. Kullanıcı soruyu yazar ya da söyler. Sesli soruda tanınan metin ekranda gösterilir.
2. Sistem yalnız kullanıcının erişebildiği dokümanlarda arar.
3. Cevap ekranda akarak gelir. Her değerin yanında kaynak (doküman, sayfa) bulunur.
4. Kaynak sayfa, bilginin geçtiği alan vurgulu olarak açılır.
5. Cevap, yazılması sürerken sesli okunmaya başlar.
6. Cevabın üstünde doğrulama rozeti görünür: doğrulandı, kısmen doğrulandı ya da doğrulanamadı.

**A2. Netleştirme.** Soru birden fazla ürüne, modele ya da dokümana uyuyorsa sistem cevap yazmadan önce "Hangi model?" gibi kısa bir soru sorar. Kullanıcı seçince akış A1'in 3. adımından sürer.

**A3. Bulunamadı.** Yetkili dokümanlarda cevap yoksa sistem bunu açıkça söyler. Alakasız bir kaynaktan cevap yazmaz, genel bilgiyle boşluk doldurmaz.

**A4. Doküman ekleme.** Departman yetkilisi PDF yükler, doküman türünü ve markayı/modeli girer, erişecek kişileri ya da grupları seçer. Sistem dokümanı işler ve bir kapsam raporu gösterir: sayfa sayısı, taranmış sayfa oranı, OCR uyarıları, şekil sayısı. Yetkili raporu onaylayınca doküman sorgulanabilir olur.

**A5. Erişim verme ve geri alma.** Yetkili, mevcut bir dokümana kişi ya da grup ekler veya çıkarır. Değişiklik bir sonraki sorudan itibaren geçerlidir ve denetim kaydına yazılır.

**A6. Doküman silme.** Yetkili dokümanı siler. Doküman, parçaları ve vektörleri indeksten kaldırılır; sonraki hiçbir cevapta kaynak olarak görünmez.

## İşlevsel gereksinimler

Öncelik: **Zorunlu** = ilk sürümde olmalı, **Sonra** = ilk sürümden sonra. "Durum" sütunu pilotta ya da benchmark'ta nereye gelindiğini gösterir.

| No | Gereksinim | Öncelik | Durum |
| --- | --- | --- | --- |
| G1 | Yazılı soru | Zorunlu | Pilotta var |
| G2 | Sesli soru; tanınan metin onaylanabilir ve düzeltilebilir | Zorunlu | Pilotta var (STT) |
| G3 | Kaynaklı cevap: her değer doküman ve sayfayla | Zorunlu | Pilotta var |
| G4 | Kaynak sayfanın vurgulu gösterimi | Zorunlu | Pilotta var |
| G5 | Akışlı sesli cevap; kodlar, toleranslar ve binlik ayırıcılar doğru okunur | Zorunlu | Pilotta var, akışlı değil |
| G6 | Doğrulama rozeti; "doğrulandı" yalnız kod kontrolünden geçen cevapta | Zorunlu | Pilotta var |
| G7 | Belirsiz soruda netleştirme | Zorunlu | Var; kapı tanımı 6 Kasım (farklı ürün zorunlu, belge içi varyant, gereksiz). Değer farklı 13/15 |
| G8 | Cevap yoksa "bulunamadı" | Zorunlu | Var; bağlanan hatta 51/51 |
| G9 | Hata kodlarında tam eşleşme; benzer kodların karışmaması | Zorunlu | Pilotta var |
| G10 | Şekil ve tabloların cevaba katılması (VLM açıklaması, tablo varyant kontrolü) | Zorunlu | Pilotta var |
| G11 | İki katmanlı yetki (departman + doküman) aramanın içinde uygulanır | Zorunlu | Departman filtresi Qdrant'ta var; doküman katmanı yok |
| G12 | Departman yetkilisinin doküman ekleme, güncelleme, silme ve erişim yönetimi | Zorunlu | Yok |
| G13 | Doküman eklerken kapsam raporu | Zorunlu | Kısmen (komut satırı) |
| G14 | Denetim kaydı: kim, ne zaman, hangi dokümana ne sordu; yetki değişiklikleri | Zorunlu | Yok |
| G15 | Tablet ve bilgisayar tarayıcısından erişim, giriş | Zorunlu | Yok (Streamlit prototip) |
| G16 | Departmana özel terim sözlüğü ve doküman kuralları (isteğe bağlı veri) | Sonra | Altyapı var |
| G17 | Kullanıcı geri bildirimi (cevap doğru / yanlış) | Sonra | Yok |
| G18 | Aynı konuda iki dokümanın çelişen değerlerinin ikisinin de kaynaklı gösterilmesi | Sonra | Yok |

## Yetki ve doküman yönetimi

Varsayılan kural: bir kullanıcı bir dokümanı ancak iki koşul birlikte sağlanırsa sorgulayabilir: doküman kullanıcının departmanına aittir ve dokümanın yetkilisi bu kullanıcıya (ya da kullanıcının grubuna) erişim vermiştir. Departmana üye olmak tek başına yetmez. Tek istisna aşağıdaki departmanlar arası paylaşımdır.

**Kurallar**

- Her dokümanın bir sahibi departmanı ve bir ya da birkaç yetkilisi vardır.
- Erişim kişi ya da grup düzeyinde verilir. Grup örneği: "Kalite – tüm ekip", "Dikimhane – hat şefleri".
- Yetki filtresi aramanın içinde uygulanır. Yetkisiz parça hiçbir aşamada aday listesine girmez, sonradan elenmez. Bu kural arama, netleştirme seçenekleri, kaynak sayfa görüntüleme ve sesli cevap için aynıdır.
- Kaynak sayfa görüntüleme de yetkiye bağlıdır. Sayfa, yalnız o dokümana erişimi olan kişiye gösterilir.
- Erişim değişikliği bir sonraki sorudan itibaren geçerlidir; indeksin yeniden kurulması gerekmez.

**Departmanlar arası istisna paylaşım.** Yetkili, kendi dokümanına başka bir departmandan belirli kişilere erişim verebilir. Bu durum seyrek olacağı için ana akış değil, istisna olarak tasarlanır:

- Paylaşım yalnız kişi düzeyindedir, başka bir departmanın tamamına verilemez.
- Her paylaşım denetim kaydına yazılır ve yetkilinin listesinde ayrıca görünür.
- Paylaşım istenirse bitiş tarihiyle verilir.

Açık karar: karşı departmanın yetkilisinin onayı gerekecek mi? (bkz. Açık kararlar, A4)

## Doğruluk ve güvenilirlik

En büyük risk, yanlış bir değerin (dikiş sıklığı, tolerans, ayar) güvenilir görünmesidir. Bu yüzden ilk sürüm, aşağıdaki K1 ölçütlerinin hepsini geçmeden gerçek veriye geçmez. Adım 2'den sonra (6 Kasım) doğru "bulunamadı" %100 (51/51) ve doğrulanmış görünen yanlış 0. En uzak ölçüt süre: ilk doğrulanmış cümlenin p95'i 3,63 sn (hedef ≤ 3 sn).

| Ölçüt | Hedef | Bugün | Not |
| --- | --- | --- | --- |
| Arama: doğru sayfa ilk 5'te (hit@5) | ≥ %90 | %89 | bge-m3 + BM25, rerank kapalı; 1M'de ölçülüyor (B3b) |
| Arama: doğru sayfa ilk sırada (hit@1) | izlenir | %72 | MRR 0,79 |
| Değer doğruluğu | ≥ %98 | kısmen | Beklenen değer cevapta (kapsama) %93 (bağlanan hat, 8 kaynak); kesinlik ölçümü ayrıca yapılacak |
| "Doğrulandı" rozetli yanlış değer | 0 | 0 | Bağlanan hatta (8 kaynak) 0. 5 kaynakta 1 vaka (B012, niteleyici uyuşmazlığı); 8 kaynak bu yüzden seçildi |
| Doğru "bulunamadı" | ≥ %90 | %100 | Bağlanan hat: 51/51 (onaylı + yeni set). Pilotta 7B modelle %48'di |
| Tuzak sorular | %100 | ölçülmedi |  |

**Ölçüm kuralları**

- Kararlar onaylı soru setiyle verilir: 199 onaylı + 46 yeni soru (2026-11-06). Onay ölçütü kanıt cümlesidir; model çıktısı onay ölçütü olmaz.
- **Netleştirme kapısı:** farklı ürün (değer farklı) → netleştirme zorunlu; belge içi varyant → netleştirme ya da bütün varyant değerleri doğru etiketleriyle; değer aynıysa ya da ürün soruda söylenmişse netleştirme gereksiz sayılır.
- **Ek kapı ve izlemeler (2026-11-06):** yanlış ret ayrıca raporlanır; "niteleyici uyuşmazlığı" (alıntı gerçek, soru başka şey soruyor) doğrulanmış görünen yanlış sayılır.
- JUKI dokümanı (`gorulmemis_juki.json`) ayar yapmakta kullanılmaz, yalnız görülmemiş doküman testi içindir.
- İyileştirmeler genel kurallarla yapılır, test dokümanlarına özgü kural yazılmaz.
- Soru setini şimdilik geliştirme ekibi hazırlar ve onaylar. Gerçek veriye geçerken departmandan bir uzmanın kontrol etmesi gerekir (Açık kararlar, A2).

## Performans ve ölçek

Sistem gerçek zamanlı çalışmalıdır: usta soruyu sorduktan sonra cevabın ilk cümlesini 3 saniye içinde görmeli, sesi 4 saniye içinde duymaya başlamalıdır. Tam cevabın bitmesini beklemek gerekmez; cevap akarak gelir.

**Süre bütçesi (p95, sunucuda, 1M parça)**

| Adım | Hedef | Bugün |
| --- | --- | --- |
| Sesli soru tanıma (STT) | ≤ 1 sn | ölçülecek |
| Arama (embed + vektör DB) | ≤ 1 sn | p50 0,45 sn (36 soru, dizüstü) |
| LLM ilk kelime | ≤ 1,5 sn | p95 ~0,9 sn (Gemma 4, DeepInfra) |
| İlk cümle ekranda | ≤ 3 sn | İlk **doğrulanmış** cümle, arama dahil: p50 2,40 sn, p95 3,63 sn (245 soru, dizüstü); duman testinde p95 3,32 sn. p95 hedefin üstünde |
| Sesli okumanın başlaması (TTS) | ≤ 4 sn | ölçülecek |

Dizüstü süreleri "üretimi temsil etmez" diye işaretlenir ve karar için kullanılmaz. Karar sunucudaki ölçümle (B3a) verilir.

**Ölçek.** 1M parça alt sınırdır, üst sınır değildir. Departmanların kaç doküman ekleyeceği henüz bilinmiyor. Sistem, indeks büyüdüğünde arama süresi ve doğruluğu izlenecek şekilde kurulur.

**Eşzamanlı kullanıcı.** Fabrika büyük olduğu ve sayı tahmin edilemediği için hedef sayı koymak yerine kapasite ölçülür. B3c yük testinde 10, 25, 50 ve 100 eşzamanlı kullanıcıyla p95 süresine bakılır. Sonuç BT'ye "bu sunucu, süre bütçesini bozmadan en fazla N kişiyi kaldırır" diye sunulur. Gerekirse sunucu büyütülür ya da ikinci sunucu eklenir.

## Veri güvenliği ve bulut kullanımı

Bulut kullanılabilir, ama yalnız veri saklamayan (ZDR) sağlayıcılarla ve yalnız parça düzeyinde. Belgenin tamamı hiçbir zaman buluta gönderilmez.

| Adım | Nerede çalışır | Buluta giden |
| --- | --- | --- |
| Ayrıştırma, OCR, parçalama, sayfa konumları | Sunucu | Hiçbir şey |
| Embedding (indeksleme ve soru) | Sunucu ya da ZDR'li bulut | Parça metni, soru metni |
| Vektör veritabanı, yetki filtresi | Sunucu | Hiçbir şey |
| Cevap üretimi (LLM) | ZDR'li bulut (Gemma 4; DeepInfra, yedek Venice/Parasail) | Soru + bulunan 8 parça |
| BM25 sorgu çevirisi | ZDR'li bulut (Gemma 4; NextBit, yedek Venice) | Yalnız soru metni |
| Şekil açıklaması (VLM) | Açık karar | Şekil görüntüsü (A3) |
| STT, TTS | Açık karar | Ses ya da cevap metni (A3) |

**Kurallar**

- ZDR kapatılamaz. ZDR'si olmayan model hiç çağrılmaz, denemelere de alınmaz.
- API anahtarı yalnız ortam değişkeninden okunur; hiçbir dosyaya, loga ya da commit'e girmez.
- Bulut harcaması önceden hesaplanır. Bir koşu 5 $'ı aşacaksa önce onay alınır.&#32;
- Test ve gerçek ortam ayrı yapılandırma profilleriyle kurulur. Test ortamındaki bulut ayarları gerçek ortama kendiliğinden geçmez.
- Gerçek veriye geçene kadar yalnız açık erişimli dokümanlar kullanılır.

## Mimari ve dağıtım

Uygulama tek bir sunucuda çalışır; kullanıcılar tablet ya da bilgisayardan tarayıcıyla bağlanır. Tabletlerde ağır işlem yapılmaz. Sunucu, şirketin kendi sunucusu da olsa "harici sunucu" gibi tasarlanır: istemciden bağımsız, ağ üzerinden erişilen tek bir servis.

&#91;embedded content: hedef mimari · istemci, sunucu, ZDR'li bulut\]

Kesik çizgili kutunun yeri henüz kararlaştırılmadı. Streamlit yalnız geliştirme ekibinin test arayüzü olarak kalır; Adım 3'ten sonra arka uç servisine bağlanır, böylece denemeler aynı servis üzerinden görülür.

**Bileşen kararları**

| Bileşen | Karar | Dayanak |
| --- | --- | --- |
| Arama | İkili yol: bge-m3 dense + BM25 (çevrilmiş sorgu, 1,2 sn sınırı), RRF ile birleşim, rerank kapalı | B4 ölçümü; Adım 2 uçtan uca ölçüm (yanlış ret 25 → 11) |
| Vektör veritabanı | Qdrant, sunucu modu, yetki filtresi içinde | B2 ölçümü |
| Embedding (1M kademesi) | bge-m3 ve Qwen3-8B (bulut) karşılaştırılıyor | B3b sürüyor |
| Cevap modeli (LLM) | **Gemma 4 26B A4B**, şema **c150b-J** (öğe başına alıntı, girintisiz JSON), 8 kaynak, max_tokens 1200. DeepInfra birincil; Venice ve Parasail **yalnız yedek** (hata, 429, 2,5 sn'de ilk token yok, akış bekçisi). Ağ yoksa "servis kullanılamıyor"; yerel modele otomatik düşüş yok | Adım 2 nihai tur, uçtan uca ölçüm ve duman testi ([plan §29](../Pilot/eval/bench/adim2/plan_cevap_modeli_2026-11-05.md)) |
| Sağlayıcı kapısı | "≥ 2 ZDR" = kesinti dayanıklılığı: kalite kapıları birincilde; yedekte doğrulanmış görünen yanlış 0, yedek kipinde ulaşmayan cevap ≤ ~%5, toplamda ≤ ~%1 | Akış bekçisi ve yedek benzetimi (2026-11-06) |
| Doğrulama | Kod: öğe başına alıntı birebir, cümlenin sayıları kendi alıntısında, tolerans; tablo alan etiketi kuralı; JSON `strict=False` ve gerçek hata nedeni | Adım 2 |
| Reranker | Kapalı; Adım 2'de "bulunamadı" ile birlikte yeniden değerlendirilir | B4 düzeltme ölçümü |
| İstemci | Tarayıcıdan erişilen web arayüzü | Tablet + bilgisayar hedefi |

## Bugünkü durum

Uçtan uca hat pilotta çalışıyor. Arama katmanı ölçülüp iyileştirildi (arama p50 56,7 sn'den 0,45 sn'ye). Adım 2'de cevap modeli seçildi ve uygulamaya bağlandı (6 Kasım): Gemma 4 + şema c150b-J + ikili yol varsayılan hat. Cevap akışlı alınıyor ve öğe başına doğrulanıyor; ekranda akarak gösterim (gri "doğrulanıyor") henüz yok. Kod GitHub'da, 455 test geçiyor.

| Tarih | Ne yapıldı | Sonuç |
| --- | --- | --- |
| 6 Kasım | Adım 2 kararı ve bağlama | Gemma 4 + şema c150b-J + ikili yol uygulamada varsayılan; duman testinin kapıları geçti; JUKI tek seferlik doğrulama yapıldı. Adım 2 harcaması ~1,82 $ (3,0 $ sınırı) |
| 3 Kasım | B3b kesinti kontrolü, push | Veri kaybı yok; 1M indeksin %93'ü hazır (932.112 parça) |
| 27 Ekim | B3 hazırlığı | 1M parçalık kalabalık korpusu, yük testi betikleri, internetsiz sunucu paketi |
| 27 Ekim | B4: lokal ve bulut karşılaştırması | Yeni varsayılan bge-m3 + BM25, rerank kapalı; hit@5 0,89; bulut harcaması \~0,9 $ |
| 23 Ekim | B0–B2.5: arama benchmark'ı | Reranker'daki gizli tekrar hesaplama giderildi; Qdrant sunucu modu, yetki filtresi, veri kalitesi düzeltmeleri |
| 16 Ekim | Pilot, ikinci dönem | VLM şekil açıklaması, tablo kontrolü, hata kodu tam eşleşme; JUKI görülmemiş doküman testi |
| 10–13 Ekim | Pilot, birinci dönem | Uçtan uca lokal hat; arama 12/12 doğru sayfa, cevap 9/18 doğru (7B model yetersiz) |
| 9 Ekim | Araştırma ve sentez | İki hatlı mimari, altı katmanlı doğruluk güvencesi, hibrit veri güvenliği |

Ayrıntılar: `PILOT-RAPORU.md`, `Pilot/eval/bench/` altındaki aşama raporları.

## Yol haritası

Benchmark kapandıktan sonraki ilk iş cevap modelinin seçilmesidir, çünkü K1'in en uzak ölçütü olan doğru "bulunamadı" oranı buna bağlıdır. Sunucu ölçümleri (B3a, B3c) sunucu gelince paralel yürür.

&#91;embedded content: yol haritası · 6 adım, 1 kapı, paralel sunucu ölçümleri\]

B5'in parametre ayarı (Optuna) onaylı soru seti hazır olunca yapılır; "bulunamadı" ile ilgili rerank ve eşik denemeleri Adım 2'ye alınmıştır. Her adım bir özetle biter ve onaydan sonra sonrakine geçilir.

## Açık kararlar

Bu kararlar ilerlemeyi bugün durdurmuyor. Her biri, engellediği adıma gelmeden önce kapanmalı.

| No | Karar | Muhatap | Engellediği adım |
| --- | --- | --- | --- |
| A1 | ~~Hangi LLM?~~ **Kapandı (2026-11-06):** Gemma 4 26B A4B, şema c150b-J, DeepInfra birincil | Geliştirme ekibi | Adım 2 sonu |
| A2 | Yanlış değer toleransı kesinleşiyor mu; soru setini gerçek veride kim kontrol edecek? | Kalite yönetimi | Adım 6 |
| A3 | VLM, STT ve TTS sunucuda mı, ZDR'li bulutta mı? | Geliştirme ekibi | Adım 5 |
| A4 | Departmanlar arası paylaşımda karşı departman yetkilisinin onayı gerekli mi? | Departmanlar, BT | Adım 4 |
| A5 | Giriş nasıl yapılacak: şirket hesabı (tek oturum açma) mı, ayrı hesap mı? | BT | Adım 3 |
| A6 | Üretim sunucusu: B3a/B3c'de ölçülen sunucu mu, ayrı bir sunucu mu? | BT | Adım 3 |
| A7 | ~~Ağ kesilirse ne olacak?~~ **Kapandı (2026-11-06):** "servis şu an kullanılamıyor" uyarısı ve bulunan kaynaklar; yerel modele otomatik düşüş yok (yerel model yalnız elle açılan geri alma anahtarı, bir sürüm) | BT, kullanıcılar | Adım 3 |
| A8 | Denetim kayıtları ne kadar saklanacak, kim görecek? | BT, hukuk | Adım 6 |
| A9 | Müşteri sözleşmeleri, parçaların ZDR'li buluta gönderilmesine izin veriyor mu? | Hukuk | Adım 6 |
| A10 | Kodlar atölyede nasıl okunuyor; sesli cevap ne uzunlukta olmalı? | Kullanıcılar | Adım 5 |
| A11 | (Uygulandı, 2026-11-06: bağlanan hatta model ve sağlayıcı yapılandırmadan) Model değişikliği yalnız yapılandırma değişikliği mi olacak? Önerilen ilke: Bir model ölçüm setinden kod değişmeden geçmiyorsa elenir, ona özel yama yazılmaz; ortak biçim sorunları yapılandırılmış cevap şemasıyla çözülür ([Adım 2 planı §15–16](../Pilot/eval/bench/adim2/plan_cevap_modeli_2026-11-05.md)) | Geliştirme ekibi | Adım 2 sonu |

## Kapsam dışı ve terimler

**İlk sürümde yok:** genel sohbet ve dokümanlarda olmayan konularda genel bilgi verme; dokümanların çevrilmesi; kullanıcının kendi dokümanını yüklemesi (yalnız departman yetkilisi yükler); internetsiz tablette çalışma; tablete yüklenen yerel uygulama (erişim tarayıcıdan).

| Terim | Anlamı |
| --- | --- |
| Parça (chunk) | Dokümanın aramada tek birim olarak kullanılan bölümü |
| hit@1, hit@5 | Doğru sayfanın ilk 1 ya da ilk 5 sonuç içinde olduğu soru oranı |
| p50, p95 | Soruların %50'sinin ya da %95'inin bu sürenin altında kaldığı süre |
| RRF | Birden fazla arama sonucunu sıralarına göre birleştirme yöntemi |
| ZDR | Zero Data Retention: sağlayıcının gönderilen veriyi saklamaması |
| K1 | Gerçek veriye geçmeden geçilmesi gereken doğruluk kapısı. K2: aynı noktadaki yetki (%100) ve süre bütçesi kapısı |
| B0–B5 | Arama benchmark'ının aşamaları |
