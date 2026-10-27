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
                id=pid, vector={"dense": _vec(pid), "sparse": models.SparseVector(indices=list(sp), values=list(sp.values()))},
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
