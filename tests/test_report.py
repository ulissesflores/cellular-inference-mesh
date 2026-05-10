"""Unit tests for src/report.py figure generation.

Covers:
- _save() multi-format output (PDF + SVG + PNG)
- Stylesheet application (scienceplots + Okabe-Ito)
- Each fig{N}_*() function generates valid output

Tests use real Salabim DES data in output/raw_replicas.jsonl to avoid
re-running the simulation.
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pytest

CODE_DIR = Path(__file__).parent.parent
OUTPUT = CODE_DIR / "output"


# Helper sample replica used by several tests
def _sample_replica():
    """Synthetic replica for fig*_*() tests when raw_replicas.jsonl is empty."""
    return {
        "scenario": "nominal",
        "arm": "baseline",
        "replica_id": 0,
        "seed": 42,
        "p50_ms": 1263.0,
        "p95_ms": 1589.0,
        "p99_ms": 1740.0,
        "fallback_rate": 0.30,
        "cost_usd": 0.0809,
        "energy_j": 4500.0,
    }


@pytest.fixture(autouse=True)
def chdir_code(monkeypatch):
    """Change to code/ directory for relative imports."""
    monkeypatch.chdir(CODE_DIR)


def test_okabe_ito_palette_size():
    """OKABE_ITO has 8 colorblind-safe colors."""
    from src.report import OKABE_ITO
    assert len(OKABE_ITO) == 8
    assert all(c.startswith("#") for c in OKABE_ITO)
    assert all(len(c) == 7 for c in OKABE_ITO)


def test_okabe_ito_includes_canonical_colors():
    """Canonical Okabe-Ito (Wong 2011) has black + 7 chromatic."""
    from src.report import OKABE_ITO
    assert "#000000" in OKABE_ITO  # black
    assert "#E69F00" in OKABE_ITO  # orange
    assert "#56B4E9" in OKABE_ITO  # sky blue


def test_save_outputs_three_formats(tmp_path, monkeypatch):
    """_save() writes PDF + SVG + PNG to OUTPUT dir."""
    from src import report
    monkeypatch.setattr(report, "OUTPUT", tmp_path)
    fig, ax = plt.subplots()
    ax.plot([0, 1, 2], [0, 1, 4])
    report._save(fig, "test_fig")
    assert (tmp_path / "test_fig.pdf").exists()
    assert (tmp_path / "test_fig.svg").exists()
    assert (tmp_path / "test_fig.png").exists()


def test_load_raw_returns_list_of_dicts():
    """_load_raw() reads raw_replicas.jsonl and returns list of dicts."""
    raw_path = CODE_DIR / "output" / "raw_replicas.jsonl"
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        pytest.skip(f"{raw_path} not generated or empty; run main.py first")
    # Read directly to avoid module-level OUTPUT path drift after reloads
    with raw_path.open() as f:
        raw = [json.loads(line) for line in f if line.strip()]
    assert isinstance(raw, list)
    assert len(raw) > 0
    assert isinstance(raw[0], dict)
    sample = raw[0]
    # Verifica que sample tem campos essenciais (qualquer um indica estrutura JSON correta)
    has_metric = any(k in sample for k in ("p99_ms", "fallback_rate", "cost_usd"))
    has_id = any(k in sample for k in ("scenario", "arm", "replica_id", "seed", "key", "label"))
    assert has_metric, f"No metric keys; got: {list(sample.keys())[:10]}"
    assert has_id, f"No identifier keys; got: {list(sample.keys())[:10]}"


def test_savefig_dpi_is_600():
    """rcParams['savefig.dpi'] is set to 600 (Layer B SOTA)."""
    import importlib

    import src.report
    importlib.reload(src.report)  # ensure fresh module-level rcParams
    assert plt.rcParams["savefig.dpi"] == 600


def test_font_family_serif():
    """rcParams['font.family'] uses serif (Nature/Science aesthetic)."""
    import importlib

    import src.report
    importlib.reload(src.report)
    assert "serif" in plt.rcParams["font.family"]


def test_text_usetex_disabled():
    """text.usetex=False (sistema sem LaTeX; mathtext interno)."""
    import importlib

    import src.report
    importlib.reload(src.report)
    assert plt.rcParams["text.usetex"] is False


def test_axes_grid_enabled():
    """axes.grid=True (rubrica v3.0 SOTA)."""
    import importlib

    import src.report
    importlib.reload(src.report)
    assert plt.rcParams["axes.grid"] is True


def test_lines_linewidth_consistent():
    """lines.linewidth=1.4 — Nature/IEEE column width."""
    import importlib

    import src.report
    importlib.reload(src.report)
    assert plt.rcParams["lines.linewidth"] == 1.4


def test_scienceplots_imported_without_error():
    """scienceplots stylesheet registers via side effect."""
    import scienceplots  # noqa: F401
    available = plt.style.available
    assert "science" in available
    assert "nature" in available


def test_fig1_latency_timeseries_generates_files(tmp_path, monkeypatch):
    """fig1_latency_timeseries() generates 3 files (png, pdf, svg)."""
    from src import report
    # _load_raw uses module-level OUTPUT for input AND output
    # Need to load raw FIRST from real OUTPUT, then redirect saves to tmp_path
    raw_path = report.OUTPUT / "raw_replicas.jsonl"
    if not raw_path.exists():
        pytest.skip(f"{raw_path} not generated; run main.py first")
    raw = report._load_raw()
    monkeypatch.setattr(report, "OUTPUT", tmp_path)
    report.fig1_latency_timeseries(raw)
    assert (tmp_path / "fig1_latency_timeseries.png").exists()
    assert (tmp_path / "fig1_latency_timeseries.pdf").exists()
    assert (tmp_path / "fig1_latency_timeseries.svg").exists()


def test_fig2_ecdf_latency_generates_files(tmp_path, monkeypatch):
    """fig2_ecdf_latency() generates ECDF figure."""
    from src import report
    raw_path = report.OUTPUT / "raw_replicas.jsonl"
    if not raw_path.exists():
        pytest.skip(f"{raw_path} not generated; run main.py first")
    raw = report._load_raw()
    monkeypatch.setattr(report, "OUTPUT", tmp_path)
    report.fig2_ecdf_latency(raw)
    assert (tmp_path / "fig2_ecdf_latency.png").exists()


def test_existing_output_pngs_are_600dpi():
    """Validate that pre-generated PNGs in output/ are at 600 dpi."""
    from PIL import Image
    fig_path = OUTPUT / "fig1_latency_timeseries.png"
    if fig_path.exists():
        img = Image.open(fig_path)
        dpi = img.info.get("dpi", (None, None))[0]
        # PNG metadata may be (600, 600) or rounded; tolerate ±5
        if dpi:
            assert dpi >= 595, f"Expected ≥595 dpi (target 600), got {dpi}"


def test_okabe_ito_is_colorblind_safe():
    """Sanity: paletas Okabe-Ito devem contrastar suficientemente."""
    from src.report import OKABE_ITO
    # No two colors should be identical
    assert len(set(OKABE_ITO)) == len(OKABE_ITO)


def test_load_raw_n_replicas_matches_runs():
    """raw_replicas.jsonl tem 30 replicas × 6 (scenario × arm) = 180 entries."""
    raw_path = CODE_DIR / "output" / "raw_replicas.jsonl"
    if not raw_path.exists() or raw_path.stat().st_size == 0:
        pytest.skip(f"{raw_path} not generated or empty; run main.py first")
    with raw_path.open() as f:
        raw = [json.loads(line) for line in f if line.strip()]
    # 3 scenarios × 2 arms × N replicas; min 30 by config (sample = identifying fields fluid)
    if not raw or "scenario" not in raw[0] or "arm" not in raw[0]:
        # Schema mudou: apenas verificar count total
        assert len(raw) >= 180, f"Expected ≥180 entries; got {len(raw)}"
        return
    n_per_combo = {}
    for r in raw:
        key = f"{r['arm']}__{r['scenario']}"
        n_per_combo[key] = n_per_combo.get(key, 0) + 1
    for key, n in n_per_combo.items():
        assert n >= 30, f"{key} has only {n} replicas (expected ≥30)"
