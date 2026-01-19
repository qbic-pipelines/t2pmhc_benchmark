#!/usr/bin/env python3
"""

This script is used to predict the binding status of a samplesheet using a given t2pmhc model.
It gives out a table with binding prediction.
It's part of the nf-core/t2pmhc_benchmark pipeline

Author: Mark Polster

"""

import pandas as pd
import argparse
import numpy as np
import logging
logger = logging.getLogger(__name__)

import torch
from torch_geometric.loader import DataLoader

from joblib import load

# necessary to import functions from a siblings dir
import sys
sys.path.append('/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/tcr_phla/tcr_phla/models')

from final_models.t2pmhc_gcn import GCNClassifier, create_graph_dataset as gcn_create_graphs, evaluate as gcn_evaluate
from final_models.t2pmhc_gat import GATClassifier, create_graph_dataset as gat_create_graphs, evaluate as gat_evaluate
from tcr_phla import read_hyperparams, read_in_samplesheet


def get_device():
    return torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def scale_test(dataset, mode, pae_node_scaler, pae_tcrpmhc_node_scaler, hydro_scaler, distance_scaler, pae_scaler_edge):
    # load shared scalers
    pae_node_scaler = load(pae_node_scaler)
    pae_tcrpmhc_node_scaler = load(pae_tcrpmhc_node_scaler)
    hydro_scaler = load(hydro_scaler)
    # load edge scalers
    distance_scaler = load(distance_scaler)

    if mode == "gcn":
        for graph in dataset:
            pae_val = np.array([[graph.meta["PAE"]]], dtype=np.float32)
            paetcrpmhc_val = np.array([[graph.meta["PAE_TCRpMHC"]]], dtype=np.float32)
            hydro_val = graph.meta["hydro"] # is already an array
            scaled_pae = pae_node_scaler.transform(pae_val)
            scaled_paetcrpmhc = pae_tcrpmhc_node_scaler.transform(paetcrpmhc_val)
            scaled_hydro = hydro_scaler.transform(hydro_val)
            # Add as new feature (column) to node features
            pae_feat = torch.tensor(scaled_pae, dtype=graph.x.dtype).repeat(graph.x.size(0), 1)
            paetcrpmhc_feat = torch.tensor(scaled_paetcrpmhc, dtype=graph.x.dtype).repeat(graph.x.size(0), 1)
            hydro_feat = torch.tensor(scaled_hydro)
            graph.x = torch.cat([graph.x, pae_feat, paetcrpmhc_feat, hydro_feat], dim=1)
            # edge feature
            edge_features = graph.edge_features
            distances = edge_features[:,0]
            scaled_distances = distance_scaler.transform(distances.reshape(-1, 1))
            graph.edge_attr = torch.tensor(scaled_distances, dtype=torch.float)

            
    elif mode == "gat":
        # load scaler only present in gat
        pae_scaler_edge = load(pae_scaler_edge)
        
        for graph in dataset:
            # get node features
            pae_val = np.array([[graph.meta["PAE"]]], dtype=np.float32)
            paetcrpmhc_val = np.array([[graph.meta["PAE_TCRpMHC"]]], dtype=np.float32)
            hydro_val = graph.meta["hydro"] # is already an array
            # scale features
            scaled_pae = pae_node_scaler.transform(pae_val)
            scaled_paetcrpmhc = pae_tcrpmhc_node_scaler.transform(paetcrpmhc_val)
            scaled_hydro = hydro_scaler.transform(hydro_val)
            # Add as new feature (column) to node features
            pae_feat = torch.tensor(scaled_pae, dtype=graph.x.dtype).repeat(graph.x.size(0), 1)
            paetcrpmhc_feat = torch.tensor(scaled_paetcrpmhc, dtype=graph.x.dtype).repeat(graph.x.size(0), 1)
            hydro_feat = torch.tensor(scaled_hydro)
            graph.x = torch.cat([graph.x, pae_feat, paetcrpmhc_feat, hydro_feat], dim=1)
            
            # get edge features
            edge_features = graph.edge_features
            distances = edge_features[:,0]
            paes = edge_features[:,1]
            # scale edge features
            scaled_distances = distance_scaler.transform(distances.reshape(-1, 1))
            scaled_pae = pae_scaler_edge.transform(paes.reshape(-1,1))
            # add edge features as features to the graph
            scaled_features = np.hstack([scaled_distances, scaled_pae]).astype(np.float32)  # Combine distances and PAE values
            graph.edge_attr = torch.tensor(scaled_features, dtype=torch.float)



def main():
    parser = argparse.ArgumentParser(description='Predict binder status of samples in a t2pmhc samplesheets')
    parser.add_argument('--mode', type=str, required=True, help="GCN or GAT")
    parser.add_argument('--samplesheet', type=str, required=True, help="Path to t2pmhc samplesheet")
    parser.add_argument('--graphs', type=str, required=True, help="Path to graphs in the samplesheet")
    parser.add_argument('--out', type=str, required=True, help="Path to store the t2pmhc result tsv")
    parser.add_argument('--model_path', type=str, required=True, help="Path to model file")
    parser.add_argument('--pae_scaler_structure', type=str, required=True, help="Path to PAE scaler file of the whole structure")
    parser.add_argument('--pae_scaler_tcrpmhc', type=str, required=True, help="Path to PAE scaler file of the TCR-pMHC complex")
    parser.add_argument('--hydro_scaler', type=str, required=False, help="Path to hydro scaler. only required for GAT")
    parser.add_argument('--distance_scaler', type=str, required=False, help="Path to Distance scaler. only required for GAT")
    parser.add_argument('--pae_scaler_edge', type=str, required=False, help="Path to PAE edge scaler. only required for GAT")
    parser.add_argument('--hyperparams', type=str, required=True, help="Path to hyperparams json")

    args = parser.parse_args()

    # init logging
    logging.basicConfig(level=logging.INFO, format='%(message)s', handlers=[logging.StreamHandler(sys.stdout)])

    # log arguments
    logging.info("======= PARAMS =====")
    logging.info(f"Mode: {args.mode}")
    logging.info(f"Samplesheet: {args.samplesheet}")
    logging.info(f"Graphs: {args.graphs}")
    logging.info(f"Output path: {args.out}")
    logging.info("======= PARAMS =====\n\n")
    


    # read in hyperparams
    
    logging.info("Reading Hyperparameters")
    hyperparams = read_hyperparams(args.hyperparams, parser)
    # Hyperparameters
    input_dim = hyperparams["input_dim"]
    hidden_dim = hyperparams["hidden_dim"]
    output_dim = hyperparams["output_dim"]
    learning_rate = hyperparams["learning_rate"]
    num_epochs = hyperparams["num_epochs"]
    weight_decay = hyperparams["weight_decay"]
    dropout_rate = hyperparams["dropout_rate"]
    batch_size = hyperparams["batch_size"]
    if args.mode == "GAT":
        edge_dim = hyperparams["edge_dim"]
        heads = hyperparams["heads"]

    # read in samplesheet 
    pdb_files = read_in_samplesheet(args.samplesheet)
    metadata = pd.read_csv(args.samplesheet, sep="\t")

    # create graphs and init respective model
    if args.mode == "GAT":
        logging.info("Creating Graphs")
        test_dataset, test_structures = gat_create_graphs(pdb_files="", metadata=metadata, sample_size=np.inf, threshold=10, load_graphs=True, saved_graphs=args.graphs, store_graphs=False, name="", test_run=False, graphs_path="")
        # scale the test features
        scale_test(test_dataset, "gat", args.pae_scaler_structure, args.pae_scaler_tcrpmhc, args.hydro_scaler, args.distance_scaler, args.pae_scaler_edge)
        # init model
        logging.info("Initialising Model")
        model = GATClassifier(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim, dropout_rate=dropout_rate, edge_dim=edge_dim, heads=heads)
    else: 
        logging.info("Creating Graphs")
        # read model and scalers
        test_dataset, test_structures = gcn_create_graphs(pdb_files="", metadata=metadata, sample_size=np.inf, threshold=10, load_graphs=True, saved_graphs=args.graphs, store_graphs=False, name="", test_run=False, graphs_path="")
        # scale the test features
        scale_test(test_dataset, "gcn", args.pae_scaler_structure, args.pae_scaler_tcrpmhc, args.hydro_scaler, args.distance_scaler, "")
        # init model
        logging.info("Initialising Model")
        model = GCNClassifier(input_dim=input_dim, hidden_dim=hidden_dim, output_dim=output_dim, dropout_rate=dropout_rate)
    
    # get the device
    device = get_device()
    print(device)
    
    # load model
    model.load_state_dict(torch.load(args.model_path, map_location=device))
    model.eval() # set at evaluation state

    # set dataloader
    loader = DataLoader(test_dataset, batch_size=32, shuffle=False)
    # evaluate the model on dataset
    dummy_criterion  = torch.nn.CrossEntropyLoss() # required by the function

    
    
    logging.info("Predicting Binder Status")
    if args.mode == "GAT": 
        _, _, labels, probs, preds = gat_evaluate(model, loader, dummy_criterion, device, return_probs=True)
    else:
        _, _, labels, probs, preds = gcn_evaluate(model, loader, dummy_criterion, device, return_probs=True)

    logging.info(f"Saving prediction to {args.out}")
    metadata["binder_prob"] = probs
    metadata["binder_prediction"] = preds
    metadata["model"] = args.mode
    
    # save metadata
    metadata.to_csv(args.out, sep="\t", index=False)





if __name__ == "__main__":
    main()