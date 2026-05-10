# Changelog

All notable changes to this project follow [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [0.3.2] — 2026-05-10

### Fixed

- `pyproject.toml`, `CITATION.cff`, `codemeta.json`, `.zenodo.json`, `src/__init__.py` and Docker/BibTeX references in `README.md` synchronized to `0.3.2` (previously stale at `0.3.0` despite v0.3.1 tag).
- Ruff configuration tightened with `per-file-ignores` for legitimate scientific patterns (`L_edge`, `L_cloud`, `M`, `k` math variables; matplotlib chained calls; notebook import positions); `ruff check .` now passes with zero errors, unblocking the GitHub Actions CI pipeline.
- `figs_math_diagrams.py` Figure 12 (decision tree) banner re-laid to avoid overlap with payload-decision blocks.
- `README.md` reproducibility example references the dynamic SHA-256 chain in `docs/hash-chain.md` (no hard-coded hashes drift).

## [0.3.1] — 2026-05-10

- Zenodo DOI `10.5281/zenodo.20108649` integrated into `CITATION.cff`, `.zenodo.json`, `README.md` and `colab/replication.ipynb`.

## [0.3.0] — 2026-05-09

> [!IMPORTANT]
> Canonical release. SHA-256 hashes locked. Bit-parity verifiable via `pytest test_reproducibility`.

### Added

- **Parametric variation per replica.** `src/main.py` now samples per-replica parameters (`lambda_voice_eps`, `n_agvs`, `partition_inject_pct`, `W_jitter_pct`) from realistic operational ranges via isolated `random.Random(42 + i)`. New fields `*_low` / `*_high` in `ExperimentConfig` define the ranges. Range design is Jensen-safe — narrow enough that means converge to the canonical 30-replica run within 5% across 24 metric-combos.
- **Two-panel figure layouts** for Fig 4 (ECDF p99) and Fig 5 (PACELC box plot) — separate scales for nominal/partition (linear zoom 1500–1850 ms) and burst (linear 100k–400k ms). Avoids log-scale collapse that hid baseline×proposed separation.
- **Five paper-ready figures** (`figura-01-speculative-speedup.png` through `figura-05-pacelc-boxplot.png`) renumbered and renamed in editorial order.
- **`pyproject.toml`** — PEP 621 build configuration; `pip install -e .` now supported.
- **`.zenodo.json`** — Zenodo deposit metadata (takes precedence over CFF for related identifiers).
- **`codemeta.json`** — Cross-platform research software metadata (CodeMeta 2.0 / JSON-LD).
- **`CHANGELOG.md`** — this file.
- **`.github/workflows/release.yml`** — automated GitHub Release on `v*.*.*` tag (triggers Zenodo webhook).
- **`08-entrega/scripts/build_paper.py`** — Abordagem B implementation: copies `TechGrowth.docx` template, edits 5 cover strings (paragraphs 3, 4, 12, 13, 16), parses `paper-final.md` via mistune AST, injects content with proper styles + APA-7 table borders + hanging-indent references + display-math PNGs.

### Changed

- **`docs/` files renamed** to kebab-case lowercase (FAIR4RS / pyOpenSci convention; matches astropy, scikit-learn, numpy):
  - `ALGORITHM-1.md` → `algorithm.md`
  - `THEOREM-1.md` → `theorem.md`
  - `HASH-CHAIN.md` → `hash-chain.md`
  - `PROOFS.md` → `proofs.md`
  - `CONJECTURE-PIPELINE-SATURADO.md` → `saturated-pipeline-conjecture.md`
- **Figure scripts** strip embedded titles (APA-7 §7.22-7.36): `set_title("")` in `report.py` and the math diagram scripts.
- **`hash-chain.md`** updated with v0.3.0 SHA-256 values (results.json, raw_replicas.jsonl, source files).
- **Colab notebook** (`colab/replication.ipynb`) updated cells 6, 8, 16 with 300-replica parametric configuration and new expected hashes.

### Fixed

- **`__version__`** in `src/__init__.py` synchronized to `"0.3.0"` (was stale at `"0.1.0"`).
- **`ruff` pinned** to `0.5.7` (was `>=0.5`).

## [0.2.0] — 2026-05-08

### Added

- 30-replica canonical Monte-Carlo simulation (3 scenarios × 2 arms × 1800 simulated seconds).
- 5 markdown documentation files in `docs/` covering Theorem, Algorithm 1, 9 propositions, Saturated Pipeline Conjecture, and SHA-256 hash chain.
- 53 pytest tests across `test_main.py`, `test_simulation.py`, `test_math.py`, `test_report.py`.
- Dockerfile (`python:3.14-slim`) for reproducible builds.
- 14 figures (10 simulation + 3 math diagrams + 1 conjecture validation plot) at 600 dpi.

## [0.1.0] — 2026-05-07

### Added

- Initial Salabim DES implementation of the Cellular Inference Mesh.
- Bit-parity reproducibility under `seed_canonical = 42`.
- CITATION.cff (CFF v1.2.0).
- README.md with reproducibility instructions.
- Apache-2.0 LICENSE.

[0.3.0]: https://github.com/ulissesflores/cellular-inference-mesh/releases/tag/v0.3.0
[0.2.0]: https://github.com/ulissesflores/cellular-inference-mesh/releases/tag/v0.2.0
[0.1.0]: https://github.com/ulissesflores/cellular-inference-mesh/releases/tag/v0.1.0
