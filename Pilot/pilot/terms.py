"""Atölye terim sözlüğü: Türkçe atölye terimi -> kılavuzlardaki İngilizce terim (R16).

Neden sözlük? Pilot deneyinde (PILOT-RAPORU §16.2) bge-m3 beş atölye teriminin 1'ini, qwen2.5:7b 0'ını
doğru eşledi ("dizlik = bobbin", "çağanoz = flywheel"). Kendinden emin yanlış çeviri aramayı sessizce yanlış
sayfaya götürür. Sözlük deterministik ve denetlenebilirdir.

Kullanım: Yalnızca ARAMA için soruya kılavuz terimi eklenir (sorgu genişletme). Modele giden soru değişmez.

DURUM: Taslak. Terimler pilot test kılavuzlarından (Brother S-7300A/B, GL-PD şartnameleri) derlendi,
uzman (usta / kalite) onayı bekliyor. Yeni terimi LLM önerebilir, uzman onaylamadan buraya eklenmez.
"""
import re

# Uzun ifadeler önce eşleşsin diye sıralama önemli değil: her terim bağımsız aranır.
GLOSSARY: dict[str, str] = {
    "çağanoz": "rotary hook",
    "masura kovanı": "bobbin case",
    "masura": "bobbin",
    "baskı ayağı": "presser foot",
    "dizlik": "knee lifter",
    "transportör": "feed dog",
    "iplik gerginliği": "thread tension",
    "üst iplik": "upper thread",
    "alt iplik": "lower thread",
    "iğne mili": "needle bar",
    "dikiş uzunluğu": "stitch length",
    "dikiş adımı": "stitch pitch",
    "geri dikiş": "backtack",
    "punteriz": "backtack",
    "dikiş atlıyor": "skipped stitches",
    "dikiş atlama": "skipped stitches",
    "iplik kopuyor": "thread breakage",
    "iplik kopması": "thread breakage",
    "yağlama": "lubrication",
    "dikiş hızı": "sewing speed",
    "ilik": "buttonhole",
    "kuşgözü": "eyelet",
    "overlok": "overedge",
    "inç başına dikiş": "stitches per inch",
    "dış görünür dikiş": "outside visible stitching",
    # Kılavuz bölüm başlıkları işlem adıyla başlıyor ("4-4. Installing the bobbin case"). Fiil eşlenmeyince
    # "masura kovanı nasıl takılır?" sorusunda alt iplik gerginliği parçası takma bölümünün önüne geçiyordu.
    # Kök eşleşir ("takıl" → takılır, takılması). "tak" kullanılmaz: "takım" kelimesini de yakalar.
    "takıl": "installing",
    "takma": "installing",
    "sökül": "removing",
    "sökme": "removing",
}

_TR_LOWER = str.maketrans({"I": "ı", "İ": "i"})


def _norm(text: str) -> str:
    return text.translate(_TR_LOWER).lower()


def expand_query(question: str) -> tuple[str, list[str]]:
    """Soruda geçen atölye terimlerinin kılavuz karşılıklarını soruya ekler.

    Terim kelime başında eşleşir, sonuna Türkçe ek gelebilir ("çağanozu", "masuranın").
    Dönüş: (genişletilmiş soru, eklenen terimler).
    """
    q = _norm(question)
    added = []
    for tr, en in GLOSSARY.items():
        if re.search(rf"(?<!\w){re.escape(tr)}", q) and en.lower() not in q and en not in added:
            added.append(en)
    if not added:
        return question, []
    return f"{question} ({', '.join(added)})", added
