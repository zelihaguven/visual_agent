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
    pipeline.soru_cevapla("Dikiş atlıyor, ne yapmalıyım?", doc_ids=["mrcoffee-2003"])
    assert calls["search"][0]["doc_ids"] == ["mrcoffee-2003"]


def test_explicit_doc_of_other_machine_is_not_found(calls):
    # 2026-10-13: Sorudaki makine modeli seçilen makine kılavuzunda eşleşmeli (query.MUST_MATCH)
    r = pipeline.soru_cevapla("S-7300A'da dikiş atlıyor", doc_ids=["mrcoffee-2003"])
    assert r.verification.status == "not_found" and calls["llm"] == []


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


def test_foreign_brand_returns_not_found_without_search_or_llm(calls):
    r = pipeline.soru_cevapla("Nike tişörtlerinde yaka ribanası kaç cm olmalı?")
    assert r.verification.status == "not_found"
    assert calls["search"] == [] and calls["llm"] == []
    assert "Nike" in r.answer["neden"]


def test_ambiguous_model_asks_before_search_or_llm(calls):
    r = pipeline.soru_cevapla("S-7300'ün maksimum dikiş hızı nedir?")
    assert r.verification.status == "clarify"
    assert calls["search"] == [] and calls["llm"] == []
    assert {o["doc_id"] for o in r.answer["secenekler"]} == {"brother-s7300a", "brother-s7300b"}
    assert r.answer["netlestirme_sorusu"]


def test_chosen_variant_runs_normally(calls):
    r = pipeline.soru_cevapla("S-7300'ün maksimum dikiş hızı nedir?", doc_ids=["brother-s7300a"])
    assert r.verification.status != "clarify"
    assert calls["search"][0]["doc_ids"] == ["brother-s7300a"]


def test_section_title_is_given_to_the_model(monkeypatch, calls):
    chunk = dict(CHUNK, section="3.11.1 Seams and stitching")
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(chunk, 0, 3.0)])
    pipeline.soru_cevapla("soru")
    assert 'bölüm="3.11.1 Seams and stitching"' in calls["llm"][0]


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


PANTOLON = dict(CHUNK, chunk_id="gl-pd-07-14a-00001", doc_id="gl-pd-07-14a", product="Pantolon", page=19,
                text="The seams for all outside visible stitching shall be sewn with 10-14 stitches per inch.")


def test_machine_plus_product_question_offers_all_sources(calls):
    # "Brother A makinesi ceket ölçüsü": A / B seçenekleri yanında ceket şartnamesi de seçenek olmalı
    r = pipeline.soru_cevapla("brother marka a makinesi ceket ölçüsü")
    assert r.verification.status == "clarify"
    assert {o["doc_id"] for o in r.answer["secenekler"]} == {"brother-s7300a", "brother-s7300b", "gl-pd-14-04a"}
    assert calls["search"] == [] and calls["llm"] == []


def test_explicit_model_plus_product_asks_which_source(calls):
    # Kullanıcı denemesi: model adı yazılınca belirsizlik yoktu, arama A + cekette yapıldı,
    # cevap A kılavuzundan "ceket ölçüsü 5 mm veya 7 mm" oldu
    r = pipeline.soru_cevapla("Brother S-7300A makinesi ceket ölçüsü")
    assert r.verification.status == "clarify"
    assert {o["doc_id"] for o in r.answer["secenekler"]} == {"brother-s7300a", "gl-pd-14-04a"}
    assert calls["search"] == [] and calls["llm"] == []


def test_two_products_of_same_type_are_not_asked(calls):
    # Karşılaştırma sorusu: iki şartname birlikte aranır
    pipeline.soru_cevapla("Ceket ve pantolon için SPI farkı nedir?")
    assert set(calls["search"][0]["doc_ids"]) == {"gl-pd-14-04a", "gl-pd-07-14a"}


def test_product_missing_in_chosen_machine_manual_is_not_found(calls):
    # Windows denemesi: A seçilince model ilgisiz "En büyük dikiş uzunluğu 5 mm" yazmıştı
    r = pipeline.soru_cevapla("brother marka a makinesi ceket ölçüsü", doc_ids=["brother-s7300a"])
    assert r.verification.status == "not_found"
    assert "ceket" in r.answer["neden"] and "Ceket" in r.answer["neden"]
    assert calls["search"] == [] and calls["llm"] == []


def test_product_missing_in_machine_manual_offers_search_without_product_name(calls):
    # Kullanıcı makine ayarını soruyor olabilir: ürün adı çıkarılmış soru önerilir, karar kullanıcının
    r = pipeline.soru_cevapla("Ceket dikerken S-7300A'da iplik gerginliği", doc_ids=["brother-s7300a"])
    assert r.verification.status == "not_found"
    assert r.answer["yalin_soru"] == "dikerken S-7300A'da iplik gerginliği"


def test_choosing_the_product_source_with_vague_question_asks_what_is_wanted(calls):
    # Windows denemesi: Ceket seçilince "ceket ölçüsü" beden tablosu ve punteriz satırları getirdi, model boş cevap
    # verdi ("doğrulanamadı"). Soru neyi sorduğunu söylemiyor: model çağrılmadan konu seçenekleri sunulur.
    r = pipeline.soru_cevapla("brother marka a makinesi ceket ölçüsü", doc_ids=["gl-pd-14-04a"])
    assert r.verification.status == "clarify"
    assert calls["search"] == [] and calls["llm"] == []
    topics = [o["etiket"] for o in r.answer["secenekler"] if "ek" in o]
    assert "Dış görünür dikiş SPI" in topics and "Overlok SPI" in topics
    assert not any("doc_id" in o for o in r.answer["secenekler"])
    assert "beden" in r.answer["ipucu"]


def test_chosen_topic_runs_and_machine_brand_is_only_context(monkeypatch, calls):
    seen = []
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: (seen.append(q), [Hit(CHUNK, 0, 3.0)])[1])
    r = pipeline.soru_cevapla("brother marka a makinesi ceket ölçüsü (dış görünür dikişlerde inç başına dikiş)",
                              doc_ids=["gl-pd-14-04a"])
    assert r.verification.status == "verified"
    # Şartname makineden bağımsız: "brother" aramadan ve modele giden sorudan çıkarılır, kullanıcıya gösterilir
    assert "brother" not in seen[0].lower()
    assert "brother" not in calls["llm"][0].split("<soru>")[1].lower()
    assert r.context_terms == ["brother"]


def test_customer_brand_without_product_asks_which_product(calls):
    r = pipeline.soru_cevapla("US Army şartnamesinde dış dikişlerde SPI kaç?")
    assert r.verification.status == "clarify"
    assert {o["doc_id"] for o in r.answer["secenekler"]} == {"gl-pd-14-04a", "gl-pd-07-14a"}
    assert "ürün" in r.answer["netlestirme_sorusu"]


def test_voice_question_without_source_asks_which_source(calls):
    # Karar: sesli soruda marka/makine/ürün yoksa sorulur (yazılı soruda tüm dokümanlarda aranır)
    r = pipeline.soru_cevapla("Masura kovanı nasıl takılır?", voice=True)
    assert r.verification.status == "clarify"
    assert len(r.answer["secenekler"]) == len(pipeline.DOCS)
    assert calls["search"] == [] and calls["llm"] == []


def test_same_question_typed_searches_all_documents(calls):
    pipeline.soru_cevapla("Masura kovanı nasıl takılır?")
    assert calls["search"][0]["doc_ids"] is None


def test_spoken_model_code_is_not_asked(calls):
    # Kullanıcı denemesi: "Es yetmiş üç yüz A'da ..." için "hangi model?" sorulmuştu
    r = pipeline.soru_cevapla("Es yetmiş üç yüz A'da E sıfır elli hatası ne demek?", voice=True)
    assert calls["search"][0]["doc_ids"] == ["brother-s7300a"]
    assert "S-7300A'da E050" in calls["llm"][0].split("<soru>")[1]
    assert r.question == "S-7300A'da E050 hatası ne demek?"


def test_voice_question_with_model_runs_normally(calls):
    pipeline.soru_cevapla("S 7300 A makinesinde üst iplik gergin değil", voice=True)
    assert calls["search"][0]["doc_ids"] == ["brother-s7300a"]


def test_voice_question_with_brand_filter_is_not_asked(calls):
    pipeline.soru_cevapla("Masura kovanı nasıl takılır?", voice=True, brands=["Brother"])
    assert calls["search"]


S7300A = dict(CHUNK, chunk_id="brother-s7300a-00087", doc_id="brother-s7300a", brand="Brother",
              product="S-7300A düz dikiş makinesi", doc_type="machine_manual", page=28,
              text="Turn off the power switch before installing the bobbin case.")
S7300B = dict(S7300A, chunk_id="brother-s7300b-00090", doc_id="brother-s7300b", product="S-7300B düz dikiş makinesi")


def test_model_ambiguity_after_search_asks_before_llm(monkeypatch, calls):
    # "Masura kovanı nasıl takılır?": aynı bölüm A ve B'de. Eskiden model 158 sn çalışıp "hangi model?" diye soruyordu
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(S7300A, 0, -0.7), Hit(S7300B, 1, -0.7)])
    r = pipeline.soru_cevapla("Masura kovanı nasıl takılır?")
    assert r.verification.status == "clarify" and calls["llm"] == []
    assert [o["doc_id"] for o in r.answer["secenekler"]] == ["brother-s7300a", "brother-s7300b"]
    assert "model" in r.answer["netlestirme_sorusu"]


def test_irrelevant_results_do_not_trigger_model_question(monkeypatch, calls):
    # Değerlendirme Q10: "Uçak motoru yağı" → A ve B'den skor −8 sonuçlar "hangi model?" sordurdu
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(S7300A, 0, -8.0), Hit(S7300B, 1, -8.1)])
    r = pipeline.soru_cevapla("Uçak motoru yağı kaç derecede değiştirilir?")
    assert r.verification.status != "clarify" and calls["llm"]


def test_unrelated_machines_in_results_do_not_trigger_model_question(monkeypatch, calls):
    bosch = dict(S7300A, doc_id="bosch-ra1171", brand="Bosch", product="RA1171 freze tezgâhı")
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(S7300A, 0, -0.7), Hit(bosch, 1, -2.0)])
    pipeline.soru_cevapla("Masura kovanı nasıl takılır?")
    assert calls["llm"]


def test_model_clarification_offers_found_documents(monkeypatch, calls):
    # Model "hangi model?" diye sorduysa bulunan dokümanlar düğme olur (serbest "a makinesi" eşlenemiyor)
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(S7300A, 0, -0.7), Hit(CHUNK, 1, -0.8)])
    ask = dict(GOOD, cevap="", sesli_metin="", netlestirme_sorusu="Hangi model için?")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (ask, {}))
    r = pipeline.soru_cevapla("Bu nasıl takılır?")
    assert r.verification.status == "clarify"
    assert {o["doc_id"] for o in r.answer["secenekler"]} == {"brother-s7300a", "gl-pd-14-04a"}


def test_model_clarification_without_answer_becomes_clarify(monkeypatch, calls):
    # Model cevap yazmadan "Hangi ölçüm?" diye sordu: "doğrulanamadı" yerine kullanıcıya sorulur
    ask = dict(GOOD, cevap="", sesli_metin="", netlestirme_sorusu="Hangi beden için?")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (ask, {}))
    r = pipeline.soru_cevapla("Ceketin kol boyu toleransı nedir?")
    assert r.verification.status == "clarify"
    assert r.answer["netlestirme_sorusu"] == "Hangi beden için?" and r.llm_called


def test_sibling_model_switch_is_not_blocked(calls):
    # "diğer modelde ara": S-7300A sorusu S-7300B kılavuzunda aranabilmeli
    pipeline.soru_cevapla("S-7300A'da E133 hatası", doc_ids=["brother-s7300b"])
    assert calls["search"][0]["doc_ids"] == ["brother-s7300b"]


def test_product_ambiguity_asks_after_search_without_llm(monkeypatch, calls):
    # R14: "Dış görünür dikişlerde SPI?" → ceket ve pantolon şartnamesi birlikte geliyor
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(CHUNK, 0, 3.0), Hit(PANTOLON, 1, 2.9)])
    r = pipeline.soru_cevapla("Dış görünür dikişlerde SPI kaç olmalı?")
    assert r.verification.status == "clarify"
    assert {o["doc_id"] for o in r.answer["secenekler"]} == {"gl-pd-14-04a", "gl-pd-07-14a"}
    assert calls["llm"] == []


def test_glossary_expands_search_query_but_not_model_question(monkeypatch, calls):
    seen = []
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: (seen.append(q), [Hit(CHUNK, 0, 3.0)])[1])
    r = pipeline.soru_cevapla("S-7300A çağanoz tipi nedir?")
    assert "rotary hook" in seen[0]
    assert "rotary hook" not in calls["llm"][0].split("<soru>")[1]
    assert r.expanded_terms == ["rotary hook"]


def test_speech_is_rebuilt_from_answer_when_model_drops_tolerance(monkeypatch, calls):
    # R15: sesli metin "11" diyor, cevap "11 (± 1)": ses cevaptan üretilmeli
    dropped = dict(GOOD, sesli_metin="Dış görünür dikişler inç başına 11 dikiş olmalı.")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (dropped, {}))
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert "artı eksi bir" in r.speech_text


def test_answer_language_follows_question(monkeypatch, calls):
    # Karar: İngilizce soruya İngilizce cevap (test sorusu 20 Türkçe cevap almıştı)
    en = dict(GOOD, cevap="Outside visible seams shall have 11 (± 1) stitches per inch [1].",
              sesli_metin="Outside visible seams need 11 (± 1) stitches per inch.")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (calls["llm"].append(u), (en, {}))[1])
    r = pipeline.soru_cevapla("How many stitches per inch are required on the coat outside seams?")
    assert "<cevap_dili>EN</cevap_dili>" in calls["llm"][0]
    assert r.lang == "en" and r.verification.status == "verified"
    assert r.speech_text == "Outside visible seams need 11, plus or minus 1 stitches per inch."


def test_speech_in_wrong_language_is_rebuilt_from_answer(monkeypatch, calls):
    # Gerçek veri: cevap İngilizce, sesli metin Türkçe geldi ("Overedge için 6-10 sütun per inç kullanmalısınız")
    mixed = dict(GOOD, cevap="Outside visible seams shall have 11 (± 1) stitches per inch [1].",
                 sesli_metin="Dış dikişlerde inç başına 11 (± 1) dikiş olmalı.")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (mixed, {}))
    r = pipeline.soru_cevapla("How many stitches per inch are required on the coat outside seams?")
    assert r.speech_text == "Outside visible seams shall have 11, plus or minus 1 stitches per inch."


def test_turkish_question_asks_turkish_answer(calls):
    pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert "<cevap_dili>TR</cevap_dili>" in calls["llm"][0]


def test_steps_are_reported_for_the_ui(calls):
    steps = []
    pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?", on_step=steps.append)
    assert [s.split(" (")[0] for s in steps] == ["Kaynaklar aranıyor", "Cevap hazırlanıyor", "Kaynakla kontrol ediliyor"]


def test_failed_verification_gives_no_speech(monkeypatch, calls):
    bad = dict(GOOD, cevap="12 (± 1) dikiş [1].", sesli_metin="12 dikiş")
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (bad, {}))
    r = pipeline.soru_cevapla("soru")
    assert r.verification.status == "failed"
    assert r.speech_text == ""
