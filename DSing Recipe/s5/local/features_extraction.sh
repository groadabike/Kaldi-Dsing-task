#!/bin/bash

# This script extract mfcc features
# if --use_plp=true
# the final features will be mfcc + plp + delta + delta-delta

# Begin configuration section.
nj=4
set=
# End configuration section.


echo "$0 $@" # Print the command line for logging

. ./cmd.sh
. ./path.sh
. utils/parse_options.sh

echo
echo "===== FEATURES EXTRACTION ====="
echo


for dataset in ${set}; do
    utils/fix_data_dir.sh data/$dataset
    steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" data/$dataset exp/make_mfcc/$dataset mfcc
    steps/compute_cmvn_stats.sh data/${dataset} exp/make_mfcc/${dataset} mfcc
    utils/fix_data_dir.sh data/$dataset
    utils/data/get_utt2dur.sh data/$dataset
done

