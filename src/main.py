"""CLI runner: 3 scenarios x N Monte-Carlo replicates x {baseline, proposed}.

Usage:
    python -m src.main --replicates 30 --duration 1800 --output-dir output/

Writes ``output/results.json`` with aggregated summary and
``output/raw_replicas.jsonl`` with each replica's raw data.

Reproducibility: canonical run is ``seed=42`` with 30 replicates of 1800 s
simulated time across 3 scenarios (nominal, partition, burst) and 2 arms
(baseline, proposed) — matching ``experiment_provenance.json``.

Author: Carlos Ulisses Flores <c.ulisses@gmail.com>
License: Apache-2.0
"""

from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import statistics
import time
from pathlib import Path
from typing import Any

from .config import ExperimentConfig
from .simulation import run_replica

SCENARIOS = ("nominal", "partition", "burst")
ARMS = (False, True)  # baseline, proposed


def _replica_worker(args: tuple[ExperimentConfig, bool, int]) -> dict[str, Any]:
    cfg, proposed, replica_seed = args
    return run_replica(cfg, proposed, replica_seed)


def aggregate(replicas: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate N replicates: mean + 95% confidence interval over key metrics.

    Args:
        replicas: List of per-replica result dicts produced by ``run_replica``.

    Returns:
        Dict with ``n_replicas`` and per-metric aggregates (mean, std, ci95).
    """
    keys = ("p50_ms", "p95_ms", "p99_ms", "fallback_rate", "cost_usd", "energy_j")
    agg: dict[str, Any] = {"n_replicas": len(replicas)}
    for k in keys:
        vals = [r[k] for r in replicas if r.get(k) is not None]
        if not vals:
            continue
        mean = statistics.mean(vals)
        std = statistics.stdev(vals) if len(vals) > 1 else 0.0
        ci95 = 1.96 * std / math.sqrt(len(vals)) if len(vals) > 1 else 0.0
        agg[k] = {"mean": mean, "std": std, "ci95": ci95}
    return agg


def main():
    parser = argparse.ArgumentParser(
        description="Cellular Inference Mesh DES runner (Salabim)"
    )
    parser.add_argument("--replicates", type=int, default=100)
    parser.add_argument("--duration", type=float, default=3600.0)
    parser.add_argument(
        "--scenarios", nargs="+", default=list(SCENARIOS), choices=list(SCENARIOS)
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path(__file__).parent.parent / "output"
    )
    parser.add_argument("--workers", type=int, default=max(1, mp.cpu_count() - 1))
    parser.add_argument("--smoke", action="store_true", help="1 replica * 60 s")
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    if args.smoke:
        args.replicates = 1
        args.duration = 60.0

    t0 = time.time()
    raw_path = args.output_dir / "raw_replicas.jsonl"
    results_path = args.output_dir / "results.json"

    all_results: dict[str, Any] = {"raw": {}, "aggregated": {}}

    with raw_path.open("w") as raw_f:
        for scenario in args.scenarios:
            for proposed in ARMS:
                arm = "proposed" if proposed else "baseline"
                key = f"{arm}__{scenario}"
                print(
                    f"[{time.time() - t0:6.1f}s] Running {key} "
                    f"({args.replicates} replicas × {args.duration:.0f}s)"
                )
                tasks = [
                    (
                        ExperimentConfig(
                            scenario=scenario,
                            sim_duration_s=args.duration,
                            seed=42 + i,
                        ),
                        proposed,
                        42 + i,
                    )
                    for i in range(args.replicates)
                ]

                if args.workers > 1 and args.replicates > 4:
                    with mp.Pool(args.workers) as pool:
                        replicas = pool.map(_replica_worker, tasks)
                else:
                    replicas = [_replica_worker(t) for t in tasks]

                for r in replicas:
                    raw_f.write(json.dumps({"key": key, **r}) + "\n")

                all_results["raw"][key] = replicas
                all_results["aggregated"][key] = aggregate(replicas)

    with results_path.open("w") as f:
        json.dump(all_results["aggregated"], f, indent=2)

    print(f"\n[{time.time() - t0:6.1f}s] Done. Wrote {raw_path} and {results_path}.")
    print("\nSummary:")
    for key, agg in all_results["aggregated"].items():
        p99 = agg.get("p99_ms", {}).get("mean", 0.0)
        fb = agg.get("fallback_rate", {}).get("mean", 0.0)
        cost = agg.get("cost_usd", {}).get("mean", 0.0)
        print(f"  {key:30s}  p99={p99:7.1f} ms  fallback={fb*100:5.2f}%  cost=${cost:7.4f}")


if __name__ == "__main__":
    main()
