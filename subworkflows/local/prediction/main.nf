/*
 * TODO Write short intro
 */

include { PREDICT_T2PMHC_GCN                                            } from '../../../modules/local/t2pmhc/predict_t2pmhc_gcn'
include { PREDICT_T2PMHC_GAT                                            } from '../../../modules/local/t2pmhc/predict_t2pmhc_gat'
include { PREDICT_MIXTCRPRED                                            } from '../../../modules/local/mixtcrpred/predict_mixtcrpred'
include { COMBINE_MIXTCRPRED                                            } from '../../../modules/local/mixtcrpred/combine_mixtcrpred'
include { PREDICT_MIXTCRPRED_PAN                                        } from '../../../modules/local/mixtcrpred/predict_mixtcrpred_pan'
include { PREDICT_TABR_BERT                                             } from '../../../modules/local/tabr-bert/predict_tabr_bert'
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

        PREDICT_T2PMHC_GCN (
            prediction_ch.gcn
        )

        // =========================================================
        //          t2pmhc -- GAT
        // =========================================================

        PREDICT_T2PMHC_GAT (
            prediction_ch.gat
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

    emit:
        ch_samplesheet
}