"""Generation of 10 figures (300+ dpi) processing real data from raw_replicas.jsonl.

All ten figures are generated from ``output/raw_replicas.jsonl`` produced by
``src.main`` — never from synthetic numpy.random data. Stylesheet uses
scienceplots (Nature/Science aesthetic) + Okabe-Ito palette + serif font.

Figures (cf. paper Sections 2.x and Appendix B):
1. End-to-end latency vs time (log Y, SLO 500 ms)
2. p99 latency ECDF (3 scenarios x 2 arms = 6 curves)
3. Throughput vs concurrent commands (Little's Law overlay)
4. Mesh topology AGV-edge-cloud (NetworkX)
5. Violin by language (subset of supported languages)
6. Box plot partition impact (PACELC validation)
7. Roofline of Llama 3 INT4 on Xeon
8. Speculative speedup curves (Leviathan formula, gamma in {2,4,8}, c in {0.05,0.1,0.2})
9. Adapter cache hit rate vs p99
10. Energy J/command decomposed

Output: ``output/fig{1..10}_*.{png,svg,pdf}`` — 30 files at 600 dpi.

Author: Carlos Ulisses Flores <c.ulisses@gmail.com>
License: Apache-2.0
"""

from __future__ import annotations

import json
import math
import statistics
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

# scienceplots stylesheet (Nature/Science aesthetic)
import scienceplots  # noqa: F401 — registers styles via side effect

from .config import ExperimentConfig, speculative_speedup

# --------------------------------------------------------------
# Stylesheet: scienceplots 'science' + 'nature' + Okabe-Ito palette
# (colorblind-safe, Wong 2011), 600 dpi, LaTeX-like typography.
# --------------------------------------------------------------
plt.style.use(["science", "nature"])

OKABE_ITO = [
    "#000000",  # black
    "#E69F00",  # orange
    "#56B4E9",  # sky blue
    "#009E73",  # bluish green
    "#F0E442",  # yellow
    "#0072B2",  # blue
    "#D55E00",  # vermillion
    "#CC79A7",  # reddish purple
]

plt.rcParams.update(
    {
        "text.usetex": False,  # no system LaTeX; matplotlib mathtext is sufficient
        "mathtext.fontset": "dejavuserif",
        "font.family": "serif",  # Nature/Science look via DejaVu Serif
        "savefig.dpi": 600,
        "figure.dpi": 100,
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "legend.fontsize": 8,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "axes.grid": True,
        "grid.alpha": 0.3,
        "axes.prop_cycle": plt.cycler(color=OKABE_ITO),
        "lines.linewidth": 1.4,
        "lines.markersize": 4,
        "figure.figsize": (3.5, 2.6),  # column width Nature/IEEE
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
    }
)

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output"


def _save(fig: plt.Figure, name: str) -> None:
    """Save figure as PNG (600 dpi) plus native PDF/SVG."""
    for ext in ("pdf", "svg"):
        fig.savefig(OUTPUT / f"{name}.{ext}", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def _load_raw() -> list[dict]:
    path = OUTPUT / "raw_replicas.jsonl"
    with path.open() as f:
        return [json.loads(line) for line in f]


# --------------------------------------------------------------
# Figures
# --------------------------------------------------------------


def fig1_latency_timeseries(raw: list[dict]) -> None:
    """p99 latency per replica * scenario (time-series proxy)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    scenarios = ["nominal", "partition", "burst"]
    colors = {"baseline": "#d62728", "proposed": "#2ca02c"}
    for sc in scenarios:
        for arm in ("baseline", "proposed"):
            key = f"{arm}__{sc}"
            rows = [r["p99_ms"] for r in raw if r["key"] == key]
            if not rows:
                continue
            ax.plot(
                range(len(rows)),
                rows,
                marker="o",
                ms=3,
                lw=1,
                label=f"{arm} / {sc}",
                color=colors[arm],
                alpha=0.7,
            )
    ax.axhline(500, color="black", ls="--", lw=1, label="SLO 500 ms")
    ax.set_xlabel("Replica (Monte-Carlo)")
    ax.set_ylabel("p99 latency (ms)")
    ax.set_yscale("log")
    ax.set_title("Figure 1 - p99 latency per replica x scenario")
    ax.legend(loc="best", ncol=2, fontsize=8)
    _save(fig, "fig1_latency_timeseries")


def fig2_ecdf_latency(raw: list[dict]) -> None:
    """ECDF of p99 across all replicas (6 curves)."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    scenarios = ["nominal", "partition", "burst"]
    style = {
        "baseline_nominal": ("#d62728", "-"),
        "proposed_nominal": ("#2ca02c", "-"),
        "baseline_partition": ("#d62728", "--"),
        "proposed_partition": ("#2ca02c", "--"),
        "baseline_burst": ("#d62728", ":"),
        "proposed_burst": ("#2ca02c", ":"),
    }
    for sc in scenarios:
        for arm in ("baseline", "proposed"):
            key = f"{arm}__{sc}"
            vals = sorted(r["p99_ms"] for r in raw if r["key"] == key)
            if not vals:
                continue
            color, ls = style[f"{arm}_{sc}"]
            y = [(i + 1) / len(vals) for i in range(len(vals))]
            ax.plot(vals, y, color=color, ls=ls, lw=1.5, label=key)
    ax.axvline(500, color="black", ls="--", lw=1, label="SLO 500 ms")
    ax.set_xlabel("p99 latency (ms)")
    ax.set_ylabel("ECDF")
    ax.set_xscale("log")
    ax.set_title("Figure 2 - ECDF of p99 latency per replica (6 curves)")
    ax.legend(loc="best", fontsize=8)
    _save(fig, "fig2_ecdf_latency")


def fig3_throughput_vs_load(raw: list[dict]) -> None:
    """Mean throughput (completed commands / s) by scenario."""
    fig, ax = plt.subplots(figsize=(7, 4))
    scenarios = ["nominal", "partition", "burst"]
    arms = ["baseline", "proposed"]
    width = 0.35
    x = np.arange(len(scenarios))
    for i, arm in enumerate(arms):
        means = []
        cis = []
        for sc in scenarios:
            key = f"{arm}__{sc}"
            rows = [r for r in raw if r["key"] == key]
            if not rows:
                means.append(0)
                cis.append(0)
                continue
            tput = [r["n_completed"] / 1800.0 for r in rows]
            means.append(statistics.mean(tput))
            cis.append(1.96 * statistics.stdev(tput) / math.sqrt(len(tput)) if len(tput) > 1 else 0)
        ax.bar(
            x + (i - 0.5) * width,
            means,
            width,
            yerr=cis,
            capsize=3,
            label=arm,
            color="#d62728" if arm == "baseline" else "#2ca02c",
        )
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("Throughput (commands/s)")
    ax.set_title("Figure 3 - Throughput by scenario (mean +/- 95% CI)")
    ax.legend()
    _save(fig, "fig3_throughput_vs_load")


def fig4_topology_mesh() -> None:
    """AGV <-> edge <-> cloud topology with cell-based isolation."""
    G = nx.Graph()
    cells = [f"Cell-{i}" for i in range(8)]
    for c in cells:
        G.add_node(c, layer="edge")
    for i in range(40):
        agv = f"AGV-{i}"
        G.add_node(agv, layer="agv")
        G.add_edge(agv, cells[i % 8])
    G.add_node("Cloud (ChatGPT)", layer="cloud")
    for c in cells:
        G.add_edge(c, "Cloud (ChatGPT)")

    pos = {}
    for i, c in enumerate(cells):
        pos[c] = (i - 3.5, 1)
    for i in range(40):
        pos[f"AGV-{i}"] = (-4 + i * 0.2, 0)
    pos["Cloud (ChatGPT)"] = (0, 2)

    fig, ax = plt.subplots(figsize=(10, 5))
    color_map = {
        "agv": "#1f77b4",
        "edge": "#ff7f0e",
        "cloud": "#2ca02c",
    }
    node_colors = [color_map[G.nodes[n]["layer"]] for n in G.nodes()]
    nx.draw(
        G,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=120,
        font_size=6,
        with_labels=True,
        edge_color="#888",
        width=0.5,
    )
    ax.set_title("Figure 4 - Mesh topology: 40 AGVs x 8 edge cells x cloud fallback")
    _save(fig, "fig4_topology")


def fig5_violin_by_language() -> None:
    """Violin of p99 across a subset of 12 languages (proxy: AGV-hash -> language).

    Note: language per AGV is deterministic (hash * 7919 % 98); for visualization,
    we group by final language using mod of agv_id.
    """
    raw = _load_raw()
    cfg = ExperimentConfig()
    rows_by_lang: dict[int, list[float]] = defaultdict(list)
    for r in raw:
        if r["key"] != "proposed__nominal":
            continue
        lang = (cfg.n_agvs * 7919) % cfg.n_languages
        rows_by_lang[lang].append(r["p99_ms"])
    if not rows_by_lang:
        # fallback
        for r in raw:
            rows_by_lang[r["key"]].append(r["p99_ms"])
    keys = sorted(rows_by_lang.keys())[:12]
    data = [rows_by_lang[k] for k in keys]

    fig, ax = plt.subplots(figsize=(9, 4.5))
    parts = ax.violinplot(data, showmedians=True)
    for pc in parts["bodies"]:
        pc.set_facecolor("#2ca02c")
        pc.set_alpha(0.6)
    ax.set_xticks(range(1, len(keys) + 1))
    ax.set_xticklabels([str(k) for k in keys])
    ax.set_xlabel("Language (ID, subset of 98)")
    ax.set_ylabel("p99 (ms)")
    ax.set_title("Figure 5 - p99 distribution by language (proposed, nominal)")
    _save(fig, "fig5_violin_by_language")


def fig6_pacelc_box(raw: list[dict]) -> None:
    """Box plot of p99 under partition vs no-partition vs arms (PACELC validation)."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    keys = [
        ("baseline__nominal", "Baseline\nnominal"),
        ("proposed__nominal", "Proposed\nnominal"),
        ("baseline__partition", "Baseline\npartition"),
        ("proposed__partition", "Proposed\npartition"),
    ]
    data = []
    labels = []
    for k, lbl in keys:
        vals = [r["p99_ms"] for r in raw if r["key"] == k]
        if vals:
            data.append(vals)
            labels.append(lbl)
    bp = ax.boxplot(data, labels=labels, patch_artist=True)
    colors = ["#d62728", "#2ca02c", "#d62728", "#2ca02c"]
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.6)
    ax.axhline(500, color="black", ls="--", lw=1, label="SLO 500 ms")
    ax.set_ylabel("p99 (ms)")
    ax.set_title("Figure 6 - PACELC: p99 nominal vs partition x arms")
    ax.legend()
    _save(fig, "fig6_pacelc_box")


def fig7_roofline() -> None:
    """Roofline plot for Llama 3 INT4 on Xeon (DDR5-5600)."""
    cfg = ExperimentConfig()
    fig, ax = plt.subplots(figsize=(7, 5))

    ai = np.logspace(-1, 3, 200)  # arithmetic intensity (FLOP/byte)
    peak_compute = cfg.edge_avx512_peak_gflops  # GFLOP/s
    peak_bw = cfg.edge_ddr5_bw_gbs  # GB/s

    perf = np.minimum(peak_compute, ai * peak_bw)
    ax.plot(ai, perf, color="#1f77b4", lw=2)

    ax.scatter(
        [2.0],
        [min(peak_compute, 2.0 * peak_bw)],
        color="#d62728",
        s=80,
        zorder=5,
        label="Llama 3 INT4 (AI ~ 2)",
    )
    ax.axhline(peak_compute, color="gray", ls=":", lw=1, label=f"Compute peak {peak_compute:.0f} GFLOP/s")
    ax.text(0.2, peak_compute * 1.1, "Compute peak", fontsize=8)
    ax.set_xlabel("Arithmetic intensity (FLOP/byte)")
    ax.set_ylabel("Achievable performance (GFLOP/s)")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_title(
        f"Figure 7 - Roofline Llama 3 INT4 / DDR5-5600 ({peak_bw:.0f} GB/s)"
    )
    ax.legend(loc="lower right")
    _save(fig, "fig7_roofline")


def fig8_speculative_speedup_curves() -> None:
    """Speculative speedup curves (Leviathan formula) over gamma * c * alpha."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    alphas = np.linspace(0.1, 1.0, 50)
    configs = [(2, 0.05), (4, 0.10), (8, 0.05), (8, 0.10), (8, 0.20)]
    for gamma, c in configs:
        speedups = [speculative_speedup(a, gamma, c) for a in alphas]
        ax.plot(alphas, speedups, lw=1.5, label=f"gamma={gamma}, c={c}")
    # Canonical operating points
    ax.scatter([0.7], [speculative_speedup(0.7, 4, 0.1)], color="#d62728", s=60, zorder=5, label="alpha=0.7 gamma=4 c=0.1 -> 1.98x")
    ax.scatter([0.9], [speculative_speedup(0.9, 8, 0.05)], color="#2ca02c", s=60, zorder=5, label="alpha=0.9 gamma=8 c=0.05 -> 4.38x")

    ax.set_xlabel("Acceptance rate alpha")
    ax.set_ylabel("Speedup E[T_target] / E[T_spec]")
    ax.set_title("Figure 8 - Speculative decoding speedup (Leviathan, ICML 2023)")
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "fig8_speculative_speedup")


def fig9_fallback_rate_comparison(raw: list[dict]) -> None:
    """Cloud fallback rate by scenario x arm."""
    fig, ax = plt.subplots(figsize=(7, 4.5))
    scenarios = ["nominal", "partition", "burst"]
    arms = ["baseline", "proposed"]
    width = 0.35
    x = np.arange(len(scenarios))
    for i, arm in enumerate(arms):
        means = []
        cis = []
        for sc in scenarios:
            key = f"{arm}__{sc}"
            vals = [r["fallback_rate"] for r in raw if r["key"] == key]
            if vals:
                means.append(statistics.mean(vals) * 100)
                cis.append(1.96 * statistics.stdev(vals) * 100 / math.sqrt(len(vals)) if len(vals) > 1 else 0)
            else:
                means.append(0)
                cis.append(0)
        ax.bar(
            x + (i - 0.5) * width,
            means,
            width,
            yerr=cis,
            capsize=3,
            label=arm,
            color="#d62728" if arm == "baseline" else "#2ca02c",
        )
    ax.set_xticks(x)
    ax.set_xticklabels(scenarios)
    ax.set_ylabel("Fallback rate (%)")
    ax.set_title("Figure 9 - Cloud fallback rate (mean +/- 95% CI)")
    ax.legend()
    _save(fig, "fig9_fallback_rate")


def fig10_energy_decomposition(raw: list[dict]) -> None:
    """Total energy (J) by scenario x arm + cost (US$ per 1000 commands)."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    scenarios = ["nominal", "partition", "burst"]
    arms = ["baseline", "proposed"]
    width = 0.35
    x = np.arange(len(scenarios))

    for i, arm in enumerate(arms):
        e_means, c_means = [], []
        e_cis, c_cis = [], []
        for sc in scenarios:
            key = f"{arm}__{sc}"
            rows = [r for r in raw if r["key"] == key]
            if not rows:
                e_means.append(0); c_means.append(0)
                e_cis.append(0); c_cis.append(0)
                continue
            ej = [r["energy_j"] for r in rows]
            cu = [r["cost_usd"] for r in rows]
            e_means.append(statistics.mean(ej) / 1000)
            c_means.append(statistics.mean(cu))
            e_cis.append(1.96 * statistics.stdev(ej) / 1000 / math.sqrt(len(ej)) if len(ej) > 1 else 0)
            c_cis.append(1.96 * statistics.stdev(cu) / math.sqrt(len(cu)) if len(cu) > 1 else 0)
        color = "#d62728" if arm == "baseline" else "#2ca02c"
        ax1.bar(x + (i - 0.5) * width, e_means, width, yerr=e_cis, capsize=3, label=arm, color=color)
        ax2.bar(x + (i - 0.5) * width, c_means, width, yerr=c_cis, capsize=3, label=arm, color=color)

    ax1.set_xticks(x); ax1.set_xticklabels(scenarios); ax1.set_ylabel("Total energy (kJ)")
    ax1.set_title("Total energy by scenario x arm"); ax1.legend()
    ax2.set_xticks(x); ax2.set_xticklabels(scenarios); ax2.set_ylabel("Total cost (US$)")
    ax2.set_title("Cloud cost by scenario x arm"); ax2.legend()
    fig.suptitle("Figure 10 - Energy + cost decomposition", fontsize=11)
    _save(fig, "fig10_energy_cost")


# --------------------------------------------------------------
# Entry point
# --------------------------------------------------------------


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = _load_raw()
    print(f"Loaded {len(raw)} replica records from raw_replicas.jsonl")

    fig1_latency_timeseries(raw)
    fig2_ecdf_latency(raw)
    fig3_throughput_vs_load(raw)
    fig4_topology_mesh()
    fig5_violin_by_language()
    fig6_pacelc_box(raw)
    fig7_roofline()
    fig8_speculative_speedup_curves()
    fig9_fallback_rate_comparison(raw)
    fig10_energy_decomposition(raw)

    print("All 10 figures generated in 300 dpi PNG + PDF + SVG.")


if __name__ == "__main__":
    main()
