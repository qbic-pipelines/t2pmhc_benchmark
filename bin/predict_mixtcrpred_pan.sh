#!/bin/bash


# Parse flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -m|--mpred_path) MPRED_PATH="$2"; shift ;;
        -i|--input) INPUT="$2"; shift ;;
        -o|--output) OUTPUT="$2"; shift ;;
        -c|--checkpoint) CHECKPOINT="$2"; shift ;;
        --model_name) MODEL_NAME="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [[ -z "$INPUT" ]]; then
    echo "Error: --input/-i is required."
    exit 1
fi


python ${MPRED_PATH}/predict_mpred_pan.py \
    --input "$INPUT" \
    -o "$OUTPUT" \
    -c "$CHECKPOINT" \
    --model_name "$MODEL_NAME"