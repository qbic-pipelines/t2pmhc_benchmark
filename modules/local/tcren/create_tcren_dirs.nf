process CREATE_TCREN_DIRS {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction/tcren_graphs", mode: 'copy'

    input:
    tuple val(meta), path(samplesheet), path(graphs)

    output:
    tuple val(meta), path("${meta.dataset}_${meta.id}_graphs"), emit: tcren_dirs
    path "versions.yml", emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def output_dir = "${meta.dataset}_${meta.id}_graphs"

    """
    mkdir -p ${output_dir}
    
    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        CREATE_TCREN_DIRS: 1.0.0
    END_VERSIONS
    """
}