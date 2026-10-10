import time, warnings; warnings.filterwarnings("ignore")
import torch, torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS
dev = "mps" if torch.backends.mps.is_available() else "cpu"
t=time.time(); m = ChatterboxMultilingualTTS.from_pretrained(device=dev); print(f"yükleme ({dev}): {time.time()-t:.1f} sn")
txt = "Dış dikişlerde inç başına on ile on dört arası dikiş atılmalıdır."
for i in range(2):
    t=time.time(); w = m.generate(txt, language_id="tr"); dt=time.time()-t
    print(f"üretim {i+1}: {dt:.1f} sn, ses süresi {w.shape[-1]/m.sr:.1f} sn")
ta.save("tts_ornek.wav", w.cpu(), m.sr)
