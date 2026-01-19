process PREDICT_ERGO2 {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/python_pip_numpy_pandas_pruned:e27f02df9f3b4a72' :
        'community.wave.seqera.io/library/python_pip_biopython_natsort_pruned:a18194a14d1e98f8' }"

    input:
    tuple val(meta), path(samplesheet), path(graphs)

    output:
    tuple val(meta), path("${meta.id}_predicted.csv")  , emit: tabr_bert_pred
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    predict_ergo2.sh \\
        vdjdb \\
        ${samplesheet} \\
        ${prefix}_predicted.csv \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        ergo2: 0.1.0
    END_VERSIONS
    """
}