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

    def test_dropped_tolerance_in_speech_is_flagged_but_answer_stays_valid(self):
        # R15: ekranda "11 (± 1)", seste "11". Cevap geçerli kalır, sesli metin ayrıca işaretlenir
        v = verify(make(sesli_metin="Dış görünür dikişler inç başına 11 dikiş olmalı."), SRC)
        assert v.status == "verified"
        assert v.checks["sesli_tolerans_tam"] is False
        assert any("Sesli metinde tolerans" in p for p in v.problems)

    def test_tolerance_in_speech_as_words_is_accepted(self):
        v = verify(make(sesli_metin="inç başına 11 artı eksi 1 dikiş"), SRC)
        assert v.checks["sesli_tolerans_tam"] is True

    def test_empty_answer_without_not_found_fails(self):
        # Windows denemesi: cevap alanı boş, alıntı var, "kısmen" gösteriliyordu
        v = verify(make(cevap="", sesli_metin=""), SRC)
        assert v.status == "failed"

    def test_citation_marker_at_end_of_quote_is_ignored(self):
        # Model alıntının sonuna "[1]" ekleyebiliyor (Windows denemesi, S-7300 hız sorusu): bu birebirliği bozmamalı
        ans = make(alintilar=[{"kaynak_no": 1,
                               "metin": "outside visible stitching shall be sewn with 11 (± 1) stitches per inch [1]"}])
        assert verify(ans, SRC).status == "verified"

    def test_quote_cut_by_length_limit_with_half_citation_is_accepted(self):
        # Şema alıntıyı 300 karakterde kesti, sonda yarım atıf kaldı: "... per inch [" (masura kovanı sorusu)
        for tail in (" [", " [1", "["):
            ans = make(alintilar=[{"kaynak_no": 1,
                                   "metin": "outside visible stitching shall be sewn with 11 (± 1) stitches per inch" + tail}])
            assert verify(ans, SRC).checks["alinti_birebir"], tail

    def test_citation_marker_does_not_hide_a_changed_quote(self):
        ans = make(alintilar=[{"kaynak_no": 1,
                               "metin": "outside visible stitching shall be sewn with 12 (± 1) stitches per inch [1]"}])
        assert verify(ans, SRC).status == "failed"

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

    def test_tolerance_only_in_speech_does_not_rescue_screen_answer(self):
        # 2026-10-13: Eskiden tolerans sesli metinde varsa ekrandaki toleranssız cevap da geçiyordu.
        # Tolerans her alanda ayrı kontrol edilir: Ekranda "11" yazıyorsa cevap eksiktir (R4, R15).
        ans = make(cevap="Dış görünür dikişler inç başına 11 dikiş olmalıdır [1].",
                   sesli_metin="inç başına 11 (± 1) dikiş")
        v = verify(ans, SRC)
        assert not v.checks["tolerans_tam"] and v.checks["sesli_tolerans_tam"]
        assert v.status == "failed"

    def test_repetition_loop_fails(self):
        loop = "Masurayı tutarak kovanı yerine yerleştirin. "
        ans = make(cevap="Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır [1]. " + loop * 3, sesli_metin="")
        v = verify(ans, SRC)
        assert v.status == "failed" and not v.checks["tekrar_yok"]

    def test_short_repeated_phrases_are_not_a_loop(self):
        ans = make(cevap="Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır [1]. Evet. Evet.", sesli_metin="")
        assert verify(ans, SRC).checks["tekrar_yok"]

    def test_chinese_drift_fails(self):
        # Kullanıcı denemesi: qwen cevabı Çince yazdı ("在进行缝制前，请先关闭电源开关...")
        ans = make(cevap="Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır [1]. 请先关闭电源开关。")
        v = verify(ans, SRC)
        assert v.status == "failed" and not v.checks["alfabe_dogru"]

    def test_turkish_and_symbols_are_not_foreign(self):
        # "・": Brother kılavuzlarının madde işareti
        ans = make(cevap="Dış görünür dikişler inç başına 11 (± 1) dikiş olmalıdır, çağanoz 90° [1]. ・Gücü kapatın.")
        assert verify(ans, SRC).checks["alfabe_dogru"]

    def test_english_tolerance_words_in_speech_are_accepted(self):
        v = verify(make(sesli_metin="Outside seams need 11 plus or minus 1 stitches per inch."), SRC)
        assert v.checks["sesli_tolerans_tam"]

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

    def test_list_markers_are_not_values(self):
        assert numbers_in("Adımlar:\n1. Gücü kapatın.\n4. Somunu (2) çevirin.\n12) Kontrol edin") == {"2"}

    def test_inline_list_markers_are_not_values(self):
        assert numbers_in("Şu adımları izleyin: 1) Güçten ayırın. 2) Makine başını 90° kaldırın.") == {"90"}

    def test_numbers_inside_sentence_are_still_values(self):
        assert numbers_in("Hız 4. kademeye alınır, 3000 sti/min") == {"4", "3000"}

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
