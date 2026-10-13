"""STT ölçümü: eval/stt/*.wav → tanınan metin, süre, varlık doğruluğu (doğru makine/ürün okundu mu).

Genel kelime hata oranı (WER) yerine varlık doğruluğuna bakılır: "S-7300A"nın "S-7300B" yazılması tek kelime hatası
ama yanlış kılavuz demek (R9). Kullanım (pilot/ klasöründe):
    $env:PILOT_STT_MODEL="small"; ..\\.venv\\Scripts\\python.exe tools\\measure_stt.py
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pilot.config import STT_MODEL  # noqa: E402
from pilot.query import analyze_query  # noqa: E402
from pilot.stt import _model, transcribe  # noqa: E402
from pilot.terms import _norm  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
items = json.loads((ROOT / "eval" / "stt_sorular.json").read_text(encoding="utf-8"))

t = time.time()
_model()
load = time.time() - t
print(f"model {STT_MODEL}: yükleme {load:.1f} sn")

rows = []
for it in items:
    wav = ROOT / "eval" / "stt" / f"{it['id']}.wav"
    if not wav.exists():
        print(f"{it['id']}: ses yok, atlandı")
        continue
    tr = transcribe(wav.read_bytes())
    docs = sorted(analyze_query(tr.text).doc_ids)
    doc_ok = docs == sorted(it["expect_docs"])
    terms_ok = all(term in _norm(tr.text) for term in it["expect_terms"])
    rows.append({"id": it["id"], "spoken": it["spoken"], "text": tr.text, "docs": docs, "doc_ok": doc_ok,
                 "terms_ok": terms_ok, "audio_s": round(tr.audio_seconds, 1), "stt_s": round(tr.seconds, 1),
                 "logprob": round(tr.avg_logprob, 2), "low": tr.low_confidence})
    print(f"{it['id']} [{'✔' if doc_ok else '✖'} kaynak, {'✔' if terms_ok else '✖'} terim] "
          f"{tr.audio_seconds:.1f} sn ses → {tr.seconds:.1f} sn · {tr.avg_logprob:.2f} | {tr.text}")

out = ROOT / "eval" / f"stt_sonuc_{STT_MODEL}.json"
out.write_text(json.dumps({"model": STT_MODEL, "load_s": round(load, 1), "rows": rows}, ensure_ascii=False, indent=1),
               encoding="utf-8")
n = len(rows)
print(f"== kaynak doğru {sum(r['doc_ok'] for r in rows)}/{n}, terim doğru {sum(r['terms_ok'] for r in rows)}/{n}, "
      f"ortalama çeviri {sum(r['stt_s'] for r in rows) / max(n, 1):.1f} sn → {out.name}")
