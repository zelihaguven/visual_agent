"""soru_cevapla(): arama ve LLM taklit edilerek hattın akış mantığı test edilir."""
import json

import pytest

from pilot import pipeline
from pilot.retrieve import Hit

CHUNK = {"chunk_id": "gl-pd-14-04a-00001", "doc_id": "gl-pd-14-04a", "brand": "US Army (GL-PD)",
         "product": "Ceket", "doc_type": "product_standard", "lang": "en", "page": 22, "pages": [22],
         "page_labels": {"22": "22"}, "boxes": [],
         "text": "The seams for all outside visible stitching shall be sewn with 11 (± 1) stitches per inch."}

GOOD = {"bulunamadi": False,
        "alintilar": [{"kaynak_no": 1, "metin": "outside visible stitching shall be sewn with 11 (± 1) stitches per inch"}],
        "cevap": "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır [1].",
        "sesli_metin": "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalı.",
        "netlestirme_sorusu": None, "celiski_var": False}


@pytest.fixture
def calls(monkeypatch):
    seen = {"search": [], "llm": []}

    def fake_search(question, **kw):
        seen["search"].append(kw)
        return [Hit(CHUNK, 0, 3.0)]

    def fake_chat(user):
        seen["llm"].append(user)
        return dict(GOOD), {"prompt_tokens": 100, "output_tokens": 50, "llm_seconds": 1.0}

    monkeypatch.setattr(pipeline, "search", fake_search)
    monkeypatch.setattr(pipeline, "chat_json", fake_chat)
    return seen


def test_verified_answer_gets_normalized_speech_text(calls):
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "verified"
    assert r.speech_text == "Dış görünür dikişler inç başına on bir, artı eksi bir dikiş olmalı."
    assert {"search", "llm", "verify", "total"} <= set(r.timings)


def test_model_code_in_question_filters_documents(calls):
    pipeline.soru_cevapla("S-7300A'da dikiş atlıyor")
    assert calls["search"][0]["doc_ids"] == ["brother-s7300a"]


def test_explicit_doc_ids_override_question_analysis(calls):
    pipeline.soru_cevapla("S-7300A'da dikiş atlıyor", doc_ids=["mrcoffee-2003"])
    assert calls["search"][0]["doc_ids"] == ["mrcoffee-2003"]


def test_brand_filter_is_passed_to_search(calls):
    pipeline.soru_cevapla("herhangi", brands=["Brother"])
    assert calls["search"][0]["brands"] == ["Brother"]


def test_sources_are_numbered_and_carry_metadata(calls):
    pipeline.soru_cevapla("soru")
    prompt = calls["llm"][0]
    assert '<kaynak no="1" doküman="gl-pd-14-04a"' in prompt and 'ürün="Ceket"' in prompt
    assert "<soru>\nsoru\n</soru>" in prompt


def test_page_number_is_not_given_to_the_model(calls):
    pipeline.soru_cevapla("soru")
    assert "22" not in calls["llm"][0].split("<kaynaklar>")[1].split("<soru>")[0].replace("11 (± 1)", "")


def test_no_hits_returns_not_found_without_calling_llm(monkeypatch):
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [])
    called = []
    monkeypatch.setattr(pipeline, "chat_json", lambda u: called.append(u))
    r = pipeline.soru_cevapla("soru")
    assert r.verification.status == "not_found"
    assert r.llm_called is False and called == []


def test_score_threshold_skips_llm(monkeypatch, calls):
    monkeypatch.setattr(pipeline, "MIN_RERANK_SCORE", 5.0)   # hit skoru 3.0
    r = pipeline.soru_cevapla("soru")
    assert r.llm_called is False
    assert calls["llm"] == []


def test_threshold_disabled_by_default(calls):
    assert pipeline.MIN_RERANK_SCORE is None
    assert pipeline.soru_cevapla("soru").llm_called is True


def test_truncated_json_does_not_crash_and_is_marked_failed(monkeypatch, calls):
    def broken(user):
        raise json.JSONDecodeError("Unterminated string", "{", 1)
    monkeypatch.setattr(pipeline, "chat_json", broken)
    r = pipeline.soru_cevapla("soru")
    assert r.verification.status == "failed"
    assert any("JSON" in p for p in r.verification.problems)
    assert r.speech_text == ""


def test_failed_verification_gives_no_speech(monkeypatch, calls):
    bad = dict(GOOD, cevap="12 (± 1) dikiş [1].", sesli_metin="12 dikiş")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (bad, {}))
    r = pipeline.soru_cevapla("soru")
    assert r.verification.status == "failed"
    assert r.speech_text == ""
