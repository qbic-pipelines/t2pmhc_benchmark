import pandas as pd
from sklearn.metrics import roc_curve, auc, roc_auc_score
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Vendored into publication/lib/. Training sets live in publication/data/training_data/.
_TRAIN_DIR = Path(__file__).resolve().parent.parent / "data" / "training_data"

class Benchmarker:
    def __init__(self):
        self.PAE_THRSH = 8.07
    
    def read_table(self, f_p):
        if f_p.endswith("csv"):
            return pd.read_csv(f_p)
        elif f_p.endswith("tsv"):
            return pd.read_csv(f_p, sep="\t")
        else: 
            return "Incorrect file ending. Needs to be 'tsv' or 'csv'"
        
    def save_table(self, df, f_p):
        if f_p.endswith("csv"):
            df.to_csv(f_p, index=False)
        elif f_p.endswith("tsv"):
            df.to_csv(f_p, sep="\t", index=False)
        else:
            return "Incorrect file ending. Needs to be 'tsv' or 'csv'. File could not be saved."
            
    def get_model(self, f_p):
        return os.path.basename(f_p).split("_")[0]

    def get_dataset(self, f_p):
        return (f_p).split("/")[-2]
    
    def get_bindercol(self, model):
        # t2pmhc
        if model.lower() in ["gcn", "gcn-ots", "gat", "mixtcrpred", "gcn-globmean", "gcn-100", "mixtcrpred-pan"]: # Case-insensitive
            return ["binder", "binder_prob"]
        elif model.lower() == "tabr-bert":
            return ["binder", "rank"]
        elif model.lower() == "ergo2":
            return ["binder", "Score"]
        else:
            raise ValueError(f"Binder Col -- Unsupported model: {model}")
            # Or return a default: return ["default_col", "default_prob"]
    
    def get_roc(self, binder_col, prob_col):
        fpr, tpr, thrsh = roc_curve(binder_col, prob_col)
        return fpr, tpr
    
    def get_auc(self, fpr, tpr):
        return auc(fpr, tpr)
    
    def get_roc_auc(self, labels, probs):
        return roc_auc_score(labels, probs)
    
    def get_roc_auc01(self, labels, probs):
        return roc_auc_score(labels, probs, max_fpr=0.1)
    
    def get_auc_df(self, df, model):
        label_col, probs_col = self.get_bindercol(model)
        return self.get_roc_auc(df[label_col], df[probs_col])
    
    def get_color(self, model):
        return self.get_color_palette()[model]
        
    def get_color_palette(self):
        return {
            'gcn': '#d65f1eb2', 
            'gat': '#f08a4bb3',
            'gcn-ots': '#C2C965',
            'mixtcrpred': '#9a9a9aff',
            'mixtcrpred-pan': "#b0b0b0ff",
            'tabr-bert': '#5f5f5fff',
            "gcn-globmean":"#783D3D",
            "gcn-100":"#7AEF80",
            "ergo2": "#7f7f7fff",
        }


    def get_train_df(self, model):
        # Repointed to the vendored training sets under publication/data/training_data/.
        if model.lower() in ["gcn", "gat", "gcn-globmean", "gcn-100"]:
            return self.read_table(str(_TRAIN_DIR / "t2pmhc_train_core.tsv"))
        elif model.lower() in ["mixtcrpred", "mixtcrpred-pan"]:
            return self.read_table(str(_TRAIN_DIR / "mixtcrpred_full_training_set_146pmhc.csv"))
        else:
            raise ValueError(f"Train df -- Unsupported model: {model}")

    def get_seen(self, model):
        train_df = self.get_train_df(model)
        if "peptide" in train_df.columns:
            return set(train_df["peptide"])
        elif "Peptide" in train_df.columns:
            return set(train_df["Peptide"])
        else: 
            return set(train_df["epitope"])
    
    def get_unseen(self, f_p, model):
        seen_peptides = self.get_seen(model)
        return set(self.read_table(f_p)["peptide"]) - seen_peptides

    def get_unseen_df(self, f_p, model):
        unseen_peptides = self.get_unseen(f_p, model)
        df = self.read_table(f_p)
        return df[df["peptide"].isin(unseen_peptides)].copy()

    def get_seen_df(self, f_p, model):
        seen_peptides = self.get_seen(model)
        df = self.read_table(f_p)
        return df[df["peptide"].isin(seen_peptides)].copy()
    
    def get_peptide_labels(self, df, peptide):
        return list(df[df["peptide"] == peptide]["binder"])

    def get_allele_labels(self, df, mhc):
        return list(df[df["mhc"] == mhc]["binder"])

    def get_peptide_probs(self, df, peptide, model):
        return list(df[df["peptide"] == peptide][self.get_bindercol(model)[1]])
    
    def get_allele_probs(self, df, mhc, model):
        return list(df[df["mhc"] == mhc][self.get_bindercol(model)[1]])
    
    def get_peptides(self, df):
        return set(df["peptide"].values)
    
    def get_alleles(self, df):
        return set(df["mhc"].values)
    
    def get_modelorder(self):
        return ["gcn", "gcn-ots", "gcn-100", "gat", "mixtcrpred-pan", "mixtcrpred", "ergo2", "tabr-bert"]
    
    def get_dataset_selection(self):
        return ["mhc1_noleakage", "mhc_noleakage_seen", "immrep_not2pmhcleakage", "immrep_noleakage_total_seen"]

    def get_pae_df(self, df):
        return df[df["model_2_ptm_pae"] <= self.PAE_THRSH].copy()
    
    def get_figure_tcrs(self, df):
        return df[df["paper_figure"] == 1].copy()
    
    def get_interesting_peptide(self, df):
        return df[df["peptide"] == "RYGEEVKEF"].copy()
    
    def count_peptides(self, df):
        return df["peptide"].nunique()

    
    def plot_roc(self, f_p, df):
        # model name
        model_name = self.get_model(f_p)
        # get binder, prob cols
        binder_col, binder_prob = self.get_bindercol(model_name)
        # calc fpr, tpr
        try:
            fpr, tpr = self.get_roc(df[binder_col], df[binder_prob])

        except ValueError:
            return None
        # calc auc
        roc_auc = self.get_auc(fpr,tpr)
        auc01 = self.get_roc_auc01(df[binder_col], df[binder_prob])
        # plot
        color = self.get_color(model_name)
        plt.plot(fpr, tpr, color=color, lw=2, label=f'{model_name} (AUC0.1 = {auc01:.3f}, AUC = {roc_auc:.3f})', alpha=0.7)
        plt.title(f"{self.get_dataset(f_p)} ({len(self.get_peptides(df))} Peptides, {(df['binder'] == 1).sum()} Positives)")
        plt.plot([0, 1], [0, 1], color='black', lw=2, linestyle='--', alpha=0.2)
        plt.ylabel('Sensitivity')
        plt.xlabel('1 - Specificity')

        # Get handles and labels from the current figure
        handles, labels = plt.gca().get_legend_handles_labels()

        # Extract AUC values from labels
        auc_values = [float(label.split('AUC = ')[1].rstrip(')')) for label in labels]

        # Sort handles and labels based on AUC values in descending order
        sorted_pairs = sorted(zip(handles, labels, auc_values), key=lambda x: x[2], reverse=True)
        sorted_handles, sorted_labels, _ = zip(*sorted_pairs)

        # Add the sorted legend
        plt.legend(sorted_handles, sorted_labels, loc="lower right")
        plt.tight_layout()


    def translate_tabr(self, df):
        tabr_df = df.copy()
        # create cols required by tabr. Just add them to the existing samplesheet to make further analyses easier
        tabr_df["cdr3"] = tabr_df["cdr3b"]
        tabr_df["allele"] = tabr_df["mhc"]
        tabr_df["label"] = tabr_df["binder"]

        # give required allele notation
        tabr_df["allele"] = tabr_df["allele"].apply(lambda x: ":".join(x.split(":")[:2]))
        tabr_df["allele"] = "HLA-" + tabr_df["allele"]

        return tabr_df
    
    def translate_mixtcrpred(self, df):
        mpred_df = df.copy()
        mpred_df["cdr3_TRA"] = mpred_df["cdr3a"]
        mpred_df["cdr3_TRB"] = mpred_df["cdr3b"]
        mpred_df["TRAV"] = mpred_df["va"].str.split("*").str[0]
        mpred_df["TRAJ"] = mpred_df["ja"].str.split("*").str[0]
        mpred_df["TRBV"] = mpred_df["vb"].str.split("*").str[0]
        mpred_df["TRBJ"] = mpred_df["jb"].str.split("*").str[0]
        mpred_df["epitope"] = mpred_df["peptide"]
        mpred_df["MHC"] = "HLA-" + mpred_df["mhc"].str.split(":").str[:2].str.join(":")
        mpred_df["MHC_class"] = "MHCI"
        return mpred_df
    
    def translate_ergo(self, df):
        ergo_df = df.copy()
        # create cols required by ergo. Just add them to the existing samplesheet to make further analyses easier
        ergo_df["TRA"] = ergo_df["cdr3a"]
        ergo_df["TRB"] = ergo_df["cdr3b"]
        ergo_df["MHC"] = ergo_df["mhc"]
        ergo_df["Peptide"] = ergo_df["peptide"]
        ergo_df["TRAV"] = ergo_df["va"]
        ergo_df["TRAJ"] = ergo_df["ja"]
        ergo_df["TRBV"] = ergo_df["vb"]
        ergo_df["TRBJ"] = ergo_df["jb"]

        # give required allele notation
        ergo_df["MHC"] = ergo_df["MHC"].apply(lambda x: ":".join(x.split(":")[:2]))
        ergo_df["MHC"] = "HLA-" + ergo_df["MHC"]
        # add t-cell type
        # Define allele groups
        cd8 = ["HLA-A", "HLA-B", "HLA-C"]          # MHC class I
        cd4 = ["HLA-DP", "HLA-DQ", "HLA-DR"]       # MHC class II
        # Extract the gene part before the '*'
        allele_prefix = ergo_df["MHC"].str.split("*").str[0]
        # Assign T-cell type
        ergo_df["T-Cell-Type"] = np.where(
            allele_prefix.isin(cd8), "CD8",
            np.where(allele_prefix.isin(cd4), "CD4", "")
        )

        return ergo_df

    def generate_seen_unseen(self, df, model):
        seen_peptides = self.get_seen(model)
        df_seen = df[df["peptide"].isin(seen_peptides)].copy()
        df_unseen = df[~df["peptide"].isin(seen_peptides)].copy()

        return df_seen, df_unseen


    def find_leakage_tabr(self, train_tabr, test_tabr):
        # Find same peptide, allele, cdr3 combinations in train and test samplesheet
        common = pd.merge(
            test_tabr,
            train_tabr,
            left_on=['peptide', 'allele', 'cdr3'],
            right_on=['peptide', 'allele', 'cdr3'],
            how='inner'
        )

        leaked_ids_tabr = set(common["identifier"])

        print("leaked_ids", len(leaked_ids_tabr))

        return leaked_ids_tabr

    def find_leakage_mpred(self, train_mpred, test_mpred):
        # Find same peptide, allele, cdr3 combinations in train and test samplesheet
        common = pd.merge(
            test_mpred,
            train_mpred,
            left_on=['epitope', 'cdr3_TRA', 'cdr3_TRB', 'TRAV', 'TRAJ', 'TRBV', 'TRBJ', 'MHC', 'MHC_class'],
            right_on=['epitope', 'cdr3_TRA', 'cdr3_TRB', 'TRAV', 'TRAJ', 'TRBV', 'TRBJ', 'MHC', 'MHC_class'],
            how='inner'
        )

        leaked_ids_mixtcrpred = set(common["identifier"])

        print("leaked_ids", len(leaked_ids_mixtcrpred))

        return leaked_ids_mixtcrpred
    

    def find_leakage_t2pmhc(self, test_df, train_df):
        common = pd.merge(
            test_df,
            train_df,
            left_on=['mhc', 'peptide', 'va', 'ja', 'vb', 'jb', 'cdr3a', 'cdr3b'],
            right_on=['mhc', 'peptide', 'va', 'ja', 'vb', 'jb', 'cdr3a', 'cdr3b'],
            how='inner'
        )
        leaked_ids_test = set(common["identifier_x"])
        
        print("leaked_ids", len(leaked_ids_test))

        return leaked_ids_test
    

    def find_leakage_ergo(self, train_ergo, test_ergo):
        # Create copies to avoid modifying original DataFrames
        train_ergo_copy = train_ergo.copy()
        test_ergo_copy = test_ergo.copy()
        
        train_ergo_copy["MHC_simple"] = train_ergo_copy["MHC"].str.split(":").str[0]
        test_ergo_copy["MHC_simple"] = test_ergo_copy["MHC"].str.split(":").str[0]

        common_trb = pd.merge(
            test_ergo_copy,
            train_ergo_copy,
            left_on=["TRB", "TRBV", "TRBJ", "Peptide", "MHC_simple"],
            right_on=["TRB", "TRBV", "TRBJ", "Peptide", "MHC_simple"],
            how="inner"
        )

        common_all = pd.merge(
            test_ergo_copy,
            train_ergo_copy,
            left_on=["TRA", "TRAV", "TRAJ", "TRB", "TRBV", "TRBJ", "Peptide", "MHC_simple"],
            right_on=["TRA", "TRAV", "TRAJ", "TRB", "TRBV", "TRBJ", "Peptide", "MHC_simple"],
            how="inner"
        )

        # get all leaked_ids
        leaked_ids = set(common_trb["identifier"]).union(set(common_all["identifier"]))

        print("leaked_ids", len(leaked_ids))

        return leaked_ids