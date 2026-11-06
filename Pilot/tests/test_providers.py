"""Aşama 4: sağlayıcı soyutlaması, BM25 normalleştirme, MRL kısa vektör, şema, önbellek. Model ve ağ gerektirmez."""
import math

import pytest
from qdrant_client import QdrantClient, models

from pilot import retrieve
from pilot.embed import short_vector
from pilot.index import collection_schema, point_vectors, short_name
from pilot.sparse import normalize


@pytest.mark.parametrize("text,expected", [
    ("İğne", "iğne"),                                  # 'İ'.lower() birleşik nokta üretip kelimeyi bölüyordu
    ("IŞIK ışık", "iŞiK işik"),                        # I/ı → i (küçük harfe tokenizer çevirir)
    ("Error E-050, E–050", "Error E050, E050"),        # tireli kod tek token
    ("MO-6814S ve S-7300A", "MO6814S ve S7300A"),
    ("3/16-inch", "3/16-inch"),                        # harf-tire-rakam değil: dokunulmaz
])
def test_bm25_normalize(text, expected):
    assert normalize(text) == expected


def test_short_vector_is_normalized_prefix():
    v = [3.0, 4.0, 12.0]
    s = short_vector(v, 2)
    assert s == pytest.approx([0.6, 0.8]) and math.isclose(sum(x * x for x in s), 1.0)


def test_schema_bm25_uses_idf_and_short_vectors():
    s = collection_schema(8, sparse="bm25", short_dims=(4,))
    assert set(s["vectors_config"]) == {"dense", "dense_s4"} and s["vectors_config"]["dense_s4"].size == 4
    assert s["sparse_vectors_config"]["bm25"].modifier == models.Modifier.IDF
    d = collection_schema(8)                           # varsayılan local: iki sparse (bm25 varsayılan, bge-m3 eski yol)
    assert set(d["vectors_config"]) == {"dense"} and set(d["sparse_vectors_config"]) == {"sparse", "bm25"}
    assert d["sparse_vectors_config"]["sparse"].modifier is None
    assert d["sparse_vectors_config"]["bm25"].modifier == models.Modifier.IDF


def test_point_vectors_names():
    pv = point_vectors({"dense": [1.0, 0.0, 0.0, 0.0], "sparse": {3: 1.0}}, sparse="bm25", short_dims=(2,))
    assert set(pv) == {"dense", "bm25", short_name(2)} and pv[short_name(2)] == [1.0, 0.0]


@pytest.fixture
def qc():
    c = QdrantClient(":memory:")
    c.create_collection("t", **collection_schema(4, sparse="bm25", short_dims=(2,)))
    pts = []
    for i in range(40):
        a = i / 40
        dense = [math.cos(a), math.sin(a), 0.3 * (i % 3), 0.1]
        pts.append(models.PointStruct(id=i, vector=point_vectors({"dense": dense, "sparse": {i % 7: 1.0}}, "bm25", (2,)),
                                      payload={"doc_id": "d", "text": f"t{i}", "pages": [1]}))
    c.upsert("t", points=pts)
    return c


@pytest.mark.parametrize("dense_mode", ["full", "short", "short_rescore"])
def test_candidates_dense_modes(qc, dense_mode):
    dense = [1.0, 0.0, 0.0, 0.1]
    q = {"dense": dense, "short": short_vector(dense, 2), "sparse": {0: 1.0}}
    pts = retrieve.candidates(qc, q, retrieve._filter(None, None), "hybrid", collection="t", sparse_name="bm25",
                              dense_mode=dense_mode, short_dim=2, prefetch_k=10, fused_k=8)
    assert 0 < len(pts) <= 8 and pts[0].payload["text"].startswith("t")


def test_short_rescore_orders_by_full_vector(qc):
    dense = [1.0, 0.0, 0.0, 0.1]
    q = {"dense": dense, "short": short_vector(dense, 2), "sparse": {}}
    full = retrieve.candidates(qc, q, None, "dense", collection="t", dense_mode="full", fused_k=5)
    resc = retrieve.candidates(qc, q, None, "dense", collection="t", dense_mode="short_rescore", short_dim=2, fused_k=5)
    assert [p.id for p in resc] == [p.id for p in full]       # aday havuzu yeterli: tam vektör sırası


def test_embed_cache_avoids_second_request(tmp_path, monkeypatch):
    from pilot import cloud
    monkeypatch.setenv("OPENROUTER_API_KEY", "sahte-deger-123")
    monkeypatch.setattr(cloud, "require_zdr", lambda m: None)
    e = cloud.CloudEmbedder("m", cache=cloud.EmbedCache(tmp_path / "c.sqlite"), batch=2)
    calls = []
    monkeypatch.setattr(e, "_call", lambda texts: calls.append(list(texts)) or [[float(len(t)), 1.0] for t in texts])
    a = e.embed(["x", "yy", "zzz"])
    b = e.embed(["yy", "x", "w"])
    assert a[1] == b[0] == [2.0, 1.0] and b[2] == [1.0, 1.0]
    assert calls == [["x", "yy"], ["zzz"], ["w"]]               # aynı metin ikinci kez gönderilmedi
    assert e.stats["cached"] == 2
    e.embed(["x"], use_cache=False)                             # süre ölçümü: önbelleksiz gerçek çağrı
    assert calls[-1] == ["x"]


def test_encode_query_local_default_is_bge_dense_plus_bm25(monkeypatch):
    from pilot import embed as em
    from pilot import sparse
    monkeypatch.setattr(em, "embed", lambda texts: [{"dense": [0.6, 0.8], "sparse": {1: 0.5}} for _ in texts])
    monkeypatch.setattr(sparse, "bm25_query", lambda text: {7: 1.0})
    assert em.encode_query("soru") == {"dense": [0.6, 0.8], "sparse": {7: 1.0}}      # varsayılan: BM25
    monkeypatch.setattr(em, "SPARSE_KIND", "bge-m3")                                # eski yol: bge-m3 sparse
    assert em.encode_query("soru") == {"dense": [0.6, 0.8], "sparse": {1: 0.5}}


def test_rerank_off_by_default_returns_fusion_order(monkeypatch):
    from pilot import embed as em
    from pilot import retrieve
    assert em.RERANK_PROVIDER == "none" and not em.rerank_enabled()
    called = []
    monkeypatch.setattr(retrieve, "rerank", lambda q, ps: called.append(1) or [0.0] * len(ps))
    c = QdrantClient(":memory:")
    c.create_collection(retrieve.COLLECTION, **collection_schema(4))
    c.upsert(retrieve.COLLECTION, points=[models.PointStruct(
        id=i, vector=point_vectors({"dense": [1.0, 0.1 * i, 0.0, 0.0], "sparses": {"bm25": {1: 1.0}, "bge-m3": {1: 1.0}}}),
        payload={"doc_id": "d", "text": f"t{i}", "pages": [1]}) for i in range(5)])
    monkeypatch.setattr(retrieve, "search_client", lambda: c)
    monkeypatch.setattr(retrieve, "release", lambda _: None)
    monkeypatch.setattr(retrieve, "encode_query", lambda t, s=None: {"dense": [1.0, 0.0, 0.0, 0.0], "sparse": {1: 1.0}})
    hits = retrieve.search("q", top_k=3)
    assert not called and [h.rerank_score for h in hits] == [None, None, None] and len(hits) == 3


def test_rerank_uses_header_text_and_rrf_fusion(monkeypatch):
    """Rerank açıkken (PILOT_RERANK_PROVIDER=local|openrouter): reranker'a embed_text gider, sıra RRF birleşimi."""
    from pilot import retrieve
    seen = []
    monkeypatch.setattr(retrieve, "rerank_enabled", lambda: True)
    monkeypatch.setattr(retrieve, "rerank", lambda q, ps: seen.extend(ps) or [0.0, 0.0, 0.0, 0.0, 9.0])
    c = QdrantClient(":memory:")
    c.create_collection(retrieve.COLLECTION, **collection_schema(4))
    c.upsert(retrieve.COLLECTION, points=[models.PointStruct(
        id=i, vector=point_vectors({"dense": [1.0, -0.1 * i, 0.0, 0.0], "sparses": {"bm25": {1: 1.0}, "bge-m3": {1: 1.0}}}),
        payload={"doc_id": "d", "text": f"t{i}", "embed_text": f"Marka Ürün | Bölüm\nt{i}", "pages": [1]})
        for i in range(5)])
    monkeypatch.setattr(retrieve, "search_client", lambda: c)
    monkeypatch.setattr(retrieve, "release", lambda _: None)
    monkeypatch.setattr(retrieve, "encode_query", lambda t, s=None: {"dense": [1.0, 0.0, 0.0, 0.0], "sparse": {1: 1.0}})
    hits = retrieve.search("q", top_k=5)
    assert seen and all(p.startswith("Marka Ürün | Bölüm") for p in seen)
    # reranker son adayı 1. yaptı; birleşimde hibrit sıranın ilk ikisinin arkasına çıkar (test_bench'teki hesap)
    assert [h.fused_rank for h in hits] == [0, 1, 4, 2, 3]
    assert retrieve.rerank_order([0.0, 0.0, 0.0, 0.0, 9.0], "none")[0] == 4       # eski: yalnız reranker skoru


def test_hits_carry_fused_score_when_rerank_off(monkeypatch):
    from pilot import retrieve
    c = QdrantClient(":memory:")
    c.create_collection(retrieve.COLLECTION, **collection_schema(4))
    c.upsert(retrieve.COLLECTION, points=[models.PointStruct(
        id=i, vector=point_vectors({"dense": [1.0, -0.1 * i, 0.0, 0.0], "sparses": {"bm25": {1: 1.0 + i}, "bge-m3": {1: 1.0}}}),
        payload={"doc_id": "d", "text": f"t{i}", "pages": [1]}) for i in range(4)])
    monkeypatch.setattr(retrieve, "search_client", lambda: c)
    monkeypatch.setattr(retrieve, "release", lambda _: None)
    monkeypatch.setattr(retrieve, "encode_query", lambda t, s=None: {"dense": [1.0, 0.0, 0.0, 0.0], "sparse": {1: 1.0}})
    hits = retrieve.search("q", top_k=4, do_rerank=False)
    scores = [h.fused_score for h in hits]
    assert all(s is not None for s in scores) and scores == sorted(scores, reverse=True)
    assert scores[0] <= 1 / 2 + 1 / 2                      # RRF üst sınırı (iki kolda da 1.)


def test_translation_within_limit_feeds_bm25_and_late_one_is_dropped(monkeypatch):
    """İkili yol (Adım 2 planı §29): çeviri dense embed ile paralel; sınır içinde gelirse BM25 onunla, gelmezse özgün soruyla."""
    import time as _t

    from pilot import sparse
    monkeypatch.setattr(retrieve, "encode_query", lambda text, sparse_text=None: {"dense": [1.0], "sparse": {"orig": 1.0}})
    monkeypatch.setattr(retrieve, "SPARSE_KIND", "bm25")
    monkeypatch.setattr(sparse, "bm25_query", lambda text: {text: 1.0})
    q = retrieve._encode_with_translation("dikiş sıklığı", lambda: "stitches per inch", 1.2)
    assert q["sparse"] == {"stitches per inch": 1.0} and retrieve.last_translation["sinir_asildi"] is False
    q = retrieve._encode_with_translation("dikiş sıklığı", lambda: (_t.sleep(0.3), "geç")[1], 0.05)
    assert q["sparse"] == {"orig": 1.0} and retrieve.last_translation["sinir_asildi"] is True
    q = retrieve._encode_with_translation("dikiş sıklığı", lambda: 1 / 0, 1.2)      # çeviri hatası aramayı durdurmaz
    assert q["sparse"] == {"orig": 1.0}
