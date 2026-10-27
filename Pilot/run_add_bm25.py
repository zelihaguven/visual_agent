"""Mevcut indekse BM25 sparse vektörünü ekle (yeniden embed yok; vektörler ve payload kopyalanır).

Varsayılan sparse kol 2026-10-27'den beri bm25 (PILOT_SPARSE). Bu tarihten önce kurulmuş indeks yalnız bge-m3 sparse
taşır; arama 'Not existing vector name: bm25' hatası verir. Bir kez çalıştırın (arayüz kapalı, ~1 dk):
    python run_add_bm25.py                       # gömülü indeks (data/qdrant)
    $env:PILOT_QDRANT_URL="http://127.0.0.1:6333"; python run_add_bm25.py      # sunucudaki koleksiyon
"""
import logging
import time
import warnings

from pilot.config import COLLECTION, QDRANT_URL
from pilot.index import add_bm25

warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")

if __name__ == "__main__":
    t = time.time()
    n = add_bm25()
    logging.info("%s (%s): %d nokta, %.0f sn", COLLECTION, QDRANT_URL or "gömülü", n, time.time() - t)
