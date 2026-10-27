"""Koleksiyonları snapshot olarak taşıma: dizüstünde al, şirket içi sunucuda (internetsiz) geri yükle.

Kullanım (Pilot klasöründe):
    python -m bench.onprem.snapshot create --collections synth_1m scale_qwen3_8b scale_bge_m3 --out data/scale/paket/snapshots
    python -m bench.onprem.snapshot restore --dir <paket>/snapshots --snapshots-path <qdrant snapshots klasörü>

- create: Qdrant sunucusunda snapshot alınır (wait), parça parça indirilir, sunucudaki kopya silinir (disk). Her
  koleksiyonun ilerleme/ayar dosyası (data/scale/progress/<ad>.meta.json) yanına konur: sunucuda arama ayarları ve
  kademe kopyaları bundan okunur. manifest.json: boyut ve sha256 (taşımada bozulma kontrolü).
- restore: sha256 doğrulanır, dosya Qdrant'ın snapshots klasörüne taşınır ve oradan geri yüklenir
  (PUT /collections/<ad>/snapshots/recover, location=file://...; Qdrant yerel dosyayı yalnız kendi snapshots klasöründen
  kabul eder). Olmazsa curl ile yükleme (POST .../snapshots/upload) denenir. Qdrant sürümü iki tarafta aynı: v1.19.2.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

URL = os.environ.get("PILOT_QDRANT_URL", "http://127.0.0.1:6333")
CHUNK = 8 << 20


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return h.hexdigest()


def create(collections: list[str], out: Path) -> dict[str, Any]:
    import requests

    from bench.scale_index import paths
    out.mkdir(parents=True, exist_ok=True)
    (out / "meta").mkdir(exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
    for c in collections:
        dest = out / f"{c}.snapshot"
        if c in manifest and dest.exists() and dest.stat().st_size == manifest[c]["bytes"]:
            print(f"{c}: zaten var ({manifest[c]['bytes'] / 2**30:.2f} GB)")
            continue
        info = requests.get(f"{URL}/collections/{c}", timeout=60).json()["result"]
        t = time.time()
        r = requests.post(f"{URL}/collections/{c}/snapshots", params={"wait": "true"}, timeout=6 * 3600)
        r.raise_for_status()
        name = r.json()["result"]["name"]
        part = dest.with_suffix(".snapshot.part")
        with requests.get(f"{URL}/collections/{c}/snapshots/{name}", stream=True, timeout=600) as g:
            g.raise_for_status()
            with part.open("wb") as f:
                for block in g.iter_content(CHUNK):
                    f.write(block)
        part.replace(dest)
        requests.delete(f"{URL}/collections/{c}/snapshots/{name}", timeout=600)
        meta_src = paths(c)[1]
        if meta_src.exists():
            shutil.copy(meta_src, out / "meta" / meta_src.name)
        manifest[c] = {"file": dest.name, "bytes": dest.stat().st_size, "sha256": sha256(dest),
                       "points": info["points_count"], "seconds": round(time.time() - t, 1),
                       "meta": meta_src.name if meta_src.exists() else None}
        manifest_path.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(f"{c}: {manifest[c]['points']} nokta, {manifest[c]['bytes'] / 2**30:.2f} GB, {manifest[c]['seconds']} sn")
    return manifest


def restore(snap_dir: Path, snapshots_path: Path, progress_dir: Path, verify: bool) -> None:
    import requests
    manifest = json.loads((snap_dir / "manifest.json").read_text(encoding="utf-8"))
    progress_dir.mkdir(parents=True, exist_ok=True)
    for c, m in manifest.items():
        src = snap_dir / m["file"]
        have = requests.get(f"{URL}/collections/{c}/exists", timeout=60).json()["result"]["exists"]
        if have and requests.get(f"{URL}/collections/{c}", timeout=60).json()["result"]["points_count"] == m["points"]:
            print(f"{c}: zaten yüklü ({m['points']} nokta)")
        else:
            if verify:
                got = sha256(src)
                if got != m["sha256"]:
                    raise SystemExit(f"{c}: sha256 tutmuyor (taşımada bozulmuş): {got} ≠ {m['sha256']}")
            target_dir = snapshots_path / c
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / m["file"]
            if not target.exists():
                try:
                    os.link(src, target)                     # aynı diskte kopyasız
                except OSError:
                    shutil.copy(src, target)
            t = time.time()
            r = requests.put(f"{URL}/collections/{c}/snapshots/recover", params={"wait": "true"},
                             json={"location": target.resolve().as_uri(), "priority": "snapshot"}, timeout=6 * 3600)
            if r.status_code >= 400:
                print(f"{c}: dosyadan geri yükleme olmadı ({r.status_code} {r.text[:200]}); yükleme deneniyor")
                subprocess.run(["curl", "-sf", "-X", "POST", f"{URL}/collections/{c}/snapshots/upload?wait=true&priority=snapshot",
                                "-F", f"snapshot=@{src}"], check=True)
            n = requests.get(f"{URL}/collections/{c}", timeout=60).json()["result"]["points_count"]
            if n != m["points"]:
                raise SystemExit(f"{c}: geri yüklendi ama nokta sayısı {n} ≠ {m['points']}")
            print(f"{c}: {n} nokta, {time.time() - t:.0f} sn")
            target.unlink(missing_ok=True)
        if m.get("meta"):
            shutil.copy(snap_dir / "meta" / m["meta"], progress_dir / m["meta"])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("create")
    c.add_argument("--collections", nargs="+", required=True)
    c.add_argument("--out", type=Path, required=True)
    r = sub.add_parser("restore")
    r.add_argument("--dir", type=Path, required=True)
    r.add_argument("--snapshots-path", type=Path, required=True)
    r.add_argument("--progress-dir", type=Path, default=Path("data/scale/progress"))
    r.add_argument("--no-verify", action="store_true")
    a = ap.parse_args()
    if a.cmd == "create":
        create(a.collections, a.out)
    else:
        restore(a.dir, a.snapshots_path, a.progress_dir, not a.no_verify)


if __name__ == "__main__":
    main()
