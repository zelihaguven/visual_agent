# Adım 2 nihai tur, şema C: `nihai_ek`

Şema C (plan §15.0): her cümle kendi alıntısıyla; tur = cevap | netlestirme | bulunamadi. Rozet öğe başına doğrulamadan (`bench/schema_c.py`). Pipeline'ın varyant kuralı C'de uygulanmadı.

| Model | çağrı | JSON/şema hatası | doğru "bulunamadı" (model) | doğrulanmış görünen yanlış | cevaplı: ✓ / ⚠ / ✖ | beklenen değer | netleştirme, değer farklı | netleştirme, değer aynı | gereksiz netleştirme | ilk token p50 / p95 | ilk doğrulanmış cümle p50 / p95 | maliyet |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| gemma4 | 39 | 0 | 33/34 (97%) | **1** | 0 / 0 / 0 | – | 6/10 (60%) | – | 0 (belge içi varyant doğru 0/0) | 453 ms / 1,42 sn | – / – | 0.0075 USD |
| gemma4_venice | 39 | 1 | 33/34 (97%) | **0** | 0 / 0 / 0 | – | 6/10 (60%) | – | 0 (belge içi varyant doğru 0/0) | 673 ms / 1,04 sn | – / – | 0.0096 USD |

İlk doğrulanmış cümle: model isteğinden, akışta ilk geçen öğenin tamamlandığı ana (model tarafı; uçtan uca süre ayrıca, arama öncesi dahil). Değer aynı: netleştirme ya da iki ürünün kaynağını birlikte gösteren doğrulanmış cevap doğru sayılır.
