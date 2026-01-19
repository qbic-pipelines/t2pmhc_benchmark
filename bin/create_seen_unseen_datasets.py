#!/usr/bin/env python3

import pandas as pd
import os
import re
import argparse



class DataReader:
    def __init__(self):
        pass
    
    def read_table(self, f_p):
        if f_p.endswith("csv"):
            return pd.read_csv(f_p)
        elif f_p.endswith("tsv"):
            return pd.read_csv(f_p, sep="\t")
        else: 
            return "Incorrect file ending. Needs to be 'tsv' or 'csv'"


    def get_train_df(self, model):
        if model.lower() == "gcn" or model.lower() == "gat":
            return self.read_table("/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/tcr_phla/data/train_samplesheets/train_mhc1_complete_highfreq_peptides.tsv")
        elif model.lower() == "mixtcrpred":
            return self.read_table("/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/benchmark/mixtcrpred/MixTCRpred/full_training_set_146pmhc.csv")
        elif model.lower() == "tabr_bert":
            return self.read_table("/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/benchmark/tabr_bert/training_data/train_tcr_pmhc.csv")
        else:
            raise ValueError(f"Train df -- Unsupported model: {model}")

    def get_seen(self, model):
        train_df = self.get_train_df(model)
        if "peptide" in train_df.columns:
            return set(train_df["peptide"])
        else: 
            return set(train_df["epitope"])
    
    def get_unseen(self, f_p, model):
        seen_peptides = self.get_seen(model)
        return set(self.read_table(f_p)["peptide"]) - seen_peptides
    
    def sample_samplesheet(self, df, peptide_set):
        return df[df["peptide"].str.isin(peptide_set)]
    
    def save_samplesheet(self, df, out_path):
        if out_path.endswith("csv"):
            df.to_csv(out_path, index=False)
        elif out_path.endswith("tsv"):
            df.to_csv(out_path, sep="\t", index=False)

    def get_out_path(self, model):
        if model.lower() == "gcn" or model.lower() == "gat":
            return "/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/benchmark/t2pmhc_samplesheets"
        elif model.lower() == "mixtcrpred":
            return "/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/benchmark/mixtcrpred/test_samplesheets"
        elif model.lower() == "tabr_bert":
            return "/mnt/lustre/groups/nahnsen/nahpo775/workdir/projects/tcrpha_pred/tcr_pHLApred/benchmark/tabr_bert/test_samplesheets"
        else:
            raise ValueError(f"out path -- Unsupported model: {model}")
        

    def get_samplesheet_name(self, f_p):
        return re.sub(r'\.(tsv|csv)$', '', os.path.basename(f_p))
    
    def set_fileending(self, model):
        if model.lower() == "gcn" or model.lower() == "gat":
            return "tsv"
        elif model.lower() == "mixtcrpred":
            return "csv"
        elif model.lower() == "tabr_bert":
            return "csv"
        else:
            raise ValueError(f"filending -- Unsupported model: {model}")


def get_shared_peptides(models, paths, seen):
    reader = DataReader()
    
    if seen:
        peptide_sets = [reader.get_seen(model) for model, f_p in zip(models, paths)]
    else:
        peptide_sets = [reader.get_unseen(f_p, model) for model, f_p in zip(models, paths)]

    return set.intersection(*peptide_sets)


def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--mode', type=str, required=True, help="GCN or GAT")
    parser.add_argument('--samplesheets', type=str, required=True, help="Path to t2pmhc samplesheets")
    parser.add_argument('--out', type=str, required=True, help="Path to store the seen/unseen samplesheets")
    parser.add_argument('--t2pmhc_train', type=str, required=True, help="t2pmhc train samplesheet")
    parser.add_argument('--mixtcrpred_train', type=str, required=True, help="mixtcrpred train samplesheet")
    parser.add_argument('--tabr_train', type=str, required=True, help="tabr train samplesheet")

    args = parser.parse_args()

    shared_seen = get_shared_peptides(["gcn", "mixtcrpred", "tabr_bert"], [t2pmhc, mixtcrpred, tabr_bert], True)
    shared_unseen = get_shared_peptides(["gcn", "mixtcrpred", "tabr_bert"], [t2pmhc, mixtcrpred, tabr_bert], False)

    reader = DataReader()

    for model, f_p in zip(["gcn", "mixtcrpred", "tabr_bert"], [t2pmhc, mixtcrpred, tabr_bert]):
        # create seen/unseen df
        for seen, peptide_set in zip(["seen", "unseen"],[shared_seen, shared_unseen]):
            df = reader.read_table(f_p)
            df = df[df["peptide"].isin(peptide_set)]
            print(df["peptide"].nunique())
            # save seen/unseen samplesheet
            print(f"{reader.get_out_path(model)}/{reader.get_samplesheet_name(f_p)}_{seen}.{reader.set_fileending(model)}")
            reader.save_samplesheet(df, f"{reader.get_out_path(model)}/{reader.get_samplesheet_name(f_p)}_{seen}.{reader.set_fileending(model)}")


