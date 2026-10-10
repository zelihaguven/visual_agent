# Visual Agent: Pilot

Araştırma aşamasının küçük, **tamamen lokal** pilotu: yazılı Türkçe soru → hibrit arama + reranker →
kaynaklı cevap → otomatik doğrulama → **vurgulu kaynak sayfa** → (isteğe bağlı) sesli okuma.

> Bu bir üretim sistemi değil. Amaç, araştırma notlarındaki mimarinin uçtan uca çalıştığını ve
> nerede zorlandığını **ölçmek**. Sonuçlar: [eval/sonuc.md](eval/sonuc.md) ve [KURULUM-LOGU.md](KURULUM-LOGU.md).

## Gereksinimler

| | |
|---|---|
| Makine | 16 GB+ RAM önerilir (24 GB'ta denendi, Apple M4 Pro). GPU şart değil |
| Yazılım | Python 3.12, [uv](https://docs.astral.sh/uv/), [Ollama](https://ollama.com/download) |
| Disk | ~12 GB (model 4,7 GB + embedding/reranker 4,6 GB + ortam 1,5 GB) |
| Ağ | Yalnızca kurulumda (model indirme). Çalışırken hiçbir veri dışarı gitmez |

## Kurulum ve çalıştırma

```bash
cd Pilot
./setup.sh                                  # ortam + model + indeks (~15-25 dk)
.venv/bin/streamlit run app.py              # arayüz
.venv/bin/python run_eval.py                # 10 soruluk ölçüm -> eval/sonuc.md
.venv/bin/python -m pytest                  # 83 birim test, <1 sn (model/PDF gerekmez)
```

Başka bir model denemek için: `PILOT_LLM_MODEL=qwen3:14b ./setup.sh` (24 GB RAM'de 14B'den büyüğü önerilmez,
bkz. KURULUM-LOGU.md "GPU belleği").

Parse edilmiş dokümanlar (`data/parsed/`, `data/chunks.jsonl`) repoda hazır gelir. Sıfırdan parse etmek için
`python run_parse.py` (Docling, CPU).

## Yapı

```
Pilot/
├── pilot/            # kütüphane: parse, chunk, embed, index, retrieve, query, llm, verify, speech, pipeline
├── app.py            # Streamlit arayüzü
├── run_parse.py      # PDF -> data/parsed/
├── run_index.py      # chunk + Qdrant indeksi
├── run_eval.py       # ölçüm
├── eval/             # test soruları ve sonuç
├── tests/            # birim testler (verify, speech, query, parse/chunk, pipeline)
├── tools/            # kurulum doğrulama betikleri, TTS yardımcısı
└── KURULUM-LOGU.md   # boyut/süre/yaşanan sorunlar (rapor için)
```

Doküman kaynakları ve lisans notu: [../Pre/notes/manual-envanteri.md](../Pre/notes/manual-envanteri.md).
Araştırma dokümanları: [../Pre/sentez.md](../Pre/sentez.md).
