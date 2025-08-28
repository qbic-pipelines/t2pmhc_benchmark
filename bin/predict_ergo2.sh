#!/bin/bash
# Wrapper script for ERGO-II Predict.py

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Store the current working directory
WORK_DIR="$(pwd)"

# Convert the second argument (input file) to absolute path
# Keep output file (third argument) as relative to work directory
args=()
for i in $(seq 1 $#); do
    arg="${!i}"
    if [[ $i -eq 2 && -f "${arg}" ]]; then
        # Second argument is input file - make absolute
        args+=("$(realpath "${arg}")")
    elif [[ $i -eq 3 ]]; then
        # Third argument is output file - make absolute to work dir
        args+=("${WORK_DIR}/${arg}")
    else
        # All other arguments stay as-is
        args+=("${arg}")
    fi
done

# Change to ERGO-II directory
cd "${SCRIPT_DIR}/ERGO-II"

# Run the script
python Predict.py "${args[@]}"