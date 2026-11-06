# Servis API'si: cevap akışı (Adım 3 için plan; kod yok)

Karar 2026-11-06: gri akış **seçenek C**. Metin gri akar; sayılar doğrulanana kadar gizlidir; ses ve rozet yalnız doğrulanmış cümleyle. c150b-JM (önce metin) kabul ölçütünü geçmedi (plan §31): şema **c150b-J** kalır, öğe metni alıntıdan sonra akar. Arayüze bağlama kararı kullanıcıda. İlgili: [plan §29, §31](plan_cevap_modeli_2026-11-05.md), [stream_view.py](../../../pilot/stream_view.py).

## 1. İlkeler

- **Gizleme sunucuda yapılır.** Doğrulanmamış değer ağdan hiç çıkmaz: istemciye yalnız maskeli metin gider, değer doğrulanınca gönderilir. İstemci gizlemeye güvenilmez; tarayıcıda "görünmez" metin de sızmış sayılır.
- **Sıra kuralı (karar 2026-11-06, okuma B):**
  - Sonraki öğelerin metni gizli sayılarıyla **hemen akmaya devam eder**; yalnız **sayıların açılması sıralıdır**.
  - Öğe *i+1*, öğe *i*'den önce doğrulansa bile sayıları *i* açılmadan (ya da ✖ olarak kapanmadan) açılmaz.
  - **✖ olan öğe sırayı tıkamaz:** yerine "Değer doğrulanamadı, kaynağa bakın." ve kaynak kartı konur, sıra sonraki öğeyle devam eder.
- **Ses yalnız doğrulanmış öğe metinlerinden (varsayılan, karar 2026-11-06).**
  - Ses, sırası gelip açılan doğrulanmış öğelerin metninden kodla üretilir (`normalize_for_speech`, R15).
  - Modelin `sesli_metin` alanı **şemadan çıkarılır.** Gerekçe: JUKI J10'da `sesli_metin` doğrulanmamış bir "1" sokmuştu; ayrıca sesli metin JSON'un sonunda geldiği için sesin başlamasını geciktirir.
  - Kalitenin bozulmadığı ölçülecek (bkz. §8).
- **Yetki aramanın içinde.** Kaynak kartları ve sayfa görüntüleri yalnız kullanıcının yetkili olduğu belgelerden (G11).
- Her soru bir denetim kaydı (G14) üretir (bkz. §7). Ses saklanmaz.

## 2. Uç nokta ve taşıma

`POST /v1/sorular`. Gövde: `{"soru": "...", "dil": "tr", "kapsam": ["doc_id", ...] | null, "marka": [...] | null, "sesli": false}`. Yanıt `text/event-stream` (SSE). WebSocket gerekmiyor: akış tek yönlü, netleştirme seçimi yeni bir istek.

**SSE ve kimlik:**
- Tarayıcının `EventSource`'u yalnız GET yapar ve `Authorization` başlığı göndermez. İki seçenek:
  - **(önerilen) `fetch` + `ReadableStream`:** POST gövdesi ve `Authorization: Bearer` başlığı gönderilir, akış elle ayrıştırılır (SSE satırları). Kimlik yöntemi (A5) ne olursa olsun çalışır.
  - **Oturum çerezi + EventSource:** önce soru POST ile kaydedilir, dönen kimlikle `GET /v1/sorular/{id}/akis` dinlenir; çerez `HttpOnly`, `Secure`, `SameSite=Strict`. CSRF koruması gerekir.
- **Ters vekil (nginx vb.) arabelleğe almayı kapatmalı.** Yoksa olaylar birikip toplu gelir ve gri akışın anlamı kalmaz:
  - yanıtta `X-Accel-Buffering: no` başlığı ve `Cache-Control: no-cache`;
  - nginx'te `proxy_buffering off;` ve uzun `proxy_read_timeout`;
  - sıkıştırma (gzip) akış yanıtında kapalı.
  - Sunucu kurulum listesinde ayrı madde: [KURULUM-KENDI-BELGELER.md §7](../../../../docs/KURULUM-KENDI-BELGELER.md).
- Uzun sessizlikte bağlantı kopmasın diye 15 sn'de bir SSE yorum satırı (`: canli`).

## 3. Olaylar

| Olay | Ne zaman | Veri |
|---|---|---|
| `durum` | adım değişince | `{"adim": "arama" \| "cevap" \| "dogrulama"}` |
| `netlestirme` | kural ya da model sorarsa (akış biter) | `{"soru", "secenekler": [{"doc_id", "etiket"} \| {"ek", "etiket"}], "ipucu"}` |
| `bulunamadi` | kural ya da model (akış biter) | `{"neden", "oneri": [doc_id]}` |
| `kaynaklar` | arama bitince, cevap başlamadan | `[{"no", "doc_id", "urun", "sayfa", "bolum", "kutular"}]` (kart ve sayfa görüntüsü için; yetkili belgeler) |
| `oge_akis` | öğenin metni akarken (parça parça; sonraki öğeler beklemeden) | `{"i", "metin": "<maskeli>"}`: gizlenen parçalar ▒▒▒ |
| `oge_dogrulandi` | öğe doğrulandı **ve** önceki bütün öğeler kapandı (sıra kuralı) | `{"i", "metin": "<açık>", "kaynaklar": [no], "alintilar": [{"no", "metin"}], "sekil": bool}` |
| `oge_dogrulanamadi` | öğe ✖ ve önceki öğeler kapandı | `{"i", "mesaj": "Değer doğrulanamadı, kaynağa bakın.", "kaynaklar": [no]}` |
| `ses` | her `oge_dogrulandi`dan sonra, sırayla | `{"i", "url"}` (TTS sunucuda ya da ZDR'li bulutta, A3) |
| `oge_sifirla` | yedeğe geçiş, henüz doğrulanmış öğe gönderilmemişken | `{}`: istemci akan gri metni siler |
| `cevap_tamamlanamadi` | akış ortasında kesinti, en az bir doğrulanmış öğe gönderilmişken | `{"mesaj": "Cevap tamamlanamadı, kaynağa bakın.", "kaynaklar": [no]}` |
| `rozet` | bütün öğeler kapanınca | `{"durum": "verified" \| "partial" \| "failed", "sorunlar": [...]}` |
| `bitti` | son | `{"sureler": {"ilk_gorunen_kelime", "ilk_dogrulanmis_cumle", "ses_baslangici", "toplam"}, "saglayici", "denetim_id"}` |
| `hata` | servis yok (bütün sağlayıcılar), hız ya da maliyet sınırı | `{"tur": "servis_yok" \| "hiz_siniri" \| "maliyet_siniri", "mesaj"}` + `kaynaklar` (varsa) |

## 4. Sunucu tarafı akış işleme

1. **Akan metin.** Model akışı geldikçe `stream_view.item_text_spans` ile öğe metni sınırları izlenir. Yeni gelen metin `mask` ile `oge_akis` olarak **hemen** gönderilir; önceki öğenin doğrulanmasını beklemez. Gizleme kararı kelime tamamlanınca verilir: yarım token gönderilmez, rakam taşıyabilir.
2. **Doğrulama.** Öğe kapandığında (`item_end_offsets`) `check_item` çalışır: alıntı birebir (karakter normalleştirmesi ve alan etiketi kuralı dahil), sayılar kendi alıntısında, tolerans.
3. **Sıralı açılış (sıra kuralı).**
   - Sonuçlar bir kuyruğa girer; açılış imleci *k* = ilk kapanmamış öğe.
   - Öğe *k* kapandıkça (✓ ise `oge_dogrulandi` + `ses`, ✖ ise `oge_dogrulanamadi`) imleç ilerler ve kuyrukta hazır bekleyen sonraki öğeler aynı anda açılır.
   - ✖ imleci durdurmaz.
4. **Akış bekçisi, ilk token sınırı ve yedeğe geçiş** sunucuda (40 boşluk; 2,5 sn; hata/429). Akış ortasında olursa:
   - **Henüz hiç `oge_dogrulandi` gönderilmediyse:** `oge_sifirla` gönderilir, istek yedeğe gider (mevcut plan). Kullanıcı gri metnin silinip yeniden aktığını görür.
   - **En az bir doğrulanmış öğe gönderildiyse: yeniden deneme YOK.** Gönderilen öğeler kalır. Kapanmamış öğeler için `cevap_tamamlanamadi` ("Cevap tamamlanamadı, kaynağa bakın.") ve kaynak kartları gönderilir. Rozet `partial` olur, denetim kaydına "kesinti" yazılır.
   - Gerekçe: yeniden deneme farklı bir cevap üretebilir. Doğrulanmış ama farklı iki cevabı birleştirmek tutarsızlık riski taşır.
5. **İptal.** İstemci bağlantıyı kapatırsa model akışı iptal edilir (maliyet).

## 5. Hız sınırı ve günlük maliyet bekçisi

- **Kullanıcı başına hız sınırı:** öneri dakikada 10, saatte 120 soru (atölyede normal kullanım dakikada 1–2). Aşılınca `hata: hiz_siniri` ("Kısa sürede çok soru soruldu, biraz sonra yeniden deneyin."). Kural çıkışları (model çağrısız) da sayılır; çeviri ve cevap çağrısı en pahalı kısım.
- **Eşzamanlılık:** kullanıcı başına aynı anda en fazla 1 açık akış. Yeni soru eskisini iptal eder.
- **Günlük maliyet bekçisi (OpenRouter):**
  - Her çağrının `usage.cost` değeri sayaçta toplanır (gün, kullanıcı, departman).
  - Eşikler, öneri:
    - günlük toplam için uyarı eşiği (ör. 5 USD) ve durdurma eşiği (ör. 20 USD);
    - kullanıcı başına günlük ~0,50 USD (≈ 1.500–2.000 soru, kötüye kullanım bekçisi).
  - Durdurma eşiğinde `hata: maliyet_siniri`; yöneticiye bildirim.
  - OpenRouter anahtarında ayrıca **anahtar düzeyinde harcama sınırı** tanımlanır (ikinci savunma hattı).
- Ölçek: bugün soru başına ~0,00025–0,0004 USD (cevap + çeviri). Günde 1.000 soru ≈ 0,3–0,4 USD.

## 6. Ölçüler (her yanıtta, `bitti` içinde ve denetim kaydında)

- **İlk görünen kelime:** sorudan, ilk `oge_akis` olayında gizlenmeyen ilk tam kelimeye. Bugün (c150b-J, 8 kaynak) p50 2,02 sn, p95 2,99 sn.
- **İlk doğrulanmış cümle:** sorudan ilk `oge_dogrulandi`ya. PRD ≤ 3 sn; bugün p50 2,40 sn, p95 3,63 sn.
- **Sesin başlaması:** ilk `ses` olayının ilk baytı. PRD ≤ 4 sn.

## 7. Denetim kaydı (G14)

- **İçerik:**
  - kullanıcı ve departman, zaman, soru metni;
  - kural kararları ve kapsam;
  - kaynak parça kimlikleri ve sayfaları;
  - sağlayıcı ve denemeler (yedeğe geçiş, bekçi);
  - **ham model çıktısı**;
  - öğe öğe doğrulama sonucu, rozet, süreler, maliyet.
- **Hassasiyet:** ham çıktı ve parça kimlikleri belge içeriğini ve kimin neyi sorduğunu ortaya koyar. Ham çıktı yetkisiz bir kişinin göremeyeceği değerleri içerebilir.
- **Açık nokta (karar bekliyor, A8), önerim:**
  - **Okuma yetkisi (rol):**
    - geliştirme ekibi ve sistem yöneticisi, ham çıktı dahil, yalnız hata ayıklama ve ölçüm için;
    - departman yetkilisi kendi departmanının kayıtlarını görür, ham çıktı olmadan (soru, kaynak, rozet);
    - kullanıcı yalnız kendi geçmişini görür.
    - Her kayıt okuması da kayda geçer.
  - **Saklama süresi:**
    - ham model çıktısı **30 gün** (hata ayıklama ve yeniden puanlama için yeter);
    - özet kayıt (soru, kaynak kimlikleri, rozet, süreler, maliyet) **1 yıl**;
    - sonra silinir ya da anonimleştirilir (kullanıcı kimliği çıkarılır).
  - Kayıtlar yerelde (sunucu), şifreli disk. Buluta gitmez.

## 8. Ölçülecekler (bağlamadan önce)

- **`sesli_metin`'siz şema:** c150b-J, yeni hat, 8 kaynak, tam set (~0,06 USD).
  - Beklenen: cevap kalitesi aynı (✓ / ✖ / beklenen değer, yanlış ret, doğrulanmış görünen yanlış), çıktı tokeni ve toplam süre biraz daha az.
  - Ses, doğrulanmış öğelerden üretileceği için "sesli metinde alıntıda olmayan sayı" türü ✖'ler kalkar. Ölçüm, bunun yanlış bir ✓ üretmediğini de gösterir: öğeler zaten tek tek doğrulanıyor.
- Sıra kuralı ve kesinti yolu: ağsız sahte akışlarla birim testleri (öğe *i+1* önce doğrulanır, *i* ✖; akış ortası kesinti, doğrulanmış öğe var/yok).

## 9. Açık noktalar

- Denetim kaydında okuma yetkisi ve saklama süresi (§7, A8).
- Hız ve maliyet eşiklerinin kesin değerleri (§5).
- Kimlik yöntemi (A5): `fetch` + `ReadableStream` önerisi her iki seçenekle uyumlu.
- Çoklu öğeli cevapta "ilk öğe öz" kuralı korunur. İlk öğe ✖ ise kullanıcı önce yer tutucuyu görür, sonraki öğeler sırayla açılır.
