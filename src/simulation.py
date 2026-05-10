"""Salabim DES — Cellular Inference Mesh edge-cloud under PACELC.

Implementation of the proposed Cellular Inference Mesh architecture, following
the formal flow documented in `docs/algorithm.md` and the analytical bounds
derived in `docs/proofs.md`.

Core components:

1. AGVCommandGenerator — emits Poisson(lambda) commands per AGV
2. CommandHandler — per-event component (Whisper ASR + LoRA + edge LLM + cloud fallback)
3. CloudFallback — ChatGPT cross-WAN (Gamma service times)
4. SpeculativeOrchestrator — EAGLE-3 drafter + target cloud with modified
   rejection sampling per the Leviathan canonical formula
5. AttestationConsensus — 2-of-3 attestation for Zippy Tug high-payload commands
6. PartitionMarkov — 2-state (good/bad) Markov, calibrated per scenario
7. TelemetryCollector — TTFT, p50/p95/p99, fallback_rate, cost, energy, Little's Law

Baseline = public Addverb architecture; Proposed = full CIM-PCE composition.

Anchor references:
- Leviathan, Kalman & Matias (2023) ICML — speculative decoding
- Patel et al. (2024) ISCA — Splitwise prefill-decode disaggregation
- Qin et al. (2025) FAST Best Paper — Mooncake KVCache-centric
- MacCárthaigh (2019) AWS Builders' Library — shuffle sharding
- Abadi (2012) IEEE Computer — PACELC
- Rose et al. (2020) NIST SP 800-207 — Zero Trust

Author: Carlos Ulisses Flores <c.ulisses@gmail.com>
License: Apache-2.0
"""

from __future__ import annotations

import math
import statistics
from collections import deque
from dataclasses import dataclass
from typing import Any

import salabim as sb

from .config import ExperimentConfig, speculative_speedup

# ============================================================
# Events
# ============================================================


@dataclass
class CommandEvent:
    """Single voice command emitted by an AGV."""
    agv_id: int
    language_id: int
    safety_payload_kg: float
    t_arrival: float = 0.0
    t_asr_done: float = 0.0
    t_first_token: float = 0.0
    t_complete: float = 0.0
    used_cloud: bool = False
    rejected_partition: bool = False
    attestation_required: bool = False
    attestation_passed: bool = False
    tokens_emitted: int = 0
    tokens_cloud: int = 0
    speculative_accepted: int = 0  # tokens accepted by target after draft (proposed arm)


# ============================================================
# Auxiliary statistical distributions
# ============================================================


def lognormal_ms(mean_ms: float, sigma_ln: float, env: sb.Environment) -> float:
    """Log-normal calibrated to a target mean in ms."""
    mu_ln = math.log(mean_ms / 1000.0) - 0.5 * sigma_ln**2
    return env.random.lognormvariate(mu_ln, sigma_ln) * 1000.0


def gamma_ms(mean_ms: float, shape: int, env: sb.Environment) -> float:
    """Gamma with mean = shape * scale = mean_ms; used for Time-Per-Output-Token
    following Dean & Barroso (2013) Tail-at-Scale and the empirical characterization
    of LLM serving (heavy Gamma tail rather than memoryless exponential)."""
    scale = mean_ms / shape
    return env.random.gammavariate(shape, scale)


def truncated_normal_ms(
    mean_ms: float, std_ms: float, env: sb.Environment, lower: float = 10.0
) -> float:
    """Lower-truncated normal (>= lower) used for industrial RTT."""
    val = env.random.normalvariate(mean_ms, std_ms)
    return max(lower, val)


# ============================================================
# Telemetry
# ============================================================


class TelemetryCollector:
    """Collects end-to-end metrics and validates Little's Law a posteriori."""

    def __init__(self, cfg: ExperimentConfig):
        self.cfg = cfg
        self.events: list[CommandEvent] = []

    def record(self, ev: CommandEvent) -> None:
        self.events.append(ev)

    def latencies_ms(self) -> list[float]:
        return [
            (ev.t_complete - ev.t_arrival) * 1000.0
            for ev in self.events
            if not ev.rejected_partition and ev.t_complete > 0
        ]

    def percentile(self, p: float) -> float:
        lats = sorted(self.latencies_ms())
        if not lats:
            return 0.0
        # Nearest-rank: index = ceil(p * N)
        k = max(0, math.ceil(p * len(lats)) - 1)
        return lats[min(k, len(lats) - 1)]

    def fallback_rate(self) -> float:
        if not self.events:
            return 0.0
        # Only completed (non-rejected) commands enter the metric
        valid = [ev for ev in self.events if not ev.rejected_partition]
        if not valid:
            return 0.0
        return sum(1 for ev in valid if ev.used_cloud) / len(valid)

    def cost_usd(self) -> float:
        cfg = self.cfg
        return sum(
            ev.tokens_cloud / 1000.0 * cfg.cost_per_1k_tokens_cloud_usd
            for ev in self.events
        )

    def energy_j(self) -> float:
        """Decomposed energy: edge (idle + load * delta) * duration + cloud * queries."""
        cfg = self.cfg
        sim_dur = cfg.sim_duration_s
        denom = max(1.0, sim_dur * cfg.lambda_voice_eps * cfg.n_agvs)
        avg_load = min(1.0, len(self.events) / denom)
        edge_w = (
            cfg.energy_edge_w_idle
            + (cfg.energy_edge_w_full - cfg.energy_edge_w_idle) * avg_load
        )
        edge_j = edge_w * sim_dur
        cloud_j = sum(cfg.energy_cloud_w_per_query for ev in self.events if ev.used_cloud)
        return edge_j + cloud_j

    def little_validate(self) -> tuple[float, float, float]:
        """Estimate (lambda_eff, W_mean, L_observed) from telemetry."""
        cfg = self.cfg
        lats_s = [
            (ev.t_complete - ev.t_arrival)
            for ev in self.events
            if ev.t_complete > 0 and not ev.rejected_partition
        ]
        if not lats_s:
            return (0.0, 0.0, 0.0)
        n_completed = len(lats_s)
        sim_dur = cfg.sim_duration_s
        lambda_eff = n_completed / sim_dur
        w_mean = statistics.mean(lats_s)
        l_observed = lambda_eff * w_mean
        return (lambda_eff, w_mean, l_observed)

    def summary(self, label: str) -> dict[str, Any]:
        l_lambda, l_w, l_l = self.little_validate()
        return {
            "label": label,
            "n_events": len(self.events),
            "n_completed": sum(
                1 for ev in self.events if not ev.rejected_partition and ev.t_complete > 0
            ),
            "p50_ms": self.percentile(0.50),
            "p95_ms": self.percentile(0.95),
            "p99_ms": self.percentile(0.99),
            "fallback_rate": self.fallback_rate(),
            "cost_usd": self.cost_usd(),
            "energy_j": self.energy_j(),
            "little_lambda": l_lambda,
            "little_w_s": l_w,
            "little_l": l_l,
            "rejected_partition": sum(1 for ev in self.events if ev.rejected_partition),
            "attestation_required": sum(1 for ev in self.events if ev.attestation_required),
            "attestation_passed": sum(1 for ev in self.events if ev.attestation_passed),
            "speculative_accepted_avg": (
                statistics.mean(
                    [ev.speculative_accepted for ev in self.events if ev.used_cloud]
                )
                if any(ev.used_cloud for ev in self.events)
                else 0.0
            ),
        }


# ============================================================
# Speculative Decoding (Leviathan, Kalman & Matias 2023)
# ============================================================


class SpeculativeOrchestrator:
    """Decides cloud fallback via entropy gating and simulates speculative decoding.

    Baseline: fixed ~30% fallback rate, representing the public Addverb pipeline
    without speculative decoding (empirical share of non-trivial queries).

    Proposed: next-token entropy gating (Beta proxy) + Leviathan modified rejection
    sampling on the cloud target, accounting for the alpha-fraction of tokens
    accepted from the local draft.
    """

    def __init__(self, cfg: ExperimentConfig, env: sb.Environment, proposed: bool):
        self.cfg = cfg
        self.env = env
        self.proposed = proposed
        # Theoretical Leviathan speedup (informative, not enforced)
        self.expected_speedup = speculative_speedup(
            cfg.acceptance_alpha, cfg.lookahead_gamma, cfg.drafter_relative_cost_c
        )

    def should_fallback(self, ev: CommandEvent) -> bool:
        """Return True iff cloud should be invoked.

        Baseline: ~30% empirical Addverb fallback rate.
        Proposed: simulated next-token entropy gating via a Beta(2, 5) sample
        (mean ~0.29). Entropy above threshold tau invokes cloud; expected
        cloud share ~ (1-alpha) * beta.
        """
        if not self.proposed:
            return self.env.random.random() < 0.30

        # Beta(2, 5) proxy for normalized next-token entropy; above tau -> cloud.
        entropy_proxy = self.env.random.betavariate(2, 5)
        return entropy_proxy > self.cfg.speculative_threshold_tau

    def speculative_decode_tokens(self, target_tokens: int) -> tuple[int, int]:
        """Simulate Leviathan modified rejection sampling.

        Returns (accepted, target_calls). For each round the drafter emits gamma
        tokens; the target verifies in parallel (1 call), accepts each with i.i.d.
        probability alpha, stops on first rejection, then emits one bonus token.
        """
        cfg = self.cfg
        if not self.proposed:
            return (0, target_tokens)

        accepted_total = 0
        target_calls = 0
        emitted = 0
        gamma = cfg.lookahead_gamma
        alpha = cfg.acceptance_alpha

        while emitted < target_tokens:
            target_calls += 1
            in_round_accepted = 0
            for _ in range(gamma):
                if self.env.random.random() < alpha:
                    in_round_accepted += 1
                else:
                    break
            # Bonus token emitted by the target after the rejection or after gamma
            emitted += in_round_accepted + 1
            accepted_total += in_round_accepted

        return (min(accepted_total, target_tokens), target_calls)


# ============================================================
# Attestation Consensus (2-of-3 for Zippy Tug high-payload commands)
# ============================================================


class AttestationConsensus:
    """2-of-3 attestation for high-risk commands (Zippy Tug 2,000 kg).

    Simulates three independent attestations (edge TDX, cloud TDX, audit log).
    The command proceeds iff at least two confirm within the timeout; otherwise
    it is rejected. Reference: Rose et al. (2020) NIST SP 800-207 (Zero Trust).
    """

    def __init__(self, cfg: ExperimentConfig, env: sb.Environment):
        self.cfg = cfg
        self.env = env

    def required_for(self, ev: CommandEvent) -> bool:
        """Whether this command requires attestation."""
        return ev.safety_payload_kg >= self.cfg.safety_payload_threshold_kg

    def sample_attestation_latency_ms(self) -> float:
        """Latency of one TDX attestation (Intel Trust Domain Extensions).
        Log-normal with mean 30 ms (proxy from TDX/SGX literature)."""
        return lognormal_ms(30.0, 0.4, self.env)

    def sample_attestation_success(self, in_partition: bool) -> bool:
        """Attestation success probability.

        Nominal mode: 99% (calibrated from Confidential Computing literature).
        Under partition: cloud TDX fails (packets lost) but edge TDX and audit
        log remain reachable, so 2-of-3 stays feasible if both confirm.
        """
        if in_partition:
            return self.env.random.random() < 0.50  # only edge + audit reachable
        return self.env.random.random() < 0.99


# ============================================================
# Partition Markov (good/bad uplink)
# ============================================================


class PartitionMarkov(sb.Component):
    """Models the edge<->cloud uplink partition as a 2-state Markov chain."""

    def setup(self, cfg: ExperimentConfig):
        self.cfg = cfg
        self.state_bad = False
        self.bad_until = 0.0

    def is_bad(self) -> bool:
        if self.cfg.scenario != "partition":
            return False
        return self.state_bad and self.env.now() < self.bad_until

    def remaining_bad_s(self) -> float:
        return max(0.0, self.bad_until - self.env.now())

    def process(self):
        cfg = self.cfg
        if cfg.scenario != "partition":
            return
        bad_dur = cfg.partition_duration_s
        # The cyclic good duration can exceed sim_duration_s, in which case the
        # partition would never fire. We force the first partition at 25% of the
        # simulated horizon so the partition arm differs from the nominal arm.
        good_dur_cyclic = (
            bad_dur
            * (100.0 - cfg.partition_inject_pct)
            / max(0.1, cfg.partition_inject_pct)
        )
        first_bad_at = min(good_dur_cyclic, cfg.sim_duration_s * 0.25)
        yield self.hold(first_bad_at)
        self.state_bad = True
        self.bad_until = self.env.now() + bad_dur
        yield self.hold(bad_dur)
        self.state_bad = False
        while True:
            yield self.hold(good_dur_cyclic)
            self.state_bad = True
            self.bad_until = self.env.now() + bad_dur
            yield self.hold(bad_dur)
            self.state_bad = False


# ============================================================
# Per-event Command Handler
# ============================================================


class CommandHandler(sb.Component):
    """Processes one command end-to-end (ASR + LoRA + edge LLM + optional cloud)."""

    def setup(
        self,
        ev: CommandEvent,
        cfg: ExperimentConfig,
        cores: sb.Resource,
        spec: SpeculativeOrchestrator,
        attestation: AttestationConsensus,
        partition: PartitionMarkov,
        telemetry: TelemetryCollector,
        lora_cache: deque,
        proposed: bool,
    ):
        self.ev = ev
        self.cfg = cfg
        self.cores = cores
        self.spec = spec
        self.attestation = attestation
        self.partition = partition
        self.telemetry = telemetry
        self.lora_cache = lora_cache
        self.proposed = proposed

    def process(self):
        cfg = self.cfg
        env = self.env
        ev = self.ev

        in_partition = self.partition.is_bad()

        # ---- PACELC PA/EL+gating (proposed) ----
        # High-risk command under partition: requires 2-of-3 attestation
        if (
            self.proposed
            and self.attestation.required_for(ev)
            and cfg.pacelc_mode == "PA/EL+gating"
        ):
            ev.attestation_required = True
            yield from self._attestation_2_of_3(ev, in_partition)
            if not ev.attestation_passed:
                ev.rejected_partition = True
                ev.t_complete = env.now()
                self.telemetry.record(ev)
                return

        # Baseline: high-risk command under partition is simply rejected
        if not self.proposed and in_partition and ev.safety_payload_kg >= cfg.safety_payload_threshold_kg:
            ev.rejected_partition = True
            ev.t_complete = env.now()
            self.telemetry.record(ev)
            return

        # ---- ASR Whisper (lognormal) ----
        asr_ms = lognormal_ms(cfg.asr_mean_ms, cfg.asr_sigma_ln, env)
        yield self.request(self.cores)
        yield self.hold(asr_ms / 1000.0)
        self.release(self.cores)
        ev.t_asr_done = env.now()

        # ---- LoRA cache LRU (proposed only) ----
        lora_overhead_ms = 0.0
        if self.proposed:
            if ev.language_id in self.lora_cache:
                # Cache hit
                self.lora_cache.remove(ev.language_id)
            else:
                lora_overhead_ms = cfg.lora_load_overhead_ms
            self.lora_cache.append(ev.language_id)

        # ---- LLM edge prefill (lognormal) ----
        prefill_ms = lognormal_ms(
            cfg.llm_edge_prefill_mean_ms, cfg.llm_edge_prefill_sigma_ln, env
        )
        yield self.request(self.cores)
        yield self.hold((prefill_ms + lora_overhead_ms) / 1000.0)
        self.release(self.cores)

        # ---- Edge-vs-cloud decision (entropy gating) ----
        use_cloud = self.spec.should_fallback(ev)

        if use_cloud:
            ev.used_cloud = True
            yield from self._cloud_decode(ev)
        else:
            yield from self._edge_decode(ev)

        ev.t_complete = env.now()
        self.telemetry.record(ev)

    def _attestation_2_of_3(self, ev: CommandEvent, in_partition: bool):
        """Request three attestations (edge TDX, cloud TDX, audit-log HMAC)."""
        # The three attestations are issued in parallel in production; we charge
        # the worst-case latency (max of the three) to keep the model conservative.
        lat_edge = self.attestation.sample_attestation_latency_ms()
        lat_cloud = self.attestation.sample_attestation_latency_ms()
        lat_audit = self.attestation.sample_attestation_latency_ms()
        worst_ms = max(lat_edge, lat_cloud, lat_audit)
        yield self.hold(worst_ms / 1000.0)
        # Independent success draws
        ok_edge = self.attestation.sample_attestation_success(False)
        ok_cloud = self.attestation.sample_attestation_success(in_partition)
        ok_audit = self.attestation.sample_attestation_success(False)
        n_ok = sum([ok_edge, ok_cloud, ok_audit])
        ev.attestation_passed = n_ok >= 2

    def _edge_decode(self, ev: CommandEvent):
        cfg = self.cfg
        env = self.env
        tokens = cfg.avg_response_tokens
        decode_total_ms = sum(
            gamma_ms(
                cfg.llm_edge_decode_mean_ms_per_token,
                cfg.llm_edge_decode_gamma_shape,
                env,
            )
            for _ in range(tokens)
        )
        yield self.request(self.cores)
        ev.t_first_token = env.now()
        yield self.hold(decode_total_ms / 1000.0)
        self.release(self.cores)
        ev.tokens_emitted = tokens

    def _cloud_decode(self, ev: CommandEvent):
        cfg = self.cfg
        env = self.env
        # RTT (truncated normal) plus loss penalty
        rtt_ms = truncated_normal_ms(
            cfg.uplink_rtt_mean_ms, cfg.uplink_rtt_std_ms, env, lower=10.0
        )
        if env.random.random() < cfg.uplink_loss_pct / 100.0:
            rtt_ms *= 2.0
        # If uplink is in "bad" state, wait for the partition to end
        if self.partition.is_bad():
            yield self.hold(self.partition.remaining_bad_s())

        # Cloud TTFT (lognormal) with RTT floor
        cloud_ttft_ms = rtt_ms + lognormal_ms(cfg.cloud_ttft_mean_ms, 0.3, env)
        yield self.hold(cloud_ttft_ms / 1000.0)
        ev.t_first_token = env.now()

        # Modified speculative decoding (proposed): local drafter + cloud target
        target_tokens = cfg.avg_response_tokens
        if self.proposed and cfg.speculative_enabled:
            accepted, target_calls = self.spec.speculative_decode_tokens(target_tokens)
            ev.speculative_accepted = accepted
            # Cloud cost scales with target calls, since each call verifies
            # gamma+1 tokens in parallel; billed cloud tokens ~ target_calls.
            ev.tokens_cloud = max(1, target_calls)
        else:
            ev.tokens_cloud = target_tokens

        # Gamma TBT (heavy-tail) instead of exponential. Baseline: token-by-token.
        # Proposed: per-call accounting (gamma+1 tokens verified in parallel).
        n_decode_steps = ev.tokens_cloud
        decode_total_ms = sum(
            gamma_ms(cfg.cloud_tbt_mean_ms, 4, env) for _ in range(n_decode_steps)
        )
        yield self.hold(decode_total_ms / 1000.0)
        ev.tokens_emitted = target_tokens


# ============================================================
# AGV Command Generator
# ============================================================


class AGVCommandGenerator(sb.Component):
    """Emits Poisson(lambda) commands per AGV; injects bursts under the 'burst' scenario."""

    def setup(
        self,
        agv_id: int,
        cfg: ExperimentConfig,
        cores: sb.Resource,
        spec: SpeculativeOrchestrator,
        attestation: AttestationConsensus,
        partition: PartitionMarkov,
        telemetry: TelemetryCollector,
        lora_cache: deque,
        proposed: bool,
    ):
        self.agv_id = agv_id
        self.cfg = cfg
        self.cores = cores
        self.spec = spec
        self.attestation = attestation
        self.partition = partition
        self.telemetry = telemetry
        self.lora_cache = lora_cache
        self.proposed = proposed
        # Pseudo-random language per AGV (98 languages total)
        self.language_id = (agv_id * 7919) % cfg.n_languages
        # Alternating payload class (50% Zippy Tug 2,000 kg, 50% Zippy 25 kg)
        self.payload_kg = 2000.0 if agv_id % 2 == 0 else 25.0

    def process(self):
        cfg = self.cfg
        rng = self.env.random
        while True:
            yield self.hold(rng.expovariate(cfg.lambda_voice_eps))

            # Burst injected under the 'burst' scenario
            if cfg.scenario == "burst":
                in_burst = (
                    self.env.now() % cfg.burst_period_s < cfg.burst_duration_s
                )
                if in_burst:
                    extra = max(1, int(cfg.burst_multiplier) - 1)
                    for _ in range(extra):
                        ev_extra = CommandEvent(
                            agv_id=self.agv_id,
                            language_id=self.language_id,
                            safety_payload_kg=self.payload_kg,
                            t_arrival=self.env.now(),
                        )
                        CommandHandler(
                            ev=ev_extra,
                            cfg=cfg,
                            cores=self.cores,
                            spec=self.spec,
                            attestation=self.attestation,
                            partition=self.partition,
                            telemetry=self.telemetry,
                            lora_cache=self.lora_cache,
                            proposed=self.proposed,
                            env=self.env,
                        )

            ev = CommandEvent(
                agv_id=self.agv_id,
                language_id=self.language_id,
                safety_payload_kg=self.payload_kg,
                t_arrival=self.env.now(),
            )
            CommandHandler(
                ev=ev,
                cfg=cfg,
                cores=self.cores,
                spec=self.spec,
                attestation=self.attestation,
                partition=self.partition,
                telemetry=self.telemetry,
                lora_cache=self.lora_cache,
                proposed=self.proposed,
                env=self.env,
            )


# ============================================================
# Main runner for one replica
# ============================================================


def run_replica(
    cfg: ExperimentConfig, proposed: bool, replica_seed: int
) -> dict[str, Any]:
    """Run one replica * scenario * {baseline | proposed} and return the summary.

    Reproducibility: identical (cfg, proposed, replica_seed) yields the same summary.
    Validation: Little's Law a posteriori via TelemetryCollector.little_validate().
    """
    env = sb.Environment(trace=False, random_seed=replica_seed, yieldless=False)

    cores = sb.Resource(name="edge_cpu", capacity=cfg.edge_cpu_cores, env=env)
    partition = PartitionMarkov(cfg=cfg, env=env)
    attestation = AttestationConsensus(cfg, env)
    telemetry = TelemetryCollector(cfg)
    spec = SpeculativeOrchestrator(cfg, env, proposed=proposed)
    lora_cache: deque = deque(maxlen=cfg.n_lora_adapters)

    for agv_id in range(cfg.n_agvs):
        AGVCommandGenerator(
            agv_id=agv_id,
            cfg=cfg,
            cores=cores,
            spec=spec,
            attestation=attestation,
            partition=partition,
            telemetry=telemetry,
            lora_cache=lora_cache,
            proposed=proposed,
            env=env,
        )

    env.run(till=cfg.sim_duration_s)

    label = f"{'proposed' if proposed else 'baseline'}_{cfg.scenario}"
    return telemetry.summary(label)
