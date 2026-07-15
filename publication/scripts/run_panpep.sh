#!/usr/bin/env bash
# PanPep zero-shot custom-model predictions. Driven by panpep_run_all.py, which reads the
# benchmark samplesheet, runs the pinned container per dataset, and writes
# <basename>_panpep.tsv (input table + binding_score). Those TSVs are fed back into
# run_tcrpmhcbinding.sh via --custom_model_name panpep.
#
# Uses the PUBLISHED, pinned container image (no local model install):
#   docker run ghcr.io/qbic-pipelines/panpep:b44ffb1 panpep --learning_setting zero-shot ...
# The image bakes both former runtime workarounds (protobuf<4, CPU-rebaked .pkl files).
set -euo pipefail
exec python "$(dirname "$0")/panpep_run_all.py"
