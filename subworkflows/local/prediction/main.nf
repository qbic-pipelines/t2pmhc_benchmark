/*
 * TODO Write short intro
 */

include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GCN             } from '../../../modules/local/t2pmhc/create_graphs' 
include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GCN_OTS         } from '../../../modules/local/t2pmhc/create_graphs' 
include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GCN_GLOBMEAN    } from '../../../modules/local/t2pmhc/create_graphs'
include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GCN_100         } from '../../../modules/local/t2pmhc/create_graphs' 
include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GAT             } from '../../../modules/local/t2pmhc/create_graphs' 
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_GRAPHS               } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_NOGRAPHS             } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_GLOBMEAN_GRAPHS      } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_GLOBMEAN_NOGRAPHS    } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_100_GRAPHS           } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_100_NOGRAPHS         } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_OTS_GRAPHS           } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_OTS_NOGRAPHS         } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GAT as PREDICT_T2PMHC_GAT_GRAPHS               } from '../../../modules/local/t2pmhc/predict_t2pmhc_gat'
include { PREDICT_T2PMHC_GAT as PREDICT_T2PMHC_GAT_NOGRAPHS             } from '../../../modules/local/t2pmhc/predict_t2pmhc_gat'
include { PREDICT_MIXTCRPRED                                            } from '../../../modules/local/mixtcrpred/predict_mixtcrpred'
include { COMBINE_MIXTCRPRED                                            } from '../../../modules/local/mixtcrpred/combine_mixtcrpred'
include { PREDICT_MIXTCRPRED_PAN                                        } from '../../../modules/local/mixtcrpred/predict_mixtcrpred_pan'
include { PREDICT_TABR_BERT                                             } from '../../../modules/local/tabr-bert/predict_tabr_bert'
include { CREATE_TCREN_DIRS                                             } from '../../../modules/local/tcren/create_tcren_dirs'
include { PREPARE_TCREN                                                 } from '../../../modules/local/tcren/prepare_tcren'
include { PREDICT_TCREN                                                 } from '../../../modules/local/tcren/predict_tcren'
include { PREDICT_ERGO2                                                 } from '../../../modules/local/ergo2/predict_ergo2'

workflow PREDICTION {
    take:
        ch_samplesheet

    main:
        ch_versions = Channel.empty()

        ch_samplesheet.branch {
            meta, samplesheet, graphs ->
                gcn: meta.id == "gcn"
                gat: meta.id == "gat"
                gcn_ots: meta.id == "gcn-ots"
                gcn_globmean: meta.id == "gcn-globmean"
                gcn_100: meta.id == "gcn-100"
                mixtcrpred: meta.id == "mixtcrpred"
                mixtcrpred_pan: meta.id == "mixtcrpred-pan"
                tabr_bert: meta.id == "tabr-bert"
                tcren: meta.id == "tcren"
                ergo2: meta.id == "ergo2"
            }
            .set { prediction_ch}

        // get seen/unseen
        ch_metadata = ch_samplesheet
                            .map { meta, samplesheet, graphs -> [meta, samplesheet] }
                            .collect()

        //ch_metadata.dump(tag: "metadata")
        //TODO: COMBINE THEM ALL TOGETHER

        
        // =========================================================
        //          t2pmhc -- GCN
        // =========================================================

        gcn_ch = prediction_ch.gcn

        
        gcn_ch.branch {
            meta, samplesheet, graphs ->
                with_graphs: !graphs.isEmpty()
                no_graphs: graphs.isEmpty()
        }
        .set { gcn_graph_ch }

        // predict those where graphs are already present
        PREDICT_T2PMHC_GCN_GRAPHS (
            gcn_graph_ch.with_graphs,
        )

        // create graphs for those without
        CREATE_T2PMHC_GRAPHS_GCN(
            gcn_graph_ch.no_graphs
        )

        // CREATE_T2PMHC_GRAPHS_GCN.out.graphs.dump(tag:"gcn_graphs")

        predict_in_ch = gcn_graph_ch.no_graphs.join(CREATE_T2PMHC_GRAPHS_GCN.out.graphs)
                            .map { meta, samplesheet, empty_graphs, graphs ->
                                    [meta, samplesheet, graphs]
                            }

        // predict binding for newly created graphs
        PREDICT_T2PMHC_GCN_NOGRAPHS (
            predict_in_ch,
        )

        // =========================================================
        //          t2pmhc -- GAT
        // =========================================================

        gat_ch = prediction_ch.gat

        
        gat_ch.branch {
            meta, samplesheet, graphs ->
                with_graphs: !graphs.isEmpty()
                no_graphs: graphs.isEmpty()
        }
        .set { gat_graph_ch }

        // predict with graphs
        PREDICT_T2PMHC_GAT_GRAPHS ( 
            gat_graph_ch.with_graphs,
        )
        
        // create graphs for those without
        CREATE_T2PMHC_GRAPHS_GAT(
            gat_graph_ch.no_graphs
        )

        gat_predict_in_ch = gat_graph_ch.no_graphs.join(CREATE_T2PMHC_GRAPHS_GAT.out.graphs)
                            .map { meta, samplesheet, empty_graphs, graphs ->
                                    [meta, samplesheet, graphs]
                            }

        // predict with newly created graphs
        PREDICT_T2PMHC_GAT_NOGRAPHS ( 
            gat_predict_in_ch
        )

        // =========================================================
        //          mixtcrpred
        // =========================================================
        mixtcrpred_path         = file("${projectDir}/bin/MixTCRpred")
        mixtcrpred_models       = file("${projectDir}/bin/MixTCRpred/pretrained_models")
        pan_model               = file("${projectDir}/bin/MixTCRpred/pretrained_models/mixtrcpred_pan_epitope.ckpt")

        print(pan_model)
        prediction_ch.mixtcrpred_pan.dump(tag: "pan")

        PREDICT_MIXTCRPRED (
            prediction_ch.mixtcrpred,
            mixtcrpred_path,
            mixtcrpred_models
        )

        COMBINE_MIXTCRPRED (
            PREDICT_MIXTCRPRED.out.mixtcrpred_results
        )

        // mixtcrpred pan
        PREDICT_MIXTCRPRED_PAN (
            prediction_ch.mixtcrpred_pan,
            mixtcrpred_path,
            pan_model
        )

        

        // =========================================================
        //          TABR-BERT
        // =========================================================

        PREDICT_TABR_BERT (
            prediction_ch.tabr_bert
        )

        // =========================================================
        //          ERGO-II
        // =========================================================

        PREDICT_ERGO2 (
            prediction_ch.ergo2
        )

        // =========================================================
        //          tcren
        // =========================================================

        // prepare_tcren_ch = prediction_ch.tcren
        //     .map { meta, samplesheet, graphs ->
        //         def rows = samplesheet.splitCsv(header: true, sep: '\t')
                
        //         // Extract paths
        //         def paths = rows.collect { row ->
        //             file(row.pdb_file_path)
        //         }
        //         // Extract chainseq
        //         def chainseqs = rows.collect { row ->
        //             row.target_chainseq   
        //         }
                
        //         // Extract peptides and create text file
        //         def peptides = rows.collect { row -> row.peptide }.unique()
        //         def peptidesFile = file("${workDir}/peptides_${meta.id}_${meta.dataset}.txt")
        //         peptidesFile.text = "peptide\n" + peptides.join('\n')
                
        //         return [meta, paths, chainseqs, peptidesFile]
        //     }

        // // adapt the pdbs
        // PREPARE_TCREN (
        //     prepare_tcren_ch
        // )

        // // predict the structures
        // PREDICT_TCREN (
        //     PREPARE_TCREN.out.tcren_pdbs
        // )

        //PREPARE_TCREN.out.tcren_pdbs.dump(tag: "tcren")

        // prepare_tcren_ch = prediction_ch.tcren
        //     .map { meta, samplesheet, graphs ->
        //         // Return just what we need for CSV parsing
        //         return [meta, samplesheet]
        //     }
        //     .splitCsv(header: true, sep: '\t')
        //     .map { meta, row ->
        //         def pdb_file = file(row.pdb_file_path, checkIfExists: true)
        //         def chainseq = row.target_chainseq
        //         return [meta, pdb_file, chainseq]
        //     }

        // // first: create all necessary directores
        // CREATE_TCREN_DIRS (
        //     prediction_ch.tcren
        // )

        // // adapt the graphs
        // PREPARE_TCREN (
        //     prepare_tcren_ch
        // )

        // // create peptides.txt
        // peptides_ch = prediction_ch.tcren
        //     .map { meta, samplesheet, graphs ->
        //         def rows = samplesheet.splitCsv(header: true, sep: '\t')    
        //         // Extract peptides and create text file
        //         def peptides = rows.collect { row -> row.peptide }
        //         def peptidesFile = file("${workDir}/peptides_${meta.id}_${meta.dataset}.txt")
        //         peptidesFile.text = "peptide\n" + peptides.join('\n')
                
        //         return [meta, peptidesFile]
        //     }

        // tcren_ch = CREATE_TCREN_DIRS.out.tcren_dirs
        //     .join(peptides_ch)
        //     .dump(tag: "combined")

            

        // PREDICT_TCREN (
        //     tcren_ch
        // )

    emit:
        ch_samplesheet
}