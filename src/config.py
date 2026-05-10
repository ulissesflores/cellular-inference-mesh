"""ExperimentConfig — canonical parametrization of the Cellular Inference Mesh DES.

Mirrors Chapter 6 of the canonical document, calibrated against:
- Supermicro SYS-111E-FWTR (32 Xeon cores, 2 TB DDR5-5600, 2x 10GbE)
- Llama 3 8B INT4 (AWQ/QLoRA NF4, Dettmers et al., 2023)
- Whisper Large-v3 (98 languages)
- Mooncake traces (Qin et al., 2025)
- Leviathan speculative decoding formula (Leviathan, Kalman & Matias, 2023)

Author: Carlos Ulisses Flores <c.ulisses@gmail.com>
ORCID:  0000-0002-6034-7765
License: Apache-2.0
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ExperimentConfig:
    """Canonical DES experiment configuration.

    Reproducibility: ``seed=42`` is the canonical default. Modify only for
    Monte-Carlo sensitivity analysis. All numeric parameters are calibrated
    from peer-reviewed literature anchors (cf. module docstring).
    """

    # ---------- Reproducibility ----------
    seed: int = 42
    scenario: Literal["nominal", "partition", "burst"] = "nominal"
    sim_duration_s: float = 3600.0  # 1 industrial hour
    n_replicates: int = 100

    # ---------- AGV fleet ----------
    n_agvs: int = 10
    n_languages: int = 98
    lambda_voice_eps: float = 2.0  # commands/s/AGV (Poisson)

    # ---------- Edge server (SYS-111E-FWTR) ----------
    edge_cpu_cores: int = 32
    edge_ram_gb: int = 2048
    edge_ddr5_bw_gbs: float = 358.0  # DDR5-5600 octa-channel
    edge_avx512_peak_gflops: float = 2150.4  # 32 * 2.1 GHz * 16 ops/cycle FP16

    # ---------- ASR (Whisper Large-v3) ----------
    # Log-normal calibrated for 5-30 s of audio
    asr_mean_ms: float = 200.0
    asr_sigma_ln: float = 0.4

    # ---------- LLM edge (Llama 3 8B INT4) ----------
    llm_edge_prefill_mean_ms: float = 120.0  # 50 tokens input
    llm_edge_prefill_sigma_ln: float = 0.3
    llm_edge_decode_mean_ms_per_token: float = 18.0  # Gamma
    llm_edge_decode_gamma_shape: int = 4
    avg_response_tokens: int = 50

    # ---------- Cloud fallback (ChatGPT) ----------
    cloud_ttft_mean_ms: float = 300.0
    cloud_tbt_mean_ms: float = 15.0
    cloud_model: str = "gpt-4o-mini"
    cost_per_1k_tokens_cloud_usd: float = 0.00015

    # ---------- Uplink WAN ----------
    uplink_rtt_mean_ms: float = 80.0
    uplink_rtt_std_ms: float = 15.0
    uplink_loss_pct: float = 0.5

    # ---------- SLO ----------
    slo_response_ms: int = 500
    slo_p99_ms: int = 800

    # ---------- Multi-LoRA mesh (S-LoRA + LoRAX, Convirza-style) ----------
    n_lora_adapters: int = 98
    lora_rank: int = 16
    lora_size_mb: int = 8
    lora_load_overhead_ms: float = 5.0

    # ---------- KV strategy (MLA + sliding + CLA-2) ----------
    kv_strategy: Literal["MHA", "GQA-2", "MQA", "MLA", "MLA+sliding+CLA-2"] = (
        "MLA+sliding+CLA-2"
    )
    sliding_window: int = 4096
    kv_cache_mb_baseline_mha: float = 134.0  # 8K tokens BF16 (Vaswani et al., 2017)
    kv_cache_mb_proposed_mla_only: float = 13.4  # MLA only ~10x reduction (DeepSeek-V3, 2024)
    kv_cache_mb_proposed_full: float = 3.5  # MLA + sliding 4K + CLA-2 ~38x (composed)

    # ---------- Speculative decoding (Leviathan + EAGLE-3) ----------
    speculative_enabled: bool = True
    drafter: str = "EAGLE-3"
    lookahead_gamma: int = 4
    acceptance_alpha: float = 0.7
    drafter_relative_cost_c: float = 0.1
    speculative_threshold_tau: float = 0.6  # entropy-based gating

    # ---------- Cell-based + shuffle sharding (MacCárthaigh, AWS) ----------
    cell_workers: int = 8
    cell_shuffle_replicas: int = 2

    # ---------- Partition injection (2-state Markov) ----------
    partition_inject_pct: float = 2.0  # % of time spent in "bad" state
    partition_duration_s: float = 60.0

    # ---------- Burst scenario ----------
    burst_multiplier: float = 10.0
    burst_duration_s: float = 30.0
    burst_period_s: float = 600.0

    # ---------- Energy (TDP) ----------
    energy_edge_w_idle: float = 80.0
    energy_edge_w_full: float = 250.0
    energy_cloud_w_per_query: float = 0.7

    # ---------- PACELC mode ----------
    pacelc_mode: Literal["PA/EL", "PC/EC", "PA/EL+gating"] = "PA/EL+gating"

    # ---------- Safety thresholds (differentiated gating) ----------
    safety_payload_threshold_kg: float = 100.0  # Zippy Tug 2,000 kg requires high-safety path


def speculative_speedup(alpha: float, gamma: int, c: float) -> float:
    """Canonical Leviathan, Kalman & Matias (2023, arXiv:2211.17192) formula.

    E[T_spec] / E[T_target] = (1 - alpha^(gamma+1)) / ((1 - alpha)(gamma*c + 1))
    """
    if alpha >= 1.0:
        return float(gamma + 1)
    return (1.0 - alpha ** (gamma + 1)) / ((1.0 - alpha) * (gamma * c + 1.0))


def little_law_check(
    arrival_rate_lambda: float, mean_wait_w: float, in_flight_l: float, tol: float = 0.05
) -> tuple[bool, float]:
    """Validate Little's Law (``L = lambda * W``).

    Returns ``(ok, relative_error)``. Accepts ``relative_error < tol`` (default 5%).
    """
    expected_l = arrival_rate_lambda * mean_wait_w
    if expected_l == 0:
        return (in_flight_l == 0, 0.0)
    rel_err = abs(in_flight_l - expected_l) / expected_l
    return (rel_err < tol, rel_err)
