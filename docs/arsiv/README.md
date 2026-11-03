# Arşiv

Kullanılmayan ama silinmesi gerekmeyen dosyalar. Projenin çalışması bu klasöre bağlı değildir.

| Klasör | Ne | Neden arşivde | Tarih |
|--------|----|---------------|-------|
| `pilot-taslak-2026-10-09/visual_agent/` | Yarım kalan ilk pilot taslağı: doküman işleme, BM25 + Qdrant arama, marka bazlı yetki filtresi (`security.py`), iki yönlü sayı-tolerans doğrulaması (`verification/`) | Repodaki pilot (`pilot/pilot/`) yerini aldı. `security.py` (e-posta/kod girişi, rol → marka, ±1 sayfa) ve `verification/numbers.py` uygulama aşamasında (Aşama 4 ve 1) başlangıç noktası olarak kullanılabilir | 2026-10-13 |
| `pilot-taslak-2026-10-09/config/` | `documents.json` (doküman kaydı + erişim türü), `users.json` (örnek kullanıcılar, kodlar SHA-256) | Aynı nedenle | 2026-10-13 |
| `pilot-taslak-2026-10-09/scripts/` | `parse_all.py` (parti parti, kaldığı yerden devam eden ayrıştırma) | Aynı nedenle | 2026-10-13 |

Silinenler (yeniden üretilebilir veya birebir kopya): `Pre/Pre/` (Pre ile 54/54 dosya aynı, hash ile doğrulandı), yarım ayrıştırma önbellekleri, `__pycache__`.
