"""Soru seti genişletme taslağı: aday sorular, ağırlık zor sorularda. Kullanıcı onayından önce ölçüme girmez.

Kullanım (Pilot klasöründe): python -m bench.aday_sorular   -> eval/aday_sorular.json ve eval/aday_sorular.md
- Beklenen parça (chunk_id) Claude tarafından önerildi; doküman, sayfa ve alıntı chunks.jsonl'den doldurulur.
- Hepsi 'dogrulandi': false; bench.common.load_questions onaysız soruları ölçüme katmaz.
- JUKI (gorulmemis_juki) ayrı tutulan doğrulama seti olduğu için taslağa alınmadı.
- Alanlar: cevap (gerçek cevap; aralık biçimi "a–b birim"), expect_in_answer (cevapta aranacak değerler, aynı biçim),
  ocr_bicimi (kaynakta OCR'ın yazdığı biçim, ör. "3116 to 114"), kanit (cevabı gösteren cümle, parçadan birebir),
  kabul (kabul edilen kaynaklar: doküman + sayfa; çok dilli/çok sayfalı), expect_clarify + olasi_urunler
  (netleştirme beklenen sorular), nf_kontrol ("bulunamadı" sorularında yapılan kaynak kontrolü).
- Etiketler: parafraz, kod_varyant, benzer_bolum, karisan_dokuman, sayi, sekil, tablo, ingilizce, kaynak_ifadesi,
  ters_soru, ocr, bulunamadi, netlestirme, gundelik (kısa/gündelik/yazım hatalı).
"""
import json
from pathlib import Path

from pilot.chunk import read_chunks

EVAL = Path(__file__).resolve().parent.parent / "eval"
NF_PDF = "chunks.jsonl ve PDF metin katmanında arandı (2026-10-27), geçmiyor"


def Q(cid, q, kind, tags, values=(), cevap="", kanit="", ocr="", accept=(), note="", **extra):
    return {"cid": cid, "q": q, "kind": kind, "tags": list(tags), "values": list(values), "cevap": cevap,
            "kanit": kanit, "ocr": ocr, "accept": list(accept), "note": note, **extra}


def NF(q, tags, kontrol, note=""):
    return Q(None, q, "bulunamadı", ["bulunamadi", *tags], nf_kontrol=kontrol, note=note)


def C(q, cids, cevap, tags=(), kanit=""):
    """Netleştirme: ürün/model belirtilmemiş; olası ürünlerin her birinde cevap var."""
    return Q(None, q, "netleştirme", ["netlestirme", *tags], cevap=cevap, kanit=kanit, clarify=list(cids))


DRAFT = [
    # --- Ceket şartnamesi (gl-pd-14-04a) --- A001-A018
    Q("gl-pd-14-04a-00102", "Ceketin kol manşetindeki ayar tırnağı hangi genişlik ve uzunlukta olmalı?", "değer", ["parafraz", "sayi"],
      ["2-1/8", "3-1/8"], "2-1/8 (± 1/8) inç genişlik × 3-1/8 (± 1/8) inç uzunluk", "The sleeve tabs shall be 2-1/8 (± 1/8) inches wide by 3-1/8 (± 1/8) in length"),
    Q("gl-pd-14-04a-00102", "Ceket manşetinde kaç tane ilik açılır?", "değer", ["parafraz"], ["3"], "3 ilik",
      "The main body of the sleeve cuff shall have three (3) buttonholes spaced as per pattern"),
    Q("gl-pd-14-04a-00113", "Ceketteki rütbe yaması cırt bandı kaç inç olmalı?", "değer", ["parafraz", "sayi"], ["2"], "2 × 2 inç (cırt bandın tüylü/loop kısmı)",
      "The rank patch shall be a piece of loop fastener tape, 2-inches wide by 2inches in cut length"),
    Q("gl-pd-14-04a-00113", "Alev almaz (Type II, III) ceketlerde FR tanıtım bandı hangi kolda bulunur?", "değer", ["parafraz"], [],
      "Sol kol manşetinde (giyildiğinde), dışarıdan görünür", "tape FR identification marker (see figure 1) on the left sleeve cuff as worn"),
    Q("gl-pd-14-04a-00185", "Ceketin arka körük (bi-swing) pli üst dikişinde iki sıra arası mesafe ne kadar?", "değer", ["benzer_bolum", "tablo"],
      ["3/16–1/4"], "3/16–1/4 inç (iki sıra)", "Gauge: Two (2) rows 3/16 to 1/4-inch gage apart"),
    Q("gl-pd-14-04a-00190", "Ceket ceplerini otomatik cep makinesiyle takarken üst dikiş kenardan ne kadar içeride olmalı?", "değer", ["benzer_bolum", "tablo"],
      ["1/16–1/8"], "1/16–1/8 inç", "Gauge: 1/16 to 1/8-inch from edge"),
    Q("gl-pd-14-04a-00206", "Ceketin IFF tırnak kapağına cırt bant hangi dikiş tipiyle takılır?", "değer", ["tablo"], ["301"],
      "301 dikiş tipi, LSbj-1 dikiş, kutu dikiş", "Seam type: LSbj-1 | Gauge: Box, 1/8 to 3/16-inch from selvage edge (see IFF pattern template) | Stitch type: 301"),
    Q("gl-pd-14-04a-00221", "Ceketin üst kol ceplerine toplam kaç punteriz atılır?", "değer", ["sayi", "tablo"], ["8"], "8 punteriz (giysi başına)",
      "# of Bar- tacks per garment: 8"),
    Q("gl-pd-14-04a-00321", "Ceket muayenesinde isim ve U.S. Army bantları ne kadar kayarsa kusur sayılır?", "değer", ["parafraz"], ["1/4"],
      "Yatay hizada değilse ya da 1/4 inçten fazla düzensizse (kusur 139)", "Not in horizontal alignment or uneven by more than 1/4-inch"),
    Q("gl-pd-14-04a-00040", "Ceket şartnamesinde ASTM D 5034 neyi ölçen bir test yöntemi?", "değer", ["parafraz"], ["5034"],
      "Kumaşların kopma mukavemeti ve uzaması (grab test); şartnamede düğme kopma/çekme testinde de kullanılıyor",
      "ASTM D 5034 - Standard Test Method for Breaking Strength and Elongation of Textile Fabrics (Grab Test)",
      accept=["gl-pd-14-04a-00351"]),
    Q("gl-pd-14-04a-00379", "Ceket şartnamesine göre permetrin geri kazanımı en az yüzde kaç olmalı?", "değer", ["karisan_dokuman", "sayi"], ["95"],
      "%95 veya üzeri", "Permethrin recovery must be 95% or greater", accept=["gl-pd-14-04a-00382"]),
    Q("gl-pd-14-04a-00421", "Ceket ısırma testinde gönüllünün test bölgesi kolun neresidir?", "değer", ["benzer_bolum", "karisan_dokuman"], ["1/2"],
      "Bilekten dirsekten yaklaşık 1/2 inç öncesine kadar", "the region from the wrist to approximately 1/2-inch before the elbow"),
    Q("gl-pd-14-04a-00294", "Bitmiş ceket için toksisite şartı nedir?", "prosedür", [], [],
      "Sağlığa zarar vermemeli, uzun süreli doğrudan cilt temasıyla uyumlu olmalı; EPA'nın insan kanserojeni saydığı kimyasallar kullanılamaz",
      "The finished coat shall not present a health hazard"),
    Q("gl-pd-14-04a-00151", "Class 2 ceketlerde böcek koruma etiketi nereye dikilir?", "değer", ["parafraz"], [],
      "Ceketin içine, sol göğüs cebinin altına (giyildiğinde)", "shall be stitched on inside of coat under the left chest pocket (as worn)"),
    Q("gl-pd-14-04a-00090", "Ceketin yaka tipi ve ön kapanışı nasıl?", "değer", ["parafraz"], [],
      "Dik (band) yaka; önde çift sürgülü fermuar ve ikincil cırt bant kapanış", "single-breasted front with a slide fastener (double slider) closure and a secondary hook and loop fastener tape closure; a band collar"),
    Q("gl-pd-14-04a-00560", "Ceket yaka çiziminde rütbe yaması halkası nasıl gösteriliyor?", "şekil", ["sekil"], [],
      "Ön patta, üstte ve altta 'Box X' dikişli iki kare arasında taralı dikdörtgen olarak (Figure 3, ölçeksiz)",
      "FIGURE 3. Coat Collar, Army Combat Uniform", note="Şekil görüntüsünden doğrulandı: 'Box \"X\" stitch' ve 'Rank Patch Loop' etiketleri görüntüde var, PDF metin katmanında yok"),
    Q("gl-pd-14-04a-00071", "Uzun boy ceketlerde 36 beden ön fermuar uzunluğu kaç inç?", "değer", ["tablo", "sayi"], ["17"], "17 inç",
      "Length: Long | Size 30: 16 | Size 33: 16 | Size 36: 17"),
    Q("gl-pd-14-04a-00002", "Type II ceket kumaşının elyaf karışımı nedir?", "değer", ["sayi"], ["65/25/10"], "%65 rayon / %25 para-aramid / %10 naylon, ripstop, alev almaz",
      "Type II - 65/25/10 Rayon/Para-Aramid/Nylon Ripstop Flame Resistant"),
    # --- Pantolon şartnamesi (gl-pd-07-14a, OCR'lı) --- A019-A036
    Q("gl-pd-07-14a-00092", "Pantolon iliklerinde inç başına kaç dikiş olmalı?", "değer", ["benzer_bolum", "sayi"], ["52–56"], "52–56 dikiş/inç (punteriz dahil)",
      "possessing 52-56 stitches per inch, including tack"),
    Q("gl-pd-07-14a-00092", "How many stitches per inch are required for trouser buttonholes?", "değer", ["ingilizce", "benzer_bolum"], ["52–56"],
      "52–56 stitches per inch, including tack", "possessing 52-56 stitches per inch, including tack"),
    Q("gl-pd-07-14a-00092", "Pantolon iliklerinin kesim boyu ne kadar?", "değer", ["parafraz"], ["3/4–7/8"], "3/4–7/8 inç", "The cut lengths shall be 3/4 to 7/8 inch"),
    Q("gl-pd-07-14a-00088", "Pantolonun ön yan cep ağzı kaç inç olmalı?", "değer", ["sayi", "ocr"], ["6–7-1/4"], "6–7-1/4 inç (punterizler arası)",
      "pocket openings measuring not less than 6 inches and not more than 7-114 inches between bartacks", ocr="7-114"),
    Q("gl-pd-07-14a-00172", "Pantolon cep kapaklarındaki punterizler kaç dikişli olur?", "değer", ["benzer_bolum", "tablo"], ["36"], "36 dikiş (punteriz başına)",
      "Size of Tack: 5/8 | Stitches per Tack: 36"),
    Q("gl-pd-07-14a-00172", "Pantolon cep kapağı punterizinin boyu ne kadar?", "değer", ["tablo"], ["5/8"], "5/8 inç", "Size of Tack: 5/8"),
    Q("gl-pd-07-14a-00148", "Pantolon cep kapaklarının üst dikişi kenardan ne kadar içeride olmalı?", "değer", ["benzer_bolum", "ocr", "tablo"],
      ["3/16–1/4"], "3/16–1/4 inç (OSf-1, 301 dikiş)", "Seam type: OSf-1 | Gage: 3116 to 114 inch from edge | Stitch type: 301", ocr="3116 to 114"),
    Q("gl-pd-07-14a-00160", "Pantolonda cırt bant kenar şeridinden ne kadar içeriden dikilir?", "değer", ["karisan_dokuman", "parafraz", "ocr"],
      ["1/8–3/16"], "1/8–3/16 inç (bağlı kenar şeridinden)", "Gage: 118 to 3/16 inch fi'om the bound selvage", ocr="118 to 3/16",
      accept=["gl-pd-07-14a-00082"]),
    Q("gl-pd-07-14a-00144", "Pantolonun fermuar (fly) dikişi J-dikişinin ne kadar üstünde bitmeli?", "değer", ["parafraz", "ocr"], ["3/8–1/2"], "3/8–1/2 inç",
      "shall end 3/8 - 112 inch above J-stitch", ocr="3/8 - 112"),
    Q("gl-pd-07-14a-00135", "Pantolon iç bacağında 5 iplik emniyet dikişi kullanılırsa kalıp nasıl ayarlanır?", "prosedür", ["parafraz", "ocr"], ["3/8"],
      "Kalıplar 1/2 inç çift iğne dikişi yerine 3/8 inç dikiş payına göre ayarlanır",
      "contractor must adjust pattems for 3/8-inch gauge in lieu of 112 inch double needle seams", ocr="112 inch"),
    Q("gl-pd-07-14a-00050", "Pantolonda 20 yıkamadan sonra permetrin miktarı en az ne olmalı?", "değer", ["sayi", "tablo"], ["0.025"], "En az 0,025 mg/cm² (en çok 0,130)",
      "After 20 launderings | Min: mg/cm2: 0.025 | Max: mg/cm2: 0.130"),
    Q("gl-pd-07-14a-00297", "Pantolon ısırma testinde kollar böcek kafesinde kaç dakika tutulur?", "değer", ["ocr", "benzer_bolum"], ["15"], "15 dakika",
      "exposed to a cage of insects for IS min", ocr="IS min"),
    Q("gl-pd-07-14a-00253", "Pantolon permetrin testinde numuneler kaç inç çapında kesilir?", "değer", ["sayi"], ["3"], "3 inç çapında (45,6037 cm²), her koşul için üç numune",
      "select three 3 inch diameter specimens"),
    Q("gl-pd-07-14a-00132", "Pantolon barkodundaki NSN kaç haneli?", "değer", ["sayi"], ["13"], "13 haneli NSN (UPC 12 haneli)", "The bar coding element shall be a 13 digit national stock number (NSN)"),
    Q("gl-pd-07-14a-00096", "Pantolon beden etiketi nereye dikilir?", "değer", ["benzer_bolum"], [], "İç bel bandı dikişinin altına, dikişe yakalanarak; dikiş baskıyı örtmemeli",
      "shall be sewn and caught in the bottom of the inside waistband seam"),
    Q("gl-pd-07-14a-00230", "Pantolon temizlik muayenesinde kaç iplikten fazlası kusur sayılır?", "değer", ["sayi", "ocr"], ["3"],
      "1/4 inçten uzun, kesilmemiş 3'ten fazla iplik (ayrıca 1/4 inçten küçük leke)", "excessive thread (more than 3) over 114 inch not trimmed or removed", ocr="114 inch"),
    Q("gl-pd-07-14a-00060", "Pantolonda cırt bant genişliklerinin toleransı ne kadar?", "değer", ["parafraz", "sayi"], ["1/32"], "± 1/32 inç",
      "The tolerance for all widths specified shall be (± 1/32) inch"),
    Q("gl-pd-07-14a-00313", "Pantolon çiziminde hangi ölçüler verilmiş?", "şekil", ["sekil"], ["14 1/2", "12 1/4", "10 1/2"], "14 1/2, 12 1/4 ve 10 1/2 inç",
      "14 1/2 inches ----- 12 1/4 inches y -4-1(--10 1/2 inches",
      note="Ölçüler şeklin OCR metninden; VLM açıklamasındaki '±' tolerans ifadesi yanlış, kaynakta yok"),
    # --- Brother S-7300A --- A037-A063
    Q("brother-s7300a-00409", "S-7300A'da E-050 hatası ne anlama gelir?", "kod", ["kod_varyant", "benzer_bolum"], ["E050"],
      "Dikiş başlarken makine kafası geriye yatık algılandı; gücü kapatıp kafayı yerine getirin, P2 konektörünü kontrol edin",
      "Code: E050 | Cause: Machine head is detected as being tilted back when start sewing."),
    Q("brother-s7300a-00409", "S-7300A ekranında E 050 yazıyor, ne yapmalıyım?", "kod", ["kod_varyant"], ["E050"],
      "Gücü kapatıp makine kafasını yerine getirin; P2 konektörünün bağlantısını kontrol edin", "Turn off the power, and then return the machine head to its original position"),
    Q("brother-s7300a-00413", "S-7300A açılırken E065 veriyor, neden?", "kod", ["kod_varyant"], ["E065"],
      "Açılışta devre dışı bir donanım tuşuna basılıydı; gücü kapatıp yeniden açın", "Code: E065 | Cause: A disabled hardware key was being pressed when the power was turned on."),
    Q("brother-s7300a-00421", "S-7300A'da E111 hata kodu ne demek?", "kod", [], ["E111"],
      "Motor durduğunda iğne yukarı durma konumu belirlenen değeri aştı; motor ya da iplik kesme mekanizması sıkı mı kontrol edin",
      "Code: E111 | Cause: The needle up stop position exceeded the specified value when the sewing machine motor stopped."),
    Q("brother-s7300a-00437", "S-7300A'da açılışta panel bağlantısı algılanmazsa hangi hata kodu çıkar?", "kod", ["ters_soru"], ["E400"],
      "E400 (P2 konektörünü kontrol edin)", "Code: E400 | Cause: Panel connection was not detected when power was turned on."),
    Q("brother-s7300a-00447", "S-7300A'da E-700 hatasında ne kontrol edilmeli?", "kod", ["kod_varyant"], ["E700"],
      "Açılışta güç kaynağı geriliminde anormal yükselme; gücü kapatıp şebeke gerilimini kontrol edin",
      "Code: E700 | Cause: Abnormal rise in power supply voltage was detected when power was turned on."),
    Q("brother-s7300a-00444", "S-7300A'da ayarlar kendiliğinden sıfırlandı ve E442 göründü, ne yapmalıyım?", "kod", ["parafraz"], ["E442"],
      "Yedek bellek verisi bozuk olduğu için ayarlar sıfırlandı; gücü kapatıp yeniden açın",
      "Code: E442 | Cause: Back up memory (main internal P.C. board) data was abnormal, so settings were initialized."),
    Q("brother-s7300a-00369", "S-7300A'da iplik kesildikten sonra üst ipliğin standart kuyruk uzunluğu kaç mm?", "değer", ["benzer_bolum"], ["25–30"],
      "25–30 mm (ön gerdirme ile ayarlanır)", "The standard upper thread trailing length is 25 to 30 mm"),
    Q("brother-s7300a-00401", "S-7300A -3 tipinde çağanoz ile masura kovanı tutucusu arasındaki boşluk ne olmalı?", "değer", ["parafraz", "sayi"],
      ["0.4–0.7"], "0,4–0,7 mm (-3 tipi); -5 tipinde 0,6–1,1 mm", "The clearance should be 0.4 to 0.7 mm (for -[][]3 specifications)"),
    Q("brother-s7300a-00406", "S-7300A'da iplik kesme kamı ayarlanırken iğne mili en alt konumdan kaç mm kaldırılır?", "değer", ["benzer_bolum", "sayi"], ["6"],
      "6 mm", "raise the needle bar 6 mm from its lowest position"),
    Q("brother-s7300a-00128", "S-7300A -3 tipinin en yüksek dikiş hızı nedir?", "değer", ["benzer_bolum"], ["5000"], "5000 dikiş/dk (-3 tipi); -5 tipinde 4500",
      "-3 specifications: 220 - 5000 sti/min"),
    Q("brother-s7300a-00160", "S-7300A'da başlangıç punterizinde B dikiş sayısı hangi aralıkta ayarlanır?", "değer", ["tablo"], ["1–19"],
      "1–19 dikiş (birim 1, başlangıç değeri 1)", "No. of stitches B | Setting value: 1 - 19 stitches"),
    Q("brother-s7300a-00240", "S-7300A'da alt iplik sayacı sıfırın altına düşünce makine ne yapar?", "prosedür", ["parafraz"], ["5"],
      "Dikiş durunca uyarı sesi 5 kez öter, uyarı mesajı çıkar, pedala basılsa da dikmez; masura değişip Reset ile sayaç geri gelir",
      "the warning buzzer sounds 5 times (1 second on/1 second off), and a lower thread counter warning message is displayed"),
    Q("brother-s7300a-00247", "S-7300A'da aydınlatma LED parlaklığı hangi aralıkta ayarlanır?", "değer", ["benzer_bolum"], ["1–9"], "1–9",
      "The setting range is from 1 to 9."),
    Q("brother-s7300a-00264", "S-7300A'ya en fazla kaç farklı desen dikişi kaydedilebilir?", "değer", ["sayi"], ["5"], "5 (DS-1 – DS-5); her biri en çok 8 grup",
      "Up to 5 different types of design stitches (DS-1 to DS-5)"),
    Q("brother-s7300a-00302", "S-7300A'da açılışta panelin otomatik kilitlenmesi hangi bellek anahtarıyla kapatılır?", "değer", ["ters_soru", "tablo"], ["311"],
      "Bellek anahtarı 311 (OFF: kapalı, başlangıç ON)", "No.: 311 | Setting range: OFF, ON | Initial value: ON"),
    Q("brother-s7300a-00474", "S-7300A'da dikiş dalgalı ve düzensiz çıkıyor, olası nedenler neler?", "arıza", ["parafraz"], [],
      "Baskı ayağı basıncı zayıf, transport dişlisi alçak ya da masura çizik", "Problem: Uneven seam"),
    Q("brother-s7300a-00469", "S-7300A'da dikişte ilmek (halka) oluşuyor, ne yapmalıyım?", "arıza", ["parafraz"], [],
      "İplik yolunu cilalayın, masuranın rahat dönüp dönmediğini kontrol edin; özel lokus 1'i deneyin", "Problem: Loops appear in seam."),
    Q("brother-s7300a-00080", "S-7300A'da ayağımı pedala koyunca makine yavaş dönmeye başlıyor, ne yapmalıyım?", "arıza", ["parafraz"], [],
      "Pedal yayının pedal koluna takıldığı konumu (a–d) değiştirerek basma hassasiyetini artırın",
      "adjust the position (a to c) at which the treadle spring (1) is hooked onto the treadle lever"),
    Q("brother-s7300a-00068", "S-7300A topraklama vidasının önerilen sıkma torku nedir?", "değer", ["sayi"], ["1.0"], "1,0 ± 0,1 N·m",
      "Recommended tightening torque 1.0±0.1 N.m"),
    Q("brother-s7300a-00375", "S-7300A'da çağanoz ve masura kovanı nasıl temizlenir?", "prosedür", ["parafraz"], [],
      "İğne plakasını sökün, transport dişlisini fırçalayın; kafayı yatırın, masura kovanını çıkarın, çağanozu yumuşak bezle silin",
      "Wipe off any dust from the rotary hook (5) with a soft cloth"),
    Q("brother-s7300a-00396", "S-7300A'da iğne mili yüksekliği neye göre ayarlanır?", "prosedür", ["benzer_bolum"], [],
      "İğne mili en alttayken üzerindeki (a) çizgisi iğne mili burcunun alt kenarıyla hizalanmalı",
      "Reference line (a) on the needle bar (1) should be aligned with the lower edge of the needle bar bush (2)"),
    Q("brother-s7300a-00434", "S-7300A'da E210 hatası ne demek?", "kod", ["kod_varyant"], ["E210"],
      "Açılışta transport motoru başlangıç konumu algılanmadı; transport mekanizmasını ve P4 konektörünü kontrol edin",
      "E210 Feed motor origin is not detected when power is turned on.",
      note="İlk taslakta yanlışlıkla 'bulunamadı' idi: satır s.99'da tablo başlığıyla birleşik ('Code Cause Remedy: E210')"),
    Q("brother-s7300a-00435", "S-7300A'da E-211 kodu çıktı, ne yapmalıyım?", "kod", ["kod_varyant"], ["E211"],
      "Dikiş sırasında transport motorunda anormal çalışma; transport mekanizmasını ve motor/P4 konektörünü kontrol edin",
      "E211 Abnormal feed motor operation detected during sewing.",
      note="İlk taslakta yanlışlıkla 'bulunamadı' idi: kod s.99'da var"),
    # --- Brother S-7300B --- A064-A080
    Q("brother-s7300b-00437", "S-7300B'de E050 hatası ne anlama gelir?", "kod", ["benzer_bolum", "karisan_dokuman"], ["E050"],
      "Dikiş başlarken makine kafası geriye yatık algılandı; kafayı yerine getirin, P2 konektörünü kontrol edin",
      "Code: E050 | Cause: Machine head is detected as being tilted back when start sewing."),
    Q("brother-s7300b-00463", "S-7300B açılışta E210 veriyor, ne kontrol etmeliyim?", "kod", [], ["E210"],
      "Transport mekanizmasını ve transport motoru konektörü ile P4'ü", "Code: E210 | Cause: Feed motor origin is not detected when power is turned on."),
    Q("brother-s7300b-00464", "S-7300B dikiş sırasında E-211 veriyor, neden?", "kod", ["kod_varyant"], ["E211"],
      "Dikiş sırasında transport motorunda anormal çalışma algılandı", "Code: E211 | Cause: Abnormal feed motor operation detected during sewing."),
    Q("brother-s7300b-00483", "S-7300B'de E705 hatası ne demek?", "kod", [], ["E705"], "Güç kaynağı geriliminde anormal düşüş; şebeke gerilimini kontrol edin",
      "Code: E705 | Cause: Abnormal drop in power supply voltage was detected."),
    Q("brother-s7300b-00150", "S-7300B'de başlangıç punteriz dikiş hızının varsayılan değeri kaç?", "değer", ["benzer_bolum", "tablo"], ["1800"],
      "1800 dikiş/dk (aralık 220–3000, birim 100)", "Setting value: 220 - 3000 sti/min | Setting units: 100 sti/min | Initial value: 1800"),
    Q("brother-s7300b-00249", "S-7300B'de dikiş adımının varsayılan değeri ve ayar birimi nedir?", "değer", ["tablo"], ["2.00", "0.05"],
      "Başlangıç 2,00 mm; birim 0,05 mm (aralık 0,05–5,00 mm)", "Setting units: 0.05 mm | Initial value: 2.00"),
    Q("brother-s7300b-00393", "S-7300B'de iplik kesildikten sonra üst ipliğin standart kuyruk uzunluğu kaç mm?", "değer", ["benzer_bolum"], ["30–45"],
      "30–45 mm (Premier tipinde 25–30 mm)", "The standard length for the upper thread trailing length is 30 to 45 mm, or 25 to 30 mm for Premier specifications."),
    Q("brother-s7300b-00393", "What is the standard upper thread trailing length on the S-7300B after thread trimming?", "değer", ["ingilizce", "benzer_bolum"],
      ["30–45"], "30–45 mm (25–30 mm for Premier specifications)", "The standard length for the upper thread trailing length is 30 to 45 mm"),
    Q("brother-s7300b-00423", "S-7300B -3 tipinde çağanoz ucu, iğne mili kaç mm yükselince iğnenin ortasına gelmeli?", "değer", ["parafraz", "sayi"], ["1.8"],
      "1,8 mm (-3 tipi); -5 tipinde 2,2 mm", "when the needle bar (1) moves up 1.8 mm (for -[][]3 specifications)"),
    Q("brother-s7300b-00430", "S-7300B'de iplik kesme kamı ayarlanırken iğne mili en alt konumdan kaç mm kaldırılır?", "değer", ["benzer_bolum", "sayi"], ["5"],
      "5 mm", "Raise the needle bar 5 mm from its lowest position"),
    Q("brother-s7300b-00316", "S-7300B'de dizlik hareket hızı hangi bellek anahtarıyla ayarlanır?", "değer", ["ters_soru", "tablo"], ["591"],
      "Bellek anahtarı 591 (1–5, başlangıç 4)", "No.: 591 | Setting range: 1 - 5 | Initial value: 4"),
    Q("brother-s7300b-00283", "S-7300B'de başlangıç punterizi B adım düzeltme oranı hangi bellek anahtarında?", "değer", ["ters_soru", "tablo"], ["202"],
      "Bellek anahtarı 202 (%50–150, başlangıç 100)", "No.: 202 | Setting range: 50 - 150% | Initial value: 100"),
    Q("brother-s7300b-00256", "S-7300B'de kısayol tuşlarına başlangıçta hangi işlevler atanmış?", "değer", [], [],
      "Başlangıç punterizi, bitiş punterizi, yavaş başlangıç ve iplik kesme kilidi", "Initially, the start backtack key, end backtack key, slow start key and thread trimming lock key are assigned."),
    Q("brother-s7300b-00507", "S-7300B'de dikişin başında atlama ve iplik çözülmesi oluyor, ne yapmalıyım?", "arıza", ["parafraz"], [],
      "İplik çekme yayı gerginliğini/aralığını azaltın, ön gerdirmeyi ayarlayın, kesme bıçaklarını bileyin", "Problem: Skipped stitches at sewing start"),
    Q("brother-s7300b-00374", "S-7300B -3 tipinde 4000 dev/dk hızda dikiş adımı en fazla kaç mm olabilir?", "değer", ["tablo", "sayi"], ["3.0"], "3,0 mm (lokus 1)",
      "-3 specifications 5000sti/min / 2.0 4000sti/min / 3.0"),
    Q("brother-s7300b-00230", "S-7300B'de alt iplik sayacı ne zaman azalır?", "prosedür", ["parafraz"], ["0.1"],
      "Dikiş sayısı × adım 0,1 m'ye ulaştıkça 0,1 azalır; ekran pedal nötre dönünce güncellenir",
      "reduced by 0.1 each time the number of stitches x sewing pitch reaches 0.1 m"),
    Q("brother-s7300b-00515", "S-7300B'de punteriz kenarı hizalı çıkmıyor, ne yapmalıyım?", "arıza", ["parafraz"], [],
      "Transport dişlisi yüksekliğini kontrol edin, artırın", "Is the height of the feed dog correct? Increase the feed dog height."),
    # --- Strickland, terzilik kitabı --- A081-A090
    Q("strickland-1956-00106", "Terzilik kitabına göre makine dikişinde inç başına kaç dikiş kullanılmalı?", "değer", ["kaynak_ifadesi", "karisan_dokuman"], ["15–20"],
      "15–20 dikiş/inç; kalın kumaşta daha uzun dikiş", "Use 15 to 20 stitches per inch, the longer stitch for bulky materials."),
    Q("strickland-1956-00106", "Kalın kumaşlarda makine dikiş boyu nasıl seçilir?", "değer", ["parafraz", "karisan_dokuman"], [],
      "Daha uzun dikiş (15–20 dikiş/inç aralığının uzun ucu); önce artık kumaşta çift kat denenir",
      "Use 15 to 20 stitches per inch, the longer stitch for bulky materials."),
    Q("strickland-1956-00143", "Fransız etek ucu (French hem) nasıl yapılır?", "prosedür", [], [],
      "Etek ucu işaretlenip ters yüze katlanır, kenara dik iğnelenir, denenir; kumaş saçaklanmıyorsa kenar zikzaklanıp teyellenir",
      "French hem: After hem is marked, fold it to wrong side along marked edge"),
    Q("strickland-1956-00173", "Uzun kruvaze paltoda düğmelenmeyen alt kat nasıl sabitlenir?", "prosedür", ["parafraz"], ["1"],
      "Astar ya da yaklaşık 1 inç genişliğinde grogren kurdeleden bağcıkla", "held in place by a tie made of the lining, or of matching grosgrain ribbon about 1 inch wide"),
    Q("strickland-1956-00182", "Klapede pad dikişine kırım çizgisinin ne kadar gerisinden başlanır?", "değer", ["parafraz"], ["1"], "1 inç gerisinden",
      "start the pad stitch 1 inch behind the break line"),
    Q("strickland-1956-00196", "Gömme cepler neden tela ile desteklenir?", "prosedür", [], [], "Kumaşa binen aşırı gerilimi önlemek için; dikiş hattı boyunca tersten",
      "This canvas prevents too great strain on the fabric."),
    Q("strickland-1956-00224", "Ok başı punteriz (arrowhead) nasıl yapılır?", "prosedür", ["karisan_dokuman"], [],
      "Üçgen teyelle işaretlenir; ilik ipliğiyle tabandan başlanıp karşı köşeye tabana paralel dikişlerle doldurulur",
      "Mark the arrowhead by basting a triangle at the desired position."),
    Q("strickland-1956-00158", "İlik aralıklarını doğru işaretlemek için ne yapılır?", "prosedür", ["parafraz"], [],
      "Uzun ve kısa teyellerle 'merdiven' yapılır: orta ön teyeli, iliğin bir ucu ve ilik boyu teyelle işaretlenir",
      "To be accurate in spacing the buttonholes, make a ladder, using long and short bastings."),
    Q("strickland-1956-00296", "Terzilik kitabına göre pantolon cebinin yün yüz parçası kaç inç kesilir?", "değer", ["karisan_dokuman", "kaynak_ifadesi"], ["10", "3"],
      "10 × 3 inç", "Wool facing 10 inches by 3 inches."),
    Q("strickland-1956-00014", "Bengalin kumaş hangi giysiler için uygundur?", "değer", [], [], "Palto ve takım (poplin benzeri rib dokuma)",
      "Bengaline: Rib weave similar to poplin. For coats or suits."),
    # --- Granovsky, onarım kitabı --- A091-A100
    Q("granovsky-1986-00190", "Parçaları yıkamak için sabun çözeltisinde litre başına kaç gram sabun kullanılır?", "değer", ["sayi"], ["25"], "Litre suya 25 g sabun",
      "a soap solution (25 g of soap per liter of water)"),
    Q("granovsky-1986-00088", "Kalın cidarlı dökme demir parçaları kaynatırken çelik pim çapı nasıl seçilir?", "değer", ["parafraz", "sayi"], ["0.3–0.4"],
      "d = (0,3–0,4) × kırılma yerindeki parça kalınlığı (b)", "d = (0.3...0.4)b", ocr="(0.3...0.4)b"),
    Q("granovsky-1986-00475", "Ring iplik makinesinde kondansatörün toplam stroku kaç mm olmalı?", "değer", ["sayi"], ["18–19"], "18–19 mm",
      "The total stroke of the condenser should be 18-19 mm."),
    Q("granovsky-1986-00504", "Birinci tip çözgü makinesinin tamburunda koni açısı hangi aralıkta değişir?", "değer", ["sayi"], ["6–26"], "6–26°",
      "a cone the angle of which changes from 6 to 26°"),
    Q("granovsky-1986-00606", "Dokuma tezgâhında orta onarım ne sıklıkla yapılır ve kaç kişi yapar?", "değer", ["parafraz"], [],
      "Yılda en az iki kez (aşırı aşınmada daha sık), en çok bir vardiya, iki kişilik ekip",
      "carried out according to the schedule at. least twice a year", ocr="at. least"),
    Q("granovsky-1986-00690", "Mekik kutusunda mekik yokken çözgü koruyucu uçları pedlerin kaç mm üstünde olmalı?", "değer", ["parafraz", "sayi", "ocr"], ["1–1.5"],
      "1–1,5 mm", "the warp protector nibs must be 1-1.5 m m above the edges of the pads", ocr="1-1.5 m m"),
    Q("granovsky-1986-00761", "Topuk konisinin elektrik kıvılcımıyla doldurulmasında katman kalınlığı kaç mm?", "değer", ["sayi", "ocr"], ["0.2"], "0,2 mm",
      "the thickness of the built-up layer is 0.2 m m", ocr="0.2 m m"),
    Q("granovsky-1986-00153", "Granovsky'ye göre santrifüj kavrama ne zaman devreye girer?", "değer", ["kaynak_ifadesi"], [],
      "Önceden belirlenen dönme hızı aşıldığında milleri otomatik bağlar",
      "Centrifugal clutches automatically connect the shafts only when the preset rotational speed is exceeded."),
    Q("granovsky-1986-00120", "Tekstil makinesi parçalarında bakır kaplama ne için kullanılır?", "değer", ["parafraz"], [],
      "Rulman bilezikleri, yatak astarları ve burçların dış yüzeyini doldurmak, sonsuz vida aşınmasını gidermek; krom kaplamaya alt katman",
      "Copperplatingis used to hard face the outer surfaces of rings in antifriction bearings", ocr="Copperplatingis"),
    Q("granovsky-1986-00645", "Yağ damperi ayar düzeneğindeki lamba kaç voltluk?", "değer", ["sayi"], ["3.5"], "3,5 V", "a lamp 3 for 3.5 V"),
    # --- Mr. Coffee --- A101-A108
    Q("mrcoffee-2003-00054", "Kahve makinesinde gecikmeli demleme saati nasıl ayarlanır?", "prosedür", ["parafraz"], [],
      "Saat modundayken SET DELAY'e basın; sarı DELAY BREW ışığı yanıp sönerken HOUR ve MINUTE ile saati girin",
      "simply press the SET DELAY button (Figure 3) and, while the DELAY BREW yellow light is flashing, set the brew time"),
    Q("mrcoffee-2003-00055", "Kahve makinesinin su filtresi klorun yüzde kaçını giderir?", "değer", ["sayi"], ["97"], "%97'ye kadar",
      "removing up to 97% of the chlorine from the water"),
    Q("mrcoffee-2003-00071", "Kahve makinesinde bir fincan kaç ons su sayılıyor?", "değer", ["sayi"], ["5"], "5 ons", "(1 cup equals 5 ounces)"),
    Q("mrcoffee-2003-00100", "Kahve makinesinin kirecini temizlerken temizleyici yerine ne kadar sirke kullanılabilir?", "değer", ["parafraz"], ["4", "20"],
      "4 fincan (20 fl. oz.) seyreltilmemiş beyaz sirke", "4 cups or 20 fl. oz. of undiluted, white household vinegar may be used as a substitute"),
    Q("mrcoffee-2003-00113", "Cam sürahideki beyaz kireç lekeleri nasıl çıkarılır?", "prosedür", ["parafraz"], ["20"],
      "Sürahiyi yarı su yarı sirkeyle doldurup yaklaşık 20 dakika bekletin, sonra yıkayın", "a solution of equal parts water and vinegar and let the solution stand in the decanter for approximately 20 minutes"),
    Q("mrcoffee-2003-00125", "Sürahi ısıtma plakasından 30 saniyeden uzun alınırsa ne olur, ne yapmalıyım?", "arıza", ["tablo"], ["30"],
      "Taşma olabilir: makineyi kapatıp fişten çekin, soğumasını bekleyin, dökülenleri silin; sıcak sürahiyi ıslak plakaya koymayın",
      "The decanter was removed from the warmer plate for more than 30 seconds."),
    Q("mrcoffee-2003-00039", "Programlanabilir kahve makinelerinde temizleme döngüsü ne kadar sürer?", "değer", ["karisan_dokuman"], ["45–60"], "45–60 dakika",
      "El ciclo completo tomará de 45 a 60 minutos en completarse.", accept=["mrcoffee-2003-00107"],
      note="Kabul: İspanyolca bölüm s.7 ve İngilizce bölüm s.17 ('The entire cycle will take 45-60 minutes')"),
    Q("mrcoffee-2003-00139", "Yedek su filtresi diskleri nereden alınır?", "değer", [], [],
      "Yerel satıcıdan ya da 1-800-MR-COFFEE (ABD) / 1-800-667-8623 (Kanada) aranarak (kâğıt filtreler ise marketlerde)",
      "Water Filtration - Replacement water filtration disks can be purchased through your local retailer or by calling 1-800-MR-COFFEE",
      note="Soru su filtresi diskini soruyor; aynı parçadaki kâğıt kahve filtresi ('most grocery stores') farklı ürün"),
    # --- Bosch freze tablası --- A109-A116
    Q("bosch-ra1171-00009", "Freze tablasıyla çalışırken hangi kişisel koruyucu ekipmanlar kullanılmalı?", "prosedür", ["parafraz"], [],
      "ANSI Z87.1 uyumlu koruyucu gözlük; gerekirse kaymaz ayakkabı, baret, toz maskesi ve kulak koruyucu", "Wear safety goggles (must comply with ANSI Standard Z87.1) at all times."),
    Q("bosch-ra1171-00144", "Freze tablası şalteri için en az kaç gauge uzatma kablosu gerekir?", "değer", ["sayi"], ["14"], "14 gauge ya da daha kalın, üç telli topraklı",
      "A 14-gauge (or heavier) three-wire extension cord"),
    Q("bosch-ra1171-00121", "Frezemin modeli bağlantı tablosunda yoksa ne yapmalıyım?", "prosedür", ["parafraz"], ["RA1186"], "Ayrıca satılan BOSCH RA1186 adaptör plakası alınmalı",
      "If it is NOT listed, you must purchase a BOSCH RA1186 Router Adapter Plate"),
    Q("bosch-ra1171-00124", "Bosch 1617 serisi frezeyi tablaya bağlamak için hangi vidalar gerekir?", "değer", ["tablo", "kod_varyant"], ["10-24"],
      "10-24 × 3/4″ yıldız başlı makine vidaları (46), delik deseni B", "Fasteners Required: 10-24 x 3/4″ Phillips machine screws (46)"),
    Q("bosch-ra1171-00170", "Çit yüzleri freze ucuna ne kadar yakın olmalı?", "değer", ["parafraz"], ["1/4"], "Uca değmeyecek kadar yakın, tipik olarak yaklaşık 1/4″",
      "(typically about 1/4″ from the bit is a suitable distance)"),
    Q("bosch-ra1171-00187", "Freze tablasının gönye kanalı hangi ölçüdeki gönye kılavuzlarına uyar?", "değer", ["sayi"], ["3/4", "3/8"], "3/4″ genişlik × 3/8″ derinlik",
      "miter gauges that measure 3/4″ wide x 3/8″ deep"),
    Q("bosch-ra1171-00155", "Freze tablası şalteri kapalı konumda nasıl kilitlenir?", "prosedür", [], [],
      "Kapağa basıp kapatın, kilit anahtarını tamamen çıkarın; kırmızı sürgü şalterin üst yarısını örter",
      "remove the lockout key completely from the side of the switch case"),
    Q("bosch-ra1171-00097", "Parça listesinde 38 numaralı Allen başlı bağlantı vidasından kaç adet var?", "değer", ["tablo", "sayi"], ["13"], "13 adet",
      "Key No.: 38 | Description: Allen-Head Connector Screw | Quantity: 13"),
]

# --- Bulunamadı (A117 sonrası yeni; ilk taslaktaki üç soru da listede) ---
NF_ITEMS = [
    NF("Bosch freze tablası kaç kilogram ağırlığında?", [],
       NF_PDF.replace("geçmiyor", "ağırlık değeri geçmiyor; yalnız sembol tablosunda 'kg = Kilograms, Weight' birim açıklaması var")),
    NF("Granovsky kitabına göre bilgisayarlı nakış makinesinin yazılımı nasıl güncellenir?", ["kaynak_ifadesi"],
       "chunks.jsonl'de 'embroider|software|computer' geçmiyor"),
    NF("Pantolon şartnamesinde kemer tokası kaç gram olmalı?", [], NF_PDF.replace("geçmiyor", "'buckle' geçmiyor")),
    NF("S-7300A'da E133 hatası ne demek?", ["kod_varyant"], NF_PDF.replace("geçmiyor", "S-7300A'da geçmiyor (yalnız S-7300B'de var)")),
    NF("S-7300A'da E-740 kodu çıktı, ne yapmalıyım?", ["kod_varyant"], NF_PDF.replace("geçmiyor", "S-7300A'da geçmiyor (yalnız S-7300B'de var)")),
    NF("S-7300A'da E582 hatası neden olur?", ["kod_varyant"], NF_PDF.replace("geçmiyor", "S-7300A'da geçmiyor (yalnız S-7300B'de var)")),
    NF("Bosch freze tablasının garanti süresi ne kadar?", [], NF_PDF.replace("geçmiyor", "garanti bilgisi geçmiyor ('warrants special attention' ifadesi garanti değil)")),
    NF("Mr. Coffee kahve makinesi kaç watt?", [], NF_PDF.replace("geçmiyor", "watt değeri geçmiyor")),
    NF("Mr. Coffee kahve makinesiyle süt nasıl köpürtülür?", ["parafraz"], NF_PDF.replace("geçmiyor", "'milk|froth|leche' geçmiyor")),
    NF("S-7300B'nin güç tüketimi kaç watt?", [], NF_PDF.replace("geçmiyor", "güç değeri geçmiyor; yalnız 'güç kaynağı tüketimden büyük olmalı' uyarısı var")),
    NF("Ceketin kapüşon ölçüleri nedir?", [], NF_PDF.replace("geçmiyor", "'hood' geçmiyor")),
    NF("Ceket fermuarı hangi markadan olmalı?", [], "chunks.jsonl'de 'YKK|Talon|brand name' ceket şartnamesinde geçmiyor; fermuar yalnız standartla tanımlı"),
    NF("Strickland kitabına göre deri ceket nasıl dikilir?", ["kaynak_ifadesi"], NF_PDF.replace("geçmiyor", "'leather' geçmiyor")),
    NF("S-7300A Bluetooth ya da Wi-Fi ile nasıl bağlanır?", [], NF_PDF.replace("geçmiyor", "'bluetooth|wireless|wi-fi' geçmiyor")),
    NF("Pantolon kumaşının su geçirmezlik (hidrostatik basınç) değeri ne olmalı?", [], "chunks.jsonl'de 'hydrostatic|water resist' pantolon şartnamesinde geçmiyor"),
    NF("Terzilik kitabına göre overlok makinesi nasıl ayarlanır?", ["kaynak_ifadesi"], "chunks.jsonl'de 'overlock|serger' Strickland'de geçmiyor"),
    NF("Mr. Coffee makinesiyle espresso nasıl yapılır?", [], "chunks.jsonl'de 'espresso' geçmiyor"),
]

# --- Netleştirme: ürün/model belirtilmemiş; olası ürünlerin hepsinde cevap var ---
CLARIFY_ITEMS = [
    C("E050 ne demek?", ["brother-s7300a-00409", "brother-s7300b-00437"], "S-7300A s.98 ve S-7300B s.105: makine kafası geriye yatık algılandı", ["kod_varyant"]),
    C("Dikişte ilmek oluşuyor, ne yapmalıyım?", ["brother-s7300a-00469", "brother-s7300b-00504"], "S-7300A s.101, S-7300B s.109 (aynı sorun satırı)", ["parafraz"]),
    C("İplik kesildikten sonra üst iplik kuyruğu kaç mm olmalı?", ["brother-s7300a-00369", "brother-s7300b-00393"],
      "S-7300A: 25–30 mm · S-7300B: 30–45 mm (Premier 25–30): değer modele göre değişiyor", ["benzer_bolum"]),
    C("Alt iplik sayacı nasıl azalıyor?", ["brother-s7300a-00239", "brother-s7300b-00230"], "İki modelde aynı: dikiş × adım 0,1 m'de bir 0,1 azalır"),
    C("Aydınlatma LED'i nasıl açılıp kapatılır?", ["brother-s7300a-00093", "brother-s7300b-00112"], "S-7300A s.32, S-7300B s.33: LED tuşu"),
    C("Topraklama vidası hangi torkla sıkılır?", ["brother-s7300a-00068", "brother-s7300b-00075"], "İki modelde 1,0 ± 0,1 N·m"),
    C("Çağanoz ile masura kovanı tutucusu arasındaki boşluk ne olmalı?", ["brother-s7300a-00401", "brother-s7300b-00425"],
      "S-7300A s.91, S-7300B s.94: -3 tipi 0,4–0,7 mm, -5 tipi 0,6–1,1 mm", ["parafraz"]),
    C("İplik kesme kamı ayarında iğne mili kaç mm kaldırılır?", ["brother-s7300a-00406", "brother-s7300b-00430"],
      "S-7300A: 6 mm · S-7300B: 5 mm: değer modele göre değişiyor", ["benzer_bolum"]),
    C("Makine kafası dik konuma nasıl getirilir?", ["brother-s7300a-00050", "brother-s7300b-00047"], "İki modelde s.14 (yüz plakasından sol elle tutarak)"),
    C("İliklerde inç başına kaç dikiş olmalı?", ["gl-pd-14-04a-00178", "gl-pd-07-14a-00092"],
      "Ceket: 54 ± 2 (s.22) · Pantolon: 52–56 (s.11): değer ürüne göre değişiyor", ["benzer_bolum"]),
    C("Cırt bant kenardan ne kadar içeriden dikilir?", ["gl-pd-14-04a-00093", "gl-pd-07-14a-00082"],
      "Ceket ve pantolonda 1/8–3/16 inç (ceket s.10, pantolon s.10/21)", ["karisan_dokuman"]),
    C("Beden etiketi nereye dikilir?", ["gl-pd-14-04a-00116", "gl-pd-07-14a-00096"],
      "Ceket: iç orta arka (s.13) · Pantolon: iç bel bandı dikişi (s.12)", ["benzer_bolum"]),
    C("Isırma testinde kollar böcek kafesinde kaç dakika tutulur?", ["gl-pd-14-04a-00423", "gl-pd-07-14a-00297"],
      "Ceket ve pantolonda 15 dakika (pantolonda OCR: 'IS min')", ["ocr"]),
    C("Permetrin geri kazanımı en az yüzde kaç olmalı?", ["gl-pd-14-04a-00382", "gl-pd-07-14a-00259"], "Ceket ve pantolonda %95 veya üzeri"),
    C("Cep kapağı punterizi kaç dikişli olur?", ["gl-pd-14-04a-00211", "gl-pd-07-14a-00172"],
      "Ceket s.25 ve pantolon s.22 punteriz tabloları (pantolon: 36 dikiş, 5/8 inç)", ["benzer_bolum", "tablo"]),
]

# --- Kısa, gündelik, yazım hatalı ---
CASUAL_ITEMS = [
    Q("brother-s7300a-00409", "s7300a e50 ne demek", "kod", ["gundelik", "kod_varyant"], ["E050"], "E050: makine kafası geriye yatık",
      "Code: E050 | Cause: Machine head is detected as being tilted back", note="Kod eksik yazılmış (E50); beklenen kod E050"),
    Q("gl-pd-14-04a-00178", "ceket ilik dikis sayisi?", "değer", ["gundelik"], ["54"], "54 ± 2 dikiş/inç (punteriz dahil)",
      "Buttonholes shall be 54 (± 2) stitches per inch including tack."),
    Q("gl-pd-07-14a-00088", "pantolon cep agzi kac inc", "değer", ["gundelik", "ocr"], ["6–7-1/4"], "6–7-1/4 inç",
      "not less than 6 inches and not more than 7-114 inches", ocr="7-114"),
    Q("brother-s7300b-00087", "masura nasıl takılır s7300b", "prosedür", ["gundelik"], [], "Gücü kapatın, iğneyi plakanın üstüne kaldırın, masura kovanını takın",
      "Turn off the power switch before installing the bobbin case."),
    Q("mrcoffee-2003-00100", "kahve makinası kireç nasil temizlenir", "prosedür", ["gundelik"], [],
      "Temizleyici ya da 4 fincan sirkeyle temizleme demlemesi (anahtarlı modeller s.16; programlanabilirlerde CLEAN döngüsü s.17)",
      "Follow package instructions to prepare one batch of MR. COFFEE ® Coffeemaker Cleaner.", accept=["mrcoffee-2003-00107"]),
    Q("bosch-ra1171-00155", "freze tablası şalteri nasıl kitlenir", "prosedür", ["gundelik"], [], "Kilit anahtarını çıkarın; kırmızı sürgü şalteri örter",
      "remove the lockout key completely from the side of the switch case"),
    Q("granovsky-1986-00190", "granovsky sabun kaç gram", "değer", ["gundelik", "kaynak_ifadesi"], ["25"], "Litre suya 25 g", "25 g of soap per liter of water"),
    Q("brother-s7300a-00367", "s7300a iplik gerginligi nasıl ayarlanır", "prosedür", ["gundelik"], [],
      "Önce alt iplik gerginliği, sonra düzgün dikiş elde edilecek şekilde üst iplik gerginliği ayarlanır",
      "After the lower thread tension has been adjusted, adjust the upper thread tension"),
    Q("gl-pd-07-14a-00082", "pantolonda cırt bant ne kadar içerde", "değer", ["gundelik", "ocr"], ["1/8–3/16"], "1/8–3/16 inç",
      "sewn 1183/16 inch from bound selvage", ocr="1183/16", accept=["gl-pd-07-14a-00160"]),
    Q("brother-s7300b-00437", "s7300b E-050?", "kod", ["gundelik", "kod_varyant"], ["E050"], "Makine kafası geriye yatık", "Code: E050"),
]


def norm(t: str) -> str:
    return " ".join(t.split())


def src(c: dict) -> dict:
    return {"doc": c["doc_id"], "pages": c["pages"], "chunk_id": c["chunk_id"]}


def build() -> list[dict]:
    chunks = {c["chunk_id"]: c for c in read_chunks()}
    out = []
    for n, d in enumerate(DRAFT + NF_ITEMS + CLARIFY_ITEMS + CASUAL_ITEMS, 1):
        item = {"id": f"A{n:03d}", "kind": d["kind"], "q": d["q"], "zorluk": d["tags"], "dogrulandi": False,
                "note": "taslak: beklenen kaynak Claude tarafından önerildi, doğrulanmadı" + (f". {d['note']}" if d["note"] else "")}
        if d.get("nf_kontrol"):
            item.update(expect_docs=[], expect_pages=[], expect_in_answer=[], expect_not_found=True, nf_kontrol=d["nf_kontrol"])
        elif d.get("clarify"):
            cs = [chunks[c] for c in d["clarify"]]
            item.update(expect_clarify=True, expect_docs=[c["doc_id"] for c in cs],
                        expect_pages=sorted({p for c in cs for p in c["pages"]}), kabul=[src(c) for c in cs],
                        olasi_urunler=[c["doc_id"] for c in cs], cevap=d["cevap"], expect_in_answer=[])
        else:
            main = chunks[d["cid"]]
            extra = [chunks[c] for c in d["accept"]]
            item.update(expect_docs=sorted({c["doc_id"] for c in [main, *extra]}),
                        expect_pages=sorted({p for c in [main, *extra] for p in c["pages"]}),
                        expect_chunk_ids=[main["chunk_id"], *[c["chunk_id"] for c in extra]],
                        kabul=[src(main), *[src(c) for c in extra]], expect_in_answer=d["values"], cevap=d["cevap"],
                        kanit=d["kanit"], bolum=main["section"][:60])
            if d["ocr"]:
                item["ocr_bicimi"] = d["ocr"]
            if d["kanit"] and norm(d["kanit"]) not in norm(main["text"]):
                item["uyari"] = "kanıt cümlesi parça metninde birebir bulunamadı"
        out.append(item)
    return out


def to_md(items: list[dict]) -> str:
    tags: dict[str, int] = {}
    for it in items:
        for t in it["zorluk"]:
            tags[t] = tags.get(t, 0) + 1
    kinds = {"bulunamadı": sum(1 for i in items if i.get("expect_not_found")),
             "netleştirme": sum(1 for i in items if i.get("expect_clarify"))}
    lines = ["# Aday soru taslağı (doğrulanmadı)", "",
             f"{len(items)} soru ({kinds['bulunamadı']} bulunamadı, {kinds['netleştirme']} netleştirme). Hepsi `dogrulandi: false`: "
             "ölçüme girmez. Kontrol: soru doğru mu, kabul edilen kaynak ve cevap doğru mu (kanıt cümlesi parçanın kendisinden, OCR "
             "biçimiyle). Onaylananlarda `eval/aday_sorular.json` içinde `dogrulandi: true`.", "",
             "Etiket dağılımı: " + ", ".join(f"{k} {v}" for k, v in sorted(tags.items(), key=lambda x: -x[1])), "",
             "| # | Soru | Beklenen (kabul) | Cevap | OCR biçimi | Etiketler | Kanıt / kontrol |", "|---|---|---|---|---|---|---|"]
    for it in items:
        if it.get("expect_not_found"):
            exp, kanit = "bulunamadı", it["nf_kontrol"]
        elif it.get("expect_clarify"):
            exp = "netleştirme: " + ", ".join(f"{k['doc']} s.{k['pages']}" for k in it["kabul"])
            kanit = ""
        else:
            exp = "; ".join(f"{k['doc']} s.{k['pages']}" for k in it["kabul"])
            kanit = it.get("kanit", "")
        warn = " ⚠" if it.get("uyari") else ""
        cevap = it.get("cevap", "")
        lines.append(f"| {it['id']} | {it['q']} | {exp} | {cevap}{warn} | {it.get('ocr_bicimi', '')} | {', '.join(it['zorluk'])} | "
                     f"{kanit.replace('|', '/')} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    items = build()
    (EVAL / "aday_sorular.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    (EVAL / "aday_sorular.md").write_text(to_md(items), encoding="utf-8")
    warn = [it for it in items if it.get("uyari")]
    print(len(items), "soru;", sum(1 for it in items if it.get("expect_not_found")), "bulunamadı;",
          sum(1 for it in items if it.get("expect_clarify")), "netleştirme;", len(warn), "uyarı")
    for it in warn:
        print(" ", it["id"], it["q"][:60], "→", it["uyari"])
