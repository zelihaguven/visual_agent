# İlke temizliği: dokümana ya da test sorusuna özgü girdiler (2026-11-03)

İlke: pipeline'a dokümana özgü, elle yapılan düzeltme girmez; her kural görülmemiş dokümanda otomatik çalışmalı. Sınıflar: **(a)** alan düzeyinde, şirketin bir kez kurup sürdürebileceği genel bilgi (tutuldu) · **(b)** belirli bir test dokümanı ya da sorusu için eklenmiş (kaldırıldı). Kanıt: pilot raporundaki gerekçe (`docs/PILOT-RAPORU.md` §6), soru setlerinde geçme ve girdinin bir dokümanın kendine özgü ifadesi olup olmaması. Git geçmişi 13 Ekim'de toptan yenilendiği için girdilerin ilk commit'i ayırt edici değil.

## Kaldırılanlar (b)

| Yer | Girdi | Neden (b) |
|---|---|---|
| `registry.py`, ceket | takma ad `coat`, `jacket` | Q16 için eklendi (rapor §6.3: "İngilizce soru ('coat') pantolona gitti → coat, jacket, pants eklendi") |
| `registry.py`, pantolon | takma ad `pants` | aynı düzeltmede eklendi |
| `terms.GLOSSARY` | `dış görünür dikiş` → `outside visible stitching` | ceket/pantolon şartnamesinin kendine özgü ifadesinin birebir çevirisi; Q01 ve Q07'nin ifadesi |
| `terms.GLOSSARY` | `takıl`, `takma` → `installing` | "Masura kovanı nasıl takılır?" test sorusu için eklendi (rapor §6.3); Brother bölüm başlıklarının biçimine göre |

## Tutulanlar (a)

- **`terms.GLOSSARY`, kalan 25 girdi:** atölye terimi → standart İngilizce terim (çağanoz → rotary hook, masura kovanı → bobbin case, dizlik → knee lifter, overlok → overedge, ilik → buttonhole, kuşgözü → eyelet, dikiş adımı → stitch pitch, punteriz → backtack …). Birçoğu test sorularında geçiyor, ama hiçbiri bir dokümanın kendine özgü ifadesi değil; bir konfeksiyon şirketi sözlüğünde olması beklenen terimler. `sökül`/`sökme` → `removing` hiçbir soruda geçmiyor, genel fiil. Not: `punteriz` için `backtack` karşılığı tartışmalı (şartnameler "bar-tack" yazıyor); uzman onayında bakılmalı.
- **`query.MUST_MATCH`:** doküman türü × varlık rolü kuralları (makine kılavuzunda makine ve ürün eşleşmeli; şartnamede ürün ve marka). Doküman türü yükleyicinin seçtiği kapalı listeden; genel.
- **`query.FOREIGN_BRANDS`:** dokümanı olmayan 26 giyim markası (Nike, Adidas, LC Waikiki …). Alan düzeyinde liste; yalnız Nike test sorularında geçiyor (Q08, Q18). Gerçek üründe bu liste koddan değil şirketin marka kaydından gelmeli; Q08/Q18'in "yabancı marka" çıkışı bu listeye dayanıyor.

## Kapsam dışında bulunan, aynı ilkeye aykırı girdiler (dokunulmadı, öneri)

| Yer | Girdi | Öneri |
|---|---|---|
| `query.analyze_query` | sabit aile grubu `("s7300", "makine", ("brother-s7300a", "brother-s7300b"))` | aile, makine kılavuzlarının takma adlarından otomatik: sorudaki kod, aynı markanın iki ya da daha çok model adının ortak öneki ise (s7300 ⊂ s7300a, s7300b) |
| `registry.BRAND_ALIASES` | `"brother": (s7300a, s7300b)` | aynı `brand` değerli dokümanların gruplanmasıyla otomatik |
| `query.ASPECTS`, `DETAIL_HINT` | "Dış görünür dikiş SPI" seçeneği, "E133 hatası" örneği | konu listesi doküman türüne göre genel kalabilir; şartname seçenekleri ceket test verisinden türetilmiş, gözden geçirilmeli |

## Yeni dürüst taban (10k, rerank'sız, geçici, onaysız set)

Çevrimdışı, önbellekten. A149'un yeni arama metni ("installing" eki düştü) önbellekte olmadığı için atlandı: 159 cevaplı soru. Ham tablo (tür bazında): [asama4_ilke_taban_10k](asama4_ilke_taban_10k_2026-11-03.md).

| Filtreli, hit@1 / hit@5 | Önce rapor edilen (eski etiket) | Dil kopyası etiketiyle | **İlke temizliği sonrası (taban)** |
|---|---|---|---|
| A: Qwen3-8B + BM25 | 0,69 / 0,84 | 0,74 / 0,87 | **0,74 / 0,87** |
| Üçlü füzyon | 0,75 / 0,89 | 0,80 / 0,94 | **0,80 / 0,94** |

Filtresiz taban: A 0,74/0,86, üçlü 0,79/0,92. Temizlik toplamı değiştirmedi; soru bazında değişen: G6 (A'da 9 → 8, üçlüde 1 → 4; "installing" eki gitti), A007 (üçlüde 2 → 1). "coat" artık kapsam belirlemiyor; Q16 filtresiz aranıp aynı sırada bulunuyor. Önce rapor edilen sayılarla farkın tamamı etiket düzeltmesinden.
