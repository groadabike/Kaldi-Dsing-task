#!/bin/bash

# "queue.pl" uses qsub.  The options to it are
# options to qsub.  If you have GridEngine installed,
# change this to a queue you have access to.
# Otherwise, use "run.pl", which will run jobs locally
# (make sure your --num-jobs options are no more than
# the number of cpus on your machine.

# This cmd.sh file is to be used on Sharc in RSE queue

export train_cmd="run.pl"
export decode_cmd="run.pl"


if [[ "$HOSTNAME" == *"sharc"* ]]; then
    export train_cmd="queue.pl --mem 6G"
    export decode_cmd="queue.pl --mem 8G"
fi
if [[ "$HOSTNAME" == *"bessemer"* ]]; then
    export train_cmd="slurm.pl --mem 6G"
    export decode_cmd="slurm.pl --mem 8G"

fi
