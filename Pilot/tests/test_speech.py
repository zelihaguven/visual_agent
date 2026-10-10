"""Sesli metin hazırlığı: sayı, tolerans, aralık, kesir -> Türkçe kelimeler."""
import pytest

from pilot.speech import normalize_for_speech as say


@pytest.mark.parametrize("text,expected", [
    ("inç başına 11 (± 1) dikiş", "inç başına on bir, artı eksi bir dikiş"),
    ("54 (± 2) dikiş", "elli dört, artı eksi iki dikiş"),
    ("10-14 dikiş", "on ile on dört arası dikiş"),
    ("5/8 inç", "sekizde beş inç"),
    ("3/16 inç", "on altıda üç inç"),
    ("0.5 mm", "sıfır virgül beş mm"),
    ("0,5 mm", "sıfır virgül beş mm"),
    ("101 sayfa", "yüz bir sayfa"),
    ("1250 devir", "bin iki yüz elli devir"),
    ("16 dikiş", "on altı dikiş"),
    ("100", "yüz"),
    ("1000", "bin"),
])
def test_numbers_become_turkish_words(text, expected):
    assert say(text) == expected


def test_citation_markers_are_not_read_aloud():
    assert say("11 dikiş [1] olmalı [2].") == "on bir dikiş olmalı."


def test_no_space_before_punctuation_after_citation_removal():
    assert "olmalı ." not in say("dikiş olmalı [1].")


def test_alphanumeric_codes_are_left_for_the_screen():
    out = say("E-07 hatası, model S-7300A")
    assert "E-07" in out and "S-7300A" in out


def test_words_are_separated_not_glued():
    """num2words'ün 'onbir' gibi bitişik çıktısı TTS'te yanlış okunuyordu."""
    assert "on bir" in say("11")
    assert "onbir" not in say("11")
    assert "elli dört" in say("54")


def test_empty_text():
    assert say("") == ""
