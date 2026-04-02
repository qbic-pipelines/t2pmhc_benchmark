process PREDICT_MIXTCRPRED_PAN {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }


    input:
    tuple val(meta), path(samplesheet), path(graphs)
    path(mixtcrpred_dir)
    path(pan_model)

    output:
    tuple val(meta), path("${meta.id}_predicted.tsv")  , emit: mpred_pan_pred
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    
    predict_mixtcrpred_pan.sh \\
        --mpred_path ${mixtcrpred_dir} \\
        --input ${samplesheet} \\
        --output ${prefix}_predicted.tsv \\
        --checkpoint ${pan_model} \\
        --model_name pan_epitope \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        mixtcrpred: 0.1.0
    END_VERSIONS
    """
}