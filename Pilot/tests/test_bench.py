"""Benchmark düzeneği (bench/): doğruluk ölçüleri, yüzdelik, aşama zamanlayıcısı, sorgu hazırlığı, gizli ayarlar."""
import json
import math

import pytest

from bench import common
from bench.common import (StageTimer, accuracy, first_rank, is_match, overlap_at_k, percentile, pilot_env, prepare,
                          write_result)

ITEM = {"expect_docs": ["a"], "expect_pages": [3, 4]}


def _c(doc, *pages):
    return {"doc_id": doc, "pages": list(pages)}


def test_match_needs_doc_and_page():
    assert is_match(_c("a", 4), ITEM)
    assert is_match(_c("a", 2, 3), ITEM)        # sayfa geçişli parça
    assert not is_match(_c("a", 5), ITEM)
    assert not is_match(_c("b", 3), ITEM)


def test_match_without_pages_is_doc_level():
    assert is_match(_c("a", 99), {"expect_docs": ["a"]})
    assert not is_match(_c("b", 1), {"expect_docs": ["a"]})


def test_match_with_kabul_pairs_is_per_document():
    """Çok dilli/çok dokümanlı kabul: sayfa her dokümanın kendi sayfasıyla eşleşmeli (a s.7 ya da b s.17)."""
    item = {"kabul": [{"doc": "a", "pages": [7]}, {"doc": "b", "pages": [17]}], "expect_docs": ["a", "b"], "expect_pages": [7, 17]}
    assert is_match(_c("a", 7), item) and is_match(_c("b", 17), item)
    assert not is_match(_c("a", 17), item) and not is_match(_c("b", 7), item)    # çapraz eşleşme yok


def test_first_rank_and_accuracy():
    chunks = [_c("b", 3), _c("a", 9), _c("a", 4)]
    assert first_rank(chunks, ITEM) == 3
    assert first_rank(chunks[:2], ITEM) is None
    acc = accuracy([1, 3, None, 6])
    assert acc["n"] == 4
    assert acc["hit@1"] == 0.25 and acc["hit@5"] == 0.5 and acc["hit@20"] == 0.75
    assert acc["mrr"] == pytest.approx((1 + 1 / 3 + 1 / 6) / 4)
    assert math.isnan(accuracy([])["mrr"])


def test_overlap_at_k():
    assert overlap_at_k([1, 2, 3], [1, 2, 3], 3) == 1.0
    assert overlap_at_k([1, 9, 3, 4], [3, 1, 2, 5], 2) == 0.5       # sıra değil küme
    assert overlap_at_k([], [], 5) == 1.0


def test_percentile_matches_linear_interpolation():
    xs = [5.0, 1.0, 3.0, 2.0, 4.0]
    assert percentile(xs, 0.5) == 3.0
    assert percentile(xs, 0.95) == pytest.approx(4.8)
    assert percentile([7.0], 0.95) == 7.0
    assert math.isnan(percentile([], 0.5))


def test_stage_timer_sums_repeated_stages():
    t = StageTimer()
    t.start()
    t("embed", 0.2)
    t("embed", 0.1)
    t("rerank", 1.0)
    cur = t.stop()
    assert cur["embed"] == pytest.approx(0.3)
    t.start()
    t("embed", 0.5)
    t.stop()
    s = t.summary()
    assert s["embed"]["n"] == 2 and s["rerank"]["n"] == 1 and s["total"]["n"] == 2


def test_stage_timer_record_external_timings():
    t = StageTimer()
    t.record({"embed": 1.0, "total": 2.0})
    t.record({"embed": 3.0, "total": 4.0})
    s = t.summary()
    assert s["embed"]["p50"] == 2.0 and s["total"]["n"] == 2


def test_secret_env_values_not_written(monkeypatch):
    monkeypatch.setenv("PILOT_OPENROUTER_API_KEY", "sahte-deger-123")
    monkeypatch.setenv("PILOT_QDRANT_URL", "http://localhost:6333")
    env = pilot_env()
    assert env["PILOT_OPENROUTER_API_KEY"] == "<gizli>"
    assert env["PILOT_QDRANT_URL"] == "http://localhost:6333"
    assert "sahte-deger-123" not in json.dumps(env)


def test_write_result_does_not_overwrite(tmp_path):
    p1 = write_result("x", {"a": 1}, "# x", tmp_path)
    p2 = write_result("x", {"a": 2}, "# x", tmp_path)
    assert p1 != p2 and p1.exists() and p2.exists()
    assert p2.with_suffix(".md").read_text(encoding="utf-8") == "# x"


@pytest.mark.parametrize("stage, sub", [
    ("baseline", "b0-b1"), ("asama1_onerilen", "b0-b1"),
    ("asama2_sunucu_grpc", "b2"), ("asama25_sonra", "b25"),
    ("asama3_sure_synth_1m_8c", "b3"), ("asama3_yuk_scale_qwen3_8b_qdrant_8c", "b3"), ("asama3b_scale_qwen3_8b", "b3"),
    ("asama4_rerank_qwen3-8b_full", "b4"), ("rerank_duzeltme_ozet", "b4"), ("rerank_teshis2", "b4"),
    ("bulunamadi_e2e", "bulunamadi"), ("netlestirme_korumasi", "bulunamadi"),
    ("kayip", "genel"), ("mod_farki", "genel"), ("rerank_modeller", "genel"), ("openrouter_modeller", "genel"),
    ("asama2", "genel"),        # alt çizgisiz "asama2" hiçbir öneke uymaz; asama25 ile karışmasın diye önek "asama2_"
])
def test_stage_dir_routes_by_prefix(stage, sub):
    assert common.stage_dir(stage) == common.OUT_DIR / sub


def test_write_result_default_dir_is_stage_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(common, "OUT_DIR", tmp_path)
    p = write_result("asama25_x", {"a": 1}, "# x")
    assert p.parent == tmp_path / "b25"


def test_load_questions_unapproved_only_on_request(tmp_path):
    (tmp_path / "s.json").write_text(json.dumps([{"id": "A", "q": "x", "dogrulandi": False}, {"id": "B", "q": "y"}]),
                                     encoding="utf-8")
    assert [it["id"] for it in common.load_questions(["s"], tmp_path)] == ["B"]
    assert [it["id"] for it in common.load_questions(["s"], tmp_path, include_unapproved=True)] == ["A", "B"]


def test_prefilter_label_free_overlap_and_order():
    from bench.prefilter_diff import label_free, rank_shift
    ch = lambda *ids: [{"chunk_id": i} for i in ids]
    ref = {"questions": {"q1": {"filtered": ch("a", "b", "c")}, "q2": {"filtered": ch("a", "b")}}}
    oth = {"questions": {"q1": {"filtered": ch("a", "c", "b")}, "q2": {"filtered": ch("a", "x")}}}
    s = label_free(ref, oth, ["q1", "q2"], "filtered")
    assert s["n"] == 2 and s["full_overlap"] == 1 and s["same_order"] == 0 and s["top1_same"] == 2
    assert s["changed"] == ["q1", "q2"] and s["overlap_mean"] == pytest.approx(0.75)
    assert rank_shift(["a", "c", "b"], ["a", "b", "c"]) == pytest.approx(2 / 3)


def test_review_excerpt_checks_quote_in_page_text():
    from bench.aday_inceleme import excerpt_and_check
    chunks = [{"chunk_id": "d-1", "doc_id": "d", "pages": [3], "text": "The tabs  shall be\n2 inches wide."}]
    by_id = {c["chunk_id"]: c for c in chunks}
    ok = {"kanit": "the tabs shall be 2 inches wide", "expect_docs": ["d"], "expect_pages": [3]}
    bad = {**ok, "kanit": "the tabs shall be 3 inches wide"}
    assert excerpt_and_check(ok, chunks, by_id)[1] == "evet"
    assert excerpt_and_check(bad, chunks, by_id)[1].startswith("HAYIR")
    assert excerpt_and_check({"expect_docs": ["d"], "expect_pages": [3]}, chunks, by_id)[0].startswith("The tabs")


def test_review_sources_are_deduplicated_per_document():
    from bench.aday_inceleme import src_text
    it = {"kabul": [{"doc": "a", "pages": [10]}, {"doc": "a", "pages": [9, 10]}, {"doc": "b", "pages": [2]}]}
    assert src_text(it) == ("a; b", "a: s. 9, 10; b: s. 2")
    assert src_text({"kabul": [{"doc": "a", "pages": [5]}, {"doc": "a", "pages": [4]}]}) == ("a", "4, 5")


def test_candidate_generator_refuses_to_lose_hand_edits():
    from bench.aday_sorular import lost_fields
    old = [{"id": "A1", "kabul": [{"doc": "d", "pages": [1]}, {"doc": "d", "pages": [9], "dil_kopyasi": True}],
            "dogrulandi": True, "not_elle": "x"},
           {"id": "A2", "q": "?"}]
    new = [{"id": "A1", "kabul": [{"doc": "d", "pages": [1]}], "dogrulandi": False}]
    lost = lost_fields(old, new)
    assert any("A1.kabul: eleman kaybolur" in x and "dil_kopyasi" in x for x in lost)
    assert any(x.startswith("A1.dogrulandi: değer değişir") for x in lost)
    assert "A1.not_elle: alan kaybolur" in lost and "A2: soru yeniden üretimde yok" in lost
    same = [{"id": "A1", "kabul": [{"doc": "d", "pages": [1]}]}]
    assert lost_fields(same, same + [{"id": "A3"}]) == []          # yeni soru ya da alan eklemek kayıp değil


def test_candidate_generator_main_refuses_current_file():
    import subprocess, sys
    from pathlib import Path
    pilot = Path(__file__).resolve().parent.parent
    path = pilot / "eval" / "aday_sorular.json"
    before = path.read_bytes()
    r = subprocess.run([sys.executable, "-m", "bench.aday_sorular"], cwd=pilot, capture_output=True, text=True,
                       encoding="utf-8", env={**__import__("os").environ, "PYTHONUTF8": "1"})
    assert r.returncode != 0 and "Yazılmadı" in r.stderr                 # dil kopyaları elle eklendi: reddeder
    assert path.read_bytes() == before


@pytest.mark.usefixtures("doc_rules")
def test_prepare_scopes_like_pipeline():
    p = prepare("S-7300A'da E050 hatası ne demek?")
    assert p["skip"] is None and p["doc_ids"] == ["brother-s7300a"]
    assert prepare("S-7300'de iplik nasıl takılır?")["skip"] == "netlestirme"     # A mı B mi
    assert prepare("Nike tişörtte dikiş sıklığı kaç olmalı?")["skip"] == "yabanci_marka"
    free = prepare("İğne nasıl değiştirilir?")
    assert free["skip"] is None and free["doc_ids"] is None


def test_question_sets_load_with_set_tag():
    items = common.load_questions(common.KNOWN_SETS)
    assert {it["set"] for it in items} == set(common.KNOWN_SETS)
    assert len({it["qid"] for it in items}) == len(items)
    assert not set(common.HOLDOUT_SETS) & set(common.KNOWN_SETS)


# ---------- reranker sağlayıcıları, CPU izleyicisi, paylaşılan Qdrant istemcisi ----------

def test_length_batches_group_similar_lengths():
    from pilot.rerankers import length_batches
    b = length_batches([5, 50, 7, 49, 6], 2)
    assert b == [[1, 3], [2, 4], [0]]
    assert sorted(i for g in b for i in g) == list(range(5))


def test_parse_rerank_response_restores_input_order():
    from pilot.rerankers import parse_rerank_response
    body = {"results": [{"index": 2, "relevance_score": 0.9}, {"index": 0, "relevance_score": 0.1}]}
    assert parse_rerank_response(body, 3) == [0.1, float("-inf"), 0.9]
    assert parse_rerank_response({"data": [{"index": 0, "score": 0.5}]}, 1) == [0.5]


def test_openrouter_needs_key_from_env(monkeypatch):
    from pilot.rerankers import make_reranker
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENROUTER_API_KEY"):
        make_reranker("openrouter", "cohere/rerank-v3.5")
    with pytest.raises(ValueError):
        make_reranker("local", "x", backend="yok")


def test_parse_config():
    from bench.rerank_bench import parse_config
    c = parse_config("local:BAAI/bge-reranker-v2-m3:onnx-int8:384:4")
    assert (c["model"], c["backend"], c["max_length"], c["batch"]) == ("BAAI/bge-reranker-v2-m3", "onnx-int8", 384, 4)
    assert parse_config("local:m:torch:512")["batch"] == 8
    o = parse_config("openrouter:cohere/rerank-v3.5")
    assert o["provider"] == "openrouter" and o["model"] == "cohere/rerank-v3.5"
    with pytest.raises(ValueError):
        parse_config("local:m")


def test_ranked_rank_limits_to_first_k_candidates():
    from bench.rerank_bench import ranked_rank
    cands = [_c("b", 1), _c("b", 2), _c("a", 3)]
    assert ranked_rank(cands, None, ITEM, 20) == 3                  # RRF sırası
    assert ranked_rank(cands, [0.1, 0.2, 0.9], ITEM, 20) == 1       # rerank öne aldı
    assert ranked_rank(cands, [0.1, 0.2, 0.9], ITEM, 2) is None     # FUSED_K=2: aday hiç reranka gitmez


def test_zdr_is_mandatory_and_cannot_be_overridden():
    from pilot.cloud import openrouter_body
    b = openrouter_body({"model": "m", "query": "q"})
    assert b["provider"] == {"zdr": True, "data_collection": "deny"} and b["query"] == "q"
    forced = openrouter_body({"model": "m", "provider": {"zdr": False, "data_collection": "allow", "order": ["x"]}})
    assert forced["provider"] == {"zdr": True, "data_collection": "deny", "order": ["x"]}


def test_models_without_zdr_are_refused_before_any_request(monkeypatch):
    from pilot import cloud, rerankers
    monkeypatch.setenv("OPENROUTER_API_KEY", "sahte-deger-123")
    monkeypatch.setattr(cloud, "_fetch_zdr_endpoints", lambda: [
        {"model_id": "qwen/qwen3-reranker-8b", "tag": "fireworks", "safety_retention": False}])
    cloud.zdr_index.cache_clear()
    try:
        with pytest.raises(ValueError, match="ZDR"):
            rerankers.make_reranker("openrouter", "cohere/rerank-v3.5")
        assert rerankers.make_reranker("openrouter", "qwen/qwen3-reranker-8b").model == "qwen/qwen3-reranker-8b"
    finally:
        cloud.zdr_index.cache_clear()


def test_safety_retention_endpoints_do_not_count_as_zdr(monkeypatch):
    """/endpoints/zdr listesi Safety Retention uç noktalarını da içeriyor: yalnız onlar varsa model reddedilir,
    karışıksa o sağlayıcı isteklerde provider.ignore ile dışlanır. Alanı olmayan uç nokta da ZDR sayılmaz."""
    from pilot import cloud
    eps = [{"model_id": "a/only-safety", "tag": "google-vertex/global", "safety_retention": True},
           {"model_id": "a/mixed", "tag": "google-vertex/global", "safety_retention": True},
           {"model_id": "a/mixed", "tag": "deepinfra/fp8", "safety_retention": False},
           {"model_id": "a/no-field", "tag": "x"}]
    monkeypatch.setattr(cloud, "_fetch_zdr_endpoints", lambda: eps)
    monkeypatch.setattr(cloud, "_IGNORE", {})
    cloud.zdr_index.cache_clear()
    try:
        for m in ("a/only-safety", "a/no-field", "a/unknown"):
            with pytest.raises(ValueError, match="ZDR"):
                cloud.require_zdr(m)
        cloud.require_zdr("a/mixed")
        assert cloud.zdr_model_ids() == {"a/mixed"}
        body = cloud.openrouter_body({"model": "a/mixed", "provider": {"ignore": ["y"], "sort": "latency"}})
        assert body["provider"] == {"zdr": True, "data_collection": "deny", "sort": "latency",
                                    "ignore": ["google-vertex", "y"]}
    finally:
        cloud.zdr_index.cache_clear()


def test_cpu_window_mean():
    from bench.cpu import window_mean
    t, v = [1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0]
    assert window_mean(t, v, 1.5, 3.5) == 25.0
    assert window_mean(t, v, 3.2, 3.8) == 30.0       # pencerede örnek yok: önceki örnek
    assert window_mean(t, v, 0.0, 0.5) is None


def test_shared_qdrant_client_is_reused_only_when_enabled(monkeypatch):
    from pilot import index

    class Fake:
        closed = False

        def close(self):
            self.closed = True

    monkeypatch.setattr(index, "client", Fake)
    monkeypatch.setattr(index, "_shared", None)
    monkeypatch.setattr(index, "REUSE", False)
    a = index.search_client()
    index.release(a)
    assert a.closed and index.search_client() is not a          # varsayılan: her arama yeni istemci
    monkeypatch.setattr(index, "REUSE", True)
    s = index.search_client()
    index.release(s)
    assert not s.closed and index.search_client() is s
    index.close_shared()
    assert s.closed and index._shared is None


def test_synthetic_access_is_deterministic_and_half_public():
    from bench.server import GROUPS, synthetic_access
    xs = [synthetic_access(i) for i in range(4000)]
    assert xs == [synthetic_access(i) for i in range(4000)]
    public = sum(1 for x in xs if x == ["all"]) / len(xs)
    assert 0.45 < public < 0.55
    assert {g for x in xs for g in x} == {"all", *GROUPS}


def test_parse_config_options():
    from bench.rerank_bench import parse_config
    c = parse_config("openrouter:qwen/qwen3-reranker-8b@embed@inst")
    assert c["model"] == "qwen/qwen3-reranker-8b" and c["passage"] == "embed_text" and c["instruct"]
    assert c["base"] == "openrouter:qwen/qwen3-reranker-8b"
    d = parse_config("local:BAAI/bge-reranker-v2-m3:onnx-int8:512:4")
    assert d["passage"] == "text" and not d["instruct"] and d["base"] == d["spec"]


def test_fused_order_combines_rerank_and_input_order():
    from bench.rerank_bench import fused_order
    # reranker ve giriş aynı fikirdeyse sıra değişmez
    assert fused_order([3.0, 2.0, 1.0]) == [0, 1, 2]
    # tam ters sıra: uçlar eşit skor (1/61 + 1/63), eşitlikte giriş sırası; ortadaki (2/62) biraz düşük
    assert fused_order([0.1, 0.2, 0.3]) == [0, 2, 1]
    # reranker son adayı birinci yapar: giriş sırasının ilk ikisinin arkasına çıkar, en sonda kalmaz
    assert fused_order([0.0, 0.0, 0.0, 0.0, 9.0]) == [0, 1, 4, 2, 3]


def test_unverified_questions_are_not_measured(tmp_path):
    (tmp_path / "x.json").write_text(json.dumps([
        {"id": "A1", "q": "a", "dogrulandi": False}, {"id": "A2", "q": "b", "dogrulandi": True}, {"id": "Q1", "q": "c"}]),
        encoding="utf-8")
    assert [it["id"] for it in common.load_questions(["x"], tmp_path)] == ["A2", "Q1"]


def test_candidate_draft_is_all_unverified():
    items = json.loads((common.EVAL_DIR / "aday_sorular.json").read_text(encoding="utf-8"))
    assert items and all(it["dogrulandi"] is False for it in items)
    assert not {d for it in items for d in it["expect_docs"]} & {"juki-mo6800s"}     # ayrı tutulan set dışarıda


def test_post_with_retry_retries_transient_errors_only():
    from types import SimpleNamespace

    from pilot.cloud import post_with_retry
    waits = []

    class S:
        def __init__(self, codes):
            self.codes = list(codes)

        def post(self, url, json, timeout):
            return SimpleNamespace(status_code=self.codes.pop(0))

    r, n = post_with_retry(S([503, 429, 200]), "u", {}, 1, sleep=waits.append)
    assert r.status_code == 200 and n == 3 and waits == [1.0, 2.0]
    r, n = post_with_retry(S([404, 200]), "u", {}, 1, sleep=waits.append)      # ZDR reddi: yeniden denenmez
    assert r.status_code == 404 and n == 1
    r, n = post_with_retry(S([503] * 10), "u", {}, 1, retries=2, sleep=lambda s: None)
    assert r.status_code == 503 and n == 3


def test_triple_fusion_rrf_by_chunk_id_with_first_arm_tiebreak():
    from types import SimpleNamespace as P
    from bench.triple_fusion import fuse
    pt = lambda cid, s: P(payload={"chunk_id": cid}, score=s)
    qwen = [pt("a", 0.9), pt("b", 0.8)]
    bge = [pt("b", 0.7), pt("c", 0.6)]          # farklı koleksiyon: aynı parça chunk_id ile eşlenir
    bm25 = [pt("c", 5.0), pt("a", 4.0)]
    out = [p.payload["chunk_id"] for p in fuse([qwen, bge, bm25], 3, rrf_k=2)]
    # a: 1/2 + 1/3, b: 1/3 + 1/2, c: 1/3 + 1/2 → eşitlik: ilk kolun skoru (a 0,9 > b 0,8 > c yok)
    assert out == ["a", "b", "c"]
    assert [p.payload["chunk_id"] for p in fuse([qwen, bge, bm25], 1, rrf_k=2)] == ["a"]


def test_answer_parser_tolerates_thought_blocks_and_classifies_json_problems():
    """Adım 2: boş düşünce bloğu (Gemma 4 kanal işareti, <think>), kod çiti tolere edilir ve sayılır; boş, kesik,
    ayrıştırılamayan ve şema dışı çıktı ayrı sınıflanır."""
    from bench.answer_models import parse_answer
    full = json.dumps({"alintilar": [], "cevap": "", "sesli_metin": "", "celiski_var": False,
                       "netlestirme_sorusu": "", "netlestirme_secenekleri": [], "bulunamadi": True})
    assert parse_answer(full, "stop")[1:] == ("ok", False)
    for wrapped in (f"<think></think>\n{full}", f"<|channel>thought\n<channel|>{full}", f"```json\n{full}\n```"):
        obj, status, thought = parse_answer(wrapped, "stop")
        assert status == "ok" and thought and obj["bulunamadi"] is True
    assert parse_answer("", "stop")[1] == "bos"
    assert parse_answer("<think></think>  ", "stop")[1] == "bos"
    assert parse_answer(full[:40], "length")[1] == "kesik"
    assert parse_answer("Üzgünüm, cevap veremem.", "stop")[1] == "gecersiz"
    assert parse_answer('{"cevap": "x"}', "stop")[1] == "sema_disi"


def test_answer_stream_is_decoded_as_utf8(monkeypatch):
    """SSE akışında charset yok: satırlar UTF-8 çözülmeli ("±", Türkçe harfler); Latin-1 varsayımı "Â±" üretiyordu."""
    from bench import answer_models
    from pilot import cloud
    monkeypatch.setattr(cloud, "require_zdr", lambda m: None)
    monkeypatch.setattr(cloud, "zdr_index", lambda: {"m/x": {"strict": frozenset({"p"}), "safety": frozenset()}})
    monkeypatch.setenv("OPENROUTER_API_KEY", "sahte-deger-123")
    monkeypatch.setitem(answer_models.MODELS, "t", {"id": "m/x", "provider": "p", "reasoning": {"enabled": False}})
    chunk = {"provider": "P", "choices": [{"delta": {"content": "11 (± 1) dikiş, ölçü"}, "finish_reason": "stop"}]}

    class R:
        status_code = 200
        encoding = "ISO-8859-1"
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def iter_lines(self, decode_unicode=False):
            assert not decode_unicode
            yield ("data: " + json.dumps(chunk, ensure_ascii=False)).encode("utf-8")
            yield b"data: [DONE]"

    m = answer_models.CloudModel("t")
    monkeypatch.setattr(m.session, "post", lambda *a, **k: R())
    assert m.stream([{"role": "user", "content": "x"}])["content"] == "11 (± 1) dikiş, ölçü"


def test_proposed_number_check_handles_multi_citations_lists_and_number_words():
    from bench.adim2_analiz import numbers_in_v2, proposed_verify, split_cites, word_numbers
    assert split_cites("a [1, 2] b [2,3,5] c [1-3] d [4]") == "a [1][2] b [2][3][5] c [1][2][3] d [4]"
    assert numbers_in_v2("kullanılmalıdır. [1, 5] 2. Uygun durumlarda 2.00 ve .5 mm [2, 3]") == {"2", "0.5"}
    assert numbers_in_v2("adımlar [1]:<br>1. Saat<br>2. Düğme") == set()
    assert numbers_in_v2("ölçüler [1, 3]: 1. **Long** boyu") == set()
    assert word_numbers("every six months, a team of two workers, back on again, once") == {"6", "2"}
    src = {1: "The tape shall be 11 (± 1) stitches per inch.", 2: "Other text."}
    ans = {"alintilar": [{"kaynak_no": 1, "metin": "The tape shall be 11 (± 1) stitches per inch."}],
           "cevap": "İnç başına 11 (± 1) dikiş [1, 2].", "sesli_metin": ""}
    v = proposed_verify(ans, src)
    assert v.status == "verified" and v.checks["sayilar_alintida"] and v.checks["atif_gecerli"]


def test_clarify_options_verdict():
    from bench.doc_rules_diff import options_verdict
    exp = ["gl-pd-14-04a", "gl-pd-07-14a"]
    assert options_verdict(["gl-pd-07-14a", "gl-pd-14-04a"], exp) == "dogru"
    assert options_verdict(["gl-pd-07-14a", "gl-pd-14-04a", "x"], exp) == "fazlasi_var"
    assert options_verdict(["gl-pd-14-04a", "gl-pd-14-04b"], exp) == "eksik_yanlis"
    assert options_verdict([], exp) == "secenek_yok"
