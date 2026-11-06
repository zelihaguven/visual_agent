import os

import pytest  # noqa: F401

# Testler model ve ağ çağırmaz (taklit); bench paketi kipin açıkça verilmesini ister (bench/__init__.py).
# c kipinin testleri kipi kendi fikstürleriyle açar.
os.environ.setdefault("PILOT_ANSWER_MODE", "bugun")
