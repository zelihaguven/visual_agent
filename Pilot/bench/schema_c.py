"""Ölçüm araçları için: şema C uygulamaya taşındı (pilot/schema_c.py, Adım 2 planı §29). Bu ad aynı modülü gösterir."""
import sys

from pilot import schema_c as _schema_c

sys.modules[__name__] = _schema_c
