"""Niteleyici uyuşmazlığı taraması (karar 2026-11-06, devir d/1; model çağrısı yok).

Hata türü "niteleyici uyuşmazlığı": alıntı kaynakta birebir, sayı alıntıda, cevap doğrulanmış görünüyor; ama soru başka
bir şeyi soruyor. Sorudaki niteleyici (dijital, -5, Premier, Type II, Class 2, model kodu…) cevabın dayandığı kaynak
parçalarında geçmiyor. İlk örnek: B012 (dijital ayak kaldırıcı → mekanik kaldırma kolu, Gemma 4 DeepInfra, c150b).

Genel kurallar, belgeye özel değil:
  - niteleyici kalıpları: sabit iki dilli küçük liste (dijital/digital, elektronik/electronic, otomatik/automatic,
    manuel/manual, pnömatik/pneumatic, Premier, Type/Tip <romen|sayı>, Class/Sınıf <sayı>, -<sayı> şartnamesi)
  - model kodu (S-7300A, MO-6814S …): kaynak belge kimliğinde ya da parça metninde geçmeli
Tarama işaretler; karar elle okumayla verilir (aday listesi). Eşleşme: cevabın atıf verdiği parçalar (C: alıntıların
kaynak_no'ları; bugünkü şema: [n] atıfları), parça metni + embed_text (başlık bağlamı).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "eval" / "bench" / "adim2" / "ham"
CACHE = ROOT / "data" / "bench_cache" / "adim2_arama.json"

QUALIFIERS = [   # (ad, sorudaki kalıp, kaynakta aranan kalıp)
    ("dijital", r"\bdijital|\bdigital", r"digital|dijital"),
    ("elektronik", r"\belektronik|\belectronic", r"electronic|elektronik"),
    ("otomatik", r"\botomatik|\bautomatic", r"automatic|auto\b|otomatik"),
    ("manuel", r"\bmanuel|\bmanual\b", r"manual|manuel|by hand"),
    ("pnömatik", r"\bpnömatik|\bpneumatic", r"pneumatic|air\b|pnömatik"),
    ("Premier", r"\bpremier\b", r"premier"),
    ("Type/Tip", r"\b(?:type|tip|tipi)\s+(i{1,3}|iv|v|\d+)\b", None),
    ("Class/Sınıf", r"\b(?:class|sınıf)\s+(\d+)\b", None),
    ("-N şartnamesi", r"(?<![\w.])-(\d)\b", None),
]
CODE = re.compile(r"\b([A-Z]{1,3})-?(\d{3,5})([A-Z]{0,2})\b")


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def qualifiers(q: str) -> list[tuple[str, str]]:
    """(ad, kaynakta aranacak düzenli ifade) listesi."""
    out = []
    for name, qpat, spat in QUALIFIERS:
        m = re.search(qpat, q, re.I)
        if not m:
            continue
        if spat is None:
            v = m.group(1)
            if name == "Type/Tip":
                spat = rf"\b(?:types?|tip|tipi)\s*{v}\b"   # çoğul da: "Types II and III"
            elif name == "Class/Sınıf":
                spat = rf"\b(?:class|sınıf)\s*{v}\b"
            else:
                spat = rf"(?<![\w.])-(?:\[\]|\s)*{v}\b"   # kaynakta "-[][]3" (model kodunda boş kutular)
            name = f"{name} {v}"
        out.append((name, spat))
    for m in CODE.finditer(q):
        out.append((f"kod {m.group(0)}", "KOD:" + _norm(m.group(0))))
    return out


def cited_chunks(row: dict, sema: str, results: list[dict]) -> list[dict]:
    nos: set[int] = set()
    if sema.startswith("c"):
        try:
            a = json.loads(row.get("ham") or "{}")
        except json.JSONDecodeError:
            return []
        for it in a.get("cevap") or []:
            for qt in it.get("alintilar") or ([it["alinti"]] if isinstance(it.get("alinti"), dict) else []):
                if isinstance(qt.get("kaynak_no"), int):
                    nos.add(qt["kaynak_no"])
    else:
        for g in re.findall(r"\[([\d,\s]+)\]", row.get("cevap") or ""):
            nos.update(int(x) for x in re.findall(r"\d+", g))
    return [results[n - 1]["chunk"] for n in sorted(nos) if 0 < n <= len(results)]


def _page_chunks() -> dict[tuple[str, int], list[dict]]:
    """(doküman, sayfa) → parçalar: kaydında parça metni olmayan koşular için (hat ölçümü, duman testi)."""
    from pilot.chunk import read_chunks
    out: dict[tuple[str, int], list[dict]] = {}
    for c in read_chunks():
        for p in c.get("pages") or [c.get("page")]:
            out.setdefault((c["doc_id"], p), []).append(c)
    return out


def _cited_page_chunks(row: dict, pages: dict) -> list[dict]:
    """Atıf yapılan kaynak numaralarının (C: alıntıların kaynak_no'ları) kayıttaki doküman/sayfalarındaki parçalar
    (sayfa düzeyinde yaklaşık: aynı sayfadaki öbür parçalar da dahil, niteleyici bulunma olasılığı artar)."""
    try:
        a = json.loads(row.get("ham") or "{}")
    except json.JSONDecodeError:
        return []
    nos = {qt.get("kaynak_no") for it in a.get("cevap") or []
           for qt in it.get("alintilar") or ([it["alinti"]] if isinstance(it.get("alinti"), dict) else [])}
    src = row.get("kaynaklar") or []
    out = []
    for n in sorted(x for x in nos if isinstance(x, int) and 0 < x <= len(src)):
        doc, pgs = src[n - 1]
        for p in pgs:
            out += pages.get((doc, p), [])
    return out


def scan(files: list[str], raw_dir: Path | None = None) -> list[dict]:
    from bench.common import load_questions
    raw = raw_dir or RAW
    pages: dict | None = None
    cache = json.loads(CACHE.read_text(encoding="utf-8"))
    by_q: dict[str, list[list]] = {}
    for k, v in cache.items():
        by_q.setdefault(json.loads(k)[0], []).append(v if isinstance(v, list) else v.get("results", []))
    sets = ["questions", "questions_ek", "sekil_sorular", "aday_sorular", "aday_sorular_ek", "gorulmemis_juki"]
    Q = {q["qid"]: q for q in load_questions(sets, include_unapproved=True)}
    hits = []
    for f in files:
        d = json.loads((raw / f).read_text(encoding="utf-8"))
        sema = d.get("sema", "bugun")
        for qid, row in d["rows"].items():
            if row.get("cikis") != "cevap" or row.get("durum") not in ("verified", "partial") or qid not in Q:
                continue
            q = Q[qid]["q"]
            quals = qualifiers(q)
            if not quals:
                continue
            docs = {doc for doc, _ in row.get("kaynaklar") or []}
            cands = [r for k, rs in by_q.items() if k.startswith(q) for r in rs
                     if {x["chunk"]["chunk_id"].rsplit("-", 1)[0] for x in r} == docs or not docs]
            own_search = bool(d.get("hat") or row.get("hat"))     # kendi aramasını yapan koşu: önbellek eşleşmez
            chunks = cited_chunks(row, sema, cands[0]) if cands and not own_search else []
            if not chunks and sema.startswith("c"):
                pages = pages if pages is not None else _page_chunks()
                chunks = _cited_page_chunks(row, pages)
            if not chunks:
                hits.append({"dosya": f, "soru": qid, "q": q, "eksik": ["(atıf parçası çözülemedi)"]})
                continue
            text = " ".join((c.get("embed_text") or "") + " " + c.get("text", "") for c in chunks)
            ids = " ".join(_norm(c["chunk_id"]) for c in chunks)
            missing = []
            for name, pat in quals:
                if pat.startswith("KOD:"):
                    if pat[4:] not in ids and pat[4:] not in _norm(text):
                        missing.append(name)
                elif not re.search(pat, text, re.I):
                    missing.append(name)
            if missing:
                hits.append({"dosya": f, "soru": qid, "q": q, "eksik": missing, "durum": row.get("durum"),
                             "deger_dogru": row.get("deger_dogru"), "cevap": (row.get("cevap") or "")[:200],
                             "parcalar": [c["chunk_id"] for c in chunks]})
    return hits


def report_section(files: list[str]) -> list[str]:
    """Rapora otomatik bölüm (plan §23 adım 1): işaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış."""
    hits = scan(files)
    L = ["## Niteleyici uyuşmazlığı taraması (otomatik; plan §23)", "",
         "Soruda niteleyici (dijital, -5, Premier, Type II, model kodu …) var, cevabın dayandığı parçalarda yok. "
         "İşaretlenen her cevap elle okunur; gerçekse doğrulanmış görünen yanlış sayılır. Tarayıcı sabit iki dilli "
         "listeye bakar; ürün adı düzeyindeki anlam uyuşmazlıklarını yakalamaz.", ""]
    if not hits:
        return L + ["İşaretlenen cevap yok.", ""]
    L += ["| Koşu | Soru | Eksik niteleyici | Durum | Soru metni |", "|---|---|---|---|---|"]
    for h in hits:
        L.append(f"| {h['dosya']} | {h['soru']} | {', '.join(h['eksik'])} | {h.get('durum', '–')} | {h['q'][:80]} |")
    return L + [""]


if __name__ == "__main__":
    files = sys.argv[1:] or ["nihai_bugun_gemma4.json", "nihai_c150b_gemma4.json", "nihai_c150b_gemma4_venice.json",
                             "nihai_ek_gemma4.json", "nihai_ek_gemma4_venice.json"]
    for h in scan(files):
        print(json.dumps(h, ensure_ascii=False))
