process CREATE_T2PMHC_GRAPHS {
    tag "$meta.id"
    label 'process_high'

    publishDir "${params.outdir}/binding_prediction/graphs/${meta.dataset}", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    // set docker container
    container "docker://mvp9/t2pmhc:1.0.0"

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
    def mode = "t2pmhc-${meta.id}"

    """
    t2pmhc create-t2pmhc-graphs \\
        --mode ${mode} \\
        --samplesheet ${samplesheet} \\
        --out ${prefix}_graphs.pt \\
        ${args}

    

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        t2pmhc: 0.1.0
    END_VERSIONS
    """
}