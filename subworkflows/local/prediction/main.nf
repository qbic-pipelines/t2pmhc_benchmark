/*
 * Prepares the raw or compressed data holding spectra information for the subsequent database search.
 */

// include { THERMORAWFILEPARSER    } from '../../../modules/nf-core/thermorawfileparser/main'
include { PREDICT_T2PMHC_GCN } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GAT } from '../../../modules/local/t2pmhc/predict_t2pmhc_gat'
include { PREDICT_MIXTCRPRED } from '../../../modules/local/mixtcrpred/predict_mixtcrpred'
include { COMBINE_MIXTCRPRED } from '../../../modules/local/mixtcrpred/combine_mixtcrpred'
include { PREDICT_TABR_BERT } from '../../../modules/local/tabr-bert/predict_tabr_bert'


workflow PREDICTION {
    take:
        ch_samplesheet

    main:
        ch_versions = Channel.empty()

        ch_samplesheet.branch {
            meta, samplesheet, graphs ->
                gcn: meta.id == "gcn"
                gat: meta.id == "gat"
                mixtcrpred: meta.id == "mixtcrpred"
                tabr_bert: meta.id == "tabr_bert"
            }
            .set { prediction_ch}

        
        // =========================================================
        //          t2pmhc -- GCN
        // =========================================================
        // Reference the prediction files
        hyperparams_gcn = file("${projectDir}/bin/hyperparams/hyperparams_final_gcn.json")
        model_gcn       = file("${projectDir}/bin/models/gcn_final.pt")
        pae_full_gcn    = file("${projectDir}/bin/scalers/gcn_final_pae_node_FULL.pkl")
        pae_tpmhc_gcn   = file("${projectDir}/bin/scalers/gcn_final_pae_node_TCRPMHC.pkl")
        
        PREDICT_T2PMHC_GCN ( 
            prediction_ch.gcn,
            hyperparams_gcn,
            model_gcn,
            pae_full_gcn,
            pae_tpmhc_gcn
        )

        // =========================================================
        //          t2pmhc -- GAT
        // =========================================================
        hyperparams_gat = file("${projectDir}/bin/hyperparams/hyperparams_standard_gat.json")
        model_gat       = file("${projectDir}/bin/models/gat_gpu.pt")
        pae_full_gat    = file("${projectDir}/bin/scalers/gat_gpu_pae_node_FULL.pkl")
        pae_tpmhc_gat   = file("${projectDir}/bin/scalers/gat_gpu_pae_node_TCRPMHC.pkl")
        pae_edge_gat    = file("${projectDir}/bin/scalers/gat_gpu_pae_edge_FULL.pkl")
        hydro_gat       = file("${projectDir}/bin/scalers/gat_gpu_hydro.pkl")
        distance_gat    = file("${projectDir}/bin/scalers/gat_gpu_distance.pkl")

        PREDICT_T2PMHC_GAT ( 
            prediction_ch.gat,
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