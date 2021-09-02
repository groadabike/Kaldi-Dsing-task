from os import listdir, makedirs
from os.path import join, exists, dirname
from shutil import copy2
import argparse
import json
import subprocess


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def list2file(path, data):
    create_folder(dirname(path))
    with open(path, "w") as file:
        for item in data:
            file.write("{}\n".format(item))


def find_oneword_annotation(country, args):
    # Path to prompt lyrics
    path = join(args.workspace, "data", country, country + "Lyrics")
    # Load list of prompt lyrics
    list_prompts = [f for f in
                        listdir(path) if f.endswith(".json")]

    # lists that saves the name of prompts lyrics files by its classification
    word_level = []  # Prompts at word/syllable level
    sentence_level = []  # Prompts at sentence level
    bad_format = []  # Bad formated prompts

    # Analyse one prompt lyrics at a time
    for prompt in list_prompts:
        # These two lines delete the first line from some prompts
        # seems an error in the creation of the file
        subprocess.call(['sed', '-i', '/.*un-termimated note on.*/d', join(path, prompt)])
        subprocess.call(['sed', '-i', '/.*found extra tempo event at beginning of file.*/d', join(path, prompt)])

        try:
            with open(join(path, prompt)) as fs:
                annotation_parser = json.load(fs)
            count_one_word = 0
            count_multiple_words = 0

            for line in annotation_parser:
                if len(line["l"].split()) == 1:
                    count_one_word += 1
                else:
                    count_multiple_words += 1

        except json.decoder.JSONDecodeError:
            # prompt lyrics is not a proper json file
            # can't process it
            print("Prompt lyrics {} is not a proper JSON file".format(prompt))
            # Discarded
            count_one_word = 0
            count_multiple_words = 0

        if count_one_word == 0 and count_multiple_words == 0:
            # Both are zero, means bad formatted Prompt Lyrics file
            bad_format.append(prompt)
        elif count_one_word > count_multiple_words:
            # Word-level prompt
            word_level.append(prompt)
        else:
            # sentence-level prompt
            sentence_level.append(prompt)

    return word_level, sentence_level, bad_format


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace("\n", ""))

    return countries


if __name__ == '__main__':
    """
    Script that copy the lyrics from the original DAMP and preprocess them to identify the word level annotations
    """
    parser = argparse.ArgumentParser(
        description='Identify the word level annotations',
    )
    parser.add_argument('workspace', type=str,
                        help='Path to Workspace')
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()
    countries = get_countries(args.workspace)

    for country in countries:
        print("[English Subset] Identifying annotations at word/syllable level for country {}"
              .format(country))
        word_level, sentence_level, bad_format = find_oneword_annotation(country, args)
        list2file(join(args.workspace, 'data', country, "word_level.txt"), word_level)
        list2file(join(args.workspace, 'data', country, "sentence_level.txt"), sentence_level)
        list2file(join(args.workspace, 'data', country, "bad_format.txt"), bad_format)

