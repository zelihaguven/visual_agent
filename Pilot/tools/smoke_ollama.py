import time, ollama
t=time.time()
r = ollama.chat(model="qwen3:30b-a3b-instruct-2507-q4_K_M",
    messages=[{"role":"user","content":"Dikişte SPI nedir? Tek cümleyle Türkçe açıkla."}],
    options={"num_predict":80,"temperature":0})
print(r["message"]["content"]); print(f"süre: {time.time()-t:.1f} sn, ilk yükleme dahil; eval_count={r['eval_count']}, tok/sn={r['eval_count']/(r['eval_duration']/1e9):.1f}")
