#!/usr/bin/env python3

import argparse
import numpy as np
import pandas as pd
from Bio.PDB import PDBParser
from tqdm import tqdm
import sys
import os


DOMAIN_ORDER = ["mhc", "tcra", "tcrb", "cdr3a", "cdr3b"]


# -----------------------------
# Helpers
# -----------------------------
def get_region_indices(full_seq, subseq):
    start = full_seq.find(subseq)
    if start == -1:
        raise ValueError(f"Subsequence not found: {subseq}")
    return np.arange(start, start + len(subseq), dtype=np.int64)


def extract_ca_coords(pdb_file):
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("complex", pdb_file)

    coords = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if "CA" in residue:
                    coords.append(residue["CA"].coord)

    if len(coords) == 0:
        raise ValueError(f"No Cα atoms found in {pdb_file}")

    return np.asarray(coords, dtype=np.float32)


def build_indices(metadata_row):
    # Ensure chain sequences exist
    if "mhc_seq" not in metadata_row:
        for chain, idx in [
            ("mhc_seq", 0),
            ("peptide", 1),
            ("tcra_seq", 2),
            ("tcrb_seq", 3),
        ]:
            metadata_row[chain] = metadata_row["target_chainseq"].split("/")[idx]

    full_seq = metadata_row["target_chainseq"].replace("/", "")

    peptide_idx = get_region_indices(full_seq, metadata_row["peptide"])
    if peptide_idx.size != 9:
        raise ValueError("Peptide is not a 9-mer")

    domain_indices = {
        "mhc": get_region_indices(full_seq, metadata_row["mhc_seq"]),
        "tcra": get_region_indices(full_seq, metadata_row["tcra_seq"]),
        "tcrb": get_region_indices(full_seq, metadata_row["tcrb_seq"]),
        "cdr3a": get_region_indices(full_seq, metadata_row["cdr3a"]),
        "cdr3b": get_region_indices(full_seq, metadata_row["cdr3b"]),
    }

    return peptide_idx, domain_indices


def accumulate_peptide_domain_contacts(
    coords,
    peptide_idx,
    domain_indices,
    accumulator,
    threshold,
):
    peptide_coords = coords[peptide_idx]  # (9, 3)

    for d, domain in enumerate(DOMAIN_ORDER):
        domain_coords = coords[domain_indices[domain]]  # (Nd, 3)

        diff = peptide_coords[:, None, :] - domain_coords[None, :, :]
        dist = np.linalg.norm(diff, axis=-1)

        accumulator[:, d] += (dist <= threshold).sum(axis=1)


# -----------------------------
# Main
# -----------------------------
def main(args):
    metadata = pd.read_table(args.metadata)


    if "pdb_file_path" not in metadata.columns:
        sys.exit("ERROR: metadata must contain 'pdb_file_path' column")

    global_matrix = np.zeros((9, len(DOMAIN_ORDER)), dtype=np.float64)

    pdb_files = metadata["pdb_file_path"].unique()

    for pdb_file in tqdm(pdb_files, desc="Processing PDBs"):
        if not os.path.exists(pdb_file):
            print(f"WARNING: missing PDB {pdb_file}, skipping", file=sys.stderr)
            continue

        try:
            coords = extract_ca_coords(pdb_file)
            row = metadata.loc[metadata["pdb_file_path"] == pdb_file].iloc[0]
            peptide_idx, domain_indices = build_indices(row)

            accumulate_peptide_domain_contacts(
                coords,
                peptide_idx,
                domain_indices,
                global_matrix,
                args.threshold,
            )

        except Exception as e:
            print(f"ERROR processing {pdb_file}: {e}", file=sys.stderr)

    df = pd.DataFrame(
        global_matrix,
        index=[f"P{i+1}" for i in range(9)],
        columns=DOMAIN_ORDER,
    )

    df.to_csv(args.out, sep="\t", index=False)
    print(f"Saved results to {args.out}")


# -----------------------------
# CLI
# -----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fast peptide-domain contact accumulation (HPC-ready)"
    )
    parser.add_argument(
        "--metadata",
        required=True,
        help="CSV file containing metadata (with pdb_file_path, target_chainseq, etc.)",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output CSV file",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=10.0,
        help="Distance threshold in Angstroms (default: 10.0)",
    )

    args = parser.parse_args()
    main(args)
