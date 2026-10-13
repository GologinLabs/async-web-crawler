"""Run examples/minimal_sync.py and minimal_async.py and measure each run.

uv run python benchmarks/sync_vs_async.py

Pages/s is wall time over the 100 pages. Peak memory is RSS summed over the
process tree (Python, the Playwright driver, Chromium). Idle is the share of
wall time the Python process spent not on the CPU: waiting for pages.
"""
import json
import subprocess
import sys
import time

import psutil


def measure(cmd: list[str]) -> dict:
    t0 = time.monotonic()
    proc = psutil.Popen(cmd, stdout=subprocess.PIPE, text=True)
    peak, cpu = 0, 0.0
    while proc.poll() is None:
        try:
            tree = [proc, *proc.children(recursive=True)]
            peak = max(peak, sum(p.memory_info().rss for p in tree))
            t = proc.cpu_times()
            cpu = t.user + t.system  # the Python process only
        except psutil.Error:
            pass
        time.sleep(0.2)
    wall = time.monotonic() - t0
    pages = int(proc.stdout.read().split()[0])
    return {"pages": pages, "seconds": round(wall, 1),
            "pages_per_s": round(pages / wall, 2),
            "peak_mb": round(peak / 2**20),
            "idle_pct": round(100 * (1 - cpu / wall))}


for name, cmd in (("sync", [sys.executable, "examples/minimal_sync.py"]),
                  ("async", [sys.executable, "examples/minimal_async.py"])):
    print(json.dumps({"crawler": name, **measure(cmd)}), flush=True)
