from bs4 import BeautifulSoup
import requests
from contextlib import closing
from os.path import join, dirname, exists
from os import listdir, makedirs
import shutil
import argparse
import json
import subprocess


def get_countries(workspace_path):
    countries = []
    with open(join(workspace_path, 'countries.txt')) as cfl:
        for line in cfl:
            countries.append(line.replace('\n', ''))

    return countries


def format_text(text):
    text = text.lower()
    symbols2dash = [" ", ",", ".", "!"]
    symbols2none = ["'", "&", "(", ")", "?"]
    for symbol in symbols2none:
        text = text.replace(symbol, "")
    text = text.lstrip().rstrip()
    for symbol in symbols2dash:
        text = text.replace(symbol, "-")
    text = text.replace("--", "-")

    return text


def create_folder(fd):
    if not exists(fd):
        makedirs(fd)


def list2file(path, data):
    create_folder(dirname(path))
    with open(path, "w") as file:
        for item in data:
            file.write("{}\n".format(item))


def file2list(filepath):
    """
    Read a file and return a list
    :param file:
    :return:
    """
    outlist = []
    with open(filepath) as file:
        for line in file:
            line = line.replace('\n', '')
            if line:
                outlist.append(line)
    return outlist


def create_original_json(args):
    """
    Saves a word-to-sentence level prompt lyrics
    :param args:
    :return:
    """
    workspace = args.workspace
    print("[English Subset] Save new sentence-level prompt lyric")
    countries = get_countries(args.workspace)

    for country in countries:
        print("[English Subset] Doing word2sentence lyrics of country {}".format(country))
        arrangement_list = file2list(join(workspace, "data", country, "word_level.txt"))

        for arrangement in arrangement_list:
            new_text_path = join(workspace, 'DownloadLyric', arrangement.split(".")[0] + ".txt")
            if exists(new_text_path):
                original_annotation_path = join(workspace, "data", country, country + 'Lyrics', arrangement)
                reconstructed_annotation = reconstruct_original_lyrics(new_text_path, original_annotation_path)
                original_reconstructed_lyrics_path = join(workspace, "data", country, country + 'DownloadLyric',
                                                            arrangement.split(".")[0] + ".json")
                create_folder(dirname(original_reconstructed_lyrics_path))
                with open(original_reconstructed_lyrics_path, 'w') as outfile:
                    json.dump(reconstructed_annotation, outfile, indent=4)

        one_word_recovered = [f for f in listdir(join(workspace, "data", country, country + 'DownloadLyric'))
                              if f.endswith(".json")]
        list2file(join(workspace, "data", country, 'one_word_recovered.txt'), one_word_recovered)
        for annotation in one_word_recovered:
            shutil.copy2(join(workspace, "data", country, country + 'DownloadLyric', annotation),
                         join(workspace, "data", country, country + 'Lyrics', annotation))


def reconstruct_original_lyrics(text_lyrics_path, json_lyrics_path):
    subprocess.call(['sed', '-i', '/.*un-termimated note on.*/d', json_lyrics_path])
    subprocess.call(['sed', '-i', '/.*found extra tempo event at beginning of file.*/d', json_lyrics_path])
    text_lyrics = file2list(text_lyrics_path)
    it_text_lyrics = iter(text_lyrics)
    current_text = next(it_text_lyrics)
    reconstruct = []
    element = {'t': 0.0,
               'l': ""}
    with open(json_lyrics_path, 'r') as data_file:
        try:
            data = json.load(data_file)
        except json.decoder.JSONDecodeError:
            print(data_file)
    for item in data:
        if item['l'] == current_text[:len(item['l'])]:
            if element['t'] == 0:
                element['t'] = item['t']
                element['l'] = current_text
            current_text = current_text[len(item['l']):].lstrip()

        # if item['l'] == current_text[1:len(item['l'])]:
        #     if element['t'] == 0:
        #         element['t'] = item['t']
        #         element['l'] = current_text
        #     current_text = current_text[len(item['l'])+1:].lstrip()
        #
        # if item['l'][1:] == current_text[:len(item['l'])-1]:
        #     if element['t'] == 0:
        #         element['t'] = item['t']
        #         element['l'] = current_text
        #     current_text = current_text[len(item['l'])-1:].lstrip()


        if len(current_text) == 0 or current_text == ',' or current_text == '.':
            reconstruct.append(element)
            element = {'t': 0.0,
                       'l': ""}
            try:
                current_text = next(it_text_lyrics)
            except StopIteration:
                break
    return reconstruct


if __name__ == '__main__':
    """
        Script that attempts to recover sentence-level prompts from Smule website
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("workspace", type=str, help="Path to Workspace")
    parser.add_argument('--version', action='version',
                        version='%(prog)s 1.0')

    args = parser.parse_args()

    create_original_json(args)
