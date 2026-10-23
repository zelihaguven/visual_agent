"""Parçalama değişikliğinin etkisi: yeni kurallarla parçalar bellekte üretilir, chunks.jsonl ile karşılaştırılır.

Kullanım: python -m bench.chunk_diff [doc_id ...]   (indeksleme yapmaz, dosya yazmaz; özet ekrana)
"""
import collections
import sys
from dataclasses import asdict

from pilot.chunk import build_chunks, read_chunks
from pilot.figures import load_figures
from pilot.parse import load_or_parse
from pilot.registry import BY_ID, DOCS


def fresh(doc_id: str) -> list[dict]:
    meta = BY_ID[doc_id]
    return [asdict(c) for c in build_chunks(meta, load_or_parse(meta)["elements"], load_figures(meta))]


def main(doc_ids: list[str]) -> None:
    old: dict[str, list[dict]] = collections.defaultdict(list)
    for c in read_chunks():
        old[c["doc_id"]].append(c)
    changed = []
    for d in doc_ids:
        new = fresh(d)
        o = old[d]
        nav = collections.Counter(c["nav"] for c in new if c["nav"])
        same_text = [c["text"] for c in o] == [c["text"] for c in new]
        sec_o = collections.Counter(c["section"] for c in o)
        sec_n = collections.Counter(c["section"] for c in new)
        same_embed = [c["embed_text"] for c in o] == [c["embed_text"] for c in new]
        print(f"{d:18} parça {len(o):4} → {len(new):4} · metin aynı: {same_text} · embed_text aynı: {same_embed} · "
              f"bölüm sayısı {len(sec_o)} → {len(sec_n)} · nav: {dict(nav)}")
        print(f"{'':18} en sık bölüm önce: {sec_o.most_common(1)[0][1]}× {sec_o.most_common(1)[0][0][:40]!r} · "
              f"sonra: {sec_n.most_common(1)[0][1]}× {sec_n.most_common(1)[0][0][:40]!r}")
        if not same_embed:
            changed.append(d)
    print("yeniden embed gereken dokümanlar:", " ".join(changed) or "–")


if __name__ == "__main__":
    main(sys.argv[1:] or [d.doc_id for d in DOCS])
