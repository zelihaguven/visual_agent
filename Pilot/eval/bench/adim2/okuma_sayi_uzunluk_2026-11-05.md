# Adım 2 ilk tur: "alıntıda olmayan sayı", cevap uzunluğu, akış okuma hatasının kapsamı (2026-11-05)

Kayıtlardan; yeni model çağrısı yok. Araç çıktısı: [adim2_analiz_2026-11-05.md](adim2_analiz_2026-11-05.md) (`python -m bench.adim2_analiz`). Model kararı bekliyor; nihai seçim onaylı ve büyütülmüş sette.

## 1. Akış okuma hatası başka nerede var?

Hata: `requests` `text/event-stream` yanıtını charset yoksa Latin-1 çözüyor (`iter_lines(decode_unicode=True)`). JSON yanıtında (`r.json()`) UTF-8 varsayıyor; orada hata yok.

| Yer | Akış okuma | İçerik nasıl kullanılıyor | Etkilenen sonuç |
|---|---|---|---|
| `bench/answer_models.py` (Adım 2) | vardı, düzeltildi | alıntı doğrulaması | ilk koşu geçersiz sayıldı (`_bozuk`), yeniden koşuldu |
| `bench/latency_e2e.py` | **aynı kod** | yalnız "ilk token geldi mi" ve usage/maliyet | [asama4_gecikme_e2e_2026-11-03](../b4/asama4_gecikme_e2e_2026-11-03.md): **etkilenmez** |
| `bench/latency_guard.py` | **aynı kod** | aynı (ilk token, sağlayıcı, maliyet) | [asama4_sure_siniri_2026-11-05](../b4/asama4_sure_siniri_2026-11-05.md) ve özet §10.3/§10.5: **etkilenmez** |
| `bench/tail_probe.py` | **aynı kod** | aynı (ilk token, maliyet) | kuyruk ölçümü t1/t2 (rapor §9.2): **etkilenmez** |
| Uygulamanın bulut yolu (`pilot/cloud.py`: çeviri, embed; `rerankers.py`) | yok (akışsız, `r.json()`) | — | etkilenmez |
| Yerel cevap modeli (`pilot/llm.py`, Ollama istemcisi) | yok | — | etkilenmez |
| `bulunamadi_e2e` (`bench/notfound_e2e.py`) | yok (pipeline + Ollama) | — | etkilenmez |

- **Neden etkilenmezler:** Üç araçta da içerik yalnız "boş değil mi" diye bakılıyor; bozuk karakter de boş değil. Süre ve maliyet aynı kalıyor.
- **Tek olası yan etki:** Latin-1'de 0x85 baytı satır sonu sayılıyor. Bu bayt bir UTF-8 karakterin içindeyse satır bölünür ve JSON çözülemez. Üç aracın kayıtlarında böyle bir hata yok (`JSONDecodeError`/`Expecting`/`Unterminated` aramasıyla kontrol edildi).
- **Öneri:** Üç araçtaki okuma da düzeltilsin (bayt satır + UTF-8, Adım 2 aracındaki gibi). Sonuçlar değişmeyeceği için yeniden koşu gerekmez. Onay verirseniz yapılır.

## 2. "Alıntıda olmayan sayı": sınıflar

Cevap başına sınıflandırıldı: rapordaki 28 / 20 / 6 / 35 cevap. Otomatik sınıflandırmadan sonra "kaynakta var", "soruda var", "birim" ve "kaynakta da yok" vakalarının hepsi elle okundu. Küçük sayılarda (1, 2, 3) "kaynakta var" eşleşmesi rastlantı olabiliyor.

| Sınıf | Gemma 4 | Qwen3.6 | GPT-5.4 mini | Mistral 2603 |
|---|---|---|---|---|
| **Biçim farkı: doğrulayıcının kendisi** (çoklu atıf `[1, 2]`, tanınmayan liste numarası, "kaynak 1'de") | **18** | 8 | 2 | **19** |
| Biçim farkı: alıntıda yazıyla ("six months" → "6 ay") | 1 | 1 | 1 | 2 |
| Biçim farkı: ondalık/sıfır | 0 | 0 | 0 | 0 |
| Birim dönüşümü (inç → mm/cm, kesir → ondalık) | 0 | 0 | 0 | 6 |
| Doğru değer var, ek sayı alıntıda değil (soruda/kaynakta: "Class 2", "Şekil 3", parça no "(6)", sayfa, model no) | 5 | 7 | 2 | 2 |
| Türetilmiş sayı (2 + 2 + 2 = toplam 6; aritmetik doğru, kaynakta toplam yok) | 1 | 1 | 1 | 1 |
| Kaynağın OCR'ı bozuk değer, model yorumladı ("112 inch" = ½, "IS min" = 15, "7-114" = 7-1/4) | 3 | 3 | 0 | 3 |
| **Gerçek uydurma / yanlış değer** | **0** | **0** | **0** | **2** |
| Toplam | 28 | 20 | 6 | 35 |

Sınıf başına örnekler:
- **Doğrulayıcı, çoklu atıf** (Gemma A004): cevap "...dış kısmında bulunmalıdır [1, 2]." İçindeki 2 "alıntıda olmayan sayı" sayılıyor. Gemma'nın 15 vakası bu.
- **Doğrulayıcı, liste numarası** (Gemma A106): "...kullanılmalıdır. [1, 5] 2. Uygun durumlarda...". Atıf, liste işaretinden sonra ayıklandığı için 2 değer sayılıyor. Qwen'de aynı durum `<br>1.` biçiminde, Mistral'de "1. **Long**" gibi Markdown'da.
- **Alıntıda yazıyla** (GPT A092): alıntı "at least every six months ... four months", cevap "her 6 ayda bir ... 4 ayda bir".
- **Birim dönüşümü** (Mistral A009): "1/4 inç (yaklaşık 6.35 mm)". Mistral A081: kaynaktaki "15 inches" → "38 cm". Dönüşümler doğru, ama kaynakta yok.
- **Ek sayı, kaynakta var** (Gemma A045): "rotary hook (6) ile bobbin case holder position bracket (7)". Parantezli sayılar şekildeki parça numaraları; değer 0.4–0.7 mm alıntıda.
- **Türetilmiş** (A008, dört model): tabloda "2 2 2", cevapta "toplam 6 punteriz".
- **OCR yorumu** (A025): Kaynakta "112 inch" yazıyor. Aynı dokümanda "3/8 - 112 inch" de geçtiği için bu büyük olasılıkla ½.
  - Gemma "1 1/2 inch" yazdı (muhtemelen yanlış).
  - Mistral "1/2 inç" yazdı (muhtemelen doğru).
  - Bu sınıfı `verify.py` doğru yakalıyor: kaynak değer bozuk, cevap doğrulanmış gösterilmemeli.
- **Gerçek uydurma** (Mistral A043): cevap "2. 10 saniye bekleyin." Kaynakta yalnız "Turn the power off and then back on again" var.
- **Yanlış değer** (Mistral Q27): Soru cırt bantla ilgili. Cevaptaki "1/4 inç", kaynağın cep kapağı maddesinden alınmış.

**Okuma:**
- Gemma 4'te gerçek uydurma yok; 9 OCR yorumundan biri muhtemelen yanlış.
- Gemma'nın ✖ fazlasının çoğu doğrulayıcıdan geliyor: Gemma çoklu atıf `[1, 2]` yazıyor, GPT-5.4 mini yazmıyor (156 cevabın hepsinde tek atıf).
- Uydurma yalnız Mistral'de (2).

## 3. Öneri: `verify.py`'ye genel düzeltme (UYGULANMADI, onayınızı bekliyor)

Biçim farkı baskın. Hepsi doğrulayıcının atıf ve liste numarası okumasından geliyor; belgeye özel kural yok.
1. Çoklu atıf tanınsın: `[1, 2]`, `[2,3,5]`, `[1; 4]`, `[1-3]`. Hem atıf kontrolünde, hem sayı ayıklamada.
2. Liste numarası daha geniş tanınsın:
   - atıf liste işaretinden önce ayıklansın;
   - `<br>` satır sonu sayılsın;
   - Markdown kalın madde başı tanınsın.
3. Sayılar değer olarak karşılaştırılsın: sondaki sıfır `2.00` = `2`, baştaki sıfır `.5` = `0.5`. Binlik ayırıcı eklenmez: `1.000` dile göre bin ya da bir.
4. (Ayrı seçenek B) Alıntıda yazıyla geçen 1–12 sayılsın (EN/ES/FR/TR). Başka dilde sık kelime olanlar dışarıda: "on", "once", "un".

Birim dönüşümü, türetilmiş sayı, OCR yorumu ve "kaynakta var, alıntıda yok" kabul **edilmez**. Alıntıda olmayan değer doğrulanmış gösterilmez.

**Önce/sonra** (cevaplı sorularda üretilen cevaplar; ✓ / ⚠ / ✖; kayıtlardan yeniden puanlandı):

| Model | Set | önce | A (1–3) | B (1–4) | kötüleşen |
|---|---|---|---|---|---|
| Gemma 4 | onaylı (33) | 27 / 5 / 1 | 27 / 5 / 1 | 27 / 5 / 1 | 0 |
| Gemma 4 | onaysız (109) | 74 / 6 / **29** | 91 / 6 / **12** | 91 / 6 / 12 | 0 |
| Qwen3.6 | onaylı (37) | 24 / 5 / 8 | 26 / 5 / 6 | 26 / 5 / 6 | 0 |
| Qwen3.6 | onaysız (115) | 90 / 7 / 18 | 94 / 7 / 14 | 94 / 7 / 14 | 0 |
| GPT-5.4 mini | onaylı (35) | 29 / 4 / 2 | 29 / 4 / 2 | 29 / 4 / 2 | 0 |
| GPT-5.4 mini | onaysız (116) | 98 / 10 / **8** | 99 / 10 / **7** | 100 / 10 / 6 | 0 |
| Mistral 2603 | onaylı (33) | 6 / 17 / 10 | 9 / 17 / 7 | 9 / 17 / 7 | 0 |
| Mistral 2603 | onaysız (110) | 40 / 29 / 41 | 49 / 31 / 30 | 49 / 32 / 29 | 0 |

- **Gemma 4'ün onaysız ✖'i 29 → 12, GPT-5.4 mini 8 → 7.** İki set birlikte: Gemma 13, GPT 9.
- Hiçbir cevap kötüleşmedi.
- Gemma'da kalan 12 ✖'in nedenleri:
  - 11'inde alıntıda olmayan sayı: ek sayı, OCR yorumu, türetilmiş;
  - 4'ünde alıntı birebir değil.
- B seçeneği küçük fark yapıyor (GPT ve Mistral'de birer cevap).
- Kayıt sınırı: Bu turun ham çıktısı 1500 karakterde kesik kaydedilmiş. 21 kesik kaydın rozeti yaklaşık; tabloda ayrı sayıldı ([araç çıktısı](adim2_analiz_2026-11-05.md) §2). Araç sonradan tam kayda geçti.
- Uygulanırsa iki şey birlikte yapılır:
  - `verify.py` değişikliği ve testleri;
  - Adım 2 raporunun bu turu için yeniden puanlama (kayıttan; yeni model çağrısı yok).
- Mistral'in "atıf yok" sorunu çoğunlukla gerçek: 45 cevapta hiç atıf yok. Yalnız çoklu atıf kullandığı 16 cevap bu düzeltmeyle ⚠'den çıkabilir.

## 4. Cevap uzunluğu

Ayrıntı ve öneri: [plan §13](plan_cevap_modeli_2026-11-05.md).
- Uzun cevapta ✖ daha sık: Gemma (öneri A ile) < 200 tk %4, 200–399 tk %11, ≥ 400 tk %25. Ama uzun cevaplar çok parçalı sorulardan geliyor.
- Cevap metni dört modelde benzer uzunlukta.
- Hiçbiri 700 token sınırına değmedi.
- Ortak uzunluk sınırı şimdilik önerilmiyor. İstenirse istemle A/B ölçülür.
