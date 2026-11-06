"""Akış bekçisi benzetimi, kayıtlardan (karar 2026-11-06; model çağrısı yok, uygulamaya bağlı değil).

Kural: akışta art arda N'den fazla boşluk karakteri (boşluk, satır sonu, sekme) gelirse akış kesilir ve istek bir kez
yeniden gönderilir. Kayıtlardaki ham çıktı ve (varsa) akış zaman çizelgesiyle:
  - yakalanan: kesik (finish=length) satırda N+1. boşluğun geldiği an (sn). Zaman çizelgesi yoksa ilk token ile toplam
    süre arasında karakter konumuna göre doğrusal (yaklaşık; satırda işaretli)
  - kaçan: kesik ama N'den uzun boşluk dizisi yok (gerçekten uzun cevap)
  - yanlış alarm: tamamlanmış (finish=stop) satırda N'den uzun boşluk dizisi (bekçi doğru cevabı keserdi)
  - yeniden deneme bedeli: yakalama anı + ikinci denemenin ilk doğrulanmış cümlesi (aynı koşunun p50 / p95'i)
  - ikinci denemede yine kaçak olasılığı: aynı sağlayıcının iki koşusunda aynı soruda kaçak oranı (koşullu), yoksa
    koşunun genel kaçak oranı (bağımsızlık varsayımı)
Kullanıcıya ulaşmayan cevap ≈ (yakalanan × ikinci denemede yine kaçak) + kaçan kesik + diğer JSON hataları + yanlış alarm
× ikinci denemede kaçak; oran model çağrılan sorulara göre.

Kullanım (Pilot klasöründe):  python -m bench.akis_bekcisi     → eval/bench/adim2/akis_bekcisi_<tarih>.md
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from bench.common import percentile

RAW = Path(__file__).resolve().parents[1] / "eval" / "bench" / "adim2" / "ham"
RUNS = {   # sağlayıcı: koşular (kaçak gösteren bütün kayıtlar + karşılaştırma için DeepInfra)
    "Venice": ["nihai_c150bJ_gemma4_venice", "nihai_c150bT_gemma4_venice", "nihai_c150b_gemma4_venice"],
    "Parasail": ["nihai_c150bJ_gemma4_parasail", "nihai_c_gemma4_parasail", "nihai_sure1_gemma4_parasail"],
    "NextBit": ["nihai_c_gemma4_nextbit", "nihai_sure1_gemma4_nextbit"],
    "Gemma 31B (Crusoe)": ["nihai_c_gemma4_31b", "nihai_sure1_gemma4_31b"],
    "DeepInfra": ["nihai_c150bJ_gemma4", "nihai_c150b_gemma4"],
}
NS = (20, 40, 80)


def first_run(raw: str, n: int) -> int | None:
    """N'den uzun ilk boşluk dizisinde N+1. karakterin konumu (bekçinin tetiklendiği karakter sayısı)."""
    m = re.search(r"\s{%d,}" % (n + 1), raw)
    return m.start() + n + 1 if m else None


def at_time(row: dict[str, Any], offset: int) -> tuple[float | None, bool]:
    """Karakter konumunun akıştaki anı: (sn, yaklaşık mı)."""
    tl = row.get("akis_zaman")
    if tl:
        return next((t for t, c in tl if c >= offset), tl[-1][0]), False
    ft, tot, ln = row.get("ilk_token"), row.get("toplam"), len(row.get("ham") or "")
    if ft is None or tot is None or not ln:
        return None, True
    return ft + (offset / ln) * (tot - ft), True


def analyse(name: str, n: int) -> dict[str, Any]:
    R = json.loads((RAW / f"{name}.json").read_text(encoding="utf-8"))["rows"]
    model = {q: r for q, r in R.items() if r.get("ham")}
    caught, missed, false_alarm, other_err, times, approx = [], [], [], [], [], False
    for q, r in model.items():
        off = first_run(r["ham"], n)
        if r.get("finish") == "length":
            if off is None:
                missed.append(q)
            else:
                caught.append(q)
                t, ap = at_time(r, off)
                approx |= ap
                if t is not None:
                    times.append(t)
        else:
            if off is not None:
                false_alarm.append(q)
            if r.get("cikis") == "json_hata":
                other_err.append(q)
    fv = [r["ilk_dogrulanmis_cumle"] for r in model.values() if r.get("ilk_dogrulanmis_cumle")]
    return {"run": name, "n_model": len(model), "caught": caught, "missed": missed, "false_alarm": false_alarm,
            "other_err": other_err, "t": times, "approx": approx, "fv50": percentile(fv, .5), "fv95": percentile(fv, .95),
            "runaway_rate": len(caught) / max(len(model), 1)}


def repeat_prob(provider: str, n: int) -> tuple[float | None, str]:
    """Aynı sağlayıcının iki tam koşusunda (aynı sorular) kaçak yaşanan soruların ikinci koşuda da kaçak olma oranı."""
    data = {}
    for name in RUNS[provider]:
        R = json.loads((RAW / f"{name}.json").read_text(encoding="utf-8"))["rows"]
        data[name] = ({q for q, r in R.items() if r.get("ham")},
                      {q for q, r in R.items() if r.get("finish") == "length" and first_run(r.get("ham") or "", n)})
    hit = base = 0          # bütün koşu çiftlerinde: A'da kaçan ve B'de de sorulan sorular; B'de de kaçan
    names = [k for k, (_, s) in data.items() if s]
    for a in names:
        for b in names:
            if a != b:
                common = data[a][1] & data[b][0]
                base += len(common)
                hit += len(common & data[b][1])
    if not base:
        return None, "tek koşuda kaçak var"
    return hit / base, f"koşu çiftleri: {hit} / {base}"


def report() -> str:
    s_ = lambda x: "–" if x is None or x != x else f"{x:.2f} sn".replace(".", ",")
    L = ["# Akış bekçisi benzetimi (kayıtlardan; model çağrısı yok)", "",
         "Kural: akışta art arda N'den fazla boşluk karakteri gelirse akış kesilir, istek bir kez yeniden gönderilir. "
         "Uygulamaya bağlı değil. Araç: `bench/akis_bekcisi.py`. Yaklaşık (≈): kayıtta akış zaman çizelgesi yok, yakalama "
         "anı karakter konumundan doğrusal.", ""]
    for n in NS:
        L += [f"## N = {n}", "",
              "| Sağlayıcı | Koşu | model çağrısı | kesik: yakalanan / kaçan | yanlış alarm | yakalama anı p50 / p95 | "
              "ikinci deneme ilk doğr. cümle p50 / p95 | toplam bedel p50 / p95 | ikinci denemede yine kaçak (tahmin) | "
              "kullanıcıya ulaşmayan (tahmin) |", "|---|---|---|---|---|---|---|---|---|---|"]
        for prov, runs in RUNS.items():
            rp, how = repeat_prob(prov, n)
            for name in runs:
                if not (RAW / f"{name}.json").exists():
                    continue
                a = analyse(name, n)
                p2 = rp if rp is not None else a["runaway_rate"]
                lost = (len(a["caught"]) + len(a["false_alarm"])) * p2 + len(a["missed"]) + len(
                    [q for q in a["other_err"] if q not in a["caught"]])
                t50, t95 = percentile(a["t"], .5), percentile(a["t"], .95)
                pre = "≈ " if a["approx"] and a["t"] else ""
                L.append(f"| {prov} | {name.replace('nihai_', '')} | {a['n_model']} | {len(a['caught'])} / {len(a['missed'])} | "
                         f"{len(a['false_alarm'])} | {pre}{s_(t50)} / {s_(t95)} | {s_(a['fv50'])} / {s_(a['fv95'])} | "
                         f"{pre}{s_(t50 + a['fv50']) if a['t'] else '–'} / {s_(t95 + a['fv95']) if a['t'] else '–'} | "
                         f"{p2:.0%} ({how if rp is not None else 'koşunun kaçak oranı'}) | "
                         f"{lost:.1f} ({lost / max(a['n_model'], 1):.1%}) |")
        L.append("")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    out = RAW.parent / f"akis_bekcisi_{date.today().isoformat()}.md"
    out.write_text(report(), encoding="utf-8")
    print(out)
    print(out.read_text(encoding="utf-8"))
