#!/usr/bin/env bash

#adapted from ami dict preparation script
#Author: Gerardo Roa

corpus=true # True  : Download preconstructed corpus
            # False : Generate new corpus downloading lyrics
datalocal=data/local
mkdir -p $datalocal


echo "$0 $@" # Print the command line for logging


. ./cmd.sh
. ./path.sh
. utils/parse_options.sh


# Preparing Dictionary
echo "=== Preparing the dictionary ..."





if [ corpus ]; then
    echo "===== Download preconstructed corpus"
    git clone https://github.com/groadabike/ASR_lyrics_pre.git $dict/groadabike
    mv $dict/groadabike/corpus.txt $datalocal/corpus.txt
fi



#utils/validate_dict_dir.pl $dict
#exit 0;

# Missing transform lexicon_full.txt into lexicon.txt
# Meanwhile is downloaded from github gerardo
mv $dict/groadabike/lexicon.txt $dict/lexicon.txt

