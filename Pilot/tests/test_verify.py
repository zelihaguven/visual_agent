"""Doğrulama katmanı: yanlış değer 'doğrulandı' diye geçmemeli (R4)."""
import pytest

from pilot.verify import normalize, numbers_in, verify

SRC = {1: "The seams for all outside visible stitching shall be sewn with 11 (± 1) stitches per inch. "
          "Overedge shall be 10 (± 2) stitches per inch.",
       2: "Upper thread is not tight. Adjust the lower thread tension."}


def make(**over):
    base = {"bulunamadi": False,
            "alintilar": [{"kaynak_no": 1, "metin": "outside visible stitching shall be sewn with 11 (± 1) stitches per inch"}],
            "cevap": "Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır [1].",
            "sesli_metin": "Dış görünür dikişler inç başına 11 artı eksi 1 dikiş olmalı.",
            "netlestirme_sorusu": None, "celiski_var": False}
    base.update(over)
    return base


class TestHappyPath:
    def test_fully_valid_answer_is_verified(self):
        v = verify(make(), SRC)
        assert v.status == "verified"
        assert v.problems == []
        assert v.badge == "✔ Doğrulandı"

    def test_missing_citation_is_partial_not_verified(self):
        v = verify(make(cevap="Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır."), SRC)
        assert v.status == "partial"
        assert not v.checks["atif_gecerli"]

    def test_range_and_decimal_with_comma_match_quote(self):
        src = {1: "Seams shall be sewn with 10-14 stitches per inch, width 0.5 inch."}
        ans = make(alintilar=[{"kaynak_no": 1, "metin": "sewn with 10-14 stitches per inch, width 0.5 inch"}],
                   cevap="10-14 dikiş, genişlik 0,5 inç [1].", sesli_metin="")
        assert verify(ans, src).status == "verified"


class TestWrongValuesAreCaught:
    def test_dropped_tolerance_fails(self):
        ans = make(cevap="Dış görünür dikişler inç başına 11 dikiş olmalıdır [1].",
                   sesli_metin="Inç başına 11 dikiş.")
        v = verify(ans, SRC)
        assert v.status == "failed"
        assert not v.checks["tolerans_tam"]

    def test_tolerance_in_speech_text_is_accepted(self):
        ans = make(cevap="Dış görünür dikişler inç başına 11 dikiş olmalıdır [1].",
                   sesli_metin="inç başına 11 (± 1) dikiş")
        assert verify(ans, SRC).checks["tolerans_tam"]

    def test_number_not_in_quote_fails(self):
        ans = make(cevap="Dış görünür dikişler inç başına 12 (± 1) dikiş olmalıdır [1].", sesli_metin="")
        v = verify(ans, SRC)
        assert v.status == "failed"
        assert any("12" in p for p in v.problems)

    def test_fabricated_quote_fails(self):
        ans = make(alintilar=[{"kaynak_no": 1, "metin": "stitches shall be 14 per inch"}])
        v = verify(ans, SRC)
        assert v.status == "failed"
        assert not v.checks["alinti_birebir"]

    def test_quote_from_other_source_fails(self):
        ans = make(alintilar=[{"kaynak_no": 2, "metin": "outside visible stitching shall be sewn with 11 (± 1)"}])
        assert verify(ans, SRC).status == "failed"

    def test_unknown_source_number_fails(self):
        ans = make(alintilar=[{"kaynak_no": 9, "metin": "anything"}])
        v = verify(ans, SRC)
        assert v.status == "failed"
        assert any("Geçersiz kaynak" in p for p in v.problems)

    def test_answer_without_quotes_fails(self):
        v = verify(make(alintilar=[]), SRC)
        assert v.status == "failed"
        assert not v.checks["alinti_var"]

    def test_invalid_citation_marker_flagged(self):
        v = verify(make(cevap="11 (± 1) dikiş [7]."), SRC)
        assert not v.checks["atif_gecerli"]
        assert v.status == "partial"  # sayı ve alıntı doğru, atıf geçersiz


class TestNotFound:
    def test_empty_answer_is_not_found(self):
        v = verify({"bulunamadi": True, "alintilar": [], "cevap": "", "sesli_metin": ""}, SRC)
        assert v.status == "not_found"
        assert v.badge == "✖ Kaynaklarda bulunamadı"

    def test_not_found_with_filled_answer_is_contradiction(self):
        v = verify({"bulunamadi": True, "alintilar": [], "cevap": "11 dikiş", "sesli_metin": ""}, SRC)
        assert v.status == "failed"


class TestModelCodesAreNotValues:
    """Model/parça kodlarının içindeki rakamlar 'uydurma değer' sayılmamalı."""

    def test_model_code_digits_ignored_in_numbers(self):
        assert numbers_in("S-7300A makinesinde 11 dikiş, E-07 hatası, ASTM D6193") == {"11"}

    def test_range_digits_still_counted(self):
        assert numbers_in("10-14 dikiş") == {"10", "14"}

    def test_unit_glued_numbers_still_counted(self):
        assert numbers_in("12mm ve 3/16") == {"12", "3", "16"}

    def test_answer_mentioning_model_code_is_not_failed(self):
        src = {1: "Problem: Skipped stitches occur while sewing. Check the needle."}
        ans = make(alintilar=[{"kaynak_no": 1, "metin": "Skipped stitches occur while sewing"}],
                   cevap="S-7300B makinesinde dikiş atlıyorsa iğneyi kontrol edin [1].", sesli_metin="")
        v = verify(ans, src)
        assert v.status == "verified", v.problems


class TestNormalize:
    @pytest.mark.parametrize("a,b", [
        ("Stitches  per\ninch", "stitches per inch"),
        ("10 - 14", "10-14"),
        ("“quote”", '"quote"'),
        ("a b", "a b"),
    ])
    def test_equivalent_forms(self, a, b):
        assert normalize(a) == normalize(b)
