# Servis API'si: cevap akışı (Adım 3 için plan; kod yok)

Karar 2026-11-06: gri akış **seçenek C**. Metin gri akar; sayılar doğrulanana kadar gizlidir; ses ve rozet yalnız doğrulanmış cümleyle. Arayüze bağlama kararı c150b-JM ölçümünden sonra verilecek. İlgili: [plan §29](plan_cevap_modeli_2026-11-05.md), [stream_view.py](../../../pilot/stream_view.py).

## 1. İlkeler

- **Gizleme sunucuda yapılır.** Doğrulanmamış değer ağdan hiç çıkmaz: istemciye yalnız maskeli metin gider, değer doğrulanınca gönderilir. İstemci gizlemeye güvenilmez; tarayıcıda "görünmez" metin de sızmış sayılır.
- **Öğe sırası korunur.** Öğe *i* doğrulanmadan *i+1* açılmaz. ✖ olan öğenin yerinde "değer doğrulanamadı, kaynağa bakın" ve kaynak kartı durur, akış sürer.
- **Ses yalnız doğrulanmış öğeden.** Model sesli metni sona yazar (şemada son alan). Ses, doğrulanmış öğe metinlerinden kodla üretilir (`normalize_for_speech`, R15). `sesli_metin` alanı en sonda gelir ve sayıları alıntılarda varsa kullanılır; şemadan çıkarılması ayrıca ölçülür (token tasarrufu).
- **Yetki aramanın içinde.** Kaynak kartları ve sayfa görüntüleri yalnız kullanıcının yetkili olduğu belgelerden (G11).
- Her soru bir denetim kaydı (G14) üretir: kullanıcı, zaman, soru, kaynak kimlikleri, sağlayıcı ve denemeler, ham model çıktısı, doğrulama sonucu, süreler. Ses saklanmaz.

## 2. Uç nokta

`POST /v1/sorular` (kimlik doğrulamalı, A5). Gövde: `{"soru": "...", "dil": "tr", "kapsam": ["doc_id", ...] | null, "marka": [...] | null, "sesli": false}`. Yanıt `text/event-stream` (SSE). WebSocket gerekmiyor: akış tek yönlü, netleştirme seçimi yeni bir istek.

## 3. Olaylar (sırayla)

| Olay | Ne zaman | Veri |
|---|---|---|
| `durum` | adım değişince | `{"adim": "arama" \| "cevap" \| "dogrulama"}` |
| `netlestirme` | kural ya da model sorarsa (akış biter) | `{"soru", "secenekler": [{"doc_id", "etiket"} \| {"ek", "etiket"}], "ipucu"}` |
| `bulunamadi` | kural ya da model (akış biter) | `{"neden", "oneri": [doc_id]}` |
| `kaynaklar` | arama bitince, cevap başlamadan | `[{"no", "doc_id", "urun", "sayfa", "bolum", "kutular"}]` (kart ve sayfa görüntüsü için; yetkili belgeler) |
| `oge_akis` | öğenin metni akarken (parça parça) | `{"i", "metin": "<maskeli>"}`: gizlenen parçalar ▒▒▒ |
| `oge_dogrulandi` | öğe bitip doğrulanınca | `{"i", "metin": "<açık>", "kaynaklar": [no], "alintilar": [{"no", "metin"}], "sekil": bool}` |
| `oge_dogrulanamadi` | öğe bitip doğrulanamayınca | `{"i", "mesaj": "Değer doğrulanamadı, kaynağa bakın.", "kaynaklar": [no]}` |
| `ses` | ilk doğrulanmış öğeden itibaren, öğe öğe | `{"i", "url"}` (TTS sunucuda ya da ZDR'li bulutta, A3) |
| `rozet` | bütün öğeler bitince | `{"durum": "verified" \| "partial" \| "failed", "sorunlar": [...]}` |
| `bitti` | son | `{"sureler": {"ilk_gorunen_kelime", "ilk_dogrulanmis_cumle", "toplam"}, "saglayici", "denetim_id"}` |
| `hata` | servis yok (bütün sağlayıcılar) | `{"tur": "servis_yok", "mesaj": "Cevap servisi şu an kullanılamıyor."}` + `kaynaklar` |

## 4. Sunucu tarafı akış işleme

1. Model akışı geldikçe `stream_view.item_text_spans` ile öğe metni sınırları izlenir. Yeni gelen metin `mask` ile `oge_akis` olarak gönderilir. Gizleme kararı kelime tamamlanınca verilir: yarım token gönderilmez, rakam taşıyabilir.
2. Öğe kapandığında (`item_end_offsets`) `check_item` çalışır (alıntı birebir, alan etiketi kuralı, sayılar kendi alıntısında, tolerans). Sonuç `oge_dogrulandi` ya da `oge_dogrulanamadi` olur.
3. Akış bekçisi (40 boşluk), ilk token sınırı (2,5 sn) ve yedeğe geçiş istemcide değil sunucuda. Yedeğe geçilirse, o ana kadar gönderilmiş `oge_akis` olayları `oge_sifirla` ile geri alınır (henüz doğrulanmış öğe yoksa).
4. İstemci bağlantıyı kapatırsa model akışı iptal edilir (maliyet).

## 5. Ölçüler (her yanıtta, `bitti` içinde ve denetim kaydında)

- **İlk görünen kelime:** sorudan, ilk `oge_akis` olayında gizlenmeyen ilk tam kelimeye.
- **İlk doğrulanmış cümle:** sorudan ilk `oge_dogrulandi`ya. PRD ≤ 3 sn.
- Sesin başlaması: ilk `ses` olayının ilk baytı. PRD ≤ 4 sn.

## 6. Açık noktalar

- Şema sırası: c150b-JM (metin önce) kabul edilirse metin hemen akar. Kabul edilmezse c150b-J'de metin alıntıdan sonra gelir; o zaman gri akışın kazancı küçük.
- `sesli_metin` alanının kaldırılması (öğelerden ses) ayrı ölçüm.
- Çoklu öğeli cevapta "ilk öğe öz" kuralı korunur; ilk öğe ✖ ise kullanıcı önce yer tutucuyu görür.
