# 256'lık ön eleme ve tam vektör: aday listesi farkı (asama4_on_eleme_10k)

Koleksiyon: `scale_qwen3_8b_10000` · aday listesi: RRF ilk 20, rerank'sız · aynı 143 soru (cevabı olanlar: 128) · setler: aday_sorular, questions, questions_ek, sekil_sorular · onaysız sorular dahil

Önbellekte sorgu vektörü olmadığı için atlanan (bulut çağrısı yapılmadı): 36 soru: aday_sorular:A002, aday_sorular:A007, aday_sorular:A008, aday_sorular:A010, aday_sorular:A011, aday_sorular:A019, aday_sorular:A021, aday_sorular:A023, aday_sorular:A024, aday_sorular:A045, aday_sorular:A046, aday_sorular:A047, aday_sorular:A048, aday_sorular:A049, aday_sorular:A057, aday_sorular:A058, aday_sorular:A065, aday_sorular:A066, aday_sorular:A069, aday_sorular:A070, aday_sorular:A071, aday_sorular:A072, aday_sorular:A075, aday_sorular:A076, aday_sorular:A077, aday_sorular:A078, aday_sorular:A084, aday_sorular:A085, aday_sorular:A086, aday_sorular:A095, aday_sorular:A115, aday_sorular:A116, aday_sorular:A126, aday_sorular:A129, aday_sorular:A147, aday_sorular:A149

## 1. Etikete bağlı olmayan: ön eleme (A) ile tam vektör (B) arasındaki fark

B = `on_eleme10k_qwen_full`. Ön elemeden geçen aday sayısı: (PREFETCH_K + 10) × SHORT_OVERSAMPLE.

### Filtreli

| A | ön elemeden geçen | ilk 20 örtüşme (ort.) | tam örtüşen soru | sırası aynı | ilk sıra aynı | ilk 5 kümesi aynı | ortak adaylarda ort. sıra farkı |
|---|---|---|---|---|---|---|---|
| `on_eleme10k_qwen_s4` | 160 | 1,00 | 139/143 | 136/143 | 143/143 | 143/143 | 0,01 |
| `on_eleme10k_qwen_s8` | 320 | 1,00 | 142/143 | 142/143 | 143/143 | 143/143 | 0,00 |
| `on_eleme10k_qwen_s16` | 640 | 1,00 | 143/143 | 143/143 | 143/143 | 143/143 | 0,00 |
| `on_eleme10k_qwen_s32` | 1280 | 1,00 | 143/143 | 143/143 | 143/143 | 143/143 | 0,00 |

`on_eleme10k_qwen_s4` sırası değişen sorular (7): aday_sorular:A003, aday_sorular:A004, aday_sorular:A015, aday_sorular:A031, aday_sorular:A090, aday_sorular:A091, aday_sorular:A120

`on_eleme10k_qwen_s8` sırası değişen sorular (1): aday_sorular:A091

`on_eleme10k_qwen_s16` sırası değişen sorular (0): –

`on_eleme10k_qwen_s32` sırası değişen sorular (0): –

### Filtresiz

| A | ön elemeden geçen | ilk 20 örtüşme (ort.) | tam örtüşen soru | sırası aynı | ilk sıra aynı | ilk 5 kümesi aynı | ortak adaylarda ort. sıra farkı |
|---|---|---|---|---|---|---|---|
| `on_eleme10k_qwen_s4` | 160 | 0,99 | 132/143 | 130/143 | 143/143 | 143/143 | 0,03 |
| `on_eleme10k_qwen_s8` | 320 | 1,00 | 141/143 | 141/143 | 143/143 | 143/143 | 0,00 |
| `on_eleme10k_qwen_s16` | 640 | 1,00 | 143/143 | 143/143 | 143/143 | 143/143 | 0,00 |
| `on_eleme10k_qwen_s32` | 1280 | 1,00 | 143/143 | 143/143 | 143/143 | 143/143 | 0,00 |

`on_eleme10k_qwen_s4` sırası değişen sorular (13): aday_sorular:A018, aday_sorular:A020, aday_sorular:A034, aday_sorular:A090, aday_sorular:A091, aday_sorular:A108, aday_sorular:A114, aday_sorular:A155, questions:Q12, questions:Q15, questions:Q16, questions_ek:Q25, sekil_sorular:G9

`on_eleme10k_qwen_s8` sırası değişen sorular (2): aday_sorular:A091, questions:Q12

`on_eleme10k_qwen_s16` sırası değişen sorular (0): –

`on_eleme10k_qwen_s32` sırası değişen sorular (0): –

## 2. Etiketli (**geçici, onaysız set**)

Beklenen sayfa etiketleri onaysız taslaktan; sayılar karar için kullanılmaz.

### Filtreli

| Yol | n | hit@1 | hit@5 | hit@20 | MRR |
|---|---|---|---|---|---|
| `on_eleme10k_qwen_full` | 128 | 0,69 | 0,85 | 0,92 | 0,75 |
| `on_eleme10k_qwen_s4` | 128 | 0,69 | 0,85 | 0,92 | 0,75 |
| `on_eleme10k_qwen_s8` | 128 | 0,69 | 0,85 | 0,92 | 0,75 |
| `on_eleme10k_qwen_s16` | 128 | 0,69 | 0,85 | 0,92 | 0,75 |
| `on_eleme10k_qwen_s32` | 128 | 0,69 | 0,85 | 0,92 | 0,75 |
| `on_eleme10k_bge_full` | 128 | 0,60 | 0,80 | 0,90 | 0,69 |

Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s4`: yok
Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s8`: yok
Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s16`: yok
Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s32`: yok

### Filtresiz

| Yol | n | hit@1 | hit@5 | hit@20 | MRR |
|---|---|---|---|---|---|
| `on_eleme10k_qwen_full` | 128 | 0,68 | 0,82 | 0,90 | 0,73 |
| `on_eleme10k_qwen_s4` | 128 | 0,68 | 0,82 | 0,90 | 0,73 |
| `on_eleme10k_qwen_s8` | 128 | 0,68 | 0,82 | 0,90 | 0,73 |
| `on_eleme10k_qwen_s16` | 128 | 0,68 | 0,82 | 0,90 | 0,73 |
| `on_eleme10k_qwen_s32` | 128 | 0,68 | 0,82 | 0,90 | 0,73 |
| `on_eleme10k_bge_full` | 128 | 0,61 | 0,77 | 0,88 | 0,68 |

Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s4`: yok
Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s8`: yok
Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s16`: yok
Ön elemenin doğru parçayı ilk 20'den düşürdüğü sorular, `on_eleme10k_qwen_s32`: yok

