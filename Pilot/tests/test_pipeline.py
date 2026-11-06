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


def test_model_family_question_goes_to_search_and_model(calls):
    # "S-7300" aile kuralı 2026-11-05'te silindi: kural katmanı sormaz, arama filtresiz; ürünler arası
    # belirsizliği cevap modeli şema C'nin netleştirme moduyla sorar (Adım 2 planı §11, §20).
    r = pipeline.soru_cevapla("S-7300'ün maksimum dikiş hızı nedir?")
    assert calls["search"] and calls["search"][0]["doc_ids"] is None and calls["llm"]
    assert r.llm_called


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


def test_json_failure_message_names_the_real_cause(monkeypatch, calls):
    """Kesik (finish=length) ile okunamayan JSON ayrı mesaj alır (2026-11-06, A066: sekme, kesik değildi)."""
    from pilot import jsonparse
    for finish, expect, absent in [("length", "uzunluk sınırında", "JSON okunamadı"),
                                   ("stop", "JSON okunamadı", "uzunluk sınırında")]:
        def broken(user, f=finish):
            return jsonparse.loads('{"cevap": "a" "b"}', f), {}
        monkeypatch.setattr(pipeline, "chat_json", broken)
        r = pipeline.soru_cevapla("soru")
        assert r.verification.status == "failed"
        assert any(expect in p for p in r.verification.problems)
        assert not any(absent in p for p in r.verification.problems)


def test_model_json_accepts_unescaped_control_characters():
    """Alıntıdaki kaçışsız sekme (A066) okunur; ortak adım bütün modeller için strict=False."""
    from pilot import jsonparse
    assert jsonparse.loads('{"metin": "Setting units: 0.05 mm |\t"}', "stop") == {"metin": "Setting units: 0.05 mm |\t"}
    assert jsonparse.raw_decode('{"a": "x\ty"} sonrası')[0] == {"a": "x\ty"}
    try:
        jsonparse.loads('{"a": "kes', "length")
    except jsonparse.ModelJSONError as e:
        assert e.truncated and isinstance(e, json.JSONDecodeError)
    else:
        raise AssertionError("kesik JSON hata vermedi")


PANTOLON =dict(CHUNK, chunk_id="gl-pd-07-14a-00001", doc_id="gl-pd-07-14a", product="Pantolon", page=19,
                text="The seams for all outside visible stitching shall be sewn with 10-14 stitches per inch.")


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
    # verdi ("doğrulanamadı"). Soru neyi sorduğunu söylemiyor: model çağrılmadan sorulur, kullanıcı ayrıntıyı yazar
    # (elle yazılmış konu seçenekleri, ASPECTS, 2026-11-05'te silindi).
    r = pipeline.soru_cevapla("Ceketin ölçüleri nedir?", doc_ids=["gl-pd-14-04a"])
    assert r.verification.status == "clarify"
    assert calls["search"] == [] and calls["llm"] == []
    assert r.answer["secenekler"] == [] and r.answer["ipucu"]


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


def test_model_ambiguity_after_search_is_left_to_the_model(monkeypatch, calls):
    # "Masura kovanı nasıl takılır?": aynı bölüm A ve B'de. Aile kuralı silindi (2026-11-05): kural katmanı
    # "hangi model?" sormaz; değer aynıysa model iki kaynakla cevaplar, farklıysa netleştirme sorar (şema C).
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(S7300A, 0, -0.7), Hit(S7300B, 1, -0.7)])
    pipeline.soru_cevapla("Masura kovanı nasıl takılır?")
    assert calls["llm"]


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


POCKET = dict(CHUNK, chunk_id="gl-pd-14-04a-00090", page=12,
              text="The finished depth of each pocket for sizes X-Small and Small shall be 3-3/4 (+1/8, -0) inches, "
                   "Medium, Large, X-Large and XX-Large shall be 4 inches.")


def test_ungrounded_clarification_is_hidden_when_answer_exists(monkeypatch, calls):
    # 2026-10-16: SPI cevabının yanında "Hangi boy ceket için? Medium, Large, XX-Large?" soruldu; SPI bedene göre
    # değişmiyor, kullanıcı cevaplayamıyordu. Kaynakta geçmeyen seçenekle sorulan soru gösterilmez.
    ask = dict(GOOD, netlestirme_sorusu="Hangi boy ceket için?", netlestirme_secenekleri=["Medium", "Large"])
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (ask, {}))
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "verified"
    assert r.answer["netlestirme_sorusu"] is None and r.answer["netlestirme_secenekleri"] == []
    assert r.answer["atlanan_netlestirme"] == "Hangi boy ceket için?"


def test_grounded_clarification_kept_with_answer(monkeypatch, calls):
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(POCKET, 0, 3.0)])
    ask = dict(GOOD, alintilar=[{"kaynak_no": 1, "metin": "Medium, Large, X-Large and XX-Large shall be 4 inches"}],
               cevap="Medium ve üstü bedenlerde cep derinliği 4 inç [1].", sesli_metin="Cep derinliği 4 inç.",
               netlestirme_sorusu="Hangi beden için?",
               netlestirme_secenekleri=["X-Small", "Medium", "3XL"])
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (ask, {}))
    r = pipeline.soru_cevapla("Ceketin göğüs cebi derinliği ne olmalı?")
    assert r.answer["netlestirme_sorusu"] == "Hangi beden için?"
    assert r.answer["netlestirme_secenekleri"] == ["X-Small", "Medium"]


def test_clarification_without_answer_offers_grounded_options(monkeypatch, calls):
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(POCKET, 0, 3.0)])
    ask = dict(GOOD, cevap="", sesli_metin="", netlestirme_sorusu="Hangi beden için?",
               netlestirme_secenekleri=["Small", "Large", "Nike"])
    monkeypatch.setattr(pipeline, "chat_json", lambda u: (ask, {}))
    r = pipeline.soru_cevapla("Ceketin göğüs cebi derinliği ne olmalı?")
    assert r.verification.status == "clarify"
    assert [o["ek"] for o in r.answer["secenekler"] if "ek" in o] == ["Small", "Large"]


JUKI_E05 = dict(CHUNK, chunk_id="juki-mo6800s-00200", doc_id="juki-mo6800s", brand="JUKI", product="MO-6800S",
                doc_type="machine_manual", chunk_type="table_row", page=46,
                text="Error code: E05 | Description: Pedal signal fault")
BROTHER_E050 = dict(CHUNK, chunk_id="brother-s7300a-00409", doc_id="brother-s7300a", brand="Brother",
                    doc_type="machine_manual", chunk_type="table_row", page=98,
                    text="Code: E050 | Cause: Machine head is detected as being tilted back when start sewing.")


@pytest.fixture
def code_chunks(monkeypatch):
    monkeypatch.setattr(pipeline, "_chunks", lambda: {"all": [JUKI_E05, BROTHER_E050], "rows": {}})


def test_code_missing_in_scope_is_not_found_without_llm(monkeypatch, calls, code_chunks):
    # 2026-10-16 J9: "MO-6800S'te E050" -> arama E05 satırını getirdi, model E05'i anlattı
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(JUKI_E05, 0, 1.0)])
    r = pipeline.soru_cevapla("MO-6800S'te E050 hatası ne demek?")
    assert r.verification.status == "not_found" and calls["llm"] == []
    assert "E050" in r.answer["neden"] and r.answer["oneri"] == ["brother-s7300a"]


def test_code_found_by_exact_match_is_added_to_sources(monkeypatch, calls, code_chunks):
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(CHUNK, 0, 1.0)])
    pipeline.soru_cevapla("MO-6800S'te E05 hatası ne demek?")
    assert "Pedal signal fault" in calls["llm"][0]


def test_code_match_ignores_hyphen_and_model_aliases():
    assert pipeline._has_code("Code: E-050 | Cause: x", "E050")
    assert not pipeline._has_code("Code: E0501", "E050")
    assert pipeline.code_lookup("S7300A dikiş atlıyor", None, None) == ([], [], {})


def test_code_match_ignores_leading_zeros_but_not_value():
    assert pipeline._has_code("Code: E050 | Cause: x", "E50")          # baştaki sıfır yazılmamış
    assert pipeline._has_code("Code: E-050", "e50")
    assert not pipeline._has_code("Error code: E05 | x", "E50")        # değer farklı (5 ≠ 50): J9 ayrımı korunur
    assert not pipeline._has_code("Code: E050", "E05")


@pytest.fixture
def code_tables(monkeypatch):
    from pilot import query
    monkeypatch.setattr(query, "_code_forms", lambda: {"juki-mo6800s": {("E", 5): frozenset({"E05"})},
                                                       "brother-s7300a": {("E", 50): frozenset({"E050"})}})


def test_short_code_is_normalized_for_search_and_code_lookup(monkeypatch, calls, code_chunks, code_tables):
    seen = []
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: seen.append(q) or [Hit(CHUNK, 0, 1.0)])
    r = pipeline.soru_cevapla("S-7300A'da e50 hatası ne demek?")
    assert r.verification.status != "not_found"                        # eskiden: "E50 kodu ... geçmiyor"
    assert "E050" in seen[0] and "Machine head" in calls["llm"][0]


def test_code_of_other_value_stays_not_found(monkeypatch, calls, code_chunks, code_tables):
    monkeypatch.setattr(pipeline, "search", lambda q, **kw: [Hit(JUKI_E05, 0, 1.0)])
    r = pipeline.soru_cevapla("MO-6800S'te e50 hatası ne demek?")       # JUKI'de E50/E050 yok, E05 başka kod
    assert r.verification.status == "not_found" and calls["llm"] == []


# --- doküman düzeyinde netleştirme (seçenek; varsayılan top3) ---

def _h(doc, score):
    from pilot.retrieve import Hit
    return Hit({"doc_id": doc, "text": "t", "pages": [1]}, 0, None, score)


def test_doc_score_ambiguity_asks_when_rival_product_is_close():
    from pilot.pipeline import doc_score_ambiguity
    hits = [_h("gl-pd-14-04a", 0.5), _h("gl-pd-07-14a", 0.4), _h("gl-pd-14-04a", 0.2), _h("strickland-1956", 0.3)]
    assert doc_score_ambiguity(hits, 0.5) == ("products", ["gl-pd-14-04a", "gl-pd-07-14a"])   # 0.4 / 0.7 = 0.57
    assert doc_score_ambiguity(hits, 0.6) is None


def test_doc_score_ambiguity_only_between_products():
    from pilot.pipeline import doc_score_ambiguity
    models = [_h("brother-s7300b", 0.5), _h("brother-s7300a", 0.45)]
    assert doc_score_ambiguity(models, 0.6) is None              # makine modelleri yer değiştirmez (aile kuralı yok)
    # en iyi doküman terzilik kitabı: kimseyle yer değiştiremez, sorulmaz
    book = [_h("strickland-1956", 0.5), _h("brother-s7300a", 0.45), _h("brother-s7300b", 0.44)]
    assert doc_score_ambiguity(book, 0.5) is None


def test_post_search_ambiguity_default_is_top3():
    from pilot.pipeline import post_search_ambiguity
    hits = [_h("brother-s7300a", 0.5), _h("brother-s7300b", 0.1), _h("brother-s7300a", 0.1)]
    assert post_search_ambiguity(hits) is None                    # iki makine modeli: kural katmanı sormaz
    assert post_search_ambiguity(hits, method="doc_score", ratio=0.5) is None                     # 0.1 / 0.6 düşük


# ---------- c kipi (Adım 2 planı §29): bulut cevap modeli, şema c150b-J ----------

C_ANSWER = {"tur": "cevap", "cevap": [{"alintilar": [{"kaynak_no": 1, "metin": "shall be sewn with 11 (± 1) stitches per inch"}],
                                       "metin": "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır."}],
            "sesli_metin": "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalı.", "celiski_var": False}
C_REC = {"provider": "deepinfra", "content": json.dumps(C_ANSWER, ensure_ascii=False), "first_token": 0.3,
         "zaman": [[0.3, 10], [0.9, 10_000]], "usage": {"cost": 0.0002}, "denemeler": [{"provider": "deepinfra", "err": ""}]}


@pytest.fixture
def c_mode(monkeypatch):
    from pilot import config
    seen = {"search": [], "c": [], "local": []}

    def fake_search(question, **kw):
        seen["search"].append(kw)
        return [Hit(CHUNK, 0, 3.0)] + [Hit(dict(CHUNK, chunk_id=f"x-{i}", text="filler"), i, 1.0) for i in range(1, 12)]

    def fake_c(user):
        seen["c"].append(user)
        return dict(seen.get("answer", C_ANSWER)), dict(C_REC)

    monkeypatch.setattr(config, "ANSWER_MODE", "c")
    monkeypatch.setattr(pipeline, "search", fake_search)
    monkeypatch.setattr(pipeline, "chat_c", fake_c)
    monkeypatch.setattr(pipeline, "chat_json", lambda u: seen["local"].append(u))
    monkeypatch.setattr(pipeline, "_translator", lambda q, scope: (lambda: "outside visible stitching SPI"))
    return seen


def test_c_mode_verified_answer_items_provider_and_eight_sources(c_mode):
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "verified" and not c_mode["local"]
    assert len(r.hits) == 8 and c_mode["c"][0].count("<kaynak no=") == 8
    assert c_mode["search"][0]["translate"]() == "outside visible stitching SPI"
    assert c_mode["search"][0]["translate_limit_s"] == 1.2
    assert r.answer["saglayici"] == "deepinfra" and r.answer["ogeler"][0]["dogrulandi"] is True
    assert r.timings["ilk_dogrulanmis_cumle"] == 0.9 and "on bir, artı eksi bir" in r.speech_text
    assert r.timings["uctan_uca_ilk_dogrulanmis"] >= 0.9 and "istek_oncesi" in r.timings


def test_c_mode_model_clarification_lists_no_answer(c_mode):
    c_mode["answer"] = {"tur": "netlestirme", "netlestirme": {"soru": "Ceket mi pantolon mu?",
                                                             "secenekler": [{"kaynak_no": 1}, {"kaynak_no": 2}]},
                        "cevap": [], "sesli_metin": "", "celiski_var": False}
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "clarify" and r.answer["netlestirme_sorusu"] == "Ceket mi pantolon mu?"
    assert r.llm_called and not r.speech_text


def test_c_mode_not_found(c_mode):
    c_mode["answer"] = {"tur": "bulunamadi", "cevap": [], "sesli_metin": "", "celiski_var": False}
    r = pipeline.soru_cevapla("Ceketin garanti süresi nedir?")
    assert r.verification.status == "not_found" and r.answer["bulunamadi"] is True


def test_c_mode_unverified_quote_fails_and_is_not_spoken(c_mode):
    bad = json.loads(json.dumps(C_ANSWER))
    bad["cevap"][0]["alintilar"][0]["metin"] = "shall be sewn with 12 stitches per inch"
    bad["cevap"][0]["metin"] = "Dış görünür dikişler inç başına 12 dikiş olmalıdır."
    c_mode["answer"] = bad
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "failed" and r.speech_text == ""
    assert r.answer["ogeler"][0]["dogrulandi"] is False


def test_c_mode_service_down_shows_message_without_local_fallback(c_mode, monkeypatch):
    from pilot.cloud import ServiceUnavailable

    def down(user):
        raise ServiceUnavailable("deepinfra: 502; venice: 502; parasail: 502")
    monkeypatch.setattr(pipeline, "chat_c", down)
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "failed" and r.answer["servis_yok"] is True
    assert "kullanılamıyor" in r.verification.problems[0] and not c_mode["local"]
    assert len(r.hits) == 8          # kaynaklar yine gösterilir


def test_c_mode_truncated_json_is_reported_as_truncated(c_mode, monkeypatch):
    from pilot.jsonparse import ModelJSONError

    def cut(user):
        raise ModelJSONError(True, "kesik")
    monkeypatch.setattr(pipeline, "chat_c", cut)
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "failed" and "uzunluk sınırında" in r.verification.problems[0]


def test_bugun_mode_is_default_and_uses_local_path(calls):
    from pilot import config
    assert config.ANSWER_MODE == "bugun"
    r = pipeline.soru_cevapla("Ceketin dış dikişlerinde SPI kaç?")
    assert r.verification.status == "verified" and "translate" not in calls["search"][0]
