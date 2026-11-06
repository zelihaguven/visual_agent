"""Arama katmanı benchmark'ı (BENCHMARK-RAPORU.md). Pilotun varsayılan davranışını değiştirmez.

Ölçüm araçları pipeline'ın model kancasını (pipeline.chat_json) kendileri doldurur ve kendi şemalarını uygular
(answer_models, hat_olcumu, adim2_analiz, doc_rules_diff ...). Uygulamanın varsayılanı c kipi olduğundan (Adım 2
planı §29, 2026-11-06), ortam değişkeni verilmemişse bu paket içindeki hat "bugun" kipindedir. Uygulamanın c yolunu
ölçen araçlar (duman_testi, arayuz_duman) c kipini kendileri açıkça seçer.
"""
import os

os.environ.setdefault("PILOT_ANSWER_MODE", "bugun")
