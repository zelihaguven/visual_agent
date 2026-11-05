# Adım 2 ilk tur: kayıtlardan analiz (2026-11-05)

Yeni model çağrısı yok: kayıtlı ham çıktılar aynı arama önbelleğiyle `pipeline.soru_cevapla`'dan yeniden geçirildi (`python -m bench.adim2_analiz`, tur `ana`). Kapsam: cevaplı sorularda üretilen cevaplar ("bulunamadı" beklenen sorular hariç), raporun rozet nedenleri tablosuyla aynı.

> Kayıt sınırı: Bu turun ham çıktısı 1500 karakterde kesik kaydedilmiş (araç sonra düzeltildi; 16:30 ve 23:00 koşuları tam kaydeder). Kesik kayıtlarda cevap kayıttaki ilk 600 karakterden, alıntılar kesik metinden alınır; bunların yeni rozeti yaklaşıktır ve ayrı sayılır.

## 1. "Alıntıda olmayan sayı" sınıfları

Bir cevapta birden çok sayı olabilir: önce sayı başına, sonra cevap başına (cevabın en ağır sınıfı; ağırlık sırası tablodaki sütunların tersi: kaynakta da yok en ağır).

| Model | cevap | sayı | doğrulayıcı: çoklu atıf [1, 2] | doğrulayıcı: liste numarası | biçim farkı (virgül/nokta, sıfır, kesir) | alıntıda yazıyla | soruda var | kaynakta var, alıntıda yok | birim dönüşümü | kaynakta da yok |
|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | 28 | 54 | 31 | 4 | 0 | 3 | 1 | 11 | 0 | 4 |
| qwen36 | 20 | 42 | 5 | 16 | 0 | 3 | 2 | 12 | 0 | 4 |
| gpt54mini | 6 | 8 | 0 | 1 | 0 | 2 | 1 | 2 | 0 | 2 |
| mistral2603 | 35 | 55 | 13 | 15 | 1 | 2 | 2 | 10 | 5 | 7 |

Cevap başına (cevabın en ağır sınıfı):

| Model | doğrulayıcı: çoklu atıf [1, 2] | doğrulayıcı: liste numarası | biçim farkı (virgül/nokta, sıfır, kesir) | alıntıda yazıyla | soruda var | kaynakta var, alıntıda yok | birim dönüşümü | kaynakta da yok |
|---|---|---|---|---|---|---|---|---|
| gemma4 | 15 | 2 | 0 | 1 | 1 | 5 | 0 | 4 |
| qwen36 | 2 | 4 | 0 | 1 | 2 | 7 | 0 | 4 |
| gpt54mini | 0 | 1 | 0 | 1 | 1 | 1 | 0 | 2 |
| mistral2603 | 6 | 13 | 0 | 2 | 1 | 3 | 3 | 7 |

## 2. Önerilen genel düzeltme: önce/sonra (verify.py'ye UYGULANMADI)

Öneri (belgeye özel kural yok):
1. Çoklu atıf tanınsın: `[1, 2]`, `[2,3,5]`, `[1; 4]`, `[1-3]` tek tek atıf sayılır (atıf kontrolü ve sayı ayıklama). Bugün yalnız `[1]` tanınıyor; çoklu atıfın içindeki sayılar "alıntıda olmayan sayı" oluyor, yalnız çoklu atıf kullanan cevap da "geçerli [n] atfı yok" alıyor.
2. Liste numarası daha geniş tanınsın: atıflar liste işaretinden önce ayıklanır (`... kullanılmalıdır. [1, 5] 2. Uygun ...`), `<br>` satır sonu sayılır, Markdown kalın madde başı da tanınır (`1. **Long**`).
3. Sayılar değer olarak karşılaştırılsın: ondalık virgül/nokta (bugün de var), sondaki sıfır (`2.00` = `2`), baştaki sıfır (`.5` = `0.5`). Binlik ayırıcı eklenmedi: `1.000` Türkçede bin, İngilizcede bir; genel kural belirsiz, bu sette vaka yok.
4. (Ayrı seçenek, B) Alıntıda yazıyla geçen 1–12 (EN/ES/FR/TR: `six months`, `two workers`) alıntı sayısı kabul edilsin. Yalnız alıntı tarafında; cevaptaki "bir" sayı sayılmaz.

Birim dönüşümü, kesirden ondalığa çeviri ve "kaynakta var, alıntıda yok" kabul EDİLMEDİ: alıntıda olmayan değer kullanıcıya doğrulanmış gibi gösterilmemeli (sınıflandırmada ayrı gösteriliyor).

| Model | Set | cevap | önce ✓ / ⚠ / ✖ | A: 1–3 | ✖ → ✓/⚠ | ⚠ → ✓ | kötüleşen | B: 1–4 | kesik kayıt (yaklaşık) |
|---|---|---|---|---|---|---|---|---|---|
| gemma4 | onaylı | 33 | 27 / 5 / 1 | 27 / 5 / 1 | 0 | 0 | 0 | 27 / 5 / 1 | 3 |
| gemma4 | onaysız | 109 | 74 / 6 / 29 | 91 / 6 / 12 | 17 | 0 | 0 | 91 / 6 / 12 | 2 |
| qwen36 | onaylı | 37 | 24 / 5 / 8 | 26 / 5 / 6 | 2 | 0 | 0 | 26 / 5 / 6 | 2 |
| qwen36 | onaysız | 115 | 90 / 7 / 18 | 94 / 7 / 14 | 4 | 0 | 0 | 94 / 7 / 14 | 1 |
| gpt54mini | onaylı | 35 | 29 / 4 / 2 | 29 / 4 / 2 | 0 | 0 | 0 | 29 / 4 / 2 | 4 |
| gpt54mini | onaysız | 116 | 98 / 10 / 8 | 99 / 10 / 7 | 1 | 0 | 0 | 100 / 10 / 6 | 1 |
| mistral2603 | onaylı | 33 | 6 / 17 / 10 | 9 / 17 / 7 | 3 | 0 | 0 | 9 / 17 / 7 | 4 |
| mistral2603 | onaysız | 110 | 40 / 29 / 41 | 49 / 31 / 30 | 11 | 0 | 0 | 49 / 32 / 29 | 4 |

Öneri A'dan sonra kalan ✖ nedenleri (bir cevapta birden çok olabilir; kesik kayıtlar hariç):

| Model | ✖ | alıntıda olmayan sayı | alıntı birebir değil | alıntı yok | tolerans düştü | tekrar | yabancı alfabe |
|---|---|---|---|---|---|---|---|
| gemma4 | 12 | 11 | 4 | 0 | 0 | 0 | 0 |
| qwen36 | 18 | 13 | 8 | 0 | 0 | 0 | 0 |
| gpt54mini | 8 | 5 | 3 | 0 | 0 | 0 | 0 |
| mistral2603 | 34 | 15 | 21 | 0 | 0 | 0 | 0 |

## 3. Örnekler (sınıf başına, modeller karışık)

- **doğrulayıcı: çoklu atıf [1, 2]** · gemma4 `aday_sorular:A004` · sayı `2` · [1, 2]
  - cevap: Type II ve Type III ceketlerde FR tanıtım bandı (FR identification marker), giyildiğinde sol kol manşetinin (left sleeve cuff) dış kısmında bulunmalıdır [1, 2].
  - alıntı: The Types II and III coat shall have a tape FR identification marker (see figure 1) on the left sleeve cuff as worn (see pattern for placement) and shall be visible from the outside when worn. The Typ
- **kaynakta da yok** · gemma4 `aday_sorular:A008` · sayı `6`
  - cevap: Ceketin üst kol cepleri (Upper sleeve pocket - through all layers) için toplam 6 adet punteriz (bar-tack) atılmalıdır [3]. Punteriz dağılımı şu şekildedir [3]: 2 adet üst ön (Top front), 2 adet alt ön (Bottom front) ve 2 adet üst arka (Top back).
  - alıntı: Bar-tack or back-tack placement: Upper sleeve pocket - through all layers a. Top front b. Bottom front c. Top back (opposite | Size of tack (inches): 5/8 5/8 5/8 | Stitches per tack 1/: 36 36 36 | # o
- **soruda var** · gemma4 `aday_sorular:A014` · sayı `2`
  - cevap: Class 2 ceketlerde böcek koruma/tanımlama/bakım etiketi (insect protection/identification/care label), ceketin iç kısmına, sol göğüs cebinin (giyildiğinde) altına dikilmelidir [1]. Etiket, dikey olarak veya cep açısına paralel olarak, etiketin üst kısmı ceketi
  - alıntı: The combination insect protection/identification/care label shall conform to Type VI, Class 15 of MIL-DTL-32075 and shall be stitched on inside of coat under the left chest pocket (as worn) vertically
- **doğrulayıcı: çoklu atıf [1, 2]** · gemma4 `aday_sorular:A015` · sayı `2` · [1, 2]
  - cevap: Ceketin tasarımı (Style A-Unisex ve Style B-Female için) şunları içerir: [2] 1. Yaka tipi: Band yaka (band collar) [2]. 2. Ön kapanış: Çift sürgülü (double slider) bir fermuar (slide fastener) ve ikincil bir cırt cırtlı bant (hook and loop fastener tape) kapan
  - alıntı: The front closure is a (double slider) slide fastener with a secondary hook and loop tape closure (see figure 1). The secondary closure consists of three (3) pairs of hook and loop fastener tape. The
- **kaynakta var, alıntıda yok** · gemma4 `aday_sorular:A016` · sayı `3`
  - cevap: Ceket yaka çiziminde (FIGURE 3), yaka çevresi ve rütbe yaması halkası (rank patch loop) gösterilmektedir; diyagramda ayrıca bir 'Box 'X' stitch' (Kutu 'X' dikişi) bulunmaktadır [1].
  - alıntı: The figure shows a diagram of a coat collar, specifically the area around the collar and the rank patch loop. The diagram includes a 'Box 'X' stitch' and a 'Rank Patch Loop.'
- **kaynakta var, alıntıda yok** · gemma4 `aday_sorular:A022` · sayı `1`
  - cevap: Pantolonun iki adet ön yan asma cebi bulunmalıdır ve bu ceplerin ağız açıklıkları (pocket openings) bartack'ler (dikiş sabitleme noktaları) arasında 6 inç'ten az olmamalı ve 7-1/4 inç'ten fazla olmamalıdır. [1]
  - alıntı: Front side pockets. The trouser shall have two (2) front side hanging pockets with pocket openings measuring not less than 6 inches and not more than 7-114 inches between bartacks.
- **kaynakta da yok** · gemma4 `aday_sorular:A025` · sayı `1`
  - cevap: Pantolon cep kapakları (pocket flaps), cep üstünün katlanmış kenarından (folded edge of pocket top) 1 1/2 inch içeride yerleştirilmelidir [3].
  - alıntı: The pocket flaps shall be set 112 inch fi'om the folded edge of pocket top (see pattem for placement).
- **kaynakta da yok** · gemma4 `aday_sorular:A030` · sayı `15`
  - cevap: Kontrol ve işlenmiş numuneleri içeren kollar, 15 dakika boyunca bir böcek kafesine maruz bırakılmalıdır [3].
  - alıntı: Arms containing the controls and treated specimens shall be exposed to a cage of insects for IS min.
- **doğrulayıcı: çoklu atıf [1, 2]** · gemma4 `aday_sorular:A033` · sayı `1` · [1, 3]
  - cevap: Kaynaklarda pantolon için iki farklı etiket yerleşimi belirtilmiştir: Class 2 pantolonlar için kombinasyon böcek koruma/tanımlama/bakım etiketi giyildiği haliyle sol kalça cebinin içine [1], Type II alev dirençli pantolonlar için kombinasyon tanımlama/bakım et
  - alıntı: The combination insect protection/identification/care label shall conform to Type VI, Class 15 of MIL­ DTL-32075 and shall be placed in the inside ofthe left hip pocket as worn, so that on the finishe
- **kaynakta var, alıntıda yok** · gemma4 `aday_sorular:A045` · sayı `6`
  - cevap: S-7300A -3 tipindeki spesifikasyonlar için rotary hook (6) ile bobbin case holder position bracket (7) arasındaki boşluk 0.4 ile 0.7 mm arasında olmalıdır [1].
  - alıntı: The clearance should be 0.4 to 0.7 mm (for -[][]3 specifications) and 0.6 to 1.1 mm (for -[][]5 specifications).
- **alıntıda yazıyla** · gemma4 `aday_sorular:A092` · sayı `2` · alıntıda yazıyla
  - cevap: Dokuma tezgâhında orta onarım (medium repairs) sıklığı çalışma düzenine göre değişmektedir: iki vardiya halinde çalışıldığında en az altı ayda bir, üç vardiya halinde çalışıldığında ise en az dört ayda bir yapılmalıdır [1, 3]. Ayrıca, tezgahın ağır aşınma duru
  - alıntı: The medium repairs are carried out according to the schedule at least twice a year, and in case of the loom’s heavy wear more frequently. The repairs are carried out by a team of two workers. Medium r
- **doğrulayıcı: liste numarası** · gemma4 `aday_sorular:A106` · sayı `2` · liste numarası
  - cevap: RA1171 freze tezgâhı için kullanılması gereken kişisel koruyucu ekipmanlar şunlardır: [1, 5] 1. Her zaman ANSI Z87.1 standardına uygun emniyet gözlüğü (baş koruması) kullanılmalıdır. [1, 5] 2. Uygun durumlarda kaymaz ayakkabı ve sert kask kullanılmalıdır. [1,
  - alıntı: Use safety goggles (head protection). Wear safety goggles (must comply with ANSI Standard Z87.1) at all times. Wear non-slip footwear and a hard hat, if appropriate. Also, use face or dust mask if cut
- **doğrulayıcı: liste numarası** · gemma4 `aday_sorular:A155` · sayı `1` · liste numarası
  - cevap: E050 hata kodu, dikişe başlarken makine kafasının arkaya eğik olduğunun algılanması durumunda ortaya çıkar [1]. Çözüm için şu adımlar izlenmelidir: [1] 1. Gücü kapatın ve makine kafasını orijinal konumuna geri getirin. 2. Gücü kapatın ve P2 konnektörünün bağla
  - alıntı: Code: E050 | Cause: Machine head is detected as being tilted back when start sewing. | Remedy: ・Turn off the power, and then return the machine head to its original position. ・Turn off the power and c
- **doğrulayıcı: liste numarası** · qwen36 `sekil_sorular:G9` · sayı `2` · liste numarası
  - cevap: Kimlik etiketinin (ID marker) yeri ceketin tipine göre değişmektedir [1]:<br>1. **Type II ve Type III ceketler için:** Kimlik etiketi, giyildiğinde sol kol manşetinde bulunur ve dışarıdan görünür olmalıdır [3].<br>2. **Diğer tipler için:** Kaynaklarda Type II
  - alıntı: See pocket detail ID Marker for Type II III left side only The Types II and III coat shall have a tape FR identification marker (see figure 1) on the left sleeve cuff as worn (see pattern for placemen
- **soruda var** · qwen36 `aday_sorular:A014` · sayı `2`
  - cevap: Class 2 ceketlerde böcek koruma etiketi, giyildiğinde sol göğüs cebinin altında, dikey olarak veya cep açısına paralel olacak şekilde, etiketin üst kısmı ceketin üstünü gösterecek şekilde dikilir [1].
  - alıntı: The combination insect protection/identification/care label shall conform to Type VI, Class 15 of MIL-DTL-32075 and shall be stitched on inside of coat under the left chest pocket (as worn) vertically
- **alıntıda yazıyla** · qwen36 `aday_sorular:A092` · sayı `2` · alıntıda yazıyla
  - cevap: Dokuma tezgâhında orta onarım sıklığı çalışma vardiyalarına göre değişir: İki vardiya çalışmasında en az 6 ayda bir (yılda en az 2 kez), üç vardiya çalışmasında en az 4 ayda bir yapılır [1][3]. Onarımı yapan ekip sayısı ise 2 kişiden oluşur [1].
  - alıntı: The medium repairs are carried out according to the schedule at least twice a year... The repairs are carried out by a team of two workers. Medium repairs are effected by a team of repair workers at l
- **soruda var** · qwen36 `aday_sorular:A109` · sayı `1617`
  - cevap: Bosch 1617 serisi (sabit tabanlı modeller) freze tezgâhını tablaya bağlamak için 46 adet 10-24 x 3/4″ Phillips makine vidası gereklidir [3].
  - alıntı: Fasteners Required: 10-24 x 3/4″ Phillips machine screws (46)
- **alıntıda yazıyla** · gpt54mini `aday_sorular:A092` · sayı `4` · alıntıda yazıyla
  - cevap: Dokuma tezgahinda orta onarim, iki vardiyada calisiliyorsa en az her 6 ayda bir, uc vardiyada calisiliyorsa en az her 4 ayda bir yapilir. Onarimi bir tamirci ekibi yapar; kaynakta kisi sayisi verilmemis. [3]
  - alıntı: Medium repairs are effected by a team of repair workers at least every six months when working in two shifts, and at least every four months when working in three shifts. For the time of medium repair
- **birim dönüşümü** · mistral2603 `aday_sorular:A009` · sayı `6.35` · 0.25 (inç→mm)
  - cevap: İsim ve U.S. Army bantları yatay hizadan en fazla 1/4 inç (yaklaşık 6.35 mm) kayabilir. Bu durumda kusur olarak sınıflandırılır [1]. Bantlar birbirleriyle de tam olarak hizalı olmalıdır [2].
  - alıntı: Examination: Front name and U.S. Army loop tapes | Defect: Not in horizontal alignment or uneven by more than 1/4-inch | Classification: 139 Both loop tapes shall be in horizontal alignment with each
- **biçim farkı (virgül/nokta, sıfır, kesir)** · mistral2603 `aday_sorular:A027` · sayı `0.375` · alıntıda değer olarak var
  - cevap: Pantolonun fermuar (fly) dikişi, J-dikişinin 3/8 - 1/2 inç (0.375 - 0.5 inç) üstünde bitmelidir [1].
  - alıntı: The fly constmction stitching offront center crotch seam shall end 3/8 - 112 inch above J-stitch. The fly shall have "J" stitching 2-inches from fly edge.
- **birim dönüşümü** · mistral2603 `aday_sorular:A028` · sayı `9.5` · 0.375 (inç→mm)
  - cevap: Pantolon iç bacağında 5 iplik emniyet dikişi kullanıldığında kalıp, 3/8 inç (yaklaşık 9.5 mm) ölçüsüne göre ayarlanmalıdır. Bu ayar, 11/2 inçlik çift iğneli dikişe göre yapılmaktadır.
  - alıntı: When the 5-thread safety stitch is used for the inseam, contractor must adjust pattems for 3/8-inch gauge in lieu of 112 inch double needle seams.
- **birim dönüşümü** · mistral2603 `aday_sorular:A082` · sayı `2.54` · 1 (inç→cm)
  - cevap: Kırım (break) çizgisinin 1 inç (2.54 cm) gerisinden başlanır. Dikişler Vi inç (1.27 cm) aralıklarla ve Vi inç (1.27 cm) genişlikte yapılmalıdır [1,4].
  - alıntı: The stitches are Vi inch across, with Vi inch between stitches. On the lapels, start the pad stitch 1 inch behind the break line, paralleling this line from neck edge to edge of garment just below the

## 4. Cevap uzunluğu (çıktı tokeni) ve ✖

| Model | cevap | token p50 | p95 | 700 sınırında kesilen | ✖ olanlarda p50 | ✓/⚠ olanlarda p50 | ✖ oranı: < 200 tk | 200–399 | ≥ 400 | ✖ oranı (öneri A ile): < 200 | 200–399 | ≥ 400 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | 142 | 205 | 424 | 0 | 258 | 192 | 3/67 (4%) | 21/63 (33%) | 6/12 (50%) | 3/67 (4%) | 7/63 (11%) | 3/12 (25%) |
| qwen36 | 152 | 228 | 450 | 0 | 285 | 223 | 3/54 (6%) | 16/79 (20%) | 7/19 (37%) | 3/54 (6%) | 14/79 (18%) | 3/19 (16%) |
| gpt54mini | 151 | 217 | 440 | 0 | 256 | 215 | 2/61 (3%) | 6/78 (8%) | 2/12 (17%) | 2/61 (3%) | 5/78 (6%) | 2/12 (17%) |
| mistral2603 | 143 | 230 | 519 | 0 | 258 | 220 | 10/49 (20%) | 32/78 (41%) | 9/16 (56%) | 9/49 (18%) | 23/78 (29%) | 5/16 (31%) |
