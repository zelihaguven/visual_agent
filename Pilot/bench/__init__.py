"""Arama katmanı benchmark'ı (BENCHMARK-RAPORU.md). Pilotun varsayılan davranışını değiştirmez.

Cevap hattı kipi AÇIKÇA verilmeli (karar 2026-11-06): PILOT_ANSWER_MODE = c | bugun. Verilmezse araç durur; sessiz
varsayılan yok (uygulamanın varsayılanı c, ölçüm araçlarının çoğu bugun ister, karışırsa ölçüm yanlış hatta yapılır).
  bugun  pipeline'ın model kancasını (pipeline.chat_json) kendisi dolduran ölçüm araçları: answer_models, hat_olcumu,
         adim2_analiz, clarify_model, doc_rules_diff, schema_overhead (kendi şemalarını uygular)
  c      uygulamanın c yolunu ölçenler: duman_testi, arayuz_duman
Yalnız arama ölçen araçlar cevap hattına dokunmaz; kip yine açıkça verilir (koşu betikleri bugun yazar).
"""
import os

MODES = ("c", "bugun")


def _mode() -> str:
    m = os.environ.get("PILOT_ANSWER_MODE")
    if m not in MODES:
        raise SystemExit("PILOT_ANSWER_MODE açıkça verilmeli (c | bugun). Ölçüm araçlarında varsayılan yok "
                         "(bench/__init__.py). Örnek: $env:PILOT_ANSWER_MODE = \"bugun\"")
    return m


MODE = _mode()


def require_mode(expected: str) -> None:
    """Araç yalnız bu kipte doğru ölçer; başka kipte durur."""
    if MODE != expected:
        raise SystemExit(f"Bu araç PILOT_ANSWER_MODE={expected} ister (verilen: {MODE}).")
