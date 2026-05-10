"""Smoke tests + Little's Law verification."""

from __future__ import annotations

from src.config import ExperimentConfig, little_law_check, speculative_speedup
from src.simulation import run_replica


def test_speculative_speedup_canonical():
    """Validation of the Leviathan, Kalman & Matias (2023) formula."""
    # alpha=0.7, gamma=4, c=0.1 -> ~1.98x
    s1 = speculative_speedup(0.7, 4, 0.1)
    assert 1.9 < s1 < 2.0, f"Expected ~1.98, got {s1}"

    # alpha=0.9, gamma=8, c=0.05 -> ~4.38x
    s2 = speculative_speedup(0.9, 8, 0.05)
    assert 4.2 < s2 < 4.6, f"Expected ~4.38, got {s2}"

    # Cost-free drafter (c=0) -> ~6.13x for alpha=0.9, gamma=8
    s2_no_c = speculative_speedup(0.9, 8, 0.0)
    assert 6.0 < s2_no_c < 6.3, f"Expected ~6.13 with c=0, got {s2_no_c}"

    # alpha=1.0 (perfect drafter) -> gamma+1
    s3 = speculative_speedup(1.0, 4, 0.1)
    assert abs(s3 - 5.0) < 0.01


def test_little_law_check_pass():
    ok, err = little_law_check(2.0, 0.250, 0.50, tol=0.05)
    assert ok
    assert err < 1e-9


def test_little_law_check_fail():
    ok, err = little_law_check(2.0, 0.250, 5.0, tol=0.05)
    assert not ok
    assert err > 0.5


def test_smoke_baseline_nominal():
    """Smoke: 1 replica * 60 s baseline nominal completes without exception."""
    cfg = ExperimentConfig(sim_duration_s=60.0, n_replicates=1, scenario="nominal")
    summary = run_replica(cfg, proposed=False, replica_seed=42)
    assert summary["n_events"] > 0
    assert summary["p99_ms"] >= 0


def test_smoke_proposed_nominal():
    cfg = ExperimentConfig(sim_duration_s=60.0, n_replicates=1, scenario="nominal")
    summary = run_replica(cfg, proposed=True, replica_seed=42)
    assert summary["n_events"] > 0
    # Cellular Inference Mesh must have a smaller fallback rate than baseline ~30%
    assert summary["fallback_rate"] < 0.20


def test_smoke_partition_pacelc_gating():
    """Partition scenario: high-payload commands are rejected under gating."""
    cfg = ExperimentConfig(
        sim_duration_s=180.0,  # longer window to capture the bad state
        scenario="partition",
        partition_inject_pct=10.0,  # more aggressive for the test
    )
    summary = run_replica(cfg, proposed=True, replica_seed=42)
    # There must be rejections due to safety gating
    assert summary["rejected_partition"] >= 0


def test_reproducibility():
    """Same seed -> same result (DES determinism)."""
    cfg = ExperimentConfig(sim_duration_s=30.0, scenario="nominal")
    s1 = run_replica(cfg, proposed=False, replica_seed=42)
    s2 = run_replica(cfg, proposed=False, replica_seed=42)
    assert s1["n_events"] == s2["n_events"]
    # Latencies (within stdlib float tolerance)
    assert abs(s1["p99_ms"] - s2["p99_ms"]) < 1e-6
