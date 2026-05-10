# Paper of record

This directory hosts the **paper artifacts** of MIT-504 (AGTU master's thesis), in two parallel sets.

## Submitted to AGTU platform (canonical, official)

These are the files the author submitted to the AGTU institutional platform on 2026-05-10:

- [`Addverb.pdf`](./Addverb.pdf) — **Official submission PDF** (1.1 MB, 51 pages, Microsoft Word export)
- [`Addverb.docx`](./Addverb.docx) — **Official submission source** (Word document hand-edited from the build pipeline output, 6.0 MB)

```text
SHA-256 (canonical submission)
2073f4cfc73e39361db7955ad4343d97484973c199c7f798e0d2f212808d037c  Addverb.pdf
91c621a56b48250393f7508603885000cfc09171e56e9de886f19fa0d497903f  Addverb.docx
```

These files carry the AGTU formal cover (logo "AGTU — The Global University"), Times New Roman 12pt unified, double line spacing + justified body via `pPrDefault`, page numbers in the top-right corner, 44 references with hanging indent, 3 native Word footnotes, and 11.348 words. They are conformant with the AGTU style guide on every dimension verified.

## Build-pipeline output (auxiliary, reproducible)

These are the files emitted by [`scripts/build_paper.py`](../../../scripts/build_paper.py) from the canonical Markdown source. They are kept here for full reproducibility of the paper from `paper-final.md` alone:

- [`paper-final.md`](./paper-final.md) — Markdown source (~515 lines, AGTU-grade pt-BR)
- [`paper-final.pdf`](./paper-final.pdf) — PDF emitted by the pipeline (LibreOffice render of the DOCX)
- [`paper-final.docx`](./paper-final.docx) — DOCX emitted by the pipeline (TechGrowth template + python-docx injection)

The pipeline DOCX/PDF differ from `Addverb.{pdf,docx}` only in cover layout (TechGrowth template logo vs AGTU oficial logo) and minor Word-vs-LibreOffice rendering details. The body content (text, equations, tables, figures, references) is identical.

## Audit notes

- [`AUDIT-2026-05-10.md`](./AUDIT-2026-05-10.md) — granular audit (7 rubric dimensions, evidence-based scoring, typographic findings, patch history v0.3.2 → v0.3.3 → v0.3.4)

## Reproducibility

The Markdown source corresponds to the v0.3.2 deposit on Zenodo ([10.5281/zenodo.20109260](https://doi.org/10.5281/zenodo.20109260)). The Concept DOI [10.5281/zenodo.20108648](https://doi.org/10.5281/zenodo.20108648) always resolves to the latest version. Public repository: [github.com/ulissesflores/cellular-inference-mesh](https://github.com/ulissesflores/cellular-inference-mesh).

To regenerate the pipeline DOCX/PDF from the Markdown source:

```bash
cd 08-entrega/codigo
.venv/bin/python ../scripts/build_paper.py
soffice --headless --convert-to pdf ../artigo/paper-final.docx --outdir ../artigo/
```

## Citing the paper

Cite the software (this repository), which carries the canonical Zenodo DOI. The paper itself is not separately deposited.

```bibtex
@software{flores_cellular_inference_mesh_2026,
  author    = {Flores, Carlos Ulisses},
  title     = {Cellular Inference Mesh: Salabim DES of Edge-Cloud LLM Inference under PACELC Saturation},
  year      = 2026,
  month     = may,
  publisher = {Zenodo},
  version   = {0.3.2},
  doi       = {10.5281/zenodo.20108648},
  url       = {https://doi.org/10.5281/zenodo.20108648},
  orcid     = {0000-0002-6034-7765}
}
```
