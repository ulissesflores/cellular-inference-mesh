# Contributing

> [!IMPORTANT]
> This repository is a published scientific software artifact. All contributions
> must preserve **FAIR replicability** (Wilkinson et al., 2016) and the
> **SHA-256 hash chain** documented in [`docs/hash-chain.md`](./docs/hash-chain.md).
> Pull requests that break bit-parity without coherently updating the hash chain
> will be closed.

## Quick start

```bash
git clone https://github.com/ulissesflores/cellular-inference-mesh.git
cd cellular-inference-mesh
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest -q                                         # 53 tests, ~5.5 s
shasum -a 256 output/results.json                 # must match docs/hash-chain.md
```

## What we accept

| Type | Requirements |
|---|---|
| **Bug fix** | Reproduction steps + commit hash where the bug was introduced. A test that exhibits the bug must fail before the fix and pass after. |
| **Simulation variant** | A new `--scenario` or `--arm` in `src/main.py`. Must regenerate figures and update `output/experiment_provenance.json`. |
| **Theorem extension** | Formal statement + proof in `docs/proofs.md` or `docs/theorem.md`. Computational verification script in `scripts/`. |
| **New reference** | DOI mandatory whenever one exists. Verify via [Crossref](https://search.crossref.org/) and [OpenAlex](https://openalex.org/) before submitting. |
| **Documentation improvement** | Renders correctly on GitHub (test math, Mermaid diagrams, callouts). |

## What we reject

- Any change that modifies the SHA-256 of `output/results.json` or `output/raw_replicas.jsonl` without coherently updating `docs/hash-chain.md`, `output/experiment_provenance.json`, and the version in `CHANGELOG.md`.
- References missing a DOI when one exists in the source databases.
- Stylistic refactors with no measurable benefit (the maintainer's principle: *surgical changes — touch only what's asked*).
- Replacement of inline LaTeX commands with "prettier" Unicode that loses precision (e.g., $\alpha$ → α inside an equation that breaks rendering).

## FAIR checklist for scientific PRs

- [ ] **Findable** — `CITATION.cff` and `.zenodo.json` are kept up to date.
- [ ] **Accessible** — License preserved (Apache-2.0). No paywalled dependencies introduced.
- [ ] **Interoperable** — Open formats only (JSON, CSV, Markdown, PNG/PDF/SVG).
- [ ] **Reusable** — Module docstrings, type hints, and a runnable example are present.

## Replication checklist for any code change

- [ ] `pytest -q` passes (53/53 currently).
- [ ] `shasum -a 256 output/results.json output/raw_replicas.jsonl` matches `docs/hash-chain.md`, or hashes are updated coherently via `scripts/gen_provenance.py` + `scripts/regen_hash_chain.py`.
- [ ] `python scripts/pareto_proof.py` confirms Theorem still holds.
- [ ] Figures regenerated via `python -m src.report` if data changed.
- [ ] `CHANGELOG.md` entry added under `[Unreleased]` or the appropriate version.

## Commit message convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

| Prefix | Use for |
|---|---|
| `feat:` | New feature, simulation variant, or theorem |
| `fix:` | Bug fix |
| `docs:` | Documentation only |
| `sim:` | Simulation parameter or scenario change |
| `proof:` | Mathematical proof or theorem extension |
| `chore:` | Tooling, CI, dependencies |
| `test:` | Test additions or improvements |

If a commit was AI-assisted, document this clearly in the commit body.

## Issue templates

Structured reports use GitHub issue forms:

- 🐛 [Bug report](.github/ISSUE_TEMPLATE/bug_report.yml) — reproducibility failures, incorrect outputs.
- 💡 [Feature request](.github/ISSUE_TEMPLATE/feature_request.yml) — new analyses, theorem extensions, simulation variants.

## Code of Conduct

This project follows the [Contributor Covenant 2.1](./CODE_OF_CONDUCT.md). Enforcement contact: c.ulisses@gmail.com.

## Scientific contact

For scientific questions or collaboration inquiries, please cite this work and contact the author via email or [ORCID 0000-0002-6034-7765](https://orcid.org/0000-0002-6034-7765).
