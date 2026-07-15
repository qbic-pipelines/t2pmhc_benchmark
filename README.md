
# qbic-pipelines/t2pmhc_benchmark

## Introduction

This pipeline was created for benchmarking t2pmhc with state-of-the-art TCR-pMHC binding predictors.
**The pipeline is NOT INTENDED for users but to showcase the benchmark performed for the t2pmhc publication.**

Three test sets were used in the study.

1. public test set (available here at ```data/test/public_test_set.tsv```). See publication for more information.
2. Immrep23-solution (available [here](https://github.com/justin-barton/IMMREP23/blob/main/data/solutions.csv))
3. epytope-viral (available on Zenodo as described in the [ePytope-TCR manuscript](https://www.sciencedirect.com/science/article/pii/S2666979X25002022?via%3Dihub#sec7.2.3)

## Usage

You can run the pipeline using:

Example `samplesheet.csv`:

```csv
model_name,dataset_name,model_samplesheet,dataset_graphs
gcn,test1,t2pmhc_samplesheet.tsv,/path/to/gcn_graphs
gat,test1,t2pmhc_samplesheet.tsv,/path/to/gat_graphs
mixtcrpred,test1,t2pmhc_samplesheet.csv,
mixtcrpred-pan,test1,mixtcrpred_samplesheet.csv,
ergo2,test1,ergo2_samplesheet.csv,
tabr-bert,test1,tabr-bert_samplesheet.csv,
```

The model_samplesheets must be in the format as expected by the individual models.

For t2pmhc models (gcn, gat), pre-computed graphs must be provided via the `dataset_graphs` column. Graphs can be created using [t2pmhc](https://github.com/mapo9/t2pmhc) directly.

MixTCRpred is licensed and must be installed by the user as described in their [Github](https://github.com/GfellerLab/MixTCRpred). The required location in this pipeline is ```bin/MixTCRpred```. The pretrained models must be stored here: ```bin/MixTCRpred/pretrained_models```</br>
MixTCRpred-pan is not made available by the authors, but must be retrained as described by the authors ([here](https://github.com/GfellerLab/MixTCRpred/issues/7)). The model must be stored here: ```bin/MixTCRpred/pretrained_models/mixtrcpred_pan_epitope.ckpt```

```bash
nextflow run qbic-pipelines/t2pmhc_benchmark \
   -profile <docker/singularity/.../institute> \
   --input samplesheet.csv \
   --outdir <OUTDIR>
```

## Reproducing the publication figures

The `publication/` directory regenerates every manuscript figure from stored prediction tables,
so a clean clone can reproduce the results end-to-end. It bundles the input tables, the scripts
that (re)build them from the published pipelines, and the notebooks that turn them into figures.

```
publication/
├── data.tar.gz   # input tables (extract before running notebooks)
├── scripts/      # regenerate data/ via the pinned, published pipelines
├── notebooks/    # produce the figures from data/
├── lib/          # vendored helpers
└── figures/      # generated figures (svg + png)
```

### 1. Extract the input tables

```bash
cd publication
tar -xzf data.tar.gz     # -> data/
```

### 2. Set up the environment

Package versions are pinned in `publication/requirements.txt`.

### 3. (Optional) Regenerate the input tables

The tables in `data/` are the verbatim outputs of the pinned, published pipelines. To rebuild
them, run the scripts in `publication/scripts/` (each pins its pipeline by GitHub/container
coordinate; see `publication/scripts/PROVENANCE.md` for run details):

| Script | Produces (`data/` subdir) | Pipeline (pin) |
|---|---|---|
| `run_tcrpmhcbinding.sh` | `analyzer/`, `tcrdock_pae/` | `mapo9/tcrpmhcbinding` (`b58c28c`) |
| `run_tcrpmhcbinding_tcren.sh` | `analyzer_tcren/` | `mapo9/tcrpmhcbinding` (`b58c28c`) |
| `run_mpredpan.sh` | `mixtcrpred_pan/` | `qbic-pipelines/t2pmhc_benchmark` (`1.0.0`) |
| `run_panpep.sh` | PanPep predictions | `ghcr.io/qbic-pipelines/panpep:b44ffb1` |

### 4. Run the notebooks

Run each from `publication/notebooks/` (Restart & Run All). Figures are written to
`publication/figures/<name>/`.

| Notebook | Output |
|---|---|
| `calibrate_probabilities.ipynb` | recalibrates stCRDab probabilities — **run before `figure5`** |
| `figure5_benchmark.ipynb` | Figure 5 (benchmark) + result tables + significance tests |
| `figure2_dataset_overview.ipynb` | Figure 2 (dataset overview) |
| `attention_structure_graphs.ipynb` | structure attention panels |
| `figure_attention.ipynb` | GCN attention panels |

## Citations

You can cite the `nf-core` publication as follows:

> **The nf-core framework for community-curated bioinformatics pipelines.**
>
> Philip Ewels, Alexander Peltzer, Sven Fillinger, Harshil Patel, Johannes Alneberg, Andreas Wilm, Maxime Ulysse Garcia, Paolo Di Tommaso & Sven Nahnsen.
>
> _Nat Biotechnol._ 2020 Feb 13. doi: [10.1038/s41587-020-0439-x](https://dx.doi.org/10.1038/s41587-020-0439-x).



**ERGO-II**
> Springer, I. et al. (2021). Contribution of T Cell Receptor Alpha and Beta CDR3, MHC Typing, V and J Genes to Peptide Binding Prediction. *Frontiers in Immunology*, 12, 664514. https://doi.org/10.3389/fimmu.2021.664514

**MIXTCRpred**
> Croce, G. et al. (2024). Deep learning predictions of TCR-epitope interactions reveal epitope-specific chains in dual alpha T cells. *Nature Communications*, 15, 3211. https://doi.org/10.1038/s41467-024-47461-8

**TABR-BERT**
> Zhang, J. et al. (2024). Accurate TCR-pMHC interaction prediction using a BERT-based transfer learning method. *Briefings in Bioinformatics*, 25(1), bbad436. https://doi.org/10.1093/bib/bbad436
