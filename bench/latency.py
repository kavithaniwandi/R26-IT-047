"""Benchmark severity and appeal inference latency.

Example:
    python bench/latency.py --requests 500 --concurrency 10
"""
from __future__ import annotations

import argparse
import platform
import statistics
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


VITALS_OK = {
    "vital_hr": 72,
    "vital_spo2": 98,
    "vital_sbp": 120,
    "vital_rr": 16,
    "vital_temp": 36.8,
    "pain_score": 1,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requests", default=500, type=int)
    parser.add_argument("--concurrency", default=10, type=int)
    return parser.parse_args()


def percentiles(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "p50_ms": ordered[int(0.50 * (len(ordered) - 1))],
        "p95_ms": ordered[int(0.95 * (len(ordered) - 1))],
        "p99_ms": ordered[int(0.99 * (len(ordered) - 1))],
    }


def timed(fn, count: int, concurrency: int) -> dict[str, float]:
    def one_call(_index: int) -> float:
        start = time.perf_counter()
        fn()
        return (time.perf_counter() - start) * 1000.0

    if concurrency <= 1:
        values = [one_call(i) for i in range(count)]
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            values = list(pool.map(one_call, range(count)))
    return {"mean_ms": statistics.mean(values), **percentiles(values)}


def main() -> None:
    args = parse_args()
    from app.models.nlp_service import _load_model
    from app.models.quality_service import get_quality_score
    from app.models.severity_service import classify_note

    nlp_start = time.perf_counter()
    _load_model()
    nlp_startup_ms = (time.perf_counter() - nlp_start) * 1000.0

    jobs = {
        "severity_ml": lambda: classify_note("Patient complains of chest pain", age=58, mode="ml", vitals=VITALS_OK, symptoms="Chest pain"),
        "severity_rule": lambda: classify_note("Patient complains of chest pain", age=58, mode="rule_based"),
        "appeal_scorer": lambda: get_quality_score("Please donate today to provide food and shelter for affected flood families.", "English"),
    }
    print(f"hardware={platform.platform()} python={platform.python_version()} nlp_startup_ms={nlp_startup_ms:.2f}")
    for concurrency in (1, args.concurrency):
        for name, fn in jobs.items():
            result = timed(fn, args.requests, concurrency)
            print(
                f"{name} concurrency={concurrency} requests={args.requests} "
                f"mean={result['mean_ms']:.2f} p50={result['p50_ms']:.2f} "
                f"p95={result['p95_ms']:.2f} p99={result['p99_ms']:.2f}"
            )


if __name__ == "__main__":
    main()
