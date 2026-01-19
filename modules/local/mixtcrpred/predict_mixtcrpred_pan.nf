process PREDICT_MIXTCRPRED_PAN {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/python_pip_biopython_natsort_pruned:3813942a2ace4c49' :
        'community.wave.seqera.io/library/python_pip_biopython_natsort_pruned:a18194a14d1e98f8' }"

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