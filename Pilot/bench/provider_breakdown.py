"""Bugünkü süre ölçümlerinde yanıt veren sağlayıcıya göre süre ve 429 dökümü (kayıtlardan; yeni çağrı yok).

Kaynaklar (2026-11-05):
    süre sınırı      eval/bench/b4/asama4_sure_siniri_2026-11-05.json   Qwen3-8B embed, cevap modeli (mistral-small 2501)
    Adım 2           eval/bench/adim2/ham/{ana,sure2}_<model>.json      cevap modelleri, tek sağlayıcıya sabit
    çeviri           data/bench_cache/ceviri_cmp_cagrilar_<tur>.json   Gemma 3 / Gemma 4, tek sağlayıcıya sabit
Süre sınırı ölçümünde çeviri çağrısının sağlayıcısı kaydedilmemişti (uygulamanın CloudChat'i); kuyruk ölçümü (11-03)
sağlayıcı kaydetmiyor. Qwen'de çağrının kendi süresi (qwen_ilk_sn) ilk isteğindir; sağlayıcısı, hedge kazanmadıysa
kayıttaki sağlayıcıdır (hedge kazanan 2 soru dışarıda).

Kullanım (Pilot klasöründe): python -m bench.provider_breakdown [--ceviri t1 t2]
    → eval/bench/b4/saglayici_dokumu_2026-11-05.md
"""
import argparse
import json
from collections import defaultdict
from typing import Any

from bench.common import OUT_DIR, PILOT_DIR, percentile

DATE = "2026-11-05"


def fmt(x: float) -> str:
    return "–" if x != x else (f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn".replace(".", ","))


def table(title: str, groups: dict[tuple[str, str], dict[str, list]], note: str, metric: str) -> list[str]:
    L = [f"## {title}", "", note, "", f"| Ölçüm | Sağlayıcı | çağrı | {metric} p50 | p95 | en uzun | > 1,5 sn | 429 | diğer hata |",
         "|---|---|---|---|---|---|---|---|---|"]
    for (src, prov), g in sorted(groups.items()):
        s = g["sn"]
        L.append(f"| {src} | {prov} | {len(s) + len(g['err'])} | {fmt(percentile(s, .5))} | {fmt(percentile(s, .95))} | "
                 f"{fmt(max(s) if s else float('nan'))} | {sum(x > 1.5 for x in s)} | "
                 f"{sum(e.startswith('429') for e in g['err'])} | {sum(not e.startswith('429') for e in g['err'])} |")
    return L + [""]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ceviri", nargs="*", default=["t1", "t2"])
    a = ap.parse_args()
    new = lambda: {"sn": [], "err": []}

    guard = json.loads((OUT_DIR / "b4" / f"asama4_sure_siniri_{DATE}.json").read_text(encoding="utf-8"))["rows"]
    qwen: dict[tuple[str, str], dict[str, list]] = defaultdict(new)
    ans: dict[tuple[str, str], dict[str, list]] = defaultdict(new)
    for r in guard:
        if r["qwen"] != "hedge":
            prov = r["qwen_provider"] or "(yanıt yok)"
            (qwen[("süre sınırı 09:19", prov)]["sn"]).append(r["qwen_ilk_sn"])
        # Kayıttaki ilk token sorunun başından: sağlayıcının kendi süresi = ilk token − grup 1 − grup 2 (yalnız ilk
        # akış kazandıysa). Yanıt vermeyen akışın sağlayıcısı boş: mistral-small 2501'in tek ZDR sağlayıcısı DeepInfra.
        g = ans[("süre sınırı 09:19 · mistral-small 2501", r["cevap_provider"] or "DeepInfra")]
        if r.get("cevap_ilk_token") is not None and r["cevap"] == "ilk":
            g["sn"].append(r["cevap_ilk_token"] - r["grup1"] - r["grup2"])
        if r.get("cevap_hata"):
            g["err"].append(r["cevap_hata"])

    for f in sorted((OUT_DIR / "adim2" / "ham").glob("*_*.json")):
        tag, model = f.stem.split("_", 1)
        if tag not in ("ana", "sure2"):
            continue
        d: dict[str, Any] = json.loads(f.read_text(encoding="utf-8"))
        when = d.get("start", "")[11:16]
        for r in d["rows"].values():
            for att in r.get("denemeler") or []:
                g = ans[(f"Adım 2 {tag} {when} · {model}", r.get("provider") or d["spec"].get("provider", "?"))]
                if att["err"]:
                    g["err"].append(att["err"])
            if r.get("ilk_token") is not None:
                ans[(f"Adım 2 {tag} {when} · {model}", r.get("provider") or "?")]["sn"].append(r["ilk_token"])

    tr: dict[tuple[str, str], dict[str, list]] = defaultdict(new)
    for t in a.ceviri:
        p = PILOT_DIR / "data" / "bench_cache" / f"ceviri_cmp_cagrilar_{t}.json"
        if not p.exists():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        for c in d["cagrilar"]:
            g = tr[(f"çeviri {t} ({d['bitis'][11:16]} bitiş) · {c['kol']}", c.get("provider") or c["kol"].split("_")[1])]
            (g["err"] if c["err"] else g["sn"]).append(c["err"] or c["sn"])

    L = [f"# Sağlayıcıya göre süre ve 429 dökümü ({DATE}, kayıtlardan; yeni çağrı yok)", "",
         "Soru: Kuyruk (uzun süre) ve 429 sorunları belirli bir sağlayıcıda (özellikle DeepInfra) mı toplanıyor? Araç: "
         "`python -m bench.provider_breakdown`. Süre sınırı ölçümünde çeviri çağrısının sağlayıcısı kaydedilmemişti; "
         "3 Kasım kuyruk ölçümü sağlayıcı kaydetmiyor. Adım 2 ve çeviri ölçümlerinde her model tek sağlayıcıya sabit "
         "(karşılaştırma modeller ve saatler arası); süre sınırı ölçümünde Qwen sağlayıcıyı OpenRouter seçti.", ""]
    L += table("Qwen3-8B embed (süre sınırı ölçümü, çağrının kendi süresi)", qwen,
               "Sağlayıcı sabitlenmedi: OpenRouter ZDR'li sağlayıcılar arasında seçti. Hedge kazanan 2 soru dışarıda.",
               "süre")
    L += table("Cevap modelleri (ilk token)", ans, "429 ve diğer hata: çağrı denemeleri (süre sınırı: ilk akışın hatası).",
               "ilk token")
    L += table("Çeviri (çağrının tamamı)", tr, "Kollar iç içe, tek sağlayıcıya sabit, yeniden denemesiz.", "süre")
    out = OUT_DIR / "b4" / f"saglayici_dokumu_{DATE}.md"
    out.write_text("\n".join(L), encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
