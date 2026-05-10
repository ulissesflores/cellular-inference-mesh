"""Three mathematical-diagram figures rendered via matplotlib.

Generates the supporting visual material for the formal documentation:

- Figure 11 — Algorithm 1 flowchart (8 layers + payload-gated attestation),
  embedded in `docs/algorithm.md`.
- Figure 12 — Payload-gating decision tree under Zero Trust, embedded in
  the paper's §2.2.6.
- Figure 13 — Multiplicative key-value cache reduction derivation,
  illustrating the steps of Proposition 1 in `docs/proofs.md`.

All figures are produced at 600 dpi (PNG + PDF + SVG) using the
scienceplots stylesheet plus the Okabe-Ito colorblind-safe palette.

Outputs:
    output/fig{11,12,13}_*.{png,pdf,svg}

Usage:
    python scripts/figs_math_diagrams.py
"""

from __future__ import annotations

__author__ = "Carlos Ulisses Flores"
__email__ = "c.ulisses@gmail.com"
__orcid__ = "0000-0002-6034-7765"
__license__ = "Apache-2.0"

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import scienceplots  # noqa: F401

OKABE_ITO = [
    "#000000", "#E69F00", "#56B4E9", "#009E73",
    "#F0E442", "#0072B2", "#D55E00", "#CC79A7",
]

plt.style.use(["science", "nature"])
plt.rcParams.update({
    "text.usetex": False,
    "mathtext.fontset": "dejavuserif",
    "font.family": "serif",
    "savefig.dpi": 600,
    "axes.prop_cycle": plt.cycler(color=OKABE_ITO),
})

OUTPUT = Path(__file__).parent.parent / "output"


def _save(fig: plt.Figure, name: str) -> None:
    """Persist a Matplotlib figure as PNG (600 dpi), PDF, and SVG.

    Each format is saved with `bbox_inches="tight"` so that no whitespace
    halo surrounds the diagram. The PDF and SVG variants are vector and
    therefore independent of dpi.

    Args:
        fig: Matplotlib `Figure` to save.
        name: Filename stem (without extension) under `output/`.

    Side effects:
        Writes three files: `output/{name}.png`, `output/{name}.pdf`,
        `output/{name}.svg`. Closes `fig` to release Matplotlib state.
    """
    for ext in ("pdf", "svg"):
        fig.savefig(OUTPUT / f"{name}.{ext}", bbox_inches="tight")
    fig.savefig(OUTPUT / f"{name}.png", dpi=600, bbox_inches="tight")
    plt.close(fig)


def fig11_algorithm_1_flowchart() -> None:
    """Algorithm 1 diagram - 8 CIM-PCE layers with payload-gating decision."""
    fig, ax = plt.subplots(figsize=(7, 9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 22)
    ax.axis("off")

    # 8 camadas em ordem vertical descendente
    layers = [
        ("Input: c (audio), m (kg), l, v", 21, "#56B4E9", "input"),
        ("Layer 1: P4 in-network NLU\n(wake-word + lang-ID line-rate)", 19, "#E69F00", "stage"),
        ("Layer 2: Edge ASR\nWhisper Large-v3 (5-30 s)", 17, "#E69F00", "stage"),
        ("Layer 3: LoRA + KV cache\nS-LoRA + MLA+SW+CLA-2", 15, "#0072B2", "stage"),
        ("Layer 4: Edge LLM\nEAGLE-3 spec + entropy gate tau_e", 13, "#0072B2", "stage"),
        ("H(p_token) > tau_e ?", 11, "#D55E00", "decision"),
        ("Layer 5: Cloud fallback\nMooncake PD-disagg", 9, "#D55E00", "stage"),
        ("Layer 6: Energy-aware routing\n(record J/command, update table)", 7, "#009E73", "stage"),
        ("Layer 7: Cellular isolation\nshuffle_shard(v, M=8, k=2)", 5, "#009E73", "stage"),
        ("m >= m_critical ?", 3, "#D55E00", "decision"),
        ("PC/EC: 2-of-3 TDX\nattestation required", 1.5, "#CC79A7", "stage"),
        ("PA/EL: auto-approve local", 1.5, "#F0E442", "stage"),  # same y, lateral
        ("Output: r (response), a (approval)", -0.3, "#56B4E9", "output"),
    ]

    def draw_box(text, y, color, kind, x_center=5):
        if kind == "decision":
            poly = mpatches.FancyBboxPatch(
                (x_center - 1.8, y - 0.5), 3.6, 1.0,
                boxstyle="round,pad=0.1", linewidth=1.2,
                edgecolor="black", facecolor=color, alpha=0.55,
            )
        else:
            poly = mpatches.FancyBboxPatch(
                (x_center - 2.0, y - 0.6), 4.0, 1.2,
                boxstyle="round,pad=0.1", linewidth=1.0,
                edgecolor="black", facecolor=color, alpha=0.55,
            )
        ax.add_patch(poly)
        ax.text(x_center, y, text, ha="center", va="center", fontsize=8, weight="bold" if kind == "decision" else "normal")

    # Stack vertical
    for i, (text, y, color, kind) in enumerate(layers[:-2]):
        if kind == "stage" and "PA/EL" in text:
            draw_box(text, y, color, kind, x_center=8)  # right branch
        else:
            draw_box(text, y, color, kind)

    # Last 2 layers special: payload-gating decision tree branches
    # Replace the 'PA/EL' from list with right branch position
    # Already drawn properly above

    # Vertical arrows between consecutive layers
    for i in range(len(layers) - 3):
        y_top = layers[i][1] - 0.6
        y_bot = layers[i + 1][1] + 0.6
        if y_top > y_bot + 0.1:
            ax.annotate("", xy=(5, y_bot), xytext=(5, y_top),
                        arrowprops=dict(arrowstyle="->", lw=1.0, color="black"))

    # Arrow from PA/EL and PC/EC to output
    ax.annotate("", xy=(5, -0.3 + 0.6), xytext=(5, 1.5 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="black"))
    ax.annotate("", xy=(5, -0.3 + 0.6), xytext=(8, 1.5 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.0, color="black"))

    # Yes/No branches of the entropy decision
    ax.text(5.3, 10.0, "no (96%)", fontsize=8, color="black", style="italic")
    ax.text(7.5, 10.5, "yes (4%)", fontsize=8, color="black", style="italic")
    # Arrow from entropy decision to Layer 5
    ax.annotate("", xy=(5, 9 + 0.6), xytext=(5, 11 - 0.5),
                arrowprops=dict(arrowstyle="->", lw=1.0))

    # Yes/No branches of the payload decision
    ax.text(3.5, 2.3, "yes\n(Zippy Tug)", fontsize=8, ha="center", color="black", style="italic")
    ax.text(6.8, 2.3, "no\n(Zippy 6)", fontsize=8, ha="center", color="black", style="italic")
    ax.annotate("", xy=(5, 1.5 + 0.6), xytext=(4, 3 - 0.5),
                arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(8, 1.5 + 0.6), xytext=(6, 3 - 0.5),
                arrowprops=dict(arrowstyle="->", lw=1.0))

    ax.set_title("Algorithm 1 - CIM-PCE Inference Routing\nwith Payload-Gated Attestation",
                 fontsize=11, weight="bold")

    _save(fig, "fig11_algorithm_1_diagram")


def fig12_decision_tree_payload_gating() -> None:
    """Payload-gating decision tree: Zippy 6 vs Zippy Tug, PACELC modes."""
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 12)
    ax.set_ylim(-1.5, 8)
    ax.axis("off")

    nodes = [
        # (x, y, text, color)
        (6, 7, "Command received\n(transcription t, AGV v)", "#56B4E9"),
        (6, 5, "m_payload >= 100 kg ?\n(AGV ground truth)", "#D55E00"),
        (3, 3, "Zippy 6 (6 kg)\n-> PA/EL mode", "#F0E442"),
        (9, 3, "Zippy Tug (2,000 kg)\n-> PC/EC mode", "#CC79A7"),
        (3, 1, "Auto-approve local\n(high consistency,\nsub-100 ms latency)", "#009E73"),
        (9, 1, "2-of-3 attestation\n(Intel TDX, RA quotes)\nLatency +200-400 ms", "#0072B2"),
    ]

    for x, y, text, color in nodes:
        box = mpatches.FancyBboxPatch(
            (x - 1.5, y - 0.6), 3.0, 1.2,
            boxstyle="round,pad=0.12", linewidth=1.1,
            edgecolor="black", facecolor=color, alpha=0.55,
        )
        ax.add_patch(box)
        ax.text(x, y, text, ha="center", va="center", fontsize=9, weight="bold")

    # Edges
    ax.annotate("", xy=(6, 5 + 0.6), xytext=(6, 7 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.annotate("", xy=(3, 3 + 0.6), xytext=(5.0, 5 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.annotate("", xy=(9, 3 + 0.6), xytext=(7.0, 5 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.annotate("", xy=(3, 1 + 0.6), xytext=(3, 3 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.2))
    ax.annotate("", xy=(9, 1 + 0.6), xytext=(9, 3 - 0.6),
                arrowprops=dict(arrowstyle="->", lw=1.2))

    # Decision labels
    ax.text(4.0, 4.0, "no\n(60% queries)", fontsize=8, ha="center", style="italic")
    ax.text(8.0, 4.0, "yes\n(40% queries)", fontsize=8, ha="center", style="italic")

    # PACELC banner — placed below the lowest decision row (y=1) with safe margin
    ax.text(6, -0.7, "PACELC operationalized:\nPA/EL for low criticality (Zippy 6) | PC/EC for high criticality (Zippy Tug)",
            ha="center", va="center", fontsize=8, style="italic", color="dimgray",
            bbox={"boxstyle": "round,pad=0.4", "fc": "lightyellow", "ec": "dimgray"})

    ax.set_title("Payload-Gating Decision Tree under Zero Trust (Rose et al., 2020)\n"
                 "PACELC trade-off operationalized by AGV mass",
                 fontsize=11, weight="bold")

    _save(fig, "fig12_decision_tree_payload_gating")


def fig13_kv_cache_derivation() -> None:
    """Visual derivation of the KV-cache composition: MHA -> MQA -> GQA -> MLA -> +Sliding -> +CLA-2."""
    fig, ax = plt.subplots(figsize=(8, 5.5))

    # Each technique sorted by descending KV size
    techniques = [
        ("MHA\n(baseline)", 128.0, "#000000", 1.0, "Vaswani et al. 2017"),
        ("MQA", 4.0, "#E69F00", 32.0, "Shazeer 2019"),
        ("GQA-8", 32.0, "#56B4E9", 4.0, "Ainslie et al. 2023"),
        ("Sliding 128", 64.0, "#009E73", 2.0, "Beltagy et al. 2020"),
        ("MLA", 13.0, "#F0E442", 9.85, "DeepSeek-AI 2024"),
        ("MLA +\nSliding 128", 6.4, "#0072B2", 20.0, "composed"),
        ("MLA + Sliding +\nCLA-2", 3.4, "#D55E00", 37.6, "Brandon et al. 2024"),
    ]

    names = [t[0] for t in techniques]
    sizes = [t[1] for t in techniques]
    colors = [t[2] for t in techniques]
    factors = [t[3] for t in techniques]

    x_pos = list(range(len(techniques)))

    bars = ax.bar(x_pos, sizes, color=colors, edgecolor="black", linewidth=0.8, alpha=0.85)

    for i, (bar, factor, size) in enumerate(zip(bars, factors, sizes)):
        if i == 0:
            txt = f"{size:.0f} MB\n(ref. 1x)"
        else:
            txt = f"{size:.1f} MB\n({factor:.1f}x)"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 3,
                txt, ha="center", va="bottom", fontsize=8, weight="bold")

    # Mark CIM-PCE on the last bar
    ax.annotate(
        "CIM-PCE\nMLA+SW+CLA-2",
        xy=(6, 3.4), xytext=(5.5, 80),
        arrowprops=dict(arrowstyle="->", lw=1.4, color="darkred"),
        fontsize=9, weight="bold", color="darkred",
        ha="center",
        bbox=dict(boxstyle="round,pad=0.3", fc="lightyellow", ec="darkred"),
    )

    ax.set_xticks(x_pos)
    ax.set_xticklabels(names, rotation=10, ha="center", fontsize=8)
    ax.set_ylabel("KV cache size (MB)\nLlama 3 8B, seq_len = 256, BF16", fontsize=9)
    ax.set_title("Proposition 1 - Multiplicative composition of the KV cache: 38x reduction\n"
                 "MHA (128 MB) -> MLA + Sliding 128 + CLA-2 (3.4 MB)",
                 fontsize=11, weight="bold")
    ax.grid(True, axis="y", linestyle="--", alpha=0.4)
    ax.set_ylim(0, 145)

    _save(fig, "fig13_kv_cache_derivation")


def main() -> None:
    print("Generating 3 math diagrams ...")
    fig11_algorithm_1_flowchart()
    print("  OK fig11_algorithm_1_diagram.{png,pdf,svg}")
    fig12_decision_tree_payload_gating()
    print("  OK fig12_decision_tree_payload_gating.{png,pdf,svg}")
    fig13_kv_cache_derivation()
    print("  OK fig13_kv_cache_derivation.{png,pdf,svg}")
    print()
    print("All 3 math diagrams generated at 600 dpi PNG + PDF + SVG.")


if __name__ == "__main__":
    main()
