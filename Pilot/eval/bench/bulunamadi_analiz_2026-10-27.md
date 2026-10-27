# "Bulunamadı" davranışı ve netleştirme yöntemi: rapor (düzeltme yapılmadı)

Ham sonuçlar: [bulunamadi_e2e_2026-10-27.md](bulunamadi_e2e_2026-10-27.md) / `.json`. 22 cevapsız soru vardı: onaylı setlerden 5 (Q08, Q09, Q10, Q18, Q31), aday taslaktan 17 (A114–A130, onaysız). Hepsi tam hattan geçti; model yerelde qwen2.5:7b (Ollama, CPU).

| Yol | Ayar |
|---|---|
| Yeni varsayılan | bge-m3 + BM25, rerank yok |
| Eski yol | bge-m3 dense + sparse, local bge-reranker (başlıksız metin, yalnız reranker sırası) |

Donanım: geliştirme dizüstü (i5-1335U, GPU yok); üretimi temsil etmez. Soru başına süre 50–140 sn (model). Q09 495 sn sürdü, o sırada başka bir ölçüm de çalışıyordu.

## 1. Sonuç

| | Yeni varsayılan | Eski (rerank) |
|---|---|---|
| Doğru "bulunamadı" | **10** | **13** |
| … kural (yabancı marka, kod yok) | 4 | 4 |
| … model "bulunamadı" dedi | 6 | 9 |
| Model netleştirme istedi (cevap yok) | 4 | 1 |
| Model cevap üretti | 8 | 8 |
| … **doğrulanmış görünen cevap** ("⚠ Kısmen doğrulandı") | **3** (A114, A126, A129) | **3** (Q09, A114, A125) |
| … kırmızı rozetli cevap ("✖ Doğrulanamadı", seslendirilmez) | 2 (Q09, A128) | 3 (A126, A128, A129) |
| … boş cevap, kırmızı rozet | 3 (Q31, A118, A125) | 2 (Q10, A118) |

**Q09 yanlış etiketli:** Soru "cevapsız" diye işaretli, ama cevap pantolon şartnamesinde var:
- s. 5: "5.04 oz/sq. yd. minimum, plain weave, 75% polyester 25% cotton … side and hip hanging pockets".
- s. 6: FR alternatifi "7.0 to 8.0 oz/sq. yd., 2×1 left hand twill".

Sorunun notu da "gramaj kumaş bölümünde olabilir; elle kontrol edilmeli" diyor. İki yolun cevabı da kaynağa dayanıyor. Etiketi değiştirmedim, onayınızı bekliyorum. Q09 düşülünce gerçek "alakasız kaynaktan cevap" sayısı yeni yolda 7, eski yolda 7.

**Asıl risk:** Cevap üretip "⚠ Kısmen doğrulandı" rozeti alan sorular. Kullanıcı bunlara güvenebilir.
- **A114 "Bosch freze tablası kaç kilogram?":** Her iki yolda da cevap "kg unitesinde ağırlığını ifade eder". Kaynakta yalnız sembol tablosundaki "kg = Kilograms" satırı var.
- **A126 / A129 (yeni yol):** Strickland'dan konu dışı adımlar geliyor: deri ceket ve overlok ayarı.
- **A125 (eski yol):** "Ceket fermuarı A-A-50199, Type II markasından olmalı." A-A-50199 bir standart numarası, marka değil; yine de kaynağa dayanıyor.

Kırmızı rozetli ve boş cevaplar "bulunamadı" demiyor, ama değer de vermiyor. Boş cevaplarda büyük ihtimalle modelin JSON'u yarıda kesildi (pipeline'daki "uzunluk sınırı" yolu); ayrım kayıtta tutulmadığı için kesin değil.

**İki yol arasındaki fark (Q10 dahil):**
- **Q10 "Uçak motoru yağı":** Yeni yolda model "bulunamadı" dedi. Eski yolda boş cevap ve kırmızı rozet. İki yolda da kaynakların üçü de granovsky-1986'dan, alakasız.
- **Yeni yolun 4 netleştirmesi (A116, A120, A121, A122):** Eski yolda model bunlara "bulunamadı" demişti. Netleştirmeyi arama koruması değil model istedi: ilk 3 kaynak tek dokümandan. Yanlış cevap değil, ama doğru davranış da değil.
- **Q31 "S-7300A motor gücü":** Eski yol "bulunamadı" dedi; yeni yol boş cevap ve kırmızı rozet.
- **A130 (yeni yol):** "Bulunamadı" kararı doğru, ama gerekçe Çince yazıldı. Dil kayması (B2); rozet bu yüzden kırmızı.

36 soruluk eşikte olduğu gibi 22 soruda 3 sorunun farkı gürültü sınırında. İki yolun "yanlış cevap" sayısı aynı.

## 2. İlk 3 kaynak ve skorlar

Tam liste: `bulunamadi_e2e_2026-10-27.json` (her iki yolun `top3` alanı). Seçilmiş satırlar:

| Soru | Yeni yol: ilk 3 (RRF) | Eski yol: ilk 3 (reranker skoru) |
|---|---|---|
| Q10 Uçak motoru yağı | granovsky s.178 (0,500); s.47–48 (0,333); s.84 (0,250) | granovsky s.47–48 (−3,82); s.178 (−4,45); s.225–226 (−5,42) |
| Q31 S-7300A motor gücü | s7300a s.12 (0,533); s.53 (0,500); s.98 (0,500) | s7300a s.85 (−5,83); s.85 (−6,01); s.53 (−6,70) |
| A114 Bosch ağırlık | bosch s.5 (1,000); s.77 (0,417); s.77 (0,343) | bosch s.87 (−6,93); s.77 (−7,34); s.77 (−7,59) |
| A123 S-7300B güç | s7300b s.23 (0,750); s.15 (0,500); s.79 (0,333) | s7300b s.23 (−0,32); s.88 (−6,30); s.88 (−6,63) |
| A130 espresso | mrcoffee s.17 (0,543); s.16 (0,500); s.16 (0,405) | mrcoffee s.8 (**2,12**); s.17 (1,36); s.11–12 (0,43) |

**Skorların anlamı:** Rerank kapalıyken skor RRF: Σ 1/(sıra+2), yalnız sıradan hesaplanıyor. Q10'un alakasız ilk sonucu (0,500), bir kolda ilk sıradaki doğru bir sonuçla aynı skoru alıyor. Bu skordan "alakasız" kararı çıkarılamaz.

Eski yolda reranker skoru vardı, ama cevapsız soruların ilk skoru −7,69 ile +2,12 arasında dağılıyor (espresso sorusunda +2,12). Bu aralık cevaplı sorularla da örtüşüyor; tek bir eşik ikisini ayırmazdı. Bu yorum ölçülmüş bir eşik değildir; eşik onaylı setle seçilecek.

## 3. "Cevap yok" kararını şu an kim veriyor?

| Sıra | Yer | Karar | Bu koşuda |
|---|---|---|---|
| 1 | `pilot/pipeline.py:203` (`query._foreign_brands`) | Soruda sistemde olmayan marka geçiyor → arama yapılmadan "bulunamadı" | Q08, Q18 |
| 2 | `pilot/pipeline.py:234` (`missing_entities`) | Kullanıcı kaynak seçmiş, sorudaki varlık o kaynakta yok → "bulunamadı" | tetiklenmedi (kaynak seçilmedi) |
| 3 | `pilot/pipeline.py:278` (`code_lookup`) | Hata kodu seçili kapsamda birebir geçmiyor → "bulunamadı", başka kaynakta geçiyorsa söylenir | A117, A119 |
| 4 | `pilot/pipeline.py:293` + `pilot/config.py:93` `MIN_RERANK_SCORE = None` | Arama skoru eşiği | **kapalı**; rerank kapalıyken skor da yok, hiç devreye giremez |
| 5 | `pilot/pipeline.py:304` (`post_search_ambiguity`, `CLARIFY_MIN_SCORE = -7`) | "Hangi ürün/model?" (bulunamadı değil) | bu sorularda tetiklenmedi |
| 6 | `pilot/prompts.py:12`: model `bulunamadi: true` yazar | **Asıl karar burada** | yeni 6, eski 9 |
| 7 | `pilot/pipeline.py:340`: model cevap yazmadan netleştirme sorar | "Netleştirme gerekli" | yeni 4, eski 1 |
| 8 | `pilot/verify.py` | Cevabı kaynakla denetler; "bulunamadı"ya çevirmez, yalnız rozet verir | — |

Kural tabanlı iki kontrol (marka, hata kodu) dışında, arama katmanında "cevap yok" kararı veren bir eşik yok; karar modele kalıyor. Yerel 7B model 22 sorunun 8'inde alakasız kaynaktan cevap yazıyor; bunların 3'ü "kısmen doğrulandı" rozeti alıyor.

## 4. Netleştirme: ilk 3 sonuç ile doküman düzeyinde skor

Ayrıntı: [netlestirme_yontem_2026-10-27.md](netlestirme_yontem_2026-10-27.md). Doküman skoru yöntemi: ilk 20 adayın RRF skoru dokümana göre toplanıyor; en iyi doküman ile yer değiştirebilir rakibinin oranı eşiği geçerse netleştirme soruluyor.

| | Doğru netleştirme | Yanlış negatif | Yanlış pozitif |
|---|---|---|---|
| Onaylı (4 soru, 2 bekleniyor): ilk 3 sonuç | 2 | 0 | 0 |
| Onaylı: doküman skoru, oran 0,5 / 0,6 / 0,7 | 1 / 1 / 0 | 1 / 1 / 2 | 0 |
| Taslak (36 soru, 15 bekleniyor; onaysız, eşik seçilmedi): ilk 3 sonuç | 10 | 5 | 0 |
| Taslak: doküman skoru, oran 0,5 / 0,6 / 0,7 | 7 / 7 / 7 | 8 / 8 / 8 | 2 / 2 / 2 |

Doküman skoru, çok sayıda zayıf eşleşmesi olan dokümanı ödüllendiriyor:
- "E050 ne demek?" sorusunda en iyi doküman Bosch çıkıyor.
- Strickland sorularında S-7300A/B öne geçiyor; iki yanlış pozitif buradan.

Oran sonucu neredeyse değiştirmiyor; sorun toplamada. Olumsuz bulgu olarak PILOT-RAPORU §7'ye yazıldı. Seçenek kapalı, varsayılan `top3`.

## 5. Açık sorular (karar sizin)

1. **Q09:** Etiket "cevapsız" yerine olumlu soruya çevrilsin mi? Kabul: gl-pd-07-14a s. 5–6.
2. **Yanlış cevaplar için bakılabilecek yerler (henüz denenmedi):**
   - Kısmen doğrulandı rozetinin cevapsız sorularda neden verildiği (`verify.py`).
   - Daha güçlü ya da bulut bir model (B2).
   - Bulut reranker skoruyla bir eşik; onaylı setle kalibre edilecek.
   - Boş cevabın nedenini kayda yazmak, JSON kesilmesi mi değil mi ayırmak için.

   Hepsi düzeltme ve onayınız olmadan yapılmayacak.
