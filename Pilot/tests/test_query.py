"""Sorgu analizi: sorudaki model kodu / ürün / marka adından doküman filtresi."""
import pytest

from pilot.query import analyze_query


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


def test_brand_without_model_covers_all_models():
    ctx = analyze_query("Brother makinesinde iplik gerginliği")
    assert set(ctx.doc_ids) == {"brother-s7300a", "brother-s7300b"}


def test_model_family_without_letter_covers_both():
    assert set(analyze_query("S-7300 makinesi").doc_ids) == {"brother-s7300a", "brother-s7300b"}


def test_ambiguous_question_has_no_filter():
    ctx = analyze_query("Dış görünür dikişlerde SPI kaç olmalı?")
    assert ctx.doc_ids == ()
    assert ctx.matched == ()


def test_two_products_in_one_question():
    ctx = analyze_query("Ceket ve pantolon için SPI farkı nedir?")
    assert set(ctx.doc_ids) == {"gl-pd-14-04a", "gl-pd-07-14a"}


def test_a_does_not_leak_to_b():
    assert "brother-s7300b" not in analyze_query("S-7300A hata kodu").doc_ids


def test_matched_terms_are_reported_for_the_ui():
    assert analyze_query("S-7300A ayarı").matched == ("s7300a",)
