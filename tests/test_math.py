"""Isolated math tests — validations of canonical formulas.

These tests do not depend on simulation.py or Salabim. They validate:
- Speculative-decoding speedup (Leviathan, Kalman & Matias, ICML 2023)
- Little's Law (Little, 1961)
- KV-cache multiplicative composition (DeepSeek-V3 + Brandon CLA + Beltagy)
- Combinatorial blast radius (MacCárthaigh, 2019)
"""

from __future__ import annotations

import math

from src.config import (
    ExperimentConfig,
    little_law_check,
    speculative_speedup,
)


# ---------- Speculative decoding (Leviathan, Kalman & Matias 2023) ----------

def test_speculative_speedup_alpha_07_gamma_4_c_01():
    """Conservative case: alpha=0.7, gamma=4, c=0.1 -> ~1.98x."""
    s = speculative_speedup(0.7, 4, 0.1)
    assert 1.9 < s < 2.0, f"Expected ~1.98, got {s}"


def test_speculative_speedup_alpha_09_gamma_8_c_005():
    """Aggressive case: alpha=0.9, gamma=8, c=0.05 -> ~4.38x."""
    s = speculative_speedup(0.9, 8, 0.05)
    assert 4.2 < s < 4.6, f"Expected ~4.38, got {s}"


def test_speculative_speedup_limit_c_zero():
    """Theoretical limit c -> 0 (cost-free drafter): alpha=0.9, gamma=8 -> ~6.13x."""
    s = speculative_speedup(0.9, 8, 0.0)
    assert 6.0 < s < 6.3, f"Expected ~6.13 with c=0, got {s}"


def test_speculative_speedup_perfect_drafter():
    """alpha=1.0 (perfect drafter) -> speedup = gamma+1."""
    s = speculative_speedup(1.0, 4, 0.1)
    assert abs(s - 5.0) < 0.01


# ---------- Little's Law (Little 1961) ----------

def test_little_law_validation_pass():
    """lambda=2.0 ev/s * W=0.250 s -> L = 0.500. Tolerance 5%."""
    ok, err = little_law_check(2.0, 0.250, 0.50, tol=0.05)
    assert ok
    assert err < 1e-9


def test_little_law_validation_fail():
    """Observed L far from expected -> reject."""
    ok, err = little_law_check(2.0, 0.250, 5.0, tol=0.05)
    assert not ok
    assert err > 0.5


def test_little_law_typical_addverb_load():
    """Typical Addverb load: lambda=2 ev/s/AGV * 10 AGVs * W=0.250 s -> L~5.0."""
    lambda_total = 2.0 * 10  # 10 AGVs
    w = 0.250
    expected_l = 5.0
    ok, err = little_law_check(lambda_total, w, expected_l, tol=0.05)
    assert ok, f"Expected L=5.0 with err<5%, got err={err}"


# ---------- KV-cache multiplicative composition ----------

def test_kv_cache_baseline_mha():
    """Llama 3 8B in Multi-Head Attention BF16 with 8K tokens ~ 134 MB."""
    cfg = ExperimentConfig()
    assert cfg.kv_cache_mb_baseline_mha == 134.0


def test_kv_cache_proposed_full_composition():
    """MLA + Sliding 4K + CLA-2 reaches ~38x reduction (composed)."""
    cfg = ExperimentConfig()
    reduction_factor = cfg.kv_cache_mb_baseline_mha / cfg.kv_cache_mb_proposed_full
    # Expect reduction in [30, 45]: nominal MLA ~10x * Sliding 2x * CLA-2 2x ~ 40x
    assert 30 < reduction_factor < 45, (
        f"Expected MLA+Sliding+CLA-2 reduction ~38x, got {reduction_factor:.1f}x"
    )


def test_kv_cache_mla_only_intermediate():
    """MLA alone reaches ~10x reduction."""
    cfg = ExperimentConfig()
    reduction_mla_only = cfg.kv_cache_mb_baseline_mha / cfg.kv_cache_mb_proposed_mla_only
    assert 9 < reduction_mla_only < 11, (
        f"Expected MLA-only reduction ~10x, got {reduction_mla_only:.1f}x"
    )


# ---------- Combinatorial blast radius (MacCarthaigh, AWS Builders' Library) ----------

def test_blast_radius_combinatorial_m8_k2():
    """For M=8 servers and k=2 replicas, simultaneous failure of 2 servers affects:
    P = C(2,2)/C(8,2) = 1/28 ~ 3.57%."""
    M, k, f = 8, 2, 2
    prob_affected = math.comb(f, k) / math.comb(M, k)
    assert abs(prob_affected - 1.0 / 28.0) < 1e-9
    assert 0.030 < prob_affected < 0.040


def test_blast_radius_scales_inversely_with_M():
    """With M=16 (k=2), blast radius drops to ~0.83%."""
    M, k, f = 16, 2, 2
    prob_affected = math.comb(f, k) / math.comb(M, k)
    # 1/120 ~ 0.833%
    assert 0.005 < prob_affected < 0.010


def test_blast_radius_naive_no_shuffle():
    """Without shuffle, 2 adjacent replicas -> 2/8 = 25% blast radius (naive baseline)."""
    naive = 2 / 8
    assert naive == 0.25


# ---------- Roofline / Bandwidth-Delay Product ----------

def test_bdp_industrial_uplink():
    """Industrial BDP: 100 Mbps * RTT 80 ms = 1.0 MB.
    Critical: 134 MB of MHA KV cache is NOT transferable cross-WAN without MLA."""
    bw_mbps = 100
    rtt_ms = 80
    bdp_bytes = (bw_mbps * 1e6 / 8) * (rtt_ms / 1000)
    bdp_mb = bdp_bytes / 1e6
    assert abs(bdp_mb - 1.0) < 1e-9


def test_kv_baseline_exceeds_bdp_two_orders():
    """KV MHA 134 MB > BDP 1 MB by two orders of magnitude -> MLA/CLA are mandatory."""
    cfg = ExperimentConfig()
    bdp_mb = 1.0  # from test_bdp_industrial_uplink
    ratio = cfg.kv_cache_mb_baseline_mha / bdp_mb
    assert 100 < ratio < 200  # ~134x > BDP


def test_roofline_ddr5_5600_octa_channel():
    """DDR5-5600 octa-channel ~ 358 GB/s aggregate; memory-bound ceiling INT4 ~720 GFLOPs/channel."""
    cfg = ExperimentConfig()
    # AVX-512 peak compute for 32 cores * 2.1 GHz * 16 ops FP16/cycle = 2150 GFLOPs/s
    assert cfg.edge_avx512_peak_gflops > 2000
    # DDR5-5600: 8 channels * 5.6 GT/s * 8 bytes ~ 358.4 GB/s
    assert 350 < cfg.edge_ddr5_bw_gbs < 365


# ---------- ExperimentConfig reproducibility ----------

def test_seed_42_canonical():
    """seed=42 default."""
    cfg = ExperimentConfig()
    assert cfg.seed == 42


def test_n_languages_98():
    """98 languages (Whisper Large-v3 covers 99; Addverb operates 98 publicly)."""
    cfg = ExperimentConfig()
    assert cfg.n_languages == 98


def test_lora_adapter_pool_size():
    """98 adapters * 8 MB = 784 MB << 2 TB DDR5 (host RAM trivial)."""
    cfg = ExperimentConfig()
    pool_mb = cfg.n_lora_adapters * cfg.lora_size_mb
    assert pool_mb < cfg.edge_ram_gb * 1024  # MB < GB*1024


def test_pacelc_default_mode_gating():
    """Default must be PA/EL+gating (differentiated gating per payload)."""
    cfg = ExperimentConfig()
    assert cfg.pacelc_mode == "PA/EL+gating"


def test_safety_threshold_below_zippy_tug():
    """Threshold 100 kg -> Zippy 6 (6 kg) auto-approved, Zippy Tug (2,000 kg) requires 2-of-3."""
    cfg = ExperimentConfig()
    assert cfg.safety_payload_threshold_kg == 100.0
    # Zippy 6 below threshold
    zippy_6_kg = 6
    assert zippy_6_kg < cfg.safety_payload_threshold_kg
    # Zippy Tug above threshold
    zippy_tug_kg = 2000
    assert zippy_tug_kg > cfg.safety_payload_threshold_kg
