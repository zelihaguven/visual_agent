"""OCR entegrasyonu regresyon kontrolü (karar 2026-11-06, ek 1a ve PLAN-OCR ek 1). Model ve ağ yok.

pilot/ocr.py ile (sayfa sınıfına göre bayrak, sayfa başına dil, eski/yeni katman seçimi, OCR sonrası süzgeç) belge
geçici klasöre OCR'lanır (gerçek config.OCR_DIR'e dokunmaz). Sonra sayfa sayfa, değer değer:
  - eski katmandaki sayılar (verify ile aynı kanonik biçim, çoklu küme) ile seçilmiş son katmanınkiler karşılaştırılır;
  - eskide olup sonda olmayan her değer "kaybolan" diye bağlamıyla listelenir (eskide doğru muydu: sayfa görüntüsüne
    bakılarak elle karar verilir; araç doğruluğa karar vermez);
  - sonda olup eskide olmayanlar "yeni" (düzeltme ya da yeni okunmuş değer).
Sayfa seçim kuralının testi: "eski" seçilen sayfalarda kayıp olmamalı.

Kullanım (Pilot klasöründe):  $env:PILOT_ANSWER_MODE = "bugun"; python -m bench.ocr_regresyon gl-pd-07-14a [--yeniden]
  --yeniden: OCR yeniden yapılır; yoksa data/ocr_test/entegrasyon/ içindeki çıktıdan yalnız rapor
Çıktı: eval/bench/ocr/ocr_regresyon_<doc>.md ve ham/ocr_regresyon_<doc>.json; OCR'lı PDF data/ocr_test/entegrasyon/
"""
from __future__ import annotations

import json
import re
import sys
import time
from collections import Counter
from typing import Any

from bench.common import PILOT_DIR

OUT = PILOT_DIR / "eval" / "bench" / "ocr"
WORK = PILOT_DIR / "data" / "ocr_test" / "entegrasyon"


def numbers(text: str) -> list[tuple[str, int]]:
    """(kanonik değer, metindeki konum) — verify.numbers_in'in çoklu ve konumlu hali."""
    from pilot import verify as V
    t = V.canon_chars(text)
    t = re.sub(r"(?<![\d.,])[.,](\d)", r"0.\1", t)
    cleaned = V.CODE_RE.sub(lambda m: " " * len(m.group(0)), V.LIST_MARK_RE.sub(lambda m: " " * len(m.group(0)), t))
    return [(V._canon_num(m.group(0)), m.start()) for m in V.NUM_RE.finditer(cleaned)]


def ctx(text: str, pos: int, w: int = 45) -> str:
    return re.sub(r"\s+", " ", text[max(0, pos - w): pos + w]).strip()


# OCR'ın karıştırdığı karakterler (parse._OCR_CONFUSABLE'ın genişletilmişi): eski "112" ile yeni "1/2" aynı okumanın iki
# hali sayılır ("/" → "1"). Ayırıcılar ("-", ".") eşlenmez: "43-3/8" ile "43.3/8" farklı değerdir.
_CONF = str.maketrans({"/": "1", "l": "1", "I": "1", "i": "1", "|": "1", "!": "1", "]": "1", "S": "5", "s": "5",
                       "O": "0", "o": "0", "B": "8", "Z": "2", "≥": "~", "±": "~", "+": "~"})


def _ck(s: str) -> str:
    return re.sub(r"\s+", "", s).translate(_CONF)


def changes(old: str, new: str) -> list[dict[str, Any]]:
    """Kelime hizalamasıyla (difflib) sayı içeren değişen bölümler, sınıflı:
    duzeltme  OCR-karışık karakter eşlemesiyle aynı (112 → 1/2, IS → 15, ISO → 150)
    bicim     yalnız boşluk/virgül farkı (135,3 → 135, 3; "43-3/8" → "43.3/8" bicim değil)
    tasindi   eski bölümün sayıları yeni sayfada başka yerde var (tablo okuma sırası)
    inceleme  geri kalan: sayfa görüntüsüne bakılarak elle karar verilir"""
    import difflib

    from pilot.verify import numbers_in
    ow, nw = old.split(), new.split()
    new_nums = Counter(v for v, _ in numbers(new))
    out = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, ow, nw, autojunk=False).get_opcodes():
        if op == "equal":
            continue
        o, n = " ".join(ow[i1:i2]), " ".join(nw[j1:j2])
        if not (re.search(r"\d", o) or re.search(r"\d", n)):
            continue
        if numbers_in(o) == numbers_in(n):
            continue
        if _ck(o) == _ck(n):
            # aynı okuma: yeni sayıya dönüştüyse düzeltme, sayı harfe döndüyse ("5-thread" → "S-thread") inceleme
            kind = "duzeltme" if len(numbers_in(n)) >= len(numbers_in(o)) else "inceleme"
        elif re.sub(r"[\s,]", "", o) == re.sub(r"[\s,]", "", n):
            kind = "bicim"
        elif op == "delete" and all(new_nums[v] for v in numbers_in(o)):
            kind = "tasindi"
        else:
            kind = "inceleme"
        out.append({"sinif": kind, "eski": o[:120], "yeni": n[:120]})
    return out


def compare(old: str, new: str) -> dict[str, Any]:
    on, nn = numbers(old), numbers(new)
    oc, nc = Counter(v for v, _ in on), Counter(v for v, _ in nn)
    lost, gained = oc - nc, nc - oc
    lost_rows = []
    for v, k in lost.items():
        pos = [p for x, p in on if x == v][:k]
        lost_rows.append({"deger": v, "adet": k, "eski_baglam": [ctx(old, p) for p in pos]})
    return {"eski_sayi": sum(oc.values()), "yeni_sayi": sum(nc.values()), "kaybolan": lost_rows,
            "eklenen": sorted(gained.elements()), "degisimler": changes(old, new)}


def main() -> None:
    from bench import require_mode
    require_mode("bugun")
    import pymupdf

    from pilot import config
    from pilot import ocr as O
    from pilot.registry import BY_ID
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    did = args[0] if args else "gl-pd-07-14a"
    meta = BY_ID[did]
    config.OCR_DIR = WORK
    t = time.perf_counter()
    rec = O.ocr_document(meta, force="--yeniden" in sys.argv)      # yoksa mevcut OCR çıktısı (yalnız rapor)
    secs = time.perf_counter() - t
    dec = {d["page"]: d for d in rec["sayfalar"]}
    rows = []
    with pymupdf.open(str(meta.source_path)) as a, pymupdf.open(str(meta.path)) as b:
        for i in range(len(a)):
            p = i + 1
            old, new = a[i].get_text(), b[i].get_text()
            c = compare(old, new)
            rows.append({"sayfa": p, **{k: dec[p][k] for k in ("kind", "lang", "old_score", "new_score", "chosen", "reason")}, **c})
    summ = {"belge": did, "sayfa": len(rows), "sure_sn": round(secs, 1), "secim": dict(Counter(r["chosen"] for r in rows)),
            "eski_sayi": sum(r["eski_sayi"] for r in rows), "son_sayi": sum(r["yeni_sayi"] for r in rows),
            "kaybolan_deger": sum(x["adet"] for r in rows for x in r["kaybolan"]),
            "kayipli_sayfa": sum(bool(r["kaybolan"]) for r in rows),
            "eklenen_deger": sum(len(r["eklenen"]) for r in rows),
            "degisim_sinifi": dict(Counter(x["sinif"] for r in rows for x in r["degisimler"])),
            "ocr_sure_sn": rec.get("sure_sn")}
    (OUT / "ham").mkdir(parents=True, exist_ok=True)
    (OUT / "ham" / f"ocr_regresyon_{did}.json").write_text(
        json.dumps({"ozet": summ, "satirlar": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    L = [f"# OCR regresyon kontrolü: {did}", "",
         f"{time.strftime('%Y-%m-%d %H:%M')}. pilot/ocr.py (sayfa sınıfı → bayrak, sayfa başına dil, eski/yeni seçimi, "
         "süzgeç). Değerler verify'ın kanonik sayı biçiminde, sayfa başına çoklu küme. \"Kaybolan\" = eski katmanda "
         "olup son katmanda olmayan; doğru olup olmadığı sayfa görüntüsünden elle değerlendirilir.", "",
         "| Ölçü | Değer |", "|---|---|"] + [f"| {k} | {v} |" for k, v in summ.items()]
    L += ["", "| Sayfa | sınıf | dil | skor eski → yeni | seçim | eski / son sayı | kaybolan | eklenen |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        ns = "–" if r["new_score"] is None else f"{r['new_score']:.2f}"
        L.append(f"| {r['sayfa']} | {r['kind']} | {r['lang'] or '–'} | {r['old_score']:.2f} → {ns} | {r['chosen']} | "
                 f"{r['eski_sayi']} / {r['yeni_sayi']} | {', '.join(str(x['deger']) + '×' + str(x['adet']) for x in r['kaybolan']) or '–'} | "
                 f"{', '.join(r['eklenen'][:12]) or '–'} |")
    L += ["", "## Sayı içeren değişimler: inceleme gerekenler (kelime hizalaması; düzeltme, biçim, taşınan hariç)", "",
          "| Sayfa | eski katman | yeni katman |", "|---|---|---|"]
    for r in rows:
        for x in r["degisimler"]:
            if x["sinif"] == "inceleme":
                L.append(f"| {r['sayfa']} | `{x['eski']}` | `{x['yeni']}` |")
    L += ["", "## Düzeltme sınıfına girenlerden örnekler", ""]
    ex = [(r["sayfa"], x) for r in rows for x in r["degisimler"] if x["sinif"] == "duzeltme"]
    L += [f"- s.{p}: `{x['eski']}` → `{x['yeni']}`" for p, x in ex[:25]]
    p = OUT / f"ocr_regresyon_{did}.md"
    p.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(json.dumps(summ, ensure_ascii=False))
    print(p)


if __name__ == "__main__":
    main()
