#!/usr/bin/env python3

import pandas as pd
import glob
import argparse


# After running all predictions, combine results
def combine_mixtcrpred_results(result_path, out):
    all_results_df = pd.DataFrame()
    result_files = glob.glob(f"{result_path}/*_predicted.csv")
    
    all_results_df = pd.concat([pd.read_csv(file, comment = "#") for file in result_files], ignore_index=True)

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