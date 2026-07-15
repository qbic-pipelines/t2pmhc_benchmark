"""Run PanPep zero-shot over every dataset in the samplesheet.

Pipeline per dataset (id, input_table):
  1. Read TSV, subset to peptide + cdr3b, rename to Peptide / CDR3,
     dedup, stable-sort by Peptide. Write panpep_run/<id>/input.csv.
  2. docker run ghcr.io/qbic-pipelines/panpep:b44ffb1 panpep
       --learning_setting zero-shot --input ... --output ...
  3. Merge the Score column back onto the original TSV and write
     panpep_results/<input_basename>_panpep.tsv with a `binding_score` column.

The rebuilt image bakes both former runtime workarounds (protobuf<4 and
CPU-rebaked .pkl files) so the wrapper is just `panpep`; no env var, no shim.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pandas as pd

SAMPLESHEET = Path(
    "/mnt/volume/workdir/projects/t2pmhc_revisions/new_benchmark"
    "/tcrpmhcbinding_runs/samplesheet.csv"
)
WORK     = Path("/mnt/volume/workdir/projects/t2pmhc_revisions/rev2_p1_panpep")
RUN_ROOT = WORK / "panpep_run"
OUT_ROOT = WORK / "panpep_results"
IMAGE    = "ghcr.io/qbic-pipelines/panpep:b44ffb1"


def main() -> int:
    OUT_ROOT.mkdir(exist_ok=True)
    sheet = pd.read_csv(SAMPLESHEET)
    for _, row in sheet.iterrows():
        run_one(row["id"], Path(row["input_table"]))
    return 0


def run_one(name: str, src: Path) -> None:
    print(f"\n=== {name} ({src.name}) ===", flush=True)
    rundir = RUN_ROOT / name
    rundir.mkdir(parents=True, exist_ok=True)

    # Step 1 -- prep input
    orig = pd.read_csv(src, sep="\t")
    missing = {"peptide", "cdr3b"} - set(orig.columns)
    if missing:
        raise ValueError(f"{src} is missing required columns: {missing}")

    input_csv = rundir / "input.csv"
    (orig[["peptide", "cdr3b"]]
        .rename(columns={"peptide": "Peptide", "cdr3b": "CDR3"})
        .drop_duplicates()
        .sort_values("Peptide", kind="stable")
        .to_csv(input_csv, index=False))
    n_in = sum(1 for _ in input_csv.open()) - 1
    print(f"  input.csv: {n_in} unique (peptide, cdr3b) pairs", flush=True)

    # Step 2 -- PanPep zero-shot
    preds_csv = rundir / "raw_predictions.csv"
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{rundir}:/work",
        IMAGE,
        "panpep",
        "--learning_setting", "zero-shot",
        "--input", "/work/input.csv",
        "--output", "/work/raw_predictions.csv",
    ]
    subprocess.run(cmd, check=True)

    # Step 3 -- join back to original TSV
    preds = (pd.read_csv(preds_csv)
               .rename(columns={"Peptide": "peptide", "CDR3": "cdr3b",
                                "Score": "binding_score"})
               .drop_duplicates(subset=["peptide", "cdr3b"]))
    merged = orig.merge(preds, on=["peptide", "cdr3b"], how="left",
                        validate="many_to_one")
    assert merged["binding_score"].notna().all(), \
        f"{name}: missing binding_score after join"
    assert len(merged) == len(orig), \
        f"{name}: row count changed after join ({len(merged)} vs {len(orig)})"

    out_tsv = OUT_ROOT / f"{src.stem}_panpep.tsv"
    merged.to_csv(out_tsv, sep="\t", index=False)
    s = merged["binding_score"]
    print(f"  wrote {out_tsv.name}: {len(merged)} rows, "
          f"score min={s.min():.4f} max={s.max():.4f} mean={s.mean():.4f}",
          flush=True)


if __name__ == "__main__":
    sys.exit(main())
