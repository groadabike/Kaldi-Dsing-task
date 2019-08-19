#!/bin/bash
#$ -V
#$ -l h_rt=96:00:00
#$ -l rmem=50G
#$ -j y
#$ -o log_DSing_decode.txt
#$ -e log_DSing_decode.txt
#$ -m bea
#$ -M groadabike1@sheffield.ac.uk
#$ -N dec_DSing
#$ -P rse
#$ -q rse.q




echo "$0 $@" # Print the command line for logging

. ./path.sh || exit 1
. ./cmd.sh || exit 1
. ./setup_env.sh

# configuration section

trainset="train"
valset="dev"
testset="test"
nj=1
stage=0
dsing=1  # 1 will use DSing1, 3 will use DSing3, 30 will use DSing30

# For TDNN-F only

decode_nj=1

# End configuration section

if [[ "$HOSTNAME" == *"sharc"* ]]; then
    export DATA_ROOT=/fastdata/acp13gr/DAMP300x30x20/sing_300x30x2
else
    export DATA_ROOT=/media/gerardo/SoloSinging/DAMP/sing_300x30x2
fi

echo "Using steps and utils from WSJ recipe"
[[ ! -L "wav" ]] && ln -s $DATA_ROOT wav
[[ ! -L "steps" ]] && ln -s $KALDI_ROOT/egs/wsj/s5/steps
[[ ! -L "utils" ]] && ln -s $KALDI_ROOT/egs/wsj/s5/utils

. utils/parse_options.sh


filename=${PWD##*/}

# Features Extraction
if [[ $stage -le 2 ]]; then

    echo
    echo "============================="
    echo "---- Features Extraction ----"
    echo "=====  $(date +"%D_%T") ====="

    for set in $valset $testset; do
        local/multiple_features_extraction.sh --nj $nj --set $set
    done
fi



if [[ $stage -le 4 ]]; then
    echo
    echo "... Decode TRI3B - Best GMM results"
    echo "=====  $(date +"%D_%T") ====="
    echo

    if [[ ! -f exp/tri3b/graph/HCLG.fst ]]; then
        utils/mkgraph.sh data/lang_3G exp/tri3b exp/tri3b/graph
     fi

    for val in ${valset}; do
        echo
        echo "--------decode $val"

        if [[ ! exp/tri3b/decode_${val}/scoring_kaldi/best_wer ]]; then
            steps/decode_fmllr.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
              --scoring-opts "--min-lmwt 10 --max-lmwt 20" --num-threads 4  \
              exp/tri3b/graph data/${val} exp/tri3b/decode_${val}
        fi
    done

    for test in ${testset}; do
        echo
        echo "--------decode $test"

        lmwt=$(cat exp/tri3b/decode_dev/scoring_kaldi/wer_details/lmwt)
        wip=$(cat exp/tri3b/decode_dev/scoring_kaldi/wer_details/wip)

        if [[ ! exp/tri3b/decode_${test}/scoring_kaldi/best_wer ]]; then
            echo "Using lmwt=$lmwt and wip=$wip"
            steps/decode_fmllr.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
              --scoring-opts "--min_lmwt $lmwt --max_lmwt $lmwt --word_ins_penalty $wip" --num-threads 4  \
              exp/tri3b/graph data/${test} exp/tri3b/decode_${test}
        fi
    done

fi


if [[ $stage -le 11 ]]; then
    echo "===== TDNN-F ====="
    echo "=====  $(date +"%D_%T") ====="
    for set in ${valset} ; do
        local/chain/run_tdnn_1d_decode.sh --nj $nj --decode_nj $decode_nj --stage 0 \
        --train_set ${trainset}_cleaned --test_sets "$set" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned
    done

    for set in ${testset} ; do
        lmwt=$(cat exp/chain_train_cleaned/tdnn_1d_sp/decode_test_gold_3G/scoring_kaldi/wer_details/lmwt)
        wip=$(cat exp/chain_train_cleaned/tdnn_1d_sp/decode_test_gold_3G/scoring_kaldi/wer_details/wip)
        
        local/chain/run_tdnn_1d_decode.sh --nj $nj --decode_nj $decode_nj --stage 0 \
        --scoring_opts "--min-lmwt $lmwt --max-lmwt $lmwt --word_ins_penalty $wip" \
        --train_set ${trainset}_cleaned --test_sets "$set" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned
    done
    
fi

if [[ $stage -le 12 ]]; then
    echo "==== SCORING MODELS ===="
    echo "=====  $(date +"%D_%T") ====="
        for x in `find exp -name "decode*"`; do
            [[ -d $x ]] && grep WER $x/wer_* | utils/best_wer.sh
        done
fi

echo
echo "=====  $(date +"%D_%T") ====="
echo "===== PROCESS $filename FINISHED =====" | tr [a-z] [A-Z]
echo

exit 1
