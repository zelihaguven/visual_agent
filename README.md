# Visual Agent

Atölye ustaları ve kalite ekibi için **manuel tabanlı soru-cevap sistemi.** Kullanıcı yazarak ya da konuşarak soru sorar ("Ceketin dış dikişlerinde inç başına kaç dikiş olmalı?", "S-7300A'da E050 hatası ne demek?"). Sistem cevabı marka şartnamelerinden ve makine kılavuzlarından bulur, **kaynağa dayalı** bir cevap yazar, bilginin geçtiği **sayfayı vurgulu olarak** gösterir ve cevabı **sesli** okur. Emin değilse tahmin etmez: Ya netleştirme sorusu sorar ya da "bulunamadı" der.

**Durum (2026-10-13):** Araştırma tamamlandı. Pilot iki makinede çalıştı ve ölçüldü. Uygulama aşaması planı hazır, paydaş kararlarını bekliyor.

---

## Hangi belgeyi okumalı

| Okumak istediğin | Belge |
|------------------|-------|
| **Projeyi tek bakışta:** amaç, önerilen mimari, araç seçimleri, riskler, bekleyen kararlar | [ARASTIRMA-SENTEZI.md](ARASTIRMA-SENTEZI.md) |
| **Pilotta ne yapıldı:** kullanılan bileşenler, ölçümler, yaşanan sorunlar ve çözümleri, açık kalanlar, öneriler | [PILOT-RAPORU.md](PILOT-RAPORU.md) |
| **Mimari:** pilot bugün nasıl çalışıyor (her aşamada ne, neden) ve gerçek sistem nasıl olmalı | [MIMARI.md](MIMARI.md) |
| **Sonraki adımlar:** uygulama aşamaları, karar kapıları, süre, riskler | [UYGULAMA-PLANI.md](UYGULAMA-PLANI.md) |
| Adım 1–7 araştırma raporları | [arastirma/README.md](arastirma/README.md) |
| Paydaşlara sorulacaklar ve alınan kararlar | [calisma-notlari/notlar/sorulacaklar.md](calisma-notlari/notlar/sorulacaklar.md) · ham cevaplar: [calisma-notlari/cevaplar.md](calisma-notlari/cevaplar.md) |
| Pilotu kurmak ve çalıştırmak (macOS, Windows) | [pilot/README.md](pilot/README.md) |

Okuma sırası önerisi: **Sentez → Pilot raporu → Mimari → Uygulama planı.**

---

## Klasörler

```
Visual Agent/
├── README.md                bu dosya
├── ARASTIRMA-SENTEZI.md     araştırmanın özeti ve önerileri (pilotla güncellendi)
├── PILOT-RAPORU.md          pilot: yapılanlar, ölçümler, sorunlar, öneriler
├── MIMARI.md                A: pilotun mimarisi · B: önerilen hedef mimari
├── UYGULAMA-PLANI.md        uygulama aşamaları ve karar kapıları
│
├── sekiller/                belgelerdeki şekiller (mimari, doğruluk katmanları, dağıtım, plan)
├── arastirma/               adım raporları 1–7 (temizlenmiş, numaralı) + açık sorular ve riskler
├── calisma-notlari/         araştırmanın çalışma alanı: kontrol sorulu ayrıntılı notlar (notlar/),
│                            araştırma planı ve günlüğü (req.md), paydaş cevapları (cevaplar.md),
│                            çekirdek deneme (faz1-test/)
├── test-dokumanlari/        pilotta kullanılan 7 açık erişimli PDF (aşağıdaki nota bakın)
├── pilot/                   çalışan pilot: kod, arayüz, testler, ölçümler
└── _arsiv/                  kullanılmayan ilk pilot taslağı
```

### pilot/ içinde

| Yol | İçerik |
|-----|--------|
| `pilot/pilot/` | Kütüphane: ayrıştırma, parçalama, embedding, arama, karar kuralları, LLM, doğrulama, ses. Her dosyanın görevi: [MIMARI.md §A8](MIMARI.md) |
| `pilot/app.py` | Streamlit arayüzü |
| `pilot/run_*.py` | Ayrıştırma, indeksleme, ölçüm |
| `pilot/eval/` | Test soruları ve ölçüm sonuçları |
| `pilot/tests/` | 204 birim test (model ve PDF gerektirmez) |
| `pilot/data/` | Ayrıştırılmış dokümanlar ve parçalar (indeks yeniden üretilir) |
| `pilot/tools/` | Seslendirme ve ölçüm betikleri |

---

## Hızlı başlangıç

```powershell
cd pilot
..\.venv\Scripts\python.exe -m pytest -q          # 204 test, birkaç saniye
..\.venv\Scripts\streamlit.exe run app.py         # arayüz: http://localhost:8501
```

İlk kurulum (Python ortamı, Ollama ve qwen2.5:7b, indeks, isteğe bağlı ses ve sesli soru): [pilot/README.md](pilot/README.md).

---

## Önemli notlar

- **Test dokümanları:** [test-dokumanlari/](test-dokumanlari/) içindeki PDF'ler açık erişimli kaynaklardan, **yalnızca iç Ar-Ge testi için** toplandı ve yeniden dağıtılmamalı (kaynaklar ve lisans notu: [manual-envanteri.md](calisma-notlari/notlar/manual-envanteri.md)). Repo bu yüzden gizli tutuluyor.
- **Gerçek müşteri verisi** pilotta kullanılmadı. Geçiş adımları: [UYGULAMA-PLANI.md §7](UYGULAMA-PLANI.md).
- **Pilot bir araştırma deneyidir,** üretim kalitesinde değildir: Küçük lokal model kullanıyor, yetkilendirme yok.
