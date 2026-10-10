# Pilot kurulum ve ölçüm logu (rapor için ham veri)

> **Tarih:** 2026-10-10 · **Makine:** Apple M4 Pro, 24 GB birleşik bellek, macOS (NVIDIA GPU yok)
> Her şey lokal çalışır, pilot verisi dışarı gönderilmedi. Rakamlar tek makinede, tek seferlik ölçümlerdir.

## 1. Son durum: neyle çalışıyor

| Bileşen | Seçim | Boyut | Not |
|---------|-------|-------|-----|
| LLM | `qwen2.5:7b` (Ollama, %100 GPU) | 4,7 GB | Önce Qwen3-30B-A3B denendi, bu makinede çalışmadı (bkz. 3.1) |
| Embedding | bge-m3 (CPU) | ~2,3 GB | dense + sparse |
| Reranker | bge-reranker-v2-m3 (CPU) | ~2,3 GB | |
| PDF işleme | Docling (CPU, OCR kapalı) + PyMuPDF yedeği | 1,3 GB model | |
| Vektör DB | Qdrant (gömülü) | 36 MB indeks | `data/qdrant/`, yeniden üretilir |
| TTS (isteğe bağlı) | Chatterbox Multilingual (CPU) | ~3,1 GB model, 1,1 GB ortam | 4,6 sn ses için 11,6 sn |
| Python ortamı | uv, Python 3.12 | 1,5 GB | |
| **Toplam (TTS hariç)** | | **~12 GB** | |

Doküman verisi: 7 PDF, 611 sayfa → 2921 parça. Parse ilk çalıştırmada ~11 dk (Docling MPS üzerinde; 578 sn'si Bosch'a gitti, CPU ölçülmedi), indeksleme 618 sn (CPU).

## 2. Ölçüm sonucu (10 soru, qwen2.5:7b)

Ayrıntı: [eval/sonuc.md](eval/sonuc.md). **Doğru: 5/10**, ortalama 14,5 sn/soru, ilk soru (soğuk başlangıç) hariç 13,3 sn (hedef 5 sn).

| Soru türü | Sonuç |
|-----------|-------|
| Değer (ceket 11 ± 1, pantolon 10-14) | Doğru değer ve sayfa bulundu. Model "Yesil ceket" gibi uydurma sözcükler ekledi, atıf [n] koymadı → otomatik doğrulama "kısmen" dedi |
| Arıza (S-7300A üst iplik) | Doğru satır bulundu, cevap kısmen doğru |
| Model tuzağı (S-7300B) | Doğru doküman ve satır bulundu, S-7300A karışmadı. İlk ölçümde doğrulama model kodundaki `7300`'ü uydurma sayı saymıştı (kusur, birim testle bulundu ve düzeltildi) → kısmen doğrulandı |
| Belirsiz soru (marka belirtilmemiş) | Başarısız: model alakasız bir tabloyu "alıntı" diye uydurdu, doğrulama yakaladı |
| Cevapsız (Nike yaka dikişi) | Doğru reddetti |
| Cevapsız (uçak motoru yağı) | Reddetmedi, uydurma alıntı verdi, doğrulama yakaladı |

**Sonuç:** Arama ve kaynak gösterme iyi çalışıyor. 7B model cevap üretiminde yetersiz (araştırma notlarındaki
beklentiyi doğruluyor). Önemli olan, otomatik doğrulama katmanının uydurma alıntıları ve sayıları yakalaması,
yani "yanlış değer ekrana ulaşmıyor" ilkesi çalışıyor. Daha büyük model için GPU/RAM yatırımı gerekir.

## 3. Yaşanan problemler

### 3.1 GPU belleği (en önemli bulgu)
18 GB'lık Qwen3-30B-A3B bu makinede çalıştırıldı. Metal'in GPU için ayırabildiği bellek (24 GB'ın ~16-18 GB'ı)
yetmedi: `Insufficient Memory (kIOGPUCommandBufferCallbackErrorOutOfMemory)`, 1,8 GB swap, arama süresi
3 sn'den 20 sn'ye çıktı ve **ekranda titreme/renk bozulması** yaşandı. Ayrıca Docling'in GPU (MPS) kullanması
yükü artırdı. **Karar:** 7B model (Ollama, GPU'da 4,7 GB ile sorunsuz) + embedding, reranker, Docling ve TTS CPU'da. `PILOT_DOCLING_DEVICE=mps` ile Docling GPU'ya alınabilir ama önerilmez.
24 GB'lık makinede ~14B üstü modeller embedding/reranker ile birlikte çalışmaz.

### 3.2 Diğer
| # | Problem | Etki | Çözüm |
|---|---------|------|-------|
| 1 | bge-m3 ve reranker Apple GPU'da (MPS) yanlış sonuç veriyor (tüm benzerlikler 1,0) | Sessiz hata | CPU'ya sabitlendi |
| 2 | Chatterbox MPS'te bozuk ses (5 sn'lik cümle için 13-40 sn, token hatası) | Kullanılamaz | CPU'ya sabitlendi |
| 3 | Chatterbox `perth` modülü yüklenmedi | TTS başlamıyor | `setuptools<81` |
| 4 | Chatterbox deposundan ~13 GB fazla indirme | Gereksiz disk | Yalnızca kodun yüklediği 6 dosya bırakıldı |
| 5 | Docling Strickland'ın %94'ünü atladı (tam sayfa tarama görseli "picture" sayıldı) | Metin kaybı | Kapsam kontrolü + PDF metin katmanı yedeği (121 sayfa) |
| 6 | Uzun paragraf (SPI değeri 1500 karakterin ortasında) embedding'i seyreltiyor | Zayıf arama | Cümle sınırından bölme, kutu aynı |
| 7 | `format=şema` ile model önce boş alıntı yazıp "bulunamadı" diyordu | Yanlış ret | Şema alan sırası: `bulunamadi` en sonda |
| 8 | Model JSON'u token sınırında yarıda bırakıyor | Hat çökerdi | Yakalanıp "doğrulanamadı" olarak gösteriliyor |
| 9 | Aynı soruda reranker skoru doğru cevapta bile −5,4 olabiliyor (bozuk OCR) | Sabit eşik yanlış ret verir | Eşik kapalı, test setiyle kalibre edilmeli (açık madde) |
| 10 | Soruda "S-7300A" yazsa da S-7300B ilk sıraya çıkabiliyor | Yanlış makine | Sorgu analizi: model kodundan doküman filtresi |
| 11 | Doğrulama: model kodundaki rakamlar (`7300`) uydurma değer sayılıyordu | Doğru cevap "doğrulanamadı" | Harf önekli kodlar değer sayılmaz. Birim testle bulundu |
| 12 | Parçalama dil sınırını aşabiliyordu (Bosch) | Yanlış dil etiketi | Dil değişince parça kapanır (gerçek veride etkilemedi) |

## 4. Açık maddeler (pilotun dışında bırakıldı)
- Daha büyük model (GPU/RAM) ile aynı 10 soru
- Reddetme eşiğinin kalibrasyonu, sorgu çevirisi (sparse kolu için TR→EN)
- Çizim/şekil açıklaması (VLM), STT (sesli soru), yetkilendirme
- Reranker CPU'da 3-7 sn: aday sayısı veya model küçültülebilir
- `Pre/` içindeki Faz 1 betiği ile `Pilot/pilot/parse.py` ortak mantık içerir, birleştirilebilir
