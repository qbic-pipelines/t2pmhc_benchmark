process PREPARE_TCREN {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction/tcren_graphs/${meta.dataset}_${meta.id}_graphs", mode: 'copy'

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/pip_biopython_pandas:4c8f985a736961d0' :
        'community.wave.seqera.io/library/pip_biopython_pandas:3f9bddfaf75f944d' }"

    input:
    tuple val(meta), path(pdb_files), val(chainseqs), path(peptide_file)

    output:
    tuple val(meta), path("*.pdb"), path(peptide_file)  , emit: tcren_pdbs
    path "versions.yml"                                 , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.dataset}_${meta.id}"

    """
    # Convert chainseqs list to array for bash
    chainseqs_array=(${chainseqs.join(' ')})
    pdb_files_array=(${pdb_files.join(' ')})
    
    # Loop through each PDB file with its corresponding chainseq
    for i in "\${!pdb_files_array[@]}"; do
        pdb_file="\${pdb_files_array[\$i]}"
        chainseq="\${chainseqs_array[\$i]}"
        
        echo "Processing \$pdb_file with chainseq \$chainseq"
        
        prepare_tcren.py \\
            --pdb_file "\$pdb_file" \\
            --chainseq "\$chainseq" \\
            --outdir . \\
            ${args}
    done

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        tcren: 0.1.0
    END_VERSIONS
    """
}