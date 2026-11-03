"""Benchmark'ların ortak parçaları: soru setleri, sorgu hazırlığı, doğruluk ölçüleri, süre istatistiği, sonuç dosyası.

Bu modül model ve ağ gerektirmez (birim testler: tests/test_bench.py). Model çalıştıran kısımlar measure.py'de.
"""
import json
import math
import os
import platform
import re
import subprocess
import time
from collections.abc import Iterable, Sequence
from datetime import datetime
from pathlib import Path
from typing import Any

PILOT_DIR = Path(__file__).resolve().parent.parent
EVAL_DIR = PILOT_DIR / "eval"
OUT_DIR = EVAL_DIR / "bench"

# Parametreler bilinen dokümanlarda optimize edilir; JUKI yalnız son raporda doğrulama setidir (R18, §8 #10–11).
KNOWN_SETS = ("questions", "questions_ek", "sekil_sorular")
HOLDOUT_SETS = ("gorulmemis_juki",)

_SECRET = re.compile(r"KEY|TOKEN|SECRET|PASSWORD", re.I)


# ---------- soru setleri ----------

def load_questions(sets: Iterable[str], eval_dir: Path | None = None) -> list[dict[str, Any]]:
    """Onaysız sorular ('dogrulandi': false, ör. eval/aday_sorular.json taslağı) ölçüme girmez."""
    out = []
    for name in sets:
        for it in json.loads(((eval_dir or EVAL_DIR) / f"{name}.json").read_text(encoding="utf-8")):
            if it.get("dogrulandi") is False:
                continue
            out.append({**it, "set": name, "qid": f"{name}:{it['id']}"})
    return out


def prepare(question: str, strip_source: bool = True) -> dict[str, Any]:
    """pipeline.soru_cevapla()'nın aramadan önceki adımlarının aynısı: söylenmiş kodlar, varlıklar, kapsam, bağlam
    terimlerinin çıkarılması, terim sözlüğü. Arama yapılmayacaksa (netleştirme, yabancı marka) 'skip' nedenini taşır.
    pipeline.py değişirse burası da güncellenmeli (tests/test_bench.py yaygın durumları kontrol eder)."""
    from pilot.query import (MUST_MATCH, analyze_query, asks_nothing_specific, context_entities, source_aliases,
                             spoken_codes, strip_source_phrases, strip_terms)
    from pilot.registry import BY_ID
    from pilot.terms import expand_query

    question = spoken_codes(question)
    ctx = analyze_query(question)
    if ctx.foreign_brands:
        return {"skip": "yabanci_marka"}
    mixed = len({BY_ID[d].doc_type for d in ctx.doc_ids if BY_ID[d].doc_type in MUST_MATCH}) >= 2
    if ctx.variants or mixed:
        return {"skip": "netlestirme"}
    scope = list(ctx.doc_ids) or None
    context = context_entities(ctx, scope) if scope else []
    asked = strip_terms(question, context) if context else question
    if scope and asks_nothing_specific(question, ctx):
        return {"skip": "konu_belirsiz"}
    if strip_source:            # strip_source=False: Aşama 2.5 öncesi ölçüm (kaynak ifadesi aramada kalır)
        asked = strip_source_phrases(asked, source_aliases(ctx, scope))
    search_q, _ = expand_query(asked)
    return {"skip": None, "search_q": search_q, "doc_ids": scope}


# ---------- doğruluk ----------

def is_match(chunk: dict[str, Any], item: dict[str, Any]) -> bool:
    """Parça beklenen kaynaklardan mı? 'kabul' varsa (doküman + sayfa çiftleri: çok dilli/çok sayfalı/çok dokümanlı
    cevap) her çift ayrı değerlendirilir; yoksa expect_docs + expect_pages (sayfa yoksa doküman yeter)."""
    if item.get("kabul"):
        return any(chunk["doc_id"] == k["doc"] and (not k.get("pages") or bool(set(chunk["pages"]) & set(k["pages"])))
                   for k in item["kabul"])
    if chunk["doc_id"] not in item.get("expect_docs", []):
        return False
    pages = item.get("expect_pages")
    return not pages or bool(set(chunk["pages"]) & set(pages))


def first_rank(chunks: Sequence[dict[str, Any]], item: dict[str, Any]) -> int | None:
    """Beklenen ilk parçanın sırası (1'den başlar), yoksa None."""
    return next((i + 1 for i, c in enumerate(chunks) if is_match(c, item)), None)


def accuracy(ranks: Sequence[int | None]) -> dict[str, float | int]:
    n = len(ranks)
    if not n:
        return {"n": 0, "hit@1": math.nan, "hit@5": math.nan, "hit@20": math.nan, "mrr": math.nan}
    return {"n": n,
            "hit@1": sum(1 for r in ranks if r == 1) / n,
            "hit@5": sum(1 for r in ranks if r is not None and r <= 5) / n,
            "hit@20": sum(1 for r in ranks if r is not None and r <= 20) / n,
            "mrr": sum(1 / r for r in ranks if r is not None) / n}


def overlap_at_k(approx: Sequence[Any], exact: Sequence[Any], k: int) -> float:
    """ANN recall@k: yaklaşık aramanın ilk k sonucundan kaçı tam aramanın ilk k sonucunda."""
    ref = list(exact)[:k]
    if not ref:
        return 1.0
    return len(set(list(approx)[:k]) & set(ref)) / len(ref)


# ---------- süre ----------

def percentile(xs: Sequence[float], q: float) -> float:
    """Doğrusal aralıklı yüzdelik (numpy 'linear' ile aynı)."""
    if not xs:
        return math.nan
    s = sorted(xs)
    pos = (len(s) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    return s[lo] + (s[hi] - s[lo]) * (pos - lo)


def stats(xs: Sequence[float]) -> dict[str, float | int]:
    return {"n": len(xs), "mean": sum(xs) / len(xs) if xs else math.nan,
            "p50": percentile(xs, 0.5), "p95": percentile(xs, 0.95)}


class StageTimer:
    """retrieve.timing_hook'a bağlanır; her çağrının aşama sürelerini toplar. Aşama adları serbest
    (embed, qdrant, rerank; sonra llm, stt, tts eklenebilir)."""

    def __init__(self) -> None:
        self.samples: dict[str, list[float]] = {}
        self._current: dict[str, float] = {}

    def __call__(self, stage: str, seconds: float) -> None:
        self._current[stage] = self._current.get(stage, 0.0) + seconds

    def start(self) -> None:
        self._current = {}
        self._t0 = time.perf_counter()

    def stop(self) -> dict[str, float]:
        cur = {**self._current, "total": time.perf_counter() - self._t0}
        for k, v in cur.items():
            self.samples.setdefault(k, []).append(v)
        return cur

    def record(self, stages: dict[str, float]) -> None:
        """Dışarıda ölçülmüş aşama süreleri (ör. bulut çağrısı + ağ) tek örnek olarak."""
        for k, v in stages.items():
            self.samples.setdefault(k, []).append(v)

    def summary(self) -> dict[str, dict[str, float | int]]:
        return {k: stats(v) for k, v in self.samples.items()}


# ---------- sonuç dosyası ----------

def _git_commit() -> str:
    if os.environ.get("BENCH_GIT_COMMIT"):          # şirket içi sunucu: git yok, paketin commit'i (bench/onprem)
        return os.environ["BENCH_GIT_COMMIT"]
    try:
        sha = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=PILOT_DIR, capture_output=True,
                             text=True, timeout=10).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--untracked-files=no"], cwd=PILOT_DIR,
                               capture_output=True, text=True, timeout=10).stdout.strip()
        return sha + ("+degisiklik" if dirty else "")
    except (OSError, subprocess.SubprocessError):
        return "?"


def hardware() -> dict[str, Any]:
    info: dict[str, Any] = {"platform": platform.platform(), "python": platform.python_version(),
                            "cpu": platform.processor(), "logical_cpus": os.cpu_count()}
    try:
        import psutil
        info["ram_gb"] = round(psutil.virtual_memory().total / 2**30, 1)
        info["physical_cpus"] = psutil.cpu_count(logical=False)
    except ImportError:
        pass
    return info


def pilot_env() -> dict[str, str]:
    """Sonuca yazılan PILOT_* ayarları. Anahtar/parola içerenlerin değeri yazılmaz."""
    return {k: ("<gizli>" if _SECRET.search(k) else v) for k, v in sorted(os.environ.items())
            if k.startswith("PILOT_") or k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS")}


# Donanım ve ağ etiketi: rapor üretimi temsil eden ölçümleri ayırır (hedef: arka uç sunucu + API'ler).
HW_LABEL = os.environ.get("BENCH_HW_LABEL", "geliştirme dizüstü (i5-1335U, GPU yok) — üretimi temsil etmez")
NETWORK_LABEL = os.environ.get("BENCH_NETWORK", "geliştirme makinesinin bağlantısı (ofis/ev)")


def meta(params: dict[str, Any]) -> dict[str, Any]:
    return {"date": datetime.now().isoformat(timespec="seconds"), "git_commit": _git_commit(),
            "hardware": hardware(), "hardware_label": HW_LABEL, "network_label": NETWORK_LABEL,
            "env": pilot_env(), "params": params}


def dir_size(path: Path) -> int:
    return sum(f.stat().st_size for f in Path(path).rglob("*") if f.is_file()) if Path(path).exists() else 0


# Sonuç klasörü, adın önekinden (eval/bench/README.md). Önekine uymayan genel araç çıktıları genel/'e.
STAGE_DIRS = (
    ("baseline", "b0-b1"), ("asama1", "b0-b1"),
    ("asama25", "b25"), ("asama2_", "b2"),
    ("asama3", "b3"),
    ("asama4", "b4"), ("rerank_duzeltme", "b4"), ("rerank_teshis2", "b4"),
    ("bulunamadi", "bulunamadi"), ("netlestirme", "bulunamadi"),
)


def stage_dir(stage: str) -> Path:
    for prefix, sub in STAGE_DIRS:
        if stage.startswith(prefix):
            return OUT_DIR / sub
    return OUT_DIR / "genel"


def write_result(stage: str, data: dict[str, Any], md: str, out_dir: Path | None = None) -> Path:
    """<aşama>_<tarih>.json ve .md, stage_dir(stage) altına. Aynı gün ikinci koşu: _2, _3 ..."""
    out_dir = out_dir or stage_dir(stage)
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{stage}_{datetime.now():%Y-%m-%d}"
    name, i = base, 1
    while (out_dir / f"{name}.json").exists():
        i += 1
        name = f"{base}_{i}"
    path = out_dir / f"{name}.json"
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1, default=float), encoding="utf-8")
    (out_dir / f"{name}.md").write_text(md, encoding="utf-8")
    return path


def fmt_s(x: float) -> str:
    if x != x:  # nan
        return "–"
    return f"{x * 1000:.0f} ms" if x < 1 else f"{x:.2f} sn"


def fmt_pct(x: float) -> str:
    return "–" if x != x else f"{x:.2f}".replace(".", ",")


def timing_table(summary: dict[str, dict[str, float | int]], order: Sequence[str]) -> list[str]:
    rows = ["| Aşama | n | ort. | p50 | p95 |", "|-------|---|------|-----|-----|"]
    for k in [o for o in order if o in summary] + [k for k in summary if k not in order]:
        s = summary[k]
        rows.append(f"| {k} | {s['n']} | {fmt_s(s['mean'])} | {fmt_s(s['p50'])} | {fmt_s(s['p95'])} |")
    return rows
