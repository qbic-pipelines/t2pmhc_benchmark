#!/bin/bash


#SBATCH --ntasks=1                                  # Number of tasks (see below)
#SBATCH --cpus-per-task=12                          # Number of CPU cores per task
#SBATCH --time=1-00:00                              # Runtime in D-HH:MM
#SBATCH --mem=64G                                   # Memory pool for all cores (see also --mem-per-cpu)
#SBATCH --output=hostname_%j.out                    # File to which STDOUT will be written - make sure this is not on HOME
#SBATCH --error=hostname_%j.err                     # File to which STDERR will be written - make sure this is not on HOME
#SBATCH --mail-type=FAIL                            # Send email on job failure
#SBATCH --mail-user=mark.polster@uni-tuebingen.de   # email address

# load conda
source ~/.bashrc

# activate environment
conda activate work


python -u peptide_contacts.py \
  --metadata samplesheets/a0201_negatives.tsv \
  --out contact_files/a0201_negative_contacts.tsv