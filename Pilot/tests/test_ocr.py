"""pilot/ocr.py ve text_layer.junk_score: saf parçalar (OCRmyPDF çağrılmaz)."""
import dataclasses

from pilot import config
from pilot import ocr as O
from pilot.registry import BY_ID
from pilot.text_layer import OCR_MIN_SCORE, junk_score


def test_page_ranges():
    assert O.page_ranges([1, 2, 3, 7, 9, 10]) == "1-3,7,9-10"
    assert O.page_ranges([5]) == "5"
    assert O.page_ranges([3, 1, 2, 2]) == "1-3"


def test_plan_groups_flag_by_kind():
    meta = BY_ID["gl-pd-07-14a"]
    g = O.plan_groups(meta, {1: "metin", 2: "yok", 3: "taranmis", 4: "zayif", 5: "taranmis"})
    assert g == {("--skip-text", "eng"): [2], ("--redo-ocr", "eng"): [3, 5], ("--force-ocr", "eng"): [4]}


def test_plan_groups_language_per_page_from_registry_ranges():
    meta = BY_ID["bosch-ra1171"]                       # en 2–31, fr 32–61, es 62–96
    g = O.plan_groups(meta, {10: "yok", 40: "yok", 70: "yok", 1: "yok"})
    assert g == {("--skip-text", "eng"): [1, 10], ("--skip-text", "fra"): [40], ("--skip-text", "spa"): [70]}


def test_plan_groups_turkish_document_single_language():
    meta = dataclasses.replace(BY_ID["gl-pd-07-14a"], default_lang="tr")
    assert O.plan_groups(meta, {1: "taranmis"}) == {("--redo-ocr", "tur"): [1]}


def test_choose_keeps_old_layer_when_new_is_worse():
    assert O.choose("taranmis", 0.97, 0.99)[0] == "yeni"
    assert O.choose("taranmis", 0.97, 0.96)[0] == "yeni"          # fark tolerans içinde
    chosen, why = O.choose("taranmis", 0.90, 0.61)
    assert chosen == "eski" and "daha kötü" in why
    assert O.choose("zayif", 0.30, 0.95)[0] == "yeni"


def test_choose_filters_meaningless_ocr_on_image_pages():
    assert O.choose("yok", 0.0, OCR_MIN_SCORE)[0] == "yeni"
    chosen, why = O.choose("yok", 0.0, 0.62)
    assert chosen == "goruntu" and "anlamsız" in why


def test_junk_score_real_text_high():
    spec = ("Buttons shall be dull finish, 4 holes, 30 ligne conforming to Type II, Class D, Style 26. "
            "The button and thread shall withstand 40 lbs (minimum) when tested as specified in 4.5.2.")
    assert junk_score(spec) >= 0.9
    tr = "İğne ipliği gerginliği: dikiş başında ipliğin çözülmesini önlemek için üst ipliği ayarlayın."
    assert junk_score(tr) >= 0.95
    assert junk_score("Type III, ±1/8 inch, 7-1/4, 3/16, 0.0001 g, MIL-DTL-32075, NSN 8415-01") >= 0.9


def test_junk_score_ocr_garbage_low():
    plate = "VPCAOLLEAELDAP0 *- RRs N ; | N RWQQN |e ll NNN SSS AWK} $ WW h 5 WK NY NNN NSS"
    assert junk_score(plate) < OCR_MIN_SCORE
    upside_down = "oy} Isn{py uoYQSsry, Moy} eUIneud | ey} J, SuIpurA JUeIIND YyooyD s}eurUI pUe"
    assert junk_score(upside_down) < OCR_MIN_SCORE
    assert junk_score("") == 0.0


def test_ocr_off_by_default_until_approved():
    import importlib
    import os
    if "PILOT_OCR" not in os.environ:
        assert importlib.reload(config).OCR_ENABLED is False


def test_meta_path_prefers_ocr_pdf(tmp_path, monkeypatch):
    meta = BY_ID["gl-pd-07-14a"]
    monkeypatch.setattr(config, "OCR_DIR", tmp_path)
    monkeypatch.setattr(config, "OCR_ENABLED", True)
    assert meta.path == meta.source_path
    (tmp_path / "gl-pd-07-14a.pdf").write_bytes(b"%PDF-1.4")
    assert meta.path == tmp_path / "gl-pd-07-14a.pdf"
    monkeypatch.setattr(config, "OCR_ENABLED", False)
    assert meta.path == meta.source_path


def test_summary_counts():
    rec = {"sure_sn": 3.0, "sayfalar": [{"page": 1, "chosen": "yeni"}, {"page": 2, "chosen": "eski"},
                                         {"page": 3, "chosen": "goruntu"}, {"page": 4, "chosen": "ozgun"}]}
    s = O.summary(rec)
    assert (s["yeni_ocr"], s["eski_katman_kaldi"], s["goruntu_kaldi"], s["ozgun"]) == (1, 1, 1, 1)
    assert s["eski_kaldi_sayfalar"] == [2] and s["goruntu_sayfalar"] == [3]


# --- İki okuma uyuşması (PLAN-OCR §10–§11) ---------------------------------------------------------------------------

def test_unconfirmed_accepts_confusable_equivalents():
    old = "seam allowance 112 inch, 7-114, 3116 and IS min; Class 1 carriers ISO"
    new = "seam allowance 1/2 inch, 7-1/4, 3/16 and 15 min; Class 1 carriers 150"
    assert O.unconfirmed(new, old) == []


def test_unconfirmed_flags_changed_values_and_separators():
    old = "Carrier gas shall be ~99.999% and size 43-3/8 GLIPD 07-14A"
    new = "Carrier gas shall be 299.999% and size 43.3/8 GL/PD 07-144"
    assert O.unconfirmed(new, old) == ["299.999%", "43.3/8", "07-144"]


def test_unconfirmed_tolerates_different_word_boundaries():
    assert O.unconfirmed("withstand 40 lbs", "withstand 40lbs") == []
    assert O.unconfirmed("withstand 40 lbs", "withstand AQ lbs") == ["40"]


def test_check_item_blocks_quote_with_uncertain_ocr_value():
    from pilot.schema_c import check_item
    src = {1: "Carrier gas shall be 299.999% pure."}
    item = {"alintilar": [{"kaynak_no": 1, "metin": "Carrier gas shall be 299.999% pure."}],
            "metin": "Taşıyıcı gaz 299.999% saflıkta olmalı."}
    assert check_item(item, src)["ok"]
    r = check_item(item, src, uncertain={1: ["299.999%"]})
    assert not r["ok"] and r["ocr_belirsiz"] == ["299.999%"]
    assert any("OCR değeri belirsiz" in p for p in r["sorunlar"])
    assert check_item(item, src, uncertain={2: ["299.999%"]})["ok"]       # başka kaynağın belirsizi etkilemez


def test_mark_ocr_sets_flag_and_tokens(tmp_path, monkeypatch):
    import json

    from pilot.chunk import Chunk, mark_ocr
    meta = BY_ID["gl-pd-07-14a"]
    monkeypatch.setattr(config, "OCR_DIR", tmp_path)
    monkeypatch.setattr(config, "OCR_ENABLED", True)
    (tmp_path / "gl-pd-07-14a.json").write_text(json.dumps({"sayfalar": [
        {"page": 30, "chosen": "yeni", "belirsiz": ["299.999%", "B.4"]},
        {"page": 31, "chosen": "eski", "belirsiz": []}]}), encoding="utf-8")
    mk = lambda p, t: Chunk("x", meta.doc_id, "", "", "", "en", "text", "", p, [p], {}, [], t)
    a, b, c = mk(30, "Carrier gas shall be 299.999% pure"), mk(31, "other 299.999%"), mk(29, "none")
    mark_ocr(meta, [a, b, c])
    assert (a.ocr, a.ocr_belirsiz) == (True, ["299.999%"])
    assert (b.ocr, b.ocr_belirsiz) == (False, []) and (c.ocr, c.ocr_belirsiz) == (False, [])
    monkeypatch.setattr(config, "OCR_ENABLED", False)
    d = mk(30, "299.999%")
    mark_ocr(meta, [d])
    assert not d.ocr
