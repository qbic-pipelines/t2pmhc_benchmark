process PREDICT_MIXTCRPRED {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction", mode: 'copy'
    // publishDir "${params.outdir}/binding_prediction/${meta.dataset}_mixtcrpred_models", mode: 'copy',
                //saveAs: { filename -> "${filename}" }


    input:
    tuple val(meta), path(samplesheet), path(graphs)
    path(mixtcrpred_dir)
    path(mixtcrpred_models)

    output:
    tuple val(meta), path("${meta.dataset}_${meta.id}_models")  , emit: mixtcrpred_results
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.dataset}_${meta.id}"

    """
    mkdir -p ${prefix}_models
    
    predict_mixtcrpred.py \\
        --mixtcrpred_path ${mixtcrpred_dir} \\
        --samplesheet ${samplesheet} \\
        --mixtcrpred_models ${mixtcrpred_models}/info_models.csv \\
        --path_pretrained_models ${mixtcrpred_models} \\
        --outdir ${prefix}_models \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        mixtcrpred: 0.1.0
    END_VERSIONS
    """
}