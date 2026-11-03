# Genel kurallar: kod biçimi, parça dili, BM25'e çevrilmiş sorgu (2026-11-03)

İlke: her kural görülmemiş bir dokümanda otomatik çalışır; dokümana özgü eşleme yok. Sayılar onaysız sette, geçici.

## 1. Kod normalleştirme (uygulandı)

Kural (`pilot/query.py`): kod = 1–3 harf + isteğe bağlı ayırıcı + 2–5 rakam; iki kod, harfleri ve rakamlarının **sayısal değeri** aynıysa aynıdır (baştaki sıfır yazılmayabilir: "E50" = "E050"; değer farklıysa farklı: "E05" ≠ "E050"). Korpustaki yazımlar doküman başına otomatik çıkarılır (`_code_forms`).

- **Arama:** sorudaki kod, kapsamda tek bir yazıma düşüyorsa o yazıma çevrilir (`normalize_codes`); BM25 ve dense aynı metni görür. Pipeline ve `bench.common.prepare` aynı adımı yapar.
- **Kod araması ve "bulunamadı":** `pipeline._has_code` anahtarla eşler; "kod kapsamda yok" çıkışı (model çağrılmadan "bulunamadı") aynı kurala bağlı.
- Doküman takma adları ("s7300a") kod sayılmaz; aynı anahtara iki yazım düşerse (korpusta tek örnek: Brother `TO099`/`TO99`) soru değiştirilmez.
- Testler: `test_query.test_code_key_and_normalization`, `test_pipeline.test_code_match_ignores_leading_zeros_but_not_value`, `test_short_code_is_normalized_for_search_and_code_lookup`, `test_code_of_other_value_stays_not_found`.

**Önce/sonra** (bütün setlerdeki "bulunamadı" ve netleştirme soruları + A146; 42 soru, 6'sında kod var). Eski davranış eski birebir eşleşmeyle yeniden kuruldu:

| Soru | Tür | Kod | Önce | Sonra |
|---|---|---|---|---|
| **A146** "s7300a e50 ne demek" | kod | e50 | kod araması E50'yi bulamıyor → **arama yapılmadan "bulunamadı"** (yanlış) | E050 satırı bulunuyor, kaynaklara ekleniyor; arama metni "s7300a E050 ne demek" |
| J9 "MO-6800S'te E050 hatası" | bulunamadı | E050 | "kapsamda yok" (doğru) | aynı (JUKI'de E050/E50 yok; E05 başka kod) |
| A117 "S-7300A'da E133" | bulunamadı | E133 | "kapsamda yok" (doğru) | aynı |
| A119 "S-7300A'da E582" | bulunamadı | E582 | "kapsamda yok" (doğru) | aynı |
| Q30 "E050 hatası ne demek?" | netleştirme | E050 | iki dokümanda bulunuyor | aynı |
| A131 "E050 ne demek?" | netleştirme | E050 | iki dokümanda bulunuyor | aynı |

Kodsuz 36 "bulunamadı"/netleştirme sorusu bu kuraldan etkilenmiyor. Korpusta 754 farklı koddan 72'si baştaki sıfırla yazılmış; sıfırsız yazılan soruyla artık bulunuyorlar.

## 2. Parça bazında dil tespiti (uygulandı)

Kütüphane: **lingua** (`lingua-language-detector==2.2.0`, Apache-2.0); aday diller kurulum ayarı `PILOT_LANGS` (varsayılan en, tr, fr, es, de, it, pt), dokümana göre değil. Kayıttaki dil alanı (`DocMeta.default_lang`, `lang_ranges`) yalnız beyan; parçanın dili metinden.

Kural (`pilot/chunk.py`, `element_languages`):
- Dil **öğe** (paragraf, tablo satırı) düzeyinde tespit edilir; sayfa düzeyi yetmiyor çünkü Mr. Coffee'nin sayfaları iki sütunlu (en + es aynı sayfada).
- Öğe kendi dilini alır, yalnız: en az 40 harf, güven ≥ 0,8 ve gerçek kelime oranı (4+ harfli kelimeler) ≥ 0,3. Son koşul OCR çöpünü dışarıda tutar: Granovsky'nin çöp sayfalarında bu oran 0,01–0,08, normal sayfada ~0,55; eşiksiz denemede çöp sayfalar Almanca/Portekizce/Fransızca sayılıp parça sınırı bozuyordu.
- Koşulu sağlamayan öğe: aynı sayfada kendinden önceki güvenli öğenin dili; sayfada yoksa sayfanın çoğunluk dili (ör. Bosch s. 32, Fransızca bölümün ilk sayfası); o da yoksa önceki sayfadan.
- Dil değişimi parça sınırıdır. Şekil parçaları bulundukları konumun dilini alır; Türkçe şablon metin ("Şekildeki yazılar", otomatik açıklama) dili belirlemez (ilk denemede şekil parçaları "tr" çıkıyordu).
- Testler: `test_parse_chunk.py` (metinden tespit, iki dilli sayfa, dil değişiminde sınır, OCR çöpü, şekil, sayfanın ilk öğesi, beyan çelişkisi).

**Sonuç (kuru çalıştırma sonra uygulandı):**

| Doküman | Parça | Sınır | Dil (sonra) | Kayıttaki beyanla çelişen sayfa |
|---|---|---|---|---|
| Mr. Coffee | 164 → **167** | değişti | en 84, es 83 | 19 sayfa (beyan "en"; 17'si iki dilli en+es, s. 3 ve 5 yalnız es) |
| Bosch RA1171 | 593 | aynı | en 191, fr 199, es 203 | s. 1 (üç dilli kapak: es+fr tespit), s. 34 (Fransızca bölümde İngilizce başlıklı tablo: en+fr) |
| Ötekiler (7 doküman) | aynı | aynı | hepsi en | yok |

Bosch'ta 7 parçanın dili değişti, sınır aynı: kapağın iki parçası (üç dilli metin, tek etiket eksik kalıyor) ve s. 34'teki 5 tablo satırı (metin gerçekten İngilizce).

**Uygulama:** `run_rechunk.py` ile `chunks.jsonl` ve `manuals` (Mr. Coffee yeniden gömüldü, 167 parça, CPU 164 sn; ötekilerde yalnız payload); yeni `providers replace-doc` ile `emb_bge-m3-local-bm25`, `emb_qwen3-8b`, `scale_bge_m3_10000`, `scale_qwen3_8b_10000` (her birinde 164 eski nokta silindi, 167 eklendi; 7 Bosch parçasının `lang` alanı eşitlendi). Beş koleksiyon da `chunks.jsonl` ile birebir tutarlı (4.235 gerçek parça). Bulut: yalnız yeni Mr. Coffee metinleri (Qwen3-8B, önbellekli). **1M koleksiyonu ve sunucu paketi güncellenmedi** (eski Mr. Coffee parçalarıyla).

**Etiketler:** Mr. Coffee'ye işaret eden 19 kabul kaynağının hepsi sayfa düzeyinde korunuyor: beklenen bilgi (kanıt cümlesi ya da parçanın açılışı) yeni parçalarda aynı sayfada. `chunk_id` alanları yeni kimliklere çevrildi (30 alan); değerlendirme sayfa düzeyinde olduğu için sonuçları değiştirmez. İnceleme tablosunda 123 kanıt cümlesinin hepsi yeni parçalarda bulunuyor.
