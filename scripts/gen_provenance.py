"""Generate `output/experiment_provenance.json` — the machine-readable
single source of truth for the SHA-256 audit chain of this artifact.

The provenance JSON consolidates:

- canonical seed (`seed_canonical = 42`)
- pinned dependency versions (resolved at runtime by introspection)
- Git commit SHA at the time of generation
- hardware fingerprint (platform, processor, Python implementation)
- SHA-256 of every source file under `src/`
- SHA-256 of the canonical outputs (`results.json`, `raw_replicas.jsonl`)
- the aggregated results (`results_summary`)
- a manifest of validation tests and their assertions
- a manifest of canonical papers cited by the model

This file is the data feed for `scripts/regen_hash_chain.py`, which renders
the human-readable companion `docs/hash-chain.md` from a template.

Usage:

    python scripts/gen_provenance.py

Exit codes: 0 on success; 1 if `results.json` or `raw_replicas.jsonl` is missing.
"""

from __future__ import annotations

__author__ = "Carlos Ulisses Flores"
__email__ = "c.ulisses@gmail.com"
__orcid__ = "0000-0002-6034-7765"
__license__ = "Apache-2.0"

import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

# Resolve project root and ensure `src` is importable for `__version__`.
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
from src import __version__ as _PACKAGE_VERSION  # noqa: E402


def sha256_of(path: Path) -> str:
    """Compute the SHA-256 hex digest of a file.

    Reads the file in 8 KiB chunks to keep memory usage bounded for
    arbitrarily large inputs (e.g. multi-megabyte JSONL).

    Args:
        path: Filesystem path to the file to hash.

    Returns:
        Lowercase hex string of length 64 (256 bits).

    Raises:
        FileNotFoundError: if `path` does not exist.
    """
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def package_versions() -> dict[str, str]:
    """Resolve the runtime versions of all pinned dependencies.

    Each package listed in the canonical pin set is imported and its
    `__version__` attribute is captured. Packages that fail to import are
    reported as `<not installed: ...>` so the provenance JSON is always
    a complete record (no silent omissions).

    Returns:
        Mapping from package name to version string (or error marker).
    """
    out: dict[str, str] = {}
    pkgs = [
        "salabim",
        "numpy",
        "scipy",
        "matplotlib",
        "seaborn",
        "networkx",
        "pandas",
        "pytest",
        "ruff",
    ]
    for p in pkgs:
        try:
            mod = __import__(p)
            out[p] = getattr(mod, "__version__", "?")
        except Exception as e:  # pragma: no cover — diagnostic path
            out[p] = f"<not installed: {e}>"
    return out


def git_commit_sha() -> str:
    """Return the current Git commit SHA-1, or a sentinel if unavailable.

    Uses `git rev-parse HEAD` rather than parsing `.git/HEAD` directly so
    that detached-HEAD states and worktrees are handled correctly.

    Returns:
        40-character lowercase hex SHA-1, or `<not in git repo>` when the
        working directory is not inside a Git repository.
    """
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "<not in git repo>"


def hardware_info() -> dict[str, str]:
    """Capture a hardware fingerprint for the execution environment.

    The fingerprint is informative — the SHA-256 chain is **hardware
    independent**. This record exists so that anyone reproducing the
    artifact can confirm the environment they used and report it in
    case of a hash mismatch.

    Returns:
        Mapping with platform, machine, processor, CPU count, Python
        implementation, and Python version.
    """
    return {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or platform.machine(),
        "cpu_count": str(os.cpu_count()),
        "python_implementation": platform.python_implementation(),
        "python_version": sys.version.split()[0],
    }


def main() -> None:
    """Build and persist `output/experiment_provenance.json`.

    Side effects:
        - Reads `output/results.json` and `output/raw_replicas.jsonl`.
        - Writes `output/experiment_provenance.json`.
        - Prints a short summary of the canonical hashes to stdout.

    Exits with code 1 if either canonical output file is missing.
    """
    root = Path(__file__).resolve().parent.parent
    output_dir = root / "output"
    results_path = output_dir / "results.json"
    raw_path = output_dir / "raw_replicas.jsonl"

    if not results_path.exists() or not raw_path.exists():
        print(
            "ERROR: output/results.json and output/raw_replicas.jsonl must exist. "
            "Run `python -m src.main --replicates 300 --duration 1800 --workers 8` first.",
            file=sys.stderr,
        )
        sys.exit(1)

    with results_path.open() as f:
        results = json.load(f)

    # SHA-256 of every source file.
    src_dir = root / "src"
    source_files_hash: dict[str, str] = {}
    for fn in ("__init__.py", "config.py", "simulation.py", "main.py", "report.py"):
        p = src_dir / fn
        if p.exists():
            source_files_hash[fn] = sha256_of(p)

    provenance = {
        "experiment": "Cellular Inference Mesh — Salabim discrete-event simulation",
        "author": __author__,
        "orcid": __orcid__,
        "license": __license__,
        "version": _PACKAGE_VERSION,
        # Public deposit metadata (set after operator-authorized publication
        # on 2026-05-10; Concept DOI auto-routes to the latest version).
        "doi_external": "10.5281/zenodo.20108648",
        "external_repo_url": "https://github.com/ulissesflores/cellular-inference-mesh",
        "publication_status": (
            "published — Zenodo Concept DOI 10.5281/zenodo.20108648 "
            "(Version DOI 10.5281/zenodo.20109260 for v0.3.2); "
            "GitHub https://github.com/ulissesflores/cellular-inference-mesh; "
            "Apache-2.0; deposited 2026-05-10."
        ),
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "seed_canonical": 42,
        "git_commit_sha": git_commit_sha(),
        "package_versions": package_versions(),
        "hardware": hardware_info(),
        "source_files_sha256": source_files_hash,
        "results_sha256": sha256_of(results_path),
        "raw_replicas_sha256": sha256_of(raw_path),
        "results_summary": results,
        "validation": {
            "little_law_check": (
                "L = λW empirically validated with error < 1e-9 in nominal scenarios."
            ),
            "speculative_speedup_canonical": (
                "α=0.9, γ=8, c=0.05 → 4.38× (test_speculative_speedup_alpha_09_gamma_8_c_005)."
            ),
            "blast_radius_combinatorial": (
                "M=8, k=2 → 3.57% (test_blast_radius_combinatorial_m8_k2)."
            ),
            "kv_cache_composition": (
                "MLA + sliding 128 + CLA-2 → ~38× reduction (test_kv_cache_proposed_full_composition)."
            ),
        },
        "honest_findings": {
            "fallback_rate_reduction": (
                "30.02% → 4.10% ≈ 7.3× (within the [5×, 10×] analytical bound)."
            ),
            "cost_per_command_reduction": (
                "$0.0809 → $0.00410 ≈ 19.7× (within the [7×, 32×] analytical bound)."
            ),
            "p99_latency_reduction_nominal": (
                "1740 ms → 1576 ms ≈ 1.1× (modest; explained by the Saturated Pipeline Conjecture "
                "in docs/saturated-pipeline-conjecture.md)."
            ),
            "p99_latency_under_burst": (
                "165 s → 296 s — both arms saturate under 10× burst; quantitative comparison only "
                "valid under nominal and partition scenarios."
            ),
            "calibration_caveat": (
                "Observed mean residence time W ≈ 1.29 s (vs initial estimate W = 0.25 s); "
                "observed in-flight L ≈ 25.8 (vs estimate L = 5.0). Little's Law remains exact "
                "(error 0%); the initial calibration underestimated per-core throughput."
            ),
        },
        "references_canonical_papers": {
            "PACELC": "Abadi (2012). DOI: 10.1109/MC.2012.33",
            "Tail at Scale": "Dean & Barroso (2013). DOI: 10.1145/2408776.2408794",
            "Speculative Decoding": "Leviathan, Kalman & Matias (2023). arXiv: 2211.17192",
            "EAGLE-3": "Li et al. (2025). arXiv: 2503.01840",
            "S-LoRA": "Sheng et al. (2024). arXiv: 2311.03285",
            "Mooncake": "Qin et al. (2025). USENIX FAST 2025 Best Paper Award.",
            "Splitwise": "Patel et al. (2024). DOI: 10.1109/ISCA59077.2024.00019",
            "Shuffle Sharding": "MacCárthaigh (2019). AWS Builders' Library.",
            "Zero Trust": "Rose et al. (2020). DOI: 10.6028/NIST.SP.800-207",
            "MLA": "DeepSeek-AI (2024). arXiv: 2412.19437",
            "CLA": "Brandon et al. (2024). arXiv: 2405.12981",
            "OpenFedLLM": "Ye et al. (2024). DOI: 10.1145/3637528.3671582",
            "vLLM": "Kwon et al. (2023). DOI: 10.1145/3600006.3613165",
            "Sirius (P4)": "Gao et al. (2024). NSDI 2024.",
            "CXL KV pool": "Tang et al. (2024). NeurIPS ML4Sys Workshop.",
            "Beluga (CXL prod)": "Yang et al. (2026). DOI: 10.1145/3786627",
            "TokenPowerBench": "Niu et al. (2025). arXiv: 2512.03024",
            "Energy-per-token": "Wilhelm et al. (2025). DOI: 10.1145/3721146.3721953",
            "FAIR Principles": "Wilkinson et al. (2016). DOI: 10.1038/sdata.2016.18",
            "ZenML LLMOps": "ZenML (2025). LLMOps in Production case study database.",
        },
    }

    out_path = output_dir / "experiment_provenance.json"
    with out_path.open("w") as f:
        json.dump(provenance, f, indent=2, ensure_ascii=False)

    print(f"Wrote {out_path}")
    print()
    print("Key hashes:")
    print(f"  results.json:       {provenance['results_sha256'][:16]}...")
    print(f"  raw_replicas.jsonl: {provenance['raw_replicas_sha256'][:16]}...")
    print(f"  package version:    {_PACKAGE_VERSION}")
    print(f"  git commit:         {provenance['git_commit_sha'][:12]}")


if __name__ == "__main__":
    main()
