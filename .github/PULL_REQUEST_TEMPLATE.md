<!-- Thank you for the contribution. This software is a published scientific
     artifact under a SHA-256 hash chain — every change must preserve or
     coherently update the chain. Pull requests that break bit-parity without
     updating docs/hash-chain.md, output/experiment_provenance.json, and
     CHANGELOG.md will be closed. -->

## Summary

<!-- One paragraph: what changed and why. Cite the relevant paper section,
     docs/proofs.md proposition, or issue. -->

## Related issue / proposition

<!-- Closes #N, addresses Proposition K, etc. -->

## Type of change

<!-- Tick all that apply. -->

- [ ] Bug fix (non-breaking, no impact on the SHA-256 hash chain)
- [ ] Bug fix (breaking — regenerates `output/results.json`)
- [ ] New simulation scenario / arm
- [ ] New theorem, proposition, or extension of Theorem
- [ ] New external-architecture comparison
- [ ] Documentation improvement
- [ ] Reproducibility / FAIR improvement
- [ ] Tooling / CI

## Reproducibility checklist

- [ ] `pytest -q` passes (53/53 currently)
- [ ] `shasum -a 256 output/results.json output/raw_replicas.jsonl` matches `docs/hash-chain.md`, **or** the hashes were regenerated coherently via `scripts/gen_provenance.py` + `scripts/regen_hash_chain.py`
- [ ] `python scripts/pareto_proof.py` confirms Theorem still holds
- [ ] `python scripts/saturated_pipeline_plot.py` regenerates the conjecture validation when relevant
- [ ] Figures regenerated via `python -m src.report` and `python scripts/figs_math_diagrams.py` if data changed
- [ ] `CHANGELOG.md` entry added under `[Unreleased]` or the appropriate version

## FAIR checklist (scientific PRs)

- [ ] **Findable** — `CITATION.cff` and `.zenodo.json` are kept up to date
- [ ] **Accessible** — License preserved (Apache-2.0); no paywalled dependencies introduced
- [ ] **Interoperable** — Open formats only (JSON, CSV, Markdown, PNG/PDF/SVG)
- [ ] **Reusable** — Module docstrings, type hints, and a runnable example are present

## References (DOI mandatory when one exists)

<!-- One per line, AGTU author-date format. Verify via Crossref/OpenAlex
     before merging. -->

## AI-assistance disclosure

<!-- If this PR was AI-assisted, document the tool, scope, and human review
     performed (per ICMJE 2024 author responsibility guidance). -->
