import time, warnings; warnings.filterwarnings("ignore")
import torch
dev = "mps" if torch.backends.mps.is_available() else "cpu"
from FlagEmbedding import BGEM3FlagModel, FlagReranker
t=time.time(); m = BGEM3FlagModel("BAAI/bge-m3", use_fp16=False, devices=["cpu"]); print(f"bge-m3 yükleme: {time.time()-t:.1f} sn")
q = "Ceketin dış dikişlerinde inç başına kaç dikiş olmalı?"
docs = ["The seams for all outside visible stitching shall be sewn with 10-14 stitches per inch.",
        "Upper thread is not tight. Adjust the lower thread tension.",
        "The coffeemaker must be cleaned monthly with vinegar."]
t=time.time(); o = m.encode([q]+docs, return_dense=True, return_sparse=True, batch_size=4); print(f"embed 4 metin: {time.time()-t:.2f} sn")
import numpy as np
d=o["dense_vecs"]; print("dense benzerlik:", [round(float(d[0]@d[i]),3) for i in range(1,4)], "boyut", d.shape[1])
print("sparse örnek terim sayısı:", len(o["lexical_weights"][1]))
r = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=False, devices=["cpu"])
t=time.time(); s = r.compute_score([[q,x] for x in docs]); print(f"rerank 3 çift: {time.time()-t:.2f} sn", [round(float(x),2) for x in s])
