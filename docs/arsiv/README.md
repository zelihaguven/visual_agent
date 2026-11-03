# Arşiv

Kullanılmayan ya da yerini başka belgenin aldığı, ama silinmesi gerekmeyen dosyalar. Projenin çalışması bu klasöre bağlı değildir.

| Klasör | Ne | Neden arşivde | Tarih |
|--------|----|---------------|-------|
| `pilot-taslak-2026-10-09/visual_agent/` | Yarım kalan ilk pilot taslağı: doküman işleme, BM25 + Qdrant arama, marka bazlı yetki filtresi (`security.py`), iki yönlü sayı-tolerans doğrulaması (`verification/`) | Repodaki pilot (`Pilot/pilot/`) yerini aldı. `security.py` (e-posta/kod girişi, rol → marka, ±1 sayfa) ve `verification/numbers.py` uygulama aşamasında (Aşama 4 ve 1) başlangıç noktası olarak kullanılabilir | 2026-10-13 |
| `pilot-taslak-2026-10-09/config/` | `documents.json` (doküman kaydı + erişim türü), `users.json` (örnek kullanıcılar, kodlar SHA-256) | Aynı nedenle | 2026-10-13 |
| `pilot-taslak-2026-10-09/scripts/` | `parse_all.py` (parti parti, kaldığı yerden devam eden ayrıştırma) | Aynı nedenle | 2026-10-13 |
| [`UYGULAMA-PLANI.md`](UYGULAMA-PLANI.md) | 13 Ekim uygulama planı (Aşama 0–7, karar kapıları) | Yerini [PRD](../PRD.md) aldı; "Aşama 0–7" numaralandırması artık kullanılmıyor (ürün adımları Adım 1–6, benchmark B0–B5) | 2026-11-03 |
| [`calisma-notlari/`](calisma-notlari/) | Araştırma çalışma alanı: ayrıntılı notlar, `req.md` (9 Ekim gereksinim ve plan), paydaş cevapları, çekirdek deneme (`faz1-test/`) | Yerini PRD aldı; notlar araştırma raporlarının (`../arastirma/`) kaynağı olarak duruyor | 2026-11-03 |
| [`pilot-bench-vm/`](pilot-bench-vm/) | Eski `Pilot/bench/vm/`: Hetzner VM kurulum ve B3 koşu betikleri, `hetzner.py` | Hetzner açılmayacak; B3a/B3c şirket içi sunucuda (`Pilot/bench/onprem/`) | 2026-11-03 |
| [`pilot-eval/`](pilot-eval/) | `sonuc_onceki.md/.json`: ilk pilot ölçümü (Mac, 10 soru) | Yerini 18 soruluk ölçüm (`Pilot/eval/sonuc.md`) ve benchmark aldı | 2026-11-03 |

Silinenler (yeniden üretilebilir veya birebir kopya): `Pre/Pre/` (Pre ile 54/54 dosya aynı, hash ile doğrulandı), yarım ayrıştırma önbellekleri, `__pycache__`.
