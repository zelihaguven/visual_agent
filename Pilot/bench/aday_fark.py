"""Aday soru taslağının iki sürümü arasındaki fark: değişen ve eklenen satırlar (onay için ayrı liste).

Kullanım (Pilot klasöründe):
    python -m bench.aday_fark --old af84cc9 [--new HEAD] [--out eval/aday_sorular_fark.md]

Değişmiş sayılan: soru metni, tür, kabul edilen doküman/sayfa ya da cevap değeri. Yalnız kanıt cümlesi, not ya da alan
adı değişen satırlar (ör. alinti → kanit) ayrıca sayılır ama tabloya girmez.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from bench.common import PILOT_DIR

PATH = "Pilot/eval/aday_sorular.json"


def load(rev: str) -> dict[str, dict[str, Any]]:
    if rev == "WORKTREE":
        text = (PILOT_DIR / "eval" / "aday_sorular.json").read_text(encoding="utf-8")
    else:
        text = subprocess.run(["git", "show", f"{rev}:{PATH}"], cwd=PILOT_DIR.parent, capture_output=True, check=True,
                              encoding="utf-8").stdout
    return {q["id"]: q for q in json.loads(text)}


def accepted(q: dict[str, Any]) -> list[tuple[str, tuple[int, ...]]]:
    if q.get("kabul"):
        return sorted((k["doc"], tuple(sorted(k.get("pages") or ()))) for k in q["kabul"])
    pages = tuple(sorted(q.get("expect_pages") or ()))
    return sorted((d, pages) for d in q.get("expect_docs") or ())


def norm(t: Any) -> str:
    return re.sub(r"\s+", " ", str(t or "")).strip().lower()


def answer(q: dict[str, Any], has_cevap: bool) -> Any:
    """İlk sürümde cevap alanı yoktu; o durumda beklenen değerler (expect_in_answer) karşılaştırılır."""
    return norm(q.get("cevap")) if has_cevap else sorted(norm(v) for v in q.get("expect_in_answer") or ())


def fmt_acc(acc: list[tuple[str, tuple[int, ...]]]) -> str:
    return "; ".join(f"{d} s.{','.join(map(str, p))}" if p else d for d, p in acc) or "–"


def diff(old: dict[str, dict], new: dict[str, dict]) -> tuple[list, list, list]:
    changed, minor = [], []
    for k, q in new.items():
        if k not in old:
            continue
        o = q_old = old[k]
        what = [name for name, a, b in (("soru", q["q"], o["q"]), ("tür", q["kind"], o["kind"]),
                                        ("kabul", accepted(q), accepted(q_old)),
                                        ("cevap", answer(q, "cevap" in o), answer(o, "cevap" in o)),
                                        ("bulunamadı", bool(q.get("expect_not_found")), bool(o.get("expect_not_found"))))
                if a != b]
        (changed if what else minor).append((q, o, what))
    added = [q for k, q in new.items() if k not in old]
    return changed, [m for m in minor if m[0] != m[1]], added


def cell(t: Any) -> str:
    return str(t or "").replace("|", "/").replace("\n", " ")


def to_md(old_rev: str, new_rev: str, changed: list, minor: list, added: list, old: dict, new: dict) -> str:
    out = [f"# Aday soru taslağı: değişen ve eklenen satırlar ({old_rev} → {new_rev})", "",
           f"{len(old)} → {len(new)} soru. Değişen (soru, tür, kabul ya da cevap): **{len(changed)}**. "
           f"Eklenen: **{len(added)}**. Yalnız kanıt/not/alan adı değişen: {len(minor)} (tabloda yok). "
           f"Kaldırılan: {len([k for k in old if k not in new])}. Hepsi onaysız (`dogrulandi: false`).", "",
           "## Değişen satırlar", "", "| # | Ne değişti | Soru | Kabul (yeni) | Cevap (yeni) | Önce |", "|---|---|---|---|---|---|"]
    for q, o, what in changed:
        before = []
        if "soru" in what:
            before.append(f"soru: {o['q']}")
        if "tür" in what:
            before.append(f"tür: {o['kind']}")
        if "kabul" in what:
            before.append(f"kabul: {fmt_acc(accepted(o))}")
        if "cevap" in what:
            before.append(f"cevap: {o['cevap']}" if "cevap" in o
                          else "beklenen değerler: " + ", ".join(o.get("expect_in_answer") or ["–"]))
        if "bulunamadı" in what:
            before.append(f"bulunamadı: {bool(o.get('expect_not_found'))}")
        out.append(f"| {q['id']} | {', '.join(what)} | {cell(q['q'])} | {cell(fmt_acc(accepted(q)))} | "
                   f"{cell(q.get('cevap'))} | {cell(' · '.join(before))} |")
    out += ["", "## Eklenen satırlar", "", "| # | Tür | Soru | Kabul | Cevap / beklenen |", "|---|---|---|---|---|"]
    for q in added:
        exp = q.get("cevap") or ("bulunamadı" if q.get("expect_not_found") else "")
        if q.get("expect_clarify"):
            exp = "netleştirme: " + ", ".join(q.get("olasi_urunler") or [])
        out.append(f"| {q['id']} | {q['kind']} | {cell(q['q'])} | {cell(fmt_acc(accepted(q)))} | {cell(exp)} |")
    return "\n".join(out) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", default="WORKTREE")
    ap.add_argument("--out", default=str(PILOT_DIR / "eval" / "aday_sorular_fark.md"))
    a = ap.parse_args()
    old, new = load(a.old), load(a.new)
    changed, minor, added = diff(old, new)
    Path(a.out).write_text(to_md(a.old, "güncel" if a.new == "WORKTREE" else a.new, changed, minor, added, old, new),
                           encoding="utf-8")
    print(f"değişen {len(changed)}, eklenen {len(added)}, küçük {len(minor)} → {a.out}")


if __name__ == "__main__":
    main()
