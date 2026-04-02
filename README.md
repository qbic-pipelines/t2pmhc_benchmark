
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
