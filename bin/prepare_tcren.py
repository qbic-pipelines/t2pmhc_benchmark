#!/usr/bin/env python3

import os
import pandas as pd
from Bio.PDB import PDBParser
import argparse

class Translator():
    def __init__(self):
        pass

    # Read in PDB file using BioPython
    def read_pdb_file(self, pdb_path):
        """
        Read a PDB file and return the structure object
        
        Args:
            pdb_path (str): Path to the PDB file
        
        Returns:
            Bio.PDB.Structure: The parsed PDB structure
        """
        parser = PDBParser(QUIET=True)  # QUIET=True suppresses warnings
        
        # Extract structure ID from filename
        structure_id = os.path.basename(pdb_path).replace('.pdb', '')
        
        # Parse the PDB file
        structure = parser.get_structure(structure_id, pdb_path)
        
        return structure
    
    # feature assigning nodes to complex (one of: tcr, peptide, mhc)
    def create_index_list(self, l, index, chain):
        """
        sets the first and last index for a specific chain.
        """
        if index > 0:
            index += 1    
        l.append(index)
        index += len(chain) - 1
        l.append(index)
        return l, index
    
    def create_complex_list(self, chainseq):
        """
        creates a list of lists. Each list holding the first and last index of a specific complex in the pdb file
        [[hla],[peptide],[tcr_a],[tcr_b]] 
        """
        residue_seq = chainseq
        x = residue_seq.split("/")
        index_counter = 0
        complex_list = [[], [], [], []]
        
        for i, j in enumerate(x):
            complex_list[i], index_counter = self.create_index_list(complex_list[i], index_counter, j)

        return complex_list


    def get_identifier_pdb_file(self, pdb_file):
        return os.path.basename(pdb_file).split("_")[0]
    
    def create_complex_dict(self, pdb_file, chainseq):

        # get structure
        structure = self.read_pdb_file(pdb_file)
        # get complex_list
        complex_list = self.create_complex_list(chainseq)

        # Get all residues in order from the PDB
        all_residues = []
        for model in structure:
            for chain in model:
                for residue in chain:
                    if residue.id[0] == ' ':  # Standard amino acid
                        all_residues.append(residue)

        # Extract each complex using the boundaries
        complexes = {
            'MHC': all_residues[complex_list[0][0]:complex_list[0][1]+1],
            'Peptide': all_residues[complex_list[1][0]:complex_list[1][1]+1],
            'TCR_Alpha': all_residues[complex_list[2][0]:complex_list[2][1]+1],
            'TCR_Beta': all_residues[complex_list[3][0]:complex_list[3][1]+1]
        }

        return complexes
    

def add_complex_annotations_to_pdb(pdb_file, output_file, complexes, translator):
    """
    Add complex annotations to PDB file by replacing the chain ID column (5th column)
    and adding TER records after each complex
    """
    structure = translator.read_pdb_file(pdb_file)
    
    # Create a mapping from residue to complex
    residue_to_complex = {}
    
    # Map each residue to its complex
    all_residues = []
    for model in structure:
        for chain in model:
            for residue in chain:
                if residue.id[0] == ' ':  # Standard amino acid
                    all_residues.append(residue)
    
    # Assign complexes based on position
    for complex_name, residue_list in complexes.items():
        for residue in residue_list:
            residue_id = (residue.get_parent().id, residue.id[1])  # (chain_id, residue_number)
            residue_to_complex[residue_id] = complex_name
    
    # Read original PDB file and modify
    with open(pdb_file, 'r') as infile:
        lines = infile.readlines()
    
    with open(output_file, 'w') as outfile:
        # Add header comments about complex assignments
        outfile.write("REMARK 100 COMPLEX ASSIGNMENTS:\n")
        outfile.write("REMARK 100 M = MHC, P = PEPTIDE, A = TCR_ALPHA, B = TCR_BETA\n")
        
        previous_complex = None
        current_complex = None
        
        for line in lines:
            if line.startswith(('ATOM', 'HETATM')):
                chain_id = line[21]
                residue_num = int(line[22:26].strip())
                
                # Find which complex this residue belongs to
                complex_code = 'U'  # Unknown
                current_complex = None
                
                for complex_name, residue_list in complexes.items():
                    for residue in residue_list:
                        if (residue.get_parent().id == chain_id and 
                            residue.id[1] == residue_num):
                            if complex_name == 'MHC':
                                complex_code = 'M'
                            elif complex_name == 'Peptide':
                                complex_code = 'P'
                            elif complex_name == 'TCR_Alpha':
                                complex_code = 'A'
                            elif complex_name == 'TCR_Beta':
                                complex_code = 'B'
                            current_complex = complex_name
                            break
                
                # Check if we need to add a TER record (complex changed)
                if (previous_complex is not None and 
                    current_complex != previous_complex and 
                    current_complex is not None):
                    outfile.write("TER\n")
                
                # Replace the chain ID (5th column, position 21) with complex code
                modified_line = line[:21] + complex_code + line[22:]
                outfile.write(modified_line)
                
                previous_complex = current_complex
                
            elif line.startswith('TER'):
                # Skip original TER records since we're adding our own
                continue
            else:
                outfile.write(line)
        
        # Add final TER record
        if previous_complex is not None:
            outfile.write("TER\n")

def read_table(f_p):
    if f_p.endswith("csv"):
            return pd.read_csv(f_p)
    elif f_p.endswith("tsv"):
        return pd.read_csv(f_p, sep="\t")
    else: 
        return "Incorrect file ending. Needs to be 'tsv' or 'csv'"

def main():

    parser = argparse.ArgumentParser(description='Translate tcrdock structures for TCRen')
    parser.add_argument('--pdb_file', type=str, required=True, help="Path to tcrdock pdb file")
    parser.add_argument('--chainseq', type=str, required=True, help="tcrdock chainseq")
    parser.add_argument('--outdir', type=str, required=True, help="Path to store the TCRen graphs")

    args = parser.parse_args()
    

    # define translator 
    translator = Translator()

    # Translate the structures
    out_path = f"{args.outdir}/tcren_{os.path.basename(args.pdb_file)}"
    complexes = translator.create_complex_dict(args.pdb_file, args.chainseq)

    add_complex_annotations_to_pdb(args.pdb_file, out_path, complexes, translator)


if __name__ == "__main__":
    main()