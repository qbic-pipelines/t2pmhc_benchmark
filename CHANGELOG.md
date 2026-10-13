# nf-core/t2pmhc_benchmark: Changelog

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v1.2.2 - [2026-10-13]

### Added
- `Evaluation protocol` section in the README documenting the mean per-peptide AUC, the
  per-peptide bootstrap confidence intervals, the paired Wilcoxon signed-rank tests with
  Holm-Bonferroni correction and the rank-biserial effect sizes, and the per-competitor
  leakage removal
- `Two evaluation settings` subsection distinguishing the cross-validation used for
  hyperparameter search and the ablation experiments in the main package from the
  per-peptide benchmark evaluation implemented here
- Reciprocal link to the main package, qbic-pipelines/t2pmhc

### Changed
- `manifest.version` set to the release version; it had remained at the template default
  of `0.0.1dev`
- Documentation only: pipeline code is unchanged

## v0.0.1dev - [date]

Initial release of nf-core/t2pmhc_benchmark, created with the [nf-core](https://nf-co.re/) template.

### `Added`

### `Fixed`

### `Dependencies`

### `Deprecated`
