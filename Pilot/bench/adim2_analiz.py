"""Adım 2 ilk tur kayıtlarından analiz (yeni model çağrısı yok).

Kayıtlı ham model çıktıları (eval/bench/adim2/ham/<tag>_<model>.json) aynı arama önbelleğiyle pipeline.soru_cevapla'dan
yeniden geçirilir; model yerine kayıtlı çıktı döner. Böylece verify.py'ye giden kaynaklar ve cevap aynen elde edilir.

1. "Alıntıda olmayan sayı" vakalarının sınıfları (sırayla ilk eşleşen):
   atif      sayı yalnız çoklu atfın içinde ("[1, 2]"): verify.py yalnız "[1]" biçimini atıf sayıyor
   sira      liste numarası verify.py'nin tanımadığı yerde: atıftan sonra ("... [1, 5] 2. Uygun"), <br> satır sonundan
             sonra, Markdown kalından önce ("1. **Long**")
   bicim     alıntıda aynı değer başka biçimde (ondalık virgül/nokta, sondaki sıfır "2.00", ".5", binlik ayırıcı, kesir)
   yazi      alıntıda yazıyla ("six months" → "6 ay")
   soruda    soruda var
   kaynakta  kaynak metninde var, alıntıda yok
   birim     alıntıdaki bir değerin birim dönüşümü (inç↔mm/cm, lb↔kg, oz↔g, ft↔m, bar↔psi)
   yok       hiçbirinde yok: elle okunur (OCR düzeltmesi, hesaplama, uydurma)
2. Önerilen genel düzeltme (verify.py'ye uygulanmadı) ile dört modelin önce/sonra rozetleri: A (atıf, liste, biçim) ve
   A + yazıyla sayılar.
3. Cevap uzunluğu: model başına çıktı token p50/p95 ve ✖ ile ilişkisi.

Kullanım (Pilot klasöründe; Qdrant gerekmez):
    python -m bench.adim2_analiz            # eval/bench/adim2/adim2_analiz_<tarih>.md (+ .json vakalar)
"""
import argparse
import json
import re
from collections import Counter
from datetime import date
from typing import Any

from bench.answer_models import MODELS, RAW_DIR, install_search_cache, parse_answer, questions
from bench.common import percentile

OUT_DIR = RAW_DIR.parent
QUOTE_RE = re.compile(r'"metin"\s*:\s*"((?:[^"\\]|\\.)*)"')
STRAY_RE = re.compile(r"Alıntıda olmayan sayı\(lar\): \[(.*?)\]")
# Çoklu atıf: "[1, 2]", "[2,3,5]", "[1; 4]", "[1-3]"
MULTI_CITE_RE = re.compile(r"\[(\d+(?:\s*[,;–-]\s*\d+)+)\]")
FACTORS = {"inç→mm": 25.4, "inç→cm": 2.54, "lb→kg": 0.45359, "oz→g": 28.35, "ft→m": 0.3048, "bar→psi": 14.504}
LABEL = {"atif": "doğrulayıcı: çoklu atıf [1, 2]", "sira": "doğrulayıcı: liste numarası",
         "bicim": "biçim farkı (virgül/nokta, sıfır, kesir)", "yazi": "alıntıda yazıyla", "soruda": "soruda var",
         "kaynakta": "kaynakta var, alıntıda yok", "birim": "birim dönüşümü", "yok": "kaynakta da yok"}


# ---------- önerilen genel düzeltme (verify.py'ye uygulanmadı) ----------

def split_cites(text: str) -> str:
    """'[1, 2]' → '[1][2]', '[1-3]' → '[1][2][3]': tek biçim atıf."""
    def one(m: re.Match) -> str:
        nums: list[int] = []
        for part in re.split(r"\s*[,;]\s*", m.group(1)):
            a, b = (re.split(r"\s*[–-]\s*", part) + [""])[:2]
            nums += list(range(int(a), int(b) + 1)) if b and 0 <= int(b) - int(a) < 20 else [int(a)] + ([int(b)] if b else [])
        return "".join(f"[{n}]" for n in nums)
    return MULTI_CITE_RE.sub(one, text)


def canon_v2(s: str) -> str:
    """Değer olarak kanonik: virgül → nokta, ondalık sondaki sıfırlar atılır ("2.00" → "2", "0.50" → "0.5")."""
    s = s.replace(",", ".")
    return s.rstrip("0").rstrip(".") if "." in s else s


# Liste işareti: verify.LIST_MARK_RE ile aynı; büyük harfe ek olarak Markdown kalın da madde başı ("1. **Long**")
LIST_MARK_V2 = re.compile(r"(?:^\s*|(?<=[.:;])\s+)\d{1,2}[.)]\s+(?=[A-ZÇĞİÖŞÜ*])|^\s*\d{1,2}[.)]\s+", re.MULTILINE)
# Alıntıda yazıyla sayı, EN/ES/FR/TR 1–12 (yalnız alıntı tarafında: cevaptaki "bir ekip" sayı sayılmaz). Başka dilde
# sık kelime olanlar yok: "on" (TR 10 / EN on), "once" (ES 11 / EN once), "un"/"une"/"una" (FR/ES artikel).
WORDS = {w: i for ws in ("one two three four five six seven eight nine ten eleven twelve",
                         "uno dos tres cuatro cinco seis siete ocho nueve diez - doce",
                         "- deux trois quatre cinq six sept huit neuf dix onze douze",
                         "bir iki üç dört beş altı yedi sekiz dokuz - onbir oniki")
         for i, w in enumerate(ws.split(), 1) if w != "-"} | {"twice": 2}
WORD_RE = re.compile(r"(?<!\w)(" + "|".join(sorted(WORDS, key=len, reverse=True)) + r")(?!\w)", re.I)


def word_numbers(text: str) -> set[str]:
    return {str(WORDS[w.lower()]) for w in WORD_RE.findall(text)}


def numbers_in_v2(text: str) -> set[str]:
    """Atıflar liste işaretlerinden ÖNCE ayıklanır; çoklu atıf tanınır; <br> satır sonu; ".5" → "0.5"; kanonik."""
    from pilot import verify as V
    t = V.CITE_RE.sub("", split_cites(re.sub(r"<br\s*/?>", "\n", text, flags=re.I)))
    t = re.sub(r"(?<![\d.,])[.,](\d)", r"0.\1", t)
    cleaned = V.CODE_RE.sub(" ", LIST_MARK_V2.sub("", t))
    return {canon_v2(m.group(0)) for m in V.NUM_RE.finditer(cleaned)}


def proposed_verify(answer: dict, sources: dict, generated: dict | None = None, words: bool = False) -> Any:
    """verify.py + öneri: cevap ve sesli metindeki çoklu atıflar tekliye çevrilir, sayılar numbers_in_v2 ile.
    words: alıntıda yazıyla geçen sayılar (1–12) da alıntı sayısı kabul edilir."""
    from pilot import verify as V
    a = dict(answer)
    for f in ("cevap", "sesli_metin"):
        if isinstance(a.get(f), str):
            a[f] = split_cites(a[f])
    quote_text = " ".join(q.get("metin", "") for q in a.get("alintilar") or [] if isinstance(q, dict))
    old = V.numbers_in
    V.numbers_in = lambda t: numbers_in_v2(t) | (word_numbers(t) if words and t == quote_text else set())
    try:
        return V.verify(a, sources, generated)
    finally:
        V.numbers_in = old


# ---------- yeniden oynatma ----------

def replay(key: str, tag: str = "ana", patch: Any = None) -> dict[str, dict[str, Any]]:
    """Kayıtlı çıktıyı pipeline'dan geçir: {qid: {row, q, res, answer, sources, kesik_kayit}} (cevaplı sorularda
    üretilen cevaplar). 2026-11-05 "ana" koşusu ham çıktıyı 1500 karakterde kesiyordu (sonra düzeltildi): Bunlarda cevap
    ayrıştırılamaz; kaynaklar yine pipeline'dan, alıntılar kesik metinden, cevap kayıttaki ilk 600 karakterden alınır."""
    from pilot import pipeline
    install_search_cache(frozen=True)
    qs = {q["qid"]: q for q in questions()}
    rows = json.loads((RAW_DIR / f"{tag}_{key}.json").read_text(encoding="utf-8"))["rows"]
    orig, cur, out = pipeline.verify, {}, {}

    def cap(answer: dict, sources: dict, generated: dict | None = None) -> Any:
        cur.update(answer=answer, sources=sources)
        return (patch or orig)(answer, sources, generated)

    pipeline.verify = cap
    try:
        for qid, row in rows.items():
            if row.get("cikis") != "cevap" or qid not in qs or qs[qid].get("expect_not_found"):
                continue
            ans = parse_answer(row["ham"], row.get("finish"))[0]
            cut = ans is None
            if cut:   # yalnız kaynakları almak için alıntısız sahte cevap
                ans = {"alintilar": [], "cevap": "-", "sesli_metin": "", "bulunamadi": False}
            pipeline.chat_json = lambda _u, a=ans: (dict(a), {"llm_seconds": 0.0})
            cur.clear()
            res = pipeline.soru_cevapla(qs[qid]["q"])
            if cut:
                cur["answer"] = {"alintilar": [{"metin": json.loads(f'"{m}"')} for m in QUOTE_RE.findall(row["ham"])],
                                 "cevap": row.get("cevap", ""), "sesli_metin": ""}
            out[qid] = {"row": row, "q": qs[qid], "res": None if cut else res, "kesik_kayit": cut, **cur}
    finally:
        pipeline.verify = orig
    return out


def status_from(checks: dict[str, Any]) -> str:
    """verify.py + pipeline varyant kuralıyla aynı karar (kesik kayıtlar için)."""
    hard = ("alinti_var", "alinti_birebir", "sayilar_alintida", "tolerans_tam", "cevap_var", "tekrar_yok", "alfabe_dogru")
    if any(checks.get(k) is False for k in hard):
        return "failed"
    ok = checks.get("atif_gecerli") and checks.get("alinti_kaynak_metni", True) and checks.get("varyant_belirli", True)
    return "verified" if ok else "partial"


def rescore_cut(c: dict[str, Any], words: bool = False) -> str:
    """Kesik kayıtta önerinin rozeti (yaklaşık): sayı ve atıf kontrolleri kayıttaki cevaptan yeniden, gerisi kayıttan."""
    a = c["answer"]
    quote = " ".join(x.get("metin", "") for x in a["alintilar"])
    checks = dict(c["row"]["kontroller"])
    qn = numbers_in_v2(quote) | (word_numbers(quote) if words else set())
    checks["sayilar_alintida"] = not (numbers_in_v2(a["cevap"]) - qn)
    cites = {int(x) for x in re.findall(r"\[(\d+)\]", split_cites(a["cevap"]))}
    checks["atif_gecerli"] = bool(cites) and cites <= set(c["sources"])
    return status_from(checks)


# ---------- sınıflandırma ----------

def _values(text: str) -> set[float]:
    vals = {float(s) for s in numbers_in_v2(text)}
    for m in re.finditer(r"(?<![\d.,])\d{1,3}(?:[., ]\d{3})+(?![\d])", text):     # binlik ayırıcı
        vals.add(float(re.sub(r"[., ]", "", m.group(0))))
    for m in re.finditer(r"(\d+)\s*/\s*(\d+)", text):                            # kesir
        if int(m.group(2)):
            vals.add(int(m.group(1)) / int(m.group(2)))
    return vals


def _close(a: float, b: float, tol: float) -> bool:
    return abs(a - b) <= tol * max(abs(a), abs(b), 1e-9)


def classify(n: str, answer_text: str, quote: str, source: str, question: str) -> tuple[str, str]:
    from pilot import verify as V
    cites = " ".join(MULTI_CITE_RE.findall(answer_text))
    if n not in numbers_in_v2(answer_text) and canon_v2(n) not in numbers_in_v2(answer_text):
        if n in {x for x in re.findall(r"\d+", cites)}:
            return "atif", f"[{cites.split('  ')[0][:20]}]"
        return "sira", "liste numarası"
    v = float(canon_v2(n))
    if canon_v2(n) in numbers_in_v2(quote) or any(_close(x, v, 1e-9) for x in _values(quote)):
        return "bicim", "alıntıda değer olarak var"
    if canon_v2(n) in word_numbers(quote):
        return "yazi", "alıntıda yazıyla"
    if canon_v2(n) in numbers_in_v2(question):
        return "soruda", ""
    if canon_v2(n) in numbers_in_v2(source) or n in V.numbers_in(source):
        return "kaynakta", ""
    for name, f in FACTORS.items() if not (v.is_integer() and v <= 20) else ():   # küçük tam sayı: rastlantı
        for x in _values(quote):
            if x and (_close(x * f, v, 0.02) or _close(x / f, v, 0.02)):
                return "birim", f"{x:g} ({name})"
    return "yok", ""


def number_cases(key: str, tag: str) -> list[dict[str, Any]]:
    from pilot.verify import numbers_in
    cases = []
    for qid, c in replay(key, tag).items():
        checks = c["row"]["kontroller"] if c["kesik_kayit"] else c["res"].verification.checks
        if checks.get("sayilar_alintida") is not False:
            continue
        a = c["answer"]
        quote = " ".join(x.get("metin", "") for x in a.get("alintilar") or [])
        text = f"{a.get('cevap', '')} {a.get('sesli_metin', '')}"
        if c["kesik_kayit"]:
            m = next((STRAY_RE.search(p) for p in c["row"]["sorunlar"] if STRAY_RE.search(p)), None)
            stray = json.loads(f"[{m.group(1)}]".replace("'", '"')) if m else \
                sorted(numbers_in(a.get("cevap", "")) - numbers_in(quote))
        else:
            stray = sorted((numbers_in(a.get("cevap", "")) | numbers_in(a.get("sesli_metin", ""))) - numbers_in(quote))
        nums = [(n, *classify(n, text, quote, " ".join(c["sources"].values()), c["q"]["q"])) for n in stray]
        cases.append({"qid": qid, "onayli": c["q"].get("dogrulandi") is not False, "nums": nums,
                      "cevap": a.get("cevap", ""), "alinti": quote, "durum": c["row"]["durum"],
                      "deger_dogru": c["row"].get("deger_dogru"), "kesik_kayit": c["kesik_kayit"]})
    return cases


def rescore(key: str, tag: str) -> dict[str, tuple[str, str, str, bool, list[str]]]:
    """{qid: (önce, öneri A, öneri A + yazıyla sayılar, kesik_kayit, öneri A'da yanlış kalan kontroller)}."""
    from functools import partial
    st = lambda c, w: rescore_cut(c, w) if c["kesik_kayit"] else c["res"].verification.status
    a = replay(key, tag, patch=proposed_verify)
    b = replay(key, tag, patch=partial(proposed_verify, words=True))
    bad = lambda c: [] if c["kesik_kayit"] else [k for k, v in c["res"].verification.checks.items() if v is False]
    return {q: (c["row"]["durum"], st(c, False), st(b[q], True), c["kesik_kayit"], bad(c)) for q, c in a.items()}


# ---------- rapor ----------

def report(tag: str) -> tuple[str, dict[str, Any]]:
    keys = [k for k in MODELS if (RAW_DIR / f"{tag}_{k}.json").exists()]
    qs = {q["qid"]: q for q in questions()}
    approved = lambda q: qs[q].get("dogrulandi") is not False
    cases = {k: number_cases(k, tag) for k in keys}
    scores = {k: rescore(k, tag) for k in keys}
    rows = {k: json.loads((RAW_DIR / f"{tag}_{k}.json").read_text(encoding="utf-8"))["rows"] for k in keys}
    L = [f"# Adım 2 ilk tur: kayıtlardan analiz ({date.today().isoformat()})", "",
         "Yeni model çağrısı yok: kayıtlı ham çıktılar aynı arama önbelleğiyle `pipeline.soru_cevapla`'dan yeniden "
         f"geçirildi (`python -m bench.adim2_analiz`, tur `{tag}`). Kapsam: cevaplı sorularda üretilen cevaplar "
         "(\"bulunamadı\" beklenen sorular hariç), raporun rozet nedenleri tablosuyla aynı.", "",
         "> Kayıt sınırı: Bu turun ham çıktısı 1500 karakterde kesik kaydedilmiş (araç sonra düzeltildi; 16:30 ve 23:00 "
         "koşuları tam kaydeder). Kesik kayıtlarda cevap kayıttaki ilk 600 karakterden, alıntılar kesik metinden "
         "alınır; bunların yeni rozeti yaklaşıktır ve ayrı sayılır.", ""]

    L += ["## 1. \"Alıntıda olmayan sayı\" sınıfları", "",
          "Bir cevapta birden çok sayı olabilir: önce sayı başına, sonra cevap başına (cevabın en ağır sınıfı; ağırlık "
          "sırası tablodaki sütunların tersi: kaynakta da yok en ağır).", "",
          "| Model | cevap | sayı | " + " | ".join(LABEL.values()) + " |", "|---|---|---|" + "---|" * len(LABEL)]
    sev = list(LABEL)
    for k in keys:
        per = Counter(cl for c in cases[k] for _n, cl, _w in c["nums"])
        L.append(f"| {k} | {len(cases[k])} | {sum(per.values())} | " + " | ".join(str(per[x]) for x in LABEL) + " |")
    L += ["", "Cevap başına (cevabın en ağır sınıfı):", "", "| Model | " + " | ".join(LABEL.values()) + " |",
          "|---|" + "---|" * len(LABEL)]
    for k in keys:
        worst = Counter(max((cl for _n, cl, _w in c["nums"]), key=sev.index) for c in cases[k] if c["nums"])
        L.append(f"| {k} | " + " | ".join(str(worst[x]) for x in LABEL) + " |")

    L += ["", "## 2. Önerilen genel düzeltme: önce/sonra (verify.py'ye UYGULANMADI)", "",
          "Öneri (belgeye özel kural yok):",
          "1. Çoklu atıf tanınsın: `[1, 2]`, `[2,3,5]`, `[1; 4]`, `[1-3]` tek tek atıf sayılır (atıf kontrolü ve sayı "
          "ayıklama). Bugün yalnız `[1]` tanınıyor; çoklu atıfın içindeki sayılar \"alıntıda olmayan sayı\" oluyor, "
          "yalnız çoklu atıf kullanan cevap da \"geçerli [n] atfı yok\" alıyor.",
          "2. Liste numarası daha geniş tanınsın: atıflar liste işaretinden önce ayıklanır (`... kullanılmalıdır. "
          "[1, 5] 2. Uygun ...`), `<br>` satır sonu sayılır, Markdown kalın madde başı da tanınır (`1. **Long**`).",
          "3. Sayılar değer olarak karşılaştırılsın: ondalık virgül/nokta (bugün de var), sondaki sıfır (`2.00` = `2`), "
          "baştaki sıfır (`.5` = `0.5`). Binlik ayırıcı eklenmedi: `1.000` Türkçede bin, İngilizcede bir; genel kural "
          "belirsiz, bu sette vaka yok.",
          "4. (Ayrı seçenek, B) Alıntıda yazıyla geçen 1–12 (EN/ES/FR/TR: `six months`, `two workers`) alıntı sayısı "
          "kabul edilsin. Yalnız alıntı tarafında; cevaptaki \"bir\" sayı sayılmaz.", "",
          "Birim dönüşümü, kesirden ondalığa çeviri ve \"kaynakta var, alıntıda yok\" kabul EDİLMEDİ: alıntıda "
          "olmayan değer kullanıcıya doğrulanmış gibi gösterilmemeli (sınıflandırmada ayrı gösteriliyor).", "",
          "| Model | Set | cevap | önce ✓ / ⚠ / ✖ | A: 1–3 | ✖ → ✓/⚠ | ⚠ → ✓ | kötüleşen | B: 1–4 | kesik kayıt (yaklaşık) |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    trip = lambda c: f"{c['verified']} / {c['partial']} / {c['failed']}"
    for k in keys:
        for label, sel in (("onaylı", True), ("onaysız", False)):
            S = {q: v for q, v in scores[k].items() if approved(q) == sel}
            c0, c1, c2 = (Counter(v[i] for v in S.values()) for i in range(3))
            up = sum(v[0] == "failed" and v[1] != "failed" for v in S.values())
            up2 = sum(v[0] == "partial" and v[1] == "verified" for v in S.values())
            rank = {"verified": 2, "partial": 1, "failed": 0}
            worse = sum(rank.get(v[1], 0) < rank.get(v[0], 0) or rank.get(v[2], 0) < rank.get(v[0], 0)
                        for v in S.values())
            L.append(f"| {k} | {label} | {len(S)} | {trip(c0)} | {trip(c1)} | {up} | {up2} | {worse} | {trip(c2)} | "
                     f"{sum(v[3] for v in S.values())} |")

    L += ["", "Öneri A'dan sonra kalan ✖ nedenleri (bir cevapta birden çok olabilir; kesik kayıtlar hariç):", "",
          "| Model | ✖ | alıntıda olmayan sayı | alıntı birebir değil | alıntı yok | tolerans düştü | tekrar | yabancı alfabe |",
          "|---|---|---|---|---|---|---|---|"]
    for k in keys:
        F = [v[4] for v in scores[k].values() if v[1] == "failed" and not v[3]]
        n = lambda c: sum(c in f for f in F)
        L.append(f"| {k} | {len(F)} | {n('sayilar_alintida')} | {n('alinti_birebir')} | {n('alinti_var')} | "
                 f"{n('tolerans_tam')} | {n('tekrar_yok')} | {n('alfabe_dogru')} |")

    L += ["", "## 3. Örnekler (sınıf başına, modeller karışık)", ""]
    shown = Counter()
    for k in keys:
        for c in cases[k]:
            for n, cl, why in c["nums"]:
                if shown[cl] >= 3 or c["kesik_kayit"]:
                    continue
                shown[cl] += 1
                L += [f"- **{LABEL[cl]}** · {k} `{c['qid']}` · sayı `{n}`{' · ' + why if why else ''}",
                      f"  - cevap: {c['cevap'][:260].strip()}", f"  - alıntı: {c['alinti'][:200].strip()}"]
                break

    L += ["", "## 4. Cevap uzunluğu (çıktı tokeni) ve ✖", "",
          "| Model | cevap | token p50 | p95 | 700 sınırında kesilen | ✖ olanlarda p50 | ✓/⚠ olanlarda p50 | "
          "✖ oranı: < 200 tk | 200–399 | ≥ 400 | ✖ oranı (öneri A ile): < 200 | 200–399 | ≥ 400 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    pct_ = lambda a, b: f"{a}/{b} ({a / b:.0%})" if b else "–"
    for k in keys:
        R = {q: r for q, r in rows[k].items() if r.get("cikis") == "cevap" and q in scores[k]}
        tk = {q: r["cikis_token"] for q, r in R.items() if r.get("cikis_token")}
        cut = sum(r.get("finish") == "length" or (r.get("cikis_token") or 0) >= 700 for r in R.values())
        fail = [tk[q] for q in tk if R[q]["durum"] == "failed"]
        okk = [tk[q] for q in tk if R[q]["durum"] != "failed"]
        b = lambda lo, hi, i: pct_(sum(scores[k][q][i] == "failed" for q in tk if lo <= tk[q] < hi),
                                   sum(lo <= tk[q] < hi for q in tk))
        pc = lambda xs, p: f"{percentile(xs, p):.0f}" if xs else "–"
        L.append(f"| {k} | {len(R)} | {pc(list(tk.values()), 0.5)} | {pc(list(tk.values()), 0.95)} | "
                 f"{cut} | {pc(fail, 0.5)} | {pc(okk, 0.5)} | "
                 f"{b(0, 200, 0)} | {b(200, 400, 0)} | {b(400, 10**6, 0)} | "
                 f"{b(0, 200, 1)} | {b(200, 400, 1)} | {b(400, 10**6, 1)} |")
    L.append("")
    return "\n".join(L), {"vakalar": cases, "rozetler": scores}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", default="ana")
    a = ap.parse_args()
    md, data = report(a.tag)
    base = OUT_DIR / f"adim2_analiz_{date.today().isoformat()}"
    base.with_suffix(".md").write_text(md, encoding="utf-8")
    base.with_suffix(".json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()
