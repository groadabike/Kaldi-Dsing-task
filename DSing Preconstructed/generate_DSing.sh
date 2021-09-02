#!/bin/bash

output_directory=/DSing
DAMP_path=/DAMP/sing_300x30x2/
for dataset in test dev train{1,3,30} ; do
    echo "--> Creating $dataset"
    python prepare_data.py $output_directory $DAMP_path $dataset
done
