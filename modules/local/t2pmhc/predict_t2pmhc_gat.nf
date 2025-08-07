process PREDICT_T2PMHC_GAT {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/python_scikit-learn_pip_biopython_pruned:e0af158d5b414f68' :
        'community.wave.seqera.io/library/python_scikit-learn_pip_biopython_pruned:3781a75b1cc752a2' }"

    input:
    tuple val(meta), path(samplesheet), path(graphs)
    path(hyperparams)
    path(model)
    path(pae_scaler_full)
    path(pae_scaler_tcrpmhc)
    path(pae_scaler_edge)
    path(hydro_scaler)
    path(distance_scaler)

    output:
    tuple val(meta), path("${meta.id}_predicted.tsv")  , emit: gcn_pred
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    predict_binding.py \\
        --mode GAT \\
        --samplesheet ${samplesheet} \\
        --graphs ${graphs} \\
        --out ${prefix}_predicted.tsv \\
        --model_path ${model} \\
        --pae_scaler_structure ${pae_scaler_full} \\
        --pae_scaler_tcrpmhc ${pae_scaler_tcrpmhc} \\
        --pae_scaler_edge ${pae_scaler_edge} \\
        --hydro_scaler ${hydro_scaler} \\
        --distance_scaler ${distance_scaler} \\
        --hyperparams ${hyperparams} \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        t2pmhc: 0.1.0
    END_VERSIONS
    """
}