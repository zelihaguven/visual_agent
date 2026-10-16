"""Tablo varyant kontrolü ve birleşik hücre başlığı (2026-10-16, JUKI MO-6800S görülmemiş doküman testi)."""
from pilot.parse import group_table_rows
from pilot.tables import column_variant, row_identifier, segments, variant_check

OVEREDGE = ("Overedge width | MO-6804(D)/DD: * 1 1.5, 4.0 mm | MO-6814S(D)/DD: 3.0, 4.0 mm | "
            "MO-6816S(D)/DD: 4.0, 5.0, * 1 6.0 mm")
SPEED = "Sewing speed | MO-6804(D)/DD & MO-6814S(D)/DD & MO-6816S(D)/DD: Max. 7,000 sti/min"
MODELS = [
    "No.: 1 | Model name: MO-6804S-0E4-30H | Maximum number of revolutions setting (P41): 7000",
    "No.: 3 | Model name: MO-6814S-BE6-40H | Maximum number of revolutions setting (P41): 6500",
    "No.: 10 | Model name: MO-6816S-FH6-60H | Maximum number of revolutions setting (P41): 6000",
]
ERRORS = [
    "Error code: E01 | Description: Overvoltage error This error code is displayed when the voltage exceeds 317 V.",
    "Error code: E02 | Description: Low voltage error This error code is displayed when the voltage drops below 170 V.",
    "Error code: E05 | Description: Pedal signal fault",
]


def row(text, page=3):
    return {"chunk_type": "table_row", "text": text, "doc_id": "juki-mo6800s", "page": page, "section": "s"}


def answer(cevap, no=1):
    return {"cevap": cevap, "alintilar": [{"kaynak_no": no, "metin": "x"}]}


class TestSpanHeader:
    def test_merged_cell_gets_all_column_headers(self):
        cells = [
            {"r0": 0, "r1": 1, "c0": 1, "c1": 2, "text": "MO-6804", "header": True},
            {"r0": 0, "r1": 1, "c0": 2, "c1": 3, "text": "MO-6814S", "header": True},
            {"r0": 1, "r1": 2, "c0": 0, "c1": 1, "text": "Weight", "header": False},
            {"r0": 1, "r1": 2, "c0": 1, "c1": 3, "text": "28 kg", "header": False},
            {"r0": 2, "r1": 3, "c0": 0, "c1": 3, "text": "Notes", "header": False},
        ]
        rows = [r["text"] for r in group_table_rows(cells)]
        assert rows == ["Weight | MO-6804 & MO-6814S: 28 kg", "Notes"]   # ilk sütundan başlayan geniş hücre: ara başlık

    def test_segments_split_span_headers(self):
        label, segs = segments(SPEED)
        assert label == "Sewing speed" and segs[0][0] == ["MO-6804(D)/DD", "MO-6814S(D)/DD", "MO-6816S(D)/DD"]


class TestColumnVariant:
    def test_differing_columns_are_a_variant(self):
        assert column_variant(OVEREDGE)[1] == ["MO-6804(D)/DD", "MO-6814S(D)/DD", "MO-6816S(D)/DD"]

    def test_common_value_is_not_a_variant(self):
        assert column_variant(SPEED) is None

    def test_answer_without_column_name_asks(self):
        # J3: cevap yalnız MO-6816S değerlerini "MO-6800S için" diye verdi
        r = variant_check(answer("MO-6800S overlok genişliği 4.0, 5.0 veya 6.0 mm olabilir [1]."),
                          "MO-6800S'te overlok genişliği kaç mm?", {1: row(OVEREDGE)})
        assert r and r[1] == ["MO-6804(D)/DD", "MO-6814S(D)/DD", "MO-6816S(D)/DD"]

    def test_answer_naming_the_column_is_fine(self):
        r = variant_check(answer("MO-6816S'te 4.0, 5.0 veya 6.0 mm [1]."), "Overlok genişliği?", {1: row(OVEREDGE)})
        assert r is None

    def test_question_naming_the_column_is_fine(self):
        r = variant_check(answer("4.0, 5.0 veya 6.0 mm [1]."), "MO-6816S overlok genişliği (MO-6816S(D)/DD)",
                          {1: row(OVEREDGE)})
        assert r is None

    def test_common_value_answer_does_not_ask(self):
        assert variant_check(answer("Dakikada 7,000 dikiş [1]."), "MO-6800S hızı?", {1: row(SPEED)}) is None

    def test_text_source_is_ignored(self):
        src = {1: {"chunk_type": "text", "text": OVEREDGE}}
        assert variant_check(answer("4.0 mm [1]."), "soru", src) is None


class TestRowVariant:
    def test_model_rows_are_a_variant(self):
        assert row_identifier(MODELS, "Maximum number of revolutions setting (P41)")[0] == "Model name"

    def test_answer_from_one_model_row_asks(self):
        # J4: değer s.36 model seçim tablosunun tek bir alt modelinin satırından geldi
        r = variant_check(answer("Maksimum devir 6500 [1]."), "MO-6800S'in maksimum hızı nedir?",
                          {1: row(MODELS[1], 36)}, {1: MODELS})
        assert r and r[1] == ["MO-6804S-0E4-30H", "MO-6814S-BE6-40H", "MO-6816S-FH6-60H"]

    def test_named_row_is_fine(self):
        r = variant_check(answer("MO-6814S-BE6-40H için 6500 [1]."), "Hız?", {1: row(MODELS[1], 36)}, {1: MODELS})
        assert r is None

    def test_error_code_table_does_not_ask(self):
        # Açıklamaların çoğu sayı içermez: hata kodu tablosu bir varyant boyutu değil
        r = variant_check(answer("Düşük voltaj, 170 V altında [1]."), "Düşük voltaj hatası hangi voltajda?",
                          {1: row(ERRORS[1], 46)}, {1: ERRORS})
        assert r is None

    def test_matrix_rows_are_not_row_variants(self):
        assert row_identifier([OVEREDGE, SPEED], "MO-6804(D)/DD") is None

    def test_min_max_answer_covering_both_is_fine(self):
        mm = "Initial | Min: 0.087 | Max: 0.130"
        assert variant_check(answer("0.087 ile 0.130 arası [1]."), "Başlangıç değeri?", {1: row(mm)}) is None
        assert variant_check(answer("En az 0.087 [1]."), "Başlangıç değeri?", {1: row(mm)})

    def test_code_and_repeated_headers_are_not_options(self):
        assert column_variant("Use | 3: For mediumweight materials | 5: For heavy-weight materials") is None
        assert column_variant("Needle up/down | Setting value: down | Setting value: up") is None

    def test_attribute_columns_are_not_variants(self):
        # Brother s.40: aynı satırın farklı özellikleri, paralel varyantlar değil
        assert column_variant("No. of stitches F | Setting value: 1 - 19 stitches | Setting units: 1 stitch | "
                              "Initial value: 1") is None
