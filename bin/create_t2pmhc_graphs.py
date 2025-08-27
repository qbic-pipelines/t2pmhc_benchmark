#!/usr/bin/env python3

import pandas as pd
import argparse
import numpy as np
import logging
logger = logging.getLogger(__name__)

import torch

from joblib import load

# necessary to import functions from a siblings dir
import sys
sys.path.append('/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/tcr_phla/tcr_phla/models')

from models.gcn_contactmaps import create_graph_dataset as gcn_create_graphs
from models.gat_contactmaps import create_graph_dataset as gat_create_graphs
from tcr_phla import read_in_samplesheet



def main():
    parser = argparse.ArgumentParser(description='Predict binder status of samples in a t2pmhc samplesheets')
    parser.add_argument('--mode', type=str, required=True, help="gcn, gcn-ots, gat")
    parser.add_argument('--samplesheet', type=str, required=True, help="Path to t2pmhc samplesheet")
    parser.add_argument('--out', type=str, required=True, help="Path to store the graphs")

    args = parser.parse_args()

    # init logging
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[logging.StreamHandler(sys.stdout)])

    # read in samplesheet 
    pdb_files = read_in_samplesheet(args.samplesheet)
    metadata = pd.read_csv(args.samplesheet, sep="\t")

    # create graphs
    if args.mode == "gat":
        logging.info("Creating Graphs -- gat")
        test_dataset, test_structures = gat_create_graphs(
            pdb_files=pdb_files, metadata=metadata, sample_size=np.inf, threshold=10, load_graphs=False, saved_graphs="", store_graphs=True, name="", test_run=True, graphs_path=args.out
        )
    elif args.mode in ["gcn", "gcn-ots", "gcn-globmean"]:
        logging.info("Creating Graphs -- gcn")
        test_dataset, test_structures = gcn_create_graphs(
            pdb_files=pdb_files, metadata=metadata, sample_size=np.inf, threshold=10, load_graphs=False, saved_graphs="", store_graphs=True, name="",  test_run=True, graphs_path=args.out
        )


if __name__ == "__main__":
    main()
