#!/bin/bash

. ./cmd.sh || exit 1

lm_order=2

echo "$0 $@" # Print the command line for logging

. ./cmd.sh
. ./path.sh
. utils/parse_options.sh

echo
echo "===== PREPARING LANGUAGE DATA ====="
echo

# Needs to be prepared by hand (or using self written scripts):
#
# lexicon.txt            [<word> <phone 1> <phone 2> ...]
# nonsilence_phones.txt  [<phone>]
# silence_phones_old.txt [<phone>]
# optional_silence.txt   [<phone>]

# Preparing language data
utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang

echo
echo "===== LANGUAGE MODEL CREATION ====="
echo "===== MAKING lm.arpa ====="
echo



datalocal=data/local
wget -nv -O $datalocal/corpus.txt https://raw.githubusercontent.com/groadabike/ASR_lyrics_pre/master/corpus.txt
mkdir -p $datalocal/tmp
ngram-count -order $lm_order -write-vocab $datalocal/tmp/vocab-full.txt -wbdiscount -text $datalocal/corpus.txt \
    -lm $datalocal/tmp/lm.arpa

echo
echo "===== MAKING G.fst ====="
echo

lang=data/lang
cat $datalocal/tmp/lm.arpa | arpa2fst - | fstprint | utils/eps2disambig.pl | \
    utils/s2eps.pl | fstcompile --isymbols=$lang/words.txt --osymbols=$lang/words.txt \
    --keep_isymbols=false --keep_osymbols=false | fstrmepsilon | fstarcsort \
    --sort_type=ilabel > $lang/G.fst