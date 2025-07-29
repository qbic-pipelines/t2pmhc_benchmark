process CREATE_T2PMHC_GRAPHS {
    tag "$meta.id"
    label 'process_medium'

    publishDir "${params.outdir}/binding_prediction/graphs/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    conda "${moduleDir}/environment.yml"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'oras://community.wave.seqera.io/library/python_scikit-learn_pip_biopython_pruned:e0af158d5b414f68' :
        'community.wave.seqera.io/library/python_scikit-learn_pip_biopython_pruned:3781a75b1cc752a2' }"

    input:
    tuple val(meta), path(samplesheet), path(graphs)

    output:
    tuple val(meta), path("${meta.id}_${meta.dataset}_graphs.pt")  , emit: graphs
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.id}_${meta.dataset}"

    """
    create_t2pmhc_graphs.py \\
        --mode ${meta.id} \\
        --samplesheet ${samplesheet} \\
        --out ${prefix}_graphs.pt \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        t2pmhc: 0.1.0
    END_VERSIONS
    """
}