# Bağlama sonrası duman testi (c kipi)

2026-11-06T11:05:59. Uygulamanın yolu (`pipeline.soru_cevapla`, PILOT_ANSWER_MODE=c), gerçek arama ve bulut. Ayarlar: {'mod': 'c', 'model': 'google/gemma-4-26b-a4b-it', 'sema': 'c150bJ', 'saglayicilar': ['deepinfra', 'venice', 'parasail'], 'max_tokens': 1200, 'kaynak': 8, 'ilk_token_s': 2.5, 'bekci': 40, 'ceviri': ['google/gemma-4-26b-a4b-it', ['nextbit', 'venice'], 1.2]}. Plan §29.5.

## Kapılar

| Kapı | Sonuç | |
|---|---|---|
| Doğrulanmış görünen yanlış = 0 | 0 | ✅ |
| Uçtan uca ilk doğrulanmış cümle p50 ≤ 3 sn | p50 2,53 sn · p95 3,32 sn (n=21) | ✅ |
| Cevap veren çağrılarda sağlayıcı DeepInfra | {'deepinfra': 25, 'deepinfra (yeniden)': 4} | ✅ |
| Kural çıkışlarında cevap modeli çağrısı yok | 0 | ✅ |
| (not) Arama sonrası kural çıkışlarında çeviri çağrısı yapılır (aramanın parçası, yalnız sorgu metni); arama öncesi çıkışlarda (yabancı marka, sesli kaynak) hiç bulut çağrısı yok | | |
| Yedeğe geçiş (birincil yapay kesik → Venice) | ['venice', 'venice', 'venice'] | ✅ |
| ✓ / yanlış ret, hat ölçümüne göre (aynı 24 soru) | duman ✓ 20 ⚠ 1 ✖ 2 ret 0 · hat k8 ✓ 20 ⚠ 1 ✖ 1 ret 1 | bilgi |

Beklenen değer (cevaplı, doğrulanmış): 13/14 · doğru "bulunamadı": 3/3 · netleştirme (değer farklı): 3/3 · servis yok: 0 · maliyet: 0.0104 USD

## Soru soru

| Soru | Beklenen | Durum | hat k8 durumu | değer | sağlayıcı | u2u | sorun |
|---|---|---|---|---|---|---|---|
| aday_sorular:A130 | bulunamadı | not_found | not_found |  | deepinfra | – |  |
| questions:Q10 | bulunamadı | not_found | not_found |  | deepinfra | – |  |
| questions:Q18 | bulunamadı | not_found | not_found |  | kural | – |  |
| aday_sorular:A133 | netleştirme | clarify | clarify |  | model | – |  |
| aday_sorular:A142 | netleştirme | clarify | clarify |  | model | – |  |
| questions:Q07 | netleştirme | clarify | clarify |  | model | – |  |
| questions:Q13 | cevap | verified | verified | ✓ | deepinfra | 2,53 sn |  |
| questions:Q06 | cevap | verified | verified |  | deepinfra | 2,20 sn |  |
| questions_ek:Q25 | cevap | clarify | clarify |  | model | – |  |
| questions_ek:Q23 | cevap | verified | verified | ✓ | deepinfra | 2,06 sn |  |
| sekil_sorular:N2 | cevap | verified | verified |  | deepinfra | 2,50 sn |  |
| sekil_sorular:G1 | cevap | partial | partial |  | deepinfra | 2,00 sn |  |
| aday_sorular:A084 | cevap | verified | verified |  | deepinfra | 2,54 sn |  |
| aday_sorular:A004 | cevap | verified | verified |  | deepinfra | 3,46 sn |  |
| aday_sorular:A148 | cevap | failed | failed |  | deepinfra | – | cümlede kendi alıntısında olmayan sayı: ['1', '14']; cümlede kendi alıntısında olmayan sayı: ['1', '14']; sesli metinde  |
| aday_sorular:A015 | cevap | verified | verified |  | deepinfra | 1,51 sn |  |
| aday_sorular:A028 | cevap | verified | verified | ✓ | deepinfra | 3,32 sn |  |
| aday_sorular:A035 | cevap | verified | verified | ✓ | deepinfra | 2,12 sn |  |
| aday_sorular:A154 | cevap | verified | verified | ✗ | deepinfra | 2,72 sn |  |
| aday_sorular:A018 | cevap | verified | verified | ✓ | deepinfra | 2,36 sn |  |
| aday_sorular:A022 | cevap | failed | verified |  | deepinfra | – | cümlede kendi alıntısında olmayan sayı: ['1', '4']; cümlede kendi alıntısında olmayan sayı: ['1', '4']; sesli metinde al |
| aday_sorular:A040 | cevap | verified | verified | ✓ | deepinfra | 3,24 sn |  |
| aday_sorular:A075 | cevap | verified | verified | ✓ | deepinfra | 2,69 sn |  |
| aday_sorular:A044 | cevap | verified | not_found | ✓ | deepinfra | 1,89 sn |  |
| aday_sorular:A146 | cevap | verified | verified | ✓ | deepinfra | 2,76 sn |  |
| aday_sorular:A088 | cevap | verified | verified | ✓ | deepinfra | 2,38 sn |  |
| aday_sorular:A001 | cevap | verified | verified | ✓ | deepinfra | 2,85 sn |  |
| aday_sorular:A031 | cevap | verified | verified | ✓ | deepinfra | 2,97 sn |  |
| aday_sorular:A092 | cevap | verified | verified |  | deepinfra | 3,31 sn |  |
| aday_sorular:A100 | cevap | verified | verified | ✓ | deepinfra | 2,11 sn |  |

## Yedeğe geçiş

| Soru | Durum | Sağlayıcı | Denemeler |
|---|---|---|---|
| questions:Q13 | verified | venice | [('deepinfra', 'yapay kesinti (duman testi)'), ('venice', '')] |
| questions:Q06 | verified | venice | [('deepinfra', 'yapay kesinti (duman testi)'), ('venice', '')] |
| questions_ek:Q25 | failed | venice | [('deepinfra', 'yapay kesinti (duman testi)'), ('venice', '')] |

## Notlar

- **Kural çıkışları:** Yalnız Q18 (yabancı marka, arama öncesi) gerçek kural çıkışı; bulut çağrısı yok. A133, A142, Q07 ve Q25 modelin netleştirmesi (DeepInfra).
  - Bu dört satırda ilk koşuda sağlayıcı kaydı yoktu (kayıt hatası; pipeline düzeltildi). Bir kez yeniden koşuldu, dördü de DeepInfra (+0,0010 USD).
  - Arama sonrası kural çıkışlarında çeviri çağrısı yapılır (yalnız sorgu metni).
- **Q25** (pantolon düğme ipliği Tex, beklenen 71–105): model netleştirme sordu; hat ölçümünde de böyleydi (gereksiz netleştirme).
  - Yedek turunda Venice aynı soruyu cevapladı ama ✖ (sayılar alıntıda yok). Güvenli yönde.
- **A022:** hat ölçümünde ✓, burada ✖ (cümle sayısı alıntıda yok). **A044:** hat ölçümünde yanlış ret, burada ✓. Koşudan koşuya oynama.
- **Yedeğe geçiş:** birincil yapay olarak kesildi. İstemci DeepInfra denemesinde bağlantı hatası döndürdü, ağa çıkmadı. Venice çağrısı gerçekti.

## Arayüz (app.py, Streamlit AppTest, c kipi; `python -m bench.arayuz_duman`)

| Senaryo | Soru | Rozet | Ekranda | İstisna |
|---|---|---|---|---|
| cevap | Ceketin dış görünür dikişlerinde inç başına kaç dikiş olmalı? | ✔ Doğrulandı | "…inç başına 11 (± 1) dikiş ile dikilmelidir. [2]"; alıntı ve kaynak etiketi; "ilk doğrulanmış cümle 2.5 sn · sağlayıcı deepinfra"; 🔊 düğmesi | yok |
| netleştirme | Dış görünür dikişlerde SPI kaç olmalı? | ❓ Netleştirme gerekli | model sorusu; düğmeler Ceket / Pantolon / İkisi için ayrı ayrı | yok |
| bulunamadı | S-7300A'nın garanti süresi kaç yıl? | ✖ Kaynaklarda bulunamadı | "Bu bilgi manuellerde bulunamadı."; sağlayıcı deepinfra | yok |
| sesli soru | masura kovanı nasıl takılır (STT sonucu oturuma yazılarak) | ❓ Netleştirme gerekli | "Sesli soruda makine, ürün ya da marka geçmiyor. Hangi kaynak için?" (kural, arama öncesi) | yok |
| İngilizce | What should the stitches per inch be for the outside visible seams of the jacket? | ❓ Netleştirme gerekli | kural: "Soru birden fazla ürünün şartnamesine uyuyor…" | yok |

- İlk sorudaki 27,5 sn'lik arama, süreçteki ilk aramada modelin yüklenmesi (uygulama açılışında bir kez).
- İngilizce soruda "jacket" ürün adı olarak okunmadı; kural katmanı (arama sonrası) ceket/pantolon sordu. Clarify kapısı tanımına göre gereksiz netleştirme. Bu davranış `bugun` kipinde de aynı (kural katmanı değişmedi); ayrı iş olarak not.
- Mikrofon kaydı test edilmedi (STT modeli ve ses girişi yok); sesli soru yolu STT çıktısı oturuma yazılarak sınandı.
