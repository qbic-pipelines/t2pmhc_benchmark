#!/bin/bash
# MixTCRpred-pan run -> publication/data/mixtcrpred_pan/. Produces
# <ds>/mixtcrpred-pan_predicted.tsv (identifier + binder_prob merged into the figure).



DATE=$(date +%Y-%m-%d)

nextflow run qbic-pipelines/t2pmhc_benchmark -r 1.0.0 \
    -profile docker \
    --input samplesheet_mpredpan.csv \
    --outdir "${DATE}_mpredpan_out" \
    -resume
