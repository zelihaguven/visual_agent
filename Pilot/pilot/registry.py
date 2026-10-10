"""Pilot doküman kaydı (metadata). Kaynak: Pre/notes/manual-envanteri.md."""
from dataclasses import dataclass
from pathlib import Path

from .config import MANUALS_DIR


@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    file: str
    brand: str
    product: str
    doc_type: str                              # product_standard | machine_manual | tailoring_guide
    default_lang: str = "en"
    lang_ranges: tuple[tuple[int, int, str], ...] = ()   # (ilk_sayfa, son_sayfa, dil)
    aliases: tuple[str, ...] = ()              # sorguda geçerse filtre: küçük harf, '-' ve boşluksuz

    @property
    def path(self) -> Path:
        return MANUALS_DIR / self.file

    def lang_of(self, page: int) -> str:
        for first, last, lang in self.lang_ranges:
            if first <= page <= last:
                return lang
        return self.default_lang


DOCS: tuple[DocMeta, ...] = (
    DocMeta("gl-pd-14-04a", "GL-PD-14-04A_ACU-Coat.pdf", "US Army (GL-PD)", "Ceket", "product_standard",
            aliases=("ceket", "acucoat", "gl-pd-14-04a"),),
    DocMeta("gl-pd-07-14a", "GL-PD-07-14A_Combat-Trousers.pdf", "US Army (GL-PD)", "Pantolon", "product_standard",
            aliases=("pantolon", "trouser", "gl-pd-07-14a"),),
    DocMeta("brother-s7300a", "Brother_S-7300A_Instruction.pdf", "Brother", "S-7300A düz dikiş makinesi", "machine_manual",
            aliases=("s7300a",)),
    DocMeta("brother-s7300b", "Brother_S-7300B_Instruction_2025-04.pdf", "Brother", "S-7300B düz dikiş makinesi", "machine_manual",
            aliases=("s7300b",)),
    DocMeta("strickland-1956", "Strickland_A-Tailoring-Manual_1956.pdf", "G. Strickland", "Terzilik kitabı", "tailoring_guide",
            aliases=("strickland", "terzilik")),
    DocMeta("mrcoffee-2003", "MrCoffee_Coffeemaker_2003.pdf", "Mr. Coffee", "Kahve makinesi", "machine_manual",
            aliases=("kahve", "mrcoffee", "coffee")),
    DocMeta("bosch-ra1171", "Bosch_RA1171_Operating-Safety_2005.pdf", "Bosch", "RA1171 freze tezgâhı", "machine_manual",
            lang_ranges=((2, 31, "en"), (32, 61, "fr"), (62, 96, "es")),
            aliases=("bosch", "freze", "ra1171")),
)

BY_ID = {d.doc_id: d for d in DOCS}

# Aynı üreticinin birden çok modeli olduğunda yalnızca marka adı geçerse tüm modelleri kapsar.
BRAND_ALIASES: dict[str, tuple[str, ...]] = {
    "brother": ("brother-s7300a", "brother-s7300b"),
}
