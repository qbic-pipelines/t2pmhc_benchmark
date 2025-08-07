/*
 * TODO Write short intro
 */

include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GCN     } from '../../../modules/local/t2pmhc/create_graphs' 
include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GCN_OTS } from '../../../modules/local/t2pmhc/create_graphs' 
include { CREATE_T2PMHC_GRAPHS as  CREATE_T2PMHC_GRAPHS_GAT     } from '../../../modules/local/t2pmhc/create_graphs' 
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_GRAPHS       } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_NOGRAPHS     } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_OTS_GRAPHS   } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GCN as PREDICT_T2PMHC_GCN_OTS_NOGRAPHS } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GAT as PREDICT_T2PMHC_GAT_GRAPHS       } from '../../../modules/local/t2pmhc/predict_t2pmhc_gat'
include { PREDICT_T2PMHC_GAT as PREDICT_T2PMHC_GAT_NOGRAPHS     } from '../../../modules/local/t2pmhc/predict_t2pmhc_gat'
include { PREDICT_MIXTCRPRED    } from '../../../modules/local/mixtcrpred/predict_mixtcrpred'
include { COMBINE_MIXTCRPRED    } from '../../../modules/local/mixtcrpred/combine_mixtcrpred'
include { PREDICT_TABR_BERT     } from '../../../modules/local/tabr-bert/predict_tabr_bert'


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
                mixtcrpred: meta.id == "mixtcrpred"
                tabr_bert: meta.id == "tabr-bert"
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
        // Reference the prediction files
        hyperparams_gcn = file("${projectDir}/bin/hyperparams/hyperparams_final_gcn.json")
        model_gcn       = file("${projectDir}/bin/models/gcn_final.pt")
        pae_full_gcn    = file("${projectDir}/bin/scalers/gcn_final_pae_node_FULL.pkl")
        pae_tpmhc_gcn   = file("${projectDir}/bin/scalers/gcn_final_pae_node_TCRPMHC.pkl")

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
            hyperparams_gcn,
            model_gcn,
            pae_full_gcn,
            pae_tpmhc_gcn
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
            hyperparams_gcn,
            model_gcn,
            pae_full_gcn,
            pae_tpmhc_gcn
        )

        // =========================================================
        //          t2pmhc -- GCN OTS
        // =========================================================
        // Reference the prediction files
        hyperparams_gcn_ots = file("${projectDir}/bin/hyperparams/hyperparams_final_gcn_ots.json")
        model_gcn_ots       = file("${projectDir}/bin/models/gcn_ots_final.pt")
        pae_full_gcn_ots    = file("${projectDir}/bin/scalers/gcn_ots_final_pae_node_FULL.pkl")
        pae_tpmhc_gcn_ots   = file("${projectDir}/bin/scalers/gcn_ots_final_pae_node_TCRPMHC.pkl")

        gcn_ots_ch = prediction_ch.gcn_ots

        
        gcn_ots_ch.branch {
            meta, samplesheet, graphs ->
                with_graphs: !graphs.isEmpty()
                no_graphs: graphs.isEmpty()
        }
        .set { gcn_ots_graph_ch }


        // predict those where graphs are already present
        PREDICT_T2PMHC_GCN_OTS_GRAPHS (
            gcn_ots_graph_ch.with_graphs,
            hyperparams_gcn,
            model_gcn,
            pae_full_gcn,
            pae_tpmhc_gcn
        )

        // create graphs for those without
        CREATE_T2PMHC_GRAPHS_GCN_OTS(
            gcn_ots_graph_ch.no_graphs
        )

        // CREATE_T2PMHC_GRAPHS_GCN.out.graphs.dump(tag:"gcn_graphs")

        gcn_ots_predict_in_ch = gcn_ots_graph_ch.no_graphs.join(CREATE_T2PMHC_GRAPHS_GCN_OTS.out.graphs)
                            .map { meta, samplesheet, empty_graphs, graphs ->
                                    [meta, samplesheet, graphs]
                            }

        // predict binding for newly created graphs
        PREDICT_T2PMHC_GCN_OTS_NOGRAPHS (
            gcn_ots_predict_in_ch,
            hyperparams_gcn_ots,
            model_gcn_ots,
            pae_full_gcn_ots,
            pae_tpmhc_gcn_ots
        )

        // =========================================================
        //          t2pmhc -- GAT
        // =========================================================
        hyperparams_gat = file("${projectDir}/bin/hyperparams/hyperparams_final_gat.json")
        model_gat       = file("${projectDir}/bin/models/gat_final.pt")
        pae_full_gat    = file("${projectDir}/bin/scalers/gat_final_pae_node_FULL.pkl")
        pae_tpmhc_gat   = file("${projectDir}/bin/scalers/gat_final_pae_node_TCRPMHC.pkl")
        pae_edge_gat    = file("${projectDir}/bin/scalers/gat_final_pae_edge_FULL.pkl")
        hydro_gat       = file("${projectDir}/bin/scalers/gat_final_hydro.pkl")
        distance_gat    = file("${projectDir}/bin/scalers/gat_final_distance.pkl")

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
            hyperparams_gat,
            model_gat,
            pae_full_gat,
            pae_tpmhc_gat,
            pae_edge_gat,
            hydro_gat,
            distance_gat
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
            gat_predict_in_ch,
            hyperparams_gat,
            model_gat,
            pae_full_gat,
            pae_tpmhc_gat,
            pae_edge_gat,
            hydro_gat,
            distance_gat
        )

        // =========================================================
        //          mixtcrpred
        // =========================================================
        mixtcrpred_path         = file("${projectDir}/bin/MixTCRpred")
        mixtcrpred_models       = file("${projectDir}/bin/MixTCRpred/pretrained_models")

        PREDICT_MIXTCRPRED (
            prediction_ch.mixtcrpred,
            mixtcrpred_path,
            mixtcrpred_models
        )

        COMBINE_MIXTCRPRED (
            PREDICT_MIXTCRPRED.out.mixtcrpred_results
        )

        

        // =========================================================
        //          TABR-BERT
        // =========================================================

        PREDICT_TABR_BERT (
            prediction_ch.tabr_bert
        )

    emit:
        ch_samplesheet
}