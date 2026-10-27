"""Aşama 3 betikleri (bench/scale_corpus.py, bench/scale_index.py): ağsız, bellek içi Qdrant ile."""
import json

import pytest
from qdrant_client import QdrantClient

from bench import scale_corpus, scale_index


def test_split_text_respects_bounds():
    text = "Para one. " * 30 + "\n\nShort para.\n\n" + "x" * 2000
    pieces = scale_corpus.split_text(text, 450, 900)
    assert all(80 <= len(p) <= 900 for p in pieces)
    assert "".join(pieces).count("x") == 2000


def test_tiers_are_nested_and_real_chunks_fill_first():
    tiers = [100, 300, 1000]
    got = [scale_corpus.tier_of(p, tiers, n_real=40) for p in range(960)]
    assert got.count(100) == 60 and got.count(300) == 200 and got.count(1000) == 700
    with pytest.raises(ValueError):
        scale_corpus.tier_of(960, tiers, n_real=40)


def test_build_writes_tier_ordered_corpus_with_real_brand_mix(tmp_path, monkeypatch):
    real = [{"chunk_id": f"r{i}", "doc_id": "gl-pd-14-04a", "brand": "US Army (GL-PD)", "embed_text": f"r {i}",
             "text": f"r {i}"} for i in range(10)]
    monkeypatch.setattr(scale_corpus, "real_chunks", lambda n: real)
    monkeypatch.setattr(scale_corpus, "collect", lambda s, quota, cfg, sample: [
        {"source": s["key"], "doc_n": i, "part": 0, "title": "T", "text": "metin " * 20} for i in range(quota)])
    out = scale_corpus.build(tmp_path, target=50, tiers=[20, 50], real_sample=None, force=True)
    rows = list(scale_corpus.iter_corpus(out))
    assert len(rows) == 50 and [r["kademe"] for r in rows] == sorted(r["kademe"] for r in rows)
    assert sum(r["kademe"] <= 20 for r in rows) == 20                      # 10 gerçek + 10 dikkat dağıtıcı
    dd = [r for r in rows if r["kind"] == "dikkat"]
    assert {r["brand"] for r in dd} == {"US Army (GL-PD)"} and all(r["doc_id"].startswith("dd-") for r in dd)
    assert len(list(scale_corpus.iter_corpus(out, max_kademe=20))) == 20
    m = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    assert m["per_tier"] == {"20": 20, "50": 50}


def test_schema_full_vector_on_disk_without_graph():
    s = scale_index.schema(4096, (256,), full_on_disk=True, full_hnsw=False)
    v = s["vectors_config"]
    assert v["dense"].on_disk and v["dense"].hnsw_config.m == 0
    assert v["dense_s256"].size == 256 and not v["dense_s256"].on_disk
    assert s["optimizers_config"].indexing_threshold == 0 and "bm25" in s["sparse_vectors_config"]


def _corpus(tmp_path, n):
    d = tmp_path / "corpus"
    d.mkdir()
    rows = [{"chunk_id": f"dd-x-{i:06d}-000", "doc_id": f"dd-x-{i:06d}", "brand": "Brother", "text": f"t{i}",
             "embed_text": f"başlık\nt{i}", "pages": [1], "nav": "", "kind": "dikkat", "kademe": 10 if i < 6 else 20}
            for i in range(n)]
    (d / "part-00000.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    return d


def test_index_resumes_without_duplicates_and_copy_tier(tmp_path, monkeypatch):
    qc = QdrantClient(":memory:")
    calls = []
    monkeypatch.setattr(scale_index, "PROGRESS_DIR", tmp_path / "progress")
    monkeypatch.setattr(scale_index, "spec_for", lambda k: {"key": k, "provider": "openrouter", "model": "m", "dim": 8,
                                                            "mrl": [4]})
    monkeypatch.setattr("bench.server.server_client", lambda *a, **k: qc)
    monkeypatch.setattr("bench.providers.prices", lambda: {})
    monkeypatch.setattr("pilot.sparse.bm25_docs", lambda texts: [{1: 1.0} for _ in texts])
    monkeypatch.setattr(scale_index.Embedder, "__call__",
                        lambda self, texts: calls.append(len(texts)) or [[1.0] + [0.1 * i] * 7 for i in range(len(texts))])
    corpus = _corpus(tmp_path, 10)
    args = dict(corpus=corpus, collection="t", key="qwen3-8b", workers=2, size=3, short_dims=(4,), max_kademe=None,
                yes=False, device="cpu", full_on_disk=True, full_hnsw=False)
    first = scale_index.index(**args, stop_after=2)
    assert not first["complete"] and qc.count("t").count == 6
    second = scale_index.index(**args, stop_after=None)
    assert second["complete"] and qc.count("t").count == 10
    assert sum(calls) == 10                                               # bitmiş toplu işler yeniden gönderilmedi
    assert scale_index.index(**args, stop_after=None)["status"] == "tamam" and sum(calls) == 10
    with pytest.raises(SystemExit):                                       # farklı ayarla sürdürme reddedilir
        scale_index.index(**{**args, "size": 4}, stop_after=None)
    assert scale_index.copy("t", "t10", max_kademe=10) == 6
    p = qc.retrieve("t10", ids=[0], with_vectors=True)[0]
    assert set(p.vector) >= {"dense", "dense_s4", "bm25"} and p.payload["access"] == ["all"]
