#!/bin/bash
#
# Recipe for the Dsing baseline
# Based mostly on the Librispeech recipe
#
# Copyright 2019  Gerardo Roa
#                 University of Sheffield
# Apache 2.0

# Begin configuration section

nj=40
stage=0
dsing=1   #  Set:  1  for DSing1
          #        3  for DSing3
          #        30 for DSing30

# For TDNN-F only
decode_nj=1

# End configuration section
. ./utils/parse_options.sh

. ./path.sh
. ./cmd.sh

set -e # exit on error

# Sing! 300x30x2 corpus path
# please change the path accordingly
sing_corpus=/export/DAMP300x30x20/sing_300x30x2


echo "Using steps and utils from WSJ recipe"
[[ ! -L "wav" ]] && ln -s $sing_corpus wav
[[ ! -L "steps" ]] && ln -s $KALDI_ROOT/egs/wsj/s5/steps
[[ ! -L "utils" ]] && ln -s $KALDI_ROOT/egs/wsj/s5/utils


trainset=train${dsing}
devset="dev"
testset="test"

# This script also needs the phonetisaurus g2p, srilm, sox
./local/check_tools.sh || exit 1


echo; echo "===== Starting at  $(date +"%D_%T") ====="; echo


if [ $stage -le 1 ]; then
    mkdir -p data/local/dict
    cp conf/corpus.txt  data/local/corpus.txt  # Corpus.txt for language model

    # Selecting the top 25000 words by frequency
    # Is expected that the final size will be larger as
    # it use all the words with the same frequency avoiding an arbitrary cut-off
    local/prepare_dict.sh --words 25000 --traiset $trainset --devset $devset --testset $testset

    utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang

    local/train_lms_srilm.sh \
        --train-text data/local/corpus.txt \
        --dev_text data/dev/text \
        --oov-symbol "<UNK>" --words-file data/lang/words.txt \
        data/ data/srilm

    # Compiles G for DSing trigram LM
    utils/format_lm.sh  data/lang data/srilm/best_3gram.gz data/local/dict/lexicon.txt data/lang_3G
    utils/format_lm.sh  data/lang data/srilm/best_4gram.gz data/local/dict/lexicon.txt data/lang_4G
fi

# Features Extraction
if [[ $stage -le 2 ]]; then

  echo
  echo "============================="
  echo "---- MFCC FEATURES EXTRACTION ----"
  echo "=====  $(date +"%D_%T") ====="

  for datadir in $trainset $devset $testset; do
    echo; echo "---- $datadir"
    utils/fix_data_dir.sh data/$datadir

    if [ "$use_pitch" = "false" ] && [ "$use_beat" = "false" ]; then
     steps/make_mfcc.sh --cmd "$train_cmd" --nj $nj data/${datadir} exp/make_mfcc/${datadir} mfcc

    elif [ "$use_pitch" = "true" ] && [ "$use_beat" = "true" ]; then
      cp -rT data/${datadir} data/${datadir}_mfcc; cp -rT data/${datadir} data/${datadir}_pitch; cp -rT data/${datadir} data/${datadir}_beat
      steps/make_mfcc.sh --cmd "$train_cmd" --nj $nj data/${datadir}_mfcc exp/make_mfcc/${datadir} mfcc_tmp_train
      local/make_pitch.sh --cmd "$train_cmd" --nj $nj --pitch-config $conf_pitch data/${datadir}_pitch exp/make_pitch/${datadir} pitch_tmp_train
      local/make_beat.sh --cmd "$train_cmd"  --nj $nj data/${datadir}_beat exp/make_beat/${datadir} beat_tmp_train
      steps/append_feats.sh --cmd "$train_cmd" --nj $nj data/${datadir}{_mfcc,_pitch,_mfcc_pitch} exp/make_pitch/append_train_pitch mfcc_tmp_train
      steps/append_feats.sh --cmd "$train_cmd" --nj $nj data/${datadir}{_mfcc_pitch,_beat,} exp/make_beat/append_train_pitch_beat mfcc
      rm -rf {mfcc,pitch,beat}_tmp_train data/${datadir}_{mfcc,pitch,mfcc_pitch}

    elif [ "$use_pitch" = "true" ]; then
      cp -rT data/${datadir} data/${datadir}_mfcc; cp -rT data/${datadir} data/${datadir}_pitch
      steps/make_mfcc.sh --cmd "$train_cmd" --nj $nj data/${datadir}_mfcc exp/make_mfcc/${datadir} mfcc_tmp_train
      local/make_pitch.sh --cmd "$train_cmd" --nj $nj data/${datadir}_pitch exp/make_pitch/${datadir} pitch_tmp_train
      steps/append_feats.sh --cmd "$train_cmd" --nj $nj data/${datadir}{_mfcc,_pitch,} exp/make_pitch/append_train mfcc
      rm -rf {mfcc,pitch}_tmp_train data/${datadir}_{mfcc,pitch}

    elif [ "$use_beat" = "true" ]; then
      cp -rT data/${datadir} data/${datadir}_mfcc; cp -rT data/${datadir} data/${datadir}_beat
      steps/make_mfcc.sh --cmd "$train_cmd" --nj $nj data/${datadir}_mfcc exp/make_mfcc/${datadir} mfcc_tmp_train
      local/make_beat.sh --cmd "$train_cmd" --nj $nj data/${datadir}_beat exp/make_beat/${datadir} beat_tmp_train
      steps/append_feats.sh --cmd "$train_cmd" --nj $nj data/${datadir}{_mfcc,_beat,} exp/make_beat/append_train mfcc
      rm -rf {mfcc,beat}_tmp_train data/${datadir}_{mfcc,beat}
    fi
    steps/compute_cmvn_stats.sh data/${datadir}
    utils/fix_data_dir.sh data/$datadir

  done
fi

if [[ $stage -le 3 ]]; then

    echo
    echo "============================="
    echo "-------- Train GMM ----------"
    echo

    echo
    echo "Mono"
    echo "=====  $(date +"%D_%T") ====="

    # Monophone
    steps/train_mono.sh --nj $nj --cmd "$train_cmd"  \
          data/${trainset} data/lang exp/mono
    
    echo
    echo "Tri 1"
    echo "=====  $(date +"%D_%T") ====="
    
    # Tri1      
    steps/align_si.sh --nj $nj --cmd "$train_cmd" \
      data/${trainset} data/lang exp/mono exp/mono_ali

    steps/train_deltas.sh  --cmd "$train_cmd" 2000 15000 \
      data/${trainset} data/lang exp/mono_ali exp/tri1
      
    echo
    echo "Tri 2"
    echo "=====  $(date +"%D_%T") ====="
    # Tri2  
    steps/align_si.sh --nj $nj --cmd "$train_cmd"  \
     data/${trainset} data/lang exp/tri1 exp/tri1_ali

    steps/train_lda_mllt.sh --cmd "$train_cmd" 2500 20000 \
      data/${trainset} data/lang exp/tri1_ali exp/tri2b
      
    echo
    echo "Tri 3"
    echo "=====  $(date +"%D_%T") ====="
   
    # Tri3 SAT
    steps/align_si.sh --nj $nj --cmd "$train_cmd"  \
      data/${trainset} data/lang exp/tri2b exp/tri2b_ali

    steps/train_sat.sh --cmd "$train_cmd" 3000 25000 \
      data/${trainset} data/lang exp/tri2b_ali exp/tri3b
   
    echo
    echo "------ End Train GMM --------"
    echo "=====  $(date +"%D_%T") ====="
fi


if [[ $stage -le 4 ]]; then
    echo
    echo "============================="
    echo "------- Decode TRI3B --------"
    echo "=====  $(date +"%D_%T") ====="
    echo

    utils/mkgraph.sh data/lang_3G exp/tri3b exp/tri3b/graph
    
    for val in ${devset}; do
        echo
        echo "--------decode $val"
        steps/decode_fmllr.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
          --scoring-opts "--min-lmwt 10 --max-lmwt 20" --num-threads 4  \
          exp/tri3b/graph data/${val} exp/tri3b/decode_${val}
    done

    for test in ${testset}; do
        echo
        echo "--------decode $test"

        lmwt=$(cat exp/tri3b/decode_dev/scoring_kaldi/wer_details/lmwt)
        wip=$(cat exp/tri3b/decode_dev/scoring_kaldi/wer_details/wip)
        echo "Using lmwt=$lmwt and wip=$wip"
        steps/decode_fmllr.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
          --scoring-opts "--min_lmwt $lmwt --max_lmwt $lmwt --word_ins_penalty $wip" --num-threads 4  \
          exp/tri3b/graph data/${test} exp/tri3b/decode_${test}
    done

fi

# Produce clean data
if [[ $stage -le 5 ]]; then
    echo
    echo "============================="
    echo "------- Cleanup Tri3b -------"
    echo "=====  $(date +"%D_%T") ====="
    echo

    steps/cleanup/clean_and_segment_data.sh --nj $nj --cmd "$train_cmd"  \
    --segmentation-opts "--min-segment-length 0.3 --min-new-segment-length 0.6" \
      data/${trainset} data/lang exp/tri3b exp/tri3b_cleaned \
      data/${trainset}_cleaned
fi

if [[ $stage -le 6 ]]; then
    echo
    echo "=================="
    echo "----- TDNN-F -----"
    echo "=====  $(date +"%D_%T") ====="
    echo

    local/chain/run_tdnn_1d.sh --nj $nj --decode_nj $decode_nj --stage 0 \
    --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
    --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned
fi

if [[ $stage -le 7 ]]; then

    echo
    echo "===== TDNN-F ====="
    echo "=====  $(date +"%D_%T") ====="
    # This network uses mfcc + beat + pitch
    # change --features_opt to modify turn-off one feature
    # when --do_pitch false and  --do_beat false the system is similar than 1d recipe
    # 1d_2a = mfcc + 4 pitch features
    # 1d_2b = mfcc + 3 pitch features (No raw log pitch)
    # 1d_2c = mfcc + 2 pitch features (No raw log pitch, no pov)
    # 1d_2d = mfcc + norm pitch features (No raw log pitch, no pov, no delta pitch)
    # 1d_2e = mfcc + norm pitch + POV

    for x in 2a 2b 2c 2d 2e 2f 2g; do
        local/chain/run_tdnn_1d_${x}.sh --nj $nj --decode_nj $decode_nj --stage 14 \
        --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned \
        --affix 1d_${x} \
        --do_mfcc true --do_pitch true --do_beat false
    done

fi

if [[ $stage -le 8 ]]; then

    echo
    echo "===== TDNN-F ====="
    echo "=====  $(date +"%D_%T") ====="
    # This network uses mfcc + beat + pitch
    # change --features_opt to modify turn-off one feature
    # when --do_pitch false and  --do_beat false the system is similar than 1d recipe
    # 1d_3a = mfcc + beat fill gap
    # 1d_3b = mfcc + beat no fill gaps


    for x in 3a 3b 3c 3d; do
        local/chain/run_tdnn_1d_${x}.sh --nj $nj --decode_nj $decode_nj --stage 14 \
        --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned \
        --affix 1d_${x} \
        --do_mfcc true --do_pitch false --do_beat true
    done

fi


if [[ $stage -le 9 ]]; then

    echo
    echo "===== TDNN-F ====="
    echo "=====  $(date +"%D_%T") ====="
    # This network uses mfcc + pyin

     local/chain/run_tdnn_1d.sh --nj $nj --decode_nj $decode_nj --stage 0 \
    --train_set ${trainset} --test_sets "$devset $testset" \
    --gmm tri3b --nnet3-affix _${trainset}

    for x in 7a; do
        local/chain/run_tdnn_1d_${x}.sh --nj $nj --decode_nj $decode_nj --stage 14 \
        --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned \
        --affix 1d_${x} \
        --do_mfcc true --do_pitch false --do_beat false --do-tempo false --do-pyin true
    done

fi


if [[ $stage -le -1 ]]; then

    echo
    echo "===== TDNN-F ====="
    echo "=====  $(date +"%D_%T") ====="
    # This network uses mfcc + beat + pitch
    # change --features_opt to modify turn-off one feature
    # when --do_pitch false and  --do_beat false the system is similar than 1d recipe
    # 1d_3a = mfcc + beat fill gap
    # 1d_3b = mfcc + beat no fill gaps


    for x in 4; do
        local/chain/run_tdnn_1d_${x}.sh --nj $nj --decode_nj $decode_nj --stage 14 \
        --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned \
        --affix 1d_${x} \
        --do_mfcc true --do_pitch true --do_beat true
    done

fi

if [[ $stage -le -1 ]]; then

    echo
    echo "===== TDNN-F ====="
    echo "=====  $(date +"%D_%T") ====="
    # This network uses mfcc + beat + pitch
    # change --features_opt to modify turn-off one feature
    # when --do_pitch false and  --do_beat false the system is similar than 1d recipe
    # 1d_3a = mfcc + beat fill gap
    # 1d_3b = mfcc + beat no fill gaps


    for x in 5; do
        local/chain/run_tdnn_1d_${x}.sh --nj $nj --decode_nj $decode_nj --stage 14 \
        --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
        --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned \
        --affix 1d_${x} \
        --do_mfcc true --do_pitch false --do_beat false --do_tempo true
    done

fi

if [[ $stage -le 12 ]]; then
    echo
    echo "============================="
    echo "------- FINAL SCORES --------"
    echo "=====  $(date +"%D_%T") ====="
    echo

    for x in `find exp/* -name "best_wer"`; do
        cat $x | grep -v ".si"
    done
fi

echo
echo "=====  $(date +"%D_%T") ====="
echo "===== PROCESS $filename FINISHED =====" | tr [a-z] [A-Z]
echo

exit 1
