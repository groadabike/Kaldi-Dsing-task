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
sing_corpus=/fastdata/acp13gr/DAMP300x30x20/sing_300x30x2


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

    for datadir in $devset $testset $trainset; do
        python local/prepare_data.py data/ wav/ conf/${datadir}.json $datadir
    done

    # Selecting the top 25000 words by frequency
    # Is expected that the final size will be larger as
    # it use all the words with the same frequency avoiding an arbitrary cut-off
    local/prepare_dict.sh --words 26000

    utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang

    local/train_lms_srilm.sh \
        --train-text data/local/corpus.txt \
        --dev_text data/dev/text \
        --oov-symbol "<UNK>" --words-file data/lang/words.txt \
        data/ data/srilm

    # Compiles G for DSing Preconstructed trigram LM
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
    steps/make_mfcc.sh --cmd "$train_cmd" --nj $nj data/${datadir} exp/make_mfcc/${datadir} mfcc
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

    steps/align_si.sh --nj $nj --cmd "$train_cmd" \
      data/${trainset} data/lang exp/mono exp/mono_ali
    
    echo
    echo "Tri 1 - delta-based triphones"
    echo "=====  $(date +"%D_%T") ====="
    
    # Tri1      


    steps/train_deltas.sh  --cmd "$train_cmd" 2000 15000 \
      data/${trainset} data/lang exp/mono_ali exp/tri1

    steps/align_si.sh --nj $nj --cmd "$train_cmd"  \
     data/${trainset} data/lang exp/tri1 exp/tri1_ali
      
    echo
    echo "Tri 2 - LDA-MLLT triphones"
    echo "=====  $(date +"%D_%T") ====="
    # Tri2  


    steps/train_lda_mllt.sh --cmd "$train_cmd" 2500 20000 \
      data/${trainset} data/lang exp/tri1_ali exp/tri2b

    steps/align_si.sh --nj $nj --cmd "$train_cmd"  \
      data/${trainset} data/lang exp/tri2b exp/tri2b_ali
      
    echo
    echo "Tri 3 - SAT triphones"
    echo "=====  $(date +"%D_%T") ====="
   
    # Tri3 SAT


    steps/train_sat.sh --cmd "$train_cmd" 3000 25000 \
      data/${trainset} data/lang exp/tri2b_ali exp/tri3b

    utils/mkgraph.sh data/lang_3G exp/tri3b exp/tri3b/graph
   
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


    
    echo; echo "--------decode ${devset}"; echo
    steps/decode_fmllr.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
      --scoring-opts "--min-lmwt 10 --max-lmwt 20" --num-threads 4  \
      exp/tri3b/graph data/${devset} exp/tri3b/decode_${devset}


    # Scoring test model with the best
    lmwt=$(cat exp/tri3b/decode_${devset}/scoring_kaldi/wer_details/lmwt)
    wip=$(cat exp/tri3b/decode_${devset}/scoring_kaldi/wer_details/wip)
    echo; echo "--------decode ${testset}"
    echo "Using [lmwt=$lmwt, wip=$wip] to score"; echo
    steps/decode_fmllr.sh --config conf/decode.config --nj $nj --cmd "$decode_cmd" \
      --scoring-opts "--min_lmwt $lmwt --max_lmwt $lmwt --word_ins_penalty $wip" --num-threads 4  \
      exp/tri3b/graph data/${testset} exp/tri3b/decode_${testset}


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

    local/chain/run_tdnn_1d.sh --nj $nj --decode_nj $decode_nj --stage 15 \
    --train_set ${trainset}_cleaned --test_sets "$devset $testset" \
    --gmm tri3b_cleaned --nnet3-affix _${trainset}_cleaned
fi


if [[ $stage -le 7 ]]; then
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
echo "===== PROCESS ENDED ====="
echo

exit 1
