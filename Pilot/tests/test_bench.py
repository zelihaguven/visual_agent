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
