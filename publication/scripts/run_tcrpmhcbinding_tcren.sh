#!/bin/bash
# TCRen run -> publication/data/analyzer_tcren/. tcren + t2pmhc variants on the samplesheet
# with FLCMKALLL dropped from iggytop_unseen (FLCMKALLL triggers an NPE in mir's
# HitList.getBestHit, emptying markup.txt and failing the downstream R script; every other
# predictor handles it fine and runs via run_tcrpmhcbinding.sh on the full samplesheet).

set -euo pipefail


DATE=$(date +%Y-%m-%d)

nextflow run mapo9/tcrpmhcbinding -r b58c28c \
    -profile docker \
    -c conf.conf \
    --input samplesheet_no_FLCMKALLL.csv \
    --models tcren,t2pmhc-gcn,t2pmhc-gat \
    --outdir "${DATE}_t2pmhc-bench_tcren-only_out" \
    -resume
