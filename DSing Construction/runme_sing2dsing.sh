#!/usr/bin/env bash

# Current script will create a copy of several of the files

echo "Starting to process the DAMP Sing!300x30x2 dataset"
echo "The objective of this process is to generate a solo-singing dataset"
echo "for Lyrics Transcription researches"
echo; echo "There are three versions of this solo-singing English Dataset"
echo "DSing1  = The English spoken recordings from users registered as GB in Smule application"
echo "DSing3  = The English spoken recordings from GB plus the English spoken recordings from users where the country registered in Smule are US or ZA"
echo "DSing30 = The English spoken recordings from GB plus all the other English spoken recordings regardless of the registered country."

version=

DSing_dest=/media/gerardo/SoloSinging/DSing_Task/${version}
SmuleSing_path=/media/gerardo/SoloSinging/DAMP/sing_300x30x2

# A- Prepare the workspace
python set_workspace.py --db=${version} $DSing_dest

# B- Make a copy of Lyrics from Sing! to DSing Preconstructed
python copy_lyrics.py $DSing_dest $SmuleSing_path

# C- Filter word/syllable prompt-lyrics
python identify_wordlevel_lyrics.py $DSing_dest

# D- Download sentence-level prompt-lyrics from Smule
python scraping_lyrics.py  $DSing_dest

# E- Transform word to sentence level
python word_to_sentence_level.py $DSing_dest

# F- Filter non-English arrengemnts
python select_english_subset.py $DSing_dest

# G- Transform the prompt-lyrics format to a suitable format for sollowing step
python reformat_annotation.py $DSing_dest

# H- Align prompt-lyrics with non-silences segments
python realign_annotation.py $DSing_dest $SmuleSing_path

# I- Extract utterances using alignment
python extract_utterances.py $DSing_dest $SmuleSing_path

# J- Split into train/dev/test sets
python split_train_dev_test.py $DSing_dest

# K- Compile all the data in a metadata file
mkdir -p $DSing_dest/kaldi/data
python create_metadata.py $DSing_dest $SmuleSing_path


python final_metadata.py $DSing_dest $SmuleSing_path $DSing_dest/metadata.json \
    /media/gerardo/SoloSinging/Construct_DSing/Gold/dev_gold.json \
    /media/gerardo/SoloSinging/Construct_DSing/Gold/test_gold.json \
    /media/gerardo/SoloSinging/Construct_DSing/Clean_speakers_performances.csv

python create_dsing.py $DSing_dest $SmuleSing_path dev.json dev
python create_dsing.py $DSing_dest $SmuleSing_path test.json test
python create_dsing.py $DSing_dest $SmuleSing_path train1.json train1
python create_dsing.py $DSing_dest $SmuleSing_path train3.json train3
python create_dsing.py $DSing_dest $SmuleSing_path train30.json train30

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







