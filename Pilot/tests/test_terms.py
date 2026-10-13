"""Atölye terim sözlüğü: soruya kılavuz terimi eklenir (R16)."""
import pytest

from pilot.terms import expand_query


@pytest.mark.parametrize("question,term", [
    ("S-7300'ün çağanoz tipi nedir?", "rotary hook"),
    ("Çağanozu nasıl yağlarım?", "rotary hook"),          # büyük harf + Türkçe ek
    ("Masuranın gerginliği", "bobbin"),
    ("Dizlik ile baskı ayağı ne kadar kalkar?", "knee lifter"),
    ("Dizlik ile baskı ayağı ne kadar kalkar?", "presser foot"),
    ("Dikiş atlıyor ne yapmalıyım?", "skipped stitches"),
])
def test_known_terms_are_added(question, term):
    expanded, added = expand_query(question)
    assert term in added and term in expanded and expanded.startswith(question)


def test_question_without_terms_is_unchanged():
    assert expand_query("Kahve makinesi nasıl temizlenir?") == ("Kahve makinesi nasıl temizlenir?", [])


def test_term_already_in_english_is_not_duplicated():
    _, added = expand_query("çağanoz (rotary hook) tipi")
    assert added == []


def test_masura_kovani_adds_specific_term():
    _, added = expand_query("Masura kovanı nasıl takılır?")
    assert "bobbin case" in added
