#!/bin/bash

# extract mfcc features

# Begin configuration section.
nj=4
datadir=
mfcc_conf=conf/mfcc.conf
compress=true
write_utt2num_frames=false  # if true writes utt2num_frames
# End configuration section.


echo "$0 $@" # Print the command line for logging

. ./cmd.sh
. ./path.sh
. utils/parse_options.sh

utils/fix_data_dir.sh data/$datadir
steps/make_mfcc.sh --nj $nj --cmd "$train_cmd" --write_utt2num_frames $write_utt2num_frames \
  --compress $compress --mfcc-config $mfcc_conf  data/$datadir data/$datadir/mfcc/log data/$datadir/mfcc
steps/compute_cmvn_stats.sh data/${datadir}
utils/fix_data_dir.sh data/$datadir



