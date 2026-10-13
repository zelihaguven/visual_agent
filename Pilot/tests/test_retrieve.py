"""Arama: içindekiler satırları sonuçlardan elenir, gerçek tablo satırları kalır."""
import pytest

from pilot.retrieve import is_toc


@pytest.mark.parametrize("text", [
    "5-5-1. Needle up/down ................................... 32 5-5-2. Thread trimming lock ........................... 32",
    "12-1. Thread tension spring ................................... 76",
])
def test_table_of_contents_is_dropped(text):
    assert is_toc(text)


@pytest.mark.parametrize("text", [
    "TOTAL. ..................................... 1 | 00.00%",          # pantolon şartnamesindeki gerçek tablo satırı
    "Permethrin ....................................... | 0.52%",
    "Max. stitch length | 5mm | 7mm(* 5 mm at time of shipment)",
    "Turn off the power switch before installing the bobbin case.",
])
def test_real_content_is_kept(text):
    assert not is_toc(text)
