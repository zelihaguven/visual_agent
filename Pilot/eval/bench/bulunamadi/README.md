# "Bulunamadı" ve netleştirme

Cevabı olmayan sorular ve "Hangi ürün/model?" netleştirmesi, tam hattan (model dahil). Aday taslaktaki sorular onaysız; yalnız bilgi amaçlı.

| Dosya | Tarih | Sonuç |
|---|---|---|
| [netlestirme_yontem](netlestirme_yontem_2026-10-27.md) | 2026-10-27 | Doküman skoru yöntemi ilk 3 sonuçtan kötü (onaylı sette 2 doğru netleştirmeden 1'i kaçıyor); varsayılan `top3` kaldı |
| [netlestirme_korumasi](netlestirme_korumasi_2026-10-27.md) | 2026-10-27 | Onaylı sette iki yolda da 2 doğru netleştirme, 0 yanlış pozitif/negatif; aday taslakta yeni yol 5 yanlış negatif |
| [bulunamadi_e2e](bulunamadi_e2e_2026-10-27.md) | 2026-10-27 | 21 cevapsız soru: doğru "bulunamadı" yeni yolda %48, eski rerank yolunda %62; 7 soruda alakasız kaynaktan cevap |
| [bulunamadi_analiz](bulunamadi_analiz_2026-10-27.md) | 2026-10-27 | Rapor ve karar noktaları: arama katmanında "cevap yok" eşiği yok; K1 hedefi ≥ %90, Adım 2'ye bırakıldı |
