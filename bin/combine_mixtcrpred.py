#!/usr/bin/env python3

import pandas as pd
import glob
import argparse
import numpy as np


# After running all predictions, combine results
def combine_mixtcrpred_results(result_path, out):
    all_results_df = pd.DataFrame()
    result_files = glob.glob(f"{result_path}/*_predicted.csv")
    
    all_results_df = pd.concat([pd.read_csv(file, comment = "#") for file in result_files], ignore_index=True)

    # adapt mixtcrpred columns to get: bigger == more likely binder (they have perc_rank which is smaller == binder)
    percent_rank = all_results_df["perc_rank"]
    # inverse --> bigger == better
    inv_perc_rank = 1 - (percent_rank / 100.0)
    inv_perc_rank = np.clip(inv_perc_rank, 0, 1)
    # add to df as "binder_prob"
    all_results_df["binder_prob"] = inv_perc_rank

    all_results_df.to_csv(out, sep="\t", index=False)

    return all_results_df





def main():
    parser = argparse.ArgumentParser(description='Predict binding using MixTCRpred')
    parser.add_argument('--result_path', type=str, required=True, help="Path to the MixTCRpred predictions")
    parser.add_argument('--out', type=str, required=True, help="Path to store the final mixtcrpred prediction table")

    args = parser.parse_args()

    combine_mixtcrpred_results(args.result_path, args.out)




if __name__ == "__main__":
    main()