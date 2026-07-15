#!/bin/bash
# Main benchmark run -> publication/data/analyzer/ (+ tcrdock_pae source predictions).
# Produces <ds>_analyzer_table.tsv for every dataset in samplesheet.csv, merging all
# sequence/structure predictors plus PanPep as a custom model.

DATE=$(date +%Y-%m-%d)

nextflow run mapo9/tcrpmhcbinding -r b58c28c \
    -profile docker \
    -c conf.conf \
    --input samplesheet.csv \
    --models mixtcrpred,ergo2,tabr-bert,t2pmhc-gcn,t2pmhc-gat,tulip-tcr \
    --ergo2_variant vdjdb \
    --custom_model_name panpep \
    --custom_model_training /path/to/panpep/meta_dataset.csv \
    --outdir "${DATE}_t2pmhc-bench_no-tcren_panpep_out" \
    -resume
