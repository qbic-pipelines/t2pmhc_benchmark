process PREDICT_TABR_BERT {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}/binding_prediction/predictions/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    container 'docker://freshwindbioinformatics/tabr-bert:v1'

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
    python /workspace/TABR-BERT/predict_tcr_pmhc_binding.py \\
        --input ${samplesheet} \\
        --healthy_tcr /workspace/TABR-BERT/data/small_healthy_tcr.csv \\
        --pseudo_sequence_dict /workspace/TABR-BERT/data/mhcflurry.allele_sequences_homo.csv \\
        --tcr_pmhc_model /workspace/TABR-BERT/model/tcr_pmhc_model.pt \\
        --tcr_model /workspace/TABR-BERT/model/tcr_model.pt \\
        --pmhc_model /workspace/TABR-BERT/model/pmhc_model.pt \\
        --output ${prefix}_predicted.csv \\
        --GPUs 0

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        t2pmhc: 0.1.0
    END_VERSIONS
    """
}