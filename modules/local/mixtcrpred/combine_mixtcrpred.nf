process COMBINE_MIXTCRPRED {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }


    input:
    tuple val(meta), path(mixtcrpred_out)

    output:
    tuple val(meta), path("${meta.id}_predicted.tsv")  , emit: mpred_pred
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