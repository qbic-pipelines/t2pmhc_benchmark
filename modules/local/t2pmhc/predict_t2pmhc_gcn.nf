process PREDICT_T2PMHC_GCN {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    // set docker container
    container "docker://mvp9/t2pmhc:release"

    input:
    tuple val(meta), path(samplesheet), path(graphs)

    output:
    tuple val(meta), path("${meta.id}_predicted.tsv")  , emit: gcn_pred
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"
    def mode = "t2pmhc-${meta.id}"

    """
    t2pmhc t2pmhc-predict-binding \\
        --mode $mode \\
        --samplesheet ${samplesheet} \\
        --saved_graphs ${graphs} \\
        --out ${prefix}_predicted.tsv \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        t2pmhc: 0.1.0
    END_VERSIONS
    """
}