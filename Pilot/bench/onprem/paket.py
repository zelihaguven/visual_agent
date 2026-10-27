"""Şirket içi sunucu paketi (3a süre, 3c yük): dizüstünde hazırlanır, sunucuda internet gerekmez.

Kullanım (Pilot klasöründe, yerel Qdrant sunucusu açık, kod commit'lenmiş):
    python -m bench.onprem.paket --out data/scale/paket --collections synth_1m scale_qwen3_8b scale_bge_m3
    python -m bench.onprem.paket --out data/scale/paket_deneme --collections synth_10k --tar   # küçük deneme paketi

Paket (klasör; --tar ile tek .tar dosyası):
    asama3_sunucu.sh          tek komut: sudo bash asama3_sunucu.sh
    BENIOKU.txt, COMMIT, requirements-onprem.txt
    python/                   CPython 3.12 (python-build-standalone, glibc ≥ 2.17, x86_64)
    bin/                      Qdrant v1.19.2 statik Linux ikilisi (musl), dizüstündeki sunucuyla aynı sürüm
    wheels/                   Python paketleri (manylinux, cp312), --no-index kurulum
    kod/Pilot/                git archive HEAD: pilot/, bench/, eval/*.json (commit'lenmemiş değişiklik pakete girmez)
    queries/                  hazır sorgu vektörleri (Qwen3-8B bulut embed'i bir kez ödendi; sunucuda ağ yok)
    snapshots/                koleksiyon snapshot'ları + manifest.json (sha256) + ayar dosyaları
İndirmeler data/scale/onprem_cache/ altında tutulur (ikinci kez inmez).
"""
import argparse
import json
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

from bench.common import PILOT_DIR
from bench.scale_corpus import SCALE_DIR, download

HERE = Path(__file__).resolve().parent
CACHE = SCALE_DIR / "onprem_cache"
QDRANT_URL = "https://github.com/qdrant/qdrant/releases/download/v1.19.2/qdrant-x86_64-unknown-linux-musl.tar.gz"
PYTHON_URL = ("https://github.com/astral-sh/python-build-standalone/releases/download/20261009/"
              "cpython-3.12.15%2B20261009-x86_64-unknown-linux-gnu-install_only.tar.gz")   # 2026-10-09 sürümü
PLATFORMS = ("manylinux2014_x86_64", "manylinux_2_17_x86_64", "manylinux_2_28_x86_64")


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=PILOT_DIR.parent, capture_output=True, text=True, check=True).stdout.strip()


def code(out: Path) -> str:
    """Commit'lenmiş kod (git archive HEAD); çalışma kopyasındaki değişiklik pakete girmez, uyarılır."""
    dirty = git("status", "--porcelain", "--untracked-files=no", "--", "Pilot/pilot", "Pilot/bench")
    if dirty:
        print("UYARI: commit'lenmemiş değişiklik var, pakete girmez:\n" + dirty)
    commit = git("rev-parse", "--short", "HEAD")
    tmp = CACHE / "kod.tar"
    CACHE.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "archive", "--format=tar", "-o", str(tmp), "HEAD", "Pilot/pilot", "Pilot/bench", "Pilot/eval"],
                   cwd=PILOT_DIR.parent, check=True)
    dest = out / "kod"
    if dest.exists():
        shutil.rmtree(dest)
    with tarfile.open(tmp) as t:
        t.extractall(dest, filter="data")
    (dest / "Pilot" / "data" / "scale" / "progress").mkdir(parents=True, exist_ok=True)
    (out / "COMMIT").write_text(commit, encoding="utf-8")
    return commit


def wheels(out: Path) -> None:
    dest = out / "wheels"
    dest.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-m", "pip", "download", "-q", "-r", str(HERE / "requirements-onprem.txt"), "-d", str(dest),
           "--only-binary=:all:", "--python-version", "3.12", "--implementation", "cp", "--abi", "cp312"]
    for p in PLATFORMS:
        cmd += ["--platform", p]
    subprocess.run(cmd, check=True)
    print(f"tekerlek: {len(list(dest.glob('*.whl')))}")


def binaries(out: Path) -> None:
    for url, sub in ((QDRANT_URL, "bin"), (PYTHON_URL, "python")):
        name = url.rsplit("/", 1)[-1].replace("%2B", "+")
        src = download(url, CACHE / name)
        (out / sub).mkdir(parents=True, exist_ok=True)
        shutil.copy(src, out / sub / name)


def queries(out: Path) -> None:
    dest = out / "queries"
    dest.mkdir(parents=True, exist_ok=True)
    for q in SCALE_DIR.glob("queries_*.json"):
        shutil.copy(q, dest / q.name)


def build(out: Path, collections: list[str], make_tar: bool) -> None:
    from bench.onprem.snapshot import create
    out.mkdir(parents=True, exist_ok=True)
    commit = code(out)
    for f in ("asama3_sunucu.sh", "BENIOKU.txt", "requirements-onprem.txt"):
        shutil.copy(HERE / f, out / f)
    binaries(out)
    wheels(out)
    queries(out)
    manifest = create(collections, out / "snapshots")
    total = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    summary = {"commit": commit, "collections": {c: {"points": m["points"], "gb": round(m["bytes"] / 2**30, 2)}
                                                 for c, m in manifest.items()}, "total_gb": round(total / 2**30, 2)}
    (out / "paket.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print(json.dumps(summary, indent=1))
    if make_tar:
        tar_path = out.with_suffix(".tar")
        with tarfile.open(tar_path, "w") as t:           # sıkıştırmasız: vektörler sıkışmaz, hızlı
            t.add(out, arcname=out.name)
        print(f"tek dosya: {tar_path} ({tar_path.stat().st_size / 2**30:.2f} GB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=SCALE_DIR / "paket")
    ap.add_argument("--collections", nargs="+", default=["synth_1m", "scale_qwen3_8b", "scale_bge_m3"])
    ap.add_argument("--tar", action="store_true")
    a = ap.parse_args()
    build(a.out, a.collections, a.tar)


if __name__ == "__main__":
    main()
