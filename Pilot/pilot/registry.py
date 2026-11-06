"""Pilot doküman kaydı (metadata). Kaynak: docs/arsiv/calisma-notlari/notlar/manual-envanteri.md."""
from dataclasses import dataclass
from pathlib import Path

from . import config
from .config import MANUALS_DIR


@dataclass(frozen=True)
class DocMeta:
    doc_id: str
    file: str
    brand: str
    product: str
    doc_type: str                              # product_standard | machine_manual | tailoring_guide | repair_guide
    default_lang: str = "en"
    lang_ranges: tuple[tuple[int, int, str], ...] = ()   # (ilk_sayfa, son_sayfa, dil)
    # Belgenin kendi başlığı (genelde İngilizce) ve varsa yazarı: metadata, kural değil (karar 2026-11-06). Yüklemede ilk
    # sayfadan önerilir, yetkili onaylar. Elle yazılmış takma ad listesi (aliases) silindi.
    title: str = ""
    author: str = ""
    # Bu dokümanı görebilecek departman/yetki grupları. "all": herkes. Parçaların payload'ına yazılır; arama
    # access verilirse Qdrant filtresinin içinde uygulanır (retrieve.search), yetkisiz parça sonuçlara hiç girmez.
    access: tuple[str, ...] = ("all",)

    @property
    def source_path(self) -> Path:
        """Yüklenen özgün dosya (metin katmanı kontrolü ve OCR bunun üzerinde)."""
        return MANUALS_DIR / self.file

    @property
    def ocr_path(self) -> Path:
        return config.OCR_DIR / f"{self.doc_id}.pdf"

    @property
    def path(self) -> Path:
        """Ayrıştırma, şekil ve sayfa görüntüsünün okuduğu dosya: OCR uygulanmışsa OCR'lı PDF (pilot/ocr.py), değilse
        özgün dosya. Sayfa sayısı ve sırası ikisinde aynı."""
        if config.OCR_ENABLED and self.ocr_path.exists():
            return self.ocr_path
        return self.source_path

    def lang_of(self, page: int) -> str:
        for first, last, lang in self.lang_ranges:
            if first <= page <= last:
                return lang
        return self.default_lang


DOCS: tuple[DocMeta, ...] = (
    DocMeta("gl-pd-14-04a", "GL-PD-14-04A_ACU-Coat.pdf", "US Army (GL-PD)", "Ceket", "product_standard", title="COAT, ARMY COMBAT UNIFORM"),
    DocMeta("gl-pd-07-14a", "GL-PD-07-14A_Combat-Trousers.pdf", "US Army (GL-PD)", "Pantolon", "product_standard", title="TROUSERS, ARMY COMBAT UNIFORM"),
    DocMeta("brother-s7300a", "Brother_S-7300A_Instruction.pdf", "Brother", "S-7300A düz dikiş makinesi", "machine_manual", title="Single Needle Direct Drive Lock Stitcher with Electronic Feeding System and Thread Trimmer, Instruction Manual"),
    DocMeta("brother-s7300b", "Brother_S-7300B_Instruction_2025-04.pdf", "Brother", "S-7300B düz dikiş makinesi", "machine_manual", title="Single Needle Direct Drive Lock Stitcher with Electronic Feeding System and Thread Trimmer, Instruction Manual"),
    DocMeta("strickland-1956", "Strickland_A-Tailoring-Manual_1956.pdf", "G. Strickland", "Terzilik kitabı", "tailoring_guide", title="A Tailoring Manual", author="Gertrude Strickland"),
    # Genel başvuru kitabı (eğirme, dokuma, örme makineleri): tür query.MUST_MATCH'te yok, hiçbir varlık engellemez.
    DocMeta("granovsky-1986", "Granovsky_Repair-Adjustment-Textile-Machines_1986.pdf", "T. Granovsky (Mir)",
            "Tekstil makineleri onarım ve ayar kitabı", "repair_guide", title="Repair and Adjustment of Textile Machines (Spinning and Weaving Equipment)", author="T. Granovsky"),
    # Görülmemiş doküman testi (2026-10-16): yalnız yükleyicinin gireceği kayıt; sözlük ve kural eklenmedi.
    # Kaynak: juki.co.jp, MO-6800S(D)/DD10 English instruction manual (instruction_eg.pdf)
    DocMeta("juki-mo6800s", "JUKI_MO-6800S_Instruction_EN.pdf", "JUKI", "MO-6800S overlok makinesi", "machine_manual", title="MO-6800S(D)/DD10 Series Instruction Manual"),
    DocMeta("mrcoffee-2003", "MrCoffee_Coffeemaker_2003.pdf", "Mr. Coffee", "Kahve makinesi", "machine_manual", title="Mr. Coffee Coffeemaker Instructions"),
    DocMeta("bosch-ra1171", "Bosch_RA1171_Operating-Safety_2005.pdf", "Bosch", "RA1171 freze tezgâhı", "machine_manual",
            lang_ranges=((2, 31, "en"), (32, 61, "fr"), (62, 96, "es")), title="RA1171 Operating/Safety Instructions"),
)

BY_ID = {d.doc_id: d for d in DOCS}


def product_names(doc: DocMeta) -> tuple[str, ...]:
    """Belgenin sorudaki adları, yalnız belge kaydının alanlarından (elle yazılmış takma ad yok; karar 2026-11-06):
    ürün adının tamamı, ürün adındaki model kodları (rakam içeren kelimeler: "S-7300A", "RA1171"), belgenin
    başlığı, yazarın soyadı ve doküman kimliği. Küçük harf; '-', '.', boşluk eşleştirmede yok sayılır (query._squash)."""
    codes = [w for w in doc.product.split() if any(ch.isdigit() for ch in w)]
    surname = doc.author.split()[-1] if doc.author.split() else ""
    names = [doc.product, *codes, doc.title, surname if len(surname) >= 4 else "", doc.doc_id]
    return tuple(dict.fromkeys(n.casefold() for n in names if n))



def visible(doc_id: str, groups: list[str] | None) -> bool:
    """groups None: yetki kontrolü yok (pilotun varsayılanı). Aksi halde doküman 'all' ya da gruplardan biri için açık."""
    if groups is None:
        return True
    access = BY_ID[doc_id].access if doc_id in BY_ID else ()
    return "all" in access or bool(set(access) & set(groups))
