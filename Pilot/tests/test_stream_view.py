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


# ---------- Olay üretici (gri akış C, sıra kuralı B) ----------

from pilot.stream_view import StreamAssembler, item_bounds  # noqa: E402

SRC = {1: "The seams for all outside visible stitching shall be sewn with 11 (± 1) stitches per inch.",
       2: "Overedge stitching shall be 10 (± 2) stitches per inch."}


def _answer(items):
    return json.dumps({"tur": "cevap", "cevap": items, "celiski_var": False}, ensure_ascii=False)


GOOD = {"alintilar": [{"kaynak_no": 1, "metin": "shall be sewn with 11 (± 1) stitches per inch"}],
        "metin": "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır."}
BAD = {"alintilar": [{"kaynak_no": 2, "metin": "Overedge stitching shall be 10 (± 2) stitches per inch."}],
       "metin": "Overlok dikişleri inç başına 12 dikiş olmalıdır."}


def _feed_all(content, step=7):
    events = []
    a = StreamAssembler(SRC, {}, 150, "tr", events.append)
    for k in range(step, len(content) + step, step):
        a.feed(content[:k], k / 1000)
    return a, events


def test_item_bounds_finds_closed_items_only():
    c = _answer([GOOD, BAD])
    b = item_bounds(c)
    assert [json.loads(c[s:e])["metin"] for s, e in b] == [GOOD["metin"], BAD["metin"]]
    assert item_bounds(c[:c.find('"metin": "Overlok')]) == b[:1]


def test_stream_masks_values_until_verified_and_marks_failed_item():
    a, ev = _feed_all(_answer([BAD, GOOD]))
    akis = [e for e in ev if e["olay"] == "oge_akis"]
    assert akis and all(not any(ch.isdigit() for ch in e["metin"]) for e in akis)       # sayı akışta hiç görünmez
    kinds = [e["olay"] for e in ev if e["olay"] != "oge_akis"]
    assert kinds == ["oge_dogrulanamadi", "oge_dogrulandi"]                          # ✖ sırayı tıkamaz
    assert ev[[e["olay"] for e in ev].index("oge_dogrulanamadi")]["mesaj"].startswith("Değer doğrulanamadı")
    done = next(e for e in ev if e["olay"] == "oge_dogrulandi")
    assert done["i"] == 1 and "11 (± 1)" in done["metin"] and done["kaynaklar"] == [1]
    assert a.ilk_gorunen_kelime is not None and a.ilk_dogrulanmis is not None
    assert a.ilk_gorunen_kelime <= a.ilk_dogrulanmis


def test_second_item_text_flows_before_first_is_revealed():
    """Sıra kuralı B: sonraki öğenin metni akar; açılış sıralı."""
    c = _answer([GOOD, GOOD])
    cut = item_bounds(c)[0][1] - 1          # birinci öğe henüz kapanmadı
    events = []
    a = StreamAssembler(SRC, {}, 150, "tr", events.append)
    a.feed(c[:cut], 0.5)
    assert not any(e["olay"] == "oge_dogrulandi" for e in events)
    a.feed(c, 1.0)
    assert [e["i"] for e in events if e["olay"] == "oge_dogrulandi"] == [0, 1]


def test_retry_allowed_only_before_first_verified_item_and_reset_event():
    c = _answer([GOOD])
    events = []
    a = StreamAssembler(SRC, {}, 150, "tr", events.append)
    a.feed(c[:40], 0.2)
    assert a.retry_allowed()
    a.reset()
    assert events[-1] == {"olay": "oge_sifirla"}
    a.feed(c, 1.0)
    assert not a.retry_allowed()
    a.interrupted()
    assert events[-1]["olay"] == "cevap_tamamlanamadi"
