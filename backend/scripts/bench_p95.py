"""Concurrent load harness for /v1/sts/respond.

Hits the running FastAPI server N times across M concurrent workers and
prints P50/P90/P95/P99 of end-to-end respond latency. Useful for
verifying NFR-01 (P95 ≤ 2.5s) per requirements/mvp_requirements.md.

Usage:
  python scripts/bench_p95.py                       # 100 reqs / 10 concurrent / localhost
  python scripts/bench_p95.py --requests 500 --concurrency 20
  python scripts/bench_p95.py --url https://staging.example.com

Each request opens a fresh session, so concurrency=N approximates N
distinct concurrent users.
"""
from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time

import httpx


async def one_request(client: httpx.AsyncClient, base_url: str, idx: int) -> float | None:
    try:
        start_res = await client.post(
            f"{base_url}/v1/sts/session/start", json={"age_group": "10-12"}
        )
        start_res.raise_for_status()
        session_id = start_res.json()["session_id"]

        started = time.perf_counter()
        res = await client.post(
            f"{base_url}/v1/sts/respond",
            json={"session_id": session_id, "text": f"안녕, 질문 {idx}"},
        )
        res.raise_for_status()
        return (time.perf_counter() - started) * 1000
    except Exception as err:
        print(f"  req {idx} failed: {err!r}", file=sys.stderr)
        return None


async def run(base_url: str, total: int, concurrency: int) -> list[float]:
    sem = asyncio.Semaphore(concurrency)
    timings: list[float] = []

    async with httpx.AsyncClient(timeout=30.0) as client:

        async def task(idx: int) -> None:
            async with sem:
                t = await one_request(client, base_url, idx)
                if t is not None:
                    timings.append(t)

        await asyncio.gather(*(task(i) for i in range(total)))

    return timings


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    k = (len(sorted_values) - 1) * pct
    f = int(k)
    c = min(f + 1, len(sorted_values) - 1)
    if f == c:
        return sorted_values[f]
    return sorted_values[f] + (sorted_values[c] - sorted_values[f]) * (k - f)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    print(
        f"Sending {args.requests} requests, concurrency={args.concurrency}, url={args.url}"
    )
    started = time.perf_counter()
    timings = asyncio.run(run(args.url, args.requests, args.concurrency))
    elapsed = time.perf_counter() - started

    if not timings:
        print("No successful requests.")
        sys.exit(1)

    print(
        f"Completed {len(timings)}/{args.requests} reqs in {elapsed:.2f}s "
        f"({len(timings) / elapsed:.1f} req/s)"
    )
    print(f"  min   = {min(timings):.1f} ms")
    print(f"  p50   = {percentile(timings, 0.50):.1f} ms")
    print(f"  p90   = {percentile(timings, 0.90):.1f} ms")
    print(f"  p95   = {percentile(timings, 0.95):.1f} ms")
    print(f"  p99   = {percentile(timings, 0.99):.1f} ms")
    print(f"  mean  = {statistics.mean(timings):.1f} ms")
    print(f"  max   = {max(timings):.1f} ms")

    p95 = percentile(timings, 0.95)
    target = 2500.0
    if p95 <= target:
        print(f"\nP95 {p95:.0f}ms <= target {target:.0f}ms ✓ (NFR-01)")
    else:
        print(f"\nP95 {p95:.0f}ms > target {target:.0f}ms ✗ (NFR-01)")
        sys.exit(2)


if __name__ == "__main__":
    main()
