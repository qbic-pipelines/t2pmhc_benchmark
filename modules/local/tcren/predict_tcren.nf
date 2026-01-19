process PREDICT_TCREN {
    tag "$meta.id"
    label 'process_single'

    publishDir "${params.outdir}/binding_prediction", mode: 'copy',
                saveAs: { filename -> "${filename}" }

    // CONTAINER IS SET IN THE CONFIG CURRENTLY

    input:
    tuple val(meta), path(pdb_files), path(candidate_epitopes)

    output:
    tuple val(meta), path("${meta.dataset}_${meta.id}_predictions")  , emit: mixtcrpred_results
    path "versions.yml"         , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    def prefix = task.ext.prefix ?: "${meta.dataset}_${meta.id}"

    """
    # Set up environment
    export HOME=/tmp

    # Prepare input in work directory (where we have write permissions)
    mkdir -p input_structures
    mkdir -p ${prefix}_predictions
    cp -L *.pdb input_structures/

    # Copy the necessary TCRen files to our work directory
    cp /opt/tcren-ms/TCRen_pipeline/run_TCRen.R .
    cp /opt/tcren-ms/TCRen_pipeline/TCRen_potential.csv .
    cp /opt/tcren-ms/TCRen_pipeline/mir-1.0-SNAPSHOT.jar .

    echo "=== Setup complete ==="
    echo "Work directory: \$PWD"
    echo "Input structures:"
    ls -la input_structures/
    echo "Candidate epitopes file:"
    ls -la ${candidate_epitopes}
    echo "Candidate epitopes content:"
    head -20 ${candidate_epitopes}

    # Check if the epitopes file has the correct format
    echo "=== Checking epitopes file format ==="
    echo "First few lines:"
    cat ${candidate_epitopes}
    echo "Number of lines:"
    wc -l ${candidate_epitopes}

    echo "=== TCRen files copied ==="
    ls -la *.R *.csv *.jar

    # Run TCRen from our work directory (where we have write permissions)
    Rscript --vanilla run_TCRen.R \\
        -s input_structures/ \\
        -c ${candidate_epitopes} \\
        -p TCRen_potential.csv \\
        -o ${prefix}_predictions/ \\
        -m ${task.cpus}G \\
        ${args}

    echo "=== Final output ==="
    ls -la ${prefix}_predictions/

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        tcren: 0.0.1
    END_VERSIONS
    """
}