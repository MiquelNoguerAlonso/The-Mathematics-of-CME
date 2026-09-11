# The Mathematics of CME

**Miquel Noguer i Alonso**  
Artificial Intelligence Finance Institute (AIFI)

**Paper DOI:** [10.5281/zenodo.22700054](https://doi.org/10.5281/zenodo.22700054)

Futures matching, implied liquidity, opening auctions, settlement variation, collateral, margin, options exercise, physical delivery, and clearing loss allocation.

[Read the paper](The_Mathematics_of_CME.pdf) · 34 pages · 9 reproducible scientific figures

## Contents

| File or directory | Contents |
| --- | --- |
| [The_Mathematics_of_CME.pdf](The_Mathematics_of_CME.pdf) | Compiled paper |
| [The_Mathematics_of_CME.tex](The_Mathematics_of_CME.tex) | Main LaTeX document |
| `sections/` | Manuscript sections and appendix |
| `references.bib`, `The_Mathematics_of_CME.bbl` | Bibliography and compiled bibliography |
| `figures/` | 9 PNG figures included for compilation |
| `reproduce.py` | Numerical examples, verification, and figure generation |
| `results.json` | Recorded numerical results |
| `environment.json`, `requirements.txt` | Recorded Python environment and dependencies |
| `CITATION.cff` | Citation metadata for this paper |
| `MANIFEST_SHA256.txt` | File checksums |

## Build the paper

Use pdfLaTeX and BibTeX, or compile with TeX Live and `latexmk`:

```sh
latexmk -pdf -interaction=nonstopmode -halt-on-error The_Mathematics_of_CME.tex
```

For Overleaf, import this repository's downloaded ZIP, select `The_Mathematics_of_CME.tex` as the main document, and use pdfLaTeX. The supplied figures allow compilation without Python or shell escape. Citations use `natbib` and `plainnat`.

## Reproduce the examples and figures

Use Python 3 in an environment with the supplied dependencies:

```sh
python -m pip install -r requirements.txt
python reproduce.py
```

The script regenerates the figures and numerical ledger. It checks the declared examples and raises an error if a check fails. The recorded Python version is in `environment.json`. All examples use synthetic inputs; no external market data, trading credentials, or network access is needed for reproduction after dependency installation.

To verify the files as committed, before regenerating outputs:

```sh
sha256sum -c MANIFEST_SHA256.txt
```

## Scope

The allocation and opening routines implement the models declared in the paper. The scenario-risk functional is an independent illustrative model, not a production SPAN or SPAN 2 calculator. Product and venue rules are cited in the paper, with consultation dates. This is a mathematical research and reproduction package; model assumptions and operational boundaries are stated in the manuscript.

## Cite

Miquel Noguer i Alonso (2026). *The Mathematics of CME*. DOI: [10.5281/zenodo.22700054](https://doi.org/10.5281/zenodo.22700054).
