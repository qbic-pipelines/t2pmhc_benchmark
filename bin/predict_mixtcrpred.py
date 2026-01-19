#!/usr/bin/env python3

import pandas as pd
import subprocess
import argparse


def get_required_models(models, train_df):

    # remove mouse models
    models = models.loc[models["Host_species"] == "HomoSapiens"]
    # remove mhc2
    models = models.loc[models["MHC_class"] == "MHCI"]
    
    # generate model col in training
    train_df["mhc_mixtcrpred_notation"] = train_df["mhc"].str.split(":").str[:2].str.join("").str.replace("*","") + "_" + train_df["peptide"]
    # get pMHCs to which I can compare the models to
    train_peptide_mhc = set(train_df["mhc_mixtcrpred_notation"])
    
    # remove all non-required models from df
    models = models[models["MixTCRpred_model_name"].isin(train_peptide_mhc)]
    
    return models

# adapt test sheet to mixtcrpred notation
def adapt_test_sheet(df):
    df["cdr3_TRA"] = df["cdr3a"]
    df["cdr3_TRB"] = df["cdr3b"]
    df["TRAV"] = df["va"].str.split("*").str[0]
    df["TRAJ"] = df["ja"].str.split("*").str[0]
    df["TRBV"] = df["vb"].str.split("*").str[0]
    df["TRBJ"] = df["jb"].str.split("*").str[0]

    return df


# run mixtcrpred prediction

def create_mixtcrpred_samplesheet(model, test_df, out):
    df = test_df.loc[test_df["MixTCRpred_model_name"] == model]
    df.to_csv(f"{out}/{model}.csv", index=False)

    return f"{out}/{model}.csv"

def run_mixtcrpred(test_df, models_df, out, mixtcrpred_path, path_pretrained_models):
    # add "model infos" to test_df
    test_df["MixTCRpred_model_name"] = test_df["mhc"].str.split(":").str[:2].str.join("").str.replace("*","") + "_" + test_df["peptide"]
    # give mixtcrpred col notation
    test_df = adapt_test_sheet(test_df)

    for model in models_df["MixTCRpred_model_name"].unique():
        # create samplesheet
        model_test_sheet = create_mixtcrpred_samplesheet(model, test_df, out)
        
        # set out_dir 
        out_path = f"{out}/{model}_predicted.csv"

        # make mixtcrpred predictions 
        subprocess.run([
            "python", f"{mixtcrpred_path}/MixTCRpred.py", 
            "--model", model, 
            "--input", model_test_sheet, 
            "--output", out_path,
            "--path_pretrained_models", path_pretrained_models
        ], check=True)




def main():
    parser = argparse.ArgumentParser(description='Predict binding using MixTCRpred')
    parser.add_argument('--mixtcrpred_path', type=str, required=True, help="Path to the MixTCRpred repository")
    parser.add_argument('--mixtcrpred_models', type=str, required=True, help="Path to the MixTCRpred models")
    parser.add_argument('--samplesheet', type=str, required=True, help="Path to the mixtcrpred samplesheet")
    parser.add_argument('--path_pretrained_models', type=str, required=True, help="Path to the mixtcrpred pretrained models")
    parser.add_argument('--outdir', type=str, required=True, help="Path to store the mixtcrpred results of the individual models")

    args = parser.parse_args()

    # read in tsv with models
    models = pd.read_csv(args.mixtcrpred_models)

    # read in test samplesheet
    test_df = pd.read_csv(f"{args.samplesheet}")

    # remove non-required models
    models = get_required_models(models, test_df)

    # run the prediction
    run_mixtcrpred(test_df, models, args.outdir, args.mixtcrpred_path, args.path_pretrained_models)



if __name__ == "__main__":
    main()