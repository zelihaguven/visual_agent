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
