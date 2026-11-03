"""Yetki alanı (access): yetkisiz parça hiçbir koşulda arama sonuçlarına ve kod eşleşmesine girmez.

Gerçek Qdrant (bellekte) ve gerçek retrieve.search ile; embedding ve reranker sahte, model gerektirmez.
"""
import dataclasses
import random

import pytest
from qdrant_client import QdrantClient, models

from pilot import index, pipeline, registry, retrieve
from pilot.index import collection_schema, with_access

DIM = 8
DOCS = {"doc-herkes": ["all"], "doc-kalite": ["kalite"], "doc-atolye": ["atolye"], "doc-iki": ["kalite", "atolye"]}


def _vec(seed: int) -> list[float]:
    r = random.Random(seed)
    return [r.uniform(-1, 1) for _ in range(DIM)]


def _sparse(seed: int) -> dict[int, float]:
    r = random.Random(seed + 10_000)
    return {r.randrange(50): r.uniform(0.1, 1.0) for _ in range(4)}


@pytest.fixture
def qc(monkeypatch):
    c = QdrantClient(":memory:")
    c.create_collection(retrieve.COLLECTION, **collection_schema(DIM))
    points, pid = [], 0
    for doc, access in DOCS.items():
        for i in range(25):
            sp = _sparse(pid)
            points.append(models.PointStruct(
                id=pid, vector={"dense": _vec(pid), "sparse": models.SparseVector(indices=list(sp), values=list(sp.values())),
                                "bm25": models.SparseVector(indices=list(sp), values=list(sp.values()))},
                payload={"doc_id": doc, "brand": "B", "text": f"{doc} parça {i} E050", "pages": [i], "access": access}))
            pid += 1
    c.upsert(retrieve.COLLECTION, points=points)
    monkeypatch.setattr(retrieve, "search_client", lambda: c)
    monkeypatch.setattr(retrieve, "release", lambda _: None)
    state = {"seed": 0}

    def fake_embed(texts):
        state["seed"] += 1
        return [{"dense": _vec(10_000 + state["seed"]), "sparse": _sparse(20_000 + state["seed"])} for _ in texts]

    monkeypatch.setattr(retrieve, "encode_query", lambda text, sparse_text=None: fake_embed([text])[0])
    monkeypatch.setattr(retrieve, "rerank", lambda q, ps: [random.random() for _ in ps])
    return c


def test_filter_puts_access_inside_qdrant_query():
    f = retrieve._filter(None, ["d"], ["kalite"])
    cond = [c for c in f.must if c.key == "access"][0]
    assert sorted(cond.match.any) == ["all", "kalite"]
    plain = retrieve._filter(None, None, None)                  # yetki/doküman koşulu yok; yalnız gezinme dışlaması
    assert plain.must is None and [c.key for c in plain.must_not] == ["nav"]


@pytest.mark.parametrize("mode", ["dense", "sparse", "hybrid"])
@pytest.mark.parametrize("do_rerank", [True, False])
def test_unauthorized_chunks_never_returned(qc, mode, do_rerank):
    allowed = {d for d, a in DOCS.items() if "all" in a or "atolye" in a}
    for _ in range(200):
        hits = retrieve.search("soru", mode=mode, top_k=20, do_rerank=do_rerank, access=["atolye"])
        assert hits, "yetkili parçalar bulunmalı"
        assert {h.chunk["doc_id"] for h in hits} <= allowed


def test_no_groups_sees_only_public(qc):
    for _ in range(50):
        hits = retrieve.search("soru", top_k=20, access=[])
        assert hits and {h.chunk["doc_id"] for h in hits} == {"doc-herkes"}


def test_access_none_keeps_old_behaviour(qc):
    seen = set()
    for _ in range(50):
        seen |= {h.chunk["doc_id"] for h in retrieve.search("soru", top_k=20)}
    assert seen == set(DOCS)


def test_missing_access_payload_is_closed(monkeypatch):
    """access alanı olmayan eski indeks + yetki verilmiş arama: hiçbir parça dönmez (açık kapı değil, kapalı)."""
    c = QdrantClient(":memory:")
    c.create_collection(retrieve.COLLECTION, **collection_schema(DIM))
    c.upsert(retrieve.COLLECTION, points=[models.PointStruct(id=0, vector={"dense": _vec(0)},
                                                              payload={"doc_id": "x", "text": "t", "pages": [1]})])
    monkeypatch.setattr(retrieve, "search_client", lambda: c)
    monkeypatch.setattr(retrieve, "release", lambda _: None)
    monkeypatch.setattr(retrieve, "encode_query", lambda text, sparse_text=None: {"dense": _vec(1), "sparse": {1: 1.0}})
    assert retrieve.search("q", mode="dense", do_rerank=False, access=["kalite"]) == []


def test_code_lookup_respects_access(monkeypatch):
    chunks = [{"doc_id": d, "brand": "B", "text": "E050 hata", "chunk_type": "table_row", "chunk_id": d}
              for d in ("brother-s7300a", "brother-s7300b")]
    monkeypatch.setattr(pipeline, "_chunks", lambda: {"all": chunks, "rows": {}})
    monkeypatch.setitem(registry.BY_ID, "brother-s7300b",
                        dataclasses.replace(registry.BY_ID["brother-s7300b"], access=("kalite",)))
    found, missing, _ = pipeline.code_lookup("E050 ne demek?", None, None, ["atolye"])
    assert [c["doc_id"] for c in found] == ["brother-s7300a"]
    # Kapsamda yok, yetkisiz dokümanda var: adı "şu kaynakta geçiyor" diye gösterilmez
    found, missing, elsewhere = pipeline.code_lookup("E050 ne demek?", ["juki-mo6800s"], None, ["atolye"])
    assert missing == ["E050"] and elsewhere["E050"] == ["brother-s7300a"]
    found, _, _ = pipeline.code_lookup("E050 ne demek?", None, None, None)     # varsayılan: kontrol yok
    assert {c["doc_id"] for c in found} == {"brother-s7300a", "brother-s7300b"}


def test_visible():
    assert registry.visible("gl-pd-14-04a", None)
    assert registry.visible("gl-pd-14-04a", [])               # varsayılan access=("all",)
    assert not registry.visible("bilinmeyen-doc", ["x"])


def test_with_access_adds_registry_groups():
    assert with_access({"doc_id": "gl-pd-14-04a", "text": "t"})["access"] == ["all"]
    assert with_access({"doc_id": "yok"})["access"] == ["all"]


def test_default_schema_matches_original():
    s = collection_schema()
    assert s["vectors_config"]["dense"].hnsw_config is None and s["vectors_config"]["dense"].on_disk is None
    assert s["quantization_config"] is None and s["on_disk_payload"] is None
    q = collection_schema(quantization="int8", m=32, ef_construct=200)
    assert q["vectors_config"]["dense"].hnsw_config.m == 32
    assert q["quantization_config"].scalar.type == models.ScalarType.INT8
    assert collection_schema(quantization="binary")["quantization_config"].binary.always_ram is True
    with pytest.raises(ValueError):
        index.quantization_config("pq", True)


def test_dense_params():
    assert retrieve.dense_params(None, None, None) is None
    p = retrieve.dense_params(128, "1", 2.0)
    assert p.hnsw_ef == 128 and p.quantization.rescore is True and p.quantization.oversampling == 2.0


def test_update_changed_reembeds_only_changed_points_with_same_ids(monkeypatch):
    c = QdrantClient(":memory:")
    c.create_collection("k", **collection_schema(DIM))
    old = [{"chunk_id": f"d-{i:05d}", "doc_id": "doc-herkes", "embed_text": f"Ürün | Eski {i}\nmetin {i}"} for i in range(3)]
    vec = lambda s: {"dense": _vec(s), "sparse": models.SparseVector(indices=[1], values=[1.0]),
                     "bm25": models.SparseVector(indices=[1], values=[1.0])}
    c.upsert("k", points=[models.PointStruct(id=100 + i, vector=vec(i), payload=ch) for i, ch in enumerate(old)])
    monkeypatch.setattr(c, "close", lambda: None)
    monkeypatch.setattr(index, "client", lambda: c)
    new = [dict(ch) for ch in old]
    new[1]["embed_text"] = "Ürün | Yeni bölüm\nmetin 1"
    calls = []

    def encode(chunks):
        calls.append([x["chunk_id"] for x in chunks])
        return [{"dense": _vec(999), "sparses": {"bm25": {7: 0.5}, "bge-m3": {7: 0.5}}} for _ in chunks]

    assert index.update_changed(new, "k", encode, dry_run=True) == ["d-00001"] and calls == []
    assert index.update_changed(new, "k", encode) == ["d-00001"] and calls == [["d-00001"]]
    pts = {p.id: p for p in c.retrieve("k", ids=[100, 101, 102], with_payload=True, with_vectors=True)}
    assert pts[101].payload["embed_text"] == "Ürün | Yeni bölüm\nmetin 1"
    unit = lambda v: [x / sum(y * y for y in v) ** 0.5 for x in v]        # Cosine: Qdrant normalleştirerek saklar
    assert pts[101].vector["dense"] == pytest.approx(unit(_vec(999)), abs=1e-5)
    assert pts[100].vector["dense"] == pytest.approx(unit(_vec(0)), abs=1e-5)     # değişmeyen nokta aynı
    assert index.update_changed(new, "k", encode) == []                      # ikinci kez: iş yok
    with pytest.raises(ValueError, match="parça kümesi farklı"):
        index.update_changed(new[:2], "k", encode)


def test_update_changed_partial_keeps_distractors_and_corpus_fields(monkeypatch):
    c = QdrantClient(":memory:")
    c.create_collection("s", **collection_schema(DIM, sparse="bm25", short_dims=(4,)))
    real = {"chunk_id": "d-00000", "doc_id": "doc-herkes", "section": "Eski", "embed_text": "Ürün | Eski\nmetin",
            "kind": "gercek", "kademe": 0}
    dd = {"chunk_id": "dd-wiki-tr-000001-000", "doc_id": "dd-wiki-tr-000001", "embed_text": "dikkat", "kind": "dikkat"}
    vec = lambda s: {"dense": _vec(s), "dense_s4": _vec(s)[:4], "bm25": models.SparseVector(indices=[1], values=[1.0])}
    c.upsert("s", points=[models.PointStruct(id=0, vector=vec(0), payload=real),
                          models.PointStruct(id=1, vector=vec(1), payload=dd)])
    monkeypatch.setattr(c, "close", lambda: None)
    monkeypatch.setattr(index, "client", lambda: c)
    new = [{**real, "section": "Yeni", "embed_text": "Ürün | Yeni\nmetin", "boxes": [1]}]
    encode = lambda cs: [{"dense": _vec(999), "sparses": {"bm25": {7: 0.5}}} for _ in cs]
    with pytest.raises(ValueError):                                   # dikkat dağıtıcı chunks'ta yok: tam kipte hata
        index.update_changed(new, "s", encode)
    assert index.update_changed(new, "s", encode, partial=True) == ["d-00000"]
    p0, p1 = c.retrieve("s", ids=[0, 1], with_payload=True, with_vectors=True)
    assert p0.payload == {**real, "section": "Yeni", "embed_text": "Ürün | Yeni\nmetin"}   # kind/kademe kaldı, boxes yok
    assert "dense_s4" in p0.vector and p1.payload == dd and p1.vector["bm25"].indices == [1]
