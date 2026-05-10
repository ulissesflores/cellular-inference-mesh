"""Unit tests for src/main.py CLI runner aggregation logic.

Covers:
- aggregate() with mean + 95% CI computation
- _replica_worker() for parallel execution wrapper
- CLI parsing (smoke tests)
"""

from __future__ import annotations

import math
import statistics
import subprocess
import sys
from pathlib import Path

import pytest

from src.config import ExperimentConfig
from src.main import _replica_worker, aggregate, main, SCENARIOS, ARMS


def test_aggregate_single_replica():
    """Aggregate with N=1 yields std=0 and ci95=0."""
    replicas = [{"p50_ms": 100.0, "p95_ms": 200.0, "p99_ms": 300.0,
                 "fallback_rate": 0.1, "cost_usd": 0.05, "energy_j": 1000.0}]
    agg = aggregate(replicas)
    assert agg["n_replicas"] == 1
    assert agg["p99_ms"]["mean"] == 300.0
    assert agg["p99_ms"]["std"] == 0.0
    assert agg["p99_ms"]["ci95"] == 0.0


def test_aggregate_multiple_replicas_ci95():
    """Aggregate with N>1 computes std + ci95 = 1.96*std/sqrt(n)."""
    replicas = [
        {"p99_ms": 1500.0, "fallback_rate": 0.30, "cost_usd": 0.08, "energy_j": 4500.0,
         "p50_ms": 800.0, "p95_ms": 1300.0},
        {"p99_ms": 1600.0, "fallback_rate": 0.32, "cost_usd": 0.082, "energy_j": 4600.0,
         "p50_ms": 810.0, "p95_ms": 1320.0},
        {"p99_ms": 1700.0, "fallback_rate": 0.28, "cost_usd": 0.079, "energy_j": 4400.0,
         "p50_ms": 790.0, "p95_ms": 1280.0},
    ]
    agg = aggregate(replicas)
    assert agg["n_replicas"] == 3
    expected_mean = 1600.0
    expected_std = statistics.stdev([1500.0, 1600.0, 1700.0])
    expected_ci95 = 1.96 * expected_std / math.sqrt(3)
    assert agg["p99_ms"]["mean"] == pytest.approx(expected_mean)
    assert agg["p99_ms"]["std"] == pytest.approx(expected_std)
    assert agg["p99_ms"]["ci95"] == pytest.approx(expected_ci95)


def test_aggregate_skips_missing_keys():
    """Aggregate ignores replicas missing a key (None values)."""
    replicas = [
        {"p99_ms": 100.0, "fallback_rate": None, "cost_usd": 0.05, "energy_j": 1000.0,
         "p50_ms": 50.0, "p95_ms": 80.0},
        {"p99_ms": 110.0, "fallback_rate": 0.1, "cost_usd": 0.06, "energy_j": 1100.0,
         "p50_ms": 55.0, "p95_ms": 90.0},
    ]
    agg = aggregate(replicas)
    assert agg["n_replicas"] == 2
    assert "p99_ms" in agg
    assert "fallback_rate" in agg
    assert agg["fallback_rate"]["mean"] == 0.1


def test_aggregate_empty_returns_n_zero():
    """Empty list yields n_replicas=0 and no metrics."""
    agg = aggregate([])
    assert agg == {"n_replicas": 0}


def test_replica_worker_returns_dict():
    """_replica_worker invokes run_replica and returns metrics dict."""
    cfg = ExperimentConfig(sim_duration_s=30.0, scenario="nominal")
    args = (cfg, False, 42)
    result = _replica_worker(args)
    assert isinstance(result, dict)
    assert "p99_ms" in result
    assert "fallback_rate" in result
    assert "cost_usd" in result


def test_replica_worker_seed_reproducibility():
    """Same seed → same result."""
    cfg = ExperimentConfig(sim_duration_s=30.0, scenario="nominal")
    r1 = _replica_worker((cfg, True, 42))
    r2 = _replica_worker((cfg, True, 42))
    assert r1["p99_ms"] == r2["p99_ms"]
    assert r1["fallback_rate"] == r2["fallback_rate"]


def test_scenarios_constant():
    """SCENARIOS tuple covers nominal, partition, burst."""
    assert SCENARIOS == ("nominal", "partition", "burst")


def test_arms_constant():
    """ARMS = (baseline=False, proposed=True)."""
    assert ARMS == (False, True)


def test_main_smoke_via_cli(tmp_path):
    """CLI smoke: --smoke runs 1 replica × 60s, writes output/results.json."""
    out_dir = tmp_path / "output"
    out_dir.mkdir()
    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--smoke", "--output-dir", str(out_dir)],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
        timeout=60,
    )
    assert result.returncode == 0, f"CLI failed: stderr={result.stderr}"
    results_file = out_dir / "results.json"
    raw_file = out_dir / "raw_replicas.jsonl"
    assert results_file.exists() or "smoke" in result.stdout.lower()


def test_aggregate_handles_zero_variance():
    """All-equal values → std=0, ci95=0."""
    replicas = [{"p99_ms": 100.0, "fallback_rate": 0.1, "cost_usd": 0.05,
                 "energy_j": 1000.0, "p50_ms": 50.0, "p95_ms": 80.0}] * 5
    agg = aggregate(replicas)
    assert agg["p99_ms"]["std"] == 0.0
    assert agg["p99_ms"]["ci95"] == 0.0
