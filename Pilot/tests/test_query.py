"""Sorgu analizi: sorudaki model kodu / ürün / marka adından doküman filtresi."""
import pytest

from pilot.query import (analyze_query, asks_nothing_specific, missing_entities, question_lang, spoken_codes,
                         strip_terms)


@pytest.mark.parametrize("question,expected", [
    ("S-7300A'da üst iplik gergin değil, ne yapmalıyım?", {"brother-s7300a"}),
    ("S-7300B'de dikiş atlıyor", {"brother-s7300b"}),
    ("s7300a makinesinde hata", {"brother-s7300a"}),
    ("Brother S-7300A iğne değişimi", {"brother-s7300a"}),
    ("Ceketin dış görünür dikişlerinde SPI kaç olmalı?", {"gl-pd-14-04a"}),
    ("Pantolonun cep astarı", {"gl-pd-07-14a"}),
    ("Nike ceketlerinde yaka dikişi", {"gl-pd-14-04a"}),
    ("Kahve makinesi nasıl temizlenir?", {"mrcoffee-2003"}),
    ("Mr. Coffee temizleme", {"mrcoffee-2003"}),
    ("Bosch freze bıçağı", {"bosch-ra1171"}),
])
def test_known_product_or_model_sets_filter(question, expected):
    assert set(analyze_query(question).doc_ids) == expected


@pytest.mark.usefixtures("doc_rules")
def test_brand_without_model_covers_all_models():
    ctx = analyze_query("Brother makinesinde iplik gerginliği")
    assert set(ctx.doc_ids) == {"brother-s7300a", "brother-s7300b"}


@pytest.mark.usefixtures("doc_rules")
def test_model_family_without_letter_covers_both():
    assert set(analyze_query("S-7300 makinesi").doc_ids) == {"brother-s7300a", "brother-s7300b"}


def test_ambiguous_question_has_no_filter():
    ctx = analyze_query("Dış görünür dikişlerde SPI kaç olmalı?")
    assert ctx.doc_ids == ()
    assert ctx.matched == ()


def test_two_products_in_one_question():
    ctx = analyze_query("Ceket ve pantolon için SPI farkı nedir?")
    assert set(ctx.doc_ids) == {"gl-pd-14-04a", "gl-pd-07-14a"}


@pytest.mark.usefixtures("doc_rules")
def test_model_family_without_letter_is_ambiguous():
    assert set(analyze_query("S-7300'ün maksimum dikiş hızı nedir?").variants) == {"brother-s7300a", "brother-s7300b"}
    assert set(analyze_query("Brother makinesinde iplik gerginliği").variants) == {"brother-s7300a", "brother-s7300b"}


def test_english_product_names_set_filter():
    # Dokümanın kendi ürün adı ("trouser", başlıkta) kapsam belirler. Q16 için elle eklenen "coat/jacket/pants"
    # eşanlamlıları ilke gereği kaldırıldı (2026-11-03): "coat" sorusu filtresiz aranır, kaynağı arama bulur.
    assert set(analyze_query("Outside seams of the trousers").doc_ids) == {"gl-pd-07-14a"}
    assert analyze_query("How many stitches per inch are required for buttonholes on the coat?").doc_ids == ()


def test_explicit_model_is_not_ambiguous():
    assert analyze_query("S-7300A'nın maksimum dikiş hızı").variants == ()


def test_a_does_not_leak_to_b():
    assert "brother-s7300b" not in analyze_query("S-7300A hata kodu").doc_ids


def test_matched_terms_are_reported_for_the_ui():
    assert analyze_query("S-7300A ayarı").matched == ("s7300a",)


@pytest.mark.usefixtures("doc_rules")
def test_brand_next_to_specific_model_does_not_widen_filter():
    ctx = analyze_query("Brother S-7300A iğne değişimi")
    assert ctx.doc_ids == ("brother-s7300a",) and ctx.variants == ()
    assert ("brother", "makine", ("brother-s7300a", "brother-s7300b")) in ctx.entities


def test_customer_brand_alone_covers_its_products():
    ctx = analyze_query("US Army SPI değerleri")
    assert set(ctx.variants) == {"gl-pd-14-04a", "gl-pd-07-14a"}
    assert analyze_query("US Army ceket SPI").variants == ()


# Seçilen kaynağa göre varlığın rolü (MUST_MATCH): eşleşmeli mi, bağlam mı
@pytest.mark.parametrize("question,scope,missing", [
    ("brother A makinesi ceket ölçüsü", ["brother-s7300a"], {"ceket"}),       # kılavuzda ürün bilgisi olmaz
    ("brother A makinesi ceket ölçüsü", ["gl-pd-14-04a"], set()),             # şartname makineden bağımsız
    ("S-7300A'da dikiş atlıyor", ["brother-s7300b"], set()),                  # aynı aile: diğer modelde ara
    ("S-7300A'da dikiş atlıyor", ["bosch-ra1171"], {"s7300a"}),               # başka makine
    ("Pantolon SPI", ["gl-pd-14-04a"], {"pantolon"}),                         # başka ürün
    ("US Army ceket SPI", ["gl-pd-14-04a"], set()),                           # müşteri markası şartnamede var
    ("Ceket yaka dikişi", ["strickland-1956"], set()),                        # genel rehber: engellemez
])
@pytest.mark.usefixtures("doc_rules")
def test_entity_roles_by_chosen_source(question, scope, missing):
    assert {e[0] for e in missing_entities(analyze_query(question), scope)} == missing


@pytest.mark.parametrize("question,vague", [
    ("brother marka a makinesi ceket ölçüsü", True),
    ("Brother makinesinde ceket dikiş ölçüsü", True),
    ("Ceketin ölçüleri nedir?", True),
    ("S-7300A ayarı", True),
    ("Ceketin dış görünür dikişlerinde SPI kaç olmalı?", False),
    ("Ceket kol boyu", False),
    ("S-7300A maksimum dikiş hızı", False),
    ("brother marka a makinesi ceket ölçüsü (dikiş tipi (stitch type))", False),
])
@pytest.mark.usefixtures("doc_rules")
def test_question_that_asks_nothing_specific(question, vague):
    assert asks_nothing_specific(question, analyze_query(question)) is vague


@pytest.mark.parametrize("spoken,written", [
    # Kullanıcı denemesi: Whisper kodu söylendiği gibi yazdı, A tanınmadı, "hangi model?" soruldu
    ("Es yetmiş üç yüz A'da E sıfır elli hatası ne demek?", "S-7300A'da E050 hatası ne demek?"),
    ("Es yedi bin üç yüz be makinesinde çağanoz", "S-7300B makinesinde çağanoz"),
    ("S yetmiş üç yüz B'de dikiş atlıyor", "S-7300B'de dikiş atlıyor"),
    ("E yüz otuz üç hatası", "E133 hatası"),
    ("E bir üç üç hatası", "E133 hatası"),          # rakam rakam okunuş
    ("e sıfır yedi hatası", "E07 hatası"),
    # Kod harfi olmadan sayı kelimelerine dokunulmaz
    ("bir sorun var, iki iplik kopuyor", "bir sorun var, iki iplik kopuyor"),
    ("Ceketin dış dikişlerinde on bir dikiş", "Ceketin dış dikişlerinde on bir dikiş"),
    ("ayarı de iki kez kontrol et", "ayarı de iki kez kontrol et"),
    ("S-7300A'da E050 hatası", "S-7300A'da E050 hatası"),
])
def test_spoken_codes_become_written_codes(spoken, written):
    assert spoken_codes(spoken) == written


@pytest.mark.parametrize("question,lang", [
    ("How many stitches per inch for the trouser overedge seams?", "en"),
    ("What does error E050 mean on the S-7300A?", "en"),
    ("Ceketin dış görünür dikişlerinde SPI kaç olmalı?", "tr"),
    ("S-7300A E050 hatasi ne demek", "tr"),          # Türkçe karakter yazılmamış
    ("SPI", "tr"),                                     # karar verilemiyor: Türkçe
])
def test_question_language(question, lang):
    assert question_lang(question) == lang


def test_spoken_model_code_sets_filter():
    assert analyze_query("Es yetmiş üç yüz A'da E sıfır elli hatası ne demek?").doc_ids == ("brother-s7300a",)


def test_strip_terms_removes_suffixed_words():
    assert strip_terms("Brother'da ceketin SPI değeri", ["brother", "ceket"]) == "SPI değeri"


@pytest.mark.parametrize("question,brand", [
    ("Nike tişörtlerinde yaka ribanası kaç cm olmalı?", "Nike"),
    ("Nike'ın ceket şartnamesinde SPI nedir?", "Nike"),
    ("Adidas eşofmanlarında dikiş tipi", "Adidas"),
    ("H&M pantolonlarında overlok", "H&M"),
])
def test_foreign_brand_is_detected(question, brand):
    assert brand in analyze_query(question).foreign_brands


@pytest.mark.parametrize("question", [
    "Ceketin dış görünür dikişlerinde SPI kaç olmalı?",
    "Mavi iplik kullanılabilir mi?",              # 'Mavi' marka adı da olabilir, renk anlamında yanlış alarm vermemeli
    "Kahve makinesi nasıl temizlenir?",
    "Brother S-7300A iğne değişimi",
])
def test_no_false_foreign_brand(question):
    assert analyze_query(question).foreign_brands == ()


def test_code_key_and_normalization(monkeypatch):
    from pilot import query
    assert query.code_key("e50") == query.code_key("E-050") == ("E", 50) and query.code_key("E05") == ("E", 5)
    monkeypatch.setattr(query, "_code_forms", lambda: {
        "brother-s7300a": {("E", 50): frozenset({"E050"}), ("TO", 99): frozenset({"TO099", "TO99"})},
        "juki-mo6800s": {("E", 5): frozenset({"E05"})}})
    n = query.normalize_codes
    assert n("s7300a e50 ne demek", None) == "s7300a E050 ne demek"     # takma ad dokunulmaz, kod tek yazıma düşer
    assert n("e50'de ne olur", ["juki-mo6800s"]) == "e50'de ne olur"     # kapsamda karşılığı yok: olduğu gibi
    assert n("E05 hatası", ["juki-mo6800s"]) == "E05 hatası"            # zaten korpustaki yazım
    assert n("to99 kodu", None) == "to99 kodu"                          # iki yazım (TO099, TO99): olduğu gibi


def test_query_translation_targets_and_call(monkeypatch):
    from collections import Counter
    from pilot import translate
    monkeypatch.setattr(translate, "_doc_lang_counts", lambda: {"bosch": Counter(en=191, fr=199, es=203),
                                                                "coffee": Counter(en=84, es=83),
                                                                "coat": Counter(en=565)})
    assert translate.target_languages(["coat"]) == ["en"]
    assert set(translate.target_languages(["bosch"])) == {"en", "fr", "es"}
    assert translate.target_languages(None) == ["en"]                     # korpusta en baskın, öteki diller < %25

    class Chat:
        calls = []
        def complete(self, messages, **kw):
            self.calls.append(messages)
            return '{"en": "How do I lock the router table switch E050?", "es": "¿Cómo bloquear el interruptor E050?"}'
    chat = Chat()
    out = translate.translate_query("Freze şalteri E050 nasıl kilitlenir?", "tr", ["en", "es"], chat)
    assert out["en"].startswith("How do I lock") and "E050" in out["es"] and len(chat.calls) == 1
    assert "E050" in translate.bm25_text(out, "x") and translate.bm25_text({}, "özgün") == "özgün"
    assert translate.translate_query("How to lock?", "en", ["en"], chat) == {"en": "How to lock?"}
    assert len(chat.calls) == 1                                           # hedef dildeki soru için çağrı yok


def test_doc_specific_rules_are_off_by_default():
    """PILOT_DOC_SPECIFIC_RULES kapalı (varsayılan): elle yazılmış marka/aile grupları ve konu seçenekleri yok.
    Model adı geçen sorular (kayıttaki takma ad) etkilenmez."""
    from pilot.query import aspects_for, brand_aliases, detail_hint, family
    assert analyze_query("Brother makinesinde iplik gerginliği").doc_ids == ()
    assert analyze_query("S-7300 makinesi").doc_ids == ()
    assert analyze_query("S-7300A hata kodu").doc_ids == ("brother-s7300a",)
    assert brand_aliases() == {} and family("brother-s7300a") == {"brother-s7300a"}
    assert aspects_for(["gl-pd-14-04a"]) == [] and detail_hint("machine_manual", "x") == "x"


def test_doc_specific_rules_flag_restores_old_behavior(doc_rules):
    from pilot.query import detail_hint, family
    assert set(analyze_query("Brother makinesinde iplik gerginliği").doc_ids) == {"brother-s7300a", "brother-s7300b"}
    assert family("brother-s7300a") == {"brother-s7300a", "brother-s7300b"}
    assert "E133" in detail_hint("machine_manual")
