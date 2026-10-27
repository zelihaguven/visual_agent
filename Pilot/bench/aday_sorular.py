"""Soru seti genişletme taslağı (Aşama 4 sonrası): ~120 aday soru, ağırlık zor sorularda.

Kullanım (Pilot klasöründe): python -m bench.aday_sorular   -> eval/aday_sorular.json ve eval/aday_sorular.md
- Beklenen parça (chunk_id) Claude tarafından önerildi; doküman, sayfa ve doğrulama alıntısı chunks.jsonl'den doldurulur.
- Hepsi 'dogrulandi': false. Ölçüm araçları (bench.common.load_questions) onaysız soruları ölçüme katmaz. Kullanıcı kontrol
  edip 'dogrulandi': true yaptığında ölçüme girer.
- JUKI (gorulmemis_juki) ayrı tutulan doğrulama seti olduğu için taslağa alınmadı.
- Etiketler: parafraz (atölye dili / farklı sözcük), kod_varyant (E-050 / E050 / E 050), benzer_bolum (aynı başlıklı bölüm
  başka dokümanda farklı değerle), karisan_dokuman (filtresiz aramada başka doküman öne çıkabilir), sayi, sekil, tablo,
  ingilizce, kaynak_ifadesi ("X kitabına göre"), ters_soru (cevaptan soruya), ocr (kaynakta OCR hatası), bulunamadi.
"""
import json
import re
from pathlib import Path

from pilot.chunk import read_chunks

EVAL = Path(__file__).resolve().parent.parent / "eval"

# (chunk_id | None, soru, tür, etiketler, beklenen değerler)
DRAFT = [
    # --- Ceket şartnamesi (gl-pd-14-04a) ---
    ("gl-pd-14-04a-00102", "Ceketin kol manşetindeki ayar tırnağı hangi genişlik ve uzunlukta olmalı?", "değer", ["parafraz", "sayi"], ["2-1/8", "3-1/8"]),
    ("gl-pd-14-04a-00102", "Ceket manşetinde kaç tane ilik açılır?", "değer", ["parafraz"], ["3"]),
    ("gl-pd-14-04a-00113", "Ceketteki rütbe yaması cırt bandı kaç inç olmalı?", "değer", ["parafraz", "sayi"], ["2"]),
    ("gl-pd-14-04a-00113", "Alev almaz (Type II, III) ceketlerde FR tanıtım bandı hangi kolda bulunur?", "değer", ["parafraz"], []),
    ("gl-pd-14-04a-00185", "Ceketin arka körük (bi-swing) pli üst dikişinde iki sıra arası mesafe ne kadar?", "değer", ["benzer_bolum", "tablo"], ["3/16", "1/4"]),
    ("gl-pd-14-04a-00190", "Ceket ceplerini otomatik cep makinesiyle takarken üst dikiş kenardan ne kadar içeride olmalı?", "değer", ["benzer_bolum", "tablo"], ["1/16", "1/8"]),
    ("gl-pd-14-04a-00206", "Ceketin IFF tırnak kapağına cırt bant hangi dikiş tipiyle takılır?", "değer", ["tablo"], ["301"]),
    ("gl-pd-14-04a-00221", "Ceketin üst kol ceplerine toplam kaç punteriz atılır?", "değer", ["sayi", "tablo"], ["8"]),
    ("gl-pd-14-04a-00321", "Ceket muayenesinde isim ve U.S. Army bantları ne kadar kayarsa kusur sayılır?", "değer", ["parafraz"], ["1/4"]),
    ("gl-pd-14-04a-00351", "Ceket düğme kopma testi hangi ASTM yöntemiyle yapılır?", "değer", ["kod_varyant"], ["5034"]),
    ("gl-pd-14-04a-00379", "Ceket şartnamesine göre permetrin geri kazanımı en az yüzde kaç olmalı?", "değer", ["karisan_dokuman", "sayi"], ["95"]),
    ("gl-pd-14-04a-00421", "Ceket ısırma testinde gönüllünün test bölgesi kolun neresidir?", "değer", ["benzer_bolum", "karisan_dokuman"], ["1/2"]),
    ("gl-pd-14-04a-00294", "Bitmiş ceket için toksisite şartı nedir?", "prosedür", [], []),
    ("gl-pd-14-04a-00151", "Class 2 ceketlerde böcek koruma etiketi nereye dikilir?", "değer", ["parafraz"], []),
    ("gl-pd-14-04a-00090", "Ceketin yaka tipi ve ön kapanışı nasıl?", "değer", ["parafraz"], []),
    ("gl-pd-14-04a-00560", "Ceket yaka çiziminde rütbe yaması halkası nasıl gösteriliyor?", "şekil", ["sekil"], []),
    ("gl-pd-14-04a-00071", "Uzun boy ceketlerde 36 beden ön fermuar uzunluğu kaç inç?", "değer", ["tablo", "sayi"], ["17"]),
    ("gl-pd-14-04a-00002", "Type II ceket kumaşının elyaf karışımı nedir?", "değer", ["sayi"], ["65/25/10"]),
    # --- Pantolon şartnamesi (gl-pd-07-14a) ---
    ("gl-pd-07-14a-00092", "Pantolon iliklerinde inç başına kaç dikiş olmalı?", "değer", ["benzer_bolum", "sayi"], ["52", "56"]),
    ("gl-pd-07-14a-00092", "How many stitches per inch are required for trouser buttonholes?", "değer", ["ingilizce", "benzer_bolum"], ["52", "56"]),
    ("gl-pd-07-14a-00092", "Pantolon iliklerinin kesim boyu ne kadar?", "değer", ["parafraz"], ["3/4", "7/8"]),
    ("gl-pd-07-14a-00088", "Pantolonun ön yan cep ağzı kaç inç olmalı?", "değer", ["sayi"], ["6"]),
    ("gl-pd-07-14a-00172", "Pantolon cep kapaklarındaki punterizler kaç dikişli olur?", "değer", ["benzer_bolum", "tablo"], ["36"]),
    ("gl-pd-07-14a-00172", "Pantolon cep kapağı punterizinin boyu ne kadar?", "değer", ["tablo"], ["5/8"]),
    ("gl-pd-07-14a-00148", "Pantolon cep kapaklarının üst dikişi kenardan ne kadar içeride olmalı?", "değer", ["benzer_bolum", "ocr", "tablo"], ["301"]),
    ("gl-pd-07-14a-00160", "Pantolonda cırt bant kenar şeridinden ne kadar içeriden dikilir?", "değer", ["karisan_dokuman", "parafraz", "ocr"], ["3/16"]),
    ("gl-pd-07-14a-00144", "Pantolonun fermuar (fly) dikişi J-dikişinin ne kadar üstünde bitmeli?", "değer", ["parafraz", "ocr"], ["3/8"]),
    ("gl-pd-07-14a-00135", "Pantolon iç bacağında 5 iplik emniyet dikişi kullanılırsa kalıp nasıl ayarlanır?", "prosedür", ["parafraz"], ["3/8"]),
    ("gl-pd-07-14a-00050", "Pantolonda 20 yıkamadan sonra permetrin miktarı en az ne olmalı?", "değer", ["sayi", "tablo"], ["0.025"]),
    ("gl-pd-07-14a-00297", "Pantolon ısırma testinde kollar böcek kafesinde kaç dakika tutulur?", "değer", ["ocr", "benzer_bolum"], []),
    ("gl-pd-07-14a-00253", "Pantolon permetrin testinde numuneler kaç inç çapında kesilir?", "değer", ["sayi"], ["3"]),
    ("gl-pd-07-14a-00132", "Pantolon barkodundaki NSN kaç haneli?", "değer", ["sayi"], ["13"]),
    ("gl-pd-07-14a-00096", "Pantolon beden etiketi nereye dikilir?", "değer", ["benzer_bolum"], []),
    ("gl-pd-07-14a-00230", "Pantolon temizlik muayenesinde kaç iplikten fazlası kusur sayılır?", "değer", ["sayi"], ["3"]),
    ("gl-pd-07-14a-00060", "Pantolonda cırt bant genişliklerinin toleransı ne kadar?", "değer", ["parafraz", "sayi"], ["1/32"]),
    ("gl-pd-07-14a-00313", "Pantolon çizimindeki 14 ve 12 inçlik ölçüler hangi toleransla verilmiş?", "şekil", ["sekil"], ["1/2", "1/4"]),
    # --- Brother S-7300A ---
    ("brother-s7300a-00409", "S-7300A'da E-050 hatası ne anlama gelir?", "kod", ["kod_varyant", "benzer_bolum"], ["E050"]),
    ("brother-s7300a-00409", "S-7300A ekranında E 050 yazıyor, ne yapmalıyım?", "kod", ["kod_varyant"], ["E050"]),
    ("brother-s7300a-00413", "S-7300A açılırken E065 veriyor, neden?", "kod", ["kod_varyant"], ["E065"]),
    ("brother-s7300a-00421", "S-7300A'da E111 hata kodu ne demek?", "kod", [], ["E111"]),
    ("brother-s7300a-00437", "S-7300A'da açılışta panel bağlantısı algılanmazsa hangi hata kodu çıkar?", "kod", ["ters_soru"], ["E400"]),
    ("brother-s7300a-00447", "S-7300A'da E-700 hatasında ne kontrol edilmeli?", "kod", ["kod_varyant"], ["E700"]),
    ("brother-s7300a-00444", "S-7300A'da ayarlar kendiliğinden sıfırlandı ve E442 göründü, ne yapmalıyım?", "kod", ["parafraz"], ["E442"]),
    ("brother-s7300a-00369", "S-7300A'da iplik kesildikten sonra üst ipliğin standart kuyruk uzunluğu kaç mm?", "değer", ["benzer_bolum"], ["25", "30"]),
    ("brother-s7300a-00401", "S-7300A -3 tipinde çağanoz ile masura kovanı tutucusu arasındaki boşluk ne olmalı?", "değer", ["parafraz", "sayi"], ["0.4", "0.7"]),
    ("brother-s7300a-00406", "S-7300A'da iplik kesme kamı ayarlanırken iğne mili en alt konumdan kaç mm kaldırılır?", "değer", ["benzer_bolum", "sayi"], ["6"]),
    ("brother-s7300a-00128", "S-7300A -3 tipinin en yüksek dikiş hızı nedir?", "değer", ["benzer_bolum"], ["5000"]),
    ("brother-s7300a-00160", "S-7300A'da başlangıç punterizinde B dikiş sayısı hangi aralıkta ayarlanır?", "değer", ["tablo"], ["19"]),
    ("brother-s7300a-00240", "S-7300A'da alt iplik sayacı sıfırın altına düşünce makine ne yapar?", "prosedür", ["parafraz"], ["5"]),
    ("brother-s7300a-00247", "S-7300A'da aydınlatma LED parlaklığı hangi aralıkta ayarlanır?", "değer", ["benzer_bolum"], ["1", "9"]),
    ("brother-s7300a-00264", "S-7300A'ya en fazla kaç farklı desen dikişi kaydedilebilir?", "değer", ["sayi"], ["5"]),
    ("brother-s7300a-00302", "S-7300A'da açılışta panelin otomatik kilitlenmesi hangi bellek anahtarıyla kapatılır?", "değer", ["ters_soru", "tablo"], ["311"]),
    ("brother-s7300a-00474", "S-7300A'da dikiş dalgalı ve düzensiz çıkıyor, olası nedenler neler?", "arıza", ["parafraz"], []),
    ("brother-s7300a-00469", "S-7300A'da dikişte ilmek (halka) oluşuyor, ne yapmalıyım?", "arıza", ["parafraz"], []),
    ("brother-s7300a-00080", "S-7300A'da ayağımı pedala koyunca makine yavaş dönmeye başlıyor, ne yapmalıyım?", "arıza", ["parafraz"], []),
    ("brother-s7300a-00068", "S-7300A topraklama vidasının önerilen sıkma torku nedir?", "değer", ["sayi"], ["1.0"]),
    ("brother-s7300a-00375", "S-7300A'da çağanoz ve masura kovanı nasıl temizlenir?", "prosedür", ["parafraz"], []),
    ("brother-s7300a-00396", "S-7300A'da iğne mili yüksekliği neye göre ayarlanır?", "prosedür", ["benzer_bolum"], []),
    (None, "S-7300A'da E210 hatası ne demek?", "bulunamadı", ["bulunamadi", "kod_varyant"], []),
    (None, "S-7300A'da E-211 kodu çıktı, ne yapmalıyım?", "bulunamadı", ["bulunamadi", "kod_varyant"], []),
    # --- Brother S-7300B ---
    ("brother-s7300b-00437", "S-7300B'de E050 hatası ne anlama gelir?", "kod", ["benzer_bolum", "karisan_dokuman"], ["E050"]),
    ("brother-s7300b-00463", "S-7300B açılışta E210 veriyor, ne kontrol etmeliyim?", "kod", [], ["E210"]),
    ("brother-s7300b-00464", "S-7300B dikiş sırasında E-211 veriyor, neden?", "kod", ["kod_varyant"], ["E211"]),
    ("brother-s7300b-00483", "S-7300B'de E705 hatası ne demek?", "kod", [], ["E705"]),
    ("brother-s7300b-00150", "S-7300B'de başlangıç punteriz dikiş hızının varsayılan değeri kaç?", "değer", ["benzer_bolum", "tablo"], ["1800"]),
    ("brother-s7300b-00249", "S-7300B'de dikiş adımının varsayılan değeri ve ayar birimi nedir?", "değer", ["tablo"], ["2.00", "0.05"]),
    ("brother-s7300b-00393", "S-7300B'de iplik kesildikten sonra üst ipliğin standart kuyruk uzunluğu kaç mm?", "değer", ["benzer_bolum"], ["30", "45"]),
    ("brother-s7300b-00393", "What is the standard upper thread trailing length on the S-7300B after thread trimming?", "değer", ["ingilizce", "benzer_bolum"], ["30", "45"]),
    ("brother-s7300b-00423", "S-7300B -3 tipinde çağanoz ucu, iğne mili kaç mm yükselince iğnenin ortasına gelmeli?", "değer", ["parafraz", "sayi"], ["1.8"]),
    ("brother-s7300b-00430", "S-7300B'de iplik kesme kamı ayarlanırken iğne mili en alt konumdan kaç mm kaldırılır?", "değer", ["benzer_bolum", "sayi"], ["5"]),
    ("brother-s7300b-00316", "S-7300B'de dizlik hareket hızı hangi bellek anahtarıyla ayarlanır?", "değer", ["ters_soru", "tablo"], ["591"]),
    ("brother-s7300b-00283", "S-7300B'de başlangıç punterizi B adım düzeltme oranı hangi bellek anahtarında?", "değer", ["ters_soru", "tablo"], ["202"]),
    ("brother-s7300b-00256", "S-7300B'de kısayol tuşlarına başlangıçta hangi işlevler atanmış?", "değer", [], []),
    ("brother-s7300b-00507", "S-7300B'de dikişin başında atlama ve iplik çözülmesi oluyor, ne yapmalıyım?", "arıza", ["parafraz"], []),
    ("brother-s7300b-00374", "S-7300B -3 tipinde 4000 dev/dk hızda dikiş adımı en fazla kaç mm olabilir?", "değer", ["tablo", "sayi"], ["3.0"]),
    ("brother-s7300b-00230", "S-7300B'de alt iplik sayacı ne zaman azalır?", "prosedür", ["parafraz"], ["0.1"]),
    ("brother-s7300b-00515", "S-7300B'de punteriz kenarı hizalı çıkmıyor, ne yapmalıyım?", "arıza", ["parafraz"], []),
    # --- Strickland, terzilik kitabı ---
    ("strickland-1956-00106", "Terzilik kitabına göre makine dikişinde inç başına kaç dikiş kullanılmalı?", "değer", ["kaynak_ifadesi", "karisan_dokuman"], ["15", "20"]),
    ("strickland-1956-00106", "Kalın kumaşlarda makine dikiş boyu nasıl seçilir?", "değer", ["parafraz", "karisan_dokuman"], []),
    ("strickland-1956-00143", "Fransız etek ucu (French hem) nasıl yapılır?", "prosedür", [], []),
    ("strickland-1956-00173", "Uzun kruvaze paltoda düğmelenmeyen alt kat nasıl sabitlenir?", "prosedür", ["parafraz"], ["1"]),
    ("strickland-1956-00182", "Klapede pad dikişine kırım çizgisinin ne kadar gerisinden başlanır?", "değer", ["parafraz"], ["1"]),
    ("strickland-1956-00196", "Gömme cepler neden tela ile desteklenir?", "prosedür", [], []),
    ("strickland-1956-00224", "Ok başı punteriz (arrowhead) nasıl yapılır?", "prosedür", ["karisan_dokuman"], []),
    ("strickland-1956-00158", "İlik aralıklarını doğru işaretlemek için ne yapılır?", "prosedür", ["parafraz"], []),
    ("strickland-1956-00296", "Pantolon cebinin yün yüz parçası kaç inç kesilir?", "değer", ["karisan_dokuman"], ["10", "3"]),
    ("strickland-1956-00014", "Bengalin kumaş hangi giysiler için uygundur?", "değer", [], []),
    # --- Granovsky, onarım kitabı ---
    ("granovsky-1986-00190", "Parçaları yıkamak için sabun çözeltisinde litre başına kaç gram sabun kullanılır?", "değer", ["sayi"], ["25"]),
    ("granovsky-1986-00088", "Kalın cidarlı dökme demir parçaları kaynatırken çelik pim çapı nasıl seçilir?", "değer", ["parafraz", "sayi"], ["0.3", "0.4"]),
    ("granovsky-1986-00475", "Ring iplik makinesinde kondansatörün toplam stroku kaç mm olmalı?", "değer", ["sayi"], ["18-19"]),
    ("granovsky-1986-00504", "Birinci tip çözgü makinesinin tamburunda koni açısı hangi aralıkta değişir?", "değer", ["sayi"], ["6", "26"]),
    ("granovsky-1986-00606", "Dokuma tezgâhında orta onarım ne sıklıkla yapılır ve kaç kişi yapar?", "değer", ["parafraz"], []),
    ("granovsky-1986-00690", "Mekik kutusunda mekik yokken çözgü koruyucu uçları pedlerin kaç mm üstünde olmalı?", "değer", ["parafraz", "sayi"], ["1-1.5"]),
    ("granovsky-1986-00761", "Topuk konisinin elektrik kıvılcımıyla doldurulmasında katman kalınlığı kaç mm?", "değer", ["sayi"], ["0.2"]),
    ("granovsky-1986-00153", "Granovsky'ye göre santrifüj kavrama ne zaman devreye girer?", "değer", ["kaynak_ifadesi"], []),
    ("granovsky-1986-00120", "Tekstil makinesi parçalarında bakır kaplama ne için kullanılır?", "değer", ["parafraz"], []),
    ("granovsky-1986-00645", "Yağ damperi ayar düzeneğindeki lamba kaç voltluk?", "değer", ["sayi"], ["3.5"]),
    # --- Mr. Coffee ---
    ("mrcoffee-2003-00054", "Kahve makinesinde gecikmeli demleme saati nasıl ayarlanır?", "prosedür", ["parafraz"], []),
    ("mrcoffee-2003-00055", "Kahve makinesinin su filtresi klorun yüzde kaçını giderir?", "değer", ["sayi"], ["97"]),
    ("mrcoffee-2003-00071", "Kahve makinesinde bir fincan kaç ons su sayılıyor?", "değer", ["sayi"], ["5"]),
    ("mrcoffee-2003-00100", "Kahve makinesinin kirecini temizlerken temizleyici yerine ne kadar sirke kullanılabilir?", "değer", ["parafraz"], ["4", "20"]),
    ("mrcoffee-2003-00113", "Cam sürahideki beyaz kireç lekeleri nasıl çıkarılır?", "prosedür", ["parafraz"], ["20"]),
    ("mrcoffee-2003-00125", "Sürahi ısıtma plakasından 30 saniyeden uzun alınırsa ne olur, ne yapmalıyım?", "arıza", ["tablo"], ["30"]),
    ("mrcoffee-2003-00039", "Programlanabilir kahve makinelerinde temizleme döngüsü ne kadar sürer?", "değer", ["karisan_dokuman"], ["45", "60"]),
    ("mrcoffee-2003-00139", "Yedek su filtresi diskleri nereden alınır?", "değer", [], []),
    # --- Bosch freze tablası ---
    ("bosch-ra1171-00009", "Freze tablasıyla çalışırken hangi kişisel koruyucu ekipmanlar kullanılmalı?", "prosedür", ["parafraz"], []),
    ("bosch-ra1171-00144", "Freze tablası şalteri için en az kaç gauge uzatma kablosu gerekir?", "değer", ["sayi"], ["14"]),
    ("bosch-ra1171-00121", "Frezemin modeli bağlantı tablosunda yoksa ne yapmalıyım?", "prosedür", ["parafraz"], ["RA1186"]),
    ("bosch-ra1171-00124", "Bosch 1617 serisi frezeyi tablaya bağlamak için hangi vidalar gerekir?", "değer", ["tablo", "kod_varyant"], ["10-24"]),
    ("bosch-ra1171-00170", "Çit yüzleri freze ucuna ne kadar yakın olmalı?", "değer", ["parafraz"], ["1/4"]),
    ("bosch-ra1171-00187", "Freze tablasının gönye kanalı hangi ölçüdeki gönye kılavuzlarına uyar?", "değer", ["sayi"], ["3/4", "3/8"]),
    ("bosch-ra1171-00155", "Freze tablası şalteri kapalı konumda nasıl kilitlenir?", "prosedür", [], []),
    ("bosch-ra1171-00097", "Parça listesinde 38 numaralı Allen başlı bağlantı vidasından kaç adet var?", "değer", ["tablo", "sayi"], ["13"]),
    (None, "Bosch freze tablası kaç kilogram ağırlığında?", "bulunamadı", ["bulunamadi"], []),
    (None, "Granovsky kitabına göre bilgisayarlı nakış makinesinin yazılımı nasıl güncellenir?", "bulunamadı", ["bulunamadi", "kaynak_ifadesi"], []),
    (None, "Pantolon şartnamesinde kemer tokası kaç gram olmalı?", "bulunamadı", ["bulunamadi"], []),
]


def evidence(text: str, values: list[str]) -> str:
    t = " ".join(text.split())
    for v in values:
        i = t.find(v)
        if i >= 0:
            return t[max(0, i - 90): i + 90]
    return t[:180]


def build() -> list[dict]:
    chunks = {c["chunk_id"]: c for c in read_chunks()}
    out = []
    for n, (cid, q, kind, tags, values) in enumerate(DRAFT, 1):
        item = {"id": f"A{n:03d}", "kind": kind, "q": q, "zorluk": tags, "dogrulandi": False,
                "note": "taslak: beklenen kaynak Claude tarafından önerildi, doğrulanmadı"}
        if cid is None:
            item.update(expect_docs=[], expect_pages=[], expect_in_answer=[], expect_not_found=True)
        else:
            c = chunks[cid]
            missing = [v for v in values if v not in " ".join(c["text"].split())]
            item.update(expect_docs=[c["doc_id"]], expect_pages=c["pages"], expect_chunk_ids=[cid],
                        expect_in_answer=values, alinti=evidence(c["text"], values),
                        bolum=c["section"][:60])
            if missing:
                item["uyari"] = f"beklenen değer parça metninde birebir yok: {missing}"
        out.append(item)
    return out


def to_md(items: list[dict]) -> str:
    tags: dict[str, int] = {}
    for it in items:
        for t in it["zorluk"]:
            tags[t] = tags.get(t, 0) + 1
    lines = ["# Aday soru taslağı (doğrulanmadı)", "",
             f"{len(items)} soru. Hepsi `dogrulandi: false`: ölçüme girmez. Kontrol: soru doğru mu, beklenen sayfa ve değer "
             "doğru mu (alıntı parçanın kendisinden). Onaylananlarda `eval/aday_sorular.json` içinde `dogrulandi: true`.", "",
             "Etiket dağılımı: " + ", ".join(f"{k} {v}" for k, v in sorted(tags.items(), key=lambda x: -x[1])), "",
             "| # | Soru | Beklenen | Değer | Etiketler | Alıntı (parçadan) |", "|---|---|---|---|---|---|"]
    for it in items:
        exp = "bulunamadı" if it.get("expect_not_found") else f"{it['expect_docs'][0]} s.{it['expect_pages']}"
        warn = " ⚠" if it.get("uyari") else ""
        al = it.get("alinti", "").replace("|", "/")
        lines.append(f"| {it['id']} | {it['q']} | {exp} | {', '.join(it['expect_in_answer'])}{warn} | "
                     f"{', '.join(it['zorluk'])} | {al} |")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    items = build()
    (EVAL / "aday_sorular.json").write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding="utf-8")
    (EVAL / "aday_sorular.md").write_text(to_md(items), encoding="utf-8")
    warn = [it for it in items if it.get("uyari")]
    print(len(items), "soru;", sum(1 for it in items if it.get("expect_not_found")), "bulunamadı;", len(warn), "uyarı")
    for it in warn:
        print(" ", it["id"], it["q"][:60], "→", it["uyari"])
