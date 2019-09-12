#!/bin/bash

output_directory=/DSing
DAMP_path=/DAMP/sing_300x30x2/
for dataset in test; do
    echo "--> Creating $dataset"
    python prepare_data.py $output_directory $DAMP_path $dataset
done
