#!/bin/bash

# This script is not really finished, all it does is train a model with its
# means adapted to the female data, to demonstrate MAP adaptation.  To have real
# gender dependent decoding (which anyway we're not very enthused about), we
# would have to train both models, do some kind of gender identification, and
# then decode.  Or we could use the gender information in the test set.  But
# anyway that's not a direction we really want to go right now.

trainset=train_guitar
testset="test_guitar test_piano"
gmm=tri3b
nj=8
stage=1


echo "$0 $@" # Print the command line for logging

. ./cmd.sh
. ./path.sh
. utils/parse_options.sh


tau=20

for gender in f m; do

if [[ $stage -le 1 ]]; then
    echo ; echo "====== Training Gender Dep. for Gender $gender ========"; echo ;
    #awk '{if ($2 == "$gender") { print $1; }}' < data/$trainset/spk2gender > data/$trainset/spklist_${gender}
    cat data/$trainset/spk2gender | grep $gender| awk '{ print $1}' >  data/$trainset/spklist_${gender}
    utils/subset_data_dir.sh --spk-list data/$trainset/spklist_${gender} data/$trainset data/${trainset}_${gender}

    for tset in $testset; do
        #awk '{if ($2 == $gender) { print $1; }}' < data/$tset/spk2gender > data/$tset/spklist_${gender}
        cat data/$tset/spk2gender | grep $gender| awk '{ print $1}' >  data/$tset/spklist_${gender}
        utils/subset_data_dir.sh --spk-list data/$tset/spklist_${gender} data/$tset data/${tset}_${gender}
    done
fi

#    numspk=`echo for s in "$trainset $testset"; do echo cat data/${s}_${gender}/spk2gender | wc -l ; done`
#    echo "numspk $numspk"
#done
#    exit;
#    min_nj=( echo $nj; echo $numspk ) | sort -rn | tail -1

    min_nj=5

if [[ $stage -le 2 ]]; then
    steps/align_si.sh  --nj $min_nj --cmd "$train_cmd" \
        data/${trainset}_${gender} data/lang exp/$gmm exp/${gmm}_ali_${gender}

    for t in $tau ; do
        echo ; echo "Tau = $t"
        steps/train_map.sh --cmd "$train_cmd" --tau $t data/${trainset}_${gender} data/lang exp/${gmm}_ali_${gender} exp/${gmm}_${gender}/tau_${t}
    done

fi

if [[ $stage -le 3 ]]; then
    # Decoding
    echo ; echo "......Decoding Gender Dep. for gender $gender"

    for t in $tau; do
        echo ; echo "Tau = $t"
        utils/mkgraph.sh data/lang exp/${gmm}_${gender}/tau_${t} exp/${gmm}_${gender}/tau_${t}/graph
    done


    for t in $tau; do
        for test in $testset; do
            echo
            echo "--------decode $test"
            steps/decode_fmllr.sh --config conf/decode.config --nj $min_nj --cmd "$decode_cmd" \
              --scoring-opts "--min-lmwt 10 --max-lmwt 20" --num-threads 1  \
              exp/${gmm}_${gender}/tau_${t}/graph data/${test}_${gender} exp/${gmm}_${gender}/tau_${t}/decode_${test} &
        done
        wait;
    done
fi
done

