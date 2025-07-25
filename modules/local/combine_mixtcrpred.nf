process COMBINE_MIXTCRPRED {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/python_pip_biopython_natsort_pruned:3813942a2ace4c49' :
        'community.wave.seqera.io/library/python_pip_biopython_natsort_pruned:a18194a14d1e98f8' }"

    input:
    tuple val(meta), path(mixtcrpred_out)

    output:
    tuple val(meta), path("${meta.id}_predicted.tsv")  , emit: gcn_pred
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    combine_mixtcrpred.py \\
        --result_path ${mixtcrpred_out} \\
        --out ${prefix}_predicted.tsv \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        mixtcrpred: 0.1.0
    END_VERSIONS
    """
}