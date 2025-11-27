#!/usr/bin/env python3
"""Runner de benchmark: tenta usar pyo3 (módulo `rustlib`) ou carregar .so via ctypes.

Gera `results.csv` com colunas: mode,size,repeat,elapsed_seconds
"""

import csv
import os
import time
from statistics import mean

import numpy as np


RESULTS_CSV = os.path.join(os.path.dirname(__file__), "results.csv")


def load_rust_module():
    """Tenta importar `rustlib` (pyo3) ou carregar `librustlib.so` via ctypes.
    Retorna (mode, call_fn).
    """
    try:
        import rustlib  # type: ignore

        def call(data: np.ndarray):
            return rustlib.compute(data.tolist())

        return "pyo3", call
    except Exception:
        pass

    # tentativa via ctypes
    try:
        from ctypes import CDLL, c_float, c_int, POINTER

        lib_paths = [
            os.path.join(os.getcwd(), "target", "release", "librustlib.so"),
            os.path.join(os.getcwd(), "librustlib.so"),
        ]
        for p in lib_paths:
            if os.path.exists(p):
                lib = CDLL(p)
                lib.compute.argtypes = [POINTER(c_float), c_int]
                lib.compute.restype = c_float

                def call(data: np.ndarray):
                    arr = (c_float * len(data))(*data.astype(np.float32).tolist())
                    return lib.compute(arr, len(data))

                return "ctypes", call
    except Exception:
        pass

    raise RuntimeError("Nenhum módulo Rust encontrado. Compile o crate com maturin ou cargo build --release.")


def bench_call(call_fn, data_sizes, repeats=5):
    rows = []
    for size in data_sizes:
        data = np.random.rand(size).astype(np.float32)
        # warmup
        call_fn(data)
        for r in range(1, repeats + 1):
            t0 = time.perf_counter()
            call_fn(data)
            t1 = time.perf_counter()
            rows.append((size, r, t1 - t0))
    return rows


def main():
    data_sizes = [1_000, 100_000, 1_000_000]
    repeats = 5

    mode, call_fn = load_rust_module()
    print(f"Modo: {mode}")

    rows = bench_call(call_fn, data_sizes, repeats=repeats)

    os.makedirs(os.path.dirname(RESULTS_CSV), exist_ok=True)
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mode", "size", "repeat", "elapsed_seconds"])
        for size, r, elapsed in rows:
            w.writerow([mode, size, r, f"{elapsed:.6f}"])

    # resumo
    by_size = {}
    for size, r, elapsed in rows:
        by_size.setdefault(size, []).append(elapsed)

    print("Resumo:")
    for size, times in sorted(by_size.items()):
        print(f"size={size} avg={mean(times):.6f}s median={np.median(times):.6f}s")


if __name__ == "__main__":
    main()
