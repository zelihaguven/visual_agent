"""CPU frekansı izleyicisi: her süre ölçümüne, o pencerede CPU'nun gerçek ortalama frekansı eklenir (ısınma/kısma testi).

psutil.cpu_freq() Windows'ta nominal taban frekansı döndürür (bu makinede sabit 1300 MHz). Gerçek frekans Windows
performans sayacından okunur: Processor Frequency (taban) × % Processor Performance / 100. İkisi de kaydedilir.
"""
import sys
import threading
import time
from bisect import bisect_left, bisect_right
from typing import Any

_PERF = r"\Processor Information(_Total)\% Processor Performance"
_BASE = r"\Processor Information(_Total)\Processor Frequency"


def window_mean(times: list[float], values: list[float], t0: float, t1: float) -> float | None:
    """[t0, t1] aralığındaki örneklerin ortalaması; aralıkta örnek yoksa t1'e en yakın önceki örnek."""
    lo, hi = bisect_left(times, t0), bisect_right(times, t1)
    if hi > lo:
        return sum(values[lo:hi]) / (hi - lo)
    return values[hi - 1] if hi > 0 else None


class CpuMonitor:
    def __init__(self, interval: float = 0.5) -> None:
        self.interval = interval
        self.times: list[float] = []
        self.mhz: list[float] = []          # gerçek (sayaç), yoksa psutil
        self.psutil_mhz: list[float] = []
        self.load: list[float] = []
        self.source = "psutil"
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "CpuMonitor":
        self.start()
        return self

    def __exit__(self, *_: Any) -> None:
        self.stop()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        import psutil
        pdh = query = perf = base = None
        if sys.platform == "win32":
            try:
                import win32pdh as pdh
                query = pdh.OpenQuery()
                perf, base = pdh.AddCounter(query, _PERF), pdh.AddCounter(query, _BASE)
                pdh.CollectQueryData(query)
                self.source = "pdh"
            except Exception:  # sayaç yoksa psutil ile sürer
                pdh = None
        psutil.cpu_percent()
        while not self._stop.wait(self.interval):
            ps = psutil.cpu_freq().current if psutil.cpu_freq() else float("nan")
            real = ps
            if pdh is not None:
                try:
                    pdh.CollectQueryData(query)
                    p = pdh.GetFormattedCounterValue(perf, pdh.PDH_FMT_DOUBLE)[1]
                    b = pdh.GetFormattedCounterValue(base, pdh.PDH_FMT_DOUBLE)[1]
                    real = b * p / 100
                except Exception:
                    pass
            self.times.append(time.perf_counter())
            self.mhz.append(real)
            self.psutil_mhz.append(ps)
            self.load.append(psutil.cpu_percent())
        if pdh is not None:
            pdh.CloseQuery(query)

    def window(self, t0: float, t1: float) -> dict[str, float | None]:
        return {"mhz": window_mean(self.times, self.mhz, t0, t1),
                "psutil_mhz": window_mean(self.times, self.psutil_mhz, t0, t1),
                "cpu_load": window_mean(self.times, self.load, t0, t1)}
