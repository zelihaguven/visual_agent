"""Aşama 3b: kalabalık korpusu. Gerçek parçalar + açık veri setlerinden konuya yakın dikkat dağıtıcı parçalar.

Kullanım (Pilot klasöründe):
    python -m bench.scale_corpus build                               # 1M (tiers'ın sonuncusu), parquet indirir (~2 GB)
    python -m bench.scale_corpus build --target 300 --tiers 100,300 --real-sample 150 --out data/scale/corpus_kuru
                                                                     # kuru çalıştırma: rows API, indirme yok
    python -m bench.scale_corpus info --out data/scale/corpus        # manifest özeti

- Kaynaklar ve lisanslar bench/scale_sources.json'da. Dikkat dağıtıcılar kaynak paylarına göre (share) toplanır,
  gerçek parça boyuna yakın (chunk_chars) paketlenir; uzun belgeden en fazla max_chunks_per_doc parça alınır.
- Kademe (kademe alanı): dikkat dağıtıcılar sabit tohumla karıştırılır; ilk (10k − gerçek) tanesi 10k kademesine, sonraki
  (100k − 10k) tanesi 100k kademesine ... Kademeler iç içe: 100k koleksiyonu 10k'nın tamamını içerir. Gerçek parçalar
  kademe 0 (hepsinde). Çıktı kademe sırasında yazılır: indeksleme yarıda kalsa da küçük kademeler tamdır.
- Dikkat dağıtıcının markası gerçek parçaların marka dağılımından seçilir: marka filtreli aramada da kalabalık oluşur.
  doc_id "dd-<kaynak>-<sıra>", access ["all"], doc_type "dikkat".
- Kaldığı yerden: parquet dosyaları data/scale/raw/ altında tutulur (indirilmişse tekrar inmez). Korpus deterministiktir;
  manifest aynı ayarlarla varsa yeniden kurulmaz (--force ile kurulur).
"""
import argparse
import json
import random
import re
import time
from collections import Counter
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from bench.common import PILOT_DIR

SOURCES_PATH = Path(__file__).with_name("scale_sources.json")
SCALE_DIR = PILOT_DIR / "data" / "scale"
DS_API = "https://datasets-server.huggingface.co"
SHARD = 100_000
ROWS_PAGE = 100                     # rows API sayfa boyu (üst sınır)


def load_sources() -> dict[str, Any]:
    return json.loads(SOURCES_PATH.read_text(encoding="utf-8"))


# ---------- metin → parça ----------

_WS = re.compile(r"[ \t\r\f\v]+")
_SENT = re.compile(r"(?<=[.!?;:])\s+")


def split_text(text: str, target: int, max_chars: int) -> list[str]:
    """Paragraflar target uzunluğa kadar birleştirilir; max_chars'ı aşan paragraf cümle sınırından bölünür."""
    paras = [_WS.sub(" ", p).strip() for p in re.split(r"\n\s*\n|\n", text)]
    pieces: list[str] = []
    for p in paras:
        if not p:
            continue
        if len(p) <= max_chars:
            pieces.append(p)
            continue
        cur = ""
        for s in _SENT.split(p):
            if cur and len(cur) + len(s) + 1 > target:
                pieces.append(cur)
                cur = ""
            cur = f"{cur} {s}".strip()
            while len(cur) > max_chars:             # cümlesiz uzun blok
                pieces.append(cur[:max_chars])
                cur = cur[max_chars:]
        if cur:
            pieces.append(cur)
    out: list[str] = []
    cur = ""
    for p in pieces:
        if cur and len(cur) + len(p) + 1 > max_chars:
            out.append(cur)
            cur = ""
        cur = f"{cur}\n{p}".strip()
        if len(cur) >= target:
            out.append(cur)
            cur = ""
    if len(cur) >= 80:                               # artık kırıntı atılır
        out.append(cur)
    return out


def short_title(t: str | None, n: int = 90) -> str:
    t = _WS.sub(" ", (t or "").replace("\n", " ")).strip()
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def relevant(src: dict[str, Any], title: str, text: str) -> bool:
    kws = src.get("keywords")
    if not kws:
        return True
    head = f"{title}\n{text[:2000]}".lower()
    return any(k in head for k in kws)


# ---------- veri seti okuma ----------

def parquet_urls(src: dict[str, Any]) -> list[str]:
    import requests
    r = requests.get(f"{DS_API}/parquet", params={"dataset": src["dataset"]}, timeout=60)
    r.raise_for_status()
    files = [f for f in r.json()["parquet_files"] if f["config"] == src["config"] and f["split"] == src["split"]]
    return [f["url"] for f in sorted(files, key=lambda f: f["filename"])]


def download(url: str, dest: Path) -> Path:
    """Kaldığı yerden: tamamlanmış dosya varsa inmez; yarım kalan .part baştan iner."""
    import requests
    if dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with part.open("wb") as f:
            for block in r.iter_content(1 << 20):
                f.write(block)
    part.replace(dest)
    return dest


def iter_parquet(src: dict[str, Any]) -> Iterator[tuple[str, str]]:
    import pyarrow.parquet as pq
    cols = [src["text"]] + ([src["title"]] if src.get("title") else [])
    for url in parquet_urls(src):
        dest = SCALE_DIR / "raw" / src["dataset"].replace("/", "__") / src["config"] / url.rsplit("/", 1)[-1]
        print(f"  {src['key']}: {dest.name}", flush=True)
        for batch in pq.ParquetFile(download(url, dest)).iter_batches(batch_size=512, columns=cols):
            d = batch.to_pydict()
            titles = d.get(src.get("title") or "", [None] * len(d[src["text"]]))
            yield from zip(titles, d[src["text"]])


def iter_rows(src: dict[str, Any], max_rows: int) -> Iterator[tuple[str, str]]:
    """Küçük örnek: datasets-server rows API (indirme yok)."""
    import requests
    for offset in range(0, max_rows, ROWS_PAGE):
        r = requests.get(f"{DS_API}/rows", params={"dataset": src["dataset"], "config": src["config"],
                                                   "split": src["split"], "offset": offset, "length": ROWS_PAGE},
                         timeout=60)
        r.raise_for_status()
        rows = r.json().get("rows", [])
        for row in rows:
            yield row["row"].get(src.get("title") or "", None), row["row"][src["text"]]
        if len(rows) < ROWS_PAGE:
            return


def collect(src: dict[str, Any], quota: int, cfg: dict[str, Any], sample: bool) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    rows = iter_rows(src, max_rows=20 * ROWS_PAGE) if sample else iter_parquet(src)
    n_doc = 0
    for title, text in rows:
        if len(out) >= quota:
            break
        if not text or not relevant(src, title or "", text):
            continue
        head = short_title(title)
        pieces = split_text(text, cfg["chunk_chars"], cfg["max_chunk_chars"])[:src.get("max_chunks_per_doc", 10 ** 9)]
        for i, p in enumerate(pieces[:quota - len(out)]):
            out.append({"source": src["key"], "doc_n": n_doc, "part": i, "title": head, "text": p})
        n_doc += 1
    print(f"  {src['key']}: {len(out)}/{quota} parça, {n_doc} belge", flush=True)
    return out


# ---------- korpus ----------

def tier_of(pos: int, tiers: list[int], n_real: int) -> int:
    for t in tiers:
        if pos < t - n_real:
            return t
    raise ValueError("konum son kademenin dışında")


def real_chunks(sample: int | None) -> list[dict[str, Any]]:
    from pilot.chunk import read_chunks
    chunks = read_chunks()
    if not sample or sample >= len(chunks):
        return chunks
    step = len(chunks) / sample                       # dokümanlara eşit yayılmış örnek
    return [chunks[int(i * step)] for i in range(sample)]


def build(out_dir: Path, target: int | None, tiers: list[int] | None, real_sample: int | None, force: bool) -> Path:
    cfg = load_sources()
    tiers = sorted(tiers or cfg["tiers"])
    target = target or tiers[-1]
    tiers = [t for t in tiers if t <= target] or [target]
    if tiers[-1] != target:
        tiers.append(target)
    params = {"target": target, "tiers": tiers, "real_sample": real_sample, "seed": cfg["seed"],
              "sources": cfg["sources"], "chunk_chars": cfg["chunk_chars"]}
    manifest_path = out_dir / "manifest.json"
    if manifest_path.exists() and not force:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("params") == params:
            print(f"korpus hazır: {out_dir} (aynı ayarlar; yeniden kurmak için --force)")
            return out_dir
    t0 = time.time()
    real = real_chunks(real_sample)
    n_dd = target - len(real)
    if n_dd < 0:
        raise SystemExit(f"hedef {target} < gerçek parça {len(real)}")
    sample = target <= 10 * ROWS_PAGE * len(cfg["sources"])
    quotas = {s["key"]: round(n_dd * s["share"]) for s in cfg["sources"]}
    quotas[cfg["sources"][-1]["key"]] += n_dd - sum(quotas.values())
    pools: dict[str, list[dict[str, Any]]] = {}
    for s in cfg["sources"]:
        if not s.get("fill"):
            pools[s["key"]] = collect(s, quotas[s["key"]], cfg, sample)
    deficit = sum(quotas[k] - len(v) for k, v in pools.items())
    for s in cfg["sources"]:
        if s.get("fill"):
            pools[s["key"]] = collect(s, quotas[s["key"]] + deficit, cfg, sample)
            deficit = 0
    dd = [c for k in pools for c in pools[k]]
    if len(dd) < n_dd:
        print(f"UYARI: dikkat dağıtıcı {len(dd)} < {n_dd}; korpus {len(real) + len(dd)} parça")
    rng = random.Random(cfg["seed"])
    rng.shuffle(dd)
    brands = Counter(c["brand"] for c in real)
    brand_names, brand_w = list(brands), list(brands.values())

    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("part-*.jsonl"):
        old.unlink()
    counts: Counter = Counter()
    chars = 0
    shard, f = -1, None
    rows = [({**c, "kademe": 0, "kind": "gercek"}) for c in real]
    for pos, c in enumerate(dd):
        doc_id = f"dd-{c['source']}-{c['doc_n']:06d}"
        rows.append({"chunk_id": f"{doc_id}-{c['part']:03d}", "doc_id": doc_id,
                     "brand": rng.choices(brand_names, brand_w)[0], "product": "", "doc_type": "dikkat",
                     "lang": next(s["lang"] for s in cfg["sources"] if s["key"] == c["source"]), "chunk_type": "text",
                     "section": c["title"], "page": 1, "pages": [1], "text": c["text"],
                     "embed_text": f"{c['title']}\n{c['text']}" if c["title"] else c["text"], "nav": "",
                     "source": c["source"], "kademe": tier_of(pos, tiers, len(real)), "kind": "dikkat"})
    for i, r in enumerate(rows):
        if i // SHARD != shard:
            if f:
                f.close()
            shard = i // SHARD
            f = (out_dir / f"part-{shard:05d}.jsonl").open("w", encoding="utf-8", newline="\n")
        f.write(json.dumps(r, ensure_ascii=False) + "\n")
        counts[(r.get("source", "gercek"), r["kademe"])] += 1
        chars += len(r["embed_text"])
    if f:
        f.close()
    per_tier = {t: len(real) + sum(n for (s, k), n in counts.items() if 0 < k <= t) for t in tiers}
    manifest = {"params": params, "total": len(rows), "real": len(real), "distractors": len(dd),
                "per_tier": per_tier, "chars": chars, "tokens_est": int(chars / 3.0),
                "by_source": {s["key"]: {"label": s["label"], "dataset": f"{s['dataset']} ({s['config']})",
                                          "license": s["license"], "chunks": len(pools.get(s["key"], []))}
                              for s in cfg["sources"]},
                "brand_mix": dict(brands), "seconds": round(time.time() - t0, 1), "mode": "rows" if sample else "parquet"}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    info(out_dir)
    return out_dir


def iter_corpus(out_dir: Path, max_kademe: int | None = None) -> Iterator[dict[str, Any]]:
    """Korpus satırları dosya sırasıyla (= nokta kimliği sırası). max_kademe: o kademeye kadar (sıralı yazıldığı için
    ilk büyük kademede durur)."""
    for p in sorted(out_dir.glob("part-*.jsonl")):
        with p.open(encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if max_kademe is not None and r["kademe"] > max_kademe:
                    return
                yield r


def info(out_dir: Path) -> None:
    m = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    print(f"korpus {out_dir}: {m['total']} parça (gerçek {m['real']}, dikkat dağıtıcı {m['distractors']}), "
          f"~{m['tokens_est'] / 1e6:.1f} M token, kademeler {m['per_tier']}, {m['mode']}, {m['seconds']} sn")
    for k, s in m["by_source"].items():
        print(f"  {k:9} {s['chunks']:8d}  {s['license']:13} {s['dataset']}  {s['label']}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--out", default=str(SCALE_DIR / "corpus"))
    b.add_argument("--target", type=int)
    b.add_argument("--tiers", help="virgülle, ör. 10000,30000,100000,1000000")
    b.add_argument("--real-sample", type=int, help="gerçek parçalardan eşit aralıklı örnek (kuru çalıştırma)")
    b.add_argument("--force", action="store_true")
    i = sub.add_parser("info")
    i.add_argument("--out", default=str(SCALE_DIR / "corpus"))
    a = ap.parse_args()
    if a.cmd == "build":
        build(Path(a.out), a.target, [int(x) for x in a.tiers.split(",")] if a.tiers else None, a.real_sample, a.force)
    else:
        info(Path(a.out))


if __name__ == "__main__":
    main()
