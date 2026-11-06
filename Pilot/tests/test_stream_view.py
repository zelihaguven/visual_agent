"""Gri akış: gizleme kuralı ve ilk görünen kelime (karar 2026-11-06, seçenek C)."""
import json

from pilot.stream_view import HIDE, first_visible_word_offset, first_visible_word_time, item_text_spans, mask


def test_mask_hides_values_ranges_codes_units_and_number_words():
    m = mask("Dış dikişler inç başına 11 (± 1) dikiş; aralık 10-14, kesir 1/2, 5 mm, E050 ve S-7300A; iki kez.")
    import re
    for s in ("11", "±", "10-14", "1/2", "5 mm", "E050", "S-7300A"):
        assert s not in m, s
    assert not re.search(r"(?<!\w)iki(?!\w)", m)
    assert "Dış dikişler inç başına" in m and HIDE in m and "kez" in m
    assert "five" not in mask("Turn it five times", "en") and "on" in mask("Turn on the power", "en")
    assert "❶" not in mask("Düğme ❶'e basın") and "½" not in mask("½ inç") and "²" not in mask("10 mm²")


def test_item_text_spans_skip_quote_texts_in_both_orders():
    j = json.dumps({"tur": "cevap", "cevap": [{"alintilar": [{"kaynak_no": 1, "metin": "quote A"}], "metin": "Cümle A"},
                                             {"alintilar": [{"kaynak_no": 2, "metin": "quote B"}], "metin": "Cümle B"}]},
                   ensure_ascii=False)
    assert [j[s:e] for s, e in item_text_spans(j)] == ["Cümle A", "Cümle B"]
    m = json.dumps({"tur": "cevap", "cevap": [{"metin": "Önce cümle", "alintilar": [{"kaynak_no": 1, "metin": "q"}]}]},
                   ensure_ascii=False)
    assert [m[s:e] for s, e in item_text_spans(m)] == ["Önce cümle"]


def test_first_visible_word_skips_hidden_tokens_and_waits_for_complete_word():
    c = '{"tur":"cevap","cevap":[{"metin":"11 (± 1) dikiş olmalıdır.","alintilar":[]}]}'
    off = first_visible_word_offset(c)
    assert c[:off].endswith("dikiş")
    assert first_visible_word_offset('{"tur":"cevap","cevap":[{"metin":"Diki') is None     # kelime bitmedi
    tl = [[0.4, 10], [0.6, off - 1], [0.7, off], [1.5, len(c)]]
    assert first_visible_word_time(c, tl) == 0.7
