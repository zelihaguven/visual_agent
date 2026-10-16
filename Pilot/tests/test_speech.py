"""Sesli metin hazırlığı: sayı, tolerans, aralık, kesir -> Türkçe kelimeler."""
import pytest

from pilot.speech import normalize_for_speech as say


@pytest.mark.parametrize("text,expected", [
    ("inç başına 11 (± 1) dikiş", "inç başına on bir, artı eksi bir dikiş"),
    ("54 (± 2) dikiş", "elli dört, artı eksi iki dikiş"),
    ("10-14 dikiş", "on ile on dört arası dikiş"),
    ("5/8 inç", "sekizde beş inç"),
    ("3/16 inç", "on altıda üç inç"),
    ("0.5 mm", "sıfır virgül beş milimetre"),
    ("0,5 mm", "sıfır virgül beş milimetre"),
    ("En büyük dikiş uzunluğu 5 mm'dir.", "En büyük dikiş uzunluğu beş milimetredir."),   # Windows denemesi
    ("10-14 SPI", "on ile on dört arası inç başına dikiş"),
    ("5000 sti/min", "dakikada beş bin dikiş"),
    # 2026-10-16 (JUKI): İngilizce binlik ayırıcı ondalık okunuyordu ("yedi virgül sıfır sıfır sıfır dikiş/dakikadir")
    ("hızı 7,000 dikiş/dakikadır", "hızı dakikada yedi bin dikiştir"),
    ("Max. 7,000 sti/min", "Max. dakikada yedi bin dikiş"),
    ("1.500 devir", "bin beş yüz devir"),
    ("12,500 dikiş", "on iki bin beş yüz dikiş"),
    ("3,8 mm", "üç virgül sekiz milimetre"),
    ("0,125 inç", "sıfır virgül bir iki beş inç"),
    ("1.25 mm", "bir virgül iki beş milimetre"),
    ("317 V - 325 V", "üç yüz on yedi V - üç yüz yirmi beş V"),
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
