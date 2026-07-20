
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
MixTCRpred-pan is not made available by the authors, but must be retrained as described by the authors ([here](https://github.com/GfellerLab/MixTCRpred/issues/7)). The model must be stored here: ```bin/MixTCRpred/pretrained_models/mixtrcpred_pan_epitope.ckpt```</br>
TABR-BERT ships its own Docker container that may only be used for non-academic use (see their License). The container can be found on the [github repository](https://github.com/freshwind-Bioinformatics/TABR-BERT#1-dockerrecommend). You can plug it into its module (modules/local/tabr-bert/predict_tabr_bert.nf) under the respective comment. 

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

## Other models

The predictors benchmarked against t2pmhc are described below. Each entry pins the
exact implementation used at the time of analysis. Where a tool has since changed
upstream, the commit is preserved via a fork and/or archive so the numbers remain
reproducible.

### ERGO-II

ERGO-II was run using its Python implementation at commit `85d320a`
(`https://github.com/IdoSpringer/ERGO-II`; no tagged release exists, so a commit is
pinned). We applied minor modifications only: automated device selection (CPU/GPU)
and updated paths to the bundled pre-trained models. The vdjdb-based ERGO-II model
was used.

```bash
git clone https://github.com/IdoSpringer/ERGO-II.git
cd ERGO-II && git checkout 85d320a
```

### TABR-BERT

TABR-BERT was run using the official Docker container with the pre-trained
embeddings provided by the authors
(`https://github.com/freshwind-Bioinformatics/TABR-BERT#1-dockerrecommend`). No
source commit is pinned because the tool is distributed as a prebuilt container.
Note the container may only be used for non-academic purposes (see the authors'
license).

### MixTCRpred

MixTCRpred was run using its Python implementation v1.0
(`https://github.com/GfellerLab/MixTCRpred`, tag `v1.0`). MixTCRpred employs a
separate model per peptide, so predictions were performed individually for each
peptide. Unlike the other predictors it reports a percent-rank score, with lower
values indicating higher binding probability; to keep the score convention
consistent across tools these were normalized to `[0, 1]` and inverted
(`1 − normalized score`), so higher values indicate predicted binding.

```bash
git clone --branch v1.0 https://github.com/GfellerLab/MixTCRpred.git
```

### MixTCRpred-pan

MixTCRpred-pan was not publicly available at the time of writing. It was retrained
on the original `pan_training_set` exactly as described by the authors (see
`https://github.com/GfellerLab/MixTCRpred/issues/7`). As for MixTCRpred, the
percent-rank score was normalized to `[0, 1]` and inverted.

### TULIP-TCR

TULIP-TCR was run using its official implementation at commit `798fab9`
(`https://github.com/barthelemymp/TULIP-TCR`) with the pre-trained weights released
by the authors.

```bash
git clone https://github.com/barthelemymp/TULIP-TCR.git
cd TULIP-TCR && git checkout 798fab9
```

### TCRen

TCRen was run using its R implementation at commit
`b85f19a54ac38c7538bff6c2eba1c896ce1be5be`. Because the upstream repository
(`antigenomics/tcren-ms`) has since been rewritten from R to Python, renamed to
`antigenomics/tcren`, and moved its default branch to the Python version (the R
code survives only under the git tag `legacy-r-1.0`), we saved a copy of the exact
commit used here as a fork (`https://github.com/mapo9/tcren-ms`) and as an archive
(doi:10.5281/zenodo.11129800). The commands below still clone the original
repository.

Each TCR-pMHC complex was scored with TCRen's residue-level statistical potential,
using the **same TCRdock-predicted structures that t2pmhc uses**, so the comparison
is on identical inputs. TCRen expects a specific input format, so we converted the
TCRdock structures: each single-chain TCRdock PDB was relabelled by re-assigning
its residues to the MHC, peptide, TCRα and TCRβ entities based on the chain-segment
boundaries, rewriting the PDB chain-identifier column accordingly, and inserting
the corresponding chain breaks, producing TCRen-compatible input structures. TCRen
scores were then inverted so that **higher values indicate more favourable
predicted recognition**, consistent with the other predictors.

```bash
git clone https://github.com/antigenomics/tcren-ms.git
cd tcren-ms && git checkout b85f19a54ac38c7538bff6c2eba1c896ce1be5be
```

As run for this benchmark, the conversion and TCRen scoring are executed by
`publication/scripts/run_tcrpmhcbinding_tcren.sh` (via the pinned pipeline
`mapo9/tcrpmhcbinding@b58c28c` under the Docker profile); the score inversion is
applied in `publication/notebooks/figure5_benchmark.ipynb`.

### PanPep

PanPep was run using its Python implementation at commit `b44ffb1`
(`https://github.com/bm2-lab/PanPep`) in the zero-shot setting with the pre-trained
models provided by the authors.

```bash
git clone https://github.com/bm2-lab/PanPep.git
cd PanPep && git checkout b44ffb185a5c5fe177bc1e0a77453d6d55cf5e14
```

### TCRdock-PAE

TCRdock-PAE is a PAE-as-classifier baseline. The mean interface PAE from the
TCRdock-predicted complex (`https://github.com/phbradley/TCRdock`, tag `v2.0.0`) was
used directly as a discriminative score. Because lower PAE indicates higher
predicted confidence, the **negated mean PAE** was used so that higher values
correspond to predicted binding. In this repo the PAE values are consumed in
`publication/notebooks/figure5_benchmark.ipynb` (treated as an inverted model).

```bash
git clone https://github.com/phbradley/TCRdock.git
cd TCRdock && git checkout v2.0.0
```

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

**TCRen**
> Karnaukhov, V. et al. (2024). Structure-based prediction of T cell receptor recognition of unseen epitopes using TCRen. *Nature Computational Science*, 4(7), 510–521. https://doi.org/10.1038/s43588-024-00653-0

**TULIP-TCR**
> Meynard-Piganeau, B. et al. (2024). TULIP: A transformer-based unsupervised language model for interacting peptides and T cell receptors that generalizes to unseen epitopes. *Proceedings of the National Academy of Sciences*, 121(24), e2316401121. https://doi.org/10.1073/pnas.2316401121

**PanPep**
> Gao, Y. et al. (2023). Pan-Peptide Meta Learning for T-cell receptor–antigen binding recognition. *Nature Machine Intelligence*, 5, 236–249. https://doi.org/10.1038/s42256-023-00619-3

**TCRdock**
> Bradley, P. (2023). Structure-based prediction of T cell receptor:peptide-MHC interactions. *eLife*, 12, e82813. https://doi.org/10.7554/eLife.82813
