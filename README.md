# Visual Agent

Atölye ustaları ve kalite ekibi için **manuel tabanlı soru-cevap sistemi.** Kullanıcı yazarak ya da konuşarak soru sorar ("Ceketin dış dikişlerinde inç başına kaç dikiş olmalı?", "S-7300A'da E050 hatası ne demek?"). Sistem cevabı marka şartnamelerinden ve makine kılavuzlarından bulur, **kaynağa dayalı** bir cevap yazar, bilginin geçtiği **sayfayı vurgulu olarak** gösterir ve cevabı **sesli** okur. Emin değilse tahmin etmez: Ya netleştirme sorusu sorar ya da "bulunamadı" der.

## Durum (2026-11-03)

- **Ürün tanımı:** [docs/PRD.md](docs/PRD.md) tek güncel belge. Ürün adımları **Adım 1–6**, arama benchmark'ının aşamaları **B0–B5** diye anılır.
- **Arama benchmark'ı:** B0–B4 tamam; varsayılan arama bge-m3 + BM25, rerank kapalı (hit@5 0,89, dizüstünde p50 0,45 sn). **B3b** (1M parçalık kalabalıkta doğruluk) bitti: hit@5 1M'e kadar sabit ([rapor](Pilot/eval/bench/b3/asama3b_sonuc_2026-11-03.md)). **B3a/B3c** (süre, yük) şirket içi sunucuyu bekliyor; internetsiz paket hazır. B5 onaylı soru setini bekliyor.
- **Sıradaki:** Adım 2, cevap modelinin seçimi. K1'in en uzak ölçütü doğru "bulunamadı" oranı: bugün %48, hedef ≥ %90.
- **Kod:** 393 test geçiyor.

---

## Hangi belgeyi okumalı

| Okumak istediğin | Belge |
|------------------|-------|
| **Ürün ne yapacak:** kullanıcılar, akışlar, gereksinimler, doğruluk ve süre hedefleri, açık kararlar, yol haritası | [docs/PRD.md](docs/PRD.md) |
| **Mimari:** pilot bugün nasıl çalışıyor (her parçada ne, neden) ve gerçek sistem nasıl olmalı | [docs/MIMARI.md](docs/MIMARI.md) |
| **Pilotta ne yapıldı:** bileşenler, ölçümler, sorunlar ve çözümleri, açık kalanlar | [docs/PILOT-RAPORU.md](docs/PILOT-RAPORU.md) |
| **Arama benchmark'ı (B0–B5):** aşama aşama sonuçlar ve kararlar | [Pilot/eval/bench/README.md](Pilot/eval/bench/README.md) |
| Araştırmanın özeti ve önerileri | [docs/ARASTIRMA-SENTEZI.md](docs/ARASTIRMA-SENTEZI.md) |
| Araştırma raporları 1–7 | [docs/arastirma/README.md](docs/arastirma/README.md) |
| Pilotu kurmak ve çalıştırmak (macOS, Windows) | [Pilot/README.md](Pilot/README.md) |
| Eski belgeler (uygulama planı, çalışma notları, ilk pilot taslağı, Hetzner betikleri) | [docs/arsiv/README.md](docs/arsiv/README.md) |

Okuma sırası önerisi: **PRD → Mimari → Pilot raporu → benchmark.**

---

## Klasörler

```
visual_agent/
├── README.md                 bu dosya: durum ve belge haritası
├── docs/
│   ├── PRD.md                ürünün tek güncel tanımı
│   ├── MIMARI.md             A: pilotun mimarisi · B: önerilen hedef mimari
│   ├── PILOT-RAPORU.md       pilot: yapılanlar, ölçümler, sorunlar, öneriler
│   ├── ARASTIRMA-SENTEZI.md  araştırmanın özeti
│   ├── arastirma/            araştırma raporları 1–7 + açık sorular ve riskler
│   ├── sekiller/             belgelerdeki şekiller
│   └── arsiv/                yerini PRD'nin aldığı ya da kullanılmayan belgeler ve betikler
├── Pilot/                    çalışan pilot: kod, arayüz, testler, benchmark
└── test-dokumanlari/         pilotta kullanılan 9 açık erişimli PDF (aşağıdaki nota bakın)
```

### Pilot/ içinde

| Yol | İçerik |
|-----|--------|
| `Pilot/pilot/` | Kütüphane: ayrıştırma, parçalama, embedding, arama, karar kuralları, LLM, doğrulama, ses. Her dosyanın görevi: [MIMARI.md §A8](docs/MIMARI.md) |
| `Pilot/app.py` | Streamlit arayüzü (geliştirme ekibinin test arayüzü) |
| `Pilot/run_*.py` | Ayrıştırma, indeksleme, ölçüm |
| `Pilot/bench/` | Benchmark kodu ve koşu betikleri (`run_asama*.ps1`); şirket içi sunucu paketi `bench/onprem/` |
| `Pilot/eval/` | Soru setleri; `eval/bench/` altında benchmark sonuçları aşama klasörlerinde (b0-b1, b2, b25, b3, b4, bulunamadi, genel) |
| `Pilot/tests/` | 393 birim test (model ve PDF gerektirmez) |
| `Pilot/data/` | Ayrıştırılmış dokümanlar ve parçalar (indeks, korpus ve önbellekler git dışında, yeniden üretilir) |
| `Pilot/tools/` | Seslendirme ve ölçüm betikleri |

---

## Hızlı başlangıç

```powershell
cd Pilot
..\.venv\Scripts\python.exe -m pytest -q          # 393 test, ~1 dakika
..\.venv\Scripts\streamlit.exe run app.py         # arayüz: http://localhost:8501
```

İlk kurulum (Python ortamı, Ollama ve qwen2.5:7b, indeks, isteğe bağlı ses ve sesli soru): [Pilot/README.md](Pilot/README.md).

---

## Önemli notlar

- **Test dokümanları:** [test-dokumanlari/](test-dokumanlari/) içindeki PDF'ler açık erişimli kaynaklardan, **yalnızca iç Ar-Ge testi için** toplandı ve yeniden dağıtılmamalı (kaynaklar ve lisans notu: [manual-envanteri.md](docs/arsiv/calisma-notlari/notlar/manual-envanteri.md)). Repo bu yüzden gizli tutuluyor.
- **Gerçek müşteri verisi** kullanılmadı. Gerçek veriye geçiş koşulları (K1, K2 kapıları): [PRD](docs/PRD.md).
- **Pilot bir araştırma deneyidir,** üretim kalitesinde değildir: Streamlit prototipi, giriş ve doküman yönetimi yok.
