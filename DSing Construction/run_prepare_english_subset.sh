#!/usr/bin/env bash

# Current script will create a copy of several of the files

echo "Starting to process the DAMP Sing!300x30x2 dataset"
echo "The objective of this process is to generate a solo-singing dataset"
echo "for Lyrics Transcription researches"
echo; echo "There are three versions of this solo-singing English Dataset"
echo "DSing1  = The English spoken recordings from users registered as GB in Smule application"
echo "DSing3  = The English spoken recordings from GB plus the English spoken recordings from users where the country registered in Smule are US or ZA"
echo "DSing30 = The English spoken recordings from GB plus all the other English spoken recordings regardless of the registered country."

version=$1

workspace=/media/gerardo/SoloSinging/${version}
db_path=/media/gerardo/SoloSinging/DAMP/sing_300x30x2

python set_workspace.py --db=${version} $workspace

python copy_lyrics.py $workspace $db_path

python identify_wordlevel_lyrics.py $workspace

# This step has problem.
# Smule changes the divs and block scrapping
#python scraping_lyrics.py  $workspace $db_path

python word_to_sentence_level.py $workspace

python select_english_subset.py $workspace

python reformat_annotation.py $workspace

python realign_annotation.py $workspace $db_path

python extract_utterances.py $workspace $db_path

python split_train_dev_test.py $workspace

mkdir -p $workspace/kaldi/data

python create_metadata.py $workspace $db_path

python final_metadata.py $workspace $db_path $workspace/metadata.json \
    /media/gerardo/SoloSinging/Construct_DSing/Gold/dev_gold.json \
    /media/gerardo/SoloSinging/Construct_DSing/Gold/test_gold.json \
    /media/gerardo/SoloSinging/Construct_DSing/Clean_speakers_performances.csv

python create_dsing.py $workspace $db_path dev.json dev
python create_dsing.py $workspace $db_path test.json test
python create_dsing.py $workspace $db_path train1.json train1
python create_dsing.py $workspace $db_path train3.json train3
python create_dsing.py $workspace $db_path train30.json train30

#
##python split_metadata_by_set.py $workspace
# python gold_standard/metadata_gold.py $workspace
#
#python to_kaldi.py $workspace metadata_train.json  train train
#python to_kaldi.py $workspace metadata_dev.json dev dev
#python to_kaldi.py $workspace metadata_test.json test test
#
#if [ "$version" = "DSing1" ]; then
#  python to_kaldi.py $workspace $workspace/kaldi/data/dev_gold/dev_gold.json dev dev_gold
#  python to_kaldi.py $workspace $workspace/kaldi/data/test_gold/test_gold.json test test_gold
#fi

#python final_metadata.py /media/gerardo/SoloSinging/DAMP/sing_300x30x2 \
# /media/gerardo/SoloSinging/DSing1 \
# /media/gerardo/SoloSinging/DSing1/metadata.json  \
# /media/gerardo/SoloSinging/Gold/dev_gold_new.json  \
# /media/gerardo/SoloSinging/Gold/test_gold_new.json  \
# /media/gerardo/SoloSinging/Clean_DAMP/performances.csv

echo "Process the DAMP Sing!300x30x2 dataset ended"






